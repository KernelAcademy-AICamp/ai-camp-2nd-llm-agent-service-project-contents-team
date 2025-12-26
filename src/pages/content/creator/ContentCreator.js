// 콘텐츠 생성기 통합 페이지

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiCopy, FiArrowRight, FiEdit3, FiChevronLeft, FiChevronRight, FiPlus, FiTrash2, FiMove, FiYoutube, FiX } from 'react-icons/fi';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';

// 상수 및 유틸리티
import {
  PLATFORMS,
  VIDEO_DURATION_OPTIONS,
  CONTENT_TYPES,
  IMAGE_COUNTS,
  IMAGE_FORMATS,
  ASPECT_RATIOS,
  QUICK_TOPICS
} from './constants';

import {
  copyToClipboard,
  getScoreColor,
  calcSnsAverageScore,
  collectAllTags,
  handleCopyBlog,
  handleCopySNS,
  handleCopyX,
  handleCopyThreads
} from './utils';

// 컴포넌트
import { PlatformContent, ImagePopup, OptionsPlaceholder } from './components';

// 훅
import { useContentCreator } from './hooks/useContentCreator';

// 생성기
import { generateTextContent } from './generators/TextGenerator';
import { generateAIImages, deductImageCredits } from './generators/ImageGenerator';
import {
  generateCardnewsPreview,
  generateCardnewsImages,
  deductCardnewsCredits,
  handlePageEdit as createPageEditHandler,
  handleAddPage as createAddPageHandler,
  handleDeletePage as createDeletePageHandler,
  handleDragEnd as createDragEndHandler
} from './generators/CardnewsGenerator';
import {
  startShortformGeneration,
  deductShortformCredits,
  VIDEO_PHASES
} from './generators/ShortformGenerator';

// API 및 스타일
import { creditsAPI, youtubeAPI } from '../../../services/api';
import { useVideoJob } from '../../../contexts/VideoJobContext';
import CreditChargeModal from '../../../components/credits/CreditChargeModal';
import '../ContentCreatorSimple.css';

