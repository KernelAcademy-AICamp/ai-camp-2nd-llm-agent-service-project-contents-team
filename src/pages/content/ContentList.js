import React, { useState } from 'react';
import './ContentList.css';

function ContentList() {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const contents = [
    {
      id: 1,
      title: '신제품 런칭 홍보 콘텐츠',
      type: '소셜 미디어',
      platform: 'Instagram',
      status: '발행됨',
      date: '2025-11-10',
      views: 1250,
    },
    {
      id: 2,
      title: '할인 이벤트 안내',
      type: '블로그',
      platform: 'Naver Blog',
      status: '예약됨',
      date: '2025-11-15',
      views: 0,
    },
    {
      id: 3,
      title: '고객 리뷰 소개 영상',
      type: '비디오',
      platform: 'YouTube',
      status: '작성 중',
      date: '2025-11-12',
      views: 0,
    },
    {
      id: 4,
      title: '신규 서비스 소개',
      type: '소셜 미디어',
      platform: 'Facebook',
      status: '발행됨',
      date: '2025-11-08',
      views: 890,
    },
    {
      id: 5,
      title: '월간 뉴스레터',
      type: '이메일',
      platform: 'Newsletter',
      status: '발행됨',
      date: '2025-11-01',
      views: 2300,
    },
  ];

  const filterOptions = [
    { id: 'all', label: '전체' },
    { id: '발행됨', label: '발행됨' },
    { id: '예약됨', label: '예약됨' },
    { id: '작성 중', label: '작성 중' },
  ];

  const filteredContents = contents.filter((content) => {
    const matchesFilter = filter === 'all' || content.status === filter;
    const matchesSearch =
      content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      content.type.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  // 필터별 카운트
  const filterCounts = {
    all: contents.length,
    '발행됨': contents.filter(c => c.status === '발행됨').length,
    '예약됨': contents.filter(c => c.status === '예약됨').length,
    '작성 중': contents.filter(c => c.status === '작성 중').length,
  };

  return (
    <div className="content-list-page">
      <div className="list-header">
        <div className="header-left">
          <h2>콘텐츠 관리</h2>
          <p className="header-subtitle">생성된 콘텐츠를 관리하고 발행 상태를 확인하세요</p>
        </div>
        <button className="btn-primary">+ 새 콘텐츠 만들기</button>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        {filterOptions.map((option) => (
          <button
            key={option.id}
            className={`tab-btn ${filter === option.id ? 'active' : ''}`}
            onClick={() => setFilter(option.id)}
          >
            {option.label} <span className="tab-count">{filterCounts[option.id]}</span>
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

      <div className="content-table-container">
        <table className="content-table">
          <thead>
            <tr>
              <th>제목</th>
              <th>유형</th>
              <th>플랫폼</th>
              <th>상태</th>
              <th>날짜</th>
              <th>조회수</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            {filteredContents.map((content) => (
              <tr key={content.id}>
                <td className="content-title-cell">
                  <strong>{content.title}</strong>
                </td>
                <td>{content.type}</td>
                <td>{content.platform}</td>
                <td>
                  <span className={`status-badge status-${content.status}`}>
                    {content.status}
                  </span>
                </td>
                <td>{content.date}</td>
                <td>{content.views.toLocaleString()}</td>
                <td>
                  <div className="action-buttons-cell">
                    <button className="action-btn-small" title="수정">
                      ✏️
                    </button>
                    <button className="action-btn-small" title="복제">
                      📋
                    </button>
                    <button className="action-btn-small" title="삭제">
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredContents.length === 0 && (
          <div className="empty-state">
            <h3>콘텐츠가 없습니다</h3>
            <p>새 콘텐츠를 만들어 시작하세요</p>
            <button className="btn-primary">+ 첫 콘텐츠 만들기</button>
          </div>
        )}
      </div>

      <div className="pagination">
        <button className="pagination-btn">이전</button>
        <div className="page-numbers">
          <button className="page-number active">1</button>
          <button className="page-number">2</button>
          <button className="page-number">3</button>
        </div>
        <button className="pagination-btn">다음</button>
      </div>
    </div>
  );
}

export default ContentList;
