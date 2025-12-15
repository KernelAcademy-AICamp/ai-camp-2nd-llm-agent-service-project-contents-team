import { useState, useEffect } from 'react';
import { FiCreditCard, FiPlus, FiMinus, FiGift, FiRefreshCw, FiFilter } from 'react-icons/fi';
import { creditsAPI } from '../../services/api';
import CreditChargeModal from '../../components/credits/CreditChargeModal';
import './CreditHistory.css';

function CreditHistory() {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, charge, use, bonus
  const [isChargeModalOpen, setIsChargeModalOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [balanceData, transactionsData] = await Promise.all([
        creditsAPI.getBalance(),
        creditsAPI.getTransactions(50, 0, filter === 'all' ? null : filter),
      ]);
      setBalance(balanceData.balance);
      setTransactions(transactionsData);
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChargeComplete = () => {
    loadData();
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'charge':
        return <FiPlus />;
      case 'use':
        return <FiMinus />;
      case 'bonus':
        return <FiGift />;
      case 'refund':
        return <FiRefreshCw />;
      default:
        return <FiCreditCard />;
    }
  };

  const getTransactionTypeLabel = (type) => {
    switch (type) {
      case 'charge':
        return '충전';
      case 'use':
        return '사용';
      case 'bonus':
        return '보너스';
      case 'refund':
        return '환불';
      default:
        return type;
    }
  };

  return (
    <div className="credit-history-page">
      {/* 헤더 */}
      <div className="page-header">
        <h2>크레딧 관리</h2>
        <p className="page-description">크레딧 잔액과 사용 내역을 확인하세요</p>
      </div>

      {/* 잔액 카드 */}
      <div className="credit-balance-card">
        <div className="balance-info">
          <div className="balance-label">보유 크레딧</div>
          <div className="balance-amount">
            <FiCreditCard className="balance-icon" />
            <span className="balance-number">{formatNumber(balance)}</span>
            <span className="balance-unit">크레딧</span>
          </div>
        </div>
        <button
          className="btn-charge-credits"
          onClick={() => setIsChargeModalOpen(true)}
        >
          <FiPlus />
          충전하기
        </button>
      </div>

      {/* 크레딧 비용 안내 */}
      <div className="credit-cost-info">
        <h3>크레딧 사용 안내</h3>
        <div className="cost-items">
          <div className="cost-item">
            <span className="cost-name">숏폼 영상 (15초)</span>
            <span className="cost-value">10 크레딧</span>
          </div>
          <div className="cost-item">
            <span className="cost-name">숏폼 영상 (30초)</span>
            <span className="cost-value">20 크레딧</span>
          </div>
          <div className="cost-item">
            <span className="cost-name">숏폼 영상 (60초)</span>
            <span className="cost-value">35 크레딧</span>
          </div>
          <div className="cost-item">
            <span className="cost-name">AI 이미지 (1장)</span>
            <span className="cost-value">2 크레딧</span>
          </div>
          <div className="cost-item">
            <span className="cost-name">카드뉴스</span>
            <span className="cost-value">5 크레딧</span>
          </div>
        </div>
      </div>

      {/* 거래 내역 */}
      <div className="transactions-section">
        <div className="transactions-header">
          <h3>거래 내역</h3>
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              전체
            </button>
            <button
              className={`filter-btn ${filter === 'charge' ? 'active' : ''}`}
              onClick={() => setFilter('charge')}
            >
              충전
            </button>
            <button
              className={`filter-btn ${filter === 'use' ? 'active' : ''}`}
              onClick={() => setFilter('use')}
            >
              사용
            </button>
            <button
              className={`filter-btn ${filter === 'bonus' ? 'active' : ''}`}
              onClick={() => setFilter('bonus')}
            >
              보너스
            </button>
          </div>
        </div>

        {loading ? (
          <div className="transactions-loading">로딩 중...</div>
        ) : transactions.length === 0 ? (
          <div className="transactions-empty">
            <FiCreditCard className="empty-icon" />
            <p>거래 내역이 없습니다</p>
          </div>
        ) : (
          <div className="transactions-list">
            {transactions.map((tx) => (
              <div key={tx.id} className={`transaction-item ${tx.type}`}>
                <div className={`transaction-icon ${tx.type}`}>
                  {getTransactionIcon(tx.type)}
                </div>
                <div className="transaction-info">
                  <div className="transaction-description">{tx.description}</div>
                  <div className="transaction-date">{formatDate(tx.created_at)}</div>
                </div>
                <div className="transaction-amount-wrapper">
                  <div className={`transaction-amount ${tx.amount >= 0 ? 'positive' : 'negative'}`}>
                    {tx.amount >= 0 ? '+' : ''}{formatNumber(tx.amount)}
                  </div>
                  <div className="transaction-balance">
                    잔액 {formatNumber(tx.balance_after)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 충전 모달 */}
      <CreditChargeModal
        isOpen={isChargeModalOpen}
        onClose={() => setIsChargeModalOpen(false)}
        onChargeComplete={handleChargeComplete}
      />
    </div>
  );
}

export default CreditHistory;
