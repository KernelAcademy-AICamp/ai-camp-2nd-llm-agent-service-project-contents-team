import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiTrash2, FiArrowLeft, FiEdit3, FiDownload } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { contentSessionAPI, generatedVideoAPI } from '../../services/api';
import './ContentHistory.css';

// ========== 상수 정의 ==========
const STYLES = [
  { id: 'casual', label: '캐주얼' },
  { id: 'professional', label: '전문적' },
  { id: 'friendly', label: '친근한' },
  { id: 'formal', label: '격식체' },
  { id: 'trendy', label: '트렌디' },
  { id: 'luxurious', label: '럭셔리' },
  { id: 'cute', label: '귀여운' },
  { id: 'minimal', label: '미니멀' },
];

// ========== 유틸리티 함수 ==========
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  const yy = String(date.getFullYear()).slice(-2);
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yy}/${mm}/${dd} ${hh}:${min}`;
};

const formatDateDetail = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const isCurrentYear = date.getFullYear() === now.getFullYear();
  const hours = date.getHours();
  const ampm = hours < 12 ? '오전' : '오후';
  const h12 = hours % 12 || 12;
  const min = String(date.getMinutes()).padStart(2, '0');

  const timeStr = `${ampm} ${h12}:${min}`;
  if (isCurrentYear) {
    return `${date.getMonth() + 1}월 ${date.getDate()}일 ${timeStr}`;
  }
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 ${timeStr}`;
};

const copyToClipboard = (text, message) => {
  navigator.clipboard.writeText(text);
  alert(message);
};

const getStyleLabel = (styleId) => STYLES.find(s => s.id === styleId)?.label || styleId;

// ========== 서브 컴포넌트 ==========
const ResultCard = ({ title, children, onCopy }) => (
  <div className="result-card">
    <div className="result-card-header">
      <h3>{title}</h3>
      {onCopy && (
        <div className="result-card-actions">
          <button className="btn-icon" onClick={onCopy} title="복사">
            <FiCopy />
          </button>
        </div>
      )}
    </div>
    <div className="result-card-content">{children}</div>
  </div>
);

const TagList = ({ tags, isHashtag = false }) => (
  <div className="result-tags">
    {tags?.map((tag, idx) => (
      <span key={idx} className={`tag-item ${isHashtag ? 'hashtag' : ''}`}>{tag}</span>
    ))}
  </div>
);

const PlatformContent = ({ platform, data, onCopy }) => {
  if (!data) return null;

  const config = {
    blog: { title: '네이버 블로그', tagsKey: 'tags', isHashtag: false },
    sns: { title: 'Instagram / Facebook', tagsKey: 'hashtags', isHashtag: true },
    x: { title: 'X', tagsKey: 'hashtags', isHashtag: true },
    threads: { title: 'Threads', tagsKey: 'hashtags', isHashtag: true },
  };

  const { title, tagsKey, isHashtag } = config[platform];
  const tags = data[tagsKey] || data.tags;

  return (
    <ResultCard title={title} onCopy={onCopy}>
      {platform === 'blog' && <div className="blog-title">{data.title}</div>}
      {platform === 'blog' ? (
        <div className="text-result markdown-content">
          <ReactMarkdown remarkPlugins={[remarkBreaks]}>{data.content}</ReactMarkdown>
        </div>
      ) : (
        <div className="text-result sns-content">
          {data.content}
        </div>
      )}
      <TagList tags={tags} isHashtag={isHashtag} />
    </ResultCard>
  );
};

