import React, { useState } from 'react';
import './CardNews.css'; // 별도의 CSS 파일이 있다고 가정

function CardNews() {
  const [titles, setTitles] = useState(['']);
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState('');
  const [previewCards, setPreviewCards] = useState([]);

  // AI Agentic 모드 상태
  const [agenticAnalysis, setAgenticAnalysis] = useState(null);
  const [pagePlans, setPagePlans] = useState([]);

  // 스타일 옵션
  const [colorTheme, setColorTheme] = useState('black'); // 'black' | 'blue' | 'orange'
  const [layoutStyle, setLayoutStyle] = useState('center'); // 'top' | 'center' | 'bottom'
  const [fontWeight, setFontWeight] = useState('bold'); // 'light' | 'medium' | 'bold'

  const handleTitleChange = (index, value) => {
    const newTitles = [...titles];
    newTitles[index] = value;
    setTitles(newTitles);
  };

  // AI Agentic 모드로 카드뉴스 생성 (스트리밍)
  const handleGenerateAgenticCardNews = async () => {
    if (titles[0].trim().length < 10) {
      alert('카드뉴스로 만들고 싶은 내용을 최소 10자 이상 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    setGeneratedCards([]);
    setPreviewCards([]);
    setAgenticAnalysis(null);
    setPagePlans([]);
    setGeneratingStatus('🤖 AI 작업 시작...');

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

          // 상태 메시지
          if (data.type === 'status') {
            setGeneratingStatus(data.message);
          }

          // 페이지 기획
          else if (data.type === 'page_planned') {
            setPagePlans(prev => [...prev, { page: data.page, title: data.title, content: data.content }]);
          }

          // 카드 생성 완료
          else if (data.type === 'card') {
            cards.push(data.card);
            setPreviewCards([...cards]);
          }

          // 완료
          else if (data.type === 'complete') {
            setGeneratedCards(cards);
            setAgenticAnalysis({
              pageCount: data.count,
              targetAudience: data.target_audience,
              tone: data.tone,
              qualityScore: data.quality_score,
              pagesInfo: pagePlans
            });
            setGeneratingStatus('');

            alert(`✅ ${data.count}장의 AI 카드뉴스가 생성되었습니다!\n\n` +
                  `📊 품질 점수: ${data.quality_score ? data.quality_score.toFixed(1) : 'N/A'}/10\n` +
                  `🎯 타겟: ${data.target_audience || 'N/A'}\n` +
                  `🎨 톤: ${data.tone || 'N/A'}`);
          }

          // 오류
          else if (data.type === 'error') {
            throw new Error(data.message);
          }
        }
      }
    } catch (error) {
      console.error('AI 카드뉴스 생성 오류:', error);
      alert(`AI 카드뉴스 생성 중 오류가 발생했습니다:\n${error.message}`);
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
        <p>🤖 AI가 프롬프트만으로 자동으로 페이지별 내용을 구성하고 카드뉴스를 생성합니다</p>

        {/* AI Agentic 모드 안내 */}
        <div style={{ marginTop: '20px', padding: '15px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: '8px', color: 'white' }}>
          <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
            🚀 AI Agentic 모드
          </div>
          <p style={{ fontSize: '14px', margin: 0, opacity: 0.95 }}>
            ✅ AI가 페이지 수, 제목, 내용, 이미지를 모두 자동으로 생성합니다
          </p>
        </div>
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

        {/* 2. 내용 입력 섹션 */}
        <div className="upload-section">
          <h3>2. 카드뉴스 내용 입력</h3>
          <p className="section-desc">
            🤖 간단한 프롬프트만 입력하세요. AI가 페이지별 제목, 내용, 이미지를 모두 자동으로 생성합니다
          </p>
          <div className="uploaded-images">
            <div className="image-list">
              <div className="image-item">
                <div className="image-info">
                  <textarea
                    placeholder="예시:
• 새로운 카페 오픈 홍보
• 여름 세일 50% 할인 이벤트
• 딸기 시즌 신메뉴 3종 출시
• 강남역 필라테스 개업 50% 할인

프롬프트가 구체적일수록 더 좋은 결과가 나옵니다!"
                    value={titles[0]}
                    onChange={(e) => handleTitleChange(0, e.target.value)}
                    className="title-input-small"
                    rows="6"
                    style={{ resize: 'vertical', minHeight: '150px' }}
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
            onClick={handleGenerateAgenticCardNews}
            disabled={isGenerating || titles[0].trim().length < 10}
            className="btn-generate"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              fontSize: '18px'
            }}
          >
            {isGenerating ? '🔄 AI가 열심히 생성 중...' : '🚀 AI가 자동으로 카드뉴스 생성하기'}
          </button>
          {generatingStatus && (
            <p className="generating-status" style={{ marginTop: '20px', fontSize: '16px', color: '#FF8B5A', fontWeight: 'bold' }}>
              {generatingStatus}
            </p>
          )}
        </div>

        <hr/>

        {/* AI 분석 결과 표시 */}
        {agenticAnalysis && !isGenerating && (
          <div className="result-section" style={{ background: '#f0f8ff', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
            <h3>📊 AI 분석 결과</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px', marginTop: '15px' }}>
              <div style={{ padding: '15px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <strong>📄 생성된 페이지 수:</strong> {agenticAnalysis.pageCount}장
              </div>
              <div style={{ padding: '15px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <strong>⭐ 품질 점수:</strong> {agenticAnalysis.qualityScore ? `${agenticAnalysis.qualityScore.toFixed(1)}/10` : 'N/A'}
              </div>
              <div style={{ padding: '15px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <strong>🎯 타겟 청중:</strong> {agenticAnalysis.targetAudience || 'N/A'}
              </div>
              <div style={{ padding: '15px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                <strong>🎨 톤앤매너:</strong> {agenticAnalysis.tone || 'N/A'}
              </div>
            </div>
            {agenticAnalysis.pagesInfo && agenticAnalysis.pagesInfo.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <h4>📝 페이지 구성</h4>
                <div style={{ marginTop: '10px' }}>
                  {agenticAnalysis.pagesInfo.map((page, index) => (
                    <div key={index} style={{ padding: '10px', background: 'white', borderRadius: '8px', marginBottom: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                      <strong>페이지 {page.page}:</strong> {page.title}
                      <br />
                      <span style={{ color: '#666', fontSize: '14px' }}>{page.content}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

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
