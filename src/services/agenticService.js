import { GoogleGenerativeAI } from '@google/generative-ai';

const API_KEY = process.env.REACT_APP_GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);

// 파일을 base64로 변환하는 헬퍼 함수
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64String = reader.result.split(',')[1];
      resolve(base64String);
    };
    reader.onerror = error => reject(error);
  });
};

// ============================================
// 1. Orchestrator Agent
// ============================================
class OrchestratorAgent {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    this.state = {
      step: 'init',
      attempts: 0,
      maxAttempts: 2,
      analysisResult: null,
      blogContent: null,
      snsContent: null,
      critique: null
    };
  }

  async analyzeInput(textInput, images) {
    console.log('🧠 Orchestrator: 입력 분석 중...');

    const prompt = `당신은 콘텐츠 생성 워크플로우를 조율하는 Orchestrator입니다.
입력을 분석하고 어떤 정보가 필요한지 판단하세요.

입력 정보:
- 텍스트: ${textInput || '없음'}
- 이미지: ${images.length}개

다음 질문에 답하세요:
1. 이 입력으로 어떤 종류의 콘텐츠를 만들 수 있는가?
2. Multi-Modal 분석이 필요한가? (이미지가 있으면 YES)
3. 부족한 정보는 무엇인가?

JSON 형식으로 답변:
{
  "contentType": "카페 홍보 / 제품 소개 / 이벤트 공지 등",
  "needsMultiModalAnalysis": true/false,
  "missingInfo": ["업종", "타겟층" 등],
  "confidence": 0-1
}`;

    const result = await this.model.generateContent(prompt);
    const response = result.response.text();
    const jsonMatch = response.match(/\{[\s\S]*\}/);

    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    return {
      contentType: "일반 콘텐츠",
      needsMultiModalAnalysis: images.length > 0,
      missingInfo: [],
      confidence: 0.5
    };
  }

  async decideNextStep(critiqueResult) {
    console.log('🧠 Orchestrator: 다음 단계 결정 중...');

    const blogScore = critiqueResult.blog.score;
    const snsScore = critiqueResult.sns.score;

    // 둘 다 80점 이상이면 완료
    if (blogScore >= 80 && snsScore >= 80) {
      console.log('✅ Orchestrator: 품질 기준 충족! 완료');
      return { action: 'complete', reason: '품질 기준 달성' };
    }

    // 최대 시도 횟수 초과
    if (this.state.attempts >= this.state.maxAttempts) {
      console.log('⚠️ Orchestrator: 최대 시도 횟수 초과');
      return { action: 'complete', reason: '최대 재시도 횟수 도달' };
    }

    // 개선 필요
    this.state.attempts++;
    console.log(`🔄 Orchestrator: 개선 필요 (시도 ${this.state.attempts}/${this.state.maxAttempts})`);

    return {
      action: 'improve',
      blogFeedback: blogScore < 80 ? critiqueResult.blog.improvements : null,
      snsFeedback: snsScore < 80 ? critiqueResult.sns.improvements : null
    };
  }

  updateState(step, data) {
    this.state.step = step;
    Object.assign(this.state, data);
  }
}

// ============================================
// 2. Multi-Modal Analysis Agent
// ============================================
class MultiModalAnalysisAgent {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  }

  async analyze(textInput, images) {
    console.log('👁️ Multi-Modal Agent: 입력 분석 중...');

    // 이미지를 base64로 변환
    const imageParts = [];
    if (images && images.length > 0) {
      for (const file of images) {
        const base64Data = await fileToBase64(file);
        imageParts.push({
          inlineData: {
            data: base64Data,
            mimeType: file.type
          }
        });
      }
    }

    const prompt = `당신은 입력을 분석하여 콘텐츠 생성에 필요한 정보를 추출하는 전문가입니다.

${textInput ? `텍스트 입력: ${textInput}` : ''}
${images.length > 0 ? `이미지 ${images.length}개 제공됨` : ''}

다음 정보를 추출하세요:
1. 주제 및 카테고리 (예: 카페, 음식점, 제품, 서비스 등)
2. 핵심 키워드 (SEO용, 5-10개)
3. 분위기/감정 (예: 따뜻함, 활기참, 고급스러움 등)
4. 타겟 고객층 추론 (예: 20-30대 여성, 직장인 등)
5. 특징/강조점 (제품/서비스의 특별한 점)
6. 색상/비주얼 (이미지가 있을 경우)
7. 추천 톤앤매너 (친근함, 전문적, 감성적 등)

JSON 형식으로 답변:
{
  "subject": "주제",
  "category": "카테고리",
  "keywords": ["키워드1", "키워드2", ...],
  "mood": "분위기",
  "targetAudience": ["타겟1", "타겟2"],
  "highlights": ["특징1", "특징2"],
  "visualInfo": "비주얼 설명" (이미지 있을 때만),
  "recommendedTone": "톤앤매너",
  "businessType": "업종"
}`;

    const contentParts = imageParts.length > 0 ? [prompt, ...imageParts] : prompt;
    const result = await this.model.generateContent(contentParts);
    const response = result.response.text();

    console.log('👁️ Multi-Modal Agent: 분석 완료');

    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    throw new Error('분석 결과 파싱 실패');
  }
}

