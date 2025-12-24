// AI 이미지 생성기

import api, { creditsAPI } from '../../../../services/api';
import { CREDIT_COSTS } from '../constants';

/**
 * 비율 ID를 API 형식으로 변환
 * @param {string} aspectRatio - 비율 ID (예: '1:1', '4:5', '16:9')
 * @returns {string} - API 형식 비율 (예: '1:1', '4:5', '16:9')
 */
const formatAspectRatio = (aspectRatio) => {
  // aspectRatio가 이미 올바른 형식이면 그대로 반환
  if (!aspectRatio) return '1:1';
  return aspectRatio;
};

/**
 * AI 이미지 생성 함수
 * @param {Object} params - 생성 파라미터
 * @param {string} params.topic - 주제/프롬프트
 * @param {number} params.imageCount - 생성할 이미지 수
 * @param {string} params.aspectRatio - 이미지 비율 (예: '1:1', '4:5', '16:9')
 * @param {Function} params.onProgress - 진행 상태 콜백
 * @returns {Object} - 생성된 이미지 결과
 */
export const generateAIImages = async ({
  topic,
  imageCount,
  aspectRatio = '1:1',
  onProgress
}) => {
  const images = [];
  const formattedRatio = formatAspectRatio(aspectRatio);

  for (let i = 0; i < imageCount; i++) {
    onProgress?.(`AI가 이미지를 생성하고 있습니다... (${i + 1}/${imageCount})`);

    try {
      const imageResponse = await api.post('/api/generate-image', {
        prompt: topic,
        model: 'nanobanana',
        aspect_ratio: formattedRatio
      });

      if (imageResponse.data.imageUrl) {
        images.push({
          url: imageResponse.data.imageUrl,
          prompt: topic
        });
      }
    } catch (imgError) {
      console.error(`이미지 ${i + 1} 생성 실패:`, imgError);
    }
  }

  return { images };
};

/**
 * AI 이미지 생성 후 크레딧 차감
 */
export const deductImageCredits = async ({
  imageCount,
  generatedCount,
  setCreditBalance
}) => {
  if (generatedCount === 0) return;

  const requiredCredits = CREDIT_COSTS.ai_image * generatedCount;

  try {
    await creditsAPI.use(
      requiredCredits,
      `AI 이미지 생성 (${generatedCount}장)`,
      'image_generation'
    );
    setCreditBalance(prev => prev - requiredCredits);
    console.log(`크레딧 ${requiredCredits} 차감 완료`);
  } catch (creditError) {
    console.error('크레딧 차감 실패:', creditError);
  }
};

/**
 * 이미지 다운로드 함수
 */
export const downloadImage = (imageUrl, index) => {
  const link = document.createElement('a');
  link.href = imageUrl;
  link.download = `generated-image-${index + 1}-${Date.now()}.png`;
  link.click();
};

/**
 * 모든 이미지 다운로드 함수
 */
export const downloadAllImages = (images) => {
  images?.forEach((img, index) => {
    setTimeout(() => downloadImage(img.url, index), index * 500);
  });
};

export default {
  generateAIImages,
  deductImageCredits,
  downloadImage,
  downloadAllImages
};
