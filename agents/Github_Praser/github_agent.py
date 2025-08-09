"""GitHub Parser Agent
=======================

Purpose:
	Fetch and parse a developer's public GitHub footprint using the GitHub REST API.
	Returns a structured summary with profile metrics, repository breakdown, language
	distribution, and simple qualitative signals useful for downstream AI agents.

Design Goals:
	- Pure async implementation (with optional sync wrapper) for easy integration.
	- Resilient to partial failures (continues when individual repo calls fail).
	- Token optional (higher rate limits if GITHUB_TOKEN provided as env var).
	- Minimal external deps (relies on httpx which is already installed via langchain/openai stack).

Data Contract (high level):
	parse_github_user(username) -> dict {
		"profile": {...raw user object...},
		"repositories": [ { name, stars, forks, language, topics, size, pushed_at, ... } ],
		"stats": {
			"public_repos": int,
			"total_stars": int,
			"total_forks": int,
			"open_issues": int,
			"archived_repos": int,
			"language_bytes": { lang: bytes },
			"top_languages": [ {"language": str, "percent": float, "bytes": int, "repo_count": int } ],
			"recent_push_activity_days": float | None,
			"activity_level": "none"|"low"|"medium"|"high",
			"recent_repos": [ repo_name, ... up to 5 ],
		},
		"meta": {
			"fetched_at": iso-datetime,
			"rate_limit_remaining": int | None,
			"username": str,
			"error_count": int
		}
	}

Limitations:
	- Does not fetch contribution calendar (requires GraphQL); left as future extension.
	- Does not inspect individual file contents (can be added if needed / cost tradeoff).

Usage Example:
	from agents.Github_Praser.github_agent import GitHubParser
	import asyncio
	async def run():
		parser = GitHubParser()
		data = await parser.parse_github_user("octocat")
		print(data["stats"]["top_languages"])  # Quick peek
	asyncio.run(run())

"""

from __future__ import annotations

import os
import math
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import httpx

GITHUB_API = "https://api.github.com"