// ========== 메인 컴포넌트 ==========
function ContentHistory() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [historyDetailTab, setHistoryDetailTab] = useState('blog');
  const [popupImage, setPopupImage] = useState(null);
  const [filterType, setFilterType] = useState('all'); // all, content, video

  // ========== 히스토리 관련 함수 ==========
  const fetchHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      // 콘텐츠와 비디오 데이터 동시 로드
      const [contentData, videoData] = await Promise.all([
        contentSessionAPI.list(0, 50),
        generatedVideoAPI.list(0, 50)
      ]);

      // 두 데이터를 통합하고 시간순 정렬
      const contentItems = contentData.map(item => ({ ...item, type: 'content' }));
      const videoItems = videoData.map(item => ({ ...item, type: 'video' }));

      const allItems = [...contentItems, ...videoItems].sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
      );

      setHistory(allItems);
    } catch (error) {
      console.error('생성 내역 로드 실패:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSelectHistory = async (item) => {
    try {
      const fullData = await contentSessionAPI.get(item.id);
      setSelectedHistoryItem(fullData);
      if (fullData.blog) setHistoryDetailTab('blog');
      else if (fullData.sns) setHistoryDetailTab('sns');
      else if (fullData.x) setHistoryDetailTab('x');
      else if (fullData.threads) setHistoryDetailTab('threads');
      else if (fullData.cardnews) setHistoryDetailTab('cardnews');
      if (item.type === 'video') {
        // 비디오 아이템은 이미 모든 데이터를 가지고 있음
        setSelectedHistoryItem(item);
        setHistoryDetailTab('video');
      } else {
        // 콘텐츠 아이템은 상세 데이터 로드
        const fullData = await contentSessionAPI.get(item.id);
        setSelectedHistoryItem(fullData);
        if (fullData.blog) setHistoryDetailTab('blog');
        else if (fullData.sns) setHistoryDetailTab('sns');
        else if (fullData.x) setHistoryDetailTab('x');
        else if (fullData.threads) setHistoryDetailTab('threads');
      }
    } catch (error) {
      console.error('상세 데이터 조회 실패:', error);
      setSelectedHistoryItem(item);
    }
  };

  const handleDeleteHistory = async (id) => {
    if (!window.confirm('이 생성 내역을 삭제하시겠습니까?')) return;
    try {
      await contentSessionAPI.delete(id);
      setHistory(prev => prev.filter(item => item.id !== id));
      if (selectedHistoryItem?.id === id) {
        setSelectedHistoryItem(null);
      }
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  const handleCopyBlog = (item) => {
    const blog = item.blog;
    if (!blog) return;
    const text = `${blog.title}\n\n${blog.content}\n\n${(blog.tags || []).join(' ')}`;
    copyToClipboard(text, '블로그 콘텐츠가 복사되었습니다.');
  };

  const handleCopySNS = (item) => {
    const sns = item.sns;
    if (!sns) return;
    const text = `${sns.content}\n\n${(sns.hashtags || sns.tags || []).join(' ')}`;
    copyToClipboard(text, 'SNS 콘텐츠가 복사되었습니다.');
  };

  const handleCopyX = (item) => {
    const x = item.x;
    if (!x) return;
    const text = `${x.content}\n\n${(x.hashtags || x.tags || []).join(' ')}`;
    copyToClipboard(text, 'X 콘텐츠가 복사되었습니다.');
  };

  const handleCopyThreads = (item) => {
    const threads = item.threads;
    if (!threads) return;
    const text = `${threads.content}\n\n${(threads.hashtags || threads.tags || []).join(' ')}`;
    copyToClipboard(text, 'Threads 콘텐츠가 복사되었습니다.');
  };

  const handleDownloadImage = async (url, idx) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `generated_image_${idx + 1}.png`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('이미지 다운로드 실패:', error);
      alert('이미지 다운로드에 실패했습니다.');
    }
  };

  const handleDownloadVideo = async (url, productName) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${productName.replace(/[^a-zA-Z0-9가-힣]/g, '_')}_video.mp4`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('비디오 다운로드 실패:', error);
      alert('비디오 다운로드에 실패했습니다.');
    }
  };

  // 편집 페이지로 이동
  const handleGoToEditor = (item) => {
    // ContentEditor가 기대하는 형식으로 데이터 변환
    const result = {
      text: {
        blog: item.blog,
        sns: item.sns,
        x: item.x,
        threads: item.threads,
      },
      images: item.images?.map(img => ({ url: img.image_url })) || [],
    };

    navigate('/editor', {
      state: {
        result,
        topic: item.topic,
        sessionId: item.id,
      },
    });
  };

  // 필터링된 히스토리
  const filteredHistory = history.filter(item => {
    if (filterType === 'all') return true;
    if (filterType === 'content') return item.type === 'content';
    if (filterType === 'video') return item.type === 'video';
    return true;
  });

  return (
    <div className="content-history">
      <button className="btn-back" onClick={() => navigate('/content')}>
        <FiArrowLeft /> 돌아가기
      </button>
      <div className="history-header">
        <h2>생성 내역</h2>
        <p className="history-subtitle">이전에 생성한 콘텐츠를 확인하고 복사할 수 있습니다</p>
      </div>

      {/* 필터 탭 */}
      <div className="history-filter-tabs">
        <button
          className={`filter-tab ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => setFilterType('all')}
        >
          전체
        </button>
        <button
          className={`filter-tab ${filterType === 'content' ? 'active' : ''}`}
          onClick={() => setFilterType('content')}
        >
          텍스트 + 이미지
        </button>
        <button
          className={`filter-tab ${filterType === 'video' ? 'active' : ''}`}
          onClick={() => setFilterType('video')}
        >
          숏폼 영상
        </button>
      </div>

      <div className="history-content">
        {isLoadingHistory ? (
          <div className="loading-state">
            <span className="spinner"></span>
            <p>생성 내역을 불러오는 중...</p>
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📝</span>
            <h3>생성 내역이 없습니다</h3>
            <p>콘텐츠를 생성하면 여기에 저장됩니다.</p>
            <button className="btn-primary" onClick={() => navigate('/create')}>콘텐츠 생성하기</button>
          </div>
        ) : (
          <div className="history-layout">
            {/* 히스토리 목록 */}
            <div className="history-list">
              {filteredHistory.map(item => (
                <div
                  key={`${item.type}-${item.id}`}
                  className={`history-item ${selectedHistoryItem?.id === item.id && selectedHistoryItem?.type === item.type ? 'selected' : ''}`}
                  onClick={() => handleSelectHistory(item)}
                >
                  <div className="history-item-header">
                    <h4>{item.type === 'video' ? item.product_name : (item.topic || '주제 없음')}</h4>
                    <span className="history-date">{formatDate(item.created_at)}</span>
                  </div>
                  <div className="history-item-info">
                    <span className="info-badge type">
                      {item.content_type === 'text' ? '글만' : item.content_type === 'image' ? '이미지만' : '글+이미지'}
                    </span>
                    <span className="info-badge style">{getStyleLabel(item.style)}</span>
                  </div>
                  <div className="history-item-meta">
                    {item.blog && <span className="platform-badge">블로그</span>}
                    {item.sns && <span className="platform-badge">IG/FB</span>}
                    {item.x && <span className="platform-badge">X</span>}
                    {item.threads && <span className="platform-badge">Threads</span>}
                    {item.cardnews && <span className="platform-badge cardnews">카드뉴스</span>}
                  </div>

                  {item.type === 'content' ? (
                    <>
                      <div className="history-item-info">
                        <span className="info-badge type">
                          {item.content_type === 'text' ? '글만' : item.content_type === 'image' ? '이미지만' : '글+이미지'}
                        </span>
                        <span className="info-badge style">{getStyleLabel(item.style)}</span>
                      </div>
                      <div className="history-item-meta">
                        {item.blog && <span className="platform-badge">블로그</span>}
                        {item.sns && <span className="platform-badge">IG/FB</span>}
                        {item.x && <span className="platform-badge">X</span>}
                        {item.threads && <span className="platform-badge">Threads</span>}
                      </div>
                    </>
                  ) : (
                    <div className="history-item-info">
                      <span className="info-badge type">🎬 숏폼 영상</span>
                      <span className="info-badge style">{item.tier} · {item.duration_seconds}초</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* 히스토리 상세 */}
            <div className="history-detail">
              {selectedHistoryItem ? (
                selectedHistoryItem.type === 'video' ? (
                  /* 비디오 상세 뷰 */
                  <>
                    <div className="history-detail-header">
                      <div className="history-detail-title-row">
                        <h3>{selectedHistoryItem.product_name}</h3>
                        <div className="history-detail-actions">
                          <button
                            className="btn-icon btn-icon-download"
                            onClick={() => handleDownloadVideo(selectedHistoryItem.final_video_url, selectedHistoryItem.product_name)}
                            title="다운로드"
                          >
                            <FiDownload />
                          </button>
                        </div>
                      </div>
                      <div className="history-detail-meta">
                        <span className="info-badge type">🎬 숏폼 영상</span>
                        <span className="info-badge style">{selectedHistoryItem.tier} · {selectedHistoryItem.duration_seconds}초</span>
                        <span className="history-date">{formatDateDetail(selectedHistoryItem.created_at)}</span>
                      </div>
                    </div>

                  {/* 플랫폼 탭 */}
                  <div className="history-detail-tabs">
                    {['blog', 'sns', 'x', 'threads'].map(platform => (
                      selectedHistoryItem[platform] && (
                        <button
                          key={platform}
                          className={`history-tab ${historyDetailTab === platform ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab(platform)}
                        >
                          {platform === 'blog' ? '블로그' : platform === 'sns' ? 'IG/FB' : platform === 'threads' ? 'Threads' : 'X'}
                        </button>
                      )
                    ))}
                    {selectedHistoryItem.cardnews && (
                      <button
                        className={`history-tab ${historyDetailTab === 'cardnews' ? 'active' : ''}`}
                        onClick={() => setHistoryDetailTab('cardnews')}
                      >
                        카드뉴스 ({selectedHistoryItem.cardnews.page_count}장)
                      </button>
                    )}
                    {selectedHistoryItem.images?.length > 0 && (
                      <button
                        className={`history-tab ${historyDetailTab === 'images' ? 'active' : ''}`}
                        onClick={() => setHistoryDetailTab('images')}
                      >
                        이미지 ({selectedHistoryItem.images.length})
                      </button>
                    )}
                  </div>

                  {/* 탭 콘텐츠 */}
                  <div className="history-detail-content">
                    {historyDetailTab === 'blog' && (
                      <PlatformContent platform="blog" data={selectedHistoryItem.blog} onCopy={() => handleCopyBlog(selectedHistoryItem)} />
                    )}
                    {historyDetailTab === 'sns' && (
                      <PlatformContent platform="sns" data={selectedHistoryItem.sns} onCopy={() => handleCopySNS(selectedHistoryItem)} />
                    )}
                    {historyDetailTab === 'x' && (
                      <PlatformContent platform="x" data={selectedHistoryItem.x} onCopy={() => handleCopyX(selectedHistoryItem)} />
                    )}
                    {historyDetailTab === 'threads' && (
                      <PlatformContent platform="threads" data={selectedHistoryItem.threads} onCopy={() => handleCopyThreads(selectedHistoryItem)} />
                    )}
                    {historyDetailTab === 'cardnews' && selectedHistoryItem.cardnews && (
                      <div className="result-card result-card-full">
                        <div className="result-card-header">
                          <h3>카드뉴스 - {selectedHistoryItem.cardnews.title}</h3>
                        </div>
                        <div className="result-card-content">
                          <div className="cardnews-info">
                            <span className="info-badge">{selectedHistoryItem.cardnews.purpose === 'promotion' ? '홍보' : selectedHistoryItem.cardnews.purpose === 'menu' ? '메뉴' : selectedHistoryItem.cardnews.purpose === 'info' ? '정보' : selectedHistoryItem.cardnews.purpose === 'event' ? '이벤트' : selectedHistoryItem.cardnews.purpose}</span>
                            <span className="info-badge">{selectedHistoryItem.cardnews.page_count}페이지</span>
                          </div>
                          <div className="images-grid cardnews-grid">
                            {selectedHistoryItem.cardnews.card_image_urls?.map((url, idx) => (
                              <div key={idx} className="image-item" onClick={() => setPopupImage(url)}>
                                <img src={url} alt={`카드뉴스 ${idx + 1}페이지`} />
                                <div className="image-label">페이지 {idx + 1}</div>
                                <button
                                  className="btn-download-single"
                                  onClick={(e) => { e.stopPropagation(); handleDownloadImage(url, idx); }}
                                >
                                  다운로드
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                    {historyDetailTab === 'images' && selectedHistoryItem.images?.length > 0 && (
                    {/* 비디오 플레이어 */}
                    <div className="history-detail-content">
                      <div className="result-card result-card-full">
                        <div className="result-card-header">
                          <h3>생성된 영상</h3>
                        </div>
                        <div className="result-card-content">
                          <div className="video-player-container">
                            <video
                              controls
                              src={selectedHistoryItem.final_video_url}
                              className="generated-video-player"
                            >
                              <source src={selectedHistoryItem.final_video_url} type="video/mp4" />
                              브라우저가 비디오 재생을 지원하지 않습니다.
                            </video>
                          </div>
                          <div className="video-info">
                            <p><strong>제품명:</strong> {selectedHistoryItem.product_name}</p>
                            <p><strong>등급:</strong> {selectedHistoryItem.tier}</p>
                            <p><strong>길이:</strong> {selectedHistoryItem.duration_seconds}초</p>
                            <p><strong>세션 ID:</strong> {selectedHistoryItem.session_id}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  /* 콘텐츠 상세 뷰 */
                  <>
                    <div className="history-detail-header">
                      <div className="history-detail-title-row">
                        <h3>{selectedHistoryItem.topic}</h3>
                        <div className="history-detail-actions">
                          <button className="btn-icon btn-icon-edit" onClick={() => handleGoToEditor(selectedHistoryItem)} title="편집">
                            <FiEdit3 />
                          </button>
                          <button className="btn-icon btn-icon-delete" onClick={() => handleDeleteHistory(selectedHistoryItem.id)} title="삭제">
                            <FiTrash2 />
                          </button>
                        </div>
                      </div>
                      <div className="history-detail-meta">
                        <span className="info-badge type">
                          {selectedHistoryItem.content_type === 'text' ? '글만' : selectedHistoryItem.content_type === 'image' ? '이미지만' : '글+이미지'}
                        </span>
                        <span className="info-badge style">{getStyleLabel(selectedHistoryItem.style)}</span>
                        <span className="history-date">{formatDateDetail(selectedHistoryItem.created_at)}</span>
                      </div>
                    </div>

                    {/* 플랫폼 탭 */}
                    <div className="history-detail-tabs">
                      {['blog', 'sns', 'x', 'threads'].map(platform => (
                        selectedHistoryItem[platform] && (
                          <button
                            key={platform}
                            className={`history-tab ${historyDetailTab === platform ? 'active' : ''}`}
                            onClick={() => setHistoryDetailTab(platform)}
                          >
                            {platform === 'blog' ? '블로그' : platform === 'sns' ? 'IG/FB' : platform === 'threads' ? 'Threads' : 'X'}
                          </button>
                        )
                      ))}
                      {selectedHistoryItem.images?.length > 0 && (
                        <button
                          className={`history-tab ${historyDetailTab === 'images' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('images')}
                        >
                          이미지 ({selectedHistoryItem.images.length})
                        </button>
                      )}
                    </div>

                    {/* 탭 콘텐츠 */}
                    <div className="history-detail-content">
                      {historyDetailTab === 'blog' && (
                        <PlatformContent platform="blog" data={selectedHistoryItem.blog} onCopy={() => handleCopyBlog(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'sns' && (
                        <PlatformContent platform="sns" data={selectedHistoryItem.sns} onCopy={() => handleCopySNS(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'x' && (
                        <PlatformContent platform="x" data={selectedHistoryItem.x} onCopy={() => handleCopyX(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'threads' && (
                        <PlatformContent platform="threads" data={selectedHistoryItem.threads} onCopy={() => handleCopyThreads(selectedHistoryItem)} />
                      )}
                      {historyDetailTab === 'images' && selectedHistoryItem.images?.length > 0 && (
                        <div className="result-card result-card-full">
                          <div className="result-card-header">
                            <h3>생성된 이미지 ({selectedHistoryItem.images.length}장)</h3>
                          </div>
                          <div className="result-card-content">
                            <div className="images-grid">
                              {selectedHistoryItem.images.map((img, idx) => (
                                <div key={idx} className="image-item" onClick={() => setPopupImage(img.image_url)}>
                                  <img src={img.image_url} alt={`생성된 이미지 ${idx + 1}`} />
                                  <button
                                    className="btn-download-single"
                                    onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.image_url, idx); }}
                                  >
                                    다운로드
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )
              ) : (
                <div className="empty-detail">
                  <span className="empty-icon">👈</span>
                  <p>왼쪽에서 콘텐츠를 선택하세요</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 이미지 팝업 */}
      {popupImage && (
        <div className="image-popup-overlay" onClick={() => setPopupImage(null)}>
          <div className="image-popup-content" onClick={(e) => e.stopPropagation()}>
            <button className="image-popup-close" onClick={() => setPopupImage(null)}>✕</button>
            <img src={popupImage} alt="확대 이미지" />
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentHistory;
