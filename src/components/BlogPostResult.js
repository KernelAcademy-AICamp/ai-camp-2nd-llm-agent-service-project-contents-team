import React from 'react';
import ReactMarkdown from 'react-markdown';
import './BlogPostResult.css';

function BlogPostResult({ result, onEdit, onSave }) {
  if (!result) return null;

  const { title, content, tags } = result;

  return (
    <div className="blog-post-result">
      <div className="result-header">
        <h2>생성된 블로그 포스트</h2>
        <div className="result-actions">
          <button className="btn-secondary" onClick={onEdit}>
            수정하기
          </button>
          <button className="btn-primary" onClick={onSave}>
            저장하기
          </button>
        </div>
      </div>

      <div className="result-content">
        <div className="result-section">
          <h3>제목</h3>
          <div className="title-display">{title}</div>
        </div>

        <div className="result-section">
          <h3>본문</h3>
          <div className="content-display">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>

        <div className="result-section">
          <h3>태그</h3>
          <div className="tags-display">
            {tags.map((tag, index) => (
              <span key={index} className="tag">
                #{tag}
              </span>
            ))}
          </div>
        </div>

        <div className="result-info">
          <div className="info-item">
            <span className="info-label">글자 수:</span>
            <span className="info-value">{content.length}자</span>
          </div>
          <div className="info-item">
            <span className="info-label">예상 읽기 시간:</span>
            <span className="info-value">{Math.ceil(content.length / 500)}분</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BlogPostResult;
