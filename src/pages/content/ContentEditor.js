import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiCopy, FiSend, FiCheck, FiEdit3, FiSave, FiClock, FiX, FiUpload, FiImage, FiTrash2 } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { publishedContentAPI } from '../../services/api';
import './ContentEditor.css';

// 플랫폼 설정
const PLATFORM_CONFIG = {
  blog: {
    name: '네이버 블로그',
    icon: '📝',
    maxLength: null,
    hasTitle: true
  },
  sns: {
    name: 'Instagram / Facebook',
    icon: '📷',
    maxLength: 2200,
    hasTitle: false
  },
  x: {
    name: 'X',
    icon: '𝕏',
    maxLength: 280,
    hasTitle: false
  },
  threads: {
    name: 'Threads',
    icon: '🧵',
    maxLength: 500,
    hasTitle: false
  },
};

function ContentEditor() {
  const location = useLocation();
  const navigate = useNavigate();
  const { result, topic, sessionId } = location.state || {};

  // 편집 상태
  const [editedContent, setEditedContent] = useState({});
  const [activePlatform, setActivePlatform] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingField, setEditingField] = useState(null); // 'title' | 'content' | 'tags'

  // 저장 상태
  const [isSaved, setIsSaved] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedContentIds, setSavedContentIds] = useState({}); // 플랫폼별 저장된 콘텐츠 ID
  const initialContentRef = useRef(null);

  // 발행 상태
  const [publishingPlatform, setPublishingPlatform] = useState(null);
  const [publishResults, setPublishResults] = useState({});

  // 예약 발행 모달
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [isScheduling, setIsScheduling] = useState(false);

  // 이미지 ID 목록 (세션에서 가져온 경우)
  const [imageIds, setImageIds] = useState([]);

  // 이미지 업로드 상태
  const [uploadedImages, setUploadedImages] = useState([]); // 직접 업로드한 이미지들
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  // 초기 데이터 설정
  useEffect(() => {
    if (result?.text) {
      const initialContent = {};
      const platforms = [];

      if (result.text.blog) {
        initialContent.blog = {
          title: result.text.blog.title || '',
          content: result.text.blog.content || '',
          tags: result.text.blog.tags || [],
        };
        platforms.push('blog');
      }
      if (result.text.sns) {
        initialContent.sns = {
          content: result.text.sns.content || '',
          tags: result.text.sns.tags || result.text.sns.hashtags || [],
        };
        platforms.push('sns');
      }
      if (result.text.x) {
        initialContent.x = {
          content: result.text.x.content || '',
          tags: result.text.x.tags || result.text.x.hashtags || [],
        };
        platforms.push('x');
      }
      if (result.text.threads) {
        initialContent.threads = {
          content: result.text.threads.content || '',
          tags: result.text.threads.tags || result.text.threads.hashtags || [],
        };
        platforms.push('threads');
      }

      setEditedContent(initialContent);
      initialContentRef.current = JSON.stringify(initialContent);
      if (platforms.length > 0) {
        setActivePlatform(platforms[0]);
      }

      // 이미지 ID 설정
      if (result.images?.length > 0) {
        // 이미지에 id가 있으면 사용, 없으면 빈 배열
        const ids = result.images.map(img => img.id).filter(Boolean);
        setImageIds(ids);
      }
    }
  }, [result]);

  // 데이터가 없으면 리다이렉트
  useEffect(() => {
    if (!result) {
      navigate('/content/create');
    }
  }, [result, navigate]);

  // 변경 감지
  useEffect(() => {
    if (initialContentRef.current) {
      const currentContent = JSON.stringify(editedContent);
      setIsSaved(currentContent === initialContentRef.current);
    }
  }, [editedContent]);

  // 페이지 이탈 경고 (브라우저 새로고침/닫기)
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (!isSaved) {
        e.preventDefault();
        e.returnValue = '저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isSaved]);

  const availablePlatforms = Object.keys(editedContent);

  // 콘텐츠 수정 핸들러
  const handleContentChange = (platform, field, value) => {
    setEditedContent(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform],
        [field]: value,
      },
    }));
  };

  // 태그 수정 핸들러
  const handleTagsChange = (platform, tagsString) => {
    const tags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    handleContentChange(platform, 'tags', tags);
  };

  // 임시저장 핸들러
  const handleSave = useCallback(async () => {
    if (isSaved || isSaving) return;

    setIsSaving(true);
    try {
      const data = editedContent[activePlatform];
      if (!data) {
        throw new Error('저장할 콘텐츠가 없습니다.');
      }

      const savedContent = await publishedContentAPI.saveDraft({
        id: savedContentIds[activePlatform] || null,  // 기존 ID가 있으면 전달 (업데이트)
        session_id: sessionId || null,
        platform: activePlatform,
        title: data.title || null,
        content: data.content,
        tags: data.tags,
        image_ids: imageIds.length > 0 ? imageIds : null,
        uploaded_image_url: uploadedImages.length > 0 ? uploadedImages[0].url : null,
      });

      // 저장된 콘텐츠 ID 업데이트
      setSavedContentIds(prev => ({
        ...prev,
        [activePlatform]: savedContent.id,
      }));

      initialContentRef.current = JSON.stringify(editedContent);
      setIsSaved(true);
      alert('임시저장되었습니다.');
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsSaving(false);
    }
  }, [editedContent, activePlatform, sessionId, imageIds, isSaved, isSaving, savedContentIds, uploadedImages]);

  // 뒤로가기 핸들러 (저장 확인)
  const handleGoBack = useCallback(() => {
    if (!isSaved) {
      const confirmed = window.confirm('저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?');
      if (confirmed) {
        handleSave().then(() => navigate(-1));
        return;
      }
    }
    navigate(-1);
  }, [isSaved, handleSave, navigate]);

  // 복사 핸들러
  const handleCopy = (platform) => {
    const data = editedContent[platform];
    if (!data) return;

    let text = '';
    if (data.title) text += `${data.title}\n\n`;
    text += data.content;
    if (data.tags?.length > 0) {
      text += '\n\n' + data.tags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ');
    }

    navigator.clipboard.writeText(text);
    alert(`${PLATFORM_CONFIG[platform].name} 콘텐츠가 복사되었습니다.`);
  };

  // 예약 발행 모달 열기
  const openScheduleModal = () => {
    // 기본값: 내일 오전 9시
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);

    setScheduleDate(tomorrow.toISOString().split('T')[0]);
    setScheduleTime('09:00');
    setShowScheduleModal(true);
  };

  // 예약 발행 핸들러
  const handleSchedule = async () => {
    if (!scheduleDate || !scheduleTime) {
      alert('예약 날짜와 시간을 선택해주세요.');
      return;
    }

    const scheduledAt = new Date(`${scheduleDate}T${scheduleTime}`);
    if (scheduledAt <= new Date()) {
      alert('예약 시간은 현재 시간 이후여야 합니다.');
      return;
    }

    setIsScheduling(true);
    try {
      const data = editedContent[activePlatform];
      if (!data) {
        throw new Error('예약할 콘텐츠가 없습니다.');
      }

      await publishedContentAPI.schedule({
        id: savedContentIds[activePlatform] || null,  // 기존 ID가 있으면 전달
        session_id: sessionId || null,
        platform: activePlatform,
        title: data.title || null,
        content: data.content,
        tags: data.tags,
        image_ids: imageIds.length > 0 ? imageIds : null,
        uploaded_image_url: uploadedImages.length > 0 ? uploadedImages[0].url : null,
        scheduled_at: scheduledAt.toISOString(),
      });

      setShowScheduleModal(false);
      setPublishResults(prev => ({
        ...prev,
        [activePlatform]: {
          success: true,
          message: `${scheduledAt.toLocaleString('ko-KR')}에 발행 예약되었습니다.`,
          scheduled: true,
        },
      }));

      // 저장 상태 업데이트
      initialContentRef.current = JSON.stringify(editedContent);
      setIsSaved(true);
    } catch (error) {
      console.error('예약 실패:', error);
      alert('예약에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsScheduling(false);
    }
  };

  // 즉시 발행 핸들러
  const handlePublish = async (platform) => {
    // 저장되지 않은 변경사항이 있으면 먼저 저장
    if (!isSaved) {
      const confirmed = window.confirm('발행 전에 변경사항을 저장해야 합니다. 저장하시겠습니까?');
      if (confirmed) {
        await handleSave();
      } else {
        return;
      }
    }

    // 저장된 콘텐츠 ID가 없으면 먼저 저장
    let contentId = savedContentIds[platform];
    if (!contentId) {
      try {
        const data = editedContent[platform];
        const savedContent = await publishedContentAPI.saveDraft({
          id: savedContentIds[platform] || null,  // 기존 ID가 있으면 전달
          session_id: sessionId || null,
          platform: platform,
          title: data.title || null,
          content: data.content,
          tags: data.tags,
          image_ids: imageIds.length > 0 ? imageIds : null,
          uploaded_image_url: uploadedImages.length > 0 ? uploadedImages[0].url : null,
        });
        contentId = savedContent.id;
        setSavedContentIds(prev => ({ ...prev, [platform]: contentId }));
      } catch (error) {
        console.error('저장 실패:', error);
        alert('발행 전 저장에 실패했습니다.');
        return;
      }
    }

    setPublishingPlatform(platform);

    try {
      await publishedContentAPI.publish(contentId);

      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: true, message: '발행 완료!' },
      }));
    } catch (error) {
      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: false, message: error.response?.data?.detail || error.message },
      }));
    } finally {
      setPublishingPlatform(null);
    }
  };

  // 편집 모드 토글
  const startEditing = (field) => {
    setIsEditing(true);
    setEditingField(field);
  };

  const finishEditing = () => {
    setIsEditing(false);
    setEditingField(null);
  };

  // 이미지 업로드 핸들러
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 파일 타입 검증
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      alert('지원하지 않는 파일 형식입니다. (JPEG, PNG, GIF, WebP만 가능)');
      return;
    }

    // 파일 크기 검증 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('파일 크기는 10MB 이하만 가능합니다.');
      return;
    }

    setIsUploading(true);
    try {
      const response = await publishedContentAPI.uploadImage(file);

      // 업로드된 이미지 추가
      setUploadedImages(prev => [...prev, {
        url: response.image_url,
        public_id: response.public_id,
        width: response.width,
        height: response.height,
      }]);

      // 저장 상태 변경
      setIsSaved(false);
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      alert('이미지 업로드에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
      // 파일 입력 초기화 (같은 파일 재선택 가능하도록)
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 업로드된 이미지 삭제 핸들러
  const handleRemoveUploadedImage = (index) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
    setIsSaved(false);
  };

  // Instagram/SNS 플랫폼에서 이미지가 필요한지 확인
  const needsImageUpload = (platform) => {
    return (platform === 'sns' || platform === 'instagram') &&
           (!result.images || result.images.length === 0) &&
           uploadedImages.length === 0;
  };

  // 현재 플랫폼에서 사용할 이미지 URL 가져오기
  const getImageUrlForPublish = () => {
    // 업로드된 이미지가 있으면 우선 사용
    if (uploadedImages.length > 0) {
      return uploadedImages[0].url;
    }
    // 세션에서 가져온 이미지가 있으면 사용
    if (result.images?.length > 0) {
      return result.images[0].url || result.images[0].image_url;
    }
    return null;
  };

  if (!result) return null;

  const currentData = editedContent[activePlatform];
  const currentConfig = PLATFORM_CONFIG[activePlatform];

  return (
    <div className="content-editor">
      {/* 헤더 */}
      <button className="btn-back" onClick={handleGoBack}>
        <FiArrowLeft /> 돌아가기
      </button>
      <div className="editor-header">
        <div className="editor-header-info">
          <h2>콘텐츠 편집 & 발행</h2>
          <p className="editor-subtitle">주제: {topic}</p>
        </div>
        <button
          className={`btn-save ${isSaved ? 'saved' : 'unsaved'}`}
          onClick={handleSave}
          disabled={isSaved || isSaving}
        >
          {isSaving ? (
            <>저장 중...</>
          ) : isSaved ? (
            <><FiCheck /> 저장됨</>
          ) : (
            <><FiSave /> 임시저장</>
          )}
        </button>
      </div>

      <div className="editor-layout">
        {/* 편집 영역 */}
        <div className="editor-main">
          {/* 플랫폼 탭 (상단) */}
          <div className="platform-tabs-horizontal">
            {availablePlatforms.map(platform => (
              <button
                key={platform}
                className={`platform-tab-h ${activePlatform === platform ? 'active' : ''} ${publishResults[platform]?.success ? 'published' : ''}`}
                onClick={() => setActivePlatform(platform)}
              >
                <span className="platform-tab-icon">{PLATFORM_CONFIG[platform].icon}</span>
                <span className="platform-tab-name">{PLATFORM_CONFIG[platform].name}</span>
                {publishResults[platform]?.success && (
                  <FiCheck className="published-icon" />
                )}
              </button>
            ))}
          </div>
          {currentData && (
            <>
              {/* 제목 (블로그만) */}
              {currentConfig?.hasTitle && (
                <div className="editor-section">
                  <div className="editor-section-header">
                    <label>제목</label>
                    {!isEditing || editingField !== 'title' ? (
                      <button className="btn-edit" onClick={() => startEditing('title')}>
                        <FiEdit3 /> 수정
                      </button>
                    ) : (
                      <button className="btn-done" onClick={finishEditing}>
                        <FiCheck /> 완료
                      </button>
                    )}
                  </div>
                  {editingField === 'title' ? (
                    <input
                      type="text"
                      className="editor-title-input"
                      value={currentData.title || ''}
                      onChange={(e) => handleContentChange(activePlatform, 'title', e.target.value)}
                      autoFocus
                    />
                  ) : (
                    <div className="editor-title-preview">{currentData.title}</div>
                  )}
                </div>
              )}

              {/* 본문 */}
              <div className="editor-section">
                <div className="editor-section-header">
                  <label>본문</label>
                  <div className="editor-section-actions">
                    {currentConfig?.maxLength && (
                      <span className={`char-count ${currentData.content.length > currentConfig.maxLength ? 'over' : ''}`}>
                        {currentData.content.length} / {currentConfig.maxLength}자
                      </span>
                    )}
                    {!isEditing || editingField !== 'content' ? (
                      <button className="btn-edit" onClick={() => startEditing('content')}>
                        <FiEdit3 /> 수정
                      </button>
                    ) : (
                      <button className="btn-done" onClick={finishEditing}>
                        <FiCheck /> 완료
                      </button>
                    )}
                  </div>
                </div>
                {editingField === 'content' ? (
                  <textarea
                    className="editor-content-textarea"
                    value={currentData.content}
                    onChange={(e) => handleContentChange(activePlatform, 'content', e.target.value)}
                    rows={15}
                    autoFocus
                  />
                ) : (
                  <div className="editor-content-preview">
                    {activePlatform === 'blog' ? (
                      <ReactMarkdown remarkPlugins={[remarkBreaks]}>
                        {currentData.content}
                      </ReactMarkdown>
                    ) : (
                      <div className="plain-text">{currentData.content}</div>
                    )}
                  </div>
                )}
              </div>

              {/* 태그 */}
              <div className="editor-section">
                <div className="editor-section-header">
                  <label>태그</label>
                  {!isEditing || editingField !== 'tags' ? (
                    <button className="btn-edit" onClick={() => startEditing('tags')}>
                      <FiEdit3 /> 수정
                    </button>
                  ) : (
                    <button className="btn-done" onClick={finishEditing}>
                      <FiCheck /> 완료
                    </button>
                  )}
                </div>
                {editingField === 'tags' ? (
                  <input
                    type="text"
                    className="editor-tags-input"
                    value={currentData.tags?.join(', ') || ''}
                    onChange={(e) => handleTagsChange(activePlatform, e.target.value)}
                    placeholder="쉼표로 구분하여 입력"
                    autoFocus
                  />
                ) : (
                  <div className="editor-tags-preview">
                    {currentData.tags?.map((tag, idx) => (
                      <span key={idx} className="editor-tag">
                        {tag.startsWith('#') ? tag : `#${tag}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 액션 버튼 */}
              <div className="editor-actions">
                <button className="btn-copy" onClick={() => handleCopy(activePlatform)}>
                  <FiCopy /> 복사하기
                </button>
                <button
                  className="btn-schedule"
                  onClick={openScheduleModal}
                  disabled={publishResults[activePlatform]?.success}
                >
                  <FiClock /> 예약 발행
                </button>
                <button
                  className={`btn-publish-platform ${publishResults[activePlatform]?.success ? 'published' : ''}`}
                  onClick={() => handlePublish(activePlatform)}
                  disabled={publishingPlatform === activePlatform || publishResults[activePlatform]?.success}
                >
                  {publishingPlatform === activePlatform ? (
                    <>발행 중...</>
                  ) : publishResults[activePlatform]?.success ? (
                    <><FiCheck /> {publishResults[activePlatform]?.scheduled ? '예약됨' : '발행 완료'}</>
                  ) : (
                    <><FiSend /> 즉시 발행</>
                  )}
                </button>
              </div>

              {/* 발행 결과 메시지 */}
              {publishResults[activePlatform] && (
                <div className={`publish-result-message ${publishResults[activePlatform].success ? 'success' : 'error'}`}>
                  {publishResults[activePlatform].message}
                </div>
              )}

              {/* Instagram/SNS용 이미지 업로드 섹션 */}
              {(activePlatform === 'sns' || activePlatform === 'instagram') && (
                <div className="editor-images-section">
                  <h4>
                    <FiImage /> 이미지 {(activePlatform === 'sns' || activePlatform === 'instagram') && <span className="required-badge">필수</span>}
                  </h4>

                  {/* 기존 이미지 미리보기 */}
                  {result.images?.length > 0 && (
                    <div className="editor-images-grid-h">
                      {result.images.map((img, idx) => (
                        <div key={`existing-${idx}`} className="editor-image-item-h">
                          <img src={img.url || img.image_url} alt={`이미지 ${idx + 1}`} />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 업로드된 이미지 미리보기 */}
                  {uploadedImages.length > 0 && (
                    <div className="uploaded-images-section">
                      <p className="uploaded-label">업로드된 이미지</p>
                      <div className="editor-images-grid-h">
                        {uploadedImages.map((img, idx) => (
                          <div key={`uploaded-${idx}`} className="editor-image-item-h uploaded">
                            <img src={img.url} alt={`업로드 이미지 ${idx + 1}`} />
                            <button
                              className="btn-remove-image"
                              onClick={() => handleRemoveUploadedImage(idx)}
                              title="이미지 삭제"
                            >
                              <FiTrash2 />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 업로드 UI (기존 이미지가 없을 때만 표시) */}
                  {(!result.images || result.images.length === 0) && (
                    <div className={`image-upload-zone ${needsImageUpload(activePlatform) ? 'required' : ''}`}>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/gif,image/webp"
                        onChange={handleImageUpload}
                        style={{ display: 'none' }}
                        id="image-upload-input"
                      />
                      <label htmlFor="image-upload-input" className="upload-label">
                        {isUploading ? (
                          <div className="uploading-state">
                            <div className="upload-spinner"></div>
                            <span>업로드 중...</span>
                          </div>
                        ) : uploadedImages.length > 0 ? (
                          <div className="upload-more">
                            <FiUpload />
                            <span>추가 이미지 업로드</span>
                          </div>
                        ) : (
                          <div className="upload-empty">
                            <FiImage className="upload-icon" />
                            <span className="upload-title">이미지를 업로드하세요</span>
                            <span className="upload-desc">Instagram 발행에는 이미지가 필요합니다</span>
                            <span className="upload-hint">JPEG, PNG, GIF, WebP (최대 10MB)</span>
                          </div>
                        )}
                      </label>
                    </div>
                  )}

                  {/* 이미지 필수 경고 */}
                  {needsImageUpload(activePlatform) && (
                    <p className="image-required-warning">
                      ⚠️ Instagram 발행을 위해서는 최소 1개의 이미지가 필요합니다.
                    </p>
                  )}
                </div>
              )}

              {/* 블로그/X/Threads용 이미지 미리보기 (기존 이미지만) */}
              {activePlatform !== 'sns' && activePlatform !== 'instagram' && result.images?.length > 0 && (
                <div className="editor-images-section">
                  <h4>첨부 이미지</h4>
                  <div className="editor-images-grid-h">
                    {result.images.map((img, idx) => (
                      <div key={idx} className="editor-image-item-h">
                        <img src={img.url || img.image_url} alt={`이미지 ${idx + 1}`} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* 예약 발행 모달 */}
      {showScheduleModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowScheduleModal(false)}>
          <div className="schedule-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3>예약 발행</h3>
              <button className="btn-close" onClick={() => setShowScheduleModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              <p className="schedule-modal-desc">
                <strong>{PLATFORM_CONFIG[activePlatform]?.name}</strong>에 발행할 시간을 선택하세요.
              </p>
              <div className="schedule-inputs">
                <div className="schedule-input-group">
                  <label>날짜</label>
                  <input
                    type="date"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div className="schedule-input-group">
                  <label>시간</label>
                  <input
                    type="time"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                  />
                </div>
              </div>
              {scheduleDate && scheduleTime && (
                <p className="schedule-preview">
                  {new Date(`${scheduleDate}T${scheduleTime}`).toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    weekday: 'long',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}에 발행됩니다.
                </p>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowScheduleModal(false)}>
                취소
              </button>
              <button
                className="btn-confirm"
                onClick={handleSchedule}
                disabled={isScheduling || !scheduleDate || !scheduleTime}
              >
                {isScheduling ? '예약 중...' : '예약하기'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentEditor;
