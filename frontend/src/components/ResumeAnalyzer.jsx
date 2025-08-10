import React, { useState } from 'react'
import FileUpload from './FileUpload'
import QueryInterface from './QueryInterface'
import { RotateCcw, FileText } from 'lucide-react'

const ResumeAnalyzer = () => {
  const [sessionId, setSessionId] = useState(null)
  const [filename, setFilename] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleUploadSuccess = (newSessionId, newFilename) => {
    setSessionId(newSessionId)
    setFilename(newFilename)
  }

  const handleReset = () => {
    setSessionId(null)
    setFilename(null)
    setIsLoading(false)
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-bold text-gray-900">
          AI-Powered Resume Analysis
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Upload your resume and get comprehensive insights with GitHub and LinkedIn integration, 
          powered by advanced AI technology.
        </p>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
        {!sessionId ? (
          // Upload Phase
          <div className="space-y-6">
            <div className="text-center">
              <FileText className="h-16 w-16 text-primary-500 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                Upload Your Resume
              </h3>
              <p className="text-gray-600">
                Start by uploading your resume in PDF, TXT, DOCX, or MD format
              </p>
            </div>
            
            <FileUpload 
              onUploadSuccess={handleUploadSuccess}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />
            
            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 pt-8 border-t border-gray-200">
              <div className="text-center space-y-2">
                <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <h4 className="font-semibold text-gray-900">Multi-Format Support</h4>
                <p className="text-sm text-gray-600">
                  Supports PDF, TXT, DOCX, and Markdown files
                </p>
              </div>
              
              <div className="text-center space-y-2">
                <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto">
                  <svg className="h-6 w-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <h4 className="font-semibold text-gray-900">AI-Powered Analysis</h4>
                <p className="text-sm text-gray-600">
                  Advanced AI extracts and analyzes key information
                </p>
              </div>
              
              <div className="text-center space-y-2">
                <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto">
                  <svg className="h-6 w-6 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-gray-900">Platform Integration</h4>
                <p className="text-sm text-gray-600">
                  Analyzes GitHub repos and LinkedIn profiles
                </p>
              </div>
            </div>
          </div>
        ) : (
          // Analysis Phase
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-semibold text-gray-900">
                  Resume Analysis
                </h3>
                <p className="text-gray-600">
                  Ask questions about the resume and get detailed insights
                </p>
              </div>
              
              <button
                onClick={handleReset}
                className="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors duration-200"
              >
                <RotateCcw className="h-4 w-4" />
                <span>New Resume</span>
              </button>
            </div>
            
            <QueryInterface 
              sessionId={sessionId} 
              filename={filename}
            />
          </div>
        )}
      </div>
      
      {/* Footer Info */}
      <div className="text-center text-sm text-gray-500 space-y-2">
        <p>
          Powered by StateGraph workflow orchestration, BM25 + Vector search, and persistent Chroma storage
        </p>
        <div className="flex justify-center space-x-4">
          <span>✅ Multi-turn conversations</span>
          <span>✅ Memory persistence</span>
          <span>✅ Real-time processing</span>
        </div>
      </div>
    </div>
  )
}

export default ResumeAnalyzer
