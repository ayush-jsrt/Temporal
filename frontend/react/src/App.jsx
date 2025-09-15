import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

const App = () => {
  const [cards, setCards] = useState([])
  const [focusedCard, setFocusedCard] = useState(null)
  const [textInput, setTextInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const carouselRef = useRef(null)

  // Fetch all cards on component mount
  useEffect(() => {
    fetchCards()
  }, [])

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

  const stripHtmlTags = (html) => {
    return html.replace(/<[^>]*>/g, '').trim()
  }

  const renderCardContent = (content) => {
    return { __html: content }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Temporal Knowledge Cards</h1>
        <p>Your personal knowledge companion powered by AI</p>
      </header>

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
      </main>
    </div>
  )
}

export default App
