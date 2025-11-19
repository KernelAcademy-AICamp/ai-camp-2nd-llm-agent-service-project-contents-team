import React, { useState } from 'react';
import './CardNews.css'; // 별도의 CSS 파일이 있다고 가정

function CardNews() {
  const [titles, setTitles] = useState(['']);
  const [descriptions, setDescriptions] = useState(['']);
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState(''); // 생성 상태 메시지
  const [previewCards, setPreviewCards] = useState([]); // 생성 중 미리보기

  // 미리 정의된 배경 이미지 URL
  const backgroundTemplates = [
    {
      id: 1,
      url: 'https://help.miricanvas.com/hc/article_attachments/900002143703/___________________15_.png',
      name: '템플릿 1'
    },
    {
      id: 2,
      url: 'https://help.miricanvas.com/hc/article_attachments/900002143783/___________________4_.png',
      name: '템플릿 2'
    },
    {
      id: 3,
      url: 'https://help.miricanvas.com/hc/article_attachments/900002143763/___________________1_.png',
      name: '템플릿 3'
    },
    {
      id: 4,
      url: 'https://help.miricanvas.com/hc/article_attachments/900002143643/___________________5_.png',
      name: '템플릿 4'
    }
  ];

  // 스타일 옵션
  const [fontStyle, setFontStyle] = useState('rounded'); // 'rounded' | 'sharp'
  const [colorTheme, setColorTheme] = useState('warm'); // 'warm' | 'cool' | 'vibrant' | 'minimal'
  const [purpose, setPurpose] = useState('promotion'); // 'promotion' | 'info' | 'event' | 'menu'
  const [layoutStyle, setLayoutStyle] = useState('overlay'); // 'overlay' | 'split' | 'minimal' | 'magazine'
  const [selectedBackground, setSelectedBackground] = useState(0); // 선택된 배경 인덱스 (기본값: 0)

  const handleTitleChange = (index, value) => {
    const newTitles = [...titles];
    newTitles[index] = value;
    setTitles(newTitles);
  };

  const handleGenerateCardNews = async () => {
    if (titles[0].trim().length < 10) {
      alert('카드뉴스로 만들고 싶은 내용을 최소 10자 이상 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    setGeneratedCards([]);
    setPreviewCards([]);
    setGeneratingStatus('AI가 카드뉴스 콘텐츠를 분석하고 있습니다...');

    try {
      const formData = new FormData();

      // 선택된 배경 템플릿 URL에서 이미지 가져오기
      const selectedTemplateUrl = backgroundTemplates[selectedBackground].url;
      
      let imageFile;
      try {
        const imageResponse = await fetch(selectedTemplateUrl);
        if (!imageResponse.ok) {
            throw new Error(`배경 이미지 가져오기 실패: HTTP ${imageResponse.status}`);
        }
        const imageBlob = await imageResponse.blob();
        imageFile = new File([imageBlob], 'background.png', { type: imageBlob.type });
      } catch (error) {
        console.error('배경 이미지 fetch 오류:', error);
        // 이미지를 가져오지 못하더라도 요청을 진행하고 싶다면 이 부분을 조정하세요.
        throw new Error('배경 이미지 파일을 준비하는 데 실패했습니다.');
      }
      

      // 이미지 파일 추가
      formData.append('images', imageFile);

      // 제목과 설명 추가 (JSON 문자열로 변환)
      formData.append('titles', JSON.stringify(titles));
      // descriptions 필드가 사용되지 않더라도 서버가 예상한다면 빈 배열로 추가
      formData.append('descriptions', JSON.stringify(descriptions)); 

      // 스타일 옵션 추가
      formData.append('fontStyle', fontStyle);
      formData.append('colorTheme', colorTheme);
      formData.append('purpose', purpose);
      formData.append('layoutStyle', layoutStyle);
      
      // 💡 디버깅을 위해 FormData 내용 확인 (필요시 주석 해제)
      // console.log('--- FormData Contents ---');
      // for (let [key, value] of formData.entries()) {
      //   console.log(`${key}:`, value);
      // }
      // console.log('-------------------------');

      const response = await fetch('/api/generate-cardnews-stream', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        // 서버에서 상세 오류 메시지를 반환한다면, 여기서 JSON을 파싱 시도할 수 있음
        const errorText = await response.text();
        console.error('서버 응답 오류:', errorText);
        throw new Error(`카드뉴스 생성 요청에 실패했습니다. (HTTP ${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const cards = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 마지막 조각은 불완전할 수 있으므로 버퍼에 저장

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          const raw = line.slice(6).trim();

          // JSON 구조인지 확인
          if (!(raw.startsWith('{') && raw.endsWith('}'))) {
            console.warn('⚠ JSON 형식 아님 → 스킵됨:', raw);
            continue;
          }

          let data;
          try {
            data = JSON.parse(raw);
          } catch (err) {
            console.error('❌ JSON 파싱 실패:', err, raw);
            continue;
          }

          // SSE 메시지 타입별 처리
          if (data.type === 'status') {
            setGeneratingStatus(data.message);
            continue;
          }

          if (data.type === 'card') {
            cards.push(data.card);
            setPreviewCards([...cards]);
            setGeneratingStatus(`카드 생성 완료`);
            continue;
          }

          if (data.type === 'complete') {
            setGeneratedCards(cards);
            setGeneratingStatus('');
            alert(`✅ AI가 카드뉴스를 생성했습니다!`);
            continue;
          }

          if (data.type === 'error') {
            throw new Error(data.message || '알 수 없는 AI 생성 오류');
          }
        }
      }
    } catch (error) {
      console.error('카드뉴스 생성 오류:', error);
      alert(`카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
      setGeneratingStatus('');
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
        <h2>📰 AI 카드뉴스 생성기</h2>
        <p>선택된 스타일과 배경 이미지, 입력한 내용을 바탕으로 카드뉴스를 만듭니다</p>
      </div>

      <div className="cardnews-content">
        {/* 1. 스타일 선택 섹션 */}
        <div className="style-section">
          <h3>1. 스타일 선택</h3>
          <p className="section-desc">카드뉴스의 용도와 분위기를 선택하세요</p>

          <div className="style-options">
            {/* 용도 선택 */}
            <div className="style-group">
              <h4>📋 용도</h4>
              <div className="style-buttons">
                {/* ... (이전 코드와 동일) ... */}
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
                {/* ... (이전 코드와 동일) ... */}
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
                {/* ... (이전 코드와 동일) ... */}
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
                {/* ... (이전 코드와 동일) ... */}
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
        
        <hr/>

        {/* 2. 배경 템플릿 선택 섹션 */}
        <div className="upload-section">
          <h3>2. 배경 템플릿 선택</h3>
          <p className="section-desc">카드뉴스에 사용할 기본 배경 디자인을 선택하세요.</p>
          <div className="uploaded-images">
            <div className="image-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
              {backgroundTemplates.map((template, index) => (
                <div
                  key={template.id}
                  className={`image-item ${selectedBackground === index ? 'selected' : ''}`}
                  onClick={() => setSelectedBackground(index)}
                  style={{
                    cursor: 'pointer',
                    border: selectedBackground === index ? '3px solid #FF8B5A' : '2px solid #ddd',
                    borderRadius: '8px',
                    padding: '10px',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <img
                    src={template.url}
                    alt={template.name}
                    style={{
                      width: '100%',
                      height: '200px',
                      objectFit: 'cover',
                      borderRadius: '4px'
                    }}
                  />
                  <p style={{ textAlign: 'center', marginTop: '10px', fontWeight: selectedBackground === index ? 'bold' : 'normal' }}>
                    {selectedBackground === index ? '✓ 선택됨' : template.name}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <hr/>

        {/* 3. 내용 입력 섹션 */}
        <div className="upload-section">
          <h3>3. 카드뉴스 내용 입력</h3>
          <p className="section-desc">AI가 입력한 내용을 바탕으로 1장의 카드뉴스를 자동 생성합니다</p>
          <div className="uploaded-images">
            <div className="image-list">
              <div className="image-item">
                <img
                  src={backgroundTemplates[selectedBackground].url}
                  alt="Selected template"
                  className="preview-thumbnail"
                />
                <div className="image-info">
                  <textarea
                    placeholder="카드뉴스로 만들고 싶은 내용을 입력하세요. 예: 새로 나온 딸기 케이크 50% 할인, 3일간만 진행되는 특별 행사. (내용이 길수록 AI가 더 풍부하게 생성합니다.)"
                    value={titles[0]}
                    onChange={(e) => handleTitleChange(0, e.target.value)}
                    className="title-input-small"
                    rows="4"
                    style={{ resize: 'vertical', minHeight: '100px' }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <hr/>

        {/* 생성 버튼 */}
        <div className="generate-section">
          <button
            onClick={handleGenerateCardNews}
            disabled={isGenerating || titles[0].trim().length < 10}
            className="btn-generate"
          >
            {isGenerating ? '🔄 AI가 열심히 생성 중...' : '🎨 카드뉴스 생성하기'}
          </button>
          {generatingStatus && (
            <p className="generating-status" style={{ marginTop: '20px', fontSize: '16px', color: '#FF8B5A', fontWeight: 'bold' }}>
              {generatingStatus}
            </p>
          )}
        </div>

        <hr/>

        {/* 생성 중 미리보기 */}
        {isGenerating && previewCards.length > 0 && (
          <div className="result-section">
            <div className="result-header">
              <h3>생성 중 미리보기</h3>
            </div>
            <div className="cards-grid">
              {previewCards.map((card, index) => (
                <div key={index} className="card-item generating">
                  {/* Base64 이미지 데이터 사용 */}
                  <img src={card} alt={`Preview Card ${index + 1}`} className="card-image" /> 
                  <p style={{ textAlign: 'center', marginTop: '10px' }}>카드 {index + 1}</p>
                </div>
              ))}
            </div>
          </div>
        )}

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
