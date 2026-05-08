import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [rememberLogin, setRememberLogin] = useState(false)
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
    
    // 로그인 유지 체크
    const savedRememberLogin = localStorage.getItem('rememberLogin')
    const savedUserEmail = localStorage.getItem('userEmail')
    
    if (savedRememberLogin === 'true' && savedUserEmail) {
      setFormData(prev => ({ ...prev, email: savedUserEmail }))
      setRememberLogin(true)
    }
    
    // 페이지 새로고침 시 로그인 상태 확인 방지
    const handleBeforeUnload = (e) => {
      if (user) {
        // 로그인된 상태에서는 새로고침해도 로그인 유지
        e.preventDefault()
        e.returnValue = ''
      }
    }
    
    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [user])

  const checkAuth = async () => {
    try {
      // 페이지 로드 시 localStorage에서 사용자 정보 확인
      const savedRememberLogin = localStorage.getItem('rememberLogin')
      const savedUserEmail = localStorage.getItem('userEmail')
      const savedUserName = localStorage.getItem('userName')
      
      if (savedRememberLogin === 'true' && savedUserEmail) {
        // 로그인 유지된 경우 자동으로 사용자 정보 설정
        setUser({ email: savedUserEmail, name: savedUserName || savedUserEmail })
        setIsLogin(false)
        setAuthLoading(false)
        return
      }
      
      // 서버에 인증 상태 확인
      const response = await fetch('http://127.0.0.1:8000/me', {
        credentials: 'include'
      })
      
      if (response.ok) {
        const userData = await response.json()
        if (!userData.error) {
          setUser(userData)
          setIsLogin(false)
        }
      }
    } catch (err) {
      console.error('Auth check failed:', err)
    } finally {
      setAuthLoading(false)
    }
  }

  const formatResponseTime = (ms) => {
    if (ms === undefined || ms === null) return ''
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}초`
    const minutes = Math.floor(ms / 60000)
    const seconds = ((ms % 60000) / 1000).toFixed(0)
    return `${minutes}분 ${seconds}초`
  }

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/login-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok) {
        setUser(data.user)
        setIsLogin(false)
        setFormData({ email: '', password: '', name: '' })
        
        // 로그인 유지 체크 확인
        if (rememberLogin) {
          localStorage.setItem('rememberLogin', 'true')
          localStorage.setItem('userEmail', formData.email)
          localStorage.setItem('userName', data.user.name || data.user.email)
        } else {
          localStorage.removeItem('rememberLogin')
          localStorage.removeItem('userEmail')
          localStorage.removeItem('userName')
        }
      } else {
        setError(data.error || '로그인에 실패했습니다.')
      }
    } catch (err) {
      setError('서버 연결 오류가 발생했습니다.')
    } finally {
      setAuthLoading(false)
    }
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
    const startTime = performance.now()

    setMessages(prev => [...prev, { text: userMessage, isUser: true }])

    try {
      // 문제 감지 및 검색 여부 확인
      const hasProblem = userMessage.includes('문제') || userMessage.includes('오류') || 
                       userMessage.includes('안돼') || userMessage.includes('안됨') || 
                       userMessage.includes('고장') || userMessage.includes('실패')
      const isSearch = userMessage.includes('검색') || userMessage.includes('찾아') || userMessage.includes('search')
      
      // 먼저 일반 채팅 API 호출
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      const data = await response.json()
      const elapsedMs = Math.round(performance.now() - startTime)

      // 웹 검색 트리거 확인
      if (data.trigger_web_search || (hasProblem && data.answer.includes('웹에서 검색'))) {
        // 웹 검색 API 호출
        const searchResponse = await fetch('/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessage }),
        })

        const searchData = await searchResponse.json()
        
        // 결합된 메시지 생성
        const combinedMessage = (
          <div>
            <p><strong>{data.answer}</strong></p>
            <div style={{marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '5px'}}>
              <h4>🌐 웹 검색 결과:</h4>
              {searchData.search_results && searchData.search_results.map((result, index) => (
                <div key={index} style={{ 
                  border: '1px solid #ddd', 
                  padding: '8px', 
                  margin: '5px 0', 
                  borderRadius: '5px',
                  backgroundColor: result.status === 'success' ? '#f0f8ff' : '#fff0f0'
                }}>
                  <strong>{result.engine}:</strong>
                  <div style={{fontSize: '12px', color: '#666', marginTop: '3px'}}>
                    {result.status === 'success' ? (
                      <a href={result.url} target="_blank" rel="noopener noreferrer" style={{color: '#007bff', textDecoration: 'none'}}>
                        🔗 {result.url}
                      </a>
                    ) : (
                      <span style={{color: '#dc3545'}}>{result.message}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
        
        setMessages(prev => [...prev, {
          text: combinedMessage,
          isUser: false,
          category: 'combined_search',
          confidence: Math.max(data.confidence, searchData.confidence || 0.8),
          responseTime: elapsedMs
        }])
      } else if (isSearch) {
        // 일반 검색 요청
        const searchResponse = await fetch('/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessage }),
        })

        const searchData = await searchResponse.json()
        
        const searchMessage = (
          <div>
            <p><strong>{searchData.answer}</strong></p>
            <div style={{marginTop: '10px'}}>
              <h4>🔍 검색 결과:</h4>
              {searchData.search_results.map((result, index) => (
                <div key={index} style={{ 
                  border: '1px solid #ddd', 
                  padding: '8px', 
                  margin: '5px 0', 
                  borderRadius: '5px',
                  backgroundColor: result.status === 'success' ? '#f0f8ff' : '#fff0f0'
                }}>
                  <strong>{result.engine}:</strong>
                  <div style={{fontSize: '12px', color: '#666'}}>
                    {result.status === 'success' ? (
                      <a href={result.url} target="_blank" rel="noopener noreferrer" style={{color: '#007bff', textDecoration: 'none'}}>
                        🔗 {result.url}
                      </a>
                    ) : (
                      <span style={{color: '#dc3545'}}>{result.message}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
        
        setMessages(prev => [...prev, {
          text: searchMessage,
          isUser: false,
          category: searchData.category,
          confidence: searchData.confidence,
          responseTime: elapsedMs
        }])
      } else {
        // 일반 채팅 응답
        setMessages(prev => [...prev, {
          text: data.answer,
          isUser: false,
          category: data.category,
          confidence: data.confidence,
          responseTime: elapsedMs
        }])
      }
    } catch (error) {
      const elapsedMs = Math.round(performance.now() - startTime)
      setMessages(prev => [...prev, { text: '오류가 발생했습니다. 다시 시도해주세요.', isUser: false, responseTime: elapsedMs }])
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
    <div className="app">
      {authLoading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>인증 확인 중...</p>
        </div>
      ) : isLogin ? (
        <div className="auth-container">
          <div className="auth-card">
            <h1 className="logo">SubBot 💬</h1>
            <h2>{isLogin ? '로그인' : '회원가입'}</h2>
            
            {error && <div className="error-message">{error}</div>}
            
            <form className="auth-form" onSubmit={isLogin ? handleLogin : handleRegister}>
              <div className="form-group">
                <label>
                  {isLogin ? '이메일' : '이메일'}
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="이메일을 입력하세요"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>
                  {isLogin ? '비밀번호' : '비밀번호'}
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="비밀번호를 입력하세요"
                  required
                />
              </div>
              
              {!isLogin && (
                <div className="form-group">
                  <label>이름</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="이름을 입력하세요"
                    required
                  />
                </div>
              )}
              
              {isLogin && (
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={rememberLogin}
                      onChange={(e) => setRememberLogin(e.target.checked)}
                    />
                    로그인 유지
                  </label>
                </div>
              )}
              
              <button type="submit" className="auth-button" disabled={authLoading}>
                {authLoading ? '처리 중...' : (isLogin ? '로그인' : '회원가입')}
              </button>
            </form>
            
            <div className="divider">
              <span>{isLogin ? '또는' : '이미'} 계정이 {isLogin ? '있으신가요?' : '있으신가요?'}</span>
            </div>
            
            <button 
              className="toggle-button" 
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? '회원가입' : '로그인'}
            </button>
          </div>
        </div>
      ) : (
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
                  <div className={`message-content ${!msg.isUser && (String(msg.text).includes('📦') || String(msg.text).includes('🔍')) ? 'product-message' : ''}`}>{msg.text}</div>
                  {!msg.isUser && msg.responseTime !== undefined && (
                    <div className="message-meta">
                      응답 시간: {formatResponseTime(msg.responseTime)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
          
          <div className="input-container">
            <input
              className="message-input"
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
            />
            <button className="send-button" onClick={sendMessage} disabled={isLoading}>
              {isLoading ? '전송 중...' : '전송'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
