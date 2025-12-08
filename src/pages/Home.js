import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import './Home.css';

function Home() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [followUpPrompts, setFollowUpPrompts] = useState([]);
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
      // 최신순으로 정렬 (updated_at 기준 내림차순)
      const sortedSessions = [...response.data.sessions].sort((a, b) => {
        return new Date(b.updated_at) - new Date(a.updated_at);
      });
      setSessions(sortedSessions);
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

      // 팔로우업 프롬프트 생성
      generateFollowUpPrompts(userInput, response.data.response);
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

  // 세션 삭제
  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation(); // 클릭 이벤트 전파 방지

    if (!window.confirm('이 대화를 삭제하시겠습니까?')) return;

    try {
      await api.delete(`/api/chat/sessions/${sessionId}`);

      // 삭제된 세션이 현재 보고 있는 세션이면 초기화
      if (currentSessionId === sessionId) {
        setMessages([]);
        setCurrentSessionId(null);
        setFollowUpPrompts([]);
      }

      // 세션 목록 갱신
      loadSessions();
    } catch (error) {
      console.error('세션 삭제 실패:', error);
      alert('대화 삭제에 실패했습니다.');
    }
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

  // 콘텐츠 생성 도구 바로가기
  const contentTools = [
    { label: '글 생성', path: '/ai-content' },
    { label: '이미지', path: '/image' },
    { label: '동영상', path: '/ai-video' },
  ];

  // AI 응답에서 콘텐츠 생성 관련 키워드 감지
  const shouldShowContentTools = (content) => {
    const keywords = [
      '콘텐츠', '생성', '만들', '작성', '블로그', '포스트', '게시물',
      '이미지', '사진', '그림', '동영상', '영상', '비디오',
      'SNS', '인스타', '페이스북', '유튜브', '마케팅', '홍보',
      '카드뉴스', '배너', '썸네일'
    ];
    return keywords.some(keyword => content.includes(keyword));
  };

  // 팔로우업 프롬프트 생성 함수
  const generateFollowUpPrompts = async (userMessage, aiResponse) => {
    try {
      const response = await api.post('/api/chat/follow-up-prompts', {
        user_message: userMessage,
        ai_response: aiResponse,
        user_info: user
      });

      if (response.data.prompts && response.data.prompts.length > 0) {
        setFollowUpPrompts(response.data.prompts);
      } else {
        // API가 없거나 실패시 기본 프롬프트 생성
        generateDefaultFollowUpPrompts(userMessage);
      }
    } catch (error) {
      console.error('팔로우업 프롬프트 생성 실패:', error);
      // 에러 시 기본 프롬프트 생성
      generateDefaultFollowUpPrompts(userMessage);
    }
  };

  // 기본 팔로우업 프롬프트 생성 (API 실패 시)
  const generateDefaultFollowUpPrompts = (userMessage) => {
    // 사용자 프로필 정보 추출 (문자열인지 확인)
    const getStringValue = (value) => {
      if (!value) return '';
      if (typeof value === 'string') return value;
      if (typeof value === 'object') return '';
      return String(value);
    };

    const industry = getStringValue(user?.industry) || getStringValue(user?.business_type);
    const target = getStringValue(user?.target_audience) || getStringValue(user?.target);
    const brandName = getStringValue(user?.brand_name) || getStringValue(user?.company_name);

    const industryText = industry ? `${industry} 업종` : '';
    const targetText = target ? `${target}` : '';
    const brandText = brandName ? `${brandName}` : '';

    // 사용자 메시지에서 핵심 키워드 추출
    const extractKeyTopic = (message) => {
      const stopWords = ['을', '를', '이', '가', '은', '는', '에', '의', '로', '으로', '와', '과', '도', '만', '까지', '부터', '에서', '해줘', '알려줘', '뭐야', '어떻게'];
      const words = message.split(/\s+/).filter(word => word.length > 1 && !stopWords.some(sw => word.endsWith(sw) && word.length <= sw.length + 2));
      return words.slice(0, 3).join(' ') || '이 주제';
    };
    const keyTopic = extractKeyTopic(userMessage);

    // 배열 랜덤 셔플 함수
    const shuffleArray = (array) => {
      const shuffled = [...array];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      return shuffled;
    };

    // 카테고리별 다양한 프롬프트 풀
    let promptPool = [];

    if (userMessage.includes('콘텐츠') || userMessage.includes('마케팅')) {
      promptPool = [
        industryText && targetText ? `${industryText}에서 ${targetText}을 위한 효과적인 콘텐츠 전략은 뭐야?` : `${keyTopic}에 효과적인 콘텐츠 전략을 더 자세히 알려줘`,
        brandText ? `${brandText}의 마케팅 효과를 높이는 SNS 채널별 콘텐츠 차별화 방법을 알려줘` : `SNS 채널별 콘텐츠 차별화 방법을 알려줘`,
        `${keyTopic}를 활용한 시즌별 마케팅 캠페인 아이디어를 더 알려줘`,
        `${keyTopic} 관련 경쟁사와 차별화되는 콘텐츠 전략은?`,
        `${keyTopic}로 바이럴 마케팅을 할 수 있는 방법은?`,
        `콘텐츠 성과를 측정하는 핵심 지표(KPI)를 알려줘`,
        `${keyTopic} 관련 월별 콘텐츠 캘린더 예시를 만들어줘`,
        `저예산으로 효과적인 ${keyTopic} 마케팅 방법은?`,
      ];
    } else if (userMessage.includes('이미지') || userMessage.includes('사진') || userMessage.includes('디자인')) {
      promptPool = [
        industryText && targetText ? `${industryText}에 어울리는 ${targetText} 취향의 이미지 스타일을 추천해줘` : `${keyTopic}에 어울리는 이미지 스타일을 추천해줘`,
        brandText ? `${brandText}만의 차별화된 비주얼 아이덴티티를 만드는 방법은?` : `차별화된 비주얼 아이덴티티를 만드는 방법은?`,
        `${keyTopic} 관련 이미지에 효과적인 텍스트 배치와 폰트 선택법을 알려줘`,
        `${keyTopic}에 어울리는 색상 팔레트를 추천해줘`,
        `SNS별 최적의 이미지 사이즈와 비율을 알려줘`,
        `${keyTopic} 관련 무료로 사용 가능한 이미지 소스를 알려줘`,
        `이미지 생성 AI 프롬프트 작성 팁을 알려줘`,
        `${keyTopic}를 표현하는 다양한 비주얼 컨셉 아이디어를 제안해줘`,
      ];
    } else if (userMessage.includes('영상') || userMessage.includes('동영상') || userMessage.includes('비디오')) {
      promptPool = [
        industryText && targetText ? `${industryText}에서 ${targetText}이 좋아하는 영상 콘텐츠 유형은 뭐가 있어?` : `${keyTopic} 관련 인기 있는 영상 콘텐츠 유형은 뭐가 있어?`,
        brandText ? `${brandText}를 홍보하는 30초 숏폼 영상 시나리오를 만들어줘` : `${keyTopic}를 홍보하는 30초 숏폼 영상 시나리오를 만들어줘`,
        `${keyTopic}를 소재로 한 바이럴 영상 아이디어를 더 제안해줘`,
        `틱톡/릴스에서 인기 있는 ${keyTopic} 관련 트렌드를 알려줘`,
        `영상 초반 3초에 시선을 끄는 후킹 기법을 알려줘`,
        `${keyTopic} 관련 유튜브 쇼츠 콘텐츠 아이디어 5가지를 알려줘`,
        `영상 편집 없이 쉽게 만들 수 있는 콘텐츠 형식은?`,
        `${keyTopic}를 브이로그 형식으로 제작하는 방법을 알려줘`,
      ];
    } else if (userMessage.includes('블로그') || userMessage.includes('글') || userMessage.includes('포스트')) {
      promptPool = [
        industryText && targetText ? `${industryText}에서 ${targetText}이 검색할 만한 블로그 키워드를 추천해줘` : `${keyTopic} 관련 검색량 높은 블로그 키워드를 추천해줘`,
        brandText ? `${brandText}의 전문성을 보여줄 수 있는 시리즈 글 주제를 제안해줘` : `${keyTopic}에 대한 시리즈 글 주제를 제안해줘`,
        `${keyTopic}에 대해 더 깊이 있는 내용을 다룬 글을 작성해줘`,
        `SEO에 최적화된 ${keyTopic} 블로그 글 구조를 알려줘`,
        `${keyTopic} 관련 클릭을 유도하는 제목 작성법을 알려줘`,
        `${keyTopic}를 리스티클 형식으로 작성하면 어떨까?`,
        `${keyTopic} 관련 FAQ 형식의 글을 작성해줘`,
        `독자 참여를 유도하는 CTA(행동유도) 문구 예시를 알려줘`,
      ];
    } else if (userMessage.includes('홍보') || userMessage.includes('광고') || userMessage.includes('프로모션')) {
      promptPool = [
        industryText && targetText ? `${industryText}에서 ${targetText}에게 효과적인 프로모션 전략은?` : `${keyTopic}에 효과적인 프로모션 전략은?`,
        brandText ? `${brandText}의 신규 고객 유치를 위한 이벤트 아이디어를 알려줘` : `신규 고객 유치를 위한 이벤트 아이디어를 알려줘`,
        `${keyTopic}를 활용한 저비용 고효율 홍보 방법을 더 알려줘`,
        `${keyTopic} 관련 입소문 마케팅 전략을 알려줘`,
        `시즌별 ${keyTopic} 프로모션 아이디어를 제안해줘`,
        `${keyTopic} 관련 콜라보레이션 마케팅 아이디어는?`,
        `오프라인과 온라인을 연계한 ${keyTopic} 홍보 방법은?`,
        `${keyTopic} 광고 카피라이팅 예시를 보여줘`,
      ];
    } else if (userMessage.includes('SNS') || userMessage.includes('인스타') || userMessage.includes('소셜')) {
      promptPool = [
        industryText && targetText ? `${industryText}의 ${targetText}이 활발히 활동하는 SNS 채널과 최적 게시 시간은?` : `${keyTopic} 관련 최적의 SNS 채널과 게시 시간은?`,
        brandText ? `${brandText}의 SNS 팔로워를 늘리는 구체적인 전략을 알려줘` : `SNS 팔로워를 늘리는 구체적인 전략을 알려줘`,
        `${keyTopic} 관련 SNS 해시태그와 캡션 작성 팁을 더 알려줘`,
        `${keyTopic} 관련 인스타그램 스토리 활용법을 알려줘`,
        `SNS 알고리즘에 유리한 게시물 작성법을 알려줘`,
        `${keyTopic} 관련 인플루언서 마케팅 전략을 알려줘`,
        `SNS에서 팔로워와 소통하는 효과적인 방법은?`,
        `${keyTopic} 관련 SNS 이벤트/챌린지 아이디어를 알려줘`,
      ];
    } else {
      promptPool = [
        `${keyTopic}에 대해 더 자세히 설명해줘`,
        `${keyTopic}를 실제로 적용할 수 있는 구체적인 예시를 알려줘`,
        `${keyTopic}와 관련된 추가 팁이나 주의사항이 있어?`,
        `${keyTopic}의 장단점을 비교해서 알려줘`,
        `${keyTopic}를 초보자도 쉽게 시작하는 방법은?`,
        `${keyTopic} 관련 자주 하는 실수와 해결 방법을 알려줘`,
        `${keyTopic}의 최신 트렌드를 알려줘`,
        `${keyTopic}를 더 효과적으로 활용하는 고급 팁을 알려줘`,
      ];
    }

    // 랜덤으로 섞어서 3개 선택
    const shuffledPrompts = shuffleArray(promptPool);
    setFollowUpPrompts(shuffledPrompts.slice(0, 3));
  };

  // 팔로우업 프롬프트 클릭 핸들러 (클릭 시 바로 전송)
  const handleFollowUpClick = async (prompt) => {
    setFollowUpPrompts([]);

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: prompt,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await api.post('/api/chat', {
        message: prompt,
        session_id: currentSessionId,
        history: messages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        }))
      });

      if (!currentSessionId && response.data.session_id) {
        setCurrentSessionId(response.data.session_id);
        loadSessions();
      }

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);

      generateFollowUpPrompts(prompt, response.data.response);
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

  return (
    <div className="home-page">
      {/* 왼쪽 채팅 히스토리 사이드바 */}
      <aside className={`chat-sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          {isSidebarOpen && (
            <button onClick={handleNewChat} className="btn-new-chat-sidebar">
              새 채팅
            </button>
          )}
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
                <div className="session-info">
                  <div className="session-title">{session.title}</div>
                  <div className="session-time">{formatDate(session.updated_at)}</div>
                </div>
                <button
                  className="session-delete-btn"
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  title="대화 삭제"
                >
                  ✕
                </button>
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
            <p className="welcome-subtitle">
              궁금한 점이 있으시면 언제든 물어보세요!
            </p>
          </div>

          {/* 가이드 질문 버튼들 */}
          <div className="guide-prompts">
            <p className="guide-prompts-label">이런 것들을 물어보세요</p>
            <div className="guide-prompts-grid">
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('이 서비스는 어떻게 사용하나요?')}
              >
                <span className="guide-icon">🚀</span>
                <span className="guide-text">서비스 시작하기</span>
              </button>
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('AI로 글을 생성하고 싶어요')}
              >
                <span className="guide-icon">✍️</span>
                <span className="guide-text">AI 글 생성하기</span>
              </button>
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('AI 이미지는 어떻게 만드나요?')}
              >
                <span className="guide-icon">🎨</span>
                <span className="guide-text">AI 이미지 만들기</span>
              </button>
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('SNS 계정 연동은 어떻게 하나요?')}
              >
                <span className="guide-icon">🔗</span>
                <span className="guide-text">SNS 연동하기</span>
              </button>
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('AI 동영상은 어떻게 만드나요?')}
              >
                <span className="guide-icon">🎬</span>
                <span className="guide-text">AI 동영상 만들기</span>
              </button>
              <button
                className="guide-prompt-btn"
                onClick={() => handleFollowUpClick('템플릿은 어떻게 사용하나요?')}
              >
                <span className="guide-icon">📋</span>
                <span className="guide-text">템플릿 사용법</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'ai' && (
                  <img src="/ddukddak_colored.png" alt="AI" className="ai-logo-icon" />
                )}
              </div>
              <div className="message-content">
                <div className="message-text">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                {/* AI 응답에 콘텐츠 생성 관련 내용이 있으면 도구 버튼 표시 */}
                {message.type === 'ai' && shouldShowContentTools(message.content) && (
                  <div className="content-tools-bar">
                    <span className="tools-label">도구 제안:</span>
                    {contentTools.map((tool, idx) => (
                      <button
                        key={idx}
                        className="tool-btn"
                        onClick={() => navigate(tool.path)}
                        title={tool.label}
                      >
                        <span className="tool-label">{tool.label}</span>
                      </button>
                    ))}
                  </div>
                )}
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
          {/* 팔로우업 프롬프트 추천 */}
          {followUpPrompts.length > 0 && messages.length > 0 && (
            <div className="follow-up-prompts">
              <span className="follow-up-label">이런 질문은 어떨까요?</span>
              <div className="follow-up-buttons">
                {followUpPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    className="follow-up-btn"
                    onClick={() => handleFollowUpClick(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
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
              전송
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