// ============================================
// 3. Writer Agent
// ============================================
class WriterAgent {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });
  }

  async generateContent(analysisData, feedback = null) {
    console.log('✍️ Writer Agent: 콘텐츠 생성 중...');

    const improvementInstructions = feedback ? `

**이전 버전의 개선 필요 사항:**
${feedback.blog ? `블로그: ${feedback.blog.join(', ')}` : ''}
${feedback.sns ? `SNS: ${feedback.sns.join(', ')}` : ''}

위 피드백을 반영하여 개선된 버전을 작성하세요.
` : '';

    // 브랜드 분석 정보가 있으면 추가
    const brandGuidelines = analysisData.brandAnalysis ? `

**🎯 브랜드 가이드라인 (기존 블로그 분석 결과):**
- 브랜드 톤: ${analysisData.brandAnalysis.brand_tone}
- 글쓰기 스타일: ${analysisData.brandAnalysis.writing_style}
- 타겟 고객: ${analysisData.brandAnalysis.target_audience}
- 감정적 톤: ${analysisData.brandAnalysis.emotional_tone}
- 행동 유도 스타일: ${analysisData.brandAnalysis.call_to_action_style}
- 콘텐츠 구조: ${analysisData.brandAnalysis.content_structure}

**중요**: 위 브랜드 가이드라인을 반드시 준수하여 일관성 있는 브랜드 톤으로 작성하세요.
` : '';

    const prompt = `당신은 전문 콘텐츠 작가입니다. 분석된 정보를 바탕으로 두 가지 플랫폼용 콘텐츠를 생성하세요.

**분석 정보:**
- 주제: ${analysisData.subject}
- 카테고리: ${analysisData.category}
- 키워드: ${analysisData.keywords.join(', ')}
- 분위기: ${analysisData.mood}
- 타겟: ${analysisData.targetAudience.join(', ')}
- 강조점: ${analysisData.highlights.join(', ')}
- 톤앤매너: ${analysisData.recommendedTone}
- 업종: ${analysisData.businessType}
${analysisData.visualInfo ? `- 비주얼: ${analysisData.visualInfo}` : ''}
${brandGuidelines}
${improvementInstructions}

**작성 요구사항:**

1. **네이버 블로그용** (800-1500자)
   - SEO 최적화 (키워드 자연스럽게 포함)
   - 소제목 사용 (##, ###)
   - 읽기 쉬운 구조
   - 정보성과 감성 균형
   - **키워드는 절대 볼드 처리하지 말 것**

2. **인스타그램/페이스북용** (150-300자)
   - 짧고 임팩트 있게
   - 감성적 어필
   - 이모지 활용
   - CTA(행동 유도) 포함
   - 해시태그 최적화

**응답 형식 (JSON):**
{
  "blog": {
    "title": "SEO 최적화된 제목",
    "content": "블로그 본문 (마크다운)",
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5", "태그6", "태그7"]
  },
  "sns": {
    "content": "SNS 본문 (이모지 포함)",
    "tags": ["해시태그1", "해시태그2", "해시태그3", "해시태그4", "해시태그5"]
  }
}

**중요:**
- 블로그 태그는 최소 7개, 최대 10개
- SNS 태그는 최소 5개, 최대 15개
- 각 플랫폼의 특성에 맞는 길이와 톤 유지
- JSON만 응답하세요`;

    const result = await this.model.generateContent(prompt);
    const response = result.response.text();

    console.log('✍️ Writer Agent: 생성 완료');

    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    throw new Error('콘텐츠 생성 결과 파싱 실패');
  }
}

