import { useState } from 'react';
import axios from 'axios';
import './ContentCommon.css';
import './VideoCreator.css';

function VideoCreator() {
  // 탭 상태: 'video' (AI 동영상 생성) 또는 'script' (비디오 스크립트)
  const [activeTab, setActiveTab] = useState('video');

  // AI 동영상 생성 상태
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    prompt: '',
    model: 'stable-video-diffusion',
    source_image_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 비디오 스크립트 상태
  const [scriptFormData, setScriptFormData] = useState({
    topic: '',
    duration: '60',
    tone: 'informative',
    targetAudience: ''
  });
  const [scriptLoading, setScriptLoading] = useState(false);
  const [generatedScript, setGeneratedScript] = useState(null);
  const [scriptError, setScriptError] = useState(null);

  // AI 동영상 생성 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleModelChange = (model) => {
    setFormData(prev => ({
      ...prev,
      model
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        'http://localhost:8000/api/video/generate',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || '동영상 생성 중 오류가 발생했습니다.');
      console.error('Video generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 비디오 스크립트 핸들러
  const handleScriptInputChange = (e) => {
    const { name, value } = e.target;
    setScriptFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenerateScript = async (e) => {
    e.preventDefault();
    setScriptLoading(true);
    setScriptError(null);
    setGeneratedScript(null);

    try {
      // TODO: API 호출 구현
      // 임시 더미 데이터
      await new Promise(resolve => setTimeout(resolve, 2000));

      setGeneratedScript({
        title: scriptFormData.topic,
        duration: scriptFormData.duration,
        script: `[인트로 - 0:00-0:10]
안녕하세요! 오늘은 ${scriptFormData.topic}에 대해 알아보겠습니다.

[본문 1 - 0:10-0:30]
${scriptFormData.topic}의 핵심 포인트를 살펴보면...

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
      setScriptError('스크립트 생성 중 오류가 발생했습니다.');
      console.error('Video script generation error:', err);
    } finally {
      setScriptLoading(false);
    }
  };

  const handleCopyScript = () => {
    if (generatedScript) {
      navigator.clipboard.writeText(generatedScript.script);
      alert('스크립트가 클립보드에 복사되었습니다.');
    }
  };

  const handleResetScript = () => {
    setGeneratedScript(null);
    setScriptError(null);
  };

  return (
    <div className="content-page">
      <div className="page-header">
        <h2>AI 동영상 생성</h2>
        <p className="page-description">AI를 활용하여 동영상을 생성하거나 비디오 스크립트를 작성하세요</p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`content-tab ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => setActiveTab('video')}
        >
          동영상 생성
        </button>
        <button
          className={`content-tab ${activeTab === 'script' ? 'active' : ''}`}
          onClick={() => setActiveTab('script')}
        >
          비디오 스크립트
        </button>
      </div>

      {/* AI 동영상 생성 탭 */}
      {activeTab === 'video' && (
        <div className="content-grid">
          {/* 왼쪽: 입력 폼 */}
          <div className="form-section">
            <form onSubmit={handleSubmit}>
              {/* 기본 정보 */}
              <div className="form-group">
                <label>제목 *</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="동영상 제목을 입력하세요"
                  required
                />
              </div>

              <div className="form-group">
                <label>설명</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="동영상 설명 (선택사항)"
                  rows="3"
                />
              </div>

              {/* 모델 선택 */}
              <div className="form-group">
                <label>생성 모델 선택</label>
                <div className="model-selector">
                  <button
                    type="button"
                    className={`model-btn ${formData.model === 'stable-video-diffusion' ? 'active' : ''}`}
                    onClick={() => handleModelChange('stable-video-diffusion')}
                  >
                    <span className="model-icon">🖼️→🎬</span>
                    <div className="model-info">
                      <div className="model-name">Stable Video Diffusion</div>
                      <div className="model-desc">이미지 → 동영상 변환 (고품질)</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    className={`model-btn ${formData.model === 'text-to-video' ? 'active' : ''}`}
                    onClick={() => handleModelChange('text-to-video')}
                  >
                    <span className="model-icon">✍️→🎬</span>
                    <div className="model-info">
                      <div className="model-name">Text-to-Video (LTX)</div>
                      <div className="model-desc">텍스트 → 동영상 생성</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* 조건부 입력: Image-to-Video */}
              {formData.model === 'stable-video-diffusion' && (
                <div className="form-group">
                  <label>원본 이미지 URL *</label>
                  <input
                    type="url"
                    name="source_image_url"
                    value={formData.source_image_url}
                    onChange={handleInputChange}
                    placeholder="https://example.com/image.jpg"
                    required={formData.model === 'stable-video-diffusion'}
                  />
                  <div className="input-hint">
                    💡 이전에 생성한 AI 이미지의 URL을 붙여넣으세요
                  </div>
                </div>
              )}

              {/* 프롬프트 */}
              <div className="form-group">
                <label>프롬프트 {formData.model === 'text-to-video' ? '*' : ''}</label>
                <textarea
                  name="prompt"
                  value={formData.prompt}
                  onChange={handleInputChange}
                  placeholder={
                    formData.model === 'stable-video-diffusion'
                      ? "동영상 스타일 설명 (선택사항)"
                      : "생성할 동영상에 대한 상세한 설명을 입력하세요"
                  }
                  rows="4"
                  required={formData.model === 'text-to-video'}
                />
              </div>

              {/* 생성 버튼 */}
              <button
                type="submit"
                className="btn-generate"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    동영상 생성 중... (1-2분 소요)
                  </>
                ) : (
                  <>
                    <span>🎬</span>
                    동영상 생성하기
                  </>
                )}
              </button>
            </form>

            {/* 안내 사항 */}
            <div className="info-box">
              <h4>📌 주요 안내</h4>
              <ul>
                <li><strong>Stable Video Diffusion</strong>: 이미지를 짧은 동영상(2-4초)으로 변환</li>
                <li><strong>Text-to-Video</strong>: 텍스트 설명으로 동영상 생성 (실험적)</li>
                <li>생성 시간: 약 1-2분 소요</li>
                <li>첫 50회 무료, 이후 회당 $0.01-0.02</li>
              </ul>
            </div>
          </div>

          {/* 오른쪽: 결과 표시 */}
          <div className="result-section">
            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                <div>
                  <strong>오류 발생</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}

            {result && (
              <div className="video-result">
                <h3>✅ 동영상 생성 완료!</h3>

                <div className="result-info">
                  <div className="info-item">
                    <span className="info-label">제목:</span>
                    <span className="info-value">{result.title}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">모델:</span>
                    <span className="info-value">{result.model}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">상태:</span>
                    <span className={`status-badge ${result.status}`}>
                      {result.status}
                    </span>
                  </div>
                </div>

                {result.video_url && (
                  <div className="video-preview">
                    <video
                      src={result.video_url}
                      controls
                      autoPlay
                      loop
                      className="generated-video"
                    >
                      Your browser does not support the video tag.
                    </video>

                    <div className="video-actions">
                      <a
                        href={result.video_url}
                        download={`${result.title}.mp4`}
                        className="btn-download"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <span>⬇️</span>
                        다운로드
                      </a>
                      <button
                        onClick={() => navigator.clipboard.writeText(result.video_url)}
                        className="btn-copy"
                      >
                        <span>🔗</span>
                        URL 복사
                      </button>
                    </div>
                  </div>
                )}

                {result.status === 'failed' && (
                  <div className="error-details">
                    <strong>실패 사유:</strong>
                    <p>{result.error_message}</p>
                  </div>
                )}
              </div>
            )}

            {!result && !error && !loading && (
              <div className="placeholder-result">
                <span className="placeholder-icon">🎬</span>
                <p>동영상을 생성하면 여기에 결과가 표시됩니다</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 비디오 스크립트 탭 */}
      {activeTab === 'script' && (
        <div className="video-script-content">
          {/* 입력 폼 */}
          {!generatedScript && (
            <div className="form-section script-form">
              <form onSubmit={handleGenerateScript}>
                <div className="form-group">
                  <label htmlFor="topic">영상 주제 *</label>
                  <input
                    type="text"
                    id="topic"
                    name="topic"
                    value={scriptFormData.topic}
                    onChange={handleScriptInputChange}
                    placeholder="예: 초보자를 위한 파이썬 입문"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="duration">영상 길이 (초)</label>
                  <select
                    id="duration"
                    name="duration"
                    value={scriptFormData.duration}
                    onChange={handleScriptInputChange}
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
                    value={scriptFormData.tone}
                    onChange={handleScriptInputChange}
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
                    value={scriptFormData.targetAudience}
                    onChange={handleScriptInputChange}
                    placeholder="예: 20-30대 직장인, 초보 개발자"
                  />
                </div>

                <button
                  type="submit"
                  className="btn-generate"
                  disabled={scriptLoading}
                >
                  {scriptLoading ? (
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
          {scriptError && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <p>{scriptError}</p>
            </div>
          )}

          {/* 생성 결과 */}
          {generatedScript && (
            <div className="result-section">
              <div className="result-header">
                <h3>✅ 스크립트 생성 완료!</h3>
                <div className="result-actions">
                  <button onClick={handleCopyScript} className="btn-copy">
                    📋 복사하기
                  </button>
                  <button onClick={handleResetScript} className="btn-reset">
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
      )}
    </div>
  );
}

export default VideoCreator;
