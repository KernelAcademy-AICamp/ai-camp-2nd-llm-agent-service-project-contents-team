import { useState, useEffect } from 'react';
import api, { aiContentAPI } from '../../services/api';
import { generateAgenticContent } from '../../services/agenticService';
import './ContentCommon.css';
import './ContentCreatorSimple.css';

function ContentCreatorSimple() {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('create');

  // 콘텐츠 타입: 'text' | 'image' | 'both'
  const [contentType, setContentType] = useState('both');

  // 입력 상태
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('casual');
  const [selectedPlatforms, setSelectedPlatforms] = useState(['instagram']);
  const [imageCount, setImageCount] = useState(1);  // 이미지 생성 갯수

  // 생성 상태
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');

  // 결과 상태
  const [result, setResult] = useState(null);

  // 생성 내역 상태
  const [history, setHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

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
    { id: 'instagram', label: 'Instagram' },
    { id: 'facebook', label: 'Facebook' },
    { id: 'blog', label: '블로그' },
    { id: 'x', label: 'X (Twitter)' },
  ];

  // 생성 내역 불러오기
  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const data = await aiContentAPI.list(0, 50);
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

  // 내역 아이템 선택
  const handleSelectHistory = (item) => {
    setSelectedHistoryItem(item);
  };

  // 내역에서 복사
  const handleCopyHistoryBlog = (item) => {
    const blogText = `${item.blog_title}\n\n${item.blog_content}\n\n태그: ${item.blog_tags?.join(', ') || ''}`;
    navigator.clipboard.writeText(blogText);
    alert('블로그 콘텐츠가 복사되었습니다.');
  };

  const handleCopyHistorySNS = (item) => {
    const snsText = `${item.sns_content}\n\n${item.sns_hashtags?.join(' ') || ''}`;
    navigator.clipboard.writeText(snsText);
    alert('SNS 콘텐츠가 복사되었습니다.');
  };

  // 내역 삭제
  const handleDeleteHistory = async (contentId) => {
    if (!window.confirm('이 콘텐츠를 삭제하시겠습니까?')) return;
    try {
      await aiContentAPI.delete(contentId);
      setHistory(history.filter(item => item.id !== contentId));
      if (selectedHistoryItem?.id === contentId) {
        setSelectedHistoryItem(null);
      }
      alert('삭제되었습니다.');
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  // 날짜 포맷
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 자동 저장 함수
  const autoSaveContent = async (content, imageUrls = []) => {
    try {
      const saveData = {
        input_text: content.analysis?.subject || topic,
        input_image_count: imageUrls.length,
        generated_image_urls: imageUrls,
        blog_title: content.blog?.title || '',
        blog_content: content.blog?.content || '',
        blog_tags: content.blog?.tags || [],
        sns_content: content.sns?.content || '',
        sns_hashtags: content.sns?.tags || [],
        analysis_data: content.analysis || null,
        blog_score: content.critique?.blog?.score || null,
        sns_score: content.critique?.sns?.score || null,
        critique_data: content.critique || null,
        generation_attempts: content.metadata?.attempts || 1
      };

      await aiContentAPI.save(saveData);
      console.log('✅ AI 콘텐츠 자동 저장 완료');
    } catch (error) {
      console.error('콘텐츠 자동 저장 실패:', error);
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
        const hasSNS = selectedPlatforms.some(p => ['instagram', 'facebook', 'x'].includes(p));

        // 선택된 스타일 정보 가져오기
        const selectedStyle = styles.find(s => s.id === style);

        // agenticService로 블로그 + SNS 콘텐츠 생성 (스타일 적용)
        const agenticResult = await generateAgenticContent(
          {
            textInput: topic,
            images: [],
            styleTone: selectedStyle?.textTone || '친근하고 편안한 말투로'
          },
          (progress) => setProgress(progress.message)
        );

        generatedResult.text = {
          blog: hasBlog ? agenticResult.blog : null,
          sns: hasSNS ? agenticResult.sns : null,
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
      if (generatedResult.text) {
        const imageUrls = generatedResult.images?.map(img => img.url) || [];
        await autoSaveContent({
          blog: generatedResult.text.blog,
          sns: generatedResult.text.sns,
          analysis: generatedResult.text.analysis,
          critique: generatedResult.text.critique,
          metadata: { attempts: 1 }
        }, imageUrls);
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
        <h2>글 + 이미지 생성</h2>
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

            {/* 콘텐츠 타입 선택 */}
            <div className="form-group">
              <label>생성 타입</label>
              <div className="type-options">
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
                  <span className="recommended-label">추천</span>
                  <div className="type-header">
                    <h4>글 + 이미지</h4>
                  </div>
                  <p className="type-desc">완성 콘텐츠</p>
                </div>
              </div>
            </div>

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
                  {[1, 2, 3, 4].map((count) => (
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

            {/* 생성 버튼 */}
            <button
              className="btn-generate"
              onClick={handleGenerate}
              disabled={isGenerating || !topic.trim()}
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
          {/* 품질 점수 표시 */}
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

          <div className="result-grid">
            {/* 블로그 콘텐츠 */}
            {result.text?.blog && (
              <div className="result-card">
                <div className="result-card-header">
                  <h3>네이버 블로그</h3>
                  <div className="result-card-actions">
                    {result.text.critique?.blog?.score && (
                      <span className="score-badge blog">{result.text.critique.blog.score}점</span>
                    )}
                    <button className="btn-copy" onClick={handleCopyBlog}>
                      복사
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

            {/* SNS 콘텐츠 */}
            {result.text?.sns && (
              <div className="result-card">
                <div className="result-card-header">
                  <h3>SNS (Instagram/Facebook)</h3>
                  <div className="result-card-actions">
                    {result.text.critique?.sns?.score && (
                      <span className="score-badge sns">{result.text.critique.sns.score}점</span>
                    )}
                    <button className="btn-copy" onClick={handleCopySNS}>
                      복사
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

            {/* 생성된 이미지들 */}
            {result.images && result.images.length > 0 && (
              <div className="result-card result-card-full">
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
                      <div key={index} className="image-item">
                        <img src={img.url} alt={`Generated ${index + 1}`} />
                        <button
                          className="btn-download-single"
                          onClick={() => handleDownloadImage(img.url, index)}
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
                      <h4>{item.blog_title || '제목 없음'}</h4>
                      <span className="history-date">{formatDate(item.created_at)}</span>
                    </div>
                    <p className="history-preview">
                      {item.blog_content?.substring(0, 80)}...
                    </p>
                    <div className="history-item-meta">
                      {item.blog_score && (
                        <span className="score-badge blog">블로그 {item.blog_score}점</span>
                      )}
                      {item.sns_score && (
                        <span className="score-badge sns">SNS {item.sns_score}점</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* 오른쪽: 선택된 콘텐츠 상세 */}
              <div className="history-detail">
                {selectedHistoryItem ? (
                  <>
                    {/* 블로그 콘텐츠 */}
                    <div className="result-card">
                      <div className="result-card-header">
                        <h3>네이버 블로그</h3>
                        <div className="result-card-actions">
                          <button className="btn-copy" onClick={() => handleCopyHistoryBlog(selectedHistoryItem)}>
                            복사
                          </button>
                          <button className="btn-delete" onClick={() => handleDeleteHistory(selectedHistoryItem.id)}>
                            삭제
                          </button>
                        </div>
                      </div>
                      <div className="result-card-content">
                        <div className="blog-title">{selectedHistoryItem.blog_title}</div>
                        <div className="text-result">
                          {selectedHistoryItem.blog_content}
                        </div>
                        {selectedHistoryItem.blog_tags && (
                          <div className="result-tags">
                            {selectedHistoryItem.blog_tags.map((tag, idx) => (
                              <span key={idx} className="tag-item">{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* SNS 콘텐츠 */}
                    {selectedHistoryItem.sns_content && (
                      <div className="result-card">
                        <div className="result-card-header">
                          <h3>SNS (Instagram/Facebook)</h3>
                          <div className="result-card-actions">
                            <button className="btn-copy" onClick={() => handleCopyHistorySNS(selectedHistoryItem)}>
                              복사
                            </button>
                          </div>
                        </div>
                        <div className="result-card-content">
                          <div className="text-result sns-content">
                            {selectedHistoryItem.sns_content}
                          </div>
                          {selectedHistoryItem.sns_hashtags && (
                            <div className="result-tags">
                              {selectedHistoryItem.sns_hashtags.map((tag, idx) => (
                                <span key={idx} className="tag-item hashtag">{tag}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 생성된 이미지 */}
                    {selectedHistoryItem.generated_image_urls && selectedHistoryItem.generated_image_urls.length > 0 && (
                      <div className="result-card result-card-full">
                        <div className="result-card-header">
                          <h3>생성된 이미지 ({selectedHistoryItem.generated_image_urls.length}장)</h3>
                        </div>
                        <div className="result-card-content">
                          <div className="images-grid">
                            {selectedHistoryItem.generated_image_urls.map((url, idx) => (
                              <div key={idx} className="image-item">
                                <img src={url} alt={`생성된 이미지 ${idx + 1}`} />
                                <button
                                  className="btn-download-single"
                                  onClick={() => handleDownloadImage(url, idx)}
                                >
                                  다운로드
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
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
    </div>
  );
}

export default ContentCreatorSimple;
