import { useState, useEffect } from 'react';
import { FiX, FiCheck, FiCreditCard, FiGift } from 'react-icons/fi';
import { creditsAPI } from '../../services/api';
import './CreditChargeModal.css';

function CreditChargeModal({ isOpen, onClose, onChargeComplete }) {
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [charging, setCharging] = useState(false);
  const [step, setStep] = useState('select'); // 'select', 'confirm', 'success'

  useEffect(() => {
    if (isOpen) {
      loadPackages();
      setStep('select');
      setSelectedPackage(null);
    }
  }, [isOpen]);

  const loadPackages = async () => {
    setLoading(true);
    try {
      const data = await creditsAPI.getPackages();
      setPackages(data);
    } catch (error) {
      console.error('패키지 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPackage = (pkg) => {
    setSelectedPackage(pkg);
  };

  const handleProceed = () => {
    if (selectedPackage) {
      setStep('confirm');
    }
  };

  const handleCharge = async () => {
    if (!selectedPackage || charging) return;

    setCharging(true);
    try {
      await creditsAPI.charge(selectedPackage.id);
      setStep('success');
      if (onChargeComplete) {
        onChargeComplete();
      }
    } catch (error) {
      console.error('충전 실패:', error);
      alert('충전 중 오류가 발생했습니다.');
    } finally {
      setCharging(false);
    }
  };

  const handleClose = () => {
    setStep('select');
    setSelectedPackage(null);
    onClose();
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  if (!isOpen) return null;

  return (
    <div className="credit-modal-overlay" onClick={handleClose}>
      <div className="credit-modal" onClick={(e) => e.stopPropagation()}>
        <button className="credit-modal-close" onClick={handleClose}>
          <FiX />
        </button>

        {step === 'select' && (
          <>
            <div className="credit-modal-header">
              <FiCreditCard className="credit-modal-icon" />
              <h2>크레딧 충전</h2>
              <p>AI 영상 생성에 필요한 크레딧을 충전하세요</p>
            </div>

            <div className="credit-packages">
              {loading ? (
                <div className="credit-packages-loading">패키지 로드 중...</div>
              ) : (
                packages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className={`credit-package-card ${selectedPackage?.id === pkg.id ? 'selected' : ''} ${pkg.is_popular ? 'popular' : ''}`}
                    onClick={() => handleSelectPackage(pkg)}
                  >
                    {pkg.badge && <span className="package-badge">{pkg.badge}</span>}
                    <div className="package-name">{pkg.name}</div>
                    <div className="package-credits">
                      <span className="credits-amount">{formatPrice(pkg.credits)}</span>
                      <span className="credits-label">크레딧</span>
                    </div>
                    {pkg.bonus_credits > 0 && (
                      <div className="package-bonus">
                        <FiGift /> +{formatPrice(pkg.bonus_credits)} 보너스
                      </div>
                    )}
                    <div className="package-total">
                      총 <strong>{formatPrice(pkg.total_credits)}</strong> 크레딧
                    </div>
                    <div className="package-price">
                      {formatPrice(pkg.price)}원
                    </div>
                    <div className="package-unit-price">
                      ({(pkg.price / pkg.total_credits).toFixed(1)}원/크레딧)
                    </div>
                    {selectedPackage?.id === pkg.id && (
                      <div className="package-selected-check">
                        <FiCheck />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="credit-modal-footer">
              <button
                className="btn-charge"
                onClick={handleProceed}
                disabled={!selectedPackage}
              >
                {selectedPackage
                  ? `${formatPrice(selectedPackage.price)}원 결제하기`
                  : '패키지를 선택하세요'}
              </button>
            </div>
          </>
        )}

        {step === 'confirm' && selectedPackage && (
          <>
            <div className="credit-modal-header">
              <FiCreditCard className="credit-modal-icon" />
              <h2>결제 확인</h2>
              <p>아래 내용을 확인해주세요</p>
            </div>

            <div className="credit-confirm-details">
              <div className="confirm-row">
                <span className="confirm-label">패키지</span>
                <span className="confirm-value">{selectedPackage.name}</span>
              </div>
              <div className="confirm-row">
                <span className="confirm-label">기본 크레딧</span>
                <span className="confirm-value">{formatPrice(selectedPackage.credits)}</span>
              </div>
              {selectedPackage.bonus_credits > 0 && (
                <div className="confirm-row bonus">
                  <span className="confirm-label">보너스 크레딧</span>
                  <span className="confirm-value">+{formatPrice(selectedPackage.bonus_credits)}</span>
                </div>
              )}
              <div className="confirm-row total">
                <span className="confirm-label">총 크레딧</span>
                <span className="confirm-value">{formatPrice(selectedPackage.total_credits)}</span>
              </div>
              <div className="confirm-divider"></div>
              <div className="confirm-row price">
                <span className="confirm-label">결제 금액</span>
                <span className="confirm-value">{formatPrice(selectedPackage.price)}원</span>
              </div>
            </div>

            <div className="credit-notice">
              <p>* 테스트 환경에서는 실제 결제 없이 크레딧이 충전됩니다.</p>
            </div>

            <div className="credit-modal-footer">
              <button className="btn-back" onClick={() => setStep('select')}>
                이전으로
              </button>
              <button
                className="btn-charge"
                onClick={handleCharge}
                disabled={charging}
              >
                {charging ? '충전 중...' : '충전하기'}
              </button>
            </div>
          </>
        )}

        {step === 'success' && selectedPackage && (
          <>
            <div className="credit-modal-header success">
              <div className="success-icon">
                <FiCheck />
              </div>
              <h2>충전 완료!</h2>
              <p>{formatPrice(selectedPackage.total_credits)} 크레딧이 충전되었습니다</p>
            </div>

            <div className="credit-success-message">
              <p>이제 AI 영상을 생성할 수 있습니다.</p>
            </div>

            <div className="credit-modal-footer">
              <button className="btn-charge" onClick={handleClose}>
                확인
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default CreditChargeModal;
