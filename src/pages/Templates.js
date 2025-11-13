import React from 'react';
import './Templates.css';

function Templates() {
  const templates = [
    { id: 1, name: '제품 소개', category: '소셜 미디어', icon: '📱', uses: 145 },
    { id: 2, name: '이벤트 홍보', category: '블로그', icon: '🎉', uses: 98 },
    { id: 3, name: '고객 후기', category: '비디오', icon: '⭐', uses: 76 },
    { id: 4, name: '신규 오픈', category: '소셜 미디어', icon: '🎊', uses: 132 },
    { id: 5, name: '할인 안내', category: '이메일', icon: '💰', uses: 189 },
    { id: 6, name: '튜토리얼', category: '비디오', icon: '📚', uses: 54 },
  ];

  return (
    <div className="templates-page">
      <div className="templates-header">
        <h2>템플릿</h2>
        <button className="btn-primary">커스텀 템플릿 만들기</button>
      </div>

      <div className="templates-grid">
        {templates.map((template) => (
          <div key={template.id} className="template-card">
            <div className="template-icon">{template.icon}</div>
            <h3>{template.name}</h3>
            <p className="template-category">{template.category}</p>
            <div className="template-footer">
              <span className="template-uses">{template.uses}회 사용됨</span>
              <button className="btn-use">사용하기</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Templates;
