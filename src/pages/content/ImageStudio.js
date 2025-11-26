import React, { useState, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import './ImageStudio.css';

const MAX_IMAGES = 5;

function ImageStudio() {
  const { user } = useContext(AuthContext);
  // 탭 상태: 'image' (이미지 생성) or 'cardnews' (카드뉴스)
  const [activeTab, setActiveTab] = useState('image');

  // ========== 이미지 생성 관련 상태 ==========
  const [aiModel, setAiModel] = useState('whisk');
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [referenceImage, setReferenceImage] = useState(null);
  const [generationMode, setGenerationMode] = useState('text');

  // ========== 카드뉴스 관련 상태 ==========
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGeneratingCards, setIsGeneratingCards] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState('');
  const [colorTheme, setColorTheme] = useState('black');
  const [layoutStyle, setLayoutStyle] = useState('center');
  const [fontWeight, setFontWeight] = useState('bold');
  const [uploadedImages, setUploadedImages] = useState([]);
  const [customTexts, setCustomTexts] = useState([]);

  const aiModels = [
    { id: 'whisk', label: 'Whisk AI (무료)', provider: 'Pollinations' },
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Anthropic' },
    { id: 'gemini', label: '제미나이 (Gemini)', provider: 'Google' },
  ];

  // ========== 이미지 생성 핸들러 ==========
  const handleReferenceImageUpload = (e) => {
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

    setIsGeneratingImage(true);
    try {
      const requestBody = {
        prompt: imagePrompt,
        model: aiModel,
        userId: user?.id || null,  // 브랜드 분석 정보 활용을 위해 userId 전달
      };

      if (generationMode === 'image' && referenceImage) {
        requestBody.referenceImage = referenceImage;
      }

      const response = await fetch('http://localhost:8000/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = '이미지 생성에 실패했습니다.';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          errorMessage = responseText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = JSON.parse(responseText);
      if (!data.imageUrl) {
        throw new Error('이미지 URL을 받지 못했습니다.');
      }

      setGeneratedImage(data.imageUrl);
      alert('이미지가 성공적으로 생성되었습니다!');
    } catch (error) {
      console.error('Image generation error:', error);
      alert(`이미지 생성 중 오류가 발생했습니다:\n\n${error.message}`);
    } finally {
      setIsGeneratingImage(false);
    }
  };

  // ========== 카드뉴스 핸들러 ==========
  const handleCardImageUpload = (e) => {
    const files = Array.from(e.target.files);
    const remainingSlots = MAX_IMAGES - uploadedImages.length;

    if (remainingSlots <= 0) {
      alert(`최대 ${MAX_IMAGES}개의 이미지만 업로드할 수 있습니다.`);
      return;
    }

    const filesToAdd = files.slice(0, remainingSlots);

    if (files.length > remainingSlots) {
      alert(`최대 ${MAX_IMAGES}개까지만 업로드 가능합니다. ${filesToAdd.length}개만 추가됩니다.`);
    }

    filesToAdd.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setUploadedImages(prev => {
          if (prev.length >= MAX_IMAGES) return prev;
          return [...prev, { file, preview: event.target.result, name: file.name }];
        });
        setCustomTexts(prev => [...prev, '']);
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  };

  const handleRemoveImage = (index) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
    setCustomTexts(prev => prev.filter((_, i) => i !== index));
  };

  const handleCustomTextChange = (index, value) => {
    const newTexts = [...customTexts];
    newTexts[index] = value;
    setCustomTexts(newTexts);
  };

  const handleGenerateCards = async () => {
    if (uploadedImages.length === 0) {
      alert('이미지를 먼저 업로드해주세요.');
      return;
    }

    setIsGeneratingCards(true);
    setGeneratedCards([]);
    setGeneratingStatus('카드뉴스 생성 중...');

    try {
      const formData = new FormData();
      uploadedImages.forEach((img) => formData.append('images', img.file));
      formData.append('texts', JSON.stringify(customTexts));
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
      setIsGeneratingCards(false);
      setGeneratingStatus('');
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
      setTimeout(() => handleDownloadCard(card, index), index * 200);
    });
  };

  return (
    <div className="image-studio">
      <div className="studio-header">
        <h2>이미지 스튜디오</h2>
        <p>AI 이미지 생성 또는 카드뉴스를 만들어보세요</p>
      </div>

      {/* 토글 탭 */}
      <div className="studio-tabs">
        <button
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => setActiveTab('image')}
        >
          <span className="tab-icon">🎨</span>
          <span>이미지 생성</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'cardnews' ? 'active' : ''}`}
          onClick={() => setActiveTab('cardnews')}
        >
          <span className="tab-icon">📰</span>
          <span>카드뉴스</span>
        </button>
      </div>

      {/* ========== 이미지 생성 탭 ========== */}
      {activeTab === 'image' && (
        <div className="tab-content">
          <div className="image-generator">
            <div className="generator-main">
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
                <p className="hint-text">
                  {aiModels.find(m => m.id === aiModel)?.provider} 제공
                </p>
              </div>

              {/* 생성 모드 선택 */}
              <div className="section">
                <h3>생성 모드</h3>
                <div className="mode-buttons">
                  <button
                    className={`mode-btn ${generationMode === 'text' ? 'active' : ''}`}
                    onClick={() => {
                      setGenerationMode('text');
                      setReferenceImage(null);
                    }}
                  >
                    <span className="mode-icon">📝</span>
                    <span className="mode-label">텍스트 → 이미지</span>
                    <span className="mode-hint">텍스트로 이미지 생성</span>
                  </button>
                  <button
                    className={`mode-btn ${generationMode === 'image' ? 'active' : ''}`}
                    onClick={() => setGenerationMode('image')}
                  >
                    <span className="mode-icon">🖼️</span>
                    <span className="mode-label">이미지 → 이미지</span>
                    <span className="mode-hint">레퍼런스 기반 생성</span>
                  </button>
                </div>

                {generationMode === 'image' && (
                  <div className="reference-upload">
                    <label htmlFor="ref-image-upload" className="upload-label">
                      <input
                        id="ref-image-upload"
                        type="file"
                        accept="image/*"
                        onChange={handleReferenceImageUpload}
                        style={{ display: 'none' }}
                      />
                      {referenceImage ? (
                        <div className="uploaded-preview">
                          <img src={referenceImage} alt="Reference" />
                          <p>레퍼런스 이미지 업로드됨 (클릭하여 변경)</p>
                        </div>
                      ) : (
                        <div className="upload-placeholder">
                          <span>📁</span>
                          <p>레퍼런스 이미지 업로드</p>
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
                  placeholder="이미지 설명을 입력하세요 (예: A beautiful sunset over mountains)"
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  rows={4}
                />
                <button
                  className="btn-generate"
                  onClick={handleGenerateImage}
                  disabled={isGeneratingImage}
                >
                  {isGeneratingImage ? '🎨 생성 중...' : '🚀 이미지 생성하기'}
                </button>
              </div>
            </div>

            {/* 미리보기 영역 */}
            <div className="generator-preview">
              <h3>미리보기</h3>
              <div className="preview-box">
                {isGeneratingImage ? (
                  <div className="loading-state">
                    <div className="spinner"></div>
                    <p>AI가 이미지를 생성하고 있습니다...</p>
                  </div>
                ) : generatedImage ? (
                  <div className="result-image">
                    <img src={generatedImage} alt="Generated" />
                    <p>우클릭하여 이미지를 저장하세요</p>
                  </div>
                ) : (
                  <div className="empty-state">
                    <span>🎨</span>
                    <p>프롬프트를 입력하고<br/>이미지를 생성해보세요</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== 카드뉴스 탭 ========== */}
      {activeTab === 'cardnews' && (
        <div className="tab-content">
          {/* 스타일 선택 */}
          <div className="style-section">
            <h3>1. 스타일 선택</h3>
            <p className="section-desc">카드뉴스의 분위기를 선택하세요</p>

            <div className="style-options">
              <div className="style-group">
                <h4>🎨 색상 분위기</h4>
                <div className="style-buttons">
                  {[
                    { id: 'black', label: '⬛ 블랙', hint: '검정배경/흰폰트' },
                    { id: 'blue', label: '🔵 블루', hint: '파란배경/흰폰트' },
                    { id: 'orange', label: '🟠 주황', hint: '주황배경/흰폰트' },
                  ].map(theme => (
                    <button
                      key={theme.id}
                      className={`style-btn ${colorTheme === theme.id ? 'active' : ''}`}
                      onClick={() => setColorTheme(theme.id)}
                    >
                      {theme.label}
                      <span className="btn-hint">{theme.hint}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="style-group">
                <h4>✏️ 폰트 굵기</h4>
                <div className="style-buttons">
                  {[
                    { id: 'light', label: '얇게', hint: '가벼운 느낌' },
                    { id: 'medium', label: '중간', hint: '균형잡힌 느낌' },
                    { id: 'bold', label: '굵게', hint: '강조된 느낌' },
                  ].map(weight => (
                    <button
                      key={weight.id}
                      className={`style-btn ${fontWeight === weight.id ? 'active' : ''}`}
                      onClick={() => setFontWeight(weight.id)}
                    >
                      {weight.label}
                      <span className="btn-hint">{weight.hint}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="style-group">
                <h4>📍 폰트 위치</h4>
                <div className="style-buttons">
                  {[
                    { id: 'top', label: '⬆️ 위', hint: '상단 배치' },
                    { id: 'center', label: '⏺️ 중앙', hint: '가운데 배치' },
                    { id: 'bottom', label: '⬇️ 아래', hint: '하단 배치' },
                  ].map(layout => (
                    <button
                      key={layout.id}
                      className={`style-btn ${layoutStyle === layout.id ? 'active' : ''}`}
                      onClick={() => setLayoutStyle(layout.id)}
                    >
                      {layout.label}
                      <span className="btn-hint">{layout.hint}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <hr />

          {/* 이미지 업로드 */}
          <div className="upload-section">
            <h3>2. 이미지 업로드 및 텍스트 입력</h3>
            <p className="section-desc">
              카드뉴스로 만들 이미지를 업로드하세요 (최대 {MAX_IMAGES}장)
            </p>

            <div className="upload-button-wrapper">
              <label
                htmlFor="card-image-upload"
                className={`upload-btn ${uploadedImages.length >= MAX_IMAGES ? 'disabled' : ''}`}
              >
                📁 이미지 선택하기 ({uploadedImages.length}/{MAX_IMAGES})
              </label>
              <input
                id="card-image-upload"
                type="file"
                accept="image/*"
                multiple
                onChange={handleCardImageUpload}
                disabled={uploadedImages.length >= MAX_IMAGES}
                style={{ display: 'none' }}
              />
              <span className="upload-hint">여러 이미지를 한 번에 선택할 수 있습니다</span>
            </div>

            {uploadedImages.length > 0 ? (
              <div className="uploaded-list">
                <h4>업로드된 이미지 ({uploadedImages.length}/{MAX_IMAGES}장)</h4>
                <div className="image-grid">
                  {uploadedImages.map((img, index) => (
                    <div key={index} className="image-card">
                      <div className="image-wrapper">
                        <img src={img.preview} alt={`Upload ${index + 1}`} />
                        <button
                          className="remove-btn"
                          onClick={() => handleRemoveImage(index)}
                        >
                          ✕
                        </button>
                        <span className="card-number">카드 {index + 1}</span>
                      </div>
                      <div className="text-input-wrapper">
                        <label>텍스트 입력:</label>
                        <textarea
                          placeholder="이미지에 추가할 텍스트를 입력하세요..."
                          value={customTexts[index] || ''}
                          onChange={(e) => handleCustomTextChange(index, e.target.value)}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-upload">
                <span>🖼️</span>
                <p>이미지를 업로드해주세요</p>
                <p className="hint">최대 {MAX_IMAGES}장까지 업로드 가능합니다</p>
              </div>
            )}
          </div>

          <hr />

          {/* 생성 버튼 */}
          <div className="generate-section">
            <button
              onClick={handleGenerateCards}
              disabled={isGeneratingCards || uploadedImages.length === 0}
              className={`btn-generate-cards ${uploadedImages.length === 0 ? 'disabled' : ''}`}
            >
              {isGeneratingCards ? '🔄 카드뉴스 생성 중...' : `🎨 카드뉴스 생성하기 (${uploadedImages.length}장)`}
            </button>
            {generatingStatus && (
              <p className="generating-status">{generatingStatus}</p>
            )}
          </div>

          <hr />

          {/* 생성 결과 */}
          {!isGeneratingCards && generatedCards.length > 0 && (
            <div className="result-section">
              <div className="result-header">
                <h3>🎉 생성 완료! 카드뉴스</h3>
                <button onClick={handleDownloadAll} className="btn-download-all">
                  📥 전체 다운로드
                </button>
              </div>
              <div className="cards-grid">
                {generatedCards.map((card, index) => (
                  <div key={index} className="card-item">
                    <img src={card} alt={`Card ${index + 1}`} className="card-image" />
                    <button
                      onClick={() => handleDownloadCard(card, index)}
                      className="btn-download"
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

export default ImageStudio;
