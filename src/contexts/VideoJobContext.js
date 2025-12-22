import React, { createContext, useState, useContext, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

const VideoJobContext = createContext(null);

// 폴링 간격 (5초)
const POLLING_INTERVAL = 5000;

// 로컬 스토리지 키
const STORAGE_KEY = 'pending_video_jobs';

export const VideoJobProvider = ({ children }) => {
  // 진행 중인 작업 목록 { jobId: jobData }
  const [activeJobs, setActiveJobs] = useState({});
  // 완료된 작업 알림 (토스트용)
  const [completedJob, setCompletedJob] = useState(null);
  // 폴링 인터벌 ref
  const pollingRef = useRef(null);

  // 로컬 스토리지에서 복원
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const jobs = JSON.parse(saved);
        setActiveJobs(jobs);
      } catch (e) {
        console.error('Failed to restore video jobs:', e);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  // 상태 변경 시 로컬 스토리지에 저장
  useEffect(() => {
    if (Object.keys(activeJobs).length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(activeJobs));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [activeJobs]);

  // 작업 상태 조회
  const fetchJobStatus = useCallback(async (jobId) => {
    try {
      const response = await api.get(`/api/ai-video/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch job ${jobId}:`, error);
      if (error.response?.status === 404) {
        return { status: 'not_found' };
      }
      return null;
    }
  }, []);

  // 모든 활성 작업 상태 체크
  const pollActiveJobs = useCallback(async () => {
    const jobIds = Object.keys(activeJobs);
    if (jobIds.length === 0) return;

    for (const jobId of jobIds) {
      const jobData = await fetchJobStatus(jobId);

      if (!jobData) continue;

      if (jobData.status === 'completed') {
        setCompletedJob({
          id: jobId,
          productName: jobData.product_name,
          finalVideoUrl: jobData.final_video_url,
        });

        setActiveJobs(prev => {
          const updated = { ...prev };
          delete updated[jobId];
          return updated;
        });
      } else if (jobData.status === 'failed' || jobData.status === 'not_found') {
        if (jobData.status === 'failed') {
          setCompletedJob({
            id: jobId,
            productName: activeJobs[jobId]?.productName || '알 수 없음',
            failed: true,
            error: jobData.error_message,
          });
        }

        setActiveJobs(prev => {
          const updated = { ...prev };
          delete updated[jobId];
          return updated;
        });
      } else {
        // 진행 중 - 상태 업데이트
        setActiveJobs(prev => ({
          ...prev,
          [jobId]: {
            ...prev[jobId],
            status: jobData.status,
            currentStep: jobData.current_step,
          },
        }));
      }
    }
  }, [activeJobs, fetchJobStatus]);

  // 폴링 시작/중지
  useEffect(() => {
    if (Object.keys(activeJobs).length > 0) {
      pollActiveJobs();
      pollingRef.current = setInterval(pollActiveJobs, POLLING_INTERVAL);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [Object.keys(activeJobs).length, pollActiveJobs]);

  // 새 작업 추가
  const addJob = useCallback((jobId, productName) => {
    setActiveJobs(prev => ({
      ...prev,
      [jobId]: {
        productName,
        status: 'pending',
        currentStep: '대기 중...',
        startedAt: Date.now(),
      },
    }));
  }, []);

  // 작업 제거
  const removeJob = useCallback((jobId) => {
    setActiveJobs(prev => {
      const updated = { ...prev };
      delete updated[jobId];
      return updated;
    });
  }, []);

  // 완료 알림 닫기
  const clearCompletedNotification = useCallback(() => {
    setCompletedJob(null);
  }, []);

  const activeJobCount = Object.keys(activeJobs).length;
  const firstActiveJob = activeJobCount > 0
    ? { id: Object.keys(activeJobs)[0], ...Object.values(activeJobs)[0] }
    : null;

  const value = {
    activeJobs,
    activeJobCount,
    firstActiveJob,
    completedJob,
    addJob,
    removeJob,
    clearCompletedNotification,
  };

  return (
    <VideoJobContext.Provider value={value}>
      {children}
    </VideoJobContext.Provider>
  );
};

export const useVideoJob = () => {
  const context = useContext(VideoJobContext);
  if (!context) {
    throw new Error('useVideoJob must be used within a VideoJobProvider');
  }
  return context;
};

export default VideoJobContext;
