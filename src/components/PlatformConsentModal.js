import React, { useState } from 'react';
import './PlatformConsentModal.css';

/**
 * 플랫폼별 분석 동의 모달
 *
 * @param {boolean} isOpen - 모달 표시 여부
 * @param {function} onClose - 모달 닫기 핸들러
 * @param {function} onAccept - 동의 완료 핸들러
 * @param {string} platform - 플랫폼 타입 ('youtube', 'instagram', 'threads')
 * @param {string} platformUrl - 플랫폼 URL 또는 계정명
 */
const PlatformConsentModal = ({ isOpen, onClose, onAccept, platform, platformUrl }) => {
  const [consents, setConsents] = useState({
    // 공통 항목
    analysis_consent: false,
    data_usage: false,
    no_original_storage: false,

    // 선택 항목
    content_improvement: false
  });

  // 플랫폼별 표시명
  const platformNames = {
    youtube: 'YouTube',
    instagram: 'Instagram',
    threads: 'Threads'
  };

  // 필수 동의 항목 (모든 플랫폼 공통)
  const requiredConsents = ['analysis_consent', 'data_usage', 'no_original_storage'];
  const allRequiredAccepted = requiredConsents.every(key => consents[key]);
  const allAccepted = Object.values(consents).every(v => v);

  const handleCheckboxChange = (id, checked) => {
    setConsents(prev => ({ ...prev, [id]: checked }));
  };

  const handleAcceptRequired = () => {
    if (allRequiredAccepted) {
      onAccept(consents);
      onClose();
    }
  };

  const handleAcceptAll = () => {
    const allTrue = {};
    Object.keys(consents).forEach(key => allTrue[key] = true);
    setConsents(allTrue);
    onAccept(allTrue);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="consent-modal-overlay" onClick={onClose}>
      <div className="consent-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* 헤더 */}
        <div className="consent-modal-header">
          <h2>📝 {platformUrl} 분석 동의</h2>
          <button className="consent-modal-close" onClick={onClose}>×</button>
        </div>

        {/* 바디 */}
        <div className="consent-modal-body">
          {/* 안내 메시지 */}
          <div className="consent-alert-box">
            <p>
              브랜드 분석을 위해 <strong>{platformUrl}</strong>의 콘텐츠를 수집합니다.
            </p>
            <p>아래 내용을 확인하고 동의해주세요.</p>
          </div>

          {/* AI 분석 및 데이터 사용 */}
          <div className="consent-section">
            <h3 className="consent-section-title">
              <span className="section-icon">🤖</span>
              AI 분석 및 데이터 사용
            </h3>

            <div className="consent-item">
              <label className="consent-checkbox-label">
                <input
                  type="checkbox"
                  checked={consents.analysis_consent}
                  onChange={(e) => handleCheckboxChange('analysis_consent', e.target.checked)}
                />
                <span className="consent-item-icon">🤖</span>
                <div className="consent-item-content">
                  <div className="consent-item-text">
                    <span className="required-badge">필수</span>
                    {platform === 'youtube' && 'YouTube '}
                    {platform === 'instagram' && 'Instagram '}
                    {platform === 'threads' && 'Threads '}
                    콘텐츠를 AI가 분석하여 브랜드 프로필을 생성하는 것에 동의합니다.
                  </div>
                  <div className="consent-item-description">
                    {platform === 'youtube' && '채널 정보 및 최근 동영상을 분석하여 브랜드 어조, 주제, 타겟 고객 등을 파악합니다.'}
                    {platform === 'instagram' && '프로필 및 최근 포스트를 분석하여 브랜드 어조, 비주얼 스타일, 타겟 고객 등을 파악합니다.'}
                    {platform === 'threads' && '프로필 및 최근 포스트를 분석하여 브랜드 어조, 주제, 타겟 고객 등을 파악합니다.'}
                  </div>
                </div>
              </label>
            </div>

            <div className="consent-item">
              <label className="consent-checkbox-label">
                <input
                  type="checkbox"
                  checked={consents.data_usage}
                  onChange={(e) => handleCheckboxChange('data_usage', e.target.checked)}
                />
                <span className="consent-item-icon">🎯</span>
                <div className="consent-item-content">
                  <div className="consent-item-text">
                    <span className="required-badge">필수</span>
                    분석 결과는 콘텐츠 생성 서비스 제공 목적으로만 사용됩니다.
                  </div>
                  <div className="consent-item-description">
                    제3자에게 공유되지 않으며, 마케팅 목적으로 사용되지 않습니다.
                  </div>
                </div>
              </label>
            </div>

            <div className="consent-item">
              <label className="consent-checkbox-label">
                <input
                  type="checkbox"
                  checked={consents.no_original_storage}
                  onChange={(e) => handleCheckboxChange('no_original_storage', e.target.checked)}
                />
                <span className="consent-item-icon">🗄️</span>
                <div className="consent-item-content">
                  <div className="consent-item-text">
                    <span className="required-badge">필수</span>
                    원본 콘텐츠는 서버에 영구 저장되지 않습니다.
                  </div>
                  <div className="consent-item-description">
                    분석 과정에서만 일시적으로 사용되며, 분석 결과(브랜드 프로필, 키워드 등)만 저장됩니다.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* 선택 섹션 */}
          <div className="consent-section consent-section-optional">
            <h3 className="consent-section-title">
              <span className="section-icon">📊</span>
              서비스 개선 (선택)
            </h3>

            <div className="consent-item">
              <label className="consent-checkbox-label">
                <input
                  type="checkbox"
                  checked={consents.content_improvement}
                  onChange={(e) => handleCheckboxChange('content_improvement', e.target.checked)}
                />
                <span className="consent-item-icon">📊</span>
                <div className="consent-item-content">
                  <div className="consent-item-text">
                    <span className="optional-badge">선택</span>
                    AI 모델 개선을 위해 익명화된 분석 데이터를 활용하는 것에 동의합니다.
                  </div>
                  <div className="consent-item-description">
                    개인 식별 정보는 제거되며, 서비스 품질 향상 목적으로만 사용됩니다.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* 사용자 권리 안내 */}
          <div className="consent-user-rights">
            <h4 className="user-rights-title">💡 귀하의 권리</h4>
            <div className="user-rights-list">
              <div className="user-right-item">
                <span className="user-right-icon">✅</span>
                <div className="user-right-content">
                  <div className="user-right-title">언제든지 삭제 가능</div>
                  <div className="user-right-description">
                    분석 결과 및 브랜드 프로필을 언제든지 삭제할 수 있습니다.
                  </div>
                </div>
              </div>
              <div className="user-right-item">
                <span className="user-right-icon">✅</span>
                <div className="user-right-content">
                  <div className="user-right-title">SNS 연결 해제</div>
                  <div className="user-right-description">
                    마이페이지에서 연결된 SNS를 언제든지 해제할 수 있습니다.
                  </div>
                </div>
              </div>
              <div className="user-right-item">
                <span className="user-right-icon">✅</span>
                <div className="user-right-content">
                  <div className="user-right-title">데이터 열람 권한</div>
                  <div className="user-right-description">
                    저장된 브랜드 프로필 및 분석 결과를 언제든지 확인할 수 있습니다.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 푸터 */}
        <div className="consent-modal-footer">
          <button className="consent-btn consent-btn-cancel" onClick={onClose}>
            취소
          </button>
          <button
            className="consent-btn consent-btn-required"
            onClick={handleAcceptRequired}
            disabled={!allRequiredAccepted}
          >
            필수 항목만 동의하고 계속하기
          </button>
          <button
            className="consent-btn consent-btn-all"
            onClick={handleAcceptAll}
          >
            모두 동의하고 계속하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlatformConsentModal;
