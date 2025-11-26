import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import './Home.css';

function Home() {
  const { user } = useAuth();
  const location = useLocation();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 컴포넌트 마운트 시 세션 목록 로드
  useEffect(() => {
    loadSessions();
  }, []);

  // URL에서 session_id를 읽어 기존 대화 로드
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session_id');

    if (sessionId) {
      loadSessionHistory(parseInt(sessionId));
    }
  }, [location.search]);

  // 세션 목록 로드
  const loadSessions = async () => {
    try {
      setSessionsLoading(true);
      const response = await api.get('/api/chat/sessions', {
        params: { limit: 50, offset: 0 }
      });
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('세션 목록 로드 실패:', error);
    } finally {
      setSessionsLoading(false);
    }
  };

  const loadSessionHistory = async (sessionId) => {
    try {
      setIsLoadingHistory(true);

      // 최근 10개 메시지만 먼저 로드 (빠른 표시)
      const response = await api.get(`/api/chat/sessions/${sessionId}/messages`, {
        params: { limit: 10, offset: 0 }
      });

      // 메시지를 UI 형식으로 변환
      const loadedMessages = response.data.messages.map((msg, index) => ({
        id: `history-${msg.id}`,
        type: msg.role === 'user' ? 'user' : 'ai',
        content: msg.content,
        timestamp: new Date(msg.created_at),
      }));

      setMessages(loadedMessages);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('대화 내역 로드 실패:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    try {
      // AI 챗봇 API 호출
      const response = await api.post('/api/chat', {
        message: userInput,
        session_id: currentSessionId,
        history: messages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }))
      });

      // 첫 메시지인 경우 세션 ID 저장하고 세션 목록 갱신
      if (!currentSessionId && response.data.session_id) {
        setCurrentSessionId(response.data.session_id);
        loadSessions(); // 세션 목록 갱신
      }

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('AI 응답 실패:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const handleSelectSession = (sessionId) => {
    loadSessionHistory(sessionId);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const diffHours = Math.floor(diff / 3600000);
    const diffDays = Math.floor(diff / 86400000);

    if (diffHours < 1) return '방금 전';
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString('ko-KR');
  };

  const suggestedPrompts = [
    { icon: '✍️', text: '블로그 포스트 작성하기' },
    { icon: '📱', text: '소셜 미디어 콘텐츠 생성' },
    { icon: '🎨', text: '크리에이티브 아이디어 브레인스토밍' },
    { icon: '📊', text: '데이터 분석 및 인사이트' },
  ];

  return (
    <div className="home-page">
      {/* 왼쪽 채팅 히스토리 사이드바 */}
      <aside className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button onClick={handleNewChat} className="btn-new-chat-sidebar">
            ➕ 새 채팅
          </button>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="btn-toggle-sidebar"
          >
            {isSidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <div className="sidebar-sessions">
          {sessionsLoading ? (
            <div className="sidebar-loading">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="sidebar-empty">
              <p>대화 내역이 없습니다</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`sidebar-session-item ${currentSessionId === session.id ? 'active' : ''}`}
                onClick={() => handleSelectSession(session.id)}
              >
                <div className="session-title">{session.title}</div>
                <div className="session-time">{formatDate(session.updated_at)}</div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* 오른쪽 채팅 영역 */}
      <div className="chat-main">
        {isLoadingHistory ? (
        <div className="loading-history">
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <p>대화 내역을 불러오는 중...</p>
        </div>
      ) : messages.length === 0 ? (
        <div className="home-welcome">
          <div className="welcome-header">
            <div className="welcome-avatar">
              <img src="/ddukddak_colored.png" alt="로고" className="avatar-logo" />
            </div>
            <h1 className="welcome-title">
              안녕하세요, {user?.username || 'User'}님!
            </h1>
            <p className="welcome-subtitle">
              무엇을 도와드릴까요? 궁금한 것을 물어보세요.
            </p>
          </div>

          <div className="suggested-prompts">
            {suggestedPrompts.map((prompt, index) => (
              <button
                key={index}
                className="prompt-card"
                onClick={() => setInputValue(prompt.text)}
              >
                <span className="prompt-icon">{prompt.icon}</span>
                <span className="prompt-text">{prompt.text}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? (
                  <span className="user-icon">👤</span>
                ) : (
                  <img src="/ddukddak_colored.png" alt="AI" className="ai-logo-icon" />
                )}
              </div>
              <div className="message-content">
                <div className="message-text">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message ai">
              <div className="message-avatar">
                <img src="/ddukddak_colored.png" alt="AI" className="ai-logo-icon" />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

        <div className="chat-input-container">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <div className="input-wrapper">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="메시지를 입력하세요..."
                className="chat-textarea"
                rows="1"
                disabled={isLoading}
              />
            <button
              type="submit"
              className="btn-send"
              disabled={!inputValue.trim() || isLoading}
            >
              <span className="send-icon">➤</span>
            </button>
          </div>
          <p className="input-hint">
            Shift + Enter로 줄바꿈, Enter로 전송
          </p>
        </form>
        </div>
      </div>
    </div>
  );
}

export default Home;
