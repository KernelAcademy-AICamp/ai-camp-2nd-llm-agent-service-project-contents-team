import { useState, useEffect } from 'react';
import axios from 'axios';
import './ContentCommon.css';
import './AIVideoGenerator.css';

// API 베이스 URL
const API_BASE_URL = 'http://localhost:8000';

function AIVideoGenerator() {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('create');

  // 단계 상태: 'input' (제품 정보 입력), 'generating' (생성 중)
  const [step, setStep] = useState('input');

  // 티어 옵션
  const [tiers, setTiers] = useState([]);
  const [selectedTier, setSelectedTier] = useState(null);

  // 폼 데이터
  const [formData, setFormData] = useState({
    product_name: '',
    product_description: ''
  });

  // 이미지 업로드
  const [productImage, setProductImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // 생성 상태
  const [loading, setLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [error, setError] = useState(null);

  // 히스토리
  const [jobHistory, setJobHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 티어 정보 로드
  useEffect(() => {
    loadTiers();
  }, []);

  // 히스토리 탭 진입 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history') {
      loadJobHistory();
    }
  }, [activeTab]);

  // 진행 중인 작업 폴링
  useEffect(() => {
    let interval;
    if (currentJob && ['pending', 'planning', 'generating_images', 'generating_videos', 'composing'].includes(currentJob.status)) {
      interval = setInterval(() => {
        pollJobStatus(currentJob.id);
      }, 3000); // 3초마다 폴링
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentJob]);

  // URL 헬퍼 함수: 상대 경로를 절대 URL로 변환
  const getFullUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path; // 이미 절대 URL
    }
    return `${API_BASE_URL}${path}`; // 상대 경로에 베이스 URL 추가
  };

  const loadTiers = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/ai-video/tiers');
      setTiers(response.data);
      // 기본값: Standard (index 1)
      if (response.data.length > 1) {
        setSelectedTier(response.data[1].tier);
      } else if (response.data.length > 0) {
        setSelectedTier(response.data[0].tier);
      }
    } catch (err) {
      console.error('Failed to load tiers:', err);
    }
  };

  const loadJobHistory = async () => {
    setHistoryLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        'http://localhost:8000/api/ai-video/jobs',
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setJobHistory(response.data);
    } catch (err) {
      console.error('Failed to load job history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `http://localhost:8000/api/ai-video/jobs/${jobId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setCurrentJob(response.data);

      // 완료 또는 실패 시 폴링 중지
      if (['completed', 'failed'].includes(response.data.status)) {
        return;
      }
    } catch (err) {
      console.error('Failed to poll job status:', err);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 파일 크기 체크 (10MB 제한)
      if (file.size > 10 * 1024 * 1024) {
        alert('이미지 파일 크기는 10MB 이하여야 합니다.');
        return;
      }

      setProductImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setProductImage(null);
    setImagePreview(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenerateVideo = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setCurrentJob(null);

    try {
      const token = localStorage.getItem('access_token');

      // FormData 생성
      const data = new FormData();
      data.append('product_name', formData.product_name);
      data.append('tier', selectedTier);
      if (formData.product_description) {
        data.append('product_description', formData.product_description);
      }
      if (productImage) {
        data.append('image', productImage);
      }

      const response = await axios.post(
        'http://localhost:8000/api/ai-video/jobs',
        data,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setCurrentJob(response.data);
      setStep('generating');
      // 생성 시작 후 진행 탭으로 이동
      setActiveTab('progress');
    } catch (err) {
      setError(err.response?.data?.detail || 'AI 비디오 생성 중 오류가 발생했습니다.');
      console.error('Video generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep('input');
    setFormData({
      product_name: '',
      product_description: ''
    });
    setProductImage(null);
    setImagePreview(null);
    setCurrentJob(null);
    setError(null);
    // 티어를 기본값(Standard)으로 리셋
    if (tiers.length > 1) {
      setSelectedTier(tiers[1].tier);
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('이 작업을 삭제하시겠습니까?')) return;

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(
        `http://localhost:8000/api/ai-video/jobs/${jobId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      loadJobHistory();
    } catch (err) {
      console.error('Failed to delete job:', err);
      alert('작업 삭제에 실패했습니다.');
    }
  };

  const getProgressPercentage = (status) => {
    const statusMap = {
      'pending': 10,
      'planning': 30,
      'generating_images': 50,
      'generating_videos': 70,
      'composing': 85,
      'completed': 100,
      'failed': 0
    };
    return statusMap[status] || 0;
  };

  const getStatusText = (status) => {
    const statusMap = {
      'pending': '대기 중',
      'planning': '스토리보드 생성 중',
      'generating_images': '이미지 생성 중',
      'generating_videos': '전환 비디오 생성 중',
      'composing': '최종 비디오 합성 중',
      'completed': '완료',
      'failed': '실패'
    };
    return statusMap[status] || status;
  };

  return (
    <div className="content-page">
      <div className="page-header">
        <h2>AI 마케팅 비디오 생성</h2>
        <p className="page-description">제품 이미지 하나로 전문적인 마케팅 비디오를 만드세요</p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`content-tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          비디오 생성
        </button>
        {currentJob && (
          <button
            className={`content-tab ${activeTab === 'progress' ? 'active' : ''}`}
            onClick={() => setActiveTab('progress')}
          >
            진행 상황
          </button>
        )}
        <button
          className={`content-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          생성 히스토리
        </button>
      </div>

      {/* 비디오 생성 탭 */}
      {activeTab === 'create' && (
        <div className="content-grid single-column">
          <div className="form-section">
            {/* 에러 메시지 */}
            {error && (
              <div className="error-message" style={{ marginBottom: '1.5rem' }}>
                <span className="error-icon">⚠️</span>
                <div>
                  <strong>오류 발생</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
            {/* Step 1: 제품 정보 입력 및 티어 선택 */}
            {step === 'input' && (
              <form onSubmit={handleGenerateVideo}>
                {/* 제품 이미지 업로드 */}
                <div className="form-group">
                  <label>제품 이미지 *</label>
                  {!imagePreview ? (
                    <div className="image-upload-area">
                      <input
                        type="file"
                        id="product-image"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="file-input"
                        required
                      />
                      <label htmlFor="product-image" className="upload-label">
                        <span className="upload-icon">📸</span>
                        <span>클릭하여 이미지 업로드</span>
                        <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                      </label>
                    </div>
                  ) : (
                    <div className="image-preview-container">
                      <img
                        src={imagePreview}
                        alt="제품 이미지"
                        className="image-preview"
                      />
                      <button
                        type="button"
                        onClick={handleRemoveImage}
                        className="btn-remove-image"
                      >
                        ✕ 제거
                      </button>
                    </div>
                  )}
                </div>

                {/* 제품명 */}
                <div className="form-group">
                  <label>제품명 *</label>
                  <input
                    type="text"
                    name="product_name"
                    value={formData.product_name}
                    onChange={handleInputChange}
                    placeholder="예: 프리미엄 무선 이어폰"
                    required
                  />
                </div>

                {/* 제품 설명 */}
                <div className="form-group">
                  <label>제품 설명 (선택)</label>
                  <textarea
                    name="product_description"
                    value={formData.product_description}
                    onChange={handleInputChange}
                    placeholder="제품의 주요 특징이나 장점을 입력하세요"
                    rows="3"
                  />
                </div>
                {/* AI 분석 버튼 */}
                <button
                  type="submit"
                  className="btn-generate"
                  disabled={analyzingProduct}
                >
                  {analyzingProduct ? (
                    <>
                      <span className="spinner"></span>
                      AI가 제품 분석 중...
                    </>
                  ) : (
                    'AI 분석하기'
                  )}
                </button>
              </form>
            )}

            {/* Step 2: AI 추천 및 티어 선택 */}
            {step === 'recommendation' && aiRecommendation && (
              <div>
                {/* AI 추천 결과 */}
                <div className="ai-recommendation">
                  <div className="recommendation-card">
                    <div className="recommendation-header">
                      <span className="recommended-badge">AI 추천</span>
                      <h4>
                        {aiRecommendation.recommended_tier === 'short' ? 'Short' :
                         aiRecommendation.recommended_tier === 'standard' ? 'Standard' :
                         'Premium'}
                      </h4>
                      <span className="confidence-score">
                        신뢰도 {Math.round(aiRecommendation.confidence * 100)}%
                      </span>
                    </div>
                    <p className="recommendation-reason">{aiRecommendation.reason}</p>
                  </div>
                </div>

                {/* 티어 선택 */}
                <div className="form-group">
                  <label>영상 길이 선택 *</label>
                  <p className="form-hint">원하는 비디오 길이를 선택하세요</p>
                  <div className="tier-options">
                    {tiers.map(tier => (
                      <div
                        key={tier.tier}
                        className={`tier-card ${selectedTier === tier.tier ? 'selected' : ''}`}
                        onClick={() => setSelectedTier(tier.tier)}
                      >
                        {aiRecommendation.recommended_tier === tier.tier && (
                          <div className="recommended-label">추천</div>
                        )}
                        <div className="tier-header">
                          <h4>{tier.tier === 'short' ? 'Short' : tier.tier === 'standard' ? 'Standard' : 'Premium'}</h4>
                          <span className="tier-price">${tier.cost}</span>
                        </div>
                        <div className="tier-details">
                          <p>{tier.duration_seconds}초 · {tier.cut_count}컷</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 비디오 생성 버튼 */}
                <button
                  type="submit"
                  className="btn-generate"
                  disabled={loading || !selectedTier}
                >
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      비디오 생성 시작 중...
                    </>
                  ) : (
                    <>
                      <span>🎬</span>
                      비디오 생성하기
                    </>
                  )}
                </button>
              </form>
            )}


            {/* 안내 사항 */}
            {step === 'input' && (
              <div className="info-box">
                <h4>🎥 AI 마케팅 비디오 생성 기능</h4>
                <ul>
                  <li>제품 이미지 1장으로 완전한 마케팅 비디오 생성</li>
                  <li>원하는 영상 길이(Short/Standard/Premium) 직접 선택</li>
                  <li>스토리보드 자동 구성 및 이미지 생성</li>
                  <li>전환 최적화로 90% 비용 절감 (Veo 3.1 + FFmpeg)</li>
                  <li>브랜드 톤앤매너 자동 반영</li>
                  <li>예상 소요 시간: 2-5분</li>
                  <li>요금: Short $0.99 | Standard $1.49 | Premium $1.99</li>
                </ul>
              </div>
            )}
          </div>

          {/* 오른쪽: 미리보기/안내 */}
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

            {!error && step === 'input' && (
              <div className="placeholder-result">
                <span className="placeholder-icon">🎬</span>
                <h3>AI 마케팅 비디오 생성</h3>
                <p>제품 정보와 원하는 영상 길이를 선택하고 비디오를 생성하세요</p>
                <div className="feature-list">
                  <div className="feature-item">
                    <span>🤖</span>
                    <p>AI 자동 스토리보드</p>
                  </div>
                  <div className="feature-item">
                    <span>🎨</span>
                    <p>고품질 이미지 생성</p>
                  </div>
                  <div className="feature-item">
                    <span>🎥</span>
                    <p>시네마틱 전환 효과</p>
                  </div>
                  <div className="feature-item">
                    <span>💰</span>
                    <p>90% 비용 최적화</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 진행 상황 탭 */}
      {activeTab === 'progress' && currentJob && (
        <div className="progress-content">
          <div className="progress-header">
            <h3>{currentJob.product_name}</h3>
            <span className={`status-badge ${currentJob.status}`}>
              {getStatusText(currentJob.status)}
            </span>
          </div>

          {/* 진행 바 */}
          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{ width: `${getProgressPercentage(currentJob.status)}%` }}
            />
            <span className="progress-percentage">
              {getProgressPercentage(currentJob.status)}%
            </span>
          </div>

          {/* 현재 단계 */}
          {currentJob.current_step && (
            <div className="current-step">
              <p>{currentJob.current_step}</p>
            </div>
          )}

          {/* 단계별 표시 */}
          <div className="steps-container">
            <div className={`step ${['planning', 'generating_images', 'generating_videos', 'composing', 'completed'].includes(currentJob.status) ? 'completed' : currentJob.status === 'pending' ? 'active' : ''}`}>
              <div className="step-icon">📝</div>
              <div className="step-label">스토리보드 생성</div>
            </div>
            <div className={`step ${['generating_images', 'generating_videos', 'composing', 'completed'].includes(currentJob.status) ? 'completed' : currentJob.status === 'planning' ? 'active' : ''}`}>
              <div className="step-icon">🎨</div>
              <div className="step-label">이미지 생성</div>
            </div>
            <div className={`step ${['generating_videos', 'composing', 'completed'].includes(currentJob.status) ? 'completed' : currentJob.status === 'generating_images' ? 'active' : ''}`}>
              <div className="step-icon">🎥</div>
              <div className="step-label">전환 비디오</div>
            </div>
            <div className={`step ${['composing', 'completed'].includes(currentJob.status) ? 'completed' : currentJob.status === 'generating_videos' ? 'active' : ''}`}>
              <div className="step-icon">🎬</div>
              <div className="step-label">최종 합성</div>
            </div>
          </div>

          {/* 결과 표시 */}
          {currentJob.status === 'completed' && currentJob.final_video_url && (
            <div className="video-result">
              <h3>✅ 비디오 생성 완료!</h3>

              <div className="video-preview">
                <video
                  src={getFullUrl(currentJob.final_video_url)}
                  controls
                  autoPlay
                  loop
                  className="generated-video"
                  poster={getFullUrl(currentJob.thumbnail_url)}
                >
                  Your browser does not support the video tag.
                </video>

                <div className="video-actions">
                  <a
                    href={getFullUrl(currentJob.final_video_url)}
                    download={`${currentJob.product_name}.mp4`}
                    className="btn-download"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span>⬇️</span>
                    다운로드
                  </a>
                  <button
                    onClick={() => navigator.clipboard.writeText(getFullUrl(currentJob.final_video_url))}
                    className="btn-copy"
                  >
                    <span>🔗</span>
                    URL 복사
                  </button>
                </div>
              </div>

              {/* 스토리보드 정보 */}
              {currentJob.storyboard && (
                <div className="storyboard-info">
                  <h4>📋 스토리보드</h4>
                  <div className="storyboard-summary">
                    <p>총 {currentJob.cut_count}개 컷, {currentJob.duration_seconds}초 영상</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 실패 메시지 */}
          {currentJob.status === 'failed' && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <div>
                <strong>생성 실패</strong>
                <p>{currentJob.error_message || '비디오 생성 중 오류가 발생했습니다.'}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 생성 히스토리 탭 */}
      {activeTab === 'history' && (
        <div className="history-content">
          <div className="history-header">
            <h3>생성된 비디오 목록</h3>
            <button className="btn-refresh" onClick={loadJobHistory} disabled={historyLoading}>
              {historyLoading ? '로딩 중...' : '새로고침'}
            </button>
          </div>

          {historyLoading ? (
            <div className="history-loading">
              <span className="spinner"></span>
              <p>비디오 목록을 불러오는 중...</p>
            </div>
          ) : jobHistory.length === 0 ? (
            <div className="history-empty">
              <span className="empty-icon">🎬</span>
              <p>아직 생성된 비디오가 없습니다.</p>
              <button onClick={() => setActiveTab('create')} className="btn-create-first">
                첫 비디오 생성하기
              </button>
            </div>
          ) : (
            <div className="history-grid">
              {jobHistory.map((job) => (
                <div key={job.id} className="history-card">
                  <div className="history-card-header">
                    <h4>{job.product_name}</h4>
                    <span className={`status-badge ${job.status}`}>
                      {getStatusText(job.status)}
                    </span>
                  </div>

                  {job.thumbnail_url && (
                    <div className="history-thumbnail">
                      <img src={getFullUrl(job.thumbnail_url)} alt={job.product_name} />
                    </div>
                  )}

                  <div className="history-card-info">
                    <div className="info-row">
                      <span className="label">티어:</span>
                      <span className="value">{job.tier}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">길이:</span>
                      <span className="value">{job.duration_seconds}초 ({job.cut_count}컷)</span>
                    </div>
                    <div className="info-row">
                      <span className="label">비용:</span>
                      <span className="value">${job.cost}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">생성일:</span>
                      <span className="value">
                        {new Date(job.created_at).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                  </div>

                  <div className="history-card-actions">
                    {job.final_video_url && job.status === 'completed' && (
                      <>
                        <button
                          onClick={() => {
                            setCurrentJob(job);
                            setActiveTab('progress');
                          }}
                          className="btn-action btn-view"
                        >
                          보기
                        </button>
                        <a
                          href={getFullUrl(job.final_video_url)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-action btn-download"
                        >
                          다운로드
                        </a>
                      </>
                    )}
                    {['pending', 'planning', 'generating_images', 'generating_videos', 'composing'].includes(job.status) && (
                      <button
                        onClick={() => {
                          setCurrentJob(job);
                          setActiveTab('progress');
                        }}
                        className="btn-action btn-view"
                      >
                        진행 상황 보기
                      </button>
                    )}
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

export default AIVideoGenerator;
