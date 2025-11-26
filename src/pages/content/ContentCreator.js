import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ContentCreator.css';
import BlogPostForm from '../../components/BlogPostForm';
import BlogPostResult from '../../components/BlogPostResult';
import AIContentGenerator from './AIContentGenerator';
import { generateBlogPost } from '../../services/geminiService';

function ContentCreator() {
  const navigate = useNavigate();
  const [contentType, setContentType] = useState('social');
  const [platform, setPlatform] = useState('instagram');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedBlogPost, setGeneratedBlogPost] = useState(null);

  const contentTypes = [
    { id: 'ai', label: 'AI 글 생성', icon: '🤖' },
    { id: 'social', label: '소셜 미디어', icon: '📱' },
    { id: 'blog', label: '블로그 포스트', icon: '📝' },
    { id: 'video-script', label: '비디오 스크립트', icon: '🎥' },
    { id: 'email', label: '이메일', icon: '✉️' },
    { id: 'image-studio', label: '이미지 스튜디오', icon: '🎨' },
    { id: 'image', label: '이미지 생성', icon: '🎨' },
    { id: 'cardnews', label: '카드뉴스', icon: '📰' },
    { id: 'ai-video', label: 'AI 동영상', icon: '🎬' },
  ];

  const platforms = {
    social: ['Instagram', 'Facebook', 'Twitter', 'LinkedIn'],
    blog: ['WordPress', 'Naver Blog', 'Tistory', 'Medium'],
    'video-script': ['YouTube', 'TikTok', 'Reels'],
    email: ['Newsletter', 'Promotion', 'Announcement'],
    image: ['Instagram', 'Pinterest', 'Blog', 'Social Media'],
    cardnews: ['Instagram', 'Facebook', 'Blog', 'Kakao'],
    'ai-video': ['YouTube', 'Instagram Reels', 'TikTok', 'Short Form'],
  };

  const aiModels = [
    { id: 'whisk', label: '✨ Whisk AI (무료)', provider: 'Pollinations' },
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Anthropic' },
    { id: 'gemini', label: '제미나이 (Gemini)', provider: 'Google' },
  ];

  // AI 동영상 또는 카드뉴스 선택 시 해당 페이지로 이동
  useEffect(() => {
    if (contentType === 'ai-video') {
      navigate('/video');
    } else if (contentType === 'cardnews') {
      navigate('/cardnews');
    }
  }, [contentType, navigate]);

  const handleGenerateBlogPost = async (formData) => {
    setIsGenerating(true);
    try {
      const result = await generateBlogPost(formData);
      setGeneratedBlogPost(result);
      setTitle(result.title);
      setContent(result.content);
    } catch (error) {
      alert('블로그 포스트 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
      console.error('Error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditBlogPost = () => {
    setGeneratedBlogPost(null);
  };

  const handleSaveBlogPost = () => {
    alert('콘텐츠가 저장되었습니다.');
  };

  const handleGenerate = () => {
    alert('AI 콘텐츠 생성 기능은 추후 구현 예정입니다.');
  };

  const handleSave = () => {
    alert('콘텐츠가 저장되었습니다.');
  };

  const handleSchedule = () => {
    alert('스케줄 설정 화면으로 이동합니다.');
  };

  return (
    <div className="content-creator">
      <div className="creator-header">
        <h2>콘텐츠 생성</h2>
        {contentType !== 'ai' && (
          <div className="header-actions">
            <button className="btn-secondary" onClick={handleSave}>
              임시 저장
            </button>
            <button className="btn-primary" onClick={handleSchedule}>
              저장 및 예약
            </button>
          </div>
        )}
      </div>

      <div className={`creator-content ${contentType === 'blog' || contentType === 'ai' ? 'blog-layout' : ''}`}>
        {/* 콘텐츠 타입 선택 */}
        <div className="section">
          <h3>콘텐츠 유형</h3>
          <div className="content-type-grid">
            {contentTypes.map((type) => (
              <button
                key={type.id}
                className={`type-card ${contentType === type.id ? 'active' : ''}`}
                onClick={() => {
                  setContentType(type.id);
                  setGeneratedBlogPost(null);
                }}
              >
                <span className="type-icon">{type.icon}</span>
                <span className="type-label">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* AI 글 생성 전용 UI */}
        {contentType === 'ai' && (
          <AIContentGenerator />
        )}

        {/* 블로그 포스트 전용 UI */}
        {contentType === 'blog' && (
          <>
            <BlogPostForm
              onGenerate={handleGenerateBlogPost}
              isGenerating={isGenerating}
            />

            {generatedBlogPost && (
              <BlogPostResult
                result={generatedBlogPost}
                onEdit={handleEditBlogPost}
                onSave={handleSaveBlogPost}
              />
            )}
          </>
        )}

        {/* 다른 콘텐츠 타입 UI */}
        {contentType !== 'blog' && contentType !== 'ai' && contentType !== 'image-studio' && (
          <>
            <div className="creator-main">
              <div className="section">
                <h3>플랫폼 선택</h3>
                <select
                  className="platform-select"
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                >
                  {platforms[contentType]?.map((p) => (
                    <option key={p} value={p.toLowerCase()}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              <div className="section">
                <h3>제목</h3>
                <input
                  type="text"
                  className="title-input"
                  placeholder="콘텐츠 제목을 입력하세요"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="section">
                <div className="section-header">
                  <h3>내용</h3>
                  <button className="btn-ai" onClick={handleGenerate}>
                    ✨ AI로 생성하기
                  </button>
                </div>
                <textarea
                  className="content-textarea"
                  placeholder="콘텐츠 내용을 입력하거나 AI로 생성하세요..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={12}
                />
              </div>
            </div>

            <div className="creator-sidebar">
              <div className="preview-section">
                <h3>미리보기</h3>
                <div className="preview-box">
                  <div className="preview-platform">{platform}</div>
                  <div className="preview-content">
                    <h4>{title || '제목 미리보기'}</h4>
                    <p>{content || '내용이 여기에 표시됩니다...'}</p>
                  </div>
                </div>
              </div>

              <div className="tips-section">
                <h3>💡 작성 팁</h3>
                <ul className="tips-list">
                  <li>명확하고 간결한 제목을 사용하세요</li>
                  <li>타겟 고객을 고려한 톤을 유지하세요</li>
                  <li>행동 유도 문구(CTA)를 포함하세요</li>
                  <li>해시태그를 적절히 활용하세요</li>
                </ul>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ContentCreator;