// ============================================
// 4. Critic Agent
// ============================================
class CriticAgent {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  }

  async critique(blogContent, snsContent, analysisData) {
    console.log('🔍 Critic Agent: 콘텐츠 평가 중...');

    const prompt = `당신은 콘텐츠 품질을 평가하는 전문 비평가입니다.

**원본 분석 정보:**
- 주제: ${analysisData.subject}
- 키워드: ${analysisData.keywords.join(', ')}
- 타겟: ${analysisData.targetAudience.join(', ')}

**블로그 콘텐츠:**
제목: ${blogContent.title}
본문: ${blogContent.content}
태그: ${blogContent.tags.join(', ')}

**SNS 콘텐츠:**
본문: ${snsContent.content}
태그: ${snsContent.tags.join(', ')}

**평가 기준:**
1. SEO 최적화 (키워드 포함, 자연스러움)
2. 플랫폼 적합성 (길이, 톤)
3. 타겟 적합성
4. 가독성
5. 감성/공감
6. CTA 포함 여부 (SNS)
7. 태그 품질

각 콘텐츠를 0-100점으로 평가하고, 개선점을 제시하세요.
**80점 이상이면 통과, 미만이면 개선 필요**

JSON 형식:
{
  "blog": {
    "score": 85,
    "strengths": ["장점1", "장점2"],
    "weaknesses": ["약점1", "약점2"],
    "improvements": ["개선사항1", "개선사항2"],
    "seoScore": 90,
    "readabilityScore": 85
  },
  "sns": {
    "score": 88,
    "strengths": ["장점1", "장점2"],
    "weaknesses": ["약점1"],
    "improvements": ["개선사항1"],
    "engagementScore": 90,
    "hashtagScore": 85
  },
  "overallRecommendation": "통과/개선필요"
}`;

    const result = await this.model.generateContent(prompt);
    const response = result.response.text();

    console.log('🔍 Critic Agent: 평가 완료');

    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    throw new Error('평가 결과 파싱 실패');
  }
}

// ============================================
// Main Agentic Workflow
// ============================================
export const generateAgenticContent = async ({ textInput, images = [] }, onProgress) => {
  try {
    // Agent 초기화
    const orchestrator = new OrchestratorAgent();
    const multiModalAgent = new MultiModalAnalysisAgent();
    const writerAgent = new WriterAgent();
    const criticAgent = new CriticAgent();

    // 진행 상황 업데이트 함수
    const updateProgress = (message, step) => {
      if (onProgress) {
        onProgress({ message, step });
      }
      console.log(`📊 Progress: ${message}`);
    };

    // 0단계: 브랜드 분석 정보 가져오기 (있다면)
    let brandAnalysis = null;
    try {
      const response = await fetch('/api/blog/brand-analysis', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        brandAnalysis = await response.json();
        console.log('✅ 브랜드 분석 정보 로드:', brandAnalysis);
      }
    } catch (error) {
      console.log('ℹ️ 브랜드 분석 정보 없음 (선택 사항)');
    }

    // 1단계: Orchestrator가 입력 분석
    updateProgress('입력 분석 중...', 'analyzing');
    const inputAnalysis = await orchestrator.analyzeInput(textInput, images);
    console.log('입력 분석 결과:', inputAnalysis);

    // 2단계: Multi-Modal 분석
    updateProgress('콘텐츠 정보 추출 중...', 'extracting');
    const analysisResult = await multiModalAgent.analyze(textInput, images);

    // 브랜드 분석 정보가 있으면 통합
    if (brandAnalysis?.analysis) {
      analysisResult.brandAnalysis = brandAnalysis.analysis;
      console.log('✅ 브랜드 분석 정보 통합 완료');
    }

    orchestrator.updateState('analyzed', { analysisResult });
    console.log('분석 결과:', analysisResult);

    let finalBlogContent = null;
    let finalSnsContent = null;
    let critiqueResult = null;

    // 3단계: Writer가 콘텐츠 생성 (반복 가능)
    while (orchestrator.state.attempts <= orchestrator.state.maxAttempts) {
      updateProgress(
        orchestrator.state.attempts === 0 ? '콘텐츠 생성 중...' : `콘텐츠 개선 중... (${orchestrator.state.attempts}차)`,
        'writing'
      );

      const feedback = orchestrator.state.attempts > 0 ? {
        blog: critiqueResult?.blog.improvements,
        sns: critiqueResult?.sns.improvements
      } : null;

      const content = await writerAgent.generateContent(analysisResult, feedback);
      finalBlogContent = content.blog;
      finalSnsContent = content.sns;

      orchestrator.updateState('written', { blogContent: content.blog, snsContent: content.sns });

      // 4단계: Critic이 평가
      updateProgress('콘텐츠 품질 검증 중...', 'critiquing');
      critiqueResult = await criticAgent.critique(content.blog, content.sns, analysisResult);
      orchestrator.updateState('critiqued', { critique: critiqueResult });

      console.log('평가 결과:', critiqueResult);

      // 5단계: Orchestrator가 다음 단계 결정
      const decision = await orchestrator.decideNextStep(critiqueResult);

      if (decision.action === 'complete') {
        console.log(`✅ 완료: ${decision.reason}`);
        break;
      }
    }

    updateProgress('완료!', 'complete');

    return {
      success: true,
      blog: finalBlogContent,
      sns: finalSnsContent,
      analysis: analysisResult,
      critique: critiqueResult,
      metadata: {
        attempts: orchestrator.state.attempts,
        finalScores: {
          blog: critiqueResult.blog.score,
          sns: critiqueResult.sns.score
        }
      }
    };

  } catch (error) {
    console.error('❌ Agentic 콘텐츠 생성 오류:', error);
    throw error;
  }
};
