/**
 * API Service for handling backend communications
 */

const API_BASE_URL = 'https://redesigned-system-xj766xv9vvv3vp66-5000.app.github.dev/'
const LANGGRAPH_API_URL = 'http://localhost:8000'

class ApiService {
  // Main Backend API (Port 5000)
  static async fetchCards() {
    const response = await fetch(`${API_BASE_URL}/cards`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async createCard(text, title = null) {
    const response = await fetch(`${API_BASE_URL}/add-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, title })
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async updateCard(cardId, data) {
    const response = await fetch(`${API_BASE_URL}/cards/${cardId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async deleteCard(cardId) {
    const response = await fetch(`${API_BASE_URL}/cards/${cardId}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  // LangGraph AI API (Port 8000)
  static async checkAIHealth() {
    try {
      const response = await fetch(`${LANGGRAPH_API_URL}/health`)
      if (!response.ok) return null
      return response.json()
    } catch (error) {
      return null
    }
  }

  static async sendChatMessage(message, sessionId = null) {
    const response = await fetch(`${LANGGRAPH_API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message, 
        session_id: sessionId 
      })
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async getSessionHistory(sessionId, limit = 10) {
    const response = await fetch(`${LANGGRAPH_API_URL}/sessions/${sessionId}/history?limit=${limit}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async setFocusedCard(sessionId, cardData) {
    const response = await fetch(`${LANGGRAPH_API_URL}/sessions/${sessionId}/focused-card`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card: cardData })
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async clearFocusedCard(sessionId) {
    const response = await fetch(`${LANGGRAPH_API_URL}/sessions/${sessionId}/focused-card`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async getActiveSessions() {
    const response = await fetch(`${LANGGRAPH_API_URL}/sessions/active`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async getWorkflowStatus() {
    const response = await fetch(`${LANGGRAPH_API_URL}/workflow/status`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }

  static async getSupportedIntents() {
    const response = await fetch(`${LANGGRAPH_API_URL}/workflow/intents`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return response.json()
  }
}

export default ApiService