function ContentCreator() {
  const navigate = useNavigate();
  const { addJob, activeJobs, completedJob, removeJob } = useVideoJob();

  // YouTube 발행 상태
  const [isYouTubeModalOpen, setIsYouTubeModalOpen] = useState(false);
  const [youtubeStatus, setYoutubeStatus] = useState(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishForm, setPublishForm] = useState({
    title: '',
    description: '',
    tags: '',
    privacyStatus: 'private'
  });

  // 공통 훅에서 상태와 핸들러 가져오기
  const {
    contentType,
    topic,
    selectedPlatforms,
    imageCount,
    imageFormat,
    uploadedImages,
    videoDuration,
    designTemplate,
    designTemplates,
    templateCategories,
    selectedCategory,
    previewSlide,
    aspectRatio,
    cardnewsPreview,
    isPreviewMode,
    editingPageIndex,
    isGenerating,
    progress,
    result,
    hasSavedRef,
    popupImage,
    creditBalance,
    isChargeModalOpen,
    userContext,
    snsColumnRef,
    blogCardRef,
    isGenerateDisabled,
    setContentType,
    setTopic,
    setImageCount,
    setImageFormat,
    setUploadedImages,
    setVideoDuration,
    setDesignTemplate,
    setSelectedCategory,
    setPreviewSlide,
    setAspectRatio,
    setCardnewsPreview,
    setIsPreviewMode,
    setEditingPageIndex,
    setIsGenerating,
    setProgress,
    setResult,
    setPopupImage,
    setCreditBalance,
    setIsChargeModalOpen,
    calculateRequiredCredits,
    togglePlatform,
    handleImageUpload,
    handleDownloadImage,
    handleDownloadAllImages,
    autoSaveContent,
    handleReset,
  } = useContentCreator();

  // VideoJobContext의 상태를 생성 화면에 동기화
  const videoJobId = result?.videoJobId;
  const activeJob = videoJobId ? activeJobs[String(videoJobId)] : null;
  const activeJobStep = activeJob?.currentStep;
  const activeJobProgress = activeJob?.progress;  // 백엔드에서 계산한 progress 값
  const completedJobId = completedJob?.id;
  const completedJobFailed = completedJob?.failed;
  const completedJobError = completedJob?.error;
  const completedJobVideoUrl = completedJob?.finalVideoUrl;

  useEffect(() => {
    if (!videoJobId) return;

    const jobId = String(videoJobId);

    // 진행 중인 작업 상태 동기화
    if (activeJobStep) {
      setProgress(activeJobStep);
    }

    // 완료된 작업 처리
    if (completedJobId && String(completedJobId) === jobId) {
      if (completedJobFailed) {
        setResult(prev => ({
          ...prev,
          videoStatus: 'failed',
          videoError: completedJobError
        }));
        setProgress(`영상 생성 실패: ${completedJobError}`);
      } else {
        setResult(prev => ({
          ...prev,
          videoStatus: 'completed',
          videoUrl: completedJobVideoUrl
        }));
        setProgress('숏폼 영상 생성 완료!');
      }
      // 작업 제거
      removeJob(jobId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoJobId, activeJobStep, completedJobId, completedJobFailed, completedJobError, completedJobVideoUrl]);

  // 카드뉴스 핸들러 생성
  const handlePageEditFn = createPageEditHandler(cardnewsPreview, setCardnewsPreview);
  const handleAddPageFn = createAddPageHandler(cardnewsPreview, setCardnewsPreview, setEditingPageIndex);
  const handleDeletePageFn = createDeletePageHandler(cardnewsPreview, setCardnewsPreview, editingPageIndex, setEditingPageIndex);
  const handleDragEndFn = createDragEndHandler(cardnewsPreview, setCardnewsPreview, editingPageIndex, setEditingPageIndex);

  // 미리보기 취소
  const handleCancelPreview = () => {
    setCardnewsPreview(null);
    setIsPreviewMode(false);
    setEditingPageIndex(null);
  };

  // YouTube 발행 모달 열기
  const handleOpenYouTubeModal = async () => {
    try {
      const status = await youtubeAPI.getStatus();
      setYoutubeStatus(status);

      if (!status.connected) {
        alert('YouTube 계정이 연동되어 있지 않습니다. 설정에서 YouTube를 연동해주세요.');
        return;
      }

      // 기본값 설정
      setPublishForm({
        title: topic || '새 영상',
        description: result?.text?.blog?.content?.slice(0, 500) || '',
        tags: '',
        privacyStatus: 'private'
      });
      setIsYouTubeModalOpen(true);
    } catch (error) {
      console.error('YouTube 상태 확인 실패:', error);
      alert('YouTube 연동 상태를 확인할 수 없습니다.');
    }
  };

  // YouTube 발행 실행
  const handlePublishToYouTube = async () => {
    if (!result?.videoUrl) return;

    setIsPublishing(true);
    try {
      const tagsArray = publishForm.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      const response = await youtubeAPI.uploadVideoFromUrl({
        video_url: result.videoUrl,
        title: publishForm.title,
        description: publishForm.description,
        tags: tagsArray,
        category_id: '22', // People & Blogs
        privacy_status: publishForm.privacyStatus
      });

      alert(`YouTube에 성공적으로 업로드되었습니다!\n영상 ID: ${response.video_id}`);
      setIsYouTubeModalOpen(false);

      // 새 탭에서 YouTube 영상 열기
      if (response.video_url) {
        window.open(response.video_url, '_blank');
      }
    } catch (error) {
      console.error('YouTube 업로드 실패:', error);
      alert(`YouTube 업로드 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  // 미리보기 확정 및 이미지 생성
  const handleConfirmPreview = async () => {
    if (!cardnewsPreview) return;

    setIsGenerating(true);
    setProgress('카드뉴스 이미지를 생성하고 있습니다...');

    try {
      const { images, cardCount } = await generateCardnewsImages({
        cardnewsPreview,
        designTemplate,
        aspectRatio,
        onProgress: setProgress
      });

      await deductCardnewsCredits({ setCreditBalance });

      setResult({ text: null, images });
      setCardnewsPreview(null);
      setIsPreviewMode(false);
      setEditingPageIndex(null);
      setProgress(`카드뉴스 ${cardCount}장 생성 완료!`);
    } catch (error) {
      console.error('카드뉴스 이미지 생성 실패:', error);
      alert('카드뉴스 이미지 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
      setProgress('');
    }
  };

  // 콘텐츠 생성
  const handleGenerate = async () => {
    if (!topic.trim()) {
      alert('주제를 입력해주세요.');
      return;
    }

    // 크레딧 체크
    const requiredCredits = calculateRequiredCredits();
    if (requiredCredits > 0 && creditBalance < requiredCredits) {
      const shortage = requiredCredits - creditBalance;
      const confirmCharge = window.confirm(
        `크레딧이 부족합니다.\n\n필요: ${requiredCredits} 크레딧\n보유: ${creditBalance} 크레딧\n부족: ${shortage} 크레딧\n\n충전 페이지로 이동하시겠습니까?`
      );
      if (confirmCharge) {
        setIsChargeModalOpen(true);
      }
      return;
    }

    setIsGenerating(true);
    setResult(null);
    setProgress('콘텐츠 생성 준비 중...');
    hasSavedRef.current = false;

    try {
      const generatedResult = { text: null, images: [] };

      // 글 생성
      if (contentType === 'text' || contentType === 'both') {
        const textResult = await generateTextContent({
          topic,
          selectedPlatforms,
          userContext,
          onProgress: setProgress
        });

        generatedResult.agenticResult = textResult.agenticResult;
        generatedResult.text = textResult.text;
      }

      // 이미지 생성
      if (contentType === 'image' || contentType === 'both') {
        if (imageFormat === 'cardnews') {
          // 카드뉴스 미리보기 생성
          try {
            const preview = await generateCardnewsPreview({
              topic,
              aspectRatio,
              userContext,
              onProgress: setProgress
            });

            setCardnewsPreview(preview);
            setIsPreviewMode(true);
            setIsGenerating(false);
            setProgress('');
            return;
          } catch (cardnewsError) {
            console.error('카드뉴스 미리보기 생성 실패:', cardnewsError);
            alert('카드뉴스 내용 생성 중 오류가 발생했습니다.');
          }
        } else {
          // AI 이미지 생성
          const imageResult = await generateAIImages({
            topic,
            imageCount,
            aspectRatio,
            onProgress: setProgress
          });

          generatedResult.images = imageResult.images;

          // 크레딧 차감
          if (imageResult.images.length > 0) {
            await deductImageCredits({
              imageCount,
              generatedCount: imageResult.images.length,
              setCreditBalance
            });
          }
        }
      }

      // 숏폼 영상 생성
      if (contentType === 'shortform') {
        try {
          const shortformResult = await startShortformGeneration({
            topic,
            videoDuration,
            uploadedImage: uploadedImages[0],
            onProgress: setProgress
          });

          generatedResult.videoJobId = shortformResult.jobId;
          generatedResult.videoStatus = shortformResult.videoStatus;

          // 크레딧 차감
          await deductShortformCredits({
            videoDuration,
            setCreditBalance
          });

          // VideoJobContext에 작업 등록 (폴링은 Context에서 통합 관리)
          addJob(shortformResult.jobId, topic || '숏폼 영상');

          // 즉시 결과 화면으로 전환
          setProgress('AI가 숏폼 영상을 생성하고 있습니다...');
          setResult({ ...generatedResult });
        } catch (videoError) {
          console.error('숏폼 영상 생성 실패:', videoError);
          const errorMsg = videoError.response?.data?.detail || videoError.message || '알 수 없는 오류';
          alert(`숏폼 영상 생성 중 오류가 발생했습니다: ${errorMsg}`);
          setProgress('');
        }
      }

      // 자동 저장
      if (generatedResult.agenticResult || generatedResult.text) {
        const imageUrls = generatedResult.images?.map(img => img.url) || [];
        const platforms = generatedResult.text?.platforms || [];
        const original = generatedResult.agenticResult || {};

        await autoSaveContent({
          blog: platforms.includes('blog') ? original.blog : null,
          sns: platforms.includes('sns') ? original.sns : null,
          x: platforms.includes('x') ? original.x : null,
          threads: platforms.includes('threads') ? original.threads : null,
          analysis: original.analysis || generatedResult.text?.analysis,
          critique: original.critique || generatedResult.text?.critique,
          metadata: { attempts: original.metadata?.attempts || 1 }
        }, imageUrls, platforms, 'default', contentType, imageCount);
      }

      setResult(generatedResult);
      setProgress('');
    } catch (error) {
      console.error('콘텐츠 생성 실패:', error);
      alert('콘텐츠 생성 중 오류가 발생했습니다.');
      setProgress('');
    } finally {
      setIsGenerating(false);
    }
  };

  // API Base URL
  const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  return (
    <div className="content-creator">
      {/* 카드뉴스 텍스트 미리보기 모드 */}
      {isPreviewMode && cardnewsPreview ? (
        <div className="creator-container">
          <div className="page-header">
            <h2>카드뉴스 내용 확인</h2>
            <p className="page-description">AI가 생성한 내용을 확인하고 수정한 후 이미지로 변환합니다</p>
          </div>

          <div className="cardnews-preview-container">
            {/* 미리보기 헤더 */}
            <div className="preview-header">
              <div className="preview-info">
                <span className="preview-badge">📝 미리보기</span>
                <span className="preview-count">{cardnewsPreview.pages.length}장의 카드뉴스</span>
              </div>
              <div className="preview-actions">
                <button
                  className="preview-cancel-btn"
                  onClick={handleCancelPreview}
                  disabled={isGenerating}
                >
                  취소
                </button>
                <button
                  className="preview-confirm-btn"
                  onClick={handleConfirmPreview}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <><span className="spinner"></span>{progress}</>
                  ) : (
                    <>이미지 생성하기 <FiArrowRight /></>
                  )}
                </button>
              </div>
            </div>

            {/* 페이지별 편집 카드 */}
            <DragDropContext onDragEnd={handleDragEndFn}>
              <Droppable droppableId="cardnews-pages" direction="vertical">
                {(provided) => (
                  <div
                    className="preview-pages"
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                  >
                    {cardnewsPreview.pages.map((page, index) => (
                      <Draggable
                        key={`page-${index}`}
                        draggableId={`page-${index}`}
                        index={index}
                        isDragDisabled={index === 0}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={`preview-page-card ${editingPageIndex === index ? 'editing' : ''} ${snapshot.isDragging ? 'dragging' : ''}`}
                          >
                            <div className="page-card-header">
                              <div className="page-header-left">
                                {index > 0 && (
                                  <span
                                    className="drag-handle"
                                    {...provided.dragHandleProps}
                                    title="드래그하여 순서 변경"
                                  >
                                    <FiMove />
                                  </span>
                                )}
                                <span className="preview-page-label">
                                  {index === 0 ? '📌 표지' : `📄 ${index}페이지`}
                                </span>
                              </div>
                              <div className="page-card-actions">
                                <button
                                  className="page-edit-btn"
                                  onClick={() => setEditingPageIndex(editingPageIndex === index ? null : index)}
                                >
                                  <FiEdit3 /> {editingPageIndex === index ? '완료' : '수정'}
                                </button>
                                {index > 0 && (
                                  <button
                                    className="page-delete-btn"
                                    onClick={() => handleDeletePageFn(index)}
                                    title="페이지 삭제"
                                  >
                                    <FiTrash2 />
                                  </button>
                                )}
                              </div>
                            </div>

                            {editingPageIndex === index ? (
                              // 편집 모드
                              <div className="page-edit-form">
                                <div className="edit-field">
                                  <label>제목</label>
                                  <input
                                    type="text"
                                    value={page.title}
                                    onChange={(e) => handlePageEditFn(index, 'title', e.target.value)}
                                    onKeyDown={(e) => e.stopPropagation()}
                                    placeholder="제목을 입력하세요"
                                  />
                                </div>
                                {index === 0 && (
                                  <div className="edit-field">
                                    <label>소제목</label>
                                    <textarea
                                      value={page.subtitle || ''}
                                      onChange={(e) => handlePageEditFn(index, 'subtitle', e.target.value)}
                                      onKeyDown={(e) => e.stopPropagation()}
                                      placeholder="소제목을 입력하세요"
                                      rows={3}
                                    />
                                  </div>
                                )}
                                <div className="edit-field">
                                  <label>{index === 0 ? '내용 (선택사항)' : '내용'} (줄바꿈으로 구분)</label>
                                  <textarea
                                    value={(page.content || []).join('\n')}
                                    onChange={(e) => handlePageEditFn(index, 'content', e.target.value)}
                                    onKeyDown={(e) => e.stopPropagation()}
                                    placeholder="• 내용 1&#10;• 내용 2&#10;• 내용 3"
                                    rows={6}
                                  />
                                </div>
                              </div>
                            ) : (
                              // 미리보기 모드
                              <div className="page-preview-content">
                                {cardnewsPreview.preview_images && cardnewsPreview.preview_images[index] && (
                                  <div className="preview-image-container">
                                    <img
                                      src={cardnewsPreview.preview_images[index]}
                                      alt={`페이지 ${index + 1} 미리보기`}
                                      className="preview-card-image"
                                    />
                                  </div>
                                )}
                                <div className="preview-text-content">
                                  <h4 className="preview-title">{page.title}</h4>
                                  {page.subtitle && (
                                    <p className="preview-subtitle">{page.subtitle}</p>
                                  )}
                                  {page.content && page.content.length > 0 && (
                                    <ul className="preview-content-list">
                                      {page.content.map((item, i) => (
                                        <li key={i}>{item}</li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}

                    {/* 카드 추가 버튼 */}
                    <button
                      className="add-page-card"
                      onClick={() => handleAddPageFn(cardnewsPreview.pages.length - 1)}
                    >
                      <FiPlus />
                      <span>페이지 추가</span>
                    </button>
                  </div>
                )}
              </Droppable>
            </DragDropContext>

            {/* 하단 안내 */}
            <div className="preview-footer">
              <p className="preview-tip">
                💡 카드를 드래그하여 순서를 변경할 수 있습니다. '수정' 버튼으로 내용을 편집하세요.
              </p>
            </div>
          </div>
        </div>
      ) : !result ? (
        <div className="creator-container">
          {/* 페이지 헤더 */}
          <div className="page-header">
            <h2>콘텐츠 생성</h2>
            <p className="page-description">AI로 블로그, SNS용 콘텐츠와 이미지를 생성합니다</p>
          </div>

          <div className="creator-grid">
            {/* 왼쪽: 기본 입력 */}
            <div className="creator-left">
              {/* 콘텐츠 타입 선택 */}
              <div className="creator-type-section">
                <label className="creator-label">생성 타입</label>
                <div className="creator-type-grid">
                  {CONTENT_TYPES.map(type => (
                    <div
                      key={type.id}
                      className={`creator-type-card ${contentType === type.id ? 'selected' : ''} ${isGenerating ? 'disabled' : ''}`}
                      onClick={() => !isGenerating && setContentType(type.id)}
                    >
                      {type.recommended && <span className="recommended-badge">추천</span>}
                      {type.isNew && <span className="new-badge">NEW</span>}
                      <span className="type-icon">{type.icon}</span>
                      <span className="type-label">{type.label}</span>
                      <span className="type-desc">{type.desc}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 주제 입력 */}
              <div className="creator-input-box">
                <textarea
                  className="creator-textarea"
                  placeholder="무엇에 대한 콘텐츠를 만들까요? 예: 가을 신상 니트 소개"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={3}
                  disabled={isGenerating}
                />
                <button
                  className="creator-generate-btn"
                  onClick={handleGenerate}
                  disabled={isGenerateDisabled}
                >
                  {isGenerating ? (
                    <><span className="spinner"></span>{progress}</>
                  ) : (
                    <>
                      생성하기 <FiArrowRight className="btn-arrow" />
                      {calculateRequiredCredits() > 0 && (
                        <span className="credit-cost-badge">
                          {calculateRequiredCredits()} 크레딧
                        </span>
                      )}
                    </>
                  )}
                </button>
              </div>

              {/* 빠른 시작 */}
              <div className="creator-quick-options">
                <span className="quick-label">빠른 시작:</span>
                {QUICK_TOPICS.map(t => (
                  <button key={t} className="quick-chip" onClick={() => setTopic(t)} disabled={isGenerating}>{t}</button>
                ))}
              </div>

            </div>

            {/* 오른쪽: 타입별 옵션 */}
            <div className="creator-right">
              {!contentType ? (
                <OptionsPlaceholder />
              ) : (
                <div className="creator-options-panel">
                  <h3 className="options-title">옵션 설정</h3>

                  {/* 이미지 형태 선택 */}
                  {contentType === 'image' && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 형태</label>
                      <div className="creator-chips">
                        {IMAGE_FORMATS.map(format => (
                          <button
                            key={format.id}
                            className={`creator-chip ${imageFormat === format.id ? 'selected' : ''}`}
                            onClick={() => setImageFormat(format.id)}
                            disabled={isGenerating}
                          >
                            {format.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 비율 선택 - 카드뉴스, AI 이미지, 글+이미지 모드에서 표시 */}
                  {(contentType === 'both' ||
                    (contentType === 'image' && (imageFormat === 'cardnews' || imageFormat === 'ai-image'))) && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 비율</label>
                      <div className="creator-chips">
                        {ASPECT_RATIOS.map(ratio => (
                          <button
                            key={ratio.id}
                            className={`creator-chip ${aspectRatio === ratio.id ? 'selected' : ''}`}
                            onClick={() => setAspectRatio(ratio.id)}
                            title={ratio.desc}
                            disabled={isGenerating}
                          >
                            {ratio.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 디자인 템플릿 선택 */}
                  {contentType === 'image' && imageFormat === 'cardnews' && templateCategories.length > 0 && (
                    <div className="creator-option-section">
                      <label className="creator-label">디자인 템플릿</label>

                      <div className="template-category-tabs">
                        <button
                          className={`category-tab no-template-tab ${designTemplate === 'none' ? 'active' : ''}`}
                          onClick={() => setDesignTemplate('none')}
                          title="템플릿 없이 AI 이미지와 텍스트만 사용합니다"
                          disabled={isGenerating}
                        >
                          <span className="category-icon">🖼️</span>
                          <span className="category-name">선택 안함</span>
                        </button>
                        {templateCategories.map(category => (
                          <button
                            key={category.id}
                            className={`category-tab ${selectedCategory === category.id && designTemplate !== 'none' ? 'active' : ''}`}
                            onClick={() => {
                              setSelectedCategory(category.id);
                              if (designTemplate === 'none') {
                                const firstTemplate = category.templates?.[0];
                                if (firstTemplate) setDesignTemplate(firstTemplate.id);
                              }
                            }}
                            title={category.description}
                            disabled={isGenerating}
                          >
                            <span className="category-icon">{category.icon}</span>
                            <span className="category-name">{category.name}</span>
                          </button>
                        ))}
                      </div>

                      {designTemplate !== 'none' && (
                        <div className="creator-template-grid">
                          {templateCategories
                            .find(cat => cat.id === selectedCategory)
                            ?.templates.map(template => (
                              <button
                                key={template.id}
                                className={`creator-template-card ${designTemplate === template.id ? 'selected' : ''}`}
                                onClick={() => setDesignTemplate(template.id)}
                                title={template.description}
                                disabled={isGenerating}
                              >
                                <span
                                  className="template-color-preview"
                                  style={{ backgroundColor: template.preview_color }}
                                />
                                <span className="template-name">{template.name}</span>
                              </button>
                            ))}
                        </div>
                      )}

                      {designTemplate && designTemplate !== 'none' && (() => {
                        const selectedTemplate = designTemplates.find(t => t.id === designTemplate);
                        const previewImages = selectedTemplate?.preview_images;

                        return (
                          <div className="template-preview-section">
                            <label className="creator-label">미리보기</label>
                            <div className="template-preview-slider">
                              <button
                                className="preview-nav-btn prev"
                                onClick={() => setPreviewSlide(prev => prev === 0 ? 1 : 0)}
                                aria-label="이전 슬라이드"
                              >
                                <FiChevronLeft />
                              </button>

                              <div className="preview-slides-container">
                                <div className="preview-slides" style={{ transform: `translateX(-${previewSlide * 100}%)` }}>
                                  <div className="preview-slide">
                                    <div className="template-preview-card template-preview-image">
                                      {previewImages?.cover ? (
                                        <img
                                          src={`${apiBaseUrl}${previewImages.cover}`}
                                          alt={`${selectedTemplate?.name} 표지`}
                                          className="preview-img"
                                        />
                                      ) : (
                                        <div className="preview-placeholder">미리보기 없음</div>
                                      )}
                                    </div>
                                    <span className="slide-label">표지</span>
                                  </div>

                                  <div className="preview-slide">
                                    <div className="template-preview-card template-preview-image">
                                      {previewImages?.content ? (
                                        <img
                                          src={`${apiBaseUrl}${previewImages.content}`}
                                          alt={`${selectedTemplate?.name} 내용`}
                                          className="preview-img"
                                        />
                                      ) : (
                                        <div className="preview-placeholder">미리보기 없음</div>
                                      )}
                                    </div>
                                    <span className="slide-label">내용</span>
                                  </div>
                                </div>
                              </div>

                              <button
                                className="preview-nav-btn next"
                                onClick={() => setPreviewSlide(prev => prev === 1 ? 0 : 1)}
                                aria-label="다음 슬라이드"
                              >
                                <FiChevronRight />
                              </button>
                            </div>

                            <div className="preview-indicators">
                              <button
                                className={`indicator ${previewSlide === 0 ? 'active' : ''}`}
                                onClick={() => setPreviewSlide(0)}
                                aria-label="표지 보기"
                              />
                              <button
                                className={`indicator ${previewSlide === 1 ? 'active' : ''}`}
                                onClick={() => setPreviewSlide(1)}
                                aria-label="내용 보기"
                              />
                            </div>

                            <p className="template-description-text">
                              {selectedTemplate?.description}
                            </p>
                          </div>
                        );
                      })()}
                    </div>
                  )}

                  {/* 플랫폼 선택 */}
                  {(contentType === 'text' || contentType === 'both') && (
                    <div className="creator-option-section">
                      <label className="creator-label">플랫폼</label>
                      <div className="creator-chips">
                        {PLATFORMS.map(p => (
                          <button
                            key={p.id}
                            className={`creator-chip ${selectedPlatforms.includes(p.id) ? 'selected' : ''}`}
                            onClick={() => togglePlatform(p.id)}
                            disabled={isGenerating}
                          >
                            {p.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 갯수 선택 */}
                  {(contentType === 'both' || (contentType === 'image' && imageFormat === 'ai-image')) && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 갯수</label>
                      <div className="creator-chips">
                        {IMAGE_COUNTS.map(count => (
                          <button
                            key={count}
                            className={`creator-chip ${imageCount === count ? 'selected' : ''}`}
                            onClick={() => setImageCount(count)}
                            disabled={isGenerating}
                          >
                            {count}장
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 업로드 (숏폼 영상) */}
                  {contentType === 'shortform' && (
                    <div className="creator-option-section">
                      <label className="creator-label">이미지 업로드 *</label>
                      <div className={`creator-upload-area ${isGenerating ? 'disabled' : ''}`}>
                        {uploadedImages.length === 0 ? (
                          <label className={`upload-label ${isGenerating ? 'disabled' : ''}`}>
                            <input type="file" accept="image/*" onChange={handleImageUpload} className="file-input" disabled={isGenerating} />
                            <span className="upload-icon">📸</span>
                            <span>클릭하여 이미지 업로드</span>
                            <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                          </label>
                        ) : (
                          <div className="uploaded-preview">
                            <img src={uploadedImages[0].preview} alt="업로드된 이미지" />
                            <button type="button" className="btn-remove" onClick={() => setUploadedImages([])} disabled={isGenerating}>✕</button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 영상 길이 선택 */}
                  {contentType === 'shortform' && (
                    <div className="creator-option-section">
                      <label className="creator-label">영상 길이</label>
                      <div className="creator-duration-grid">
                        {VIDEO_DURATION_OPTIONS.map(option => (
                          <div
                            key={option.id}
                            className={`creator-duration-card ${videoDuration === option.id ? 'selected' : ''} ${isGenerating ? 'disabled' : ''}`}
                            onClick={() => !isGenerating && setVideoDuration(option.id)}
                          >
                            <span className="duration-label">{option.label}</span>
                            <span className="duration-time">{option.duration}</span>
                            <span className="duration-info">{option.cuts}컷 · {option.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* 결과 화면 */
        <div className="creator-result">
          <div className="result-header">
            {contentType === 'shortform' && result.videoStatus === 'processing' ? (
              <>
                <h2 className="result-title">생성 중..</h2>
                <p className="result-subtitle">"{topic}" 주제로 숏폼 영상을 생성하고 있습니다</p>
              </>
            ) : (
              <>
                <h2 className="result-title">생성 완료!</h2>
                <p className="result-subtitle">"{topic}" 주제로 콘텐츠가 생성되었습니다</p>
              </>
            )}
          </div>

          {/* 생성된 이미지 */}
          {result.images?.length > 0 && (
            <div className="creator-result-card result-images-section">
              <div className="creator-result-card-header">
                <h3>생성된 이미지 ({result.images.length}장)</h3>
                {result.images.length > 1 && (
                  <button className="btn-download" onClick={handleDownloadAllImages}>전체 다운로드</button>
                )}
              </div>
              <div className="creator-result-card-content">
                <div className="creator-images-grid">
                  {result.images.map((img, index) => (
                    <div key={index} className="creator-image-item" onClick={() => setPopupImage(img.url)}>
                      <img src={img.url} alt={`Generated ${index + 1}`} />
                      <button className="btn-download-overlay" onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.url, index); }}>
                        다운로드
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 생성된 비디오 */}
          {result.videoUrl && (
            <div className="creator-result-card result-video-section">
              <div className="creator-result-card-header">
                <h3>생성된 숏폼 영상</h3>
              </div>
              <div className="creator-result-card-content">
                <div className="creator-video-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <video
                    controls
                    style={{
                      width: '100%',
                      maxWidth: '400px',
                      aspectRatio: '9/16',
                      borderRadius: '8px',
                      backgroundColor: '#000'
                    }}
                  >
                    <source src={result.videoUrl} type="video/mp4" />
                    브라우저가 비디오를 지원하지 않습니다.
                  </video>
                  <div style={{ marginTop: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <a href={result.videoUrl} download className="btn-download">
                      비디오 다운로드
                    </a>
                    <button
                      onClick={handleOpenYouTubeModal}
                      className="btn-youtube-publish"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '10px 20px',
                        backgroundColor: '#FF0000',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseOver={(e) => e.target.style.backgroundColor = '#CC0000'}
                      onMouseOut={(e) => e.target.style.backgroundColor = '#FF0000'}
                    >
                      <FiYoutube size={18} />
                      YouTube 발행
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 비디오 생성 중 */}
          {result.videoStatus === 'processing' && (() => {
            // 백엔드에서 계산한 progress 값 사용 (팝업과 동기화)
            const progressPercent = activeJobProgress || 5;
            // 현재 단계 계산 (progress 기반)
            let currentPhase = 0;
            if (progressPercent >= 55) currentPhase = 3;  // 최종 합성
            else if (progressPercent >= 50) currentPhase = 2;  // 전환 비디오 생성
            else if (progressPercent >= 25) currentPhase = 1;  // 이미지 생성
            else currentPhase = 0;  // 스토리보드 생성

            return (
              <div className="creator-result-card result-video-section">
                <div className="creator-result-card-header">
                  <h3>숏폼 영상 생성 중...</h3>
                </div>
                <div className="creator-result-card-content">
                  <div style={{ padding: '40px' }}>
                    {/* 전체 프로그레스바 */}
                    <div style={{ marginBottom: '32px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', fontWeight: '500' }}>전체 진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600', color: '#D8BFD8' }}>{Math.round(progressPercent)}%</span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        backgroundColor: '#F8F8FF',
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${progressPercent}%`,
                          height: '100%',
                          backgroundColor: '#D8BFD8',
                          transition: 'width 0.5s ease',
                          borderRadius: '4px'
                        }}></div>
                      </div>
                    </div>

                    {/* 단계별 표시 */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: '16px',
                      marginBottom: '24px'
                    }}>
                      {VIDEO_PHASES.map((phase, index) => (
                        <div key={index} style={{
                          padding: '16px',
                          borderRadius: '8px',
                          border: `2px solid ${currentPhase === index ? '#D8BFD8' : currentPhase > index ? '#E6E6FA' : '#F8F8FF'}`,
                          backgroundColor: currentPhase === index ? '#E6E6FA' : currentPhase > index ? '#F8F8FF' : '#fff',
                          textAlign: 'center',
                          transition: 'all 0.3s ease'
                        }}>
                          <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                            {phase.icon}
                          </div>
                          <div style={{
                            fontSize: '12px',
                            fontWeight: currentPhase === index ? '600' : '500',
                            color: currentPhase === index ? '#D8BFD8' : currentPhase > index ? '#6b7280' : '#9ca3af'
                          }}>
                            {phase.name}
                          </div>
                          {currentPhase === index && (
                            <div style={{ marginTop: '8px' }}>
                              <div className="spinner" style={{ margin: '0 auto', width: '16px', height: '16px', borderWidth: '2px', borderColor: '#D8BFD8 transparent #D8BFD8 transparent' }}></div>
                            </div>
                          )}
                          {currentPhase > index && (
                            <div style={{ marginTop: '8px', fontSize: '16px', color: '#D8BFD8' }}>✓</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* 현재 작업 표시 */}
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
                        현재 작업
                      </p>
                      <p style={{ fontSize: '15px', fontWeight: '500', color: '#111827' }}>
                        {progress || 'AI가 영상을 생성하고 있습니다...'}
                      </p>
                    </div>

                    {/* 다른 기능 둘러보기 버튼 */}
                    <div style={{ textAlign: 'center', marginTop: '32px' }}>
                      <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '12px' }}>
                        영상 생성은 백그라운드에서 계속 진행됩니다
                      </p>
                      <button
                        onClick={() => {
                          // VideoJobContext에 작업 등록 후 홈으로 이동
                          if (result.videoJobId) {
                            addJob(result.videoJobId, topic || '숏폼 영상');
                          }
                          navigate('/');
                        }}
                        style={{
                          padding: '12px 24px',
                          backgroundColor: '#f3f4f6',
                          color: '#374151',
                          border: 'none',
                          borderRadius: '8px',
                          fontSize: '14px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#e5e7eb'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                      >
                        다른 기능 둘러보기
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* 비디오 생성 실패 */}
          {result.videoStatus === 'failed' && (
            <div className="creator-result-card result-video-section">
              <div className="creator-result-card-header">
                <h3>영상 생성 실패</h3>
              </div>
              <div className="creator-result-card-content">
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#ef4444' }}>❌ {result.videoError || '알 수 없는 오류가 발생했습니다.'}</p>
                  <button className="btn-reset" onClick={handleReset} style={{ marginTop: '16px' }}>
                    다시 시도
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 품질 점수 */}
          {result.text?.critique && (
            <div className="creator-quality-scores">
              <div className="quality-score-item">
                <div className="score-circle blog">
                  <span className="score-number">{result.text.critique.blog?.score || '-'}</span>
                </div>
                <span className="score-label">블로그</span>
              </div>
              <div className="quality-score-item">
                <div className="score-circle sns">
                  <span className="score-number">{calcSnsAverageScore(result.text.critique) || '-'}</span>
                </div>
                <span className="score-label">SNS 평균</span>
              </div>
            </div>
          )}

          {/* 통합 태그 섹션 */}
          {result.text && (() => {
            const allTags = collectAllTags(result.text);
            if (allTags.length === 0) return null;
            return (
              <div className="creator-all-tags">
                <div className="tags-header">
                  <span className="tags-label">태그</span>
                  <button
                    className="btn-icon btn-copy-tags"
                    onClick={() => copyToClipboard(allTags.join(' '), '태그가 복사되었습니다!')}
                    title="전체 태그 복사"
                  >
                    <FiCopy />
                  </button>
                </div>
                <div className="tags-list">
                  {allTags.map((tag, idx) => (
                    <span key={idx} className="creator-tag-item hashtag">{tag}</span>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* 텍스트 결과 */}
          <div className="creator-result-grid">
            <div className="result-column blog-column">
              {result.text?.blog && (
                <div className="creator-result-card" ref={blogCardRef}>
                  <div className="creator-result-card-header">
                    <h3>
                      네이버 블로그
                      {result.text?.critique?.blog?.score != null && (
                        <span className="header-score" style={{ color: getScoreColor(result.text.critique.blog.score) }}>
                          {result.text.critique.blog.score}점
                        </span>
                      )}
                    </h3>
                    <button className="btn-icon" onClick={() => handleCopyBlog({ blog: result.text.blog })} title="복사">
                      <FiCopy />
                    </button>
                  </div>
                  <div className="creator-result-card-content">
                    <div className="creator-blog-title">{result.text.blog.title}</div>
                    <div className="creator-text-result markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkBreaks]}>{result.text.blog.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="result-column sns-column" ref={snsColumnRef}>
              <PlatformContent platform="sns" data={result.text?.sns} onCopy={() => handleCopySNS({ sns: result.text.sns })} score={result.text?.critique?.sns?.score} />
              <PlatformContent platform="x" data={result.text?.x} onCopy={() => handleCopyX({ x: result.text.x })} score={result.text?.critique?.x?.score} />
              <PlatformContent platform="threads" data={result.text?.threads} onCopy={() => handleCopyThreads({ threads: result.text.threads })} score={result.text?.critique?.threads?.score} />
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="creator-result-actions">
            <button className="btn-reset" onClick={handleReset}>새로 만들기</button>
            {result.text && (
              <button
                className="btn-edit-publish"
                onClick={() => navigate('/editor', { state: { result, topic } })}
              >
                <FiEdit3 /> 편집 & 발행
              </button>
            )}
          </div>
        </div>
      )}

      {/* 이미지 팝업 */}
      <ImagePopup imageUrl={popupImage} onClose={() => setPopupImage(null)} />

      {/* YouTube 발행 모달 */}
      {isYouTubeModalOpen && (
        <div className="modal-overlay" style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="modal-content" style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '24px',
            width: '90%',
            maxWidth: '500px',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiYoutube color="#FF0000" size={24} />
                YouTube 발행
              </h2>
              <button
                onClick={() => setIsYouTubeModalOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <FiX size={24} />
              </button>
            </div>

            {youtubeStatus?.channel_title && (
              <div style={{
                backgroundColor: '#f0f9ff',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '14px'
              }}>
                <strong>채널:</strong> {youtubeStatus.channel_title}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500' }}>제목 *</label>
                <input
                  type="text"
                  value={publishForm.title}
                  onChange={(e) => setPublishForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="영상 제목을 입력하세요"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500' }}>설명</label>
                <textarea
                  value={publishForm.description}
                  onChange={(e) => setPublishForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="영상 설명을 입력하세요"
                  rows={4}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '14px',
                    resize: 'vertical',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500' }}>태그 (쉼표로 구분)</label>
                <input
                  type="text"
                  value={publishForm.tags}
                  onChange={(e) => setPublishForm(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="예: 일상, vlog, 여행"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500' }}>공개 설정</label>
                <select
                  value={publishForm.privacyStatus}
                  onChange={(e) => setPublishForm(prev => ({ ...prev, privacyStatus: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="private">비공개</option>
                  <option value="unlisted">일부 공개</option>
                  <option value="public">전체 공개</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setIsYouTubeModalOpen(false)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: 'white',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                취소
              </button>
              <button
                onClick={handlePublishToYouTube}
                disabled={isPublishing || !publishForm.title.trim()}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '8px',
                  backgroundColor: isPublishing ? '#ccc' : '#FF0000',
                  color: 'white',
                  cursor: isPublishing ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {isPublishing ? (
                  <>업로드 중...</>
                ) : (
                  <>
                    <FiYoutube size={16} />
                    업로드
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 크레딧 충전 모달 */}
      <CreditChargeModal
        isOpen={isChargeModalOpen}
        onClose={() => setIsChargeModalOpen(false)}
        onChargeComplete={() => {
          creditsAPI.getBalance().then(data => setCreditBalance(data.balance));
        }}
      />
    </div>
  );
}

export default ContentCreator;
