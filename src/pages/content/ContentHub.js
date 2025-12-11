import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { contentSessionAPI } from '../../services/api';
import './ContentHub.css';

// 기본 샘플 데이터 (데이터가 없을 때 사용)
const DEFAULT_PREVIEWS = [
  {
    id: 'sample-1',
    type: 'blog',
    label: '블로그',
    title: '성수동 핫플 카페 투어 BEST 5',
    content: '요즘 성수동이 정말 핫하죠! 오늘은 제가 직접 다녀온 성수동 카페 중에서 분위기와 맛 모두 만족스러웠던 곳들을 소개해드릴게요. 첫 번째는 빈티지 감성이 물씬 풍기는 카페 온더플레인입니다. 이곳은 특히 시그니처 라떼가 유명해요.',
    tags: ['#성수동카페', '#카페추천'],
  },
  {
    id: 'sample-2',
    type: 'instagram',
    label: 'Instagram',
    title: '',
    content: '성수동에서 발견한 숨은 보석 같은 카페 ☕✨\n\n빈티지 인테리어에 맛있는 커피까지!\n사진 찍기 좋은 포토존도 있어서\n인생샷 건지고 왔어요 📸\n\n위치는 성수역 3번 출구에서 도보 5분!',
    tags: ['#성수카페', '#카페스타그램', '#서울카페'],
  },
  {
    id: 'sample-3',
    type: 'x',
    label: 'X (Twitter)',
    title: '',
    content: '성수동 카페 투어 완료 ☕\n\n빈티지 감성 터지는 곳 발견!\n커피 맛도 분위기도 최고였음 👍\n\n특히 시그니처 라떼 강추!\n달달하면서도 깔끔한 맛이에요',
    tags: ['#성수동', '#카페투어'],
  },
  {
    id: 'sample-4',
    type: 'threads',
    label: 'Threads',
    title: '',
    content: '오늘 성수동 카페 탐방 다녀왔는데요,\n진짜 숨은 보석 같은 곳을 발견했어요!\n\n빈티지한 인테리어에 커피 맛까지 완벽 ✨\n조용히 작업하기도 좋고\n친구랑 수다 떨기도 딱이에요!',
    tags: ['#성수동카페', '#카페추천', '#일상'],
  },
  {
    id: 'sample-5',
    type: 'image',
    label: 'AI 이미지',
    title: 'AI로 생성한 이미지',
    content: '',
    isImage: true,
    imageUrl: null,
  },
];

// 히스토리 데이터를 슬라이드 형식으로 변환 (플랫폼별 하나씩만)
const convertHistoryToSlides = (historyItems) => {
  const slides = [];
  const addedTypes = new Set(); // 이미 추가된 플랫폼 타입 추적

  for (const item of historyItems) {
    // 블로그 콘텐츠 (아직 없으면 추가)
    if (item.blog && !addedTypes.has('blog')) {
      slides.push({
        id: `${item.id}-blog`,
        type: 'blog',
        label: '블로그',
        title: item.blog.title || '',
        content: item.blog.content?.substring(0, 200) || '',
        tags: (item.blog.tags || []).slice(0, 3),
      });
      addedTypes.add('blog');
    }

    // Instagram/Facebook 콘텐츠
    if (item.sns && !addedTypes.has('instagram')) {
      slides.push({
        id: `${item.id}-sns`,
        type: 'instagram',
        label: 'Instagram',
        title: '',
        content: item.sns.content?.substring(0, 200) || '',
        tags: (item.sns.hashtags || item.sns.tags || []).slice(0, 3),
      });
      addedTypes.add('instagram');
    }

    // X 콘텐츠
    if (item.x && !addedTypes.has('x')) {
      slides.push({
        id: `${item.id}-x`,
        type: 'x',
        label: 'X (Twitter)',
        title: '',
        content: item.x.content?.substring(0, 200) || '',
        tags: (item.x.hashtags || item.x.tags || []).slice(0, 2),
      });
      addedTypes.add('x');
    }

    // Threads 콘텐츠
    if (item.threads && !addedTypes.has('threads')) {
      slides.push({
        id: `${item.id}-threads`,
        type: 'threads',
        label: 'Threads',
        title: '',
        content: item.threads.content?.substring(0, 200) || '',
        tags: (item.threads.hashtags || item.threads.tags || []).slice(0, 3),
      });
      addedTypes.add('threads');
    }

    // 이미지 (아직 없으면 추가)
    if (item.images?.length > 0 && !addedTypes.has('image')) {
      slides.push({
        id: `${item.id}-image`,
        type: 'image',
        label: 'AI 이미지',
        title: item.topic || '생성된 이미지',
        content: '',
        isImage: true,
        imageUrl: item.images[0].image_url,
      });
      addedTypes.add('image');
    }

    // 모든 플랫폼이 채워졌으면 종료
    if (addedTypes.size >= 5) break;
  }

  return slides;
};

