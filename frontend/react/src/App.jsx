import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'
const LANGGRAPH_API_URL = 'http://localhost:8000'

const App = () => {
  const [cards, setCards] = useState([])
  const [focusedCard, setFocusedCard] = useState(null)
  const [textInput, setTextInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  
  // AI Chat functionality
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [aiError, setAiError] = useState('')
  const [showChat, setShowChat] = useState(false)
  const [aiStatus, setAiStatus] = useState(null)
  
  const carouselRef = useRef(null)
  const chatEndRef = useRef(null)

  // Fetch all cards on component mount
  useEffect(() => {
    fetchCards()
    checkAIStatus()
  }, [])

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatMessages])

  // Update focused card in AI session when manually focused
  useEffect(() => {
    if (focusedCard && sessionId && aiStatus?.redis_enabled) {
      updateAIFocusedCard(focusedCard)
    }
  }, [focusedCard, sessionId])

  // Handle carousel scroll and focus detection
  useEffect(() => {
    const handleScroll = () => {
      if (carouselRef.current && cards.length > 0) {
        const carousel = carouselRef.current
        const carouselRect = carousel.getBoundingClientRect()
        const carouselCenter = carouselRect.left + carouselRect.width / 2
        
        let closestCard = null
        let closestDistance = Infinity
        
        const cardElements = carousel.querySelectorAll('.card')
        cardElements.forEach((cardElement, index) => {
          const cardRect = cardElement.getBoundingClientRect()
          const cardCenter = cardRect.left + cardRect.width / 2
          const distance = Math.abs(cardCenter - carouselCenter)
          
          if (distance < closestDistance) {
            closestDistance = distance
            closestCard = cards[index]
          }
        })
        
        if (closestCard && closestCard.id !== focusedCard?.id) {
          setFocusedCard(closestCard)
        }
      }
    }

    if (carouselRef.current) {
      carouselRef.current.addEventListener('scroll', handleScroll)
      // Initial focus detection
      setTimeout(handleScroll, 100)
      
      return () => {
        if (carouselRef.current) {
          carouselRef.current.removeEventListener('scroll', handleScroll)
        }
      }
    }
  }, [cards, focusedCard])

  // API Functions
  const checkAIStatus = async () => {
    try {
      const response = await axios.get(`${LANGGRAPH_API_URL}/health`)
      setAiStatus(response.data)
    } catch (err) {
      console.warn('LangGraph server not available:', err.message)
      setAiStatus(null)
    }
  }

  const fetchCards = async () => {
    try {
      setIsLoading(true)
      const response = await axios.get(`${API_BASE_URL}/cards`)
      if (response.data.success) {
        setCards(response.data.cards)
        if (response.data.cards.length > 0 && !focusedCard) {
          setFocusedCard(response.data.cards[0])
        }
      }
    } catch (err) {
      setError('Failed to fetch cards: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const addCard = async () => {
    if (!textInput.trim()) return

    try {
      setIsLoading(true)
      setError('')
      
      const response = await axios.post(`${API_BASE_URL}/add-text`, {
        text: textInput
      })
      
      if (response.data.success) {
        setTextInput('')
        await fetchCards()
      } else {
        setError(response.data.error || 'Failed to add card')
      }
    } catch (err) {
      setError('Failed to add card: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !aiStatus) return

    const userMessage = chatInput.trim()
    setChatInput('')
    setIsChatLoading(true)
    setAiError('')

    // Add user message to chat
    const newUserMessage = {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setChatMessages(prev => [...prev, newUserMessage])

    try {
      // Prepare the request payload
      const requestPayload = {
        message: userMessage,
        session_id: sessionId
      }

      // Include focused card if available
      if (focusedCard) {
        requestPayload.focused_card = {
          id: focusedCard.id,
          title: focusedCard.title,
          content: focusedCard.content.substring(0, 500) // Limit content size
        }
        console.log(`🎯 Sending focused card context: ${focusedCard.title}`)
      } else {
        console.log(`ℹ️ No focused card context available`)
      }

      const response = await axios.post(`${LANGGRAPH_API_URL}/chat`, requestPayload)

      if (response.data.success) {
        const aiData = response.data.data
        
        // Update session ID for continuity
        setSessionId(aiData.session_id)

        // Add AI response to chat
        const aiMessage = {
          type: 'ai',
          content: aiData.response,
          intent: aiData.intent,
          confidence: aiData.confidence,
          reasoning: aiData.reasoning,
          cardId: aiData.card_id,
          timestamp: aiData.timestamp
        }
        setChatMessages(prev => [...prev, aiMessage])

        // If a card was created or updated, refresh the cards
        if (aiData.card_id && (aiData.intent === 'CREATE_NEW' || aiData.intent === 'UPDATE')) {
          await fetchCards()
          
          // Focus on the created/updated card
          if (aiData.intent === 'CREATE_NEW') {
            // Find and focus the newly created card
            setTimeout(() => {
              setCards(currentCards => {
                const newCard = currentCards.find(card => card.id === aiData.card_id)
                if (newCard) {
                  setFocusedCard(newCard)
                }
                return currentCards
              })
            }, 1000)
          }
        }
      } else {
        throw new Error(response.data.error)
      }
    } catch (err) {
      setAiError('Failed to send message: ' + err.message)
      
      // Add error message to chat
      const errorMessage = {
        type: 'error',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  const updateAIFocusedCard = async (card) => {
    if (!sessionId || !aiStatus?.redis_enabled) return

    try {
      console.log(`🎯 Setting focused card in AI: ${card.title}`)
      await axios.post(`${LANGGRAPH_API_URL}/sessions/${sessionId}/focused-card`, {
        card: {
          id: card.id,
          title: card.title,
          content: card.content.substring(0, 500) // Limit content size
        }
      })
      console.log(`✅ Focused card set successfully`)
    } catch (err) {
      console.warn('❌ Failed to update AI focused card:', err.message)
    }
  }

  const clearChat = () => {
    setChatMessages([])
    setSessionId(null)
    setAiError('')
  }

  const deleteCard = async (cardId) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/cards/${cardId}`)
      if (response.data.success) {
        setCards(prev => prev.filter(card => card.id !== cardId))
        if (focusedCard && focusedCard.id === cardId) {
          const remainingCards = cards.filter(card => card.id !== cardId)
          setFocusedCard(remainingCards.length > 0 ? remainingCards[0] : null)
        }
      }
    } catch (err) {
      setError('Failed to delete card: ' + err.message)
    }
  }

  const scrollToCard = (cardIndex) => {
    if (carouselRef.current) {
      const cardElement = carouselRef.current.children[0].children[cardIndex]
      if (cardElement) {
        cardElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'center'
        })
      }
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const stripHtmlTags = (html) => {
    return html.replace(/<[^>]*>/g, '').trim()
  }

  const renderCardContent = (content) => {
    return { __html: content }
  }

  const getIntentColor = (intent) => {
    switch (intent) {
      case 'NO_ACTION': return '#6366f1'
      case 'CREATE_NEW': return '#10b981'
      case 'UPDATE': return '#f59e0b'
      default: return '#6b7280'
    }
  }

  const getIntentLabel = (intent) => {
    switch (intent) {
      case 'NO_ACTION': return 'Information'
      case 'CREATE_NEW': return 'Create Card'
      case 'UPDATE': return 'Update Card'
      default: return 'Unknown'
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Temporal Knowledge Cards</h1>
        <p>Your personal knowledge companion powered by AI</p>
        
        {/* AI Status */}
        <div className="ai-status-bar">
          <div className="ai-status">
            <span className={`status-indicator ${aiStatus ? 'online' : 'offline'}`}></span>
            AI Assistant: {aiStatus ? 'Online' : 'Offline'}
            {aiStatus?.redis_enabled && <span className="feature-badge">Session Memory</span>}
          </div>
        </div>
      </header>

      {/* Floating Chat Toggle Button */}
      {aiStatus && (
        <button 
          className={`floating-chat-toggle ${showChat ? 'active' : ''}`}
          onClick={() => setShowChat(!showChat)}
          title={showChat ? 'Hide AI Chat' : 'Show AI Chat'}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
          </svg>
        </button>
      )}

      <main className="main-content">
        {/* Input Section */}
        <section className="input-section">
          <h2>Add New Knowledge</h2>
          <form className="input-form" onSubmit={(e) => { e.preventDefault(); addCard(); }}>
            <textarea
              className="text-input"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Enter your thoughts, ideas, or any text you'd like to process into a knowledge card..."
              disabled={isLoading}
            />
            <button
              type="submit"
              className="submit-btn"
              disabled={isLoading || !textInput.trim()}
            >
              {isLoading ? 'Processing...' : 'Create Knowledge Card'}
            </button>
          </form>
          {error && <div className="error">{error}</div>}
        </section>

        {/* Cards Section */}
        {isLoading && cards.length === 0 ? (
          <div className="loading">Loading your knowledge cards...</div>
        ) : (
          <>
            {/* Carousel */}
            {cards.length > 0 && (
              <div className="carousel-container">
                <div className="carousel-wrapper" ref={carouselRef}>
                  <div className="carousel">
                    {cards.map((card, index) => (
                      <div
                        key={card.id}
                        className={`card ${focusedCard?.id === card.id ? 'focused' : ''}`}
                        onClick={() => {
                          setFocusedCard(card)
                          scrollToCard(index)
                        }}
                      >
                        <button
                          className="card-delete"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteCard(card.id)
                          }}
                          title="Delete card"
                        >
                          ×
                        </button>
                        <h3 className="card-title">{card.title}</h3>
                        <div className="card-preview">
                          {stripHtmlTags(card.content).substring(0, 120)}...
                        </div>
                        <div className="card-date">{formatDate(card.created_at)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Detail View */}
            <div className={`detail-view ${!focusedCard ? 'empty' : ''}`}>
              {focusedCard ? (
                <>
                  <h2 className="detail-title">{focusedCard.title}</h2>
                  <div
                    className="detail-content"
                    dangerouslySetInnerHTML={renderCardContent(focusedCard.content)}
                  />
                  <div className="detail-meta">
                    <span className="detail-date">
                      Created: {formatDate(focusedCard.created_at)}
                    </span>
                    {focusedCard.metadata?.novelty && (
                      <span className="novelty-indicator">
                        {focusedCard.metadata.novelty} Novelty
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <p>Select a knowledge card to view details</p>
              )}
            </div>
          </>
        )}

        {cards.length === 0 && !isLoading && (
          <div className="detail-view empty">
            <p>No knowledge cards yet. Add your first one above!</p>
          </div>
        )}

        {/* AI Chat Interface - Moved to bottom */}
        {showChat && aiStatus && (
          <section className="chat-section">
            <div className="chat-header">
              <h2>AI Assistant</h2>
              <div className="chat-actions">
                <button onClick={clearChat} className="clear-chat-btn">
                  Clear Chat
                </button>
              </div>
            </div>
            
            <div className="chat-messages">
              {chatMessages.length === 0 ? (
                <div className="chat-welcome">
                  <p>Start a conversation...</p>
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div key={index} className={`message ${message.type}`}>
                    <div className="message-content">
                      {message.content}
                    </div>
                    {message.type === 'ai' && (
                      <div className="message-meta">
                        <span 
                          className="intent-badge" 
                          style={{ backgroundColor: getIntentColor(message.intent) }}
                        >
                          {getIntentLabel(message.intent)}
                        </span>
                        <span className="confidence">
                          {Math.round(message.confidence * 100)}% confidence
                        </span>
                        <span className="timestamp">
                          {formatTime(message.timestamp)}
                        </span>
                        {message.cardId && (
                          <span className="card-link">
                            Card #{message.cardId}
                          </span>
                        )}
                      </div>
                    )}
                    {message.type === 'user' && (
                      <div className="message-time">
                        {formatTime(message.timestamp)}
                      </div>
                    )}
                  </div>
                ))
              )}
              {isChatLoading && (
                <div className="message ai loading">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="chat-input-container">
              {focusedCard && (
                <div className="focused-card-indicator">
                  📌 Focused on: <strong>{focusedCard.title}</strong>
                  {sessionId && aiStatus?.redis_enabled && (
                    <span className="ai-context-status">✓ AI has context</span>
                  )}
                  {(!sessionId || !aiStatus?.redis_enabled) && (
                    <span className="ai-context-status warning">⚠ AI has no context</span>
                  )}
                </div>
              )}
              <form 
                className="chat-form" 
                onSubmit={(e) => { e.preventDefault(); sendChatMessage(); }}
              >
                <input
                  type="text"
                  className="chat-input"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask anything or say 'create a card about...' or 'update this card with...'"
                  disabled={isChatLoading}
                />
                <button
                  type="submit"
                  className="chat-send-btn"
                  disabled={isChatLoading || !chatInput.trim()}
                >
                  Send
                </button>
              </form>
              {aiError && <div className="ai-error">{aiError}</div>}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
