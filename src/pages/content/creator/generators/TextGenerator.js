// 텍스트 콘텐츠 생성기

import { generateAgenticContent } from '../../../../services/agenticService';
import { contentSessionAPI } from '../../../../services/api';

/**
 * 텍스트(글) 콘텐츠 생성 함수
 * @param {Object} params - 생성 파라미터
 * @param {string} params.topic - 주제
 * @param {Array} params.selectedPlatforms - 선택된 플랫폼 목록
 * @param {Object} params.userContext - 사용자 컨텍스트 (온보딩 정보)
 * @param {Function} params.onProgress - 진행 상태 콜백
 * @returns {Object} - 생성된 콘텐츠 결과
 */
export const generateTextContent = async ({
  topic,
  selectedPlatforms,
  userContext,
  onProgress
}) => {
  onProgress?.('AI가 글을 작성하고 있습니다...');

  const agenticResult = await generateAgenticContent(
    {
      textInput: topic,
      images: [],
      styleTone: '친근하고 편안한 말투로',
      selectedPlatforms,
      userContext
    },
    (progress) => onProgress?.(progress.message)
  );

  return {
    agenticResult,
    text: {
      blog: selectedPlatforms.includes('blog') ? agenticResult.blog : null,
      sns: selectedPlatforms.includes('sns') ? agenticResult.sns : null,
      x: selectedPlatforms.includes('x') ? agenticResult.x : null,
      threads: selectedPlatforms.includes('threads') ? agenticResult.threads : null,
      analysis: agenticResult.analysis,
      critique: agenticResult.critique,
      platforms: selectedPlatforms,
    }
  };
};

/**
 * 텍스트 콘텐츠 자동 저장 함수
 */
export const saveTextContent = async ({
  topic,
  content,
  platforms,
  hasSavedRef
}) => {
  if (hasSavedRef?.current) {
    console.log('이미 저장됨, 중복 저장 스킵');
    return;
  }

  if (!content.blog && !content.sns && !content.x && !content.threads) {
    console.log('저장할 콘텐츠가 없음, 스킵');
    return;
  }

  if (!platforms || platforms.length === 0) {
    console.log('선택된 플랫폼이 없음, 스킵');
    return;
  }

  try {
    const saveData = {
      topic,
      content_type: 'text',
      style: 'default',
      selected_platforms: platforms,
      blog: content.blog ? {
        title: content.blog.title || '제목 없음',
        content: content.blog.content || '',
        tags: content.blog.tags || [],
        score: content.critique?.blog?.score || null
      } : null,
      sns: content.sns ? {
        content: content.sns.content || '',
        hashtags: content.sns.tags || content.sns.hashtags || [],
        score: content.critique?.sns?.score || null
      } : null,
      x: content.x ? {
        content: content.x.content || '',
        hashtags: content.x.tags || content.x.hashtags || [],
        score: content.critique?.x?.score || null
      } : null,
      threads: content.threads ? {
        content: content.threads.content || '',
        hashtags: content.threads.tags || content.threads.hashtags || [],
        score: content.critique?.threads?.score || null
      } : null,
      images: null,
      requested_image_count: 0,
      analysis_data: content.analysis || null,
      critique_data: content.critique || null,
      generation_attempts: content.metadata?.attempts || 1
    };

    await contentSessionAPI.save(saveData);
    if (hasSavedRef) hasSavedRef.current = true;
    console.log('텍스트 콘텐츠 저장 성공');
  } catch (error) {
    console.error('텍스트 콘텐츠 저장 실패:', error);
  }
};

export default { generateTextContent, saveTextContent };
