import { useNavigate } from 'react-router-dom';
import { useVideoJob } from '../contexts/VideoJobContext';
import './VideoJobIndicator.css';

/**
 * 백그라운드 영상 생성 작업 진행 상황 표시 컴포넌트
 * - 오른쪽 상단에 플로팅 형태로 표시
 * - 진행률 바와 현재 단계 표시
 * - 완료 시 토스트 알림
 */
const VideoJobIndicator = () => {
  const navigate = useNavigate();
  const {
    activeJobCount,
    firstActiveJob,
    completedJob,
    clearCompletedNotification,
  } = useVideoJob();

  // 완료 알림 토스트 닫기
  const handleCloseToast = () => {
    clearCompletedNotification();
  };

  // 완료된 영상 보기
  const handleViewResult = () => {
    if (completedJob && !completedJob.failed) {
      navigate('/history');
    }
    clearCompletedNotification();
  };

  // 상태별 한글 텍스트
  const getStatusText = (status) => {
    const statusMap = {
      'pending': '대기 중...',
      'analyzing_product': '제품 분석 중...',
      'planning_story': '스토리 기획 중...',
      'designing_scenes': '장면 설계 중...',
      'validating_quality': '품질 검증 중...',
      'generating_storyboard': '스토리보드 생성 중...',
      'generating_images': '이미지 생성 중...',
      'generating_videos': '영상 생성 중...',
      'composing_video': '영상 합성 중...',
    };
    return statusMap[status] || status;
  };

  return (
    <>
      {/* 진행 중인 작업 인디케이터 (오른쪽 상단) */}
      {activeJobCount > 0 && firstActiveJob && (
        <div className="video-job-indicator">
          <div className="video-job-indicator__header">
            <span className="video-job-indicator__icon">🎬</span>
            <span className="video-job-indicator__title">
              영상 생성 중
              {activeJobCount > 1 && ` (${activeJobCount}개)`}
            </span>
          </div>

          <div className="video-job-indicator__content">
            <div className="video-job-indicator__product-name">
              {firstActiveJob.productName}
            </div>

            <div className="video-job-indicator__progress-bar">
              <div
                className="video-job-indicator__progress-fill"
                style={{ width: `${firstActiveJob.progress || 5}%` }}
              />
            </div>

            <div className="video-job-indicator__status">
              {getStatusText(firstActiveJob.status)}
              <span className="video-job-indicator__percentage">
                {firstActiveJob.progress || 5}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 완료/실패 토스트 알림 */}
      {completedJob && (
        <div className={`video-job-toast ${completedJob.failed ? 'video-job-toast--failed' : 'video-job-toast--success'}`}>
          <div className="video-job-toast__content">
            <span className="video-job-toast__icon">
              {completedJob.failed ? '❌' : '✅'}
            </span>
            <div className="video-job-toast__text">
              <strong>{completedJob.productName}</strong>
              <span>
                {completedJob.failed
                  ? `영상 생성 실패: ${completedJob.error || '알 수 없는 오류'}`
                  : '영상 생성이 완료되었습니다!'
                }
              </span>
            </div>
          </div>

          <div className="video-job-toast__actions">
            {!completedJob.failed && (
              <button
                className="video-job-toast__btn video-job-toast__btn--primary"
                onClick={handleViewResult}
              >
                결과 보기
              </button>
            )}
            <button
              className="video-job-toast__btn video-job-toast__btn--close"
              onClick={handleCloseToast}
            >
              닫기
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default VideoJobIndicator;
