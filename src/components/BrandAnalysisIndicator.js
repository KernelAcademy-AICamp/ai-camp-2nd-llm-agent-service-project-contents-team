import { useNavigate } from 'react-router-dom';
import { useBrandAnalysis } from '../contexts/BrandAnalysisContext';
import './BrandAnalysisIndicator.css';

/**
 * 백그라운드 브랜드 분석 진행 상황 표시 컴포넌트
 * - 오른쪽 상단에 플로팅 형태로 표시
 * - 분석 진행 상태 표시
 * - 완료 시 토스트 알림
 */
const BrandAnalysisIndicator = () => {
  const navigate = useNavigate();
  const {
    isAnalyzing,
    progress,
    step,
    notification,
    clearNotification,
  } = useBrandAnalysis();

  // 단계별 메시지
  const getStepMessage = (currentStep) => {
    const stepMessages = {
      'collecting': '콘텐츠 수집 중...',
      'analyzing': 'AI가 브랜드 특성을 분석 중...',
      'synthesizing': '브랜드 프로필 생성 중...',
      'completed': '분석 완료!',
    };
    return stepMessages[currentStep] || '분석 준비 중...';
  };

  // 완료 알림 토스트 닫기
  const handleCloseToast = () => {
    clearNotification();
  };

  // 설정 페이지로 이동
  const handleViewResult = () => {
    navigate('/settings');
    clearNotification();
  };

  return (
    <>
      {/* 진행 중인 분석 인디케이터 (오른쪽 상단) */}
      {isAnalyzing && (
        <div className="brand-analysis-indicator">
          <div className="brand-analysis-indicator__header">
            <span className="brand-analysis-indicator__icon">
              <span className="brand-analysis-indicator__spinner"></span>
            </span>
            <span className="brand-analysis-indicator__title">
              브랜드 분석 중
            </span>
          </div>

          <div className="brand-analysis-indicator__content">
            <div className="brand-analysis-indicator__message">
              {getStepMessage(step)}
            </div>

            <div className="brand-analysis-indicator__progress-bar">
              <div
                className="brand-analysis-indicator__progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="brand-analysis-indicator__status">
              <span>{progress}%</span>
            </div>
          </div>
        </div>
      )}

      {/* 완료/실패 토스트 알림 */}
      {notification && (
        <div className={`brand-analysis-toast ${notification.type === 'success' ? 'brand-analysis-toast--success' : 'brand-analysis-toast--failed'}`}>
          <div className="brand-analysis-toast__content">
            <span className="brand-analysis-toast__icon">
              {notification.type === 'success' ? '✅' : '❌'}
            </span>
            <div className="brand-analysis-toast__text">
              <strong>브랜드 분석</strong>
              <span>{notification.message}</span>
            </div>
          </div>

          <div className="brand-analysis-toast__actions">
            {notification.type === 'success' && (
              <button
                className="brand-analysis-toast__btn brand-analysis-toast__btn--primary"
                onClick={handleViewResult}
              >
                결과 보기
              </button>
            )}
            <button
              className="brand-analysis-toast__btn brand-analysis-toast__btn--close"
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

export default BrandAnalysisIndicator;
