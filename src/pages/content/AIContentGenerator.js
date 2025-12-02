import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import AgenticContentForm from '../../components/AgenticContentForm';
import AgenticContentResult from '../../components/AgenticContentResult';
import { generateAgenticContent } from '../../services/agenticService';
import { useContent } from '../../contexts/ContentContext';
import './ContentCommon.css';
import './AIContentGenerator.css';

function AIContentGenerator() {
  const location = useLocation();
  const { generatedContent, setGeneratedContent } = useContent();
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [currentStep, setCurrentStep] = useState('');
  const [templateText, setTemplateText] = useState('');

  // 템플릿에서 넘어온 경우 프롬프트 적용
  useEffect(() => {
    if (location.state?.template) {
      const template = location.state.template;
      setTemplateText(template.prompt || '');
    }
  }, [location.state]);

  const handleGenerate = async (formData) => {
    setIsGenerating(true);
    setGeneratedContent(null);
    setProgressMessage('AI 에이전트 초기화 중...');
    setCurrentStep('init');

    try {
      const result = await generateAgenticContent(formData, (progress) => {
        setProgressMessage(progress.message);
        setCurrentStep(progress.step);
        console.log(`📊 Progress: ${progress.message} (${progress.step})`);
      });

      console.log('✅ AI 콘텐츠 생성 완료:', result);
      setGeneratedContent(result);
      setProgressMessage('');
      setCurrentStep('');
    } catch (error) {
      console.error('❌ AI 콘텐츠 생성 오류:', error);
      alert('콘텐츠 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
      setProgressMessage('');
      setCurrentStep('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEdit = () => {
    setGeneratedContent(null);
    setProgressMessage('');
    setCurrentStep('');
  };

  const handleSave = () => {
    // TODO: 실제 저장 로직 구현
    alert('콘텐츠가 저장되었습니다.');
  };

  // 진행 상태에 따른 아이콘
  const getStepIcon = (step) => {
    switch (step) {
      case 'analyzing':
        return '🧠';
      case 'extracting':
        return '👁️';
      case 'writing':
        return '✍️';
      case 'critiquing':
        return '🔍';
      case 'complete':
        return '✅';
      default:
        return '⚙️';
    }
  };

  return (
    <div className="content-page">
      <div className="page-header">
        <div>
          <h1>AI 글 생성</h1>
          <p className="page-description">
            최소한의 입력으로 AI가 자동으로 네이버 블로그와 SNS용 콘텐츠를 생성합니다.
          </p>
        </div>
      </div>

      {/* 진행 상태 표시 */}
      {isGenerating && progressMessage && (
        <div className="progress-banner">
          <div className="progress-content">
            <span className="progress-icon">{getStepIcon(currentStep)}</span>
            <div className="progress-text">
              <div className="progress-message">{progressMessage}</div>
              <div className="progress-detail">
                AI 에이전트가 협력하여 최적의 콘텐츠를 생성하고 있습니다.
              </div>
            </div>
            <div className="progress-spinner"></div>
          </div>
        </div>
      )}

      <div className="generator-content">
        {/* 입력 폼 */}
        {!generatedContent && (
          <AgenticContentForm
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            initialText={templateText}
          />
        )}

        {/* 생성 결과 */}
        {generatedContent && (
          <AgenticContentResult
            result={generatedContent}
            onEdit={handleEdit}
            onSave={handleSave}
          />
        )}
      </div>

      {/* 기능 설명 섹션 (결과가 없을 때만 표시) */}
      {!generatedContent && !isGenerating && (
        <div className="feature-info">
          <h3>AI 글 생성의 특징</h3>
          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h4>4개의 AI 에이전트 협업</h4>
              <p>Orchestrator, Multi-Modal Analyzer, Writer, Critic 에이전트가 협력하여 고품질 콘텐츠를 생성합니다.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h4>플랫폼 최적화</h4>
              <p>네이버 블로그와 SNS 각 플랫폼의 특성에 맞는 길이, 톤, 형식으로 자동 생성됩니다.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔍</div>
              <h4>자동 품질 검증</h4>
              <p>Critic 에이전트가 콘텐츠를 평가하고, 80점 미만일 경우 자동으로 개선합니다.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📸</div>
              <h4>멀티모달 분석</h4>
              <p>텍스트와 이미지를 함께 분석하여 더욱 풍부하고 정확한 콘텐츠를 생성합니다.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIContentGenerator;
