import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiCopy, FiSend, FiCheck, FiEdit3, FiSave } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
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
  const { result, topic } = location.state || {};

  // 편집 상태
  const [editedContent, setEditedContent] = useState({});
  const [activePlatform, setActivePlatform] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingField, setEditingField] = useState(null); // 'title' | 'content' | 'tags'

  // 저장 상태
  const [isSaved, setIsSaved] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const initialContentRef = useRef(null);

  // 발행 상태
  const [publishingPlatform, setPublishingPlatform] = useState(null);
  const [publishResults, setPublishResults] = useState({});

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

  // 저장 핸들러
  const handleSave = useCallback(async () => {
    if (isSaved || isSaving) return;

    setIsSaving(true);
    try {
      // TODO: 실제 저장 API 연동
      // 현재는 로컬 상태만 업데이트
      await new Promise(resolve => setTimeout(resolve, 500));

      initialContentRef.current = JSON.stringify(editedContent);
      setIsSaved(true);
      alert('저장되었습니다.');
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  }, [editedContent, isSaved, isSaving]);

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

  // 발행 핸들러
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

    setPublishingPlatform(platform);

    try {
      // TODO: 실제 발행 API 연동
      // 현재는 모의 발행
      await new Promise(resolve => setTimeout(resolve, 1500));

      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: true, message: '발행 완료!' },
      }));
    } catch (error) {
      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: false, message: error.message },
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
            <><FiSave /> 저장</>
          )}
        </button>
      </div>

      <div className="editor-layout">
        {/* 왼쪽: 플랫폼 탭 */}
        <div className="editor-sidebar">
          <div className="platform-tabs">
            {availablePlatforms.map(platform => (
              <button
                key={platform}
                className={`platform-tab ${activePlatform === platform ? 'active' : ''} ${publishResults[platform]?.success ? 'published' : ''}`}
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

          {/* 이미지 미리보기 */}
          {result.images?.length > 0 && (
            <div className="editor-images">
              <h4>첨부 이미지</h4>
              <div className="editor-images-grid">
                {result.images.map((img, idx) => (
                  <div key={idx} className="editor-image-item">
                    <img src={img.url} alt={`이미지 ${idx + 1}`} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 오른쪽: 편집 영역 */}
        <div className="editor-main">
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
                  className={`btn-publish-platform ${publishResults[activePlatform]?.success ? 'published' : ''}`}
                  onClick={() => handlePublish(activePlatform)}
                  disabled={publishingPlatform === activePlatform || publishResults[activePlatform]?.success}
                >
                  {publishingPlatform === activePlatform ? (
                    <>발행 중...</>
                  ) : publishResults[activePlatform]?.success ? (
                    <><FiCheck /> 발행 완료</>
                  ) : (
                    <><FiSend /> {currentConfig?.name}에 발행</>
                  )}
                </button>
              </div>

              {/* 발행 결과 메시지 */}
              {publishResults[activePlatform] && (
                <div className={`publish-result-message ${publishResults[activePlatform].success ? 'success' : 'error'}`}>
                  {publishResults[activePlatform].message}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContentEditor;
