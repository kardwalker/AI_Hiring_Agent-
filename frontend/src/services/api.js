import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for file processing
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🔄 ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('❌ Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
    return response
  },
  (error) => {
    console.error('❌ Response error:', error.response?.data || error.message)
    
    // Transform error for better handling
    const errorMessage = error.response?.data?.detail || 
                         error.response?.data?.message || 
                         error.message || 
                         'An unexpected error occurred'
    
    return Promise.reject(new Error(errorMessage))
  }
)

const api = {
  // Health check
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Upload resume file
  async uploadResume(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post('/upload-resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    return response.data
  },

  // Analyze resume with query
  async analyzeResume(sessionId, query) {
    const response = await apiClient.post('/analyze-resume', {
      session_id: sessionId,
      query: query
    })
    
    return response.data
  },

  // Continue conversation
  async continueConversation(sessionId, query) {
    const response = await apiClient.post('/continue-conversation', {
      session_id: sessionId,
      query: query
    })
    
    return response.data
  },

  // Get session info
  async getSessionInfo(sessionId) {
    const response = await apiClient.get(`/session/${sessionId}`)
    return response.data
  },

  // Delete session
  async deleteSession(sessionId) {
    const response = await apiClient.delete(`/session/${sessionId}`)
    return response.data
  },

  // List active sessions
  async listSessions() {
    const response = await apiClient.get('/sessions')
    return response.data
  }
}

export default api
