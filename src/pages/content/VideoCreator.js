import { useState, useEffect } from 'react';
import axios from 'axios';
import './ContentCommon.css';
import './VideoCreator.css';

function VideoCreator() {
  // 탭 상태: 'video' (AI 동영상 생성), 'script' (비디오 스크립트), 'history' (생성 히스토리)
  const [activeTab, setActiveTab] = useState('video');

  // AI 동영상 생성 상태
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    prompt: '',
    model: 'wan-2.1',  // 기본값을 Wan 2.1 모델로 변경
    source_image_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [translatedPrompt, setTranslatedPrompt] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);  // 업로드된 이미지 (base64)

  // 생성 히스토리 상태
  const [videoHistory, setVideoHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 히스토리 탭 진입 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history') {
      loadVideoHistory();
    }
  }, [activeTab]);

  // 비디오 히스토리 로드
  const loadVideoHistory = async () => {
    setHistoryLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        'http://localhost:8000/api/video/list',
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setVideoHistory(response.data);
    } catch (err) {
      console.error('Failed to load video history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 비디오 삭제
  const handleDeleteVideo = async (videoId) => {
    if (!window.confirm('이 동영상을 삭제하시겠습니까?')) return;

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(
        `http://localhost:8000/api/video/${videoId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      // 목록 새로고침
      loadVideoHistory();
    } catch (err) {
      console.error('Failed to delete video:', err);
      alert('동영상 삭제에 실패했습니다.');
    }
  };

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
    // 모델 변경 시 업로드된 이미지 초기화
    if (model !== 'stable-video-diffusion') {
      setUploadedImage(null);
    }
  };

  // 이미지 파일 업로드 핸들러
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 파일 크기 체크 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('이미지 파일은 10MB 이하로 업로드해주세요.');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setUploadedImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setTranslatedPrompt(null);

    try {
      const token = localStorage.getItem('access_token');

      // 무료 모델인 경우 다른 API 사용
      if (formData.model === 'wan-2.1') {
        const response = await axios.post(
          'http://localhost:8000/api/video/generate-free',
          {
            prompt: formData.prompt,
            title: formData.title || 'AI 생성 동영상',
            description: formData.description || null
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        setResult({
          title: response.data.title,
          video_url: response.data.video_url,
          status: 'completed',
          model: 'wan-2.1'
        });

        if (response.data.translated_prompt) {
          setTranslatedPrompt(response.data.translated_prompt);
        }
      } else if (formData.model === 'stable-video-diffusion' && uploadedImage) {
        // 업로드된 이미지로 동영상 생성
        const response = await axios.post(
          'http://localhost:8000/api/video/generate-from-image',
          {
            title: formData.title || 'AI 생성 동영상',
            description: formData.description || null,
            prompt: formData.prompt || null,
            image_data: uploadedImage
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            timeout: 180000  // 3분 타임아웃
          }
        );

        setResult({
          title: response.data.title,
          video_url: response.data.video_url,
          status: response.data.status,
          model: 'stable-video-diffusion'
        });
      } else {
        // 기존 Replicate API (URL 기반)
        const response = await axios.post(
          'http://localhost:8000/api/video/generate',
          formData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            timeout: 180000  // 3분 타임아웃
          }
        );

        setResult(response.data);
      }
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
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        'http://localhost:8000/api/video/generate-script',
        {
          topic: scriptFormData.topic,
          duration: parseInt(scriptFormData.duration),
          tone: scriptFormData.tone,
          target_audience: scriptFormData.targetAudience || null
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setGeneratedScript({
        title: response.data.title,
        duration: response.data.duration,
        script: response.data.script,
        scenes: response.data.scenes,
        hashtags: response.data.hashtags || [],
        thumbnailIdeas: response.data.thumbnail_ideas || []
      });
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '스크립트 생성 중 오류가 발생했습니다.';
      setScriptError(errorMessage);
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
        <button
          className={`content-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          생성 히스토리
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
                    className={`model-btn ${formData.model === 'wan-2.1' ? 'active' : ''}`}
                    onClick={() => handleModelChange('wan-2.1')}
                  >
                    <span className="model-icon">🎬</span>
                    <div className="model-info">
                      <div className="model-name">Wan 2.1 (저렴)</div>
                      <div className="model-desc">텍스트 → 동영상 (한글 지원, ~$0.01)</div>
                    </div>
                  </button>

                  <button
                    type="button"
                    className={`model-btn ${formData.model === 'stable-video-diffusion' ? 'active' : ''}`}
                    onClick={() => handleModelChange('stable-video-diffusion')}
                  >
                    <span className="model-icon">🖼️</span>
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
                    <span className="model-icon">✍️</span>
                    <div className="model-info">
                      <div className="model-name">Text-to-Video (LTX)</div>
                      <div className="model-desc">텍스트 → 동영상 생성 (Replicate)</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* 조건부 입력: Image-to-Video */}
              {formData.model === 'stable-video-diffusion' && (
                <div className="form-group">
                  <label>원본 이미지 *</label>

                  {/* 이미지 업로드 영역 */}
                  <div className="image-upload-section">
                    <label htmlFor="video-image-upload" className="image-upload-label">
                      <input
                        id="video-image-upload"
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        style={{ display: 'none' }}
                      />
                      {uploadedImage ? (
                        <div className="uploaded-image-preview">
                          <img src={uploadedImage} alt="업로드된 이미지" />
                          <p className="upload-success-text">이미지 업로드됨 (클릭하여 변경)</p>
                        </div>
                      ) : (
                        <div className="upload-placeholder">
                          <span className="upload-icon">📁</span>
                          <p className="upload-title">이미지 파일 업로드</p>
                          <p className="upload-hint">클릭하여 이미지 선택 (10MB 이하)</p>
                        </div>
                      )}
                    </label>
                  </div>

                  <div className="divider-text">또는</div>

                  {/* URL 입력 */}
                  <input
                    type="url"
                    name="source_image_url"
                    value={formData.source_image_url}
                    onChange={handleInputChange}
                    placeholder="이미지 URL 직접 입력 (https://...)"
                    disabled={!!uploadedImage}
                  />
                  <div className="input-hint">
                    💡 이전에 생성한 AI 이미지를 업로드하거나 URL을 붙여넣으세요
                  </div>
                </div>
              )}

              {/* 프롬프트 */}
              <div className="form-group">
                <label>프롬프트 {(formData.model === 'text-to-video' || formData.model === 'wan-2.1') ? '*' : ''}</label>
                <textarea
                  name="prompt"
                  value={formData.prompt}
                  onChange={handleInputChange}
                  placeholder={
                    formData.model === 'stable-video-diffusion'
                      ? "동영상 스타일 설명 (선택사항)"
                      : formData.model === 'wan-2.1'
                      ? "생성할 동영상을 설명해주세요 (한글 가능)\n예: 해변에서 일몰을 바라보는 풍경, 시네마틱한 느낌"
                      : "생성할 동영상에 대한 상세한 설명을 입력하세요"
                  }
                  rows="4"
                  required={formData.model === 'text-to-video' || formData.model === 'wan-2.1'}
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
                <li><strong>Wan 2.1 (저렴)</strong>: 텍스트로 동영상 생성, 한글 자동 번역 (~$0.01)</li>
                <li><strong>Stable Video Diffusion</strong>: 이미지를 짧은 동영상(2-4초)으로 변환</li>
                <li><strong>Text-to-Video (LTX)</strong>: Replicate 기반 텍스트 동영상</li>
                <li>모든 모델은 Replicate 기반 (회당 $0.01-0.05)</li>
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
                    <span className="info-value">
                      {result.model === 'wan-2.1' ? 'Wan 2.1' : result.model}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">상태:</span>
                    <span className={`status-badge ${result.status}`}>
                      {result.status === 'completed' ? '완료' : result.status}
                    </span>
                  </div>
                  {translatedPrompt && (
                    <div className="info-item translated-prompt">
                      <span className="info-label">번역된 프롬프트:</span>
                      <span className="info-value">{translatedPrompt}</span>
                    </div>
                  )}
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
                        {scene.visual_suggestion && (
                          <p className="scene-visual">🎬 {scene.visual_suggestion}</p>
                        )}
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

              {/* 해시태그 */}
              {generatedScript.hashtags && generatedScript.hashtags.length > 0 && (
                <div className="hashtags-section">
                  <h4>#️⃣ 추천 해시태그</h4>
                  <div className="hashtags-list">
                    {generatedScript.hashtags.map((tag, index) => (
                      <span key={index} className="hashtag">#{tag}</span>
                    ))}
                  </div>
                  <button
                    className="btn-copy-hashtags"
                    onClick={() => {
                      navigator.clipboard.writeText(generatedScript.hashtags.map(t => `#${t}`).join(' '));
                      alert('해시태그가 복사되었습니다.');
                    }}
                  >
                    해시태그 복사
                  </button>
                </div>
              )}

              {/* 썸네일 아이디어 */}
              {generatedScript.thumbnailIdeas && generatedScript.thumbnailIdeas.length > 0 && (
                <div className="thumbnail-ideas-section">
                  <h4>🖼️ 썸네일 아이디어</h4>
                  <ul className="thumbnail-ideas-list">
                    {generatedScript.thumbnailIdeas.map((idea, index) => (
                      <li key={index}>{idea}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 생성 히스토리 탭 */}
      {activeTab === 'history' && (
        <div className="history-content">
          <div className="history-header">
            <h3>생성된 동영상 목록</h3>
            <button className="btn-refresh" onClick={loadVideoHistory} disabled={historyLoading}>
              {historyLoading ? '로딩 중...' : '새로고침'}
            </button>
          </div>

          {historyLoading ? (
            <div className="history-loading">
              <span className="spinner"></span>
              <p>동영상 목록을 불러오는 중...</p>
            </div>
          ) : videoHistory.length === 0 ? (
            <div className="history-empty">
              <span className="empty-icon">🎬</span>
              <p>아직 생성된 동영상이 없습니다.</p>
              <button onClick={() => setActiveTab('video')} className="btn-create-first">
                첫 동영상 생성하기
              </button>
            </div>
          ) : (
            <div className="history-grid">
              {videoHistory.map((video) => (
                <div key={video.id} className="history-card">
                  <div className="history-card-header">
                    <h4>{video.title}</h4>
                    <span className={`status-badge ${video.status}`}>
                      {video.status === 'completed' ? '완료' : video.status === 'processing' ? '처리 중' : '실패'}
                    </span>
                  </div>

                  {video.video_url && video.status === 'completed' && (
                    <div className="history-video-preview">
                      <video src={video.video_url} controls preload="metadata" />
                    </div>
                  )}

                  <div className="history-card-info">
                    <div className="info-row">
                      <span className="label">모델:</span>
                      <span className="value">
                        {video.model === 'wan-2.1' ? 'Wan 2.1' : video.model}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="label">생성일:</span>
                      <span className="value">
                        {new Date(video.created_at).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                    {video.prompt && (
                      <div className="info-row prompt-row">
                        <span className="label">프롬프트:</span>
                        <span className="value prompt-text">{video.prompt}</span>
                      </div>
                    )}
                  </div>

                  <div className="history-card-actions">
                    {video.video_url && (
                      <a
                        href={video.video_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-action btn-download"
                      >
                        다운로드
                      </a>
                    )}
                    <button
                      onClick={() => handleDeleteVideo(video.id)}
                      className="btn-action btn-delete"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default VideoCreator;
