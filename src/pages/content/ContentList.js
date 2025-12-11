import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEdit3, FiCopy, FiTrash2, FiCalendar, FiX } from 'react-icons/fi';
import { publishedContentAPI } from '../../services/api';
import './ContentList.css';

// 플랫폼 설정
const PLATFORM_CONFIG = {
  blog: { name: '블로그', icon: '📝' },
  sns: { name: 'IG/FB', icon: '📷' },
  x: { name: 'X', icon: '𝕏' },
  threads: { name: 'Threads', icon: '🧵' },
};

// 상태 설정
const STATUS_CONFIG = {
  draft: { label: '작성 중', className: 'status-draft' },
  scheduled: { label: '예약됨', className: 'status-scheduled' },
  published: { label: '발행됨', className: 'status-published' },
  failed: { label: '발행 실패', className: 'status-failed' },
};

// 날짜 포맷
const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

const formatDateTime = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

function ContentList() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [contents, setContents] = useState([]);
  const [stats, setStats] = useState({ total: 0, draft: 0, scheduled: 0, published: 0 });
  const [isLoading, setIsLoading] = useState(true);

  const filterOptions = [
    { id: 'all', label: '전체' },
    { id: 'draft', label: '작성 중' },
    { id: 'scheduled', label: '예약됨' },
    { id: 'published', label: '발행됨' },
  ];

  // 데이터 로드
  const fetchContents = useCallback(async () => {
    setIsLoading(true);
    try {
      const status = filter === 'all' ? null : filter;
      const data = await publishedContentAPI.list(status, null, 0, 50);
      setContents(data);
    } catch (error) {
      console.error('콘텐츠 목록 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  // 통계 로드
  const fetchStats = useCallback(async () => {
    try {
      const data = await publishedContentAPI.getStats();
      setStats(data);
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  }, []);

  useEffect(() => {
    fetchContents();
    fetchStats();
  }, [fetchContents, fetchStats]);

  // 검색 필터링
  const filteredContents = contents.filter((content) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      content.title?.toLowerCase().includes(searchLower) ||
      content.content?.toLowerCase().includes(searchLower) ||
      PLATFORM_CONFIG[content.platform]?.name.toLowerCase().includes(searchLower)
    );
  });

  // 삭제 핸들러
  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('이 콘텐츠를 삭제하시겠습니까?')) return;

    try {
      await publishedContentAPI.delete(id);
      setContents(prev => prev.filter(c => c.id !== id));
      fetchStats(); // 통계 업데이트
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  // 예약 취소 핸들러
  const handleCancelSchedule = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('예약을 취소하시겠습니까?')) return;

    try {
      await publishedContentAPI.cancelSchedule(id);
      fetchContents(); // 목록 새로고침
      fetchStats(); // 통계 업데이트
    } catch (error) {
      console.error('예약 취소 실패:', error);
      alert('예약 취소에 실패했습니다.');
    }
  };

  // 편집 페이지로 이동
  const handleEdit = (content, e) => {
    e.stopPropagation();
    // 기존 데이터를 편집 형식으로 변환하여 전달
    const result = {
      text: {
        [content.platform]: {
          title: content.title,
          content: content.content,
          tags: content.tags,
        },
      },
      images: [], // 이미지는 별도로 로드 필요
    };

    navigate('/editor', {
      state: {
        result,
        topic: content.title || '콘텐츠 편집',
        publishedContentId: content.id,
      },
    });
  };

  // 복사 핸들러
  const handleCopy = (content, e) => {
    e.stopPropagation();
    let text = '';
    if (content.title) text += `${content.title}\n\n`;
    text += content.content;
    if (content.tags?.length > 0) {
      text += '\n\n' + content.tags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ');
    }

    navigator.clipboard.writeText(text);
    alert('콘텐츠가 복사되었습니다.');
  };

  // 콘텐츠 미리보기 (본문 일부만)
  const getContentPreview = (content, maxLength = 50) => {
    if (!content) return '';
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  // 표시할 날짜 결정
  const getDisplayDate = (content) => {
    if (content.status === 'published' && content.published_at) {
      return { label: '발행일', date: formatDate(content.published_at) };
    }
    if (content.status === 'scheduled' && content.scheduled_at) {
      return { label: '예약일', date: formatDateTime(content.scheduled_at) };
    }
    return { label: '생성일', date: formatDate(content.created_at) };
  };

  return (
    <div className="content-list-page">
      <div className="list-header">
        <div className="header-left">
          <h2>콘텐츠 관리</h2>
          <p className="header-subtitle">생성된 콘텐츠를 관리하고 발행 상태를 확인하세요</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/create')}>
          + 새 콘텐츠 만들기
        </button>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        {filterOptions.map((option) => (
          <button
            key={option.id}
            className={`tab-btn ${filter === option.id ? 'active' : ''}`}
            onClick={() => setFilter(option.id)}
          >
            {option.label}{' '}
            <span className="tab-count">
              {option.id === 'all' ? stats.total : stats[option.id] || 0}
            </span>
          </button>
        ))}
      </div>

      {/* 검색 */}
      <div className="search-container">
        <input
          type="text"
          placeholder="콘텐츠 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {isLoading ? (
        <div className="loading-state">
          <span className="spinner"></span>
          <p>콘텐츠를 불러오는 중...</p>
        </div>
      ) : filteredContents.length === 0 ? (
        <div className="empty-state">
          <h3>콘텐츠가 없습니다</h3>
          <p>
            {filter !== 'all'
              ? `${filterOptions.find(f => f.id === filter)?.label} 상태의 콘텐츠가 없습니다.`
              : '새 콘텐츠를 만들어 시작하세요'}
          </p>
          <button className="btn-primary" onClick={() => navigate('/create')}>
            + 첫 콘텐츠 만들기
          </button>
        </div>
      ) : (
        <div className="content-table-container">
          <table className="content-table">
            <thead>
              <tr>
                <th>플랫폼</th>
                <th>콘텐츠</th>
                <th>상태</th>
                <th>날짜</th>
                <th>조회수</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {filteredContents.map((content) => {
                const displayDate = getDisplayDate(content);
                return (
                  <tr key={content.id}>
                    <td>
                      <div className="platform-cell">
                        <span className="platform-icon">
                          {PLATFORM_CONFIG[content.platform]?.icon}
                        </span>
                        <span className="platform-name">
                          {PLATFORM_CONFIG[content.platform]?.name}
                        </span>
                      </div>
                    </td>
                    <td className="content-title-cell">
                      {content.title ? (
                        <>
                          <strong>{content.title}</strong>
                          <span className="content-preview">
                            {getContentPreview(content.content, 30)}
                          </span>
                        </>
                      ) : (
                        <span className="content-preview-only">
                          {getContentPreview(content.content, 60)}
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${STATUS_CONFIG[content.status]?.className}`}>
                        {STATUS_CONFIG[content.status]?.label}
                      </span>
                    </td>
                    <td>
                      <div className="date-cell">
                        <span className="date-label">{displayDate.label}</span>
                        <span className="date-value">{displayDate.date}</span>
                      </div>
                    </td>
                    <td>{content.views?.toLocaleString() || 0}</td>
                    <td>
                      <div className="action-buttons-cell">
                        <button
                          className="action-btn-small"
                          title="수정"
                          onClick={(e) => handleEdit(content, e)}
                        >
                          <FiEdit3 />
                        </button>
                        <button
                          className="action-btn-small"
                          title="복사"
                          onClick={(e) => handleCopy(content, e)}
                        >
                          <FiCopy />
                        </button>
                        {content.status === 'scheduled' && (
                          <button
                            className="action-btn-small action-btn-cancel"
                            title="예약 취소"
                            onClick={(e) => handleCancelSchedule(content.id, e)}
                          >
                            <FiX />
                          </button>
                        )}
                        <button
                          className="action-btn-small action-btn-delete"
                          title="삭제"
                          onClick={(e) => handleDelete(content.id, e)}
                        >
                          <FiTrash2 />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ContentList;
