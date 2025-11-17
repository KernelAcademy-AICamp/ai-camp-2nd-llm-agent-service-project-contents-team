import React, { useState } from 'react';
import './BlogPostForm.css';

function BlogPostForm({ onGenerate, isGenerating }) {
  const [formData, setFormData] = useState({
    industry: '카페',
    location: '서울 강남구',
    purpose: '',
    customPurpose: '',
    targetAudience: [],
    keywords: [],
    tone: '',
  });

  const [customAudienceInput, setCustomAudienceInput] = useState('');
  const [showCustomAudienceInput, setShowCustomAudienceInput] = useState(false);

  const [keywordInput, setKeywordInput] = useState('');
  const [detailMode, setDetailMode] = useState('simple'); // 'simple' or 'detailed'
  const [simpleInput, setSimpleInput] = useState('');

  // 상세 입력 폼 데이터
  const [detailedFormData, setDetailedFormData] = useState({
    // 이벤트 공지
    eventName: '',
    discountTarget: '',
    discountRate: '',
    eventPeriodStart: '',
    eventPeriodEnd: '',
    additionalBenefit: '',
    participationCondition: '',
    eventEtc: '',

    // 신메뉴 공지
    menuName: '',
    menuPrice: '',
    releaseDate: '',
    menuDescription: '',
    menuFeatures: '',

    // 서비스 설명
    serviceName: '',
    serviceContent: '',
    usageMethod: '',
    servicePrice: '',
    serviceContact: '',

    // 정보 및 팁 공유
    infoTitle: '',
    infoContent: '',
    tip1: '',
    tip2: '',
    tip3: '',
    relatedProduct: '',

    // 기타
    customContent: '',
  });

  const purposeOptions = [
    { value: 'new_menu', label: '신메뉴 공지' },
    { value: 'event', label: '이벤트 공지' },
    { value: 'service', label: '서비스 설명' },
    { value: 'info_tips', label: '정보 및 팁 공유' },
    { value: 'custom', label: '기타' },
  ];

  const targetAudienceOptions = [
    { value: '직장인', label: '직장인' },
    { value: '대학생', label: '대학생' },
    { value: '주부', label: '주부' },
    { value: '시니어', label: '시니어' },
    { value: '청소년', label: '청소년' },
    { value: 'custom', label: '기타' },
  ];

  const handleAddAudience = (value) => {
    if (formData.targetAudience.length >= 5) {
      return;
    }

    if (value === 'custom') {
      // 기타 선택 시 입력 필드 토글
      setShowCustomAudienceInput(!showCustomAudienceInput);
      return;
    }

    if (!formData.targetAudience.includes(value)) {
      setFormData({
        ...formData,
        targetAudience: [...formData.targetAudience, value],
      });
    }
  };

  const handleAddCustomAudience = () => {
    if (customAudienceInput.trim() && formData.targetAudience.length < 5) {
      setFormData({
        ...formData,
        targetAudience: [...formData.targetAudience, customAudienceInput.trim()],
      });
      setCustomAudienceInput('');
    }
  };

  const handleRemoveAudience = (index) => {
    setFormData({
      ...formData,
      targetAudience: formData.targetAudience.filter((_, i) => i !== index),
    });
  };

  const toneOptions = [
    { value: 'friendly', label: '친근한' },
    { value: 'professional', label: '전문적인' },
    { value: 'humorous', label: '유머러스한' },
    { value: 'casual', label: '캐주얼한' },
    { value: 'formal', label: '격식있는' },
  ];

  const handleAddKeyword = () => {
    if (keywordInput.trim() && formData.keywords.length < 5) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput.trim()],
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (index) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((_, i) => i !== index),
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!formData.purpose || formData.targetAudience.length === 0 || !formData.tone || formData.keywords.length === 0) {
      alert('모든 필수 항목을 입력해주세요.');
      return;
    }

    if (formData.purpose === 'custom' && !formData.customPurpose.trim()) {
      alert('기타 주제를 입력해주세요.');
      return;
    }

    // 실제 전송할 데이터 준비
    const submitData = {
      ...formData,
      purpose: formData.purpose === 'custom' ? formData.customPurpose : formData.purpose,
      detailMode,
      simpleInput: detailMode === 'simple' ? simpleInput : null,
      detailedFormData: detailMode === 'detailed' ? detailedFormData : null,
    };

    console.log('Submitting data:', submitData);
    onGenerate(submitData);
  };

  return (
    <form className="blog-post-form" onSubmit={handleSubmit}>
      <div className="form-section">
        <h3>비즈니스 정보</h3>
        <div className="form-row">
          <div className="form-group">
            <label>업종</label>
            <input
              type="text"
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="예: 카페, 레스토랑, 미용실"
            />
          </div>
          <div className="form-group">
            <label>지역</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="예: 서울 강남구"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>글의 주제 *</h3>
        <div className="purpose-options">
          {purposeOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`option-btn ${formData.purpose === option.value ? 'active' : ''}`}
              onClick={() => setFormData({ ...formData, purpose: option.value })}
            >
              {option.label}
            </button>
          ))}
        </div>
        {formData.purpose === 'custom' && (
          <input
            type="text"
            className="custom-purpose-input"
            placeholder="주제를 입력하세요 (예: 매장 이전 안내, 채용 공고 등)"
            value={formData.customPurpose}
            onChange={(e) => setFormData({ ...formData, customPurpose: e.target.value })}
          />
        )}
      </div>

      {/* 상세 정보 입력 섹션 */}
      {formData.purpose && formData.purpose !== '' && (
        <div className="form-section detail-section">
          <div className="detail-header">
            <h3>상세 정보</h3>
            <div className="mode-toggle">
              <button
                type="button"
                className={`mode-btn ${detailMode === 'simple' ? 'active' : ''}`}
                onClick={() => setDetailMode('simple')}
              >
                📝 간편 입력 모드
              </button>
              <button
                type="button"
                className={`mode-btn ${detailMode === 'detailed' ? 'active' : ''}`}
                onClick={() => setDetailMode('detailed')}
              >
                📋 상세 입력 모드
              </button>
            </div>
          </div>

          {detailMode === 'simple' ? (
            <div className="simple-mode">
              <label className="input-label">내용을 자유롭게 작성해주세요:</label>
              <textarea
                className="simple-textarea"
                placeholder={
                  formData.purpose === 'event'
                    ? "예: 3월 한 달 아메리카노 20% 할인\n앱 다운로드 고객 대상\n3월 1일부터 31일까지"
                    : formData.purpose === 'new_menu'
                    ? "예: 딸기 라떼 신메뉴 출시\n가격 6,500원\n3월 1일 출시\n국내산 생딸기 100% 사용\n계절 한정 메뉴"
                    : formData.purpose === 'service'
                    ? "예: 단체 예약 서비스 시작\n10인 이상 예약 가능\n1인당 15,000원\n전화 또는 홈페이지에서 예약"
                    : formData.purpose === 'info_tips'
                    ? "예: 커피 맛있게 마시는 법\n- 신선한 원두 사용하기\n- 적정 온도(60-70도) 유지\n- 개인 취향에 맞게 농도 조절\n- 좋은 물 사용하기"
                    : "예: 매장 이전 안내\n새 주소: 서울시 강남구 테헤란로 123\n이전 일자: 3월 15일\n리뉴얼 오픈 할인 이벤트 진행"
                }
                value={simpleInput}
                onChange={(e) => setSimpleInput(e.target.value)}
                rows={4}
              />
            </div>
          ) : (
            <div className="detailed-mode">
              {/* 이벤트 공지 */}
              {formData.purpose === 'event' && (
                <div className="detailed-form">
                  <div className="form-group-required">
                    <h4>필수 정보</h4>
                    <div className="input-row">
                      <label>이벤트명 *</label>
                      <input
                        type="text"
                        placeholder="예: 봄맞이 할인 이벤트"
                        value={detailedFormData.eventName}
                        onChange={(e) => setDetailedFormData({...detailedFormData, eventName: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>할인 대상 *</label>
                      <input
                        type="text"
                        placeholder="예: 아메리카노, 라떼류 전체"
                        value={detailedFormData.discountTarget}
                        onChange={(e) => setDetailedFormData({...detailedFormData, discountTarget: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>할인율/가격 *</label>
                      <input
                        type="text"
                        placeholder="예: 20% 할인 / 2,000원 → 1,600원"
                        value={detailedFormData.discountRate}
                        onChange={(e) => setDetailedFormData({...detailedFormData, discountRate: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>기간 *</label>
                      <div className="date-range">
                        <input
                          type="date"
                          value={detailedFormData.eventPeriodStart}
                          onChange={(e) => setDetailedFormData({...detailedFormData, eventPeriodStart: e.target.value})}
                        />
                        <span>~</span>
                        <input
                          type="date"
                          value={detailedFormData.eventPeriodEnd}
                          onChange={(e) => setDetailedFormData({...detailedFormData, eventPeriodEnd: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="form-group-optional">
                    <h4>선택 정보</h4>
                    <div className="input-row">
                      <label>추가 혜택</label>
                      <input
                        type="text"
                        placeholder="예: 1+1, 포인트 적립"
                        value={detailedFormData.additionalBenefit}
                        onChange={(e) => setDetailedFormData({...detailedFormData, additionalBenefit: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>참여 조건</label>
                      <input
                        type="text"
                        placeholder="예: 앱 다운로드 고객 한정"
                        value={detailedFormData.participationCondition}
                        onChange={(e) => setDetailedFormData({...detailedFormData, participationCondition: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>기타 설명</label>
                      <textarea
                        placeholder="자유 입력"
                        value={detailedFormData.eventEtc}
                        onChange={(e) => setDetailedFormData({...detailedFormData, eventEtc: e.target.value})}
                        rows={3}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* 신메뉴 공지 */}
              {formData.purpose === 'new_menu' && (
                <div className="detailed-form">
                  <div className="form-group-required">
                    <h4>필수 정보</h4>
                    <div className="input-row">
                      <label>메뉴명 *</label>
                      <input
                        type="text"
                        placeholder="예: 딸기 라떼"
                        value={detailedFormData.menuName}
                        onChange={(e) => setDetailedFormData({...detailedFormData, menuName: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>가격 *</label>
                      <input
                        type="text"
                        placeholder="예: 6,500원"
                        value={detailedFormData.menuPrice}
                        onChange={(e) => setDetailedFormData({...detailedFormData, menuPrice: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>출시일 *</label>
                      <input
                        type="date"
                        value={detailedFormData.releaseDate}
                        onChange={(e) => setDetailedFormData({...detailedFormData, releaseDate: e.target.value})}
                      />
                    </div>
                  </div>

                  <div className="form-group-optional">
                    <h4>선택 정보</h4>
                    <div className="input-row">
                      <label>메뉴 설명</label>
                      <textarea
                        placeholder="예: 국내산 생딸기 100% 사용"
                        value={detailedFormData.menuDescription}
                        onChange={(e) => setDetailedFormData({...detailedFormData, menuDescription: e.target.value})}
                        rows={3}
                      />
                    </div>
                    <div className="input-row">
                      <label>특징/포인트</label>
                      <input
                        type="text"
                        placeholder="예: 계절 한정, 비건 가능"
                        value={detailedFormData.menuFeatures}
                        onChange={(e) => setDetailedFormData({...detailedFormData, menuFeatures: e.target.value})}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* 서비스 설명 */}
              {formData.purpose === 'service' && (
                <div className="detailed-form">
                  <div className="form-group-required">
                    <h4>필수 정보</h4>
                    <div className="input-row">
                      <label>서비스명 *</label>
                      <input
                        type="text"
                        placeholder="예: 단체 예약 서비스"
                        value={detailedFormData.serviceName}
                        onChange={(e) => setDetailedFormData({...detailedFormData, serviceName: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>주요 내용 * (3-5줄 권장)</label>
                      <textarea
                        placeholder="서비스에 대한 주요 내용을 작성해주세요"
                        value={detailedFormData.serviceContent}
                        onChange={(e) => setDetailedFormData({...detailedFormData, serviceContent: e.target.value})}
                        rows={5}
                      />
                    </div>
                  </div>

                  <div className="form-group-optional">
                    <h4>선택 정보</h4>
                    <div className="input-row">
                      <label>이용 방법</label>
                      <textarea
                        placeholder="서비스 이용 방법을 작성해주세요"
                        value={detailedFormData.usageMethod}
                        onChange={(e) => setDetailedFormData({...detailedFormData, usageMethod: e.target.value})}
                        rows={3}
                      />
                    </div>
                    <div className="input-row">
                      <label>가격/조건</label>
                      <input
                        type="text"
                        placeholder="예: 10인 이상, 1인당 15,000원"
                        value={detailedFormData.servicePrice}
                        onChange={(e) => setDetailedFormData({...detailedFormData, servicePrice: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>예약/문의</label>
                      <input
                        type="text"
                        placeholder="예: 02-1234-5678, 홈페이지 예약"
                        value={detailedFormData.serviceContact}
                        onChange={(e) => setDetailedFormData({...detailedFormData, serviceContact: e.target.value})}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* 정보 및 팁 공유 */}
              {formData.purpose === 'info_tips' && (
                <div className="detailed-form">
                  <div className="form-group-required">
                    <h4>필수 정보</h4>
                    <div className="input-row">
                      <label>제목 *</label>
                      <input
                        type="text"
                        placeholder="예: 커피 맛있게 마시는 법"
                        value={detailedFormData.infoTitle}
                        onChange={(e) => setDetailedFormData({...detailedFormData, infoTitle: e.target.value})}
                      />
                    </div>
                    <div className="input-row">
                      <label>주요 내용 *</label>
                      <textarea
                        placeholder="주요 내용을 자유롭게 작성하거나 아래 팁 항목을 사용하세요"
                        value={detailedFormData.infoContent}
                        onChange={(e) => setDetailedFormData({...detailedFormData, infoContent: e.target.value})}
                        rows={4}
                      />
                    </div>
                    <div className="tips-section">
                      <label>또는 팁 형식으로 작성:</label>
                      <input
                        type="text"
                        placeholder="팁 1"
                        value={detailedFormData.tip1}
                        onChange={(e) => setDetailedFormData({...detailedFormData, tip1: e.target.value})}
                      />
                      <input
                        type="text"
                        placeholder="팁 2"
                        value={detailedFormData.tip2}
                        onChange={(e) => setDetailedFormData({...detailedFormData, tip2: e.target.value})}
                      />
                      <input
                        type="text"
                        placeholder="팁 3"
                        value={detailedFormData.tip3}
                        onChange={(e) => setDetailedFormData({...detailedFormData, tip3: e.target.value})}
                      />
                    </div>
                  </div>

                  <div className="form-group-optional">
                    <h4>선택 정보</h4>
                    <div className="input-row">
                      <label>관련 상품/서비스</label>
                      <input
                        type="text"
                        placeholder="예: 에스프레소, 핸드드립"
                        value={detailedFormData.relatedProduct}
                        onChange={(e) => setDetailedFormData({...detailedFormData, relatedProduct: e.target.value})}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* 기타 */}
              {formData.purpose === 'custom' && (
                <div className="detailed-form">
                  <div className="form-group-required">
                    <h4>글의 핵심 내용</h4>
                    <div className="input-row">
                      <textarea
                        placeholder="자유롭게 작성해주세요 (제한 없음)"
                        value={detailedFormData.customContent}
                        onChange={(e) => setDetailedFormData({...detailedFormData, customContent: e.target.value})}
                        rows={8}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="form-section">
        <div className="section-title-with-hint">
          <h3>타겟 고객층 *</h3>
          <span className="hint-text">최소 1개 ~ 최대 5개</span>
        </div>
        <div className="audience-options">
          {targetAudienceOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`option-btn ${
                option.value !== 'custom' && formData.targetAudience.includes(option.value)
                  ? 'active'
                  : ''
              }`}
              onClick={() => handleAddAudience(option.value)}
              disabled={
                formData.targetAudience.length >= 5 &&
                (option.value === 'custom' || !formData.targetAudience.includes(option.value))
              }
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* 기타 입력 필드 - 기타 버튼 클릭 시에만 표시 */}
        {showCustomAudienceInput && (
          <div className="custom-audience-input-group">
            <input
              type="text"
              value={customAudienceInput}
              onChange={(e) => setCustomAudienceInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddCustomAudience();
                }
              }}
              placeholder="기타 타겟층 입력 (예: 매일매일이 피곤한 직장인)"
              disabled={formData.targetAudience.length >= 5}
            />
            <button
              type="button"
              onClick={handleAddCustomAudience}
              className="add-audience-btn"
              disabled={formData.targetAudience.length >= 5 || !customAudienceInput.trim()}
            >
              추가
            </button>
          </div>
        )}

        {/* 선택된 타겟층 표시 */}
        <div className="selected-audience-list">
          {formData.targetAudience.map((audience, index) => (
            <span key={index} className="audience-tag">
              {audience}
              <button
                type="button"
                onClick={() => handleRemoveAudience(index)}
                className="remove-audience"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="form-section">
        <div className="section-title-with-hint">
          <h3>핵심 키워드 *</h3>
          <span className="hint-text">최소 1개 ~ 최대 5개</span>
        </div>
        <div className="keyword-input-group">
          <input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddKeyword();
              }
            }}
            placeholder="키워드 입력 후 추가 버튼 클릭"
            disabled={formData.keywords.length >= 5}
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            className="add-keyword-btn"
            disabled={formData.keywords.length >= 5 || !keywordInput.trim()}
          >
            추가
          </button>
        </div>
        <p className="keyword-example">예시: 가성비, 프리미엄, 당일치기</p>
        <div className="keywords-list">
          {formData.keywords.map((keyword, index) => (
            <span key={index} className="keyword-tag">
              {keyword}
              <button
                type="button"
                onClick={() => handleRemoveKeyword(index)}
                className="remove-keyword"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="form-section">
        <h3>톤앤 매너 *</h3>
        <div className="tone-options">
          {toneOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`option-btn ${formData.tone === option.value ? 'active' : ''}`}
              onClick={() => setFormData({ ...formData, tone: option.value })}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <button type="submit" className="generate-btn" disabled={isGenerating}>
        {isGenerating ? '생성 중...' : '✨ AI로 블로그 포스트 생성하기'}
      </button>
    </form>
  );
}

export default BlogPostForm;
