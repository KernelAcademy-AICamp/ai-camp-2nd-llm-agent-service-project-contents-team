import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiTrash2, FiArrowLeft } from 'react-icons/fi';
import { contentSessionAPI } from '../../services/api';
import './ContentHistory.css';

// ========== 유틸리티 함수 ==========
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const isCurrentYear = date.getFullYear() === now.getFullYear();
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');

  if (isCurrentYear) {
    return `${date.getMonth() + 1}/${date.getDate()} ${hh}:${min}`;
  }
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} ${hh}:${min}`;
};

const copyToClipboard = (text, message) => {
  navigator.clipboard.writeText(text);
  alert(message);
};

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

const getStyleLabel = (styleId) => STYLES.find(s => s.id === styleId)?.label || styleId;

// ========== 메인 컴포넌트 ==========
function ContentHistory() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [detailTab, setDetailTab] = useState('blog');
  const [popupImage, setPopupImage] = useState(null);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await contentSessionAPI.list(0, 100);
      setHistory(data);

      // 첫 번째 아이템 상세 조회
      if (data.length > 0) {
        try {
          const firstItem = await contentSessionAPI.get(data[0].id);
          setSelectedItem(firstItem);
          if (firstItem.blog) setDetailTab('blog');
          else if (firstItem.sns) setDetailTab('sns');
          else if (firstItem.x) setDetailTab('x');
          else if (firstItem.threads) setDetailTab('threads');
        } catch {
          setSelectedItem(data[0]);
          if (data[0].blog) setDetailTab('blog');
          else if (data[0].sns) setDetailTab('sns');
          else if (data[0].x) setDetailTab('x');
          else if (data[0].threads) setDetailTab('threads');
        }
      }
    } catch (error) {
      console.error('생성 내역 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSelectItem = async (item) => {
    // 상세 데이터 조회 (list에서는 관계 데이터가 id만 포함됨)
    try {
      const fullData = await contentSessionAPI.get(item.id);
      console.log('📦 상세 데이터 조회:', fullData);
      setSelectedItem(fullData);
      // 선택된 아이템의 사용 가능한 탭 설정
      if (fullData.blog) setDetailTab('blog');
      else if (fullData.sns) setDetailTab('sns');
      else if (fullData.x) setDetailTab('x');
      else if (fullData.threads) setDetailTab('threads');
    } catch (error) {
      console.error('상세 데이터 조회 실패:', error);
      setSelectedItem(item);
      if (item.blog) setDetailTab('blog');
      else if (item.sns) setDetailTab('sns');
      else if (item.x) setDetailTab('x');
      else if (item.threads) setDetailTab('threads');
    }
  };

  const handleDeleteItem = async (id) => {
    if (!window.confirm('이 생성 내역을 삭제하시겠습니까?')) return;
    try {
      await contentSessionAPI.delete(id);
      setHistory(prev => prev.filter(item => item.id !== id));
      if (selectedItem?.id === id) {
        setSelectedItem(null);
      }
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  const handleCopyContent = (content, platform) => {
    let text = '';
    if (platform === 'blog') {
      text = `${content.title}\n\n${content.content}\n\n${(content.tags || []).join(' ')}`;
    } else {
      text = `${content.content}\n\n${(content.hashtags || content.tags || []).join(' ')}`;
    }
    copyToClipboard(text, `${platform} 콘텐츠가 복사되었습니다.`);
  };

  const renderContent = () => {
    if (!selectedItem) return null;
    const content = selectedItem[detailTab];

    // 데이터가 없으면 메시지 표시
    if (!content) {
      return (
        <div className="content-detail-body">
          <div className="no-content">이 플랫폼의 콘텐츠가 없습니다.</div>
        </div>
      );
    }

    // content 데이터 추출
    let title = '';
    let text = '';
    let tags = [];

    if (typeof content === 'string') {
      text = content;
    } else if (typeof content === 'object') {
      // title이 객체인 경우 (예: {id, title}) 처리
      if (content.title && typeof content.title === 'object') {
        title = content.title.title || '';
      } else {
        title = content.title || '';
      }
      text = content.content || '';
      tags = content.hashtags || content.tags || [];
    }

    return (
      <div className="content-detail-body">
        {detailTab === 'blog' && title && (
          <h3 className="content-title">{title}</h3>
        )}
        <div className="content-text">{text}</div>
        {tags.length > 0 && (
          <div className="content-tags">
            {tags.map((tag, idx) => (
              <span key={idx} className={`tag ${detailTab !== 'blog' ? 'hashtag' : ''}`}>
                {typeof tag === 'string' ? tag : tag.name || tag.tag || ''}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="content-history">
        <button className="btn-back" onClick={() => navigate('/content')}>
          <FiArrowLeft /> 돌아가기
        </button>
        <div className="history-header">
          <h2>생성 내역</h2>
        </div>
        <div className="loading-state">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="content-history">
      <button className="btn-back" onClick={() => navigate('/content')}>
        <FiArrowLeft /> 돌아가기
      </button>
      <div className="history-header">
        <h2>생성 내역</h2>
        <p className="history-subtitle">이전에 생성한 콘텐츠를 확인하고 복사할 수 있습니다</p>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          <p>아직 생성된 콘텐츠가 없습니다.</p>
          <button className="btn-create" onClick={() => navigate('/content')}>
            콘텐츠 생성하러 가기
          </button>
        </div>
      ) : (
        <div className="history-layout">
          {/* 좌측: 목록 */}
          <div className="history-list">
            {history.map((item) => (
              <div
                key={item.id}
                className={`history-item ${selectedItem?.id === item.id ? 'active' : ''}`}
                onClick={() => handleSelectItem(item)}
              >
                <div className="item-header">
                  <h4>{item.topic || '주제 없음'}</h4>
                  <span className="item-date">{formatDate(item.created_at)}</span>
                </div>
                <div className="item-info">
                  <span className="info-badge type">
                    {item.content_type === 'text' ? '글만' : item.content_type === 'image' ? '이미지만' : '글+이미지'}
                  </span>
                  <span className="info-badge style">{getStyleLabel(item.style)}</span>
                </div>
                <div className="item-platforms">
                  {item.blog && <span className="platform-badge">블로그</span>}
                  {item.sns && <span className="platform-badge">IG/FB</span>}
                  {item.x && <span className="platform-badge">X</span>}
                  {item.threads && <span className="platform-badge">Threads</span>}
                </div>
              </div>
            ))}
          </div>

          {/* 우측: 상세 */}
          <div className="history-detail">
            {selectedItem ? (
              <>
                <div className="detail-header">
                  <div className="detail-title-row">
                    <h3>{selectedItem.topic}</h3>
                    <button
                      className="btn-icon btn-delete"
                      onClick={() => handleDeleteItem(selectedItem.id)}
                      title="삭제"
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                  <span className="detail-date">{formatDate(selectedItem.created_at)}</span>
                </div>

                {/* 탭 버튼 */}
                <div className="detail-tabs">
                  {['blog', 'sns', 'x', 'threads'].map(platform => (
                    selectedItem[platform] && (
                      <button
                        key={platform}
                        className={`tab-btn ${detailTab === platform ? 'active' : ''}`}
                        onClick={() => setDetailTab(platform)}
                      >
                        {platform === 'blog' ? '블로그' : platform === 'sns' ? 'IG/FB' : platform === 'threads' ? 'Threads' : 'X'}
                      </button>
                    )
                  ))}
                  {selectedItem.images?.length > 0 && (
                    <button
                      className={`tab-btn ${detailTab === 'images' ? 'active' : ''}`}
                      onClick={() => setDetailTab('images')}
                    >
                      이미지 ({selectedItem.images.length})
                    </button>
                  )}
                </div>

                {/* 콘텐츠 표시 */}
                {detailTab === 'images' ? (
                  <div className="images-grid">
                    {selectedItem.images?.map((img, idx) => (
                      <div key={idx} className="image-item" onClick={() => setPopupImage(img)}>
                        <img src={img} alt={`생성 이미지 ${idx + 1}`} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                    {renderContent()}
                    <button
                      className="btn-copy"
                      onClick={() => handleCopyContent(selectedItem[detailTab], detailTab)}
                    >
                      <FiCopy /> 복사하기
                    </button>
                  </>
                )}
              </>
            ) : (
              <div className="no-selection">
                <p>좌측에서 콘텐츠를 선택하세요</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 이미지 팝업 */}
      {popupImage && (
        <div className="image-popup-overlay" onClick={() => setPopupImage(null)}>
          <div className="image-popup-content" onClick={(e) => e.stopPropagation()}>
            <button className="popup-close" onClick={() => setPopupImage(null)}>✕</button>
            <img src={popupImage} alt="확대 이미지" />
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentHistory;
