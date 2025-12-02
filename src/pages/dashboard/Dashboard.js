import React from 'react';
import './Dashboard.css';

function Dashboard() {
  const stats = [
    { label: '총 콘텐츠', value: '24', change: '+12%' },
    { label: '이번 주 생성', value: '8', change: '+25%' },
    { label: '예약된 포스트', value: '12', change: '+8%' },
    { label: '총 조회수', value: '1.2K', change: '+15%' },
  ];

  const recentContents = [
    { id: 1, title: '신제품 런칭 홍보 콘텐츠', type: '소셜 미디어', status: '발행됨', date: '2025-11-10' },
    { id: 2, title: '할인 이벤트 안내', type: '블로그', status: '예약됨', date: '2025-11-15' },
    { id: 3, title: '고객 리뷰 소개 영상', type: '비디오', status: '작성 중', date: '2025-11-12' },
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>대시보드</h2>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-content">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">{stat.value}</div>
              <div className="stat-change positive">{stat.change}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-content">
        <div className="content-section">
          <h3>최근 콘텐츠</h3>
          <div className="content-list">
            {recentContents.map((content) => (
              <div key={content.id} className="content-item">
                <div className="content-info">
                  <h4>{content.title}</h4>
                  <div className="content-meta">
                    <span className="content-type">{content.type}</span>
                    <span className="content-date">{content.date}</span>
                  </div>
                </div>
                <span className={`content-status status-${content.status}`}>
                  {content.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="quick-actions">
          <h3>빠른 작업</h3>
          <div className="action-buttons">
            <button className="action-btn">
              <span>콘텐츠 생성</span>
            </button>
            <button className="action-btn">
              <span>템플릿 선택</span>
            </button>
            <button className="action-btn">
              <span>스케줄 설정</span>
            </button>
            <button className="action-btn">
              <span>분석 보기</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
