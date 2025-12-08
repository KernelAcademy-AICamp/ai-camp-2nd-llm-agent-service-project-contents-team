import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Templates.css';

function Templates() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('all'); // all, text, image, video
  const [templates, setTemplates] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'text',
    category: '',
    prompt: '',
    description: '',
    icon: '📝'
  });

  // 아이콘 옵션
  const iconOptions = {
    text: ['📝', '✍️', '📰', '📖', '💬', '📢', '📣', '💡'],
    image: ['🎨', '🖼️', '📷', '🌅', '🎭', '✨', '🌈', '🎪'],
    video: ['🎬', '📹', '🎥', '🎞️', '📺', '🎦', '🎙️', '🎵']
  };

  // 카테고리 옵션
  const categoryOptions = {
    text: ['블로그', 'SNS 게시물', '광고 카피', '이메일', '제품 설명', '보도자료'],
    image: ['제품 이미지', '배너', '썸네일', '일러스트', '로고', '포스터'],
    video: ['제품 소개', '튜토리얼', '광고', '브이로그', '인터뷰', '애니메이션']
  };

  // 초기 샘플 템플릿
  const defaultTemplates = [
    // 글 템플릿
    { id: 1, name: '블로그 포스트', type: 'text', category: '블로그', icon: '📝',
      prompt: '주제: {topic}\n\n위 주제에 대해 SEO 최적화된 블로그 포스트를 작성해주세요. 서론, 본론, 결론 구조로 작성하고 핵심 키워드를 자연스럽게 포함해주세요.',
      description: 'SEO 최적화된 블로그 포스트 작성', uses: 145 },
    { id: 2, name: '인스타그램 캡션', type: 'text', category: 'SNS 게시물', icon: '📱',
      prompt: '주제: {topic}\n\n위 주제로 인스타그램 캡션을 작성해주세요. 이모지를 적절히 사용하고, 해시태그 5-10개를 포함해주세요.',
      description: '감성적인 인스타그램 캡션과 해시태그', uses: 234 },
    { id: 3, name: '제품 설명', type: 'text', category: '제품 설명', icon: '🛍️',
      prompt: '제품명: {product}\n특징: {features}\n\n위 제품에 대해 매력적인 설명을 작성해주세요. 고객의 문제점과 해결책을 중심으로 설득력 있게 작성해주세요.',
      description: '설득력 있는 제품 설명 문구', uses: 189 },
    { id: 4, name: '뉴스레터', type: 'text', category: '이메일', icon: '📧',
      prompt: '주제: {topic}\n대상: {audience}\n\n위 정보를 바탕으로 전문적이면서도 친근한 뉴스레터를 작성해주세요.',
      description: '구독자를 위한 뉴스레터 템플릿', uses: 98 },

    // 이미지 템플릿
    { id: 5, name: '제품 사진', type: 'image', category: '제품 이미지', icon: '🎨',
      prompt: 'Professional product photography of {product}, studio lighting, white background, high resolution, commercial photography style',
      description: '깔끔한 제품 촬영 스타일', uses: 312 },
    { id: 6, name: 'SNS 배너', type: 'image', category: '배너', icon: '🖼️',
      prompt: 'Modern social media banner design, {theme}, vibrant colors, minimalist style, professional, 16:9 aspect ratio',
      description: 'SNS용 배너 이미지 생성', uses: 178 },
    { id: 7, name: '유튜브 썸네일', type: 'image', category: '썸네일', icon: '📺',
      prompt: 'Eye-catching YouTube thumbnail, {topic}, bold text space, bright colors, high contrast, engaging composition',
      description: '클릭을 유도하는 썸네일', uses: 267 },
    { id: 8, name: '일러스트', type: 'image', category: '일러스트', icon: '✨',
      prompt: 'Digital illustration of {subject}, flat design style, pastel colors, cute and friendly, vector art style',
      description: '귀여운 일러스트 스타일', uses: 145 },

    // 영상 템플릿
    { id: 9, name: '제품 소개 영상', type: 'video', category: '제품 소개', icon: '🎬',
      prompt: 'Cinematic product showcase of {product}, smooth camera movements, elegant lighting, professional commercial style',
      description: '세련된 제품 소개 영상', uses: 89 },
    { id: 10, name: '튜토리얼 인트로', type: 'video', category: '튜토리얼', icon: '📚',
      prompt: 'Modern tutorial intro animation, {topic}, clean motion graphics, professional educational content style',
      description: '교육 콘텐츠용 인트로', uses: 76 },
    { id: 11, name: '브이로그 전환', type: 'video', category: '브이로그', icon: '📹',
      prompt: 'Aesthetic vlog transition, {mood} atmosphere, smooth transitions, lifestyle content style',
      description: '브이로그용 전환 효과', uses: 134 },
    { id: 12, name: '광고 클립', type: 'video', category: '광고', icon: '📺',
      prompt: 'Dynamic advertisement clip for {product}, energetic pace, modern style, attention-grabbing visuals',
      description: '짧은 광고 영상 클립', uses: 167 }
  ];

  // 로컬 스토리지에서 템플릿 로드
  useEffect(() => {
    const saved = localStorage.getItem('userTemplates');
    if (saved) {
      setTemplates(JSON.parse(saved));
    } else {
      setTemplates(defaultTemplates);
      localStorage.setItem('userTemplates', JSON.stringify(defaultTemplates));
    }
  }, []);

  // 템플릿 저장
  const saveTemplates = (newTemplates) => {
    setTemplates(newTemplates);
    localStorage.setItem('userTemplates', JSON.stringify(newTemplates));
  };

  // 필터링된 템플릿
  const filteredTemplates = templates.filter(t =>
    activeTab === 'all' || t.type === activeTab
  );

  // 탭별 카운트
  const tabCounts = {
    all: templates.length,
    text: templates.filter(t => t.type === 'text').length,
    image: templates.filter(t => t.type === 'image').length,
    video: templates.filter(t => t.type === 'video').length
  };

  // 모달 열기 (새 템플릿)
  const openNewModal = () => {
    setEditingTemplate(null);
    setFormData({
      name: '',
      type: activeTab === 'all' ? 'text' : activeTab,
      category: '',
      prompt: '',
      description: '',
      icon: activeTab === 'image' ? '🎨' : activeTab === 'video' ? '🎬' : '📝'
    });
    setShowModal(true);
  };

  // 모달 열기 (수정)
  const openEditModal = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      type: template.type,
      category: template.category,
      prompt: template.prompt,
      description: template.description,
      icon: template.icon
    });
    setShowModal(true);
  };

  // 폼 입력 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
      // 타입 변경 시 아이콘과 카테고리 초기화
      ...(name === 'type' && {
        icon: iconOptions[value][0],
        category: ''
      })
    }));
  };

  // 템플릿 저장
  const handleSaveTemplate = () => {
    if (!formData.name.trim() || !formData.prompt.trim()) {
      alert('템플릿 이름과 프롬프트는 필수입니다.');
      return;
    }

    if (editingTemplate) {
      // 수정
      const updated = templates.map(t =>
        t.id === editingTemplate.id
          ? { ...t, ...formData }
          : t
      );
      saveTemplates(updated);
    } else {
      // 새로 추가
      const newTemplate = {
        id: Date.now(),
        ...formData,
        uses: 0
      };
      saveTemplates([...templates, newTemplate]);
    }
    setShowModal(false);
  };

  // 템플릿 삭제
  const handleDeleteTemplate = (id) => {
    if (window.confirm('이 템플릿을 삭제하시겠습니까?')) {
      saveTemplates(templates.filter(t => t.id !== id));
    }
  };

  // 템플릿 사용
  const handleUseTemplate = (template) => {
    // 사용 횟수 증가
    const updated = templates.map(t =>
      t.id === template.id
        ? { ...t, uses: (t.uses || 0) + 1 }
        : t
    );
    saveTemplates(updated);

    // 해당 페이지로 이동하면서 템플릿 데이터 전달
    const routes = {
      text: '/ai-content',
      image: '/image',
      video: '/ai-video'
    };

    navigate(routes[template.type], {
      state: { template: template }
    });
  };

  // 템플릿 복제
  const handleDuplicateTemplate = (template) => {
    const duplicated = {
      ...template,
      id: Date.now(),
      name: `${template.name} (복사본)`,
      uses: 0
    };
    saveTemplates([...templates, duplicated]);
  };

  return (
    <div className="templates-page">
      <div className="templates-header">
        <div className="header-left">
          <h2>템플릿 갤러리</h2>
          <p className="header-subtitle">자주 사용하는 프롬프트를 템플릿으로 저장하고 재사용하세요</p>
        </div>
        <button className="btn-primary" onClick={openNewModal}>
          + 새 템플릿 만들기
        </button>
      </div>

      {/* 탭 네비게이션 */}
      <div className="templates-tabs">
        <button
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          전체 <span className="tab-count">{tabCounts.all}</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
          onClick={() => setActiveTab('text')}
        >
          글 <span className="tab-count">{tabCounts.text}</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => setActiveTab('image')}
        >
          이미지 <span className="tab-count">{tabCounts.image}</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => setActiveTab('video')}
        >
          영상 <span className="tab-count">{tabCounts.video}</span>
        </button>
      </div>

      {/* 템플릿 그리드 */}
      {filteredTemplates.length === 0 ? (
        <div className="templates-empty">
          <h3>템플릿이 없습니다</h3>
          <p>새 템플릿을 만들어 자주 사용하는 프롬프트를 저장하세요</p>
          <button className="btn-primary" onClick={openNewModal}>
            + 첫 템플릿 만들기
          </button>
        </div>
      ) : (
        <div className="templates-grid">
          {filteredTemplates.map((template) => (
            <div key={template.id} className={`template-card type-${template.type}`}>
              <div className="template-header">
                <h3>{template.name}</h3>
                <div className="template-type-badge">{
                  template.type === 'text' ? '글' :
                  template.type === 'image' ? '이미지' : '영상'
                }</div>
              </div>
              <p className="template-category">{template.category}</p>
              <p className="template-description">{template.description}</p>
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
          ))}
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
                <label>템플릿 타입</label>
                <div className="type-selector">
                  <button
                    type="button"
                    className={`type-btn ${formData.type === 'text' ? 'active' : ''}`}
                    onClick={() => handleInputChange({ target: { name: 'type', value: 'text' }})}
                  >
                    글
                  </button>
                  <button
                    type="button"
                    className={`type-btn ${formData.type === 'image' ? 'active' : ''}`}
                    onClick={() => handleInputChange({ target: { name: 'type', value: 'image' }})}
                  >
                    이미지
                  </button>
                  <button
                    type="button"
                    className={`type-btn ${formData.type === 'video' ? 'active' : ''}`}
                    onClick={() => handleInputChange({ target: { name: 'type', value: 'video' }})}
                  >
                    영상
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label>템플릿 이름 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="예: 인스타그램 캡션"
                />
              </div>

              <div className="form-group">
                <label>카테고리</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                >
                  <option value="">선택하세요</option>
                  {categoryOptions[formData.type].map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>설명</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="템플릿에 대한 간단한 설명"
                />
              </div>

              <div className="form-group">
                <label>프롬프트 템플릿 *</label>
                <textarea
                  name="prompt"
                  value={formData.prompt}
                  onChange={handleInputChange}
                  placeholder="프롬프트를 입력하세요. {변수} 형식으로 변수를 추가할 수 있습니다."
                  rows={6}
                />
                <p className="form-hint">
                  팁: {'{topic}'}, {'{product}'} 등 중괄호로 변수를 지정하면 사용 시 값을 입력받을 수 있습니다.
                </p>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                취소
              </button>
              <button className="btn-primary" onClick={handleSaveTemplate}>
                {editingTemplate ? '수정 완료' : '템플릿 저장'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Templates;
