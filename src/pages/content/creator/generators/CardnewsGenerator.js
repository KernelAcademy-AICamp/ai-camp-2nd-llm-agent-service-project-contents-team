// 카드뉴스 생성기

import api, { creditsAPI } from '../../../../services/api';
import { CREDIT_COSTS } from '../constants';

/**
 * 카드뉴스 미리보기 생성 함수
 * @param {Object} params - 생성 파라미터
 * @param {string} params.topic - 주제
 * @param {string} params.aspectRatio - 이미지 비율
 * @param {Object} params.userContext - 사용자 컨텍스트
 * @param {Function} params.onProgress - 진행 상태 콜백
 * @returns {Object} - 미리보기 결과
 */
export const generateCardnewsPreview = async ({
  topic,
  aspectRatio,
  userContext,
  onProgress
}) => {
  onProgress?.('AI가 카드뉴스 내용과 이미지를 생성하고 있습니다...');

  const previewFormData = new FormData();
  previewFormData.append('prompt', topic);
  previewFormData.append('purpose', 'info');
  previewFormData.append('generateImages', 'true');
  previewFormData.append('fontStyle', 'pretendard');
  previewFormData.append('colorTheme', 'warm');
  previewFormData.append('designTemplate', 'none');
  previewFormData.append('aspectRatio', aspectRatio);

  if (userContext) {
    previewFormData.append('userContext', JSON.stringify(userContext));
  }

  const previewResponse = await api.post('/api/preview-cardnews-content', previewFormData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  if (previewResponse.data.success && previewResponse.data.pages) {
    return {
      pages: previewResponse.data.pages,
      preview_images: previewResponse.data.preview_images || [],
      analysis: previewResponse.data.analysis,
      design_settings: previewResponse.data.design_settings,
      prompt: topic
    };
  }

  throw new Error('카드뉴스 미리보기 생성 실패');
};

/**
 * 카드뉴스 이미지 최종 생성 함수
 * @param {Object} params - 생성 파라미터
 * @param {Object} params.cardnewsPreview - 미리보기 데이터
 * @param {string} params.designTemplate - 디자인 템플릿
 * @param {string} params.aspectRatio - 이미지 비율
 * @param {Function} params.onProgress - 진행 상태 콜백
 * @returns {Object} - 생성된 카드뉴스 이미지 결과
 */
export const generateCardnewsImages = async ({
  cardnewsPreview,
  designTemplate,
  aspectRatio,
  onProgress
}) => {
  onProgress?.('카드뉴스 이미지를 생성하고 있습니다...');

  const colorTheme = 'warm';

  // 빈 줄 필터링된 페이지 데이터 생성
  const cleanedPages = cardnewsPreview.pages.map(page => ({
    ...page,
    content: (page.content || []).filter(line => line.trim())
  }));

  const formData = new FormData();
  formData.append('pages', JSON.stringify(cleanedPages));
  formData.append('prompt', cardnewsPreview.prompt);
  formData.append('purpose', 'info');
  formData.append('fontStyle', cardnewsPreview.design_settings?.font_pair || 'pretendard');
  formData.append('colorTheme', colorTheme);
  formData.append('designTemplate', designTemplate);
  formData.append('aspectRatio', aspectRatio);

  // 미리보기에서 생성된 배경 이미지가 있으면 전달 (재사용)
  if (cardnewsPreview.background_images && cardnewsPreview.background_images.length > 0) {
    formData.append('previewImages', JSON.stringify(cardnewsPreview.background_images));
  }

  const cardnewsResponse = await api.post('/api/generate-cardnews-from-content', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  if (cardnewsResponse.data.success && cardnewsResponse.data.cards) {
    const images = cardnewsResponse.data.cards.map((card, index) => ({
      url: card,
      prompt: `${cardnewsPreview.prompt} - 카드 ${index + 1}`
    }));

    return { images, cardCount: cardnewsResponse.data.cards.length };
  }

  throw new Error('카드뉴스 이미지 생성 실패');
};

/**
 * 카드뉴스 생성 후 크레딧 차감
 */
export const deductCardnewsCredits = async ({ setCreditBalance }) => {
  const requiredCredits = CREDIT_COSTS.cardnews;

  try {
    await creditsAPI.use(requiredCredits, '카드뉴스 생성', 'cardnews_generation');
    setCreditBalance(prev => prev - requiredCredits);
    console.log(`크레딧 ${requiredCredits} 차감 완료`);
  } catch (creditError) {
    console.error('크레딧 차감 실패:', creditError);
  }
};

/**
 * 카드뉴스 페이지 수정 핸들러
 */
export const handlePageEdit = (cardnewsPreview, setCardnewsPreview) => (pageIndex, field, value) => {
  if (!cardnewsPreview) return;

  const updatedPages = [...cardnewsPreview.pages];
  if (field === 'content') {
    updatedPages[pageIndex] = {
      ...updatedPages[pageIndex],
      content: value.split('\n')
    };
  } else {
    updatedPages[pageIndex] = {
      ...updatedPages[pageIndex],
      [field]: value
    };
  }

  setCardnewsPreview({
    ...cardnewsPreview,
    pages: updatedPages
  });
};

/**
 * 카드뉴스 페이지 추가 핸들러
 */
export const handleAddPage = (cardnewsPreview, setCardnewsPreview, setEditingPageIndex) => (afterIndex) => {
  if (!cardnewsPreview) return;

  const newPage = {
    title: '새 페이지',
    content: ['내용을 입력하세요']
  };

  const updatedPages = [...cardnewsPreview.pages];
  updatedPages.splice(afterIndex + 1, 0, newPage);

  setCardnewsPreview({
    ...cardnewsPreview,
    pages: updatedPages
  });

  setEditingPageIndex(afterIndex + 1);
};

/**
 * 카드뉴스 페이지 삭제 핸들러
 */
export const handleDeletePage = (cardnewsPreview, setCardnewsPreview, editingPageIndex, setEditingPageIndex) => (pageIndex) => {
  if (!cardnewsPreview) return;

  // 최소 2장은 유지 (표지 + 내용 1장)
  if (cardnewsPreview.pages.length <= 2) {
    alert('카드뉴스는 최소 2장 이상이어야 합니다.');
    return;
  }

  // 표지(0번 페이지)는 삭제 불가
  if (pageIndex === 0) {
    alert('표지는 삭제할 수 없습니다.');
    return;
  }

  if (!window.confirm(`${pageIndex}페이지를 삭제하시겠습니까?`)) {
    return;
  }

  const updatedPages = cardnewsPreview.pages.filter((_, idx) => idx !== pageIndex);

  setCardnewsPreview({
    ...cardnewsPreview,
    pages: updatedPages
  });

  if (editingPageIndex === pageIndex) {
    setEditingPageIndex(null);
  } else if (editingPageIndex > pageIndex) {
    setEditingPageIndex(editingPageIndex - 1);
  }
};

/**
 * 드래그 앤 드롭 핸들러
 */
export const handleDragEnd = (cardnewsPreview, setCardnewsPreview, editingPageIndex, setEditingPageIndex) => (result) => {
  if (!cardnewsPreview) return;

  const { destination, source } = result;

  if (!destination) return;
  if (destination.index === source.index) return;

  // 표지(0번)는 이동 불가
  if (source.index === 0 || destination.index === 0) {
    return;
  }

  const updatedPages = Array.from(cardnewsPreview.pages);
  const [movedPage] = updatedPages.splice(source.index, 1);
  updatedPages.splice(destination.index, 0, movedPage);

  setCardnewsPreview({
    ...cardnewsPreview,
    pages: updatedPages
  });

  if (editingPageIndex !== null) {
    if (editingPageIndex === source.index) {
      setEditingPageIndex(destination.index);
    } else if (source.index < editingPageIndex && destination.index >= editingPageIndex) {
      setEditingPageIndex(editingPageIndex - 1);
    } else if (source.index > editingPageIndex && destination.index <= editingPageIndex) {
      setEditingPageIndex(editingPageIndex + 1);
    }
  }
};

export default {
  generateCardnewsPreview,
  generateCardnewsImages,
  deductCardnewsCredits,
  handlePageEdit,
  handleAddPage,
  handleDeletePage,
  handleDragEnd
};
