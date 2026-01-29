import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const chatAPI = {
  async send(message, conversationId = null) {
    const response = await api.post('/api/v1/chat', {
      message,
      conversation_id: conversationId
    })
    return response.data
  },

  async getHistory(conversationId) {
    const response = await api.get(`/api/v1/conversations/${conversationId}/history`)
    return response.data
  }
}

export default api
