import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })
  const [authLoading, setAuthLoading] = useState(true)
  const [error, setError] = useState('')

  // 인증 상태 확인
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/me', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const userData = await response.json()
        if (!userData.error) {
          setUser(userData)
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      const url = isLogin ? '/login-email' : '/register'
      
      const response = await fetch(`http://127.0.0.1:8000${url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok) {
        if (isLogin) {
          setUser(data.user)
        } else {
          setIsLogin(true)
          setError('회원가입이 완료되었습니다. 로그인해주세요.')
        }
      } else {
        setError(data.error || '오류가 발생했습니다.')
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.')
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage = inputMessage
    setInputMessage('')
    setIsLoading(true)

    setMessages(prev => [...prev, { text: userMessage, isUser: true }])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      const data = await response.json()
      
      setMessages(prev => [...prev, { 
        text: data.answer, 
        isUser: false,
        category: data.category,
        confidence: data.confidence
      }])
    } catch (error) {
      setMessages(prev => [...prev, { text: '오류가 발생했습니다. 다시 시도해주세요.', isUser: false }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleGoogleLogin = () => {
    window.location.href = 'http://127.0.0.1:8000/login'
  }

  const handleLogout = async () => {
    try {
      await fetch('http://127.0.0.1:8000/logout', {
        credentials: 'include'
      })
      setUser(null)
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  // 로딩 중
  if (authLoading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>로딩 중...</p>
      </div>
    )
  }

  // 로그인 페이지
  if (!user) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1 className="logo">SubBot 💬</h1>
          <h2>{isLogin ? '로그인' : '회원가입'}</h2>
          
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleSubmit} className="auth-form">
            {!isLogin && (
              <div className="form-group">
                <label>이름</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required={!isLogin}
                  placeholder="이름을 입력하세요"
                />
              </div>
            )}
            
            <div className="form-group">
              <label>이메일</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                placeholder="이메일을 입력하세요"
              />
            </div>
            
            <div className="form-group">
              <label>비밀번호</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                minLength="6"
                placeholder="비밀번호를 입력하세요"
              />
            </div>
            
            <button type="submit" className="auth-button">
              {isLogin ? '로그인' : '회원가입'}
            </button>
          </form>
          
          <div className="divider">
            <span>또는</span>
          </div>
          
          <button onClick={handleGoogleLogin} className="google-button">
            Google로 계속하기
          </button>
          
          <div className="toggle">
            {isLogin ? '계정이 없으신가요? ' : '이미 계정이 있으신가요? '}
            <button 
              onClick={() => {
                setIsLogin(!isLogin)
                setError('')
              }}
              className="toggle-button"
            >
              {isLogin ? '회원가입' : '로그인'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // 채팅 화면
  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>SubBot 💬</h1>
        <div className="user-info">
          <span>{user.name || user.email}</span>
          <button onClick={handleLogout} className="logout-button">로그아웃</button>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <p>안녕하세요! SubBot입니다. 무엇이 궁금하신가요?</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.isUser ? 'user' : 'bot'}`}>
              <div className="message-content">{msg.text}</div>
            </div>
          ))
        )}
        {isLoading && <div className="message bot"><div className="typing-indicator">...</div></div>}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="메시지를 입력하세요..."
          disabled={isLoading}
          className="message-input"
        />
        <button 
          onClick={sendMessage} 
          disabled={isLoading || !inputMessage.trim()}
          className="send-button"
        >
          {isLoading ? '...' : '전송'}
        </button>
      </div>
    </div>
  )
}

export default App
