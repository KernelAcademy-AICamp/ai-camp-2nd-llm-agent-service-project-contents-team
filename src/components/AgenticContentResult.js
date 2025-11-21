import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './AgenticContentResult.css';

function AgenticContentResult({ result, onEdit, onSave }) {
  const [activeTab, setActiveTab] = useState('blog');

  if (!result) return null;

  const { blog, sns, analysis, critique, metadata } = result;

  // 점수에 따른 색상 결정
  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  // 점수에 따른 등급
  const getScoreGrade = (score) => {
    if (score >= 90) return '우수';
    if (score >= 80) return '양호';
    if (score >= 70) return '보통';
    return '개선필요';
  };

  return (
    <div className="agentic-content-result">
      <div className="result-header">
        <div className="header-left">
          <h2>AI 생성 결과</h2>
          <div className="metadata-badges">
            <span className="badge badge-attempts">
              생성 시도: {metadata.attempts + 1}회
            </span>
            <span className="badge badge-score" style={{
              backgroundColor: getScoreColor(metadata.finalScores.blog),
              color: 'white'
            }}>
              블로그 점수: {metadata.finalScores.blog}점
            </span>
            <span className="badge badge-score" style={{
              backgroundColor: getScoreColor(metadata.finalScores.sns),
              color: 'white'
            }}>
              SNS 점수: {metadata.finalScores.sns}점
            </span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={onEdit}>
            다시 생성
          </button>
          <button className="btn-primary" onClick={onSave}>
            저장하기
          </button>
        </div>
      </div>

      {/* 분석 정보 섹션 */}
      {analysis && (
        <div className="analysis-section">
          <h3>AI 분석 결과</h3>
          <div className="analysis-grid">
            <div className="analysis-item">
              <span className="analysis-label">주제:</span>
              <span className="analysis-value">{analysis.subject}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">카테고리:</span>
              <span className="analysis-value">{analysis.category}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">타겟 고객:</span>
              <span className="analysis-value">{analysis.targetAudience.join(', ')}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">분위기:</span>
              <span className="analysis-value">{analysis.mood}</span>
            </div>
            <div className="analysis-item">
              <span className="analysis-label">추천 톤:</span>
              <span className="analysis-value">{analysis.recommendedTone}</span>
            </div>
            {analysis.visualInfo && (
              <div className="analysis-item full-width">
                <span className="analysis-label">비주얼 분석:</span>
                <span className="analysis-value">{analysis.visualInfo}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`tab-button ${activeTab === 'blog' ? 'active' : ''}`}
          onClick={() => setActiveTab('blog')}
        >
          <span className="tab-icon">📝</span>
          네이버 블로그
        </button>
        <button
          className={`tab-button ${activeTab === 'sns' ? 'active' : ''}`}
          onClick={() => setActiveTab('sns')}
        >
          <span className="tab-icon">📱</span>
          인스타그램/페이스북
        </button>
      </div>

      {/* 블로그 콘텐츠 */}
      {activeTab === 'blog' && (
        <div className="content-panel">
          <div className="content-section">
            <div className="section-header">
              <h3>제목</h3>
              <span className="quality-badge" style={{
                backgroundColor: getScoreColor(critique.blog.score)
              }}>
                {getScoreGrade(critique.blog.score)} ({critique.blog.score}점)
              </span>
            </div>
            <div className="title-display">{blog.title}</div>
          </div>

          <div className="content-section">
            <h3>본문</h3>
            <div className="content-display markdown-content">
              <ReactMarkdown>{blog.content}</ReactMarkdown>
            </div>
            <div className="content-stats">
              <span>글자 수: {blog.content.length}자</span>
              <span>예상 읽기 시간: {Math.ceil(blog.content.length / 500)}분</span>
            </div>
          </div>

          <div className="content-section">
            <h3>태그</h3>
            <div className="tags-display">
              {blog.tags.map((tag, index) => (
                <span key={index} className="tag tag-blog">
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          {/* 블로그 평가 상세 */}
          {critique && critique.blog && (
            <div className="critique-section">
              <h3>품질 평가</h3>
              <div className="critique-scores">
                <div className="score-item">
                  <span className="score-label">SEO 점수:</span>
                  <span className="score-value">{critique.blog.seoScore}점</span>
                </div>
                <div className="score-item">
                  <span className="score-label">가독성 점수:</span>
                  <span className="score-value">{critique.blog.readabilityScore}점</span>
                </div>
              </div>
              {critique.blog.strengths && critique.blog.strengths.length > 0 && (
                <div className="feedback-box strengths">
                  <h4>강점</h4>
                  <ul>
                    {critique.blog.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              {critique.blog.weaknesses && critique.blog.weaknesses.length > 0 && (
                <div className="feedback-box weaknesses">
                  <h4>약점</h4>
                  <ul>
                    {critique.blog.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SNS 콘텐츠 */}
      {activeTab === 'sns' && (
        <div className="content-panel">
          <div className="content-section">
            <div className="section-header">
              <h3>SNS 본문</h3>
              <span className="quality-badge" style={{
                backgroundColor: getScoreColor(critique.sns.score)
              }}>
                {getScoreGrade(critique.sns.score)} ({critique.sns.score}점)
              </span>
            </div>
            <div className="sns-content-display">
              {sns.content}
            </div>
            <div className="content-stats">
              <span>글자 수: {sns.content.length}자</span>
            </div>
          </div>

          <div className="content-section">
            <h3>해시태그</h3>
            <div className="tags-display">
              {sns.tags.map((tag, index) => (
                <span key={index} className="tag tag-sns">
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          {/* SNS 평가 상세 */}
          {critique && critique.sns && (
            <div className="critique-section">
              <h3>품질 평가</h3>
              <div className="critique-scores">
                <div className="score-item">
                  <span className="score-label">참여도 점수:</span>
                  <span className="score-value">{critique.sns.engagementScore}점</span>
                </div>
                <div className="score-item">
                  <span className="score-label">해시태그 점수:</span>
                  <span className="score-value">{critique.sns.hashtagScore}점</span>
                </div>
              </div>
              {critique.sns.strengths && critique.sns.strengths.length > 0 && (
                <div className="feedback-box strengths">
                  <h4>강점</h4>
                  <ul>
                    {critique.sns.strengths.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              {critique.sns.weaknesses && critique.sns.weaknesses.length > 0 && (
                <div className="feedback-box weaknesses">
                  <h4>약점</h4>
                  <ul>
                    {critique.sns.weaknesses.map((weakness, index) => (
                      <li key={index}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AgenticContentResult;
