import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import './ContentCommon.css';
import './VideoCreator.css';

function VideoCreator() {
  const location = useLocation();

  // 탭 상태: 'video' (AI 동영상 생성), 'script' (비디오 스크립트), 'history' (생성 히스토리)
  const [activeTab, setActiveTab] = useState('video');

  // AI 동영상 생성 상태
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    prompt: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [translatedPrompt, setTranslatedPrompt] = useState(null);

  // 이미지 업로드 상태
  const [sourceImage, setSourceImage] = useState(null);
  const [sourceImagePreview, setSourceImagePreview] = useState(null);

  // 생성 히스토리 상태
  const [videoHistory, setVideoHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 히스토리 탭 진입 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history') {
      loadVideoHistory();
    }
  }, [activeTab]);

  // 템플릿에서 넘어온 경우 프롬프트 적용
  useEffect(() => {
    if (location.state?.template) {
      const template = location.state.template;
      setFormData(prev => ({
        ...prev,
        prompt: template.prompt || '',
        title: template.name || '',
        description: template.description || ''
      }));
    }
  }, [location.state]);

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

  // 이미지 업로드 핸들러
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 파일 크기 체크 (10MB 제한)
      if (file.size > 10 * 1024 * 1024) {
        alert('이미지 파일 크기는 10MB 이하여야 합니다.');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setSourceImage(reader.result);
        setSourceImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 이미지 제거 핸들러
  const handleRemoveImage = () => {
    setSourceImage(null);
    setSourceImagePreview(null);
  };

  // AI 동영상 생성 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setTranslatedPrompt(null);

    try {
      const token = localStorage.getItem('access_token');

      // 나노바나나 (Veo 3.1) API 호출
      const requestData = {
        prompt: formData.prompt,
        title: formData.title || 'AI 생성 동영상',
        description: formData.description || null
      };

      // 이미지가 있으면 추가
      if (sourceImage) {
        requestData.image_data = sourceImage;
      }

      const response = await axios.post(
        'http://localhost:8000/api/video/generate-veo31',
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 360000  // 6분 타임아웃
        }
      );

      setResult({
        title: response.data.title,
        video_url: response.data.video_url,
        status: response.data.status,
        model: 'nanobanana',
        message: response.data.message
      });

      if (response.data.translated_prompt) {
        setTranslatedPrompt(response.data.translated_prompt);
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
        <p className="page-description">나노바나나 AI를 활용하여 고품질 동영상을 생성하세요</p>
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

              {/* 프롬프트 */}
              <div className="form-group">
                <label>프롬프트 *</label>
                <textarea
                  name="prompt"
                  value={formData.prompt}
                  onChange={handleInputChange}
                  placeholder="고품질 동영상을 생성할 프롬프트를 입력하세요 (한글 가능)&#10;예: 해변에서 일몰을 바라보는 풍경, 시네마틱한 느낌"
                  rows="4"
                  required
                />
              </div>

              {/* 이미지 업로드 (선택사항) */}
              <div className="form-group">
                <label>시작 이미지 (선택사항)</label>
                <p className="form-hint">이미지를 업로드하면 해당 이미지를 첫 프레임으로 동영상을 생성합니다.</p>

                {!sourceImagePreview ? (
                  <div className="image-upload-area">
                    <input
                      type="file"
                      id="source-image"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="file-input"
                    />
                    <label htmlFor="source-image" className="upload-label">
                      <span className="upload-icon">🖼️</span>
                      <span>클릭하여 이미지 업로드</span>
                      <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                    </label>
                  </div>
                ) : (
                  <div className="image-preview-container">
                    <img
                      src={sourceImagePreview}
                      alt="업로드된 이미지"
                      className="image-preview"
                    />
                    <button
                      type="button"
                      onClick={handleRemoveImage}
                      className="btn-remove-image"
                    >
                      ✕ 이미지 제거
                    </button>
                  </div>
                )}
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
              <h4>📌 나노바나나 AI 동영상 생성</h4>
              <ul>
                <li>Google의 최신 AI 비디오 생성 모델 (Veo 3.1) 사용</li>
                <li>텍스트 프롬프트로 고품질 시네마틱 동영상 생성</li>
                <li>이미지 업로드 시 해당 이미지를 첫 프레임으로 동영상 생성</li>
                <li>한글 프롬프트 자동 번역 지원</li>
                <li>생성 시간: 약 1-5분 소요</li>
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
                    <span className="info-value">나노바나나 (Veo 3.1)</span>
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
                        {video.model === 'veo-3.1' || video.model === 'nanobanana' ? '나노바나나' : video.model}
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