function ContentHub() {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [previews, setPreviews] = useState(DEFAULT_PREVIEWS);
  const [isLoading, setIsLoading] = useState(true);

  // 히스토리 데이터 로드
  const fetchHistory = useCallback(async () => {
    try {
      const listData = await contentSessionAPI.list(0, 5); // 최근 5개
      if (listData && listData.length > 0) {
        // 각 아이템의 전체 데이터를 가져옴
        const fullDataPromises = listData.map(item => contentSessionAPI.get(item.id));
        const fullData = await Promise.all(fullDataPromises);
        const slides = convertHistoryToSlides(fullData);
        if (slides.length > 0) {
          setPreviews(slides.slice(0, 8)); // 최대 8개 슬라이드
        }
      }
    } catch (error) {
      // 에러 시 기본 샘플 데이터 유지
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // 자동 슬라이드
  useEffect(() => {
    if (previews.length === 0) return;

    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % previews.length);
    }, 3000);
    return () => clearInterval(timer);
  }, [previews.length]);

  return (
    <div className="content-hub">
      <div className="hub-container">
        {/* 왼쪽: 입력 섹션 */}
        <div className="hub-input-section">
          <h1 className="hub-title">
            <span className="title-highlight">AI</span>로 콘텐츠를
            <br />한번에 만들어보세요
          </h1>
          <p className="hub-subtitle">
            주제만 입력하면 블로그, SNS, 이미지까지 자동 생성
          </p>

          <button className="generate-btn" onClick={() => navigate('/create')}>
            콘텐츠 생성하기
            <span className="btn-arrow">→</span>
          </button>

          <div className="other-options">
            <button className="option-btn" onClick={() => navigate('/history')}>
              <span className="option-icon">📋</span>
              생성 내역 보기
            </button>
          </div>

        </div>

        {/* 오른쪽: 슬라이드 미리보기 섹션 */}
        <div className="hub-preview-section">
          <div className="preview-slider">
            {previews.map((item, index) => (
              <div
                key={item.id}
                className={`preview-slide ${index === currentSlide ? 'active' : ''}`}
              >
                <div className="preview-card">
                  <div className="preview-card-header">
                    <span className={`preview-badge badge-${item.type}`}>
                      {item.label}
                    </span>
                  </div>
                  {item.isVideo ? (
                    <div className="preview-video-placeholder">
                      <div className="video-play-btn">▶</div>
                      <div className="video-progress">
                        <div className="video-progress-bar"></div>
                      </div>
                      <span className="video-duration">0:15</span>
                    </div>
                  ) : item.isImage ? (
                    item.imageUrl ? (
                      <div className="preview-image-actual">
                        <img src={item.imageUrl} alt={item.title} />
                      </div>
                    ) : (
                      <div className="preview-image-placeholder">
                        <div className="image-icon">🖼️</div>
                        <span>AI 생성 이미지</span>
                      </div>
                    )
                  ) : (
                    <div className="preview-card-body">
                      {item.title && <h4 className="preview-title">{item.title}</h4>}
                      {item.type === 'blog' ? (
                        <div className="preview-content preview-markdown">
                          <ReactMarkdown remarkPlugins={[remarkBreaks]}>{item.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="preview-content">{item.content}</p>
                      )}
                      {item.tags && item.tags.length > 0 && (
                        <div className="preview-tags">
                          {item.tags.map((tag, i) => (
                            <span key={i} className="preview-tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* 슬라이드 인디케이터 */}
          <div className="slide-indicators">
            {previews.map((_, index) => (
              <button
                key={index}
                className={`slide-dot ${index === currentSlide ? 'active' : ''}`}
                onClick={() => setCurrentSlide(index)}
              />
            ))}
          </div>

          <p className="preview-caption">
            {isLoading ? '불러오는 중...' : '내가 생성한 콘텐츠 미리보기'}
          </p>
        </div>
      </div>
    </div>
  );
}

export default ContentHub;
