import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './ChatHistory.css';

function ChatHistory() {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/chat/sessions', {
        params: { limit: 50, offset: 0 }
      });
      setSessions(response.data.sessions);
      setTotal(response.data.total);
      setError(null);
    } catch (err) {
      console.error('채팅 세션 조회 실패:', err);
      setError('채팅 세션을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionMessages = async (sessionId) => {
    try {
      setMessagesLoading(true);
      const response = await api.get(`/api/chat/sessions/${sessionId}/messages`, {
        params: { limit: 100, offset: 0 }
      });
      setMessages(response.data.messages);
      setSelectedSession(sessionId);
    } catch (err) {
      console.error('메시지 조회 실패:', err);
      setError('메시지를 불러오는데 실패했습니다.');
    } finally {
      setMessagesLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const diffMinutes = Math.floor(diff / 60000);
    const diffHours = Math.floor(diff / 3600000);
    const diffDays = Math.floor(diff / 86400000);

    if (diffMinutes < 1) return '방금 전';
    if (diffMinutes < 60) return `${diffMinutes}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;

    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleBackToSessions = () => {
    setSelectedSession(null);
    setMessages([]);
  };

  if (loading) {
    return (
      <div className="chat-history-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>채팅 내역을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error && !sessions.length) {
    return (
      <div className="chat-history-page">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={fetchSessions} className="btn-retry">
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // 세션 목록 뷰
  if (!selectedSession) {
    return (
      <div className="chat-history-page">
        <div className="chat-history-header">
          <h1>💬 채팅 내역</h1>
          <p className="chat-history-subtitle">
            전체 {total}개의 대화
          </p>
        </div>

        {sessions.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">💬</span>
            <h2>채팅 내역이 없습니다</h2>
            <p>홈 화면에서 AI와 대화를 시작해보세요!</p>
          </div>
        ) : (
          <div className="sessions-list">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="session-card"
                onClick={() => fetchSessionMessages(session.id)}
              >
                <div className="session-header">
                  <h3 className="session-title">{session.title}</h3>
                  <span className="session-time">
                    {formatDate(session.updated_at)}
                  </span>
                </div>
                <div className="session-footer">
                  <span className="message-count">
                    💬 {session.message_count}개 메시지
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 메시지 뷰
  return (
    <div className="chat-history-page">
      <div className="chat-history-header">
        <button onClick={handleBackToSessions} className="btn-back">
          ← 대화 목록
        </button>
        <h1>💬 채팅 메시지</h1>
      </div>

      {messagesLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>메시지를 불러오는 중...</p>
        </div>
      ) : (
        <div className="chat-history-list">
          {messages.map((message) => (
            <div key={message.id} className={`history-message ${message.role}`}>
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? '👤 나' : '✨ AI 어시스턴트'}
                </span>
                <span className="message-time">
                  {formatDate(message.created_at)}
                </span>
              </div>
              <div className="message-content">
                {message.content}
              </div>
              {message.model && (
                <div className="message-footer">
                  <span className="message-model">
                    모델: {message.model}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChatHistory;
