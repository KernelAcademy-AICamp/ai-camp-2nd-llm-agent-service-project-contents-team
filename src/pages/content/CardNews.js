import React, { useState } from 'react';
import './CardNews.css'; // 별도의 CSS 파일이 있다고 가정

function CardNews() {
  const [titles, setTitles] = useState(['']);
  const [descriptions, setDescriptions] = useState(['']);
  const [generatedCards, setGeneratedCards] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState(''); // 생성 상태 메시지
  const [previewCards, setPreviewCards] = useState([]); // 생성 중 미리보기

  // AI Agentic 모드 상태
  const [agenticAnalysis, setAgenticAnalysis] = useState(null); // AI 분석 결과
  const [processLogs, setProcessLogs] = useState([]); // AI 처리 과정 로그
  const [pagePlans, setPagePlans] = useState([]); // 기획된 페이지들

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
    setProcessLogs([]);
    setPagePlans([]);
    setGeneratingStatus('🤖 AI 작업 시작...');

    try {
      const formData = new FormData();
      formData.append('prompt', titles[0]);
      formData.append('purpose', purpose);
      formData.append('fontStyle', fontStyle);
      formData.append('colorTheme', colorTheme);
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
      let finalAnalysis = null;
      let finalScore = null;

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
            setProcessLogs(prev => [...prev, { type: 'status', message: data.message, time: new Date().toLocaleTimeString() }]);
          }

          // 분석 결과
          else if (data.type === 'analysis') {
            finalAnalysis = data.data;
            setProcessLogs(prev => [...prev, {
              type: 'analysis',
              message: `📊 분석 완료: ${data.data.page_count}페이지, ${data.data.target_audience}, ${data.data.tone}`,
              time: new Date().toLocaleTimeString()
            }]);
          }

          // 페이지 기획
          else if (data.type === 'page_planned') {
            setPagePlans(prev => [...prev, { page: data.page, title: data.title, content: data.content }]);
            setProcessLogs(prev => [...prev, {
              type: 'page',
              message: `📄 페이지 ${data.page}: "${data.title}"`,
              detail: data.content,
              time: new Date().toLocaleTimeString()
            }]);
          }

          // 프롬프트 생성
          else if (data.type === 'prompt_generated') {
            setProcessLogs(prev => [...prev, {
              type: 'prompt',
              message: `🎨 페이지 ${data.page} 비주얼 프롬프트 생성`,
              detail: data.prompt,
              time: new Date().toLocaleTimeString()
            }]);
          }

          // 품질 점수
          else if (data.type === 'quality_report') {
            finalScore = data.score;
            setProcessLogs(prev => [...prev, {
              type: 'quality',
              message: `⭐ 품질 점수: ${data.score.toFixed(1)}/10`,
              time: new Date().toLocaleTimeString()
            }]);
          }

          // 이미지 생성
          else if (data.type === 'image_generated') {
            setProcessLogs(prev => [...prev, {
              type: 'image',
              message: `🖼️ 페이지 ${data.page} 배경 이미지 생성 완료`,
              time: new Date().toLocaleTimeString()
            }]);
          }

          // 카드 생성 완료
          else if (data.type === 'card') {
            cards.push(data.card);
            setPreviewCards([...cards]);
            setProcessLogs(prev => [...prev, {
              type: 'card',
              message: `✅ 카드 ${data.index + 1} 완성: "${data.title}"`,
              time: new Date().toLocaleTimeString()
            }]);
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
      setProcessLogs(prev => [...prev, { type: 'error', message: `❌ 오류: ${error.message}`, time: new Date().toLocaleTimeString() }]);
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

        {/* AI 처리 과정 로그 (실시간) */}
        {processLogs.length > 0 && (
          <div className="result-section" style={{ background: '#fff9f0', padding: '20px', borderRadius: '8px', marginBottom: '20px', border: '2px solid #ff9800' }}>
            <h3>🔄 AI 처리 과정 (실시간)</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto', marginTop: '15px' }}>
              {processLogs.map((log, index) => (
                <div key={index} style={{
                  padding: '12px',
                  background: log.type === 'error' ? '#ffebee' : log.type === 'card' ? '#e8f5e9' : 'white',
                  borderLeft: `4px solid ${log.type === 'error' ? '#f44336' : log.type === 'card' ? '#4caf50' : log.type === 'prompt' ? '#9c27b0' : '#2196f3'}`,
                  borderRadius: '4px',
                  marginBottom: '10px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <strong style={{ color: '#333' }}>{log.message}</strong>
                      {log.detail && (
                        <div style={{
                          marginTop: '8px',
                          padding: '10px',
                          background: '#f5f5f5',
                          borderRadius: '4px',
                          fontSize: '13px',
                          color: '#666',
                          fontFamily: 'monospace',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word'
                        }}>
                          {log.detail}
                        </div>
                      )}
                    </div>
                    <span style={{ fontSize: '11px', color: '#999', marginLeft: '10px', whiteSpace: 'nowrap' }}>
                      {log.time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
