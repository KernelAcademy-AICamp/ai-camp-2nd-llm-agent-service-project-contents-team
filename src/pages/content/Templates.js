import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { templatesAPI } from '../../services/api';
import './Templates.css';

function Templates() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('all');
  const [templates, setTemplates] = useState([]);
  const [tabs, setTabs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showTabModal, setShowTabModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [editingTab, setEditingTab] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    tab_id: '',
    category: '',
    prompt: '',
    description: '',
    icon: '📝'
  });
  const [tabFormData, setTabFormData] = useState({
    label: '',
    icon: '📁'
  });

  // 탭 아이콘 옵션
  const tabIconOptions = [
    '🎯', '💎', '🌟', '🔥', '💫', '✨', '🎁', '💝',
    '🎉', '🎊', '🎈', '🗓️', '🎪', '🏆', '🎗️',
    '🍽️', '☕', '🍰', '🥗', '🍜', '🍕', '🍷', '🌮',
    '💡', '📚', '📖', '🔍', '💬', '📢', '📋', '🎓',
    '📝', '✅', '🔧', '📐', '🛠️', '📌', '💪', '📁',
    '🛒', '💼', '🎨', '🎵', '📷', '🎬', '✈️', '🏠'
  ];

  // 데이터 로드
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [tabsData, templatesData] = await Promise.all([
        templatesAPI.getTabs(),
        templatesAPI.getTemplates()
      ]);
      setTabs(tabsData);
      setTemplates(templatesData);
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 필터링된 템플릿
  const filteredTemplates = templates.filter(t =>
    activeTab === 'all' || t.tab_id === parseInt(activeTab)
  );

  // 탭별 카운트
  const getTabCount = (tabId) => {
    if (tabId === 'all') return templates.length;
    return templates.filter(t => t.tab_id === parseInt(tabId)).length;
  };

  // ========== 탭 모달 관련 ==========
  const openNewTabModal = () => {
    setEditingTab(null);
    setTabFormData({ label: '', icon: '📁' });
    setShowTabModal(true);
  };

  const openEditTabModal = (tab, e) => {
    e.stopPropagation();
    setEditingTab(tab);
    setTabFormData({ label: tab.label, icon: tab.icon });
    setShowTabModal(true);
  };

  const handleTabFormChange = (e) => {
    const { name, value } = e.target;
    setTabFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveTab = async () => {
    if (!tabFormData.label.trim()) {
      alert('탭 이름을 입력해주세요.');
      return;
    }

    try {
      if (editingTab) {
        await templatesAPI.updateTab(editingTab.id, tabFormData);
      } else {
        await templatesAPI.createTab(tabFormData);
      }
      await loadData();
      setShowTabModal(false);
    } catch (error) {
      console.error('탭 저장 실패:', error);
      alert('탭 저장에 실패했습니다.');
    }
  };

  const handleDeleteTab = async (tab, e) => {
    e.stopPropagation();
    const tabTemplates = templates.filter(t => t.tab_id === tab.id);
    const confirmMsg = tabTemplates.length > 0
      ? `이 탭에 ${tabTemplates.length}개의 템플릿이 있습니다. 탭을 삭제하면 해당 템플릿도 함께 삭제됩니다. 계속하시겠습니까?`
      : '이 탭을 삭제하시겠습니까?';

    if (window.confirm(confirmMsg)) {
      try {
        await templatesAPI.deleteTab(tab.id);
        if (activeTab === String(tab.id)) setActiveTab('all');
        await loadData();
      } catch (error) {
        console.error('탭 삭제 실패:', error);
        alert('탭 삭제에 실패했습니다.');
      }
    }
  };

  // ========== 템플릿 모달 관련 ==========
  const openNewModal = () => {
    setEditingTemplate(null);
    const defaultTabId = activeTab === 'all' ? (tabs[0]?.id || '') : activeTab;
    setFormData({
      name: '',
      tab_id: defaultTabId,
      category: '',
      prompt: '',
      description: '',
      icon: '📝'
    });
    setShowModal(true);
  };

  const openEditModal = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      tab_id: template.tab_id,
      category: template.category || '',
      prompt: template.prompt,
      description: template.description || '',
      icon: template.icon
    });
    setShowModal(true);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
      ...(name === 'tab_id' && { category: '' })
    }));
  };

  const handleSaveTemplate = async () => {
    if (!formData.name.trim() || !formData.prompt.trim()) {
      alert('템플릿 이름과 프롬프트는 필수입니다.');
      return;
    }

    try {
      const data = {
        ...formData,
        tab_id: parseInt(formData.tab_id)
      };

      if (editingTemplate) {
        await templatesAPI.updateTemplate(editingTemplate.id, data);
      } else {
        await templatesAPI.createTemplate(data);
      }
      await loadData();
      setShowModal(false);
    } catch (error) {
      console.error('템플릿 저장 실패:', error);
      alert('템플릿 저장에 실패했습니다.');
    }
  };

  const handleDeleteTemplate = async (id) => {
    if (window.confirm('이 템플릿을 삭제하시겠습니까?')) {
      try {
        await templatesAPI.deleteTemplate(id);
        await loadData();
      } catch (error) {
        console.error('템플릿 삭제 실패:', error);
        alert('템플릿 삭제에 실패했습니다.');
      }
    }
  };

  const handleUseTemplate = async (template) => {
    try {
      await templatesAPI.useTemplate(template.id);
    } catch (error) {
      console.error('템플릿 사용 기록 실패:', error);
    }
    // /create 페이지로 템플릿 데이터 전달
    const tab = tabs.find(t => t.id === template.tab_id);
    navigate('/create', {
      state: {
        template: template,
        purpose: tab?.tab_key || 'promotion',
        fromTemplate: true
      }
    });
  };

  const handleDuplicateTemplate = async (template) => {
    try {
      await templatesAPI.duplicateTemplate(template.id);
      await loadData();
    } catch (error) {
      console.error('템플릿 복제 실패:', error);
      alert('템플릿 복제에 실패했습니다.');
    }
  };

  // 탭 라벨/아이콘 가져오기
  const getTabInfo = (tabId) => {
    const tab = tabs.find(t => t.id === tabId);
    return tab || { label: '미분류', icon: '📁' };
  };

  if (loading) {
    return (
      <div className="templates-page">
        <div className="templates-loading">
          <div className="templates-spinner"></div>
          <p>템플릿을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="templates-page">
      <div className="templates-header">
        <div className="header-left">
          <h2>템플릿 갤러리</h2>
          <p className="header-subtitle">자주 사용하는 프롬프트를 템플릿으로 저장하고 재사용하세요</p>
        </div>
        <div className="header-actions">
          <button className="btn-primary" onClick={openNewModal}>
            + 새 템플릿
          </button>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="templates-tabs">
        <button
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          전체 <span className="tab-count">{getTabCount('all')}</span>
        </button>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === String(tab.id) ? 'active' : ''}`}
            onClick={() => setActiveTab(String(tab.id))}
          >
            {tab.icon} {tab.label} <span className="tab-count">{getTabCount(tab.id)}</span>
          </button>
        ))}
        {/* 탭 추가 버튼 */}
        <button
          className="tab-btn tab-add-btn"
          onClick={openNewTabModal}
          title="새 탭 추가"
        >
          +
        </button>
      </div>

      {/* 탭 콘텐츠 헤더 (선택된 탭 정보 + 편집/삭제 버튼) */}
      {activeTab !== 'all' && (
        <div className="tab-content-header">
          <div className="tab-content-info">
            {(() => {
              const currentTab = tabs.find(t => String(t.id) === activeTab);
              return currentTab ? (
                <>
                  <span className="tab-content-icon">{currentTab.icon}</span>
                  <span className="tab-content-label">{currentTab.label}</span>
                  <span className="tab-content-count">{getTabCount(currentTab.id)}개 템플릿</span>
                </>
              ) : null;
            })()}
          </div>
          <div className="tab-content-actions">
            <button
              className="btn-tab-action"
              onClick={(e) => {
                const currentTab = tabs.find(t => String(t.id) === activeTab);
                if (currentTab) openEditTabModal(currentTab, e);
              }}
              title="탭 수정"
            >
              ✏️ 탭 수정
            </button>
            <button
              className="btn-tab-action delete"
              onClick={(e) => {
                const currentTab = tabs.find(t => String(t.id) === activeTab);
                if (currentTab) handleDeleteTab(currentTab, e);
              }}
              title="탭 삭제"
            >
              🗑️ 탭 삭제
            </button>
          </div>
        </div>
      )}

      {/* 템플릿 그리드 */}
      {filteredTemplates.length === 0 ? (
        <div className="templates-empty">
          <div className="empty-icon">📝</div>
          <h3>템플릿이 없습니다</h3>
          <p>새 템플릿을 만들어 자주 사용하는 프롬프트를 저장하세요</p>
          <button className="btn-primary" onClick={openNewModal}>
            + 첫 템플릿 만들기
          </button>
        </div>
      ) : (
        <div className="templates-grid">
          {filteredTemplates.map((template) => {
            const tabInfo = getTabInfo(template.tab_id);
            return (
              <div key={template.id} className="template-card">
                <div className="template-header">
                  <h3>{template.name}</h3>
                  <div className="template-type-badge">
                    {tabInfo.icon} {tabInfo.label}
                  </div>
                </div>
                {template.category && (
                  <p className="template-category">{template.category}</p>
                )}
                {template.description && (
                  <p className="template-description">{template.description}</p>
                )}
                <div className="template-prompt-preview">
                  <code>{template.prompt.substring(0, 80)}...</code>
                </div>
                <div className="template-footer">
                  <span className="template-uses">{template.uses || 0}회 사용</span>
                  <div className="template-actions">
                    <button
                      className="btn-action"
                      title="복제"
                      onClick={(e) => { e.stopPropagation(); handleDuplicateTemplate(template); }}
                    >
                      📋
                    </button>
                    <button
                      className="btn-action"
                      title="수정"
                      onClick={(e) => { e.stopPropagation(); openEditModal(template); }}
                    >
                      ✏️
                    </button>
                    <button
                      className="btn-action delete"
                      title="삭제"
                      onClick={(e) => { e.stopPropagation(); handleDeleteTemplate(template.id); }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                <button
                  className="btn-use-template"
                  onClick={() => handleUseTemplate(template)}
                >
                  이 템플릿 사용하기
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* 탭 생성/수정 모달 */}
      {showTabModal && (
        <div className="modal-overlay" onClick={() => setShowTabModal(false)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingTab ? '탭 수정' : '새 탭 만들기'}</h3>
              <button className="modal-close" onClick={() => setShowTabModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>탭 이름 *</label>
                <input
                  type="text"
                  name="label"
                  value={tabFormData.label}
                  onChange={handleTabFormChange}
                  placeholder="예: 공지사항"
                />
              </div>

              <div className="form-group">
                <label>아이콘</label>
                <div className="icon-selector">
                  {tabIconOptions.map(icon => (
                    <button
                      key={icon}
                      type="button"
                      className={`icon-btn ${tabFormData.icon === icon ? 'active' : ''}`}
                      onClick={() => setTabFormData(prev => ({ ...prev, icon }))}
                    >
                      {icon}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowTabModal(false)}>
                취소
              </button>
              <button className="btn-primary" onClick={handleSaveTab}>
                {editingTab ? '수정 완료' : '탭 추가'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 템플릿 생성/수정 모달 */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingTemplate ? '템플릿 수정' : '새 템플릿 만들기'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>분류 탭</label>
                <select
                  name="tab_id"
                  value={formData.tab_id}
                  onChange={handleInputChange}
                >
                  <option value="">선택하세요</option>
                  {tabs.map(tab => (
                    <option key={tab.id} value={tab.id}>{tab.icon} {tab.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>템플릿 이름 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="예: 신제품 출시 홍보"
                />
              </div>

              <div className="form-group">
                <label>세부 카테고리</label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  placeholder="예: 신제품 출시"
                />
              </div>

              <div className="form-group">
                <label>간단한 설명</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="예: AIDA 구조의 신제품 출시 홍보"
                />
              </div>

              <div className="form-group">
                <label>프롬프트 *</label>
                <textarea
                  name="prompt"
                  value={formData.prompt}
                  onChange={handleInputChange}
                  placeholder="프롬프트 내용을 입력하세요...&#10;&#10;예: 제품명: {product}&#10;핵심 특징: {features}&#10;&#10;위 제품을 홍보해주세요."
                  rows={8}
                />
                <p className="form-hint">
                  변수는 {'{변수명}'} 형식으로 입력하세요
                </p>
              </div>

              <div className="form-group">
                <label>아이콘</label>
                <div className="icon-selector">
                  {tabIconOptions.slice(0, 24).map(icon => (
                    <button
                      key={icon}
                      type="button"
                      className={`icon-btn ${formData.icon === icon ? 'active' : ''}`}
                      onClick={() => setFormData(prev => ({ ...prev, icon }))}
                    >
                      {icon}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                취소
              </button>
              <button className="btn-primary" onClick={handleSaveTemplate}>
                {editingTemplate ? '수정 완료' : '템플릿 추가'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Templates;
