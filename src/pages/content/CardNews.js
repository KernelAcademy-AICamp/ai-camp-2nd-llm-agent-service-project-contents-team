import React, { useState } from 'react';
import './CardNews.css';

function CardNews() {
  const [images, setImages] = useState([]);
  const [titles, setTitles] = useState([]);
  const [descriptions, setDescriptions] = useState([]);
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // 스타일 옵션
  const [fontStyle, setFontStyle] = useState('rounded'); // 'rounded' | 'sharp'
  const [colorTheme, setColorTheme] = useState('warm'); // 'warm' | 'cool' | 'vibrant' | 'minimal'
  const [purpose, setPurpose] = useState('promotion'); // 'promotion' | 'info' | 'event' | 'menu'
  const [layoutStyle, setLayoutStyle] = useState('overlay'); // 'overlay' | 'split' | 'minimal' | 'magazine'

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 10) {
      alert('최대 10개의 이미지만 업로드 가능합니다.');
      return;
    }

    setImages(files);
    // 초기 제목과 설명 배열 생성
    setTitles(files.map((_, i) => `카드 ${i + 1}`));
    setDescriptions(files.map(() => ''));
  };

  const handleTitleChange = (index, value) => {
    const newTitles = [...titles];
    newTitles[index] = value;
    setTitles(newTitles);
  };

  const handleDescriptionChange = (index, value) => {
    const newDescriptions = [...descriptions];
    newDescriptions[index] = value;
    setDescriptions(newDescriptions);
  };

  const handleRemoveImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    const newTitles = titles.filter((_, i) => i !== index);
    const newDescriptions = descriptions.filter((_, i) => i !== index);

    setImages(newImages);
    setTitles(newTitles);
    setDescriptions(newDescriptions);
  };

  const handleGenerateCardNews = async () => {
    if (images.length === 0) {
      alert('최소 1개 이상의 이미지를 업로드해주세요.');
      return;
    }

    setIsGenerating(true);
    setGeneratedCards([]);

    try {
      const formData = new FormData();

      // 이미지 파일 추가
      images.forEach((image) => {
        formData.append('images', image);
      });

      // 제목과 설명 추가 (JSON 문자열로 변환)
      formData.append('titles', JSON.stringify(titles));
      formData.append('descriptions', JSON.stringify(descriptions));

      // 스타일 옵션 추가
      formData.append('fontStyle', fontStyle);
      formData.append('colorTheme', colorTheme);
      formData.append('purpose', purpose);
      formData.append('layoutStyle', layoutStyle);

      const response = await fetch('/api/generate-cardnews', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedCards(data.cards);
        alert(`✅ ${data.count}개의 카드뉴스가 생성되었습니다!`);
      } else {
        throw new Error(data.error || '카드뉴스 생성에 실패했습니다.');
      }
    } catch (error) {
      console.error('카드뉴스 생성 오류:', error);
      alert(`카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
    } finally {
      setIsGenerating(false);
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
      }, index * 200); // 각 다운로드 사이 200ms 지연
    });
  };

  return (
    <div className="cardnews-page">
      <div className="cardnews-header">
        <h2>📰 카드뉴스 생성</h2>
        <p>여러 이미지를 업로드하고 제목과 설명을 추가하여 카드뉴스를 만드세요</p>
      </div>

      <div className="cardnews-content">
        {/* 스타일 선택 섹션 */}
        <div className="style-section">
          <h3>1. 스타일 선택</h3>
          <p className="section-desc">카드뉴스의 용도와 분위기를 선택하세요</p>

          <div className="style-options">
            {/* 용도 선택 */}
            <div className="style-group">
              <h4>📋 용도</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${purpose === 'promotion' ? 'active' : ''}`}
                  onClick={() => setPurpose('promotion')}
                >
                  🎯 프로모션
                  <span className="btn-hint">할인/이벤트</span>
                </button>
                <button
                  className={`style-btn ${purpose === 'menu' ? 'active' : ''}`}
                  onClick={() => setPurpose('menu')}
                >
                  ☕ 신메뉴
                  <span className="btn-hint">상품 소개</span>
                </button>
                <button
                  className={`style-btn ${purpose === 'info' ? 'active' : ''}`}
                  onClick={() => setPurpose('info')}
                >
                  💡 정보 전달
                  <span className="btn-hint">팁/노하우</span>
                </button>
                <button
                  className={`style-btn ${purpose === 'event' ? 'active' : ''}`}
                  onClick={() => setPurpose('event')}
                >
                  🎉 이벤트
                  <span className="btn-hint">행사 안내</span>
                </button>
              </div>
            </div>

            {/* 색상 분위기 */}
            <div className="style-group">
              <h4>🎨 색상 분위기</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${colorTheme === 'warm' ? 'active' : ''}`}
                  onClick={() => setColorTheme('warm')}
                >
                  🌅 따뜻한
                  <span className="btn-hint">베이지/브라운</span>
                </button>
                <button
                  className={`style-btn ${colorTheme === 'cool' ? 'active' : ''}`}
                  onClick={() => setColorTheme('cool')}
                >
                  ❄️ 시원한
                  <span className="btn-hint">블루/그린</span>
                </button>
                <button
                  className={`style-btn ${colorTheme === 'vibrant' ? 'active' : ''}`}
                  onClick={() => setColorTheme('vibrant')}
                >
                  ✨ 화사한
                  <span className="btn-hint">핑크/옐로우</span>
                </button>
                <button
                  className={`style-btn ${colorTheme === 'minimal' ? 'active' : ''}`}
                  onClick={() => setColorTheme('minimal')}
                >
                  ⚪ 미니멀
                  <span className="btn-hint">흑백/그레이</span>
                </button>
              </div>
            </div>

            {/* 폰트 스타일 */}
            <div className="style-group">
              <h4>✏️ 폰트 스타일</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${fontStyle === 'rounded' ? 'active' : ''}`}
                  onClick={() => setFontStyle('rounded')}
                >
                  🔘 부드러운 폰트
                  <span className="btn-hint">카페/일상</span>
                </button>
                <button
                  className={`style-btn ${fontStyle === 'sharp' ? 'active' : ''}`}
                  onClick={() => setFontStyle('sharp')}
                >
                  ▪️ 각진 폰트
                  <span className="btn-hint">전문적/세련됨</span>
                </button>
              </div>
            </div>

            {/* 레이아웃 스타일 */}
            <div className="style-group">
              <h4>📐 레이아웃</h4>
              <div className="style-buttons">
                <button
                  className={`style-btn ${layoutStyle === 'overlay' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('overlay')}
                >
                  🖼️ 오버레이
                  <span className="btn-hint">이미지 위 텍스트</span>
                </button>
                <button
                  className={`style-btn ${layoutStyle === 'split' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('split')}
                >
                  ⬛ 분할
                  <span className="btn-hint">이미지+텍스트 분리</span>
                </button>
                <button
                  className={`style-btn ${layoutStyle === 'minimal' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('minimal')}
                >
                  ⚪ 미니멀
                  <span className="btn-hint">여백 많은 깔끔함</span>
                </button>
                <button
                  className={`style-btn ${layoutStyle === 'magazine' ? 'active' : ''}`}
                  onClick={() => setLayoutStyle('magazine')}
                >
                  📖 매거진
                  <span className="btn-hint">고급스러운 편집</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 이미지 업로드 섹션 */}
        <div className="upload-section">
          <h3>2. 이미지 업로드 (최대 10개)</h3>
          <div className="upload-area">
            <input
              type="file"
              id="image-upload"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              style={{ display: 'none' }}
            />
            <label htmlFor="image-upload" className="upload-label">
              <span className="upload-icon">📁</span>
              <p>이미지를 선택하세요 (클릭)</p>
              <p className="upload-hint">JPG, PNG, GIF 형식 지원</p>
            </label>
          </div>

          {/* 업로드된 이미지 목록 */}
          {images.length > 0 && (
            <div className="uploaded-images">
              <h4>업로드된 이미지 ({images.length}개)</h4>
              <div className="image-list">
                {images.map((image, index) => (
                  <div key={index} className="image-item">
                    <img
                      src={URL.createObjectURL(image)}
                      alt={`Upload ${index + 1}`}
                      className="preview-thumbnail"
                    />
                    <div className="image-info">
                      <input
                        type="text"
                        placeholder="제목"
                        value={titles[index]}
                        onChange={(e) => handleTitleChange(index, e.target.value)}
                        className="title-input-small"
                      />
                      <input
                        type="text"
                        placeholder="설명 (선택사항)"
                        value={descriptions[index]}
                        onChange={(e) => handleDescriptionChange(index, e.target.value)}
                        className="desc-input-small"
                      />
                      <button
                        onClick={() => handleRemoveImage(index)}
                        className="btn-remove"
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 생성 버튼 */}
        {images.length > 0 && (
          <div className="generate-section">
            <button
              onClick={handleGenerateCardNews}
              disabled={isGenerating}
              className="btn-generate"
            >
              {isGenerating ? '🔄 생성 중...' : '🎨 카드뉴스 생성하기'}
            </button>
          </div>
        )}

        {/* 생성된 카드뉴스 */}
        {generatedCards.length > 0 && (
          <div className="result-section">
            <div className="result-header">
              <h3>생성된 카드뉴스</h3>
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
