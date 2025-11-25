import React, { useState } from 'react';
import './VideoScript.css';

function VideoScript() {
  const [formData, setFormData] = useState({
    topic: '',
    duration: '60',
    tone: 'informative',
    targetAudience: ''
  });
  const [loading, setLoading] = useState(false);
  const [generatedScript, setGeneratedScript] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setGeneratedScript(null);

    try {
      // TODO: API 호출 구현
      // 임시 더미 데이터
      await new Promise(resolve => setTimeout(resolve, 2000));

      setGeneratedScript({
        title: formData.topic,
        duration: formData.duration,
        script: `[인트로 - 0:00-0:10]
안녕하세요! 오늘은 ${formData.topic}에 대해 알아보겠습니다.

[본문 1 - 0:10-0:30]
${formData.topic}의 핵심 포인트를 살펴보면...

[본문 2 - 0:30-0:50]
이를 실제로 활용하는 방법은...

[아웃트로 - 0:50-1:00]
오늘 영상이 도움이 되셨다면 구독과 좋아요 부탁드립니다!`,
        scenes: [
          { time: '0:00-0:10', type: 'intro', description: '오프닝 멘트 및 주제 소개' },
          { time: '0:10-0:30', type: 'content', description: '핵심 내용 설명' },
          { time: '0:30-0:50', type: 'content', description: '활용 방법 안내' },
          { time: '0:50-1:00', type: 'outro', description: '마무리 멘트' }
        ]
      });
    } catch (err) {
      setError('스크립트 생성 중 오류가 발생했습니다.');
      console.error('Video script generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (generatedScript) {
      navigator.clipboard.writeText(generatedScript.script);
      alert('스크립트가 클립보드에 복사되었습니다.');
    }
  };

  const handleReset = () => {
    setGeneratedScript(null);
    setError(null);
  };

  return (
    <div className="video-script">
      <div className="page-header">
        <h1>🎥 비디오 스크립트 생성</h1>
        <p className="page-description">
          AI가 영상 콘텐츠에 최적화된 스크립트를 자동으로 생성합니다.
        </p>
      </div>

      <div className="video-script-content">
        {/* 입력 폼 */}
        {!generatedScript && (
          <div className="form-section">
            <form onSubmit={handleGenerate}>
              <div className="form-group">
                <label htmlFor="topic">영상 주제 *</label>
                <input
                  type="text"
                  id="topic"
                  name="topic"
                  value={formData.topic}
                  onChange={handleInputChange}
                  placeholder="예: 초보자를 위한 파이썬 입문"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="duration">영상 길이 (초)</label>
                <select
                  id="duration"
                  name="duration"
                  value={formData.duration}
                  onChange={handleInputChange}
                >
                  <option value="30">30초 (숏폼)</option>
                  <option value="60">1분</option>
                  <option value="120">2분</option>
                  <option value="180">3분</option>
                  <option value="300">5분</option>
                  <option value="600">10분</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="tone">톤앤매너</label>
                <select
                  id="tone"
                  name="tone"
                  value={formData.tone}
                  onChange={handleInputChange}
                >
                  <option value="informative">정보 전달형</option>
                  <option value="casual">친근한 대화형</option>
                  <option value="professional">전문가형</option>
                  <option value="entertaining">엔터테인먼트형</option>
                  <option value="educational">교육형</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="targetAudience">타겟 시청자</label>
                <input
                  type="text"
                  id="targetAudience"
                  name="targetAudience"
                  value={formData.targetAudience}
                  onChange={handleInputChange}
                  placeholder="예: 20-30대 직장인, 초보 개발자"
                />
              </div>

              <button
                type="submit"
                className="btn-generate"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    스크립트 생성 중...
                  </>
                ) : (
                  <>
                    <span>🎥</span>
                    스크립트 생성하기
                  </>
                )}
              </button>
            </form>

            {/* 기능 안내 */}
            <div className="info-box">
              <h4>📌 기능 안내</h4>
              <ul>
                <li>영상 길이에 맞는 최적화된 스크립트 생성</li>
                <li>씬(Scene)별 시간 배분 및 설명 제공</li>
                <li>선택한 톤앤매너에 맞는 대사 생성</li>
                <li>타겟 시청자에 맞춘 콘텐츠 구성</li>
              </ul>
            </div>
          </div>
        )}

        {/* 에러 메시지 */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <p>{error}</p>
          </div>
        )}

        {/* 생성 결과 */}
        {generatedScript && (
          <div className="result-section">
            <div className="result-header">
              <h3>✅ 스크립트 생성 완료!</h3>
              <div className="result-actions">
                <button onClick={handleCopy} className="btn-copy">
                  📋 복사하기
                </button>
                <button onClick={handleReset} className="btn-reset">
                  🔄 새로 만들기
                </button>
              </div>
            </div>

            <div className="script-info">
              <div className="info-item">
                <span className="info-label">제목:</span>
                <span className="info-value">{generatedScript.title}</span>
              </div>
              <div className="info-item">
                <span className="info-label">길이:</span>
                <span className="info-value">{generatedScript.duration}초</span>
              </div>
            </div>

            {/* 씬 구성 */}
            <div className="scenes-section">
              <h4>📽️ 씬 구성</h4>
              <div className="scenes-list">
                {generatedScript.scenes.map((scene, index) => (
                  <div key={index} className="scene-item">
                    <div className="scene-time">{scene.time}</div>
                    <div className="scene-content">
                      <span className="scene-type">{scene.type}</span>
                      <p className="scene-description">{scene.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 스크립트 본문 */}
            <div className="script-content">
              <h4>📝 스크립트</h4>
              <div className="script-text">
                {generatedScript.script}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default VideoScript;
