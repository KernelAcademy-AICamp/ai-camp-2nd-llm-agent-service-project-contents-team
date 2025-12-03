import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import AgenticContentForm from '../../components/AgenticContentForm';
import AgenticContentResult from '../../components/AgenticContentResult';
import { generateAgenticContent } from '../../services/agenticService';
import { useContent } from '../../contexts/ContentContext';
import { aiContentAPI, snsContentAPI } from '../../services/api';
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

  // 자동 저장 함수 (생성 완료 시 호출)
  const autoSaveContent = async (content) => {
    try {
      // AI 생성 콘텐츠 저장
      const saveData = {
        input_text: content.analysis?.subject || '',
        input_image_count: content.uploadedImages?.length || 0,
        blog_title: content.blog?.title || '',
        blog_content: content.blog?.content || '',
        blog_tags: content.blog?.tags || [],
        sns_content: content.sns?.content || '',
        sns_hashtags: content.sns?.tags || [],
        analysis_data: content.analysis || null,
        blog_score: content.critique?.blog?.score || null,
        sns_score: content.critique?.sns?.score || null,
        critique_data: content.critique || null,
        generation_attempts: content.metadata?.attempts || 1
      };

      await aiContentAPI.save(saveData);
      console.log('✅ AI 콘텐츠 자동 저장 완료');

      // SNS 콘텐츠도 별도 저장 (Instagram용)
      if (content.sns?.content) {
        await snsContentAPI.save({
          platform: 'instagram',
          caption: content.sns.content || '',
          hashtags: content.sns.tags || [],
          image_urls: content.uploadedImages || [],
          status: 'draft'
        });
        console.log('✅ SNS 콘텐츠 자동 저장 완료');
      }
    } catch (error) {
      console.error('콘텐츠 자동 저장 실패:', error);
    }
  };

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

      // 생성 완료 시 자동 저장
      await autoSaveContent(result);
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
        {/* 생성 전: 입력 폼 + 미리보기 플레이스홀더 */}
        {!generatedContent && (
          <div className="generator-layout">
            {/* 왼쪽: 입력 폼 */}
            <div className="generator-form-section">
              <AgenticContentForm
                onGenerate={handleGenerate}
                isGenerating={isGenerating}
                initialText={templateText}
              />
            </div>

            {/* 오른쪽: 미리보기 (예시 콘텐츠) */}
            <div className="generator-preview-section">
              <div className="preview-example">
                <div className="preview-header">
                  <h3>생성 결과 예시</h3>
                  <span className="preview-badge">SAMPLE</span>
                </div>

                {/* 블로그 예시 */}
                <div className="example-card">
                  <div className="example-card-header">
                    <span className="example-icon">📝</span>
                    <span className="example-title">네이버 블로그</span>
                  </div>
                  <div className="example-card-body">
                    <div className="example-blog-title">성수동 핫플 카페 투어 | 인생샷 명소 BEST 5</div>
                    <div className="example-blog-content">
                      요즘 성수동이 정말 핫하죠! 오늘은 제가 직접 다녀온 성수동 카페 중에서 분위기도 좋고 사진도 예쁘게 나오는 곳들을 소개해 드릴게요...
                    </div>
                    <div className="example-tags">
                      <span className="example-tag">#성수동카페</span>
                      <span className="example-tag">#카페추천</span>
                      <span className="example-tag">#인생샷</span>
                    </div>
                  </div>
                </div>

                {/* SNS 예시 */}
                <div className="example-card">
                  <div className="example-card-header">
                    <span className="example-icon">📱</span>
                    <span className="example-title">인스타그램/페이스북</span>
                  </div>
                  <div className="example-card-body">
                    <div className="example-sns-content">
                      성수동에서 발견한 숨은 보석 같은 카페 ☕️✨ 빈티지한 인테리어에 맛있는 커피까지, 여기 진짜 분위기 대박이에요!
                    </div>
                    <div className="example-tags sns">
                      <span className="example-tag">#성수카페</span>
                      <span className="example-tag">#카페스타그램</span>
                      <span className="example-tag">#서울카페</span>
                      <span className="example-tag">#핫플</span>
                    </div>
                  </div>
                </div>

                {/* AI 분석 예시 */}
                <div className="example-card">
                  <div className="example-card-header">
                    <span className="example-icon">🧠</span>
                    <span className="example-title">AI 분석 결과</span>
                  </div>
                  <div className="example-card-body">
                    <div className="example-analysis">
                      <div className="analysis-row">
                        <span className="analysis-label">주제</span>
                        <span className="analysis-value">카페 리뷰</span>
                      </div>
                      <div className="analysis-row">
                        <span className="analysis-label">카테고리</span>
                        <span className="analysis-value">라이프스타일</span>
                      </div>
                      <div className="analysis-row">
                        <span className="analysis-label">타겟</span>
                        <span className="analysis-value">20-30대 여성</span>
                      </div>
                      <div className="analysis-row">
                        <span className="analysis-label">톤</span>
                        <span className="analysis-value">친근하고 캐주얼</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 품질 점수 예시 */}
                <div className="example-card">
                  <div className="example-card-header">
                    <span className="example-icon">📊</span>
                    <span className="example-title">품질 점수</span>
                  </div>
                  <div className="example-card-body">
                    <div className="example-scores">
                      <div className="score-circle blog">
                        <span className="score-number">99</span>
                        <span className="score-label">블로그</span>
                      </div>
                      <div className="score-circle sns">
                        <span className="score-number">81</span>
                        <span className="score-label">SNS</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="preview-footer">
                  <span>왼쪽에서 내용을 입력하면 위와 같은 형식으로 생성됩니다</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 생성 후: 결과 표시 */}
        {generatedContent && (
          <AgenticContentResult
            result={generatedContent}
            onEdit={handleEdit}
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
