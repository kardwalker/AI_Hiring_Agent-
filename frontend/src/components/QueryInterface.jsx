import React, { useState } from 'react'
import { Send, MessageSquare, User, Bot, Loader } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'

const QueryInterface = ({ sessionId, filename }) => {
  const [query, setQuery] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [conversation, setConversation] = useState([])
  const [analysisData, setAnalysisData] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || isAnalyzing) return

    const userMessage = { type: 'user', content: query, timestamp: new Date() }
    setConversation(prev => [...prev, userMessage])
    setIsAnalyzing(true)

    try {
      let response
      if (conversation.length === 0) {
        // First query - full analysis
        response = await api.analyzeResume(sessionId, query)
        setAnalysisData({
          resumeData: response.resume_data,
          githubAnalysis: response.github_analysis,
          linkedinAnalysis: response.linkedin_analysis
        })
      } else {
        // Follow-up query
        response = await api.continueConversation(sessionId, query)
      }

      const botMessage = { 
        type: 'bot', 
        content: response.answer, 
        timestamp: new Date(),
        metadata: conversation.length === 0 ? {
          resumeProcessed: !!response.resume_data,
          githubFound: !!response.github_analysis?.github_found,
          linkedinFound: !!response.linkedin_analysis?.linkedin_found
        } : null
      }
      
      setConversation(prev => [...prev, botMessage])
      setQuery('')
      
      if (conversation.length === 0) {
        toast.success('Resume analysis completed!')
      }
    } catch (error) {
      toast.error(error.message || 'Analysis failed')
      console.error('Analysis error:', error)
      
      const errorMessage = { 
        type: 'error', 
        content: error.message || 'An error occurred during analysis', 
        timestamp: new Date() 
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const suggestedQueries = [
    "What are the main technical skills and programming languages?",
    "Tell me about the GitHub repositories and projects",
    "What is the work experience and career progression?",
    "Summarize the educational background and qualifications",
    "What machine learning experience does this person have?"
  ]

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* File Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-blue-600" />
          <div>
            <p className="text-blue-800 font-medium">Ready for Analysis</p>
            <p className="text-blue-600 text-sm">File: {filename}</p>
          </div>
        </div>
      </div>

      {/* Conversation */}
      {conversation.length > 0 && (
        <div className="space-y-4 max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-white">
          {conversation.map((message, index) => (
            <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`
                max-w-3xl rounded-lg p-4 ${
                  message.type === 'user' 
                    ? 'bg-primary-600 text-white' 
                    : message.type === 'error'
                    ? 'bg-red-100 text-red-800 border border-red-200'
                    : 'bg-gray-100 text-gray-800'
                }
              `}>
                <div className="flex items-start space-x-2">
                  {message.type === 'user' ? (
                    <User className="h-5 w-5 mt-1 flex-shrink-0" />
                  ) : (
                    <Bot className="h-5 w-5 mt-1 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {message.metadata && (
                      <div className="mt-3 pt-3 border-t border-gray-300 text-sm">
                        <div className="flex flex-wrap gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            message.metadata.resumeProcessed 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            ✅ Resume Processed
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            message.metadata.githubFound 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {message.metadata.githubFound ? '✅' : 'ℹ️'} GitHub Analysis
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            message.metadata.linkedinFound 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {message.metadata.linkedinFound ? '✅' : 'ℹ️'} LinkedIn Analysis
                          </span>
                        </div>
                      </div>
                    )}
                    
                    <div className="text-xs mt-2 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isAnalyzing && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 rounded-lg p-4 max-w-3xl">
                <div className="flex items-center space-x-2">
                  <Bot className="h-5 w-5" />
                  <div className="flex items-center space-x-2">
                    <Loader className="h-4 w-4 animate-spin" />
                    <span>Analyzing resume...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Suggested Queries (show only if no conversation yet) */}
      {conversation.length === 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Suggested Questions:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestedQueries.map((suggestedQuery, index) => (
              <button
                key={index}
                onClick={() => setQuery(suggestedQuery)}
                className="text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors duration-200"
                disabled={isAnalyzing}
              >
                {suggestedQuery}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={conversation.length === 0 
              ? "Ask a question about the resume (e.g., 'What are the main technical skills?')" 
              : "Ask a follow-up question..."
            }
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isAnalyzing}
          />
          <button
            type="submit"
            disabled={!query.trim() || isAnalyzing}
            className="bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
          >
            {isAnalyzing ? (
              <Loader className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
            <span>{conversation.length === 0 ? 'Analyze' : 'Send'}</span>
          </button>
        </div>
      </form>
    </div>
  )
}

export default QueryInterface
