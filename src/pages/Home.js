import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Home.css';

function Home() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: '안녕하세요! 저는 AI 어시스턴트입니다. 어떻게 도와드릴까요?',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestedPrompts = [
    { icon: '✍️', text: '블로그 포스트 작성하기' },
    { icon: '📱', text: '소셜 미디어 콘텐츠 생성' },
    { icon: '🎨', text: '크리에이티브 아이디어 브레인스토밍' },
    { icon: '📊', text: '데이터 분석 및 인사이트' },
  ];

  return (
    <div className="home-page">
      {messages.length === 0 ? (
        <div className="home-welcome">
          <div className="welcome-header">
            <div className="welcome-avatar">
              <span className="avatar-icon">✨</span>
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
                  <span className="ai-icon">✨</span>
                )}
              </div>
              <div className="message-content">
                <div className="message-text">{message.content}</div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message ai">
              <div className="message-avatar">
                <span className="ai-icon">✨</span>
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
  );
}

export default Home;
