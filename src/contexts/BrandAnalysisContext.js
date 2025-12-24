import React, { createContext, useState, useContext, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

const BrandAnalysisContext = createContext(null);

// 폴링 간격 (5초)
const POLLING_INTERVAL = 5000;

// 로컬 스토리지 키
const STORAGE_KEY = 'brand_analysis_status';

export const BrandAnalysisProvider = ({ children }) => {
  // 분석 상태: null | 'analyzing' | 'completed' | 'failed'
  const [analysisStatus, setAnalysisStatus] = useState(null);
  // 분석 에러 메시지
  const [analysisError, setAnalysisError] = useState(null);
  // 분석 결과 데이터
  const [analysisResult, setAnalysisResult] = useState(null);
  // 완료/실패 알림 (토스트용)
  const [notification, setNotification] = useState(null);
  // 폴링 인터벌 ref
  const pollingRef = useRef(null);
  // 분석 시작 시간
  const [startedAt, setStartedAt] = useState(null);
  // 분석 진행률 (0-100)
  const [progress, setProgress] = useState(0);
  // 현재 분석 단계
  const [step, setStep] = useState(null);

  // 로컬 스토리지에서 복원
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.status === 'analyzing') {
          setAnalysisStatus('analyzing');
          setStartedAt(data.startedAt);
        }
      } catch (e) {
        console.error('Failed to restore brand analysis status:', e);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  // 상태 변경 시 로컬 스토리지에 저장
  useEffect(() => {
    if (analysisStatus === 'analyzing') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        status: 'analyzing',
        startedAt: startedAt || Date.now(),
      }));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [analysisStatus, startedAt]);

  // 분석 상태 조회
  const fetchAnalysisStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/brand-analysis/status');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch brand analysis status:', error);
      return null;
    }
  }, []);

  // 폴링 함수
  const pollAnalysisStatus = useCallback(async () => {
    if (analysisStatus !== 'analyzing') return;

    const data = await fetchAnalysisStatus();
    if (!data) return;

    // 진행률 및 단계 업데이트
    if (data.analysis_progress !== undefined) {
      setProgress(data.analysis_progress);
    }
    if (data.analysis_step) {
      setStep(data.analysis_step);
    }

    if (data.analysis_status === 'completed') {
      setAnalysisStatus('completed');
      setAnalysisResult(data);
      setProgress(100);
      setStep('completed');
      setNotification({
        type: 'success',
        message: '브랜드 분석이 완료되었습니다!',
        data: data.overall,
      });
    } else if (data.analysis_status === 'failed') {
      setAnalysisStatus('failed');
      setAnalysisError(data.analysis_error);
      setNotification({
        type: 'error',
        message: '브랜드 분석에 실패했습니다.',
        error: data.analysis_error,
      });
    }
    // 'analyzing' 상태면 계속 폴링
  }, [analysisStatus, fetchAnalysisStatus]);

  // 폴링 시작/중지
  useEffect(() => {
    if (analysisStatus === 'analyzing') {
      pollAnalysisStatus();
      pollingRef.current = setInterval(pollAnalysisStatus, POLLING_INTERVAL);
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
  }, [analysisStatus, pollAnalysisStatus]);

  // 분석 시작
  const startAnalysis = useCallback(() => {
    setAnalysisStatus('analyzing');
    setAnalysisError(null);
    setAnalysisResult(null);
    setStartedAt(Date.now());
    setProgress(0);
    setStep('collecting');
  }, []);

  // 분석 중지 (수동 취소 시)
  const stopAnalysis = useCallback(() => {
    setAnalysisStatus(null);
    setStartedAt(null);
    setProgress(0);
    setStep(null);
  }, []);

  // 알림 닫기
  const clearNotification = useCallback(() => {
    setNotification(null);
  }, []);

  // 분석 상태 직접 설정 (페이지 로드 시 복원용)
  const setStatus = useCallback((status, result = null) => {
    setAnalysisStatus(status);
    if (result) {
      setAnalysisResult(result);
    }
  }, []);

  // 경과 시간 계산 (초)
  const elapsedSeconds = startedAt ? Math.floor((Date.now() - startedAt) / 1000) : 0;

  const value = {
    // 상태
    analysisStatus,
    analysisError,
    analysisResult,
    notification,
    elapsedSeconds,
    progress,
    step,
    isAnalyzing: analysisStatus === 'analyzing',
    isCompleted: analysisStatus === 'completed',
    isFailed: analysisStatus === 'failed',

    // 액션
    startAnalysis,
    stopAnalysis,
    setStatus,
    clearNotification,
    fetchAnalysisStatus,
  };

  return (
    <BrandAnalysisContext.Provider value={value}>
      {children}
    </BrandAnalysisContext.Provider>
  );
};

export const useBrandAnalysis = () => {
  const context = useContext(BrandAnalysisContext);
  if (!context) {
    throw new Error('useBrandAnalysis must be used within a BrandAnalysisProvider');
  }
  return context;
};

export default BrandAnalysisContext;
