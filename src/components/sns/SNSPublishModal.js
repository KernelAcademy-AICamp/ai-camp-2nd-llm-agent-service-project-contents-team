import { useState, useEffect } from 'react';
import './SNSPublishModal.css';

function SNSPublishModal({ isOpen, onClose, content }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState({
    instagram: false,
    facebook: false
  });
  const [instagramCaption, setInstagramCaption] = useState('');
  const [facebookPost, setFacebookPost] = useState('');
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishResults, setPublishResults] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState({
    instagram: { connected: false },
    facebook: { connected: false }
  });

  // 콘텐츠가 변경되면 초기값 설정
  useEffect(() => {
    if (content) {
      setInstagramCaption(content.instagramCaption || '');
      setFacebookPost(content.facebookPost || '');
    }
  }, [content]);

  // 연동 상태 확인
  useEffect(() => {
    if (isOpen) {
      checkConnectionStatus();
    }
  }, [isOpen]);

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sns/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setConnectionStatus(data);
      }
    } catch (error) {
      console.error('Failed to check connection status:', error);
    }
  };

  const handlePlatformToggle = (platform) => {
    setSelectedPlatforms(prev => ({
      ...prev,
      [platform]: !prev[platform]
    }));
  };

  const handlePublish = async () => {
    if (!selectedPlatforms.instagram && !selectedPlatforms.facebook) {
      alert('발행할 플랫폼을 선택해주세요.');
      return;
    }

    setIsPublishing(true);
    setPublishResults(null);

    try {
      const response = await fetch('http://localhost:8000/api/sns/publish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          platforms: selectedPlatforms,
          content: {
            type: content?.type || 'text',
            instagramCaption: instagramCaption,
            facebookPost: facebookPost,
            hashtags: content?.hashtags || [],
            images: content?.images || []
          }
        })
      });

      const result = await response.json();

      if (response.ok) {
        setPublishResults(result);
        // 발행 성공 시 DB 저장은 백엔드에서 자동 처리됨
      } else {
        throw new Error(result.detail || '발행에 실패했습니다.');
      }
    } catch (error) {
      console.error('Publish error:', error);
      setPublishResults({
        success: false,
        error: error.message
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleClose = () => {
    setPublishResults(null);
    setSelectedPlatforms({ instagram: false, facebook: false });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="sns-modal-overlay" onClick={handleClose}>
      <div className="sns-modal-content" onClick={e => e.stopPropagation()}>
        <div className="sns-modal-header">
          <h2>SNS 발행</h2>
          <button className="sns-modal-close" onClick={handleClose}>&times;</button>
        </div>

        <div className="sns-modal-body">
          {/* 플랫폼 선택 */}
          <div className="platform-selection">
            <h3>발행할 플랫폼 선택</h3>
            <div className="platform-options">
              <label className={`platform-option ${!connectionStatus.instagram?.connected ? 'disabled' : ''}`}>
                <input
                  type="checkbox"
                  checked={selectedPlatforms.instagram}
                  onChange={() => handlePlatformToggle('instagram')}
                  disabled={!connectionStatus.instagram?.connected}
                />
                <span className="platform-icon">📷</span>
                <span className="platform-name">Instagram</span>
                {!connectionStatus.instagram?.connected && (
                  <span className="platform-status">연동 필요</span>
                )}
              </label>
              <label className={`platform-option ${!connectionStatus.facebook?.connected ? 'disabled' : ''}`}>
                <input
                  type="checkbox"
                  checked={selectedPlatforms.facebook}
                  onChange={() => handlePlatformToggle('facebook')}
                  disabled={!connectionStatus.facebook?.connected}
                />
                <span className="platform-icon">📘</span>
                <span className="platform-name">Facebook</span>
                {!connectionStatus.facebook?.connected && (
                  <span className="platform-status">
                    <a href="/facebook" style={{color: '#3b82f6', textDecoration: 'underline'}}>
                      페이지 연동 필요
                    </a>
                  </span>
                )}
              </label>
            </div>
          </div>

          {/* Instagram 콘텐츠 편집 */}
          {selectedPlatforms.instagram && (
            <div className="content-editor">
              <h3>Instagram 캡션</h3>
              <textarea
                value={instagramCaption}
                onChange={(e) => setInstagramCaption(e.target.value)}
                placeholder="Instagram 캡션을 입력하세요..."
                rows={5}
              />
              <div className="char-count">{instagramCaption.length} / 2,200자</div>
            </div>
          )}

          {/* Facebook 콘텐츠 편집 */}
          {selectedPlatforms.facebook && (
            <div className="content-editor">
              <h3>Facebook 게시글</h3>
              <textarea
                value={facebookPost}
                onChange={(e) => setFacebookPost(e.target.value)}
                placeholder="Facebook 게시글을 입력하세요..."
                rows={5}
              />
            </div>
          )}

          {/* 이미지 미리보기 */}
          {content?.images && content.images.length > 0 && (
            <div className="image-preview-section">
              <h3>첨부 이미지</h3>
              <div className="image-preview-grid">
                {content.images.map((img, idx) => (
                  <div key={idx} className="image-preview-item">
                    <img src={img} alt={`Preview ${idx + 1}`} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 발행 결과 */}
          {publishResults && (
            <div className={`publish-results ${publishResults.success ? 'success' : 'error'}`}>
              {publishResults.success ? (
                <>
                  <div className="result-icon">✅</div>
                  <div className="result-message">발행이 완료되었습니다!</div>
                  {publishResults.instagram && (
                    <div className="result-detail">
                      Instagram: {publishResults.instagram.success ? '성공' : publishResults.instagram.error}
                    </div>
                  )}
                  {publishResults.facebook && (
                    <div className="result-detail">
                      Facebook: {publishResults.facebook.success ? '성공' : publishResults.facebook.error}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="result-icon">❌</div>
                  <div className="result-message">발행에 실패했습니다.</div>
                  <div className="result-detail">{publishResults.error}</div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="sns-modal-footer">
          <button className="btn-cancel" onClick={handleClose}>
            취소
          </button>
          <button
            className="btn-publish"
            onClick={handlePublish}
            disabled={isPublishing || (!selectedPlatforms.instagram && !selectedPlatforms.facebook)}
          >
            {isPublishing ? '발행 중...' : '발행하기'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SNSPublishModal;
