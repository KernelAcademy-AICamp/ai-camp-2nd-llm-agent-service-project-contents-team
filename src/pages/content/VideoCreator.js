import React, { useState } from 'react';
import axios from 'axios';
import './VideoCreator.css';

function VideoCreator() {
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

  return (
    <div className="video-creator">
      <div className="video-creator-header">
        <h2>🎬 AI 동영상 생성</h2>
        <p>AI를 활용하여 이미지를 동영상으로 변환하거나 텍스트로 동영상을 생성하세요</p>
      </div>

      <div className="video-creator-content">
        {/* 왼쪽: 입력 폼 */}
        <div className="video-form-section">
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
        <div className="video-result-section">
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
    </div>
  );
}

export default VideoCreator;