class GitHubParser:
	"""High-level GitHub profile & repository parser using REST API.

	Provides an async interface plus a sync convenience wrapper.
	"""

	def __init__(self, token: Optional[str] = None, timeout: float = 15.0):
		self.token = token or os.getenv("GITHUB_TOKEN")
		self.timeout = timeout

	# ----------------------------- Public API ----------------------------- #
	async def parse_github_user(self, username: str, max_repos: int = 200) -> Dict[str, Any]:
		"""Fetch profile + repositories and compute aggregate statistics.

		Args:
			username: GitHub username (login).
			max_repos: Upper bound on number of repos to fetch (pagination limit).
		"""
		fetched_at = datetime.now(timezone.utc).isoformat()
		headers = self._build_headers()
		error_count = 0

		async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
			profile = await self._safe_get_json(client, f"{GITHUB_API}/users/{username}")
			if profile.get("message") == "Not Found":
				return {
					"profile": {},
					"repositories": [],
					"stats": {},
					"meta": {
						"fetched_at": fetched_at,
						"username": username,
						"error": "User not found"
					}
				}

			repos = await self._fetch_all_repositories(client, username, max_repos)

			# Compute derived stats
			stats = self._compute_stats(profile, repos)

			# Rate limit info (best effort)
			rate_remaining = None
			try:
				# /rate_limit is one extra call; we avoid by checking headers from last resp
				# If not available, we skip.
				rate_remaining = client.headers.get("X-RateLimit-Remaining")  # type: ignore
				if rate_remaining is not None:
					rate_remaining = int(rate_remaining)
			except Exception:
				pass

			return {
				"profile": profile,
				"repositories": repos,
				"stats": stats,
				"meta": {
					"fetched_at": fetched_at,
					"username": username,
					"rate_limit_remaining": rate_remaining,
					"error_count": error_count,
				}
			}

	def parse_github_user_sync(self, username: str, max_repos: int = 200) -> Dict[str, Any]:
		"""Synchronous wrapper for environments without full async orchestration."""
		return asyncio.run(self.parse_github_user(username, max_repos=max_repos))

	# -------------------------- Internal Helpers ------------------------- #
	def _build_headers(self) -> Dict[str, str]:
		headers = {"Accept": "application/vnd.github+json"}
		if self.token:
			headers["Authorization"] = f"Bearer {self.token}"
		return headers

	async def _safe_get_json(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
		try:
			resp = await client.get(url)
			resp.raise_for_status()
			return resp.json()
		except httpx.HTTPStatusError as e:
			return {"error": str(e), "status_code": e.response.status_code, "url": url}
		except Exception as e:  # Network or JSON parse
			return {"error": str(e), "url": url}

	async def _fetch_all_repositories(self, client: httpx.AsyncClient, username: str, max_repos: int) -> List[Dict[str, Any]]:
		repos: List[Dict[str, Any]] = []
		per_page = 100
		pages = math.ceil(max_repos / per_page)
		for page in range(1, pages + 1):
			url = f"{GITHUB_API}/users/{username}/repos?per_page={per_page}&page={page}&sort=updated"
			data = await self._safe_get_json(client, url)
			if isinstance(data, list):
				repos.extend(data)
				if len(data) < per_page:  # Last page
					break
			else:
				# Error occurred; break to avoid further rate usage
				break
			if len(repos) >= max_repos:
				break
		# Trim to max_repos
		repos = repos[:max_repos]
		# Lightweight normalization
		normalized = [
			{
				"name": r.get("name"),
				"full_name": r.get("full_name"),
				"private": r.get("private"),
				"fork": r.get("fork"),
				"archived": r.get("archived"),
				"language": r.get("language"),
				"topics": r.get("topics", []),
				"stargazers_count": r.get("stargazers_count", 0),
				"forks_count": r.get("forks_count", 0),
				"open_issues_count": r.get("open_issues_count", 0),
				"size_kb": r.get("size"),
				"pushed_at": r.get("pushed_at"),
				"created_at": r.get("created_at"),
				"updated_at": r.get("updated_at"),
				"html_url": r.get("html_url"),
				"default_branch": r.get("default_branch"),
				"license": (r.get("license") or {}).get("spdx_id") if r.get("license") else None,
			}
			for r in repos
		]
		return normalized

	def _compute_stats(self, profile: Dict[str, Any], repos: List[Dict[str, Any]]) -> Dict[str, Any]:
		total_stars = sum(r.get("stargazers_count", 0) for r in repos)
		total_forks = sum(r.get("forks_count", 0) for r in repos)
		total_open_issues = sum(r.get("open_issues_count", 0) for r in repos)
		archived = sum(1 for r in repos if r.get("archived"))

		language_bytes: Dict[str, int] = {}
		# size_kb is repo size; approximate distribution by primary language counts (rough heuristic)
		for r in repos:
			lang = r.get("language") or "Unknown"
			size_kb = r.get("size_kb") or 0
			language_bytes[lang] = language_bytes.get(lang, 0) + int(size_kb) * 1024

		total_lang_bytes = sum(language_bytes.values()) or 1
		top_languages = [
			{
				"language": lang,
				"bytes": b,
				"percent": round(b * 100 / total_lang_bytes, 2),
				"repo_count": sum(1 for r in repos if (r.get("language") or "Unknown") == lang),
			}
			for lang, b in sorted(language_bytes.items(), key=lambda kv: kv[1], reverse=True)
		]

		# Recent push activity
		push_times = [r["pushed_at"] for r in repos if r.get("pushed_at")]
		recent_days = None
		activity_level = "none"
		if push_times:
			latest = max(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in push_times)
			delta_days = (datetime.now(timezone.utc) - latest).total_seconds() / 86400
			recent_days = round(delta_days, 2)
			if delta_days < 3:
				activity_level = "high"
			elif delta_days < 14:
				activity_level = "medium"
			elif delta_days < 45:
				activity_level = "low"
			else:
				activity_level = "none"

		recent_repos = [r["name"] for r in sorted(
			repos, key=lambda r: r.get("pushed_at") or "", reverse=True
		)[:5]]

		return {
			"public_repos": profile.get("public_repos"),
			"followers": profile.get("followers"),
			"following": profile.get("following"),
			"total_stars": total_stars,
			"total_forks": total_forks,
			"open_issues": total_open_issues,
			"archived_repos": archived,
			"language_bytes": language_bytes,
			"top_languages": top_languages,
			"recent_push_activity_days": recent_days,
			"activity_level": activity_level,
			"recent_repos": recent_repos,
		}


# --------------------------- Module CLI Helper --------------------------- #
async def _main_cli():  # pragma: no cover (simple manual utility)
	import argparse

	parser = argparse.ArgumentParser(description="Parse a GitHub user's public profile")
	parser.add_argument("username", help="GitHub username (login)")
	parser.add_argument("--max-repos", type=int, default=200, help="Maximum repositories to fetch")
	args = parser.parse_args()

	parser_instance = GitHubParser()
	data = await parser_instance.parse_github_user(args.username, max_repos=args.max_repos)

	# Print compact summary
	stats = data.get("stats", {})
	print(f"User: {args.username}")
	print(f"Public Repos: {stats.get('public_repos')} | Followers: {stats.get('followers')} | Stars: {stats.get('total_stars')}")
	langs = ", ".join(f"{l['language']}({l['percent']}%)" for l in stats.get("top_languages", [])[:5])
	print(f"Top Languages: {langs}")
	print(f"Activity Level: {stats.get('activity_level')} (last push ~{stats.get('recent_push_activity_days')} days ago)")

	# Optional: full JSON
	# import json; print(json.dumps(data, indent=2))


if __name__ == "__main__":  # pragma: no cover
	asyncio.run(_main_cli())

from la