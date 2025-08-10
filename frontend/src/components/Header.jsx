import React from 'react'
import { Brain, FileText, Github, Linkedin } from 'lucide-react'

const Header = () => {
  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Brain className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                AI Resume Analyzer
              </h1>
              <p className="text-sm text-gray-600">
                Powered by Advanced AI & Multi-Platform Analysis
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <FileText className="h-4 w-4" />
                <span>Resume Analysis</span>
              </div>
              <div className="flex items-center space-x-1">
                <Github className="h-4 w-4" />
                <span>GitHub Integration</span>
              </div>
              <div className="flex items-center space-x-1">
                <Linkedin className="h-4 w-4" />
                <span>LinkedIn Insights</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-4 flex items-center space-x-2 text-xs text-gray-500">
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
            ✅ Multi-format Support
          </span>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            ✅ AI-Powered Analysis
          </span>
          <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
            ✅ Real-time Processing
          </span>
          <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
            ✅ Conversation Memory
          </span>
        </div>
      </div>
    </header>
  )
}

export default Header
