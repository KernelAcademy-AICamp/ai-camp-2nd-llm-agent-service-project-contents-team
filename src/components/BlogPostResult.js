import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import './BlogPostResult.css';

function BlogPostResult({ result, onEdit, onSave }) {
  // React Hooks는 조건문이나 early return 이전에 호출되어야 함
  const { title = '', content = '', tags = [], imageUrls = [] } = result || {};

  // useMemo로 치환된 content 메모이제이션
  const processedContent = useMemo(() => {
    if (!content) return '';

    console.log('=== BlogPostResult Processing Start ===');
    console.log('imageUrls:', imageUrls);
    console.log('imageUrls length:', imageUrls.length);
    console.log('original content:', content);

    // IMAGE_PLACEHOLDER_X를 실제 이미지 URL로 치환
    let processed = content;

    // 모든 placeholder 찾기
    const allPlaceholders = content.match(/IMAGE_PLACEHOLDER_\d+/g) || [];
    console.log('All placeholders found:', allPlaceholders);

    imageUrls.forEach((url, index) => {
      const placeholder = `IMAGE_PLACEHOLDER_${index}`;
      console.log(`\n[${index}] Replacing "${placeholder}" with "${url}"`);
      console.log(`[${index}] Before replace:`, processed.includes(placeholder));

      // 간단한 문자열 치환 사용
      processed = processed.split(placeholder).join(url);

      console.log(`[${index}] After replace:`, processed.includes(placeholder));
      console.log(`[${index}] Contains blob URL:`, processed.includes(url));
    });

    // 치환 후에도 남아있는 placeholder 확인
    const remainingPlaceholders = processed.match(/IMAGE_PLACEHOLDER_\d+/g);
    if (remainingPlaceholders && remainingPlaceholders.length > 0) {
      console.warn('WARNING: Unreplaced placeholders found:', remainingPlaceholders);
      console.warn('This will cause empty src attributes!');
    }

    console.log('\nFinal processed content:', processed);
    console.log('=== BlogPostResult Processing End ===\n');

    return processed;
  }, [content, imageUrls]);

  // Hooks 이후에 early return
  if (!result) return null;

  return (
    <div className="blog-post-result">
      <div className="result-header">
        <h2>생성된 블로그 포스트</h2>
        <div className="result-actions">
          <button className="btn-secondary" onClick={onEdit}>
            수정하기
          </button>
          <button className="btn-primary" onClick={onSave}>
            저장하기
          </button>
        </div>
      </div>

      <div className="result-content">
        <div className="result-section">
          <h3>제목</h3>
          <div className="title-display">{title}</div>
        </div>

        <div className="result-section">
          <h3>본문</h3>
          <div className="content-display">
            <ReactMarkdown
              urlTransform={(uri) => {
                console.log('🔗 URL Transform - Original URI:', uri);
                // blob URL을 포함한 모든 URL을 그대로 유지
                return uri;
              }}
              components={{
                img: ({node, ...props}) => {
                  console.log('🖼️ ReactMarkdown img component props:', props);
                  console.log('🖼️ img src value:', props.src);
                  console.log('🖼️ img alt value:', props.alt);

                  if (!props.src || props.src === '') {
                    console.error('❌ Empty src detected in img component!');
                    console.error('Full props:', props);
                  }

                  return (
                    <img
                      {...props}
                      style={{
                        maxWidth: '600px',
                        maxHeight: '400px',
                        width: 'auto',
                        height: 'auto',
                        objectFit: 'contain',
                        borderRadius: '8px',
                        margin: '20px 0',
                        display: 'block'
                      }}
                      onError={(e) => console.error('Image load error:', e.target.src)}
                      onLoad={() => console.log('✅ Image loaded successfully:', props.src)}
                    />
                  );
                }
              }}
            >
              {processedContent}
            </ReactMarkdown>
          </div>
        </div>

        <div className="result-section">
          <h3>태그</h3>
          <div className="tags-display">
            {tags.map((tag, index) => (
              <span key={index} className="tag">
                #{tag}
              </span>
            ))}
          </div>
        </div>

        <div className="result-info">
          <div className="info-item">
            <span className="info-label">글자 수:</span>
            <span className="info-value">{processedContent.length}자</span>
          </div>
          <div className="info-item">
            <span className="info-label">예상 읽기 시간:</span>
            <span className="info-value">{Math.ceil(processedContent.length / 500)}분</span>
          </div>
          {imageUrls.length > 0 && (
            <div className="info-item">
              <span className="info-label">이미지:</span>
              <span className="info-value">{imageUrls.length}개</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BlogPostResult;
