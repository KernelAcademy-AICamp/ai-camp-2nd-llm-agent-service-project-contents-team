import { useState } from 'react';
import './ContentCommon.css';
import './ImageGenerator.css';

function ImageGenerator() {
  // 탭 상태: 'image' (AI 이미지 생성) 또는 'cardnews' (카드뉴스)
  const [activeTab, setActiveTab] = useState('image');

  // AI 이미지 생성 상태
  const [aiModel, setAiModel] = useState('whisk');
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [referenceImage, setReferenceImage] = useState(null);
  const [generationMode, setGenerationMode] = useState('text');

  // 카드뉴스 상태
  const [titles, setTitles] = useState(['']);
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isCardGenerating, setIsCardGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState('');
  const [previewCards, setPreviewCards] = useState([]);
  const [agenticAnalysis, setAgenticAnalysis] = useState(null);
  const [pagePlans, setPagePlans] = useState([]);
  const [colorTheme, setColorTheme] = useState('black');
  const [layoutStyle, setLayoutStyle] = useState('center');
  const [fontWeight, setFontWeight] = useState('bold');

  // 카드뉴스 이미지 업로드 상태
  const MAX_CARDNEWS_IMAGES = 5;
  const [cardnewsImages, setCardnewsImages] = useState([]);
  const [cardnewsTexts, setCardnewsTexts] = useState([]);
  const [cardnewsMode, setCardnewsMode] = useState('ai'); // 'ai' or 'custom'

  const aiModels = [
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Google' },
  ];

  // AI 이미지 생성 핸들러
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setReferenceImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) {
      alert('이미지 생성을 위한 프롬프트를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    try {
      const requestBody = {
        prompt: imagePrompt,
        model: aiModel,
      };

      if (generationMode === 'image' && referenceImage) {
        requestBody.referenceImage = referenceImage;
      }

      const response = await fetch('http://localhost:8000/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = '이미지 생성에 실패했습니다.';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `서버 오류: ${response.status}`;
        }
        alert(errorMessage);
        console.error('Image generation failed:', responseText);
        return;
      }

      const data = JSON.parse(responseText);
      setGeneratedImage(data.imageUrl);

      if (data.optimizedPrompt) {
        console.log('최적화된 프롬프트:', data.optimizedPrompt);
      }
    } catch (error) {
      console.error('Image generation error:', error);
      alert('이미지 생성 중 오류가 발생했습니다. 콘솔을 확인해주세요.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadImage = () => {
    if (!generatedImage) return;

    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `generated_image_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setGeneratedImage(null);
    setImagePrompt('');
    setReferenceImage(null);
  };

  // 카드뉴스 핸들러
  const handleTitleChange = (index, value) => {
    const newTitles = [...titles];
    newTitles[index] = value;
    setTitles(newTitles);
  };

  // 카드뉴스 이미지 업로드 핸들러
  const handleCardnewsImageUpload = (e) => {
    const files = Array.from(e.target.files);
    const remainingSlots = MAX_CARDNEWS_IMAGES - cardnewsImages.length;

    if (remainingSlots <= 0) {
      alert(`최대 ${MAX_CARDNEWS_IMAGES}개의 이미지만 업로드할 수 있습니다.`);
      return;
    }

    const filesToAdd = files.slice(0, remainingSlots);

    if (files.length > remainingSlots) {
      alert(`최대 ${MAX_CARDNEWS_IMAGES}개까지만 업로드 가능합니다. ${filesToAdd.length}개만 추가됩니다.`);
    }

    filesToAdd.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCardnewsImages(prev => {
          if (prev.length >= MAX_CARDNEWS_IMAGES) return prev;
          return [...prev, {
            file: file,
            preview: event.target.result,
            name: file.name
          }];
        });
        setCardnewsTexts(prev => [...prev, '']);
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  };

  // 업로드된 이미지 삭제
  const handleRemoveCardnewsImage = (index) => {
    setCardnewsImages(prev => prev.filter((_, i) => i !== index));
    setCardnewsTexts(prev => prev.filter((_, i) => i !== index));
  };

  // 커스텀 텍스트 변경
  const handleCardnewsTextChange = (index, value) => {
    const newTexts = [...cardnewsTexts];
    newTexts[index] = value;
    setCardnewsTexts(newTexts);
  };

  // 커스텀 카드뉴스 생성 (이미지 업로드 방식)
  const handleGenerateCustomCardNews = async () => {
    if (cardnewsImages.length === 0) {
      alert('이미지를 먼저 업로드해주세요.');
      return;
    }

    setIsCardGenerating(true);
    setGeneratedCards([]);
    setGeneratingStatus('카드뉴스 생성 중...');

    try {
      const formData = new FormData();

      cardnewsImages.forEach((img) => {
        formData.append('images', img.file);
      });

      formData.append('texts', JSON.stringify(cardnewsTexts));
      formData.append('colorTheme', colorTheme);
      formData.append('fontWeight', fontWeight);
      formData.append('layoutType', layoutStyle);

      const response = await fetch('/api/generate-custom-cardnews', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`서버 오류: HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setGeneratedCards(result.cards);
        alert(`${result.cards.length}장의 카드뉴스가 생성되었습니다!`);
      } else {
        throw new Error(result.error || '카드 생성 실패');
      }
    } catch (error) {
      console.error('카드뉴스 생성 오류:', error);
      alert(`카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
    } finally {
      setIsCardGenerating(false);
      setGeneratingStatus('');
    }
  };

  const handleGenerateAgenticCardNews = async () => {
    if (titles[0].trim().length < 10) {
      alert('카드뉴스로 만들고 싶은 내용을 최소 10자 이상 입력해주세요.');
      return;
    }

    setIsCardGenerating(true);
    setGeneratedCards([]);
    setPreviewCards([]);
    setAgenticAnalysis(null);
    setPagePlans([]);
    setGeneratingStatus('AI 작업 시작...');

    try {
      const formData = new FormData();
      formData.append('prompt', titles[0]);
      formData.append('colorTheme', colorTheme);
      formData.append('fontWeight', fontWeight);
      formData.append('layoutType', layoutStyle);
      formData.append('generateImages', 'true');

      const response = await fetch('/api/generate-agentic-cardnews-stream', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`서버 오류: HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const cards = [];
      const plans = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          const raw = line.slice(6).trim();
          if (!(raw.startsWith('{') && raw.endsWith('}'))) continue;

          let data;
          try {
            data = JSON.parse(raw);
          } catch (err) {
            console.error('JSON 파싱 실패:', err);
            continue;
          }

          if (data.type === 'status') {
            setGeneratingStatus(data.message);
          } else if (data.type === 'page_planned') {
            plans.push({ page: data.page, title: data.title, content: data.content });
            setPagePlans([...plans]);
          } else if (data.type === 'card') {
            cards.push(data.card);
            setPreviewCards([...cards]);
          } else if (data.type === 'complete') {
            setGeneratedCards(cards);
            setAgenticAnalysis({
              pageCount: data.count,
              targetAudience: data.target_audience,
              tone: data.tone,
              qualityScore: data.quality_score,
              pagesInfo: plans
            });
            setGeneratingStatus('');

            alert(`${data.count}장의 AI 카드뉴스가 생성되었습니다!\n\n` +
                  `품질 점수: ${data.quality_score ? data.quality_score.toFixed(1) : 'N/A'}/10\n` +
                  `타겟: ${data.target_audience || 'N/A'}\n` +
                  `톤: ${data.tone || 'N/A'}`);
          } else if (data.type === 'error') {
            throw new Error(data.message);
          }
        }
      }
    } catch (error) {
      console.error('AI 카드뉴스 생성 오류:', error);
      alert(`AI 카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
      setGeneratingStatus('');
    } finally {
      setIsCardGenerating(false);
    }
  };

  const handleDownloadCard = (cardBase64, index) => {
    const link = document.createElement('a');
    link.href = cardBase64;
    link.download = `cardnews_${index + 1}.png`;
    link.click();
  };

  const handleDownloadAll = () => {
    generatedCards.forEach((card, index) => {
      setTimeout(() => {
        handleDownloadCard(card, index);
      }, index * 200);
    });
  };

  return (
    <div className="content-page">
      <div className="page-header">
        <h1>AI 이미지 생성</h1>
        <p className="page-description">
          AI를 활용하여 이미지를 생성하거나 카드뉴스를 만들어보세요.
        </p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="content-tabs">
        <button
          className={`content-tab ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => setActiveTab('image')}
        >
          이미지 생성
        </button>
        <button
          className={`content-tab ${activeTab === 'cardnews' ? 'active' : ''}`}
          onClick={() => setActiveTab('cardnews')}
        >
          카드뉴스 생성
        </button>
      </div>

      {/* AI 이미지 생성 탭 */}
      {activeTab === 'image' && (
        <div className="content-grid">
          <div className="form-section">
            {/* AI 모델 선택 */}
            <div className="section">
              <h3>AI 모델 선택</h3>
              <select
                className="model-select"
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
              >
                {aiModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
                  </option>
                ))}
              </select>
              <p className="model-provider">
                {aiModels.find(m => m.id === aiModel)?.provider} 제공
              </p>
            </div>

            {/* 생성 모드 선택 */}
            <div className="section">
              <h3>생성 모드 선택</h3>
              <div className="mode-buttons">
                <button
                  className={`mode-button ${generationMode === 'text' ? 'active' : ''}`}
                  onClick={() => {
                    setGenerationMode('text');
                    setReferenceImage(null);
                  }}
                >
                  <div className="mode-icon">T</div>
                  <div className="mode-title">텍스트 - 이미지</div>
                  <div className="mode-desc">텍스트 설명으로 이미지 생성</div>
                </button>
                <button
                  className={`mode-button ${generationMode === 'image' ? 'active' : ''}`}
                  onClick={() => setGenerationMode('image')}
                >
                  <div className="mode-icon">I</div>
                  <div className="mode-title">이미지 - 이미지</div>
                  <div className="mode-desc">레퍼런스 이미지 기반 생성</div>
                </button>
              </div>

              {/* 레퍼런스 이미지 업로드 */}
              {generationMode === 'image' && (
                <div className="reference-upload">
                  <label htmlFor="reference-image-upload" className="upload-label">
                    <input
                      id="reference-image-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      style={{ display: 'none' }}
                    />
                    {referenceImage ? (
                      <div className="uploaded-preview">
                        <img src={referenceImage} alt="Reference" />
                        <p className="upload-success">레퍼런스 이미지 업로드됨 (클릭하여 변경)</p>
                      </div>
                    ) : (
                      <div className="upload-placeholder">
                        <div className="upload-icon">+</div>
                        <p className="upload-title">레퍼런스 이미지 업로드</p>
                        <p className="upload-hint">클릭하여 이미지 파일 선택</p>
                      </div>
                    )}
                  </label>
                </div>
              )}
            </div>

            {/* 프롬프트 입력 */}
            <div className="section">
              <h3>이미지 프롬프트</h3>
              <textarea
                className="prompt-textarea"
                placeholder={
                  generationMode === 'text'
                    ? '생성할 이미지를 설명해주세요. 예: 해질녘의 평화로운 호숫가 풍경, 수채화 스타일'
                    : '레퍼런스 이미지를 어떻게 변경할지 설명해주세요.'
                }
                value={imagePrompt}
                onChange={(e) => setImagePrompt(e.target.value)}
                rows={5}
              />
            </div>

            {/* 생성 버튼 */}
            <button
              className="btn-generate"
              onClick={handleGenerateImage}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  이미지 생성 중...
                </>
              ) : (
                '이미지 생성하기'
              )}
            </button>

            {/* 안내 사항 */}
            <div className="info-box">
              <h4>AI 모델 안내</h4>
              <ul>
                <li><strong>Nanovana</strong>: Gemini 2.5 Flash Image (Text/Image-to-Image)</li>
              </ul>
            </div>
          </div>

          {/* 생성 결과 */}
          <div className="result-section">
            {generatedImage ? (
              <div className="result-container">
                <div className="result-header">
                  <h3>이미지 생성 완료!</h3>
                  <div className="result-actions">
                    <button onClick={handleDownloadImage} className="btn-download">
                      다운로드
                    </button>
                    <button onClick={handleReset} className="btn-reset">
                      새로 만들기
                    </button>
                  </div>
                </div>
                <div className="generated-image-wrapper">
                  <img src={generatedImage} alt="Generated" className="generated-image" />
                </div>
              </div>
            ) : (
              <div className="placeholder-result">
                <div className="placeholder-icon">+</div>
                <p>이미지를 생성하면 여기에 결과가 표시됩니다</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 카드뉴스 탭 */}
      {activeTab === 'cardnews' && (
        <div className="cardnews-content">
          {/* 모드 선택 */}
          <div className="cardnews-mode-section">
            <h3>생성 방식 선택</h3>
            <div className="mode-buttons">
              <button
                className={`mode-button ${cardnewsMode === 'ai' ? 'active' : ''}`}
                onClick={() => setCardnewsMode('ai')}
              >
                <div className="mode-icon">🤖</div>
                <div className="mode-title">AI 자동 생성</div>
                <div className="mode-desc">프롬프트만 입력하면 AI가 모두 생성</div>
              </button>
              <button
                className={`mode-button ${cardnewsMode === 'custom' ? 'active' : ''}`}
                onClick={() => setCardnewsMode('custom')}
              >
                <div className="mode-icon">📷</div>
                <div className="mode-title">이미지 업로드</div>
                <div className="mode-desc">내 이미지로 카드뉴스 만들기</div>
              </button>
            </div>
          </div>

          <hr className="section-divider" />

          {cardnewsMode === 'ai' && (
            <>
              <div className="cardnews-header-info">
                <p>AI가 프롬프트만으로 자동으로 페이지별 내용을 구성하고 카드뉴스를 생성합니다</p>
                <div className="agentic-mode-badge">
                  AI Agentic 모드 - AI가 페이지 수, 제목, 내용, 이미지를 모두 자동으로 생성합니다
                </div>
              </div>
            </>
          )}

          {/* 1. 스타일 선택 섹션 */}
          <div className="style-section">
            <h3>1. 스타일 선택</h3>
            <p className="section-desc">카드뉴스의 분위기를 선택하세요</p>

            <div className="style-options">
              {/* 색상 분위기 */}
              <div className="style-group">
                <h4>색상 분위기</h4>
                <div className="style-buttons">
                  <button
                    className={`style-btn ${colorTheme === 'black' ? 'active' : ''}`}
                    onClick={() => setColorTheme('black')}
                  >
                    블랙
                    <span className="btn-hint">검정배경/흰폰트</span>
                  </button>
                  <button
                    className={`style-btn ${colorTheme === 'blue' ? 'active' : ''}`}
                    onClick={() => setColorTheme('blue')}
                  >
                    블루
                    <span className="btn-hint">파란배경/흰폰트</span>
                  </button>
                  <button
                    className={`style-btn ${colorTheme === 'orange' ? 'active' : ''}`}
                    onClick={() => setColorTheme('orange')}
                  >
                    주황
                    <span className="btn-hint">주황배경/흰폰트</span>
                  </button>
                </div>
              </div>

              {/* 폰트 굵기 */}
              <div className="style-group">
                <h4>폰트 굵기</h4>
                <div className="style-buttons">
                  <button
                    className={`style-btn ${fontWeight === 'light' ? 'active' : ''}`}
                    onClick={() => setFontWeight('light')}
                  >
                    얇게
                    <span className="btn-hint">가벼운 느낌</span>
                  </button>
                  <button
                    className={`style-btn ${fontWeight === 'medium' ? 'active' : ''}`}
                    onClick={() => setFontWeight('medium')}
                  >
                    중간
                    <span className="btn-hint">균형잡힌 느낌</span>
                  </button>
                  <button
                    className={`style-btn ${fontWeight === 'bold' ? 'active' : ''}`}
                    onClick={() => setFontWeight('bold')}
                  >
                    굵게
                    <span className="btn-hint">강조된 느낌</span>
                  </button>
                </div>
              </div>

              {/* 폰트 위치 */}
              <div className="style-group">
                <h4>폰트 위치</h4>
                <div className="style-buttons">
                  <button
                    className={`style-btn ${layoutStyle === 'top' ? 'active' : ''}`}
                    onClick={() => setLayoutStyle('top')}
                  >
                    위
                    <span className="btn-hint">상단 배치</span>
                  </button>
                  <button
                    className={`style-btn ${layoutStyle === 'center' ? 'active' : ''}`}
                    onClick={() => setLayoutStyle('center')}
                  >
                    중앙
                    <span className="btn-hint">가운데 배치</span>
                  </button>
                  <button
                    className={`style-btn ${layoutStyle === 'bottom' ? 'active' : ''}`}
                    onClick={() => setLayoutStyle('bottom')}
                  >
                    아래
                    <span className="btn-hint">하단 배치</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <hr className="section-divider" />

          {/* AI 모드: 내용 입력 섹션 */}
          {cardnewsMode === 'ai' && (
            <>
              <div className="input-section">
                <h3>2. 카드뉴스 내용 입력</h3>
                <p className="section-desc">
                  간단한 프롬프트만 입력하세요. AI가 페이지별 제목, 내용, 이미지를 모두 자동으로 생성합니다
                </p>
                <textarea
                  placeholder={`예시:
- 새로운 카페 오픈 홍보
- 여름 세일 50% 할인 이벤트
- 딸기 시즌 신메뉴 3종 출시
- 강남역 필라테스 개업 50% 할인

프롬프트가 구체적일수록 더 좋은 결과가 나옵니다!`}
                  value={titles[0]}
                  onChange={(e) => handleTitleChange(0, e.target.value)}
                  className="cardnews-input"
                  rows="6"
                />
              </div>

              <hr className="section-divider" />

              {/* 생성 버튼 */}
              <div className="generate-section">
                <button
                  onClick={handleGenerateAgenticCardNews}
                  disabled={isCardGenerating || titles[0].trim().length < 10}
                  className="btn-generate cardnews-generate"
                >
                  {isCardGenerating ? 'AI가 열심히 생성 중...' : 'AI가 자동으로 카드뉴스 생성하기'}
                </button>
                {generatingStatus && (
                  <p className="generating-status">
                    {generatingStatus}
                  </p>
                )}
              </div>

              <hr className="section-divider" />

              {/* AI 분석 결과 표시 */}
              {agenticAnalysis && !isCardGenerating && (
                <div className="analysis-result">
                  <h3>AI 분석 결과</h3>
                  <div className="analysis-grid">
                    <div className="analysis-item">
                      <strong>생성된 페이지 수:</strong> {agenticAnalysis.pageCount}장
                    </div>
                    <div className="analysis-item">
                      <strong>품질 점수:</strong> {agenticAnalysis.qualityScore ? `${agenticAnalysis.qualityScore.toFixed(1)}/10` : 'N/A'}
                    </div>
                    <div className="analysis-item">
                      <strong>타겟 청중:</strong> {agenticAnalysis.targetAudience || 'N/A'}
                    </div>
                    <div className="analysis-item">
                      <strong>톤앤매너:</strong> {agenticAnalysis.tone || 'N/A'}
                    </div>
                  </div>
                  {agenticAnalysis.pagesInfo && agenticAnalysis.pagesInfo.length > 0 && (
                    <div className="pages-info">
                      <h4>페이지 구성</h4>
                      {agenticAnalysis.pagesInfo.map((page, index) => (
                        <div key={index} className="page-info-item">
                          <strong>페이지 {page.page}:</strong> {page.title}
                          <br />
                          <span className="page-content">{page.content}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* 커스텀 모드: 이미지 업로드 섹션 */}
          {cardnewsMode === 'custom' && (
            <>
              <div className="upload-section">
                <h3>2. 이미지 업로드 및 텍스트 입력</h3>
                <p className="section-desc">
                  카드뉴스로 만들 이미지를 업로드하세요. 각 이미지에 텍스트를 추가할 수 있습니다. (최대 {MAX_CARDNEWS_IMAGES}장)
                </p>

                {/* 이미지 업로드 버튼 */}
                <div className="upload-button-wrapper">
                  <label
                    htmlFor="cardnews-image-upload"
                    className={`upload-label-btn ${cardnewsImages.length >= MAX_CARDNEWS_IMAGES ? 'disabled' : ''}`}
                  >
                    📁 이미지 선택하기 ({cardnewsImages.length}/{MAX_CARDNEWS_IMAGES})
                  </label>
                  <input
                    id="cardnews-image-upload"
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleCardnewsImageUpload}
                    disabled={cardnewsImages.length >= MAX_CARDNEWS_IMAGES}
                    style={{ display: 'none' }}
                  />
                  <span className="upload-hint">여러 이미지를 한 번에 선택할 수 있습니다</span>
                </div>

                {/* 업로드된 이미지 목록 */}
                {cardnewsImages.length > 0 && (
                  <div className="uploaded-images-grid">
                    {cardnewsImages.map((img, index) => (
                      <div key={index} className="uploaded-image-card">
                        <div className="image-preview-wrapper">
                          <img src={img.preview} alt={`Upload ${index + 1}`} className="uploaded-preview-img" />
                          <button
                            onClick={() => handleRemoveCardnewsImage(index)}
                            className="btn-remove-image"
                          >
                            ✕
                          </button>
                          <span className="image-number">카드 {index + 1}</span>
                        </div>
                        <div className="image-text-input">
                          <label>텍스트 입력:</label>
                          <textarea
                            placeholder="이미지에 추가할 텍스트를 입력하세요..."
                            value={cardnewsTexts[index] || ''}
                            onChange={(e) => handleCardnewsTextChange(index, e.target.value)}
                            rows={3}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 이미지가 없을 때 안내 메시지 */}
                {cardnewsImages.length === 0 && (
                  <div className="empty-upload-placeholder">
                    <span className="placeholder-icon">🖼️</span>
                    <p>이미지를 업로드해주세요</p>
                    <p className="placeholder-hint">최대 {MAX_CARDNEWS_IMAGES}장까지 업로드 가능합니다</p>
                  </div>
                )}
              </div>

              <hr className="section-divider" />

              {/* 생성 버튼 */}
              <div className="generate-section">
                <button
                  onClick={handleGenerateCustomCardNews}
                  disabled={isCardGenerating || cardnewsImages.length === 0}
                  className="btn-generate cardnews-generate"
                >
                  {isCardGenerating ? '카드뉴스 생성 중...' : `카드뉴스 생성하기 (${cardnewsImages.length}장)`}
                </button>
                {generatingStatus && (
                  <p className="generating-status">
                    {generatingStatus}
                  </p>
                )}
              </div>

              <hr className="section-divider" />
            </>
          )}

          {/* 생성 중 미리보기 */}
          {isCardGenerating && previewCards.length > 0 && (
            <div className="cards-result">
              <h3>생성 중 미리보기</h3>
              <div className="cards-grid">
                {previewCards.map((card, index) => (
                  <div key={index} className="card-item generating">
                    <img src={card} alt={`Preview Card ${index + 1}`} className="card-image" />
                    <p className="card-label">카드 {index + 1}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 생성된 카드뉴스 결과 */}
          {!isCardGenerating && generatedCards.length > 0 && (
            <div className="cards-result">
              <div className="cards-header">
                <h3>생성 완료! 카드뉴스</h3>
                <button onClick={handleDownloadAll} className="btn-download-all">
                  전체 다운로드
                </button>
              </div>
              <div className="cards-grid">
                {generatedCards.map((card, index) => (
                  <div key={index} className="card-item">
                    <img src={card} alt={`Card ${index + 1}`} className="card-image" />
                    <button
                      onClick={() => handleDownloadCard(card, index)}
                      className="btn-card-download"
                    >
                      다운로드
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ImageGenerator;
