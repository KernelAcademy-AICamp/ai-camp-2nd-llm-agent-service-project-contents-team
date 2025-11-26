import React, { useState } from 'react';
import './CardNews.css'; // 별도의 CSS 파일이 있다고 가정

const MAX_IMAGES = 5;

function CardNews() {
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState('');

  // 스타일 옵션
  const [colorTheme, setColorTheme] = useState('black'); // 'black' | 'blue' | 'orange'
  const [layoutStyle, setLayoutStyle] = useState('center'); // 'top' | 'center' | 'bottom'
  const [fontWeight, setFontWeight] = useState('bold'); // 'light' | 'medium' | 'bold'

  // 이미지 업로드 (최대 5개)
  const [uploadedImages, setUploadedImages] = useState([]);
  const [customTexts, setCustomTexts] = useState([]);

  // 이미지 업로드 핸들러 (최대 5개 제한)
  const handleImageUpload = (e) => {
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
          return [...prev, {
            file: file,
            preview: event.target.result,
            name: file.name
          }];
        });
        setCustomTexts(prev => [...prev, '']);
      };
      reader.readAsDataURL(file);
    });

    // input 초기화 (같은 파일 다시 선택 가능하도록)
    e.target.value = '';
  };

  // 업로드된 이미지 삭제
  const handleRemoveImage = (index) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
    setCustomTexts(prev => prev.filter((_, i) => i !== index));
  };

  // 커스텀 텍스트 변경
  const handleCustomTextChange = (index, value) => {
    const newTexts = [...customTexts];
    newTexts[index] = value;
    setCustomTexts(newTexts);
  };

  // 카드뉴스 생성
  const handleGenerateCards = async () => {
    if (uploadedImages.length === 0) {
      alert('이미지를 먼저 업로드해주세요.');
      return;
    }

    setIsGenerating(true);
    setGeneratedCards([]);
    setGeneratingStatus('🖼️ 카드뉴스 생성 중...');

    try {
      const formData = new FormData();

      // 이미지 파일들 추가
      uploadedImages.forEach((img) => {
        formData.append('images', img.file);
      });

      // 텍스트 배열 추가
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
        alert(`✅ ${result.cards.length}장의 카드뉴스가 생성되었습니다!`);
      } else {
        throw new Error(result.error || '카드 생성 실패');
      }
    } catch (error) {
      console.error('카드뉴스 생성 오류:', error);
      alert(`카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
    } finally {
      setIsGenerating(false);
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
      setTimeout(() => {
        handleDownloadCard(card, index);
      }, index * 200);
    });
  };

  return (
    <div className="cardnews-page">
      <div className="cardnews-header">
        <h2>📰 카드뉴스 생성기</h2>
        <p>🖼️ 이미지를 업로드하고 텍스트를 추가하여 카드뉴스를 만드세요 (최대 {MAX_IMAGES}장)</p>
      </div>

      <div className="cardnews-content">
        {/* 1. 스타일 선택 섹션 */}
        <div className="style-section">
          <h3>1. 스타일 선택</h3>
          <p className="section-desc">카드뉴스의 분위기를 선택하세요</p>

          <div className="style-options">
            {/* 색상 분위기 */}
            <div className="style-group">
              <h4>🎨 색상 분위기</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${colorTheme === 'black' ? 'active' : ''}`}
                  onClick={() => setColorTheme('black')}
                >
                  ⬛ 블랙
                  <span className="btn-hint">검정배경/흰폰트</span>
                </button>
                <button
                  className={`style-btn ${colorTheme === 'blue' ? 'active' : ''}`}
                  onClick={() => setColorTheme('blue')}
                >
                  🔵 블루
                  <span className="btn-hint">파란배경/흰폰트</span>
                </button>
                <button
                  className={`style-btn ${colorTheme === 'orange' ? 'active' : ''}`}
                  onClick={() => setColorTheme('orange')}
                >
                  🟠 주황
                  <span className="btn-hint">주황배경/흰폰트</span>
                </button>
              </div>
            </div>

            {/* 폰트 굵기 */}
            <div className="style-group">
              <h4>✏️ 폰트 굵기</h4>
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
              <h4>📍 폰트 위치</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${layoutStyle === 'top' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('top')}
                >
                  ⬆️ 위
                  <span className="btn-hint">상단 배치</span>
                </button>
                <button
                  className={`style-btn ${layoutStyle === 'center' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('center')}
                >
                  ⏺️ 중앙
                  <span className="btn-hint">가운데 배치</span>
                </button>
                <button
                  className={`style-btn ${layoutStyle === 'bottom' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('bottom')}
                >
                  ⬇️ 아래
                  <span className="btn-hint">하단 배치</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <hr/>

        {/* 2. 이미지 업로드 섹션 */}
        <div className="upload-section">
          <h3>2. 이미지 업로드 및 텍스트 입력</h3>
          <p className="section-desc">
            🖼️ 카드뉴스로 만들 이미지를 업로드하세요. 각 이미지에 텍스트를 추가할 수 있습니다. (최대 {MAX_IMAGES}장)
          </p>

          {/* 이미지 업로드 버튼 */}
          <div style={{ marginBottom: '20px' }}>
            <label
              htmlFor="image-upload"
              style={{
                display: 'inline-block',
                padding: '15px 30px',
                background: uploadedImages.length >= MAX_IMAGES
                  ? '#ccc'
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: '8px',
                cursor: uploadedImages.length >= MAX_IMAGES ? 'not-allowed' : 'pointer',
                fontWeight: 'bold'
              }}
            >
              📁 이미지 선택하기 ({uploadedImages.length}/{MAX_IMAGES})
            </label>
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              disabled={uploadedImages.length >= MAX_IMAGES}
              style={{ display: 'none' }}
            />
            <span style={{ marginLeft: '15px', color: '#666' }}>
              여러 이미지를 한 번에 선택할 수 있습니다
            </span>
          </div>

          {/* 업로드된 이미지 목록 */}
          {uploadedImages.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4>업로드된 이미지 ({uploadedImages.length}/{MAX_IMAGES}장)</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px', marginTop: '15px' }}>
                {uploadedImages.map((img, index) => (
                  <div
                    key={index}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      padding: '15px',
                      background: '#fafafa'
                    }}
                  >
                    <div style={{ position: 'relative' }}>
                      <img
                        src={img.preview}
                        alt={`Upload ${index + 1}`}
                        style={{
                          width: '100%',
                          height: '200px',
                          objectFit: 'cover',
                          borderRadius: '8px'
                        }}
                      />
                      <button
                        onClick={() => handleRemoveImage(index)}
                        style={{
                          position: 'absolute',
                          top: '10px',
                          right: '10px',
                          background: 'rgba(255,0,0,0.8)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '50%',
                          width: '30px',
                          height: '30px',
                          cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        X
                      </button>
                      <span
                        style={{
                          position: 'absolute',
                          top: '10px',
                          left: '10px',
                          background: 'rgba(0,0,0,0.7)',
                          color: 'white',
                          padding: '5px 10px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}
                      >
                        카드 {index + 1}
                      </span>
                    </div>
                    <div style={{ marginTop: '10px' }}>
                      <label style={{ fontWeight: 'bold', fontSize: '14px' }}>
                        텍스트 입력:
                      </label>
                      <textarea
                        placeholder="이미지에 추가할 텍스트를 입력하세요..."
                        value={customTexts[index] || ''}
                        onChange={(e) => handleCustomTextChange(index, e.target.value)}
                        style={{
                          width: '100%',
                          marginTop: '8px',
                          padding: '10px',
                          borderRadius: '8px',
                          border: '1px solid #ddd',
                          resize: 'vertical',
                          minHeight: '80px',
                          boxSizing: 'border-box'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 이미지가 없을 때 안내 메시지 */}
          {uploadedImages.length === 0 && (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              background: '#f5f5f5',
              borderRadius: '8px',
              color: '#666',
              marginTop: '20px'
            }}>
              <p style={{ fontSize: '48px', margin: '0 0 10px 0' }}>🖼️</p>
              <p>이미지를 업로드해주세요</p>
              <p style={{ fontSize: '14px', color: '#999' }}>최대 {MAX_IMAGES}장까지 업로드 가능합니다</p>
            </div>
          )}
        </div>

        <hr/>

        {/* 생성 버튼 */}
        <div className="generate-section">
          <button
            onClick={handleGenerateCards}
            disabled={isGenerating || uploadedImages.length === 0}
            className="btn-generate"
            style={{
              background: uploadedImages.length === 0
                ? '#ccc'
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              fontSize: '18px'
            }}
          >
            {isGenerating ? '🔄 카드뉴스 생성 중...' : `🎨 카드뉴스 생성하기 (${uploadedImages.length}장)`}
          </button>
          {generatingStatus && (
            <p className="generating-status" style={{ marginTop: '20px', fontSize: '16px', color: '#FF8B5A', fontWeight: 'bold' }}>
              {generatingStatus}
            </p>
          )}
        </div>

        <hr/>

        {/* 생성된 카드뉴스 결과 */}
        {!isGenerating && generatedCards.length > 0 && (
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
    </div>
  );
}

export default CardNews;
