import { useState, useEffect } from 'react';
import { FiCopy, FiTrash2 } from 'react-icons/fi';
import api, { contentSessionAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import './ContentCommon.css';
import './ContentCreatorSimple.css';

function ContentCreatorSimple() {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('create');

  // 콘텐츠 타입: 'text' | 'image' | 'both' | 'shortform' | null
  const [contentType, setContentType] = useState(null);

  // 입력 상태
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [imageCount, setImageCount] = useState(1);  // 이미지 생성 갯수

  // 이미지 업로드 상태
  const [uploadedImages, setUploadedImages] = useState([]);

  // 숏폼 영상 옵션
  const [videoDuration, setVideoDuration] = useState('standard'); // short, standard, premium

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');

  // 결과 상태
  const [result, setResult] = useState(null);

  // 생성 내역 상태
  const [history, setHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [historyDetailTab, setHistoryDetailTab] = useState('blog'); // 상세 보기 탭

  // 이미지 팝업 상태
  const [popupImage, setPopupImage] = useState(null);

  // 스타일 옵션 (글 + 이미지 모두에 적용)
  const styles = [
    { id: 'casual', label: '캐주얼', textTone: '친근하고 편안한 말투로, 이모지를 적절히 사용', imageStyle: 'casual lifestyle photography, warm natural lighting, relaxed atmosphere' },
    { id: 'professional', label: '전문적', textTone: '전문적이고 신뢰감 있는 어조로, 정확한 정보 전달', imageStyle: 'professional corporate style, clean minimalist design, sophisticated lighting' },
    { id: 'friendly', label: '친근한', textTone: '다정하고 따뜻한 말투로, 독자와 대화하듯', imageStyle: 'friendly warm tones, soft lighting, inviting and approachable mood' },
    { id: 'formal', label: '격식체', textTone: '격식있고 품위있는 문체로, 존댓말 사용', imageStyle: 'formal elegant style, classic composition, refined and prestigious look' },
    { id: 'trendy', label: '트렌디', textTone: 'MZ세대 감성으로, 신조어와 트렌디한 표현 사용', imageStyle: 'trendy modern aesthetic, vibrant colors, Gen-Z style, dynamic composition' },
    { id: 'luxurious', label: '럭셔리', textTone: '고급스럽고 세련된 톤으로, 프리미엄 가치 강조', imageStyle: 'luxury premium style, rich dark tones, gold accents, elegant and exclusive' },
    { id: 'cute', label: '귀여운', textTone: '귀엽고 발랄한 말투로, 이모지 많이 사용', imageStyle: 'cute kawaii style, pastel colors, soft rounded shapes, adorable and playful' },
    { id: 'minimal', label: '미니멀', textTone: '간결하고 핵심만 담은 문체로, 군더더기 없이', imageStyle: 'minimalist clean design, white space, simple geometric shapes, modern simplicity' },
  ];

  const platforms = [
    { id: 'sns', label: 'Instagram/Facebook' },
    { id: 'blog', label: '블로그' },
    { id: 'x', label: 'X' },
    { id: 'threads', label: 'Threads' },
  ];

  // 숏폼 영상 길이 옵션
  const videoDurationOptions = [
    { id: 'short', label: 'Short', duration: '15초', cuts: 3, description: '빠른 임팩트' },
    { id: 'standard', label: 'Standard', duration: '30초', cuts: 5, description: '균형잡힌 구성' },
    { id: 'premium', label: 'Premium', duration: '60초', cuts: 8, description: '상세한 스토리' },
  ];

  // 생성 내역 불러오기 (v2 API)
  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await contentSessionAPI.list(0, 50);
      setHistory(data);
    } catch (error) {
      console.error('생성 내역 로드 실패:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // 내역 탭 클릭 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  // 내역 아이템 선택 (상세 API 호출하여 전체 콘텐츠 가져오기)
  const handleSelectHistory = async (item) => {
    // 첫 번째 사용 가능한 탭 선택
    const firstTab = item.blog ? 'blog' : item.sns ? 'sns' : item.x ? 'x' : item.threads ? 'threads' : (item.image_count > 0 ? 'images' : 'blog');
    setHistoryDetailTab(firstTab);

    // 항상 상세 API 호출 (목록 API는 content를 포함하지 않음)
    try {
      const detail = await contentSessionAPI.get(item.id);
      setSelectedHistoryItem(detail);
    } catch (error) {
      console.error('상세 조회 실패:', error);
      setSelectedHistoryItem(item);
    }
  };

  // 내역에서 복사 (v2 구조)
  const handleCopyHistoryBlog = (item) => {
    if (!item.blog) return;
    const blogText = `${item.blog.title}\n\n${item.blog.content}\n\n태그: ${item.blog.tags?.join(', ') || ''}`;
    navigator.clipboard.writeText(blogText);
    alert('블로그 콘텐츠가 복사되었습니다.');
  };

  const handleCopyHistorySNS = (item) => {
    if (!item.sns) return;
    const snsText = `${item.sns.content}\n\n${item.sns.hashtags?.join(' ') || ''}`;
    navigator.clipboard.writeText(snsText);
    alert('SNS 콘텐츠가 복사되었습니다.');
  };

  const handleCopyHistoryX = (item) => {
    if (!item.x) return;
    const xText = `${item.x.content}\n\n${item.x.hashtags?.join(' ') || ''}`;
    navigator.clipboard.writeText(xText);
    alert('X 콘텐츠가 복사되었습니다.');
  };

  const handleCopyHistoryThreads = (item) => {
    if (!item.threads) return;
    const threadsText = `${item.threads.content}\n\n${item.threads.hashtags?.join(' ') || ''}`;
    navigator.clipboard.writeText(threadsText);
    alert('Threads 콘텐츠가 복사되었습니다.');
  };

  // 내역 삭제 (v2 API)
  const handleDeleteHistory = async (sessionId) => {
    if (!window.confirm('이 콘텐츠를 삭제하시겠습니까?')) return;
    try {
      await contentSessionAPI.delete(sessionId);
      setHistory(history.filter(item => item.id !== sessionId));
      if (selectedHistoryItem?.id === sessionId) {
        setSelectedHistoryItem(null);
      }
      alert('삭제되었습니다.');
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  // 날짜 포맷 (목록용: 올해면 월/일 시:분, 지난 년도면 yy/mm/dd 시:분)
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const currentYear = now.getFullYear();
    const dateYear = date.getFullYear();
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');

    if (dateYear === currentYear) {
      // 올해: MM/DD HH:MM
      return `${date.getMonth() + 1}/${date.getDate()} ${hh}:${min}`;
    } else {
      // 지난 년도: YY/MM/DD HH:MM
      const yy = String(dateYear).slice(-2);
      const mm = String(date.getMonth() + 1).padStart(2, '0');
      const dd = String(date.getDate()).padStart(2, '0');
      return `${yy}/${mm}/${dd} ${hh}:${min}`;
    }
  };

  // 날짜 포맷 (상세용: 올해면 M월 D일 오전/오후 H:MM, 지난 년도면 YYYY년 M월 D일 오전/오후 H:MM)
  const formatDateDetail = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const currentYear = now.getFullYear();
    const dateYear = date.getFullYear();
    const hours = date.getHours();
    const ampm = hours < 12 ? '오전' : '오후';
    const h12 = hours % 12 || 12;
    const min = String(date.getMinutes()).padStart(2, '0');

    if (dateYear === currentYear) {
      // 올해: M월 D일 오전/오후 H:MM
      return `${date.getMonth() + 1}월 ${date.getDate()}일 ${ampm} ${h12}:${min}`;
    } else {
      // 지난 년도: YYYY년 M월 D일 오전/오후 H:MM
      return `${dateYear}년 ${date.getMonth() + 1}월 ${date.getDate()}일 ${ampm} ${h12}:${min}`;
    }
  };

  // 자동 저장 함수 (v2 API - 플랫폼별 분리 저장)
  const autoSaveContent = async (content, imageUrls = [], platforms = [], currentStyle = 'casual', currentContentType = 'both', requestedImageCount = 0) => {
    try {
      const saveData = {
        // 사용자 입력값
        topic: topic,
        content_type: currentContentType,
        style: currentStyle,
        selected_platforms: platforms,

        // 플랫폼별 콘텐츠 (선택된 플랫폼만)
        blog: content.blog ? {
          title: content.blog.title,
          content: content.blog.content,
          tags: content.blog.tags,
          score: content.critique?.blog?.score || null
        } : null,

        sns: content.sns ? {
          content: content.sns.content,
          hashtags: content.sns.tags,
          score: content.critique?.sns?.score || null
        } : null,

        x: content.x ? {
          content: content.x.content,
          hashtags: content.x.tags,
          score: content.critique?.x?.score || null
        } : null,

        threads: content.threads ? {
          content: content.threads.content,
          hashtags: content.threads.tags,
          score: content.critique?.threads?.score || null
        } : null,

        // 생성된 이미지
        images: imageUrls.map(url => ({ image_url: url, prompt: topic })),
        requested_image_count: requestedImageCount,

        // AI 분석/평가 결과
        analysis_data: content.analysis || null,
        critique_data: content.critique || null,
        generation_attempts: content.metadata?.attempts || 1
      };

      await contentSessionAPI.save(saveData);
      console.log('✅ 콘텐츠 세션 저장 완료');
    } catch (error) {
      console.error('콘텐츠 저장 실패:', error);
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      alert('주제를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    setResult(null);
    setProgress('콘텐츠 생성 준비 중...');

    try {
      const generatedResult = {
        text: null,
        images: [],
      };

      // 글 생성 (agenticService 사용)
      if (contentType === 'text' || contentType === 'both') {
        setProgress('AI가 글을 작성하고 있습니다...');

        const hasBlog = selectedPlatforms.includes('blog');
        const hasSNS = selectedPlatforms.includes('sns');
        const hasX = selectedPlatforms.includes('x');
        const hasThreads = selectedPlatforms.includes('threads');

        // 선택된 스타일 정보 가져오기
        const selectedStyle = styles.find(s => s.id === style);

        // agenticService로 콘텐츠 생성 (선택된 플랫폼만, 스타일 적용)
        const agenticResult = await generateAgenticContent(
          {
            textInput: topic,
            images: [],
            styleTone: selectedStyle?.textTone || '친근하고 편안한 말투로',
            selectedPlatforms: selectedPlatforms
          },
          (progress) => setProgress(progress.message)
        );

        // 원본 agenticResult 저장 (저장용)
        generatedResult.agenticResult = agenticResult;

        // UI 표시용 (플랫폼 선택에 따라 필터링)
        generatedResult.text = {
          blog: hasBlog ? agenticResult.blog : null,
          sns: hasSNS ? agenticResult.sns : null,
          x: hasX ? agenticResult.x : null,
          threads: hasThreads ? agenticResult.threads : null,
          analysis: agenticResult.analysis,
          critique: agenticResult.critique,
          platforms: selectedPlatforms,
          style: style,
        };
      }

      // 이미지 생성 (여러 개)
      if (contentType === 'image' || contentType === 'both') {
        const generatedImages = [];

        // 선택된 스타일 정보 가져오기 (글 생성에서 이미 정의된 경우도 있음)
        const selectedStyleForImage = styles.find(s => s.id === style);
        const imageStylePrompt = selectedStyleForImage?.imageStyle || '';

        for (let i = 0; i < imageCount; i++) {
          setProgress(`AI가 이미지를 생성하고 있습니다... (${i + 1}/${imageCount})`);

          try {
            // 스타일이 적용된 프롬프트 생성
            const enhancedPrompt = imageStylePrompt
              ? `${topic}. Style: ${imageStylePrompt}`
              : topic;

            const imageResponse = await api.post('/api/generate-image', {
              prompt: enhancedPrompt,
              model: 'nanovana',  // Gemini 2.5 Flash Image 사용
            });

            if (imageResponse.data.imageUrl) {
              generatedImages.push({
                url: imageResponse.data.imageUrl,
                prompt: topic,
              });
            }
          } catch (imgError) {
            console.error(`이미지 ${i + 1} 생성 실패:`, imgError);
            // 실패해도 계속 진행
          }
        }

        generatedResult.images = generatedImages;
      }

      // 자동 저장 (글 + 이미지 모두 생성 후)
      // 선택된 플랫폼의 콘텐츠만 저장 (원본 agenticResult에서 가져옴)
      if (generatedResult.agenticResult || generatedResult.text) {
        const imageUrls = generatedResult.images?.map(img => img.url) || [];
        const platforms = generatedResult.text?.platforms || [];
        const original = generatedResult.agenticResult || {};

        await autoSaveContent({
          // 선택된 플랫폼만 저장 (원본 데이터 사용)
          blog: platforms.includes('blog') ? original.blog : null,
          sns: platforms.includes('sns') ? original.sns : null,
          x: platforms.includes('x') ? original.x : null,
          threads: platforms.includes('threads') ? original.threads : null,
          analysis: original.analysis || generatedResult.text?.analysis,
          critique: original.critique || generatedResult.text?.critique,
          metadata: { attempts: original.metadata?.attempts || 1 }
        }, imageUrls, platforms, style, contentType, imageCount);

        // 저장 후 히스토리 새로고침 (다음에 히스토리 탭 열 때 최신 데이터 표시)
        fetchHistory();
      }

      setResult(generatedResult);
      setProgress('');
      setActiveTab('result');
    } catch (error) {
      console.error('콘텐츠 생성 실패:', error);
      alert('콘텐츠 생성 중 오류가 발생했습니다.');
      setProgress('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setTopic('');
    setProgress('');
    setActiveTab('create');
  };

  const handleCopyBlog = () => {
    if (result?.text?.blog) {
      const blogText = `${result.text.blog.title}\n\n${result.text.blog.content}\n\n태그: ${result.text.blog.tags.join(', ')}`;
      navigator.clipboard.writeText(blogText);
      alert('블로그 콘텐츠가 복사되었습니다.');
    }
  };

  const handleCopySNS = () => {
    if (result?.text?.sns) {
      const snsText = `${result.text.sns.content}\n\n${result.text.sns.tags.join(' ')}`;
      navigator.clipboard.writeText(snsText);
      alert('SNS 콘텐츠가 복사되었습니다.');
    }
  };

  const handleCopyX = () => {
    if (result?.text?.x) {
      const xText = `${result.text.x.content}\n\n${result.text.x.tags.join(' ')}`;
      navigator.clipboard.writeText(xText);
      alert('X 콘텐츠가 복사되었습니다.');
    }
  };

  const handleCopyThreads = () => {
    if (result?.text?.threads) {
      const threadsText = `${result.text.threads.content}\n\n${result.text.threads.tags.join(' ')}`;
      navigator.clipboard.writeText(threadsText);
      alert('Threads 콘텐츠가 복사되었습니다.');
    }
  };

  const handleDownloadImage = (imageUrl, index) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `generated-image-${index + 1}-${Date.now()}.png`;
    link.click();
  };

  const handleDownloadAllImages = () => {
    if (result?.images?.length > 0) {
      result.images.forEach((img, index) => {
        setTimeout(() => {
          handleDownloadImage(img.url, index);
        }, index * 500);  // 0.5초 간격으로 다운로드
      });
    }
  };

  return (
    <div className="content-page">
      {/* 헤더 */}
      <div className="page-header">
        <h2>Contents 생성</h2>
        <p className="page-description">주제만 입력하면 AI가 글과 이미지를 한번에 생성합니다</p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`content-tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          콘텐츠 생성
        </button>
        {result && (
          <button
            className={`content-tab ${activeTab === 'result' ? 'active' : ''}`}
            onClick={() => setActiveTab('result')}
          >
            생성 결과
          </button>
        )}
        <button
          className={`content-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          생성 내역
        </button>
      </div>

      {/* 콘텐츠 생성 탭 */}
      {activeTab === 'create' && (
        <div className="content-grid single-column">
          <div className="form-section">
            {/* 콘텐츠 타입 선택 (가장 상단) */}
            <div className="form-group">
              <label>생성 타입</label>
              <div className="type-options type-options-4">
                <div
                  className={`type-card ${contentType === 'text' ? 'selected' : ''}`}
                  onClick={() => setContentType('text')}
                >
                  <div className="type-header">
                    <h4>글만</h4>
                  </div>
                  <p className="type-desc">블로그, SNS 캡션</p>
                </div>
                <div
                  className={`type-card ${contentType === 'image' ? 'selected' : ''}`}
                  onClick={() => setContentType('image')}
                >
                  <div className="type-header">
                    <h4>이미지만</h4>
                  </div>
                  <p className="type-desc">썸네일, 배너</p>
                </div>
                <div
                  className={`type-card ${contentType === 'both' ? 'selected' : ''}`}
                  onClick={() => setContentType('both')}
                >
                  <div className="type-header">
                    <h4>글 + 이미지</h4>
                  </div>
                  <p className="type-desc">완성 콘텐츠</p>
                </div>
                <div
                  className={`type-card ${contentType === 'shortform' ? 'selected' : ''}`}
                  onClick={() => setContentType('shortform')}
                >
                  <div className="type-header">
                    <h4>숏폼 영상</h4>
                  </div>
                  <p className="type-desc">마케팅 비디오</p>
                </div>
              </div>
            </div>

            {/* 주제 입력 */}
            <div className="form-group">
              <label>주제 *</label>
              <textarea
                className="form-textarea"
                placeholder="예: 가을 신상 니트 소개, 카페 오픈 이벤트 안내, 새로운 메뉴 출시..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                rows={3}
              />
            </div>

            {/* 이미지 업로드 (숏폼 영상 선택 시) */}
            {contentType === 'shortform' && (
              <div className="form-group">
                <label>이미지 *</label>
                <div className="image-upload-area">
                  {uploadedImages.length === 0 ? (
                    <label className="upload-label">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            if (file.size > 10 * 1024 * 1024) {
                              alert('이미지 파일 크기는 10MB 이하여야 합니다.');
                              return;
                            }
                            const reader = new FileReader();
                            reader.onloadend = () => {
                              setUploadedImages([{ file, preview: reader.result }]);
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                        className="file-input"
                      />
                      <span className="upload-icon">📸</span>
                      <span>클릭하여 이미지 업로드</span>
                      <span className="upload-hint">PNG, JPG, WebP (최대 10MB)</span>
                    </label>
                  ) : (
                    <div className="uploaded-image-preview">
                      <img src={uploadedImages[0].preview} alt="업로드된 이미지" />
                      <button
                        type="button"
                        className="btn-remove-image"
                        onClick={() => setUploadedImages([])}
                      >
                        ✕ 제거
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 스타일 선택 */}
            <div className="form-group">
              <label>스타일</label>
              <div className="option-cards">
                {styles.map((s) => (
                  <div
                    key={s.id}
                    className={`option-card ${style === s.id ? 'selected' : ''}`}
                    onClick={() => setStyle(s.id)}
                  >
                    {s.label}
                  </div>
                ))}
              </div>
            </div>

            {/* 플랫폼 선택 (글 생성 시에만) */}
            {(contentType === 'text' || contentType === 'both') && (
              <div className="form-group">
                <label>플랫폼</label>
                <div className="option-cards">
                  {platforms.map((p) => (
                    <div
                      key={p.id}
                      className={`option-card ${selectedPlatforms.includes(p.id) ? 'selected' : ''}`}
                      onClick={() => {
                        if (selectedPlatforms.includes(p.id)) {
                          if (selectedPlatforms.length > 1) {
                            setSelectedPlatforms(selectedPlatforms.filter(id => id !== p.id));
                          }
                        } else {
                          setSelectedPlatforms([...selectedPlatforms, p.id]);
                        }
                      }}
                    >
                      {p.label}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 이미지 갯수 선택 (이미지 생성 시에만) */}
            {(contentType === 'image' || contentType === 'both') && (
              <div className="form-group">
                <label>이미지 갯수</label>
                <div className="option-cards">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((count) => (
                    <div
                      key={count}
                      className={`option-card ${imageCount === count ? 'selected' : ''}`}
                      onClick={() => setImageCount(count)}
                    >
                      {count}장
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 영상 길이 선택 (숏폼 영상 선택 시에만) */}
            {contentType === 'shortform' && (
              <div className="form-group">
                <label>영상 길이</label>
                <div className="video-duration-options">
                  {videoDurationOptions.map((option) => (
                    <div
                      key={option.id}
                      className={`duration-card ${videoDuration === option.id ? 'selected' : ''}`}
                      onClick={() => setVideoDuration(option.id)}
                    >
                      <div className="duration-header">
                        <h4>{option.label}</h4>
                        <span className="duration-time">{option.duration}</span>
                      </div>
                      <div className="duration-info">
                        <span className="duration-cuts">{option.cuts}개 컷</span>
                        <span className="duration-desc">{option.description}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 생성 버튼 */}
            <button
              className="btn-generate"
              onClick={handleGenerate}
              disabled={
                isGenerating ||
                !topic.trim() ||
                !contentType ||
                (contentType !== 'image' && contentType !== 'shortform' && !style) ||
                (contentType !== 'image' && contentType !== 'shortform' && selectedPlatforms.length === 0) ||
                (contentType === 'shortform' && uploadedImages.length === 0)
              }
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  {progress}
                </>
              ) : (
                '생성하기'
              )}
            </button>
          </div>
        </div>
      )}

      {/* 결과 탭 */}
      {activeTab === 'result' && result && (
        <div className="result-content">
          {/* 생성된 이미지들 (상단) */}
          {result.images && result.images.length > 0 && (
            <div className="result-card result-images-top">
              <div className="result-card-header">
                <h3>생성된 이미지 ({result.images.length}장)</h3>
                <div className="result-card-actions">
                  {result.images.length > 1 && (
                    <button className="btn-download" onClick={handleDownloadAllImages}>
                      전체 다운로드
                    </button>
                  )}
                </div>
              </div>
              <div className="result-card-content">
                <div className="images-grid">
                  {result.images.map((img, index) => (
                    <div key={index} className="image-item" onClick={() => setPopupImage(img.url)}>
                      <img src={img.url} alt={`Generated ${index + 1}`} />
                      <button
                        className="btn-download-single"
                        onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.url, index); }}
                      >
                        다운로드
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 2열 레이아웃: 블로그 (좌) | SNS 플랫폼들 (우) */}
          <div className="result-two-column">
            {/* 좌측: 블로그 */}
            <div className="result-column-left">
              {/* 블로그 콘텐츠 */}
              {result.text?.blog && (
                <div className="result-card">
                  <div className="result-card-header">
                    <h3>네이버 블로그</h3>
                    <div className="result-card-actions">
                      <button className="btn-icon" onClick={handleCopyBlog} title="복사">
                        <FiCopy />
                      </button>
                    </div>
                  </div>
                  <div className="result-card-content">
                    <div className="blog-title">{result.text.blog.title}</div>
                    <div className="text-result">
                      {result.text.blog.content}
                    </div>
                    <div className="result-tags">
                      {result.text.blog.tags.map((tag, idx) => (
                        <span key={idx} className="tag-item">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 우측: 품질 점수 + SNS 플랫폼들 (세로 정렬) */}
            <div className="result-column-right">
              {/* 품질 점수 (우측 상단) */}
              {result.text?.critique && (
                <div className="quality-scores">
                  <div className="quality-score-card">
                    <div className="score-circle blog">
                      <span className="score-number">{result.text.critique.blog?.score || '-'}</span>
                    </div>
                    <span className="score-label">블로그 품질</span>
                  </div>
                  <div className="quality-score-card">
                    <div className="score-circle sns">
                      <span className="score-number">{result.text.critique.sns?.score || '-'}</span>
                    </div>
                    <span className="score-label">SNS 품질</span>
                  </div>
                </div>
              )}

              {/* SNS 콘텐츠 (Instagram/Facebook) */}
              {result.text?.sns && (
                <div className="result-card">
                  <div className="result-card-header">
                    <h3>Instagram / Facebook</h3>
                    <div className="result-card-actions">
                      <button className="btn-icon" onClick={handleCopySNS} title="복사">
                        <FiCopy />
                      </button>
                    </div>
                  </div>
                  <div className="result-card-content">
                    <div className="text-result sns-content">
                      {result.text.sns.content}
                    </div>
                    <div className="result-tags">
                      {result.text.sns.tags.map((tag, idx) => (
                        <span key={idx} className="tag-item hashtag">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* X 콘텐츠 */}
              {result.text?.x && (
                <div className="result-card">
                  <div className="result-card-header">
                    <h3>X</h3>
                    <div className="result-card-actions">
                      <button className="btn-icon" onClick={handleCopyX} title="복사">
                        <FiCopy />
                      </button>
                    </div>
                  </div>
                  <div className="result-card-content">
                    <div className="text-result sns-content">
                      {result.text.x.content}
                    </div>
                    <div className="result-tags">
                      {result.text.x.tags.map((tag, idx) => (
                        <span key={idx} className="tag-item hashtag">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Threads 콘텐츠 */}
              {result.text?.threads && (
                <div className="result-card">
                  <div className="result-card-header">
                    <h3>Threads</h3>
                    <div className="result-card-actions">
                      <button className="btn-icon" onClick={handleCopyThreads} title="복사">
                        <FiCopy />
                      </button>
                    </div>
                  </div>
                  <div className="result-card-content">
                    <div className="text-result sns-content">
                      {result.text.threads.content}
                    </div>
                    <div className="result-tags">
                      {result.text.threads.tags.map((tag, idx) => (
                        <span key={idx} className="tag-item hashtag">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="result-actions-bar">
            <button className="btn-reset" onClick={handleReset}>
              새로 만들기
            </button>
          </div>
        </div>
      )}

      {/* 생성 내역 탭 */}
      {activeTab === 'history' && (
        <div className="history-content">
          {isLoadingHistory ? (
            <div className="loading-state">
              <span className="spinner"></span>
              <p>생성 내역을 불러오는 중...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">📝</span>
              <h3>생성 내역이 없습니다</h3>
              <p>콘텐츠를 생성하면 여기에 저장됩니다.</p>
              <button className="btn-primary" onClick={() => setActiveTab('create')}>
                콘텐츠 생성하기
              </button>
            </div>
          ) : (
            <div className="history-layout">
              {/* 왼쪽: 내역 목록 */}
              <div className="history-list">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className={`history-item ${selectedHistoryItem?.id === item.id ? 'selected' : ''}`}
                    onClick={() => handleSelectHistory(item)}
                  >
                    <div className="history-item-header">
                      <h4>{item.topic || '주제 없음'}</h4>
                      <span className="history-date">{formatDate(item.created_at)}</span>
                    </div>
                    <div className="history-item-info">
                      <span className="info-badge type">
                        {item.content_type === 'text' ? '글만' : item.content_type === 'image' ? '이미지만' : '글+이미지'}
                      </span>
                      <span className="info-badge style">
                        {styles.find(s => s.id === item.style)?.label || item.style}
                      </span>
                    </div>
                    <div className="history-item-meta">
                      {item.blog && <span className="platform-badge">블로그</span>}
                      {item.sns && <span className="platform-badge">SNS</span>}
                      {item.x && <span className="platform-badge">X</span>}
                      {item.threads && <span className="platform-badge">Threads</span>}
                    </div>
                  </div>
                ))}
              </div>

              {/* 오른쪽: 선택된 콘텐츠 상세 */}
              <div className="history-detail">
                {selectedHistoryItem ? (
                  <>
                    {/* 세션 정보 헤더 */}
                    <div className="history-detail-header">
                      <div className="history-detail-title-row">
                        <h3>{selectedHistoryItem.topic}</h3>
                        <button className="btn-icon btn-icon-delete" onClick={() => handleDeleteHistory(selectedHistoryItem.id)} title="삭제">
                          <FiTrash2 />
                        </button>
                      </div>
                      <div className="history-detail-meta">
                        <span className="info-badge type">
                          {selectedHistoryItem.content_type === 'text' ? '글만' : selectedHistoryItem.content_type === 'image' ? '이미지만' : '글+이미지'}
                        </span>
                        <span className="info-badge style">
                          {styles.find(s => s.id === selectedHistoryItem.style)?.label || selectedHistoryItem.style}
                        </span>
                        <span className="history-date">{formatDateDetail(selectedHistoryItem.created_at)}</span>
                      </div>
                    </div>

                    {/* 플랫폼 탭 */}
                    <div className="history-detail-tabs">
                      {selectedHistoryItem.blog && (
                        <button
                          className={`history-tab ${historyDetailTab === 'blog' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('blog')}
                        >
                          블로그
                        </button>
                      )}
                      {selectedHistoryItem.sns && (
                        <button
                          className={`history-tab ${historyDetailTab === 'sns' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('sns')}
                        >
                          SNS
                        </button>
                      )}
                      {selectedHistoryItem.x && (
                        <button
                          className={`history-tab ${historyDetailTab === 'x' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('x')}
                        >
                          X
                        </button>
                      )}
                      {selectedHistoryItem.threads && (
                        <button
                          className={`history-tab ${historyDetailTab === 'threads' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('threads')}
                        >
                          Threads
                        </button>
                      )}
                      {selectedHistoryItem.images && selectedHistoryItem.images.length > 0 && (
                        <button
                          className={`history-tab ${historyDetailTab === 'images' ? 'active' : ''}`}
                          onClick={() => setHistoryDetailTab('images')}
                        >
                          이미지 ({selectedHistoryItem.images.length})
                        </button>
                      )}
                    </div>

                    {/* 탭 콘텐츠 */}
                    <div className="history-detail-content">
                      {/* 블로그 콘텐츠 */}
                      {historyDetailTab === 'blog' && selectedHistoryItem.blog && (
                        <div className="result-card">
                          <div className="result-card-header">
                            <h3>네이버 블로그</h3>
                            <div className="result-card-actions">
                              <button className="btn-icon" onClick={() => handleCopyHistoryBlog(selectedHistoryItem)} title="복사">
                                <FiCopy />
                              </button>
                            </div>
                          </div>
                          <div className="result-card-content">
                            <div className="blog-title">{selectedHistoryItem.blog.title}</div>
                            <div className="text-result">
                              {selectedHistoryItem.blog.content}
                            </div>
                            {selectedHistoryItem.blog.tags && (
                              <div className="result-tags">
                                {selectedHistoryItem.blog.tags.map((tag, idx) => (
                                  <span key={idx} className="tag-item">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* SNS 콘텐츠 */}
                      {historyDetailTab === 'sns' && selectedHistoryItem.sns && (
                        <div className="result-card">
                          <div className="result-card-header">
                            <h3>SNS (Instagram/Facebook)</h3>
                            <div className="result-card-actions">
                              <button className="btn-icon" onClick={() => handleCopyHistorySNS(selectedHistoryItem)} title="복사">
                                <FiCopy />
                              </button>
                            </div>
                          </div>
                          <div className="result-card-content">
                            <div className="text-result sns-content">
                              {selectedHistoryItem.sns.content}
                            </div>
                            {selectedHistoryItem.sns.hashtags && (
                              <div className="result-tags">
                                {selectedHistoryItem.sns.hashtags.map((tag, idx) => (
                                  <span key={idx} className="tag-item hashtag">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* X 콘텐츠 */}
                      {historyDetailTab === 'x' && selectedHistoryItem.x && (
                        <div className="result-card">
                          <div className="result-card-header">
                            <h3>X</h3>
                            <div className="result-card-actions">
                              <button className="btn-icon" onClick={() => handleCopyHistoryX(selectedHistoryItem)} title="복사">
                                <FiCopy />
                              </button>
                            </div>
                          </div>
                          <div className="result-card-content">
                            <div className="text-result sns-content">
                              {selectedHistoryItem.x.content}
                            </div>
                            {selectedHistoryItem.x.hashtags && (
                              <div className="result-tags">
                                {selectedHistoryItem.x.hashtags.map((tag, idx) => (
                                  <span key={idx} className="tag-item hashtag">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Threads 콘텐츠 */}
                      {historyDetailTab === 'threads' && selectedHistoryItem.threads && (
                        <div className="result-card">
                          <div className="result-card-header">
                            <h3>Threads</h3>
                            <div className="result-card-actions">
                              <button className="btn-icon" onClick={() => handleCopyHistoryThreads(selectedHistoryItem)} title="복사">
                                <FiCopy />
                              </button>
                            </div>
                          </div>
                          <div className="result-card-content">
                            <div className="text-result sns-content">
                              {selectedHistoryItem.threads.content}
                            </div>
                            {selectedHistoryItem.threads.hashtags && (
                              <div className="result-tags">
                                {selectedHistoryItem.threads.hashtags.map((tag, idx) => (
                                  <span key={idx} className="tag-item hashtag">{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* 생성된 이미지 */}
                      {historyDetailTab === 'images' && selectedHistoryItem.images && selectedHistoryItem.images.length > 0 && (
                        <div className="result-card result-card-full">
                          <div className="result-card-header">
                            <h3>생성된 이미지 ({selectedHistoryItem.images.length}장)</h3>
                          </div>
                          <div className="result-card-content">
                            <div className="images-grid">
                              {selectedHistoryItem.images.map((img, idx) => (
                                <div key={idx} className="image-item" onClick={() => setPopupImage(img.image_url)}>
                                  <img src={img.image_url} alt={`생성된 이미지 ${idx + 1}`} />
                                  <button
                                    className="btn-download-single"
                                    onClick={(e) => { e.stopPropagation(); handleDownloadImage(img.image_url, idx); }}
                                  >
                                    다운로드
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="empty-detail">
                    <span className="empty-icon">👈</span>
                    <p>왼쪽에서 콘텐츠를 선택하세요</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 이미지 팝업 */}
      {popupImage && (
        <div className="image-popup-overlay" onClick={() => setPopupImage(null)}>
          <div className="image-popup-content" onClick={(e) => e.stopPropagation()}>
            <button className="image-popup-close" onClick={() => setPopupImage(null)}>
              ✕
            </button>
            <img src={popupImage} alt="확대 이미지" />
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentCreatorSimple;
