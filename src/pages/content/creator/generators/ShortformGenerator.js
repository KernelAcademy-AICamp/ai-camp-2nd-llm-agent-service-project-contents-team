// 숏폼 영상 생성기

import api, { creditsAPI } from '../../../../services/api';
import { VIDEO_DURATION_OPTIONS } from '../constants';

/**
 * 숏폼 영상 생성 시작 함수
 * @param {Object} params - 생성 파라미터
 * @param {string} params.topic - 주제
 * @param {string} params.videoDuration - 영상 길이 (short/standard/premium)
 * @param {Object} params.uploadedImage - 업로드된 이미지 정보
 * @param {Function} params.onProgress - 진행 상태 콜백
 * @returns {Object} - 생성 작업 정보
 */
export const startShortformGeneration = async ({
  topic,
  videoDuration,
  uploadedImage,
  onProgress
}) => {
  onProgress?.('AI가 숏폼 영상을 생성하고 있습니다...');

  const formData = new FormData();
  formData.append('product_name', topic);
  formData.append('product_description', `${topic} 홍보 영상`);
  formData.append('tier', videoDuration);
  formData.append('image', uploadedImage.file);

  const videoJobResponse = await api.post('/api/ai-video/jobs', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  if (videoJobResponse.data && videoJobResponse.data.id) {
    return {
      jobId: videoJobResponse.data.id,
      videoStatus: 'processing'
    };
  }

  throw new Error('숏폼 영상 생성 작업 시작 실패');
};

/**
 * 숏폼 영상 생성 상태 확인 함수
 * @param {string} jobId - 작업 ID
 * @returns {Object} - 작업 상태 정보
 */
export const checkShortformStatus = async (jobId) => {
  const statusResponse = await api.get(`/api/ai-video/jobs/${jobId}`);
  return statusResponse.data;
};

/**
 * 숏폼 영상 폴링 시작 함수
 * @param {Object} params - 폴링 파라미터
 * @param {string} params.jobId - 작업 ID
 * @param {Object} params.generatedResult - 현재 생성 결과
 * @param {Function} params.setProgress - 진행 상태 설정 함수
 * @param {Function} params.setResult - 결과 설정 함수
 */
export const startPolling = ({
  jobId,
  generatedResult,
  setProgress,
  setResult
}) => {
  const checkVideoStatus = async () => {
    try {
      const job = await checkShortformStatus(jobId);

      if (job.status === 'completed' && job.final_video_url) {
        generatedResult.videoUrl = job.final_video_url;
        generatedResult.videoStatus = 'completed';
        setProgress('숏폼 영상 생성 완료!');
        setResult({ ...generatedResult });
      } else if (job.status === 'failed') {
        generatedResult.videoStatus = 'failed';
        generatedResult.videoError = job.error_message;
        setProgress(`영상 생성 실패: ${job.error_message}`);
        setResult({ ...generatedResult });
      } else {
        // 아직 처리 중
        const currentStep = job.current_step || '처리 중';
        setProgress(currentStep);
        setResult({ ...generatedResult });
        setTimeout(checkVideoStatus, 2000);
      }
    } catch (statusError) {
      console.error('영상 상태 확인 실패:', statusError);
      setProgress('영상 상태 확인 중 오류가 발생했습니다.');
    }
  };

  // 1초 후 첫 번째 상태 확인
  setTimeout(checkVideoStatus, 1000);
};

/**
 * 숏폼 영상 생성 후 크레딧 차감
 */
export const deductShortformCredits = async ({
  videoDuration,
  setCreditBalance
}) => {
  const option = VIDEO_DURATION_OPTIONS.find(o => o.id === videoDuration);
  const requiredCredits = option?.credits || 0;

  if (requiredCredits === 0) return;

  try {
    await creditsAPI.use(
      requiredCredits,
      `숏폼 영상 생성 (${option?.duration || videoDuration})`,
      'video_generation'
    );
    setCreditBalance(prev => prev - requiredCredits);
    console.log(`크레딧 ${requiredCredits} 차감 완료`);
  } catch (creditError) {
    console.error('크레딧 차감 실패:', creditError);
  }
};

/**
 * 영상 진행 상태 파싱 함수
 * @param {string} currentStep - 현재 단계 문자열
 * @returns {Object} - 파싱된 진행 상태
 */
export const parseVideoProgress = (currentStep) => {
  let currentPhase = 0;
  let progressPercent = 0;

  // 1단계: 스토리보드 생성 (4 Agents 포함)
  if (currentStep.includes('1단계') || currentStep.includes('제품 분석') || currentStep.includes('로딩')) {
    currentPhase = 0;
    progressPercent = 5;
  } else if (currentStep.includes('2단계') || currentStep.includes('스토리 기획')) {
    currentPhase = 0;
    progressPercent = 10;
  } else if (currentStep.includes('3단계') || currentStep.includes('장면 연출')) {
    currentPhase = 0;
    progressPercent = 15;
  } else if (currentStep.includes('4단계') || currentStep.includes('품질 검증')) {
    currentPhase = 0;
    progressPercent = 20;
  } else if (currentStep.includes('Generating image') || currentStep.includes('이미지')) {
    // 2단계: 이미지 생성
    currentPhase = 1;
    const match = currentStep.match(/(\d+)\/(\d+)/);
    if (match) {
      const current = parseInt(match[1]);
      const total = parseInt(match[2]);
      progressPercent = 25 + (current / total) * 25;
    } else {
      progressPercent = 30;
    }
  } else if (currentStep.includes('transition') || currentStep.includes('Kling') || currentStep.includes('Veo')) {
    // 3단계: 전환 비디오 생성
    currentPhase = 2;
    const match = currentStep.match(/(\d+)\/(\d+)/);
    if (match) {
      const current = parseInt(match[1]);
      const total = parseInt(match[2]);
      progressPercent = 50 + (current / total) * 35;
    } else {
      progressPercent = 55;
    }
  } else if (currentStep.includes('Composing') || currentStep.includes('Concatenating') || currentStep.includes('Rendering') || currentStep.includes('Uploading')) {
    // 4단계: 최종 합성
    currentPhase = 3;
    if (currentStep.includes('Composing')) progressPercent = 85;
    else if (currentStep.includes('Concatenating')) progressPercent = 90;
    else if (currentStep.includes('Rendering')) progressPercent = 95;
    else if (currentStep.includes('Uploading')) progressPercent = 98;
  }

  return { currentPhase, progressPercent };
};

/**
 * 영상 생성 단계 목록
 */
export const VIDEO_PHASES = [
  { name: '스토리보드 생성', icon: '📝' },
  { name: '이미지 생성', icon: '🖼️' },
  { name: '전환 비디오 생성', icon: '🎬' },
  { name: '최종 합성', icon: '✨' }
];

export default {
  startShortformGeneration,
  checkShortformStatus,
  startPolling,
  deductShortformCredits,
  parseVideoProgress,
  VIDEO_PHASES
};
