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

// 파일을 data URL로 변환하는 헬퍼 함수 (미리보기용)
const fileToDataURL = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
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

  async generateContent(analysisData, feedback = null, imageCount = 0) {
    console.log('✍️ Writer Agent: 콘텐츠 생성 중...');

    const improvementInstructions = feedback ? `

**이전 버전의 개선 필요 사항:**
${feedback.blog ? `블로그: ${feedback.blog.join(', ')}` : ''}
${feedback.sns ? `SNS: ${feedback.sns.join(', ')}` : ''}

위 피드백을 반영하여 개선된 버전을 작성하세요.
` : '';

    // 이미지 삽입 지시문
    const imageInstructions = imageCount > 0 ? `

**이미지 삽입 안내:**
- 사용자가 ${imageCount}개의 이미지를 업로드했습니다.
- 블로그 본문 중 적절한 위치에 이미지 마커를 삽입하세요.
- 이미지 마커 형식: [IMAGE_1], [IMAGE_2], ... (숫자는 1부터 시작)
- 이미지는 글의 맥락에 맞는 곳에 자연스럽게 배치하세요.
- 예: 제품 설명 후, 분위기 묘사 후, 결론 전 등
- 첫 번째 이미지는 도입부 또는 주요 내용 설명 후에 배치하세요.
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

    const prompt = `당신은 10년 경력의 전문 콘텐츠 마케터입니다.
이전 버전의 콘텐츠가 품질 기준에 미달했습니다. 피드백을 반영하여 **확실히 개선된** 버전을 작성하세요.

═══════════════════════════════════════
📌 분석 정보
═══════════════════════════════════════
- 주제: ${analysisData.subject}
- 카테고리: ${analysisData.category}
- 키워드: ${analysisData.keywords.join(', ')}
- 분위기: ${analysisData.mood}
- 타겟: ${analysisData.targetAudience.join(', ')}
- 강조점: ${analysisData.highlights.join(', ')}
- 톤앤매너: ${analysisData.recommendedTone}
- 업종: ${analysisData.businessType || '일반'}
${analysisData.visualInfo ? `- 비주얼: ${analysisData.visualInfo}` : ''}
${brandGuidelines}
${improvementInstructions}
${imageInstructions}

═══════════════════════════════════════
🎯 품질 향상 핵심 포인트
═══════════════════════════════════════

**반드시 개선해야 할 것:**
1. **구체성 강화**: 추상적 표현 → 구체적 묘사, 숫자, 사례
2. **독자 가치**: 읽는 사람이 얻어갈 수 있는 실질적 정보/팁 포함
3. **자연스러운 흐름**: 서론-본론-결론, 문단 간 매끄러운 연결
4. **과장 제거**: "최고", "완벽" 등 근거 없는 표현 삭제

**절대 하지 말 것:**
- 키워드 과다 반복
- 의미 없는 이모지 남발
- 뻔하고 공허한 문구

═══════════════════════════════════════
📝 플랫폼별 요구사항
═══════════════════════════════════════

**[네이버 블로그] (800-1500자)**
- 제목: 검색 키워드 + 클릭 유도 요소
- 도입: 독자 공감 또는 문제 제기
- 본문: 소제목(##)으로 구분, 각 섹션에 실질적 정보
- 마무리: 핵심 요약 + 행동 유도
- **키워드 볼드 처리 금지**

**[Instagram/Facebook] (150-300자)**
- 첫 줄: 스크롤 멈추게 하는 훅
- 이모지: 3-5개만 포인트로
- CTA: 구체적 행동 유도

**[X] (280자 이내)**
- 임팩트 있는 핵심 메시지
- 해시태그 2-3개만

**[Threads] (500자 이내)**
- 대화체로 친근하게
- 스토리텔링 + 인사이트

═══════════════════════════════════════
📤 출력 형식 (JSON)
═══════════════════════════════════════
{
  "blog": {
    "title": "개선된 SEO 최적화 제목",
    "content": "개선된 블로그 본문 (마크다운)",
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5", "태그6", "태그7"]
  },
  "sns": {
    "content": "개선된 SNS 본문",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3", "#해시태그4", "#해시태그5"]
  },
  "x": {
    "content": "개선된 X 본문 (280자 이내)",
    "tags": ["#해시태그1", "#해시태그2"]
  },
  "threads": {
    "content": "개선된 Threads 본문 (500자 이내)",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3"]
  }
}

JSON만 응답하세요.`;

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

  async critique(blogContent, snsContent, analysisData, xContent = null, threadsContent = null) {
    console.log('🔍 Critic Agent: 콘텐츠 평가 중...');

    const xSection = xContent ? `
**X 콘텐츠:**
본문: ${xContent.content}
태그: ${xContent.tags?.join(', ') || ''}
` : '';

    const threadsSection = threadsContent ? `
**Threads 콘텐츠:**
본문: ${threadsContent.content}
태그: ${threadsContent.tags?.join(', ') || ''}
` : '';

    const prompt = `당신은 엄격한 콘텐츠 품질 평가 전문가입니다.
**실제 사용자들이 읽고 싶어할 가치 있는 콘텐츠인지** 냉정하게 평가하세요.

═══════════════════════════════════════
📌 원본 분석 정보
═══════════════════════════════════════
- 주제: ${analysisData.subject}
- 키워드: ${analysisData.keywords.join(', ')}
- 타겟: ${analysisData.targetAudience.join(', ')}

═══════════════════════════════════════
📝 평가 대상 콘텐츠
═══════════════════════════════════════

**[블로그]**
제목: ${blogContent.title}
본문: ${blogContent.content}
태그: ${blogContent.tags.join(', ')}

**[SNS (인스타/페이스북)]**
본문: ${snsContent.content}
태그: ${snsContent.tags.join(', ')}
${xSection}${threadsSection}

═══════════════════════════════════════
🔍 상세 평가 기준 (각 항목 0-20점)
═══════════════════════════════════════

**1. 독자 가치 (0-20점)** ⭐ 가장 중요
- 읽는 사람이 얻어가는 실질적 정보/팁/인사이트가 있는가?
- 단순 홍보/정보 나열이 아닌 문제 해결 또는 새로운 관점 제공?
- 15점 미만: 공허하고 뻔한 내용
- 15점 이상: 독자에게 도움이 되는 구체적 가치

**2. 구체성 (0-20점)**
- 추상적 표현(맛있다, 좋다, 최고) 대신 구체적 묘사?
- 숫자, 데이터, 실제 사례 포함?
- 15점 미만: 추상적이고 모호한 표현 다수
- 15점 이상: 생생하고 구체적인 내용

**3. 신뢰성 (0-20점)**
- 과장/허위 표현 없는가? ("최고", "완벽", "혁신적" 남발?)
- 주장에 근거가 있는가?
- 15점 미만: 과장되거나 신뢰하기 어려움
- 15점 이상: 믿을 수 있고 정직한 톤

**4. 플랫폼 최적화 (0-20점)**
- 각 플랫폼 특성에 맞는 길이/톤/형식?
- SEO(블로그), 훅(SNS), 임팩트(X), 대화체(Threads)?
- 15점 미만: 플랫폼 특성 무시
- 15점 이상: 플랫폼에 최적화됨

**5. 가독성/흐름 (0-20점)**
- 서론-본론-결론 구조?
- 문단 간 자연스러운 연결?
- 읽기 쉬운 문장 길이?
- 15점 미만: 읽기 불편하거나 구조 없음
- 15점 이상: 술술 읽히는 자연스러운 흐름

═══════════════════════════════════════
⚠️ 자동 감점 사항
═══════════════════════════════════════
- 키워드 과다 반복: -10점
- "최고/완벽/혁신적" 등 근거 없는 과장: -5점씩
- 의미 없는 이모지 남발 (5개 초과): -5점
- 복사-붙여넣기 같은 천편일률적 문구: -10점

═══════════════════════════════════════
📤 평가 결과 (JSON)
═══════════════════════════════════════
{
  "blog": {
    "score": 총점(0-100),
    "breakdown": {
      "readerValue": 0-20,
      "specificity": 0-20,
      "credibility": 0-20,
      "platformOptimization": 0-20,
      "readability": 0-20
    },
    "strengths": ["구체적 장점"],
    "weaknesses": ["구체적 문제점"],
    "improvements": ["구체적 개선 방법"],
    "seoScore": 0-100,
    "readabilityScore": 0-100
  },
  "sns": {
    "score": 총점(0-100),
    "breakdown": {
      "readerValue": 0-20,
      "specificity": 0-20,
      "credibility": 0-20,
      "platformOptimization": 0-20,
      "readability": 0-20
    },
    "strengths": ["구체적 장점"],
    "weaknesses": ["구체적 문제점"],
    "improvements": ["구체적 개선 방법"],
    "engagementScore": 0-100,
    "hashtagScore": 0-100
  },
  "x": {
    "score": 총점(0-100),
    "strengths": ["장점"],
    "weaknesses": ["문제점"],
    "improvements": ["개선 방법"]
  },
  "threads": {
    "score": 총점(0-100),
    "strengths": ["장점"],
    "weaknesses": ["문제점"],
    "improvements": ["개선 방법"]
  },
  "overallRecommendation": "통과/개선필요"
}

**80점 이상 = 통과, 미만 = 개선 필요**
엄격하게 평가하세요. 평범한 콘텐츠는 70점대입니다.`;

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
// Main Agentic Workflow (with Quality Check)
// ============================================
export const generateAgenticContent = async ({ textInput, images = [], styleTone = '' }, onProgress) => {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    const criticAgent = new CriticAgent();
    const writerAgent = new WriterAgent();
    const MAX_ATTEMPTS = 2;

    const updateProgress = (message, step) => {
      if (onProgress) {
        onProgress({ message, step });
      }
    };

    updateProgress('콘텐츠 생성 중...', 'writing');

    // 이미지 변환 (병렬로 미리 시작)
    const imageDataUrlsPromise = Promise.all(
      (images || []).map(file => fileToDataURL(file))
    );

    // 이미지를 base64로 변환
    const imageParts = [];
    if (images && images.length > 0) {
      for (const file of images) {
        const base64Data = await fileToBase64(file);
        imageParts.push({
          inlineData: { data: base64Data, mimeType: file.type }
        });
      }
    }

    // 스타일 지시문
    const styleInstruction = styleTone
      ? `\n**글쓰기 스타일**: ${styleTone}\n위 스타일을 반드시 적용하여 작성하세요.\n`
      : '';

    // ⚡ 단일 API 호출로 분석 + 생성 동시 처리 (강화된 프롬프트 엔지니어링)
    const prompt = `당신은 10년 경력의 전문 콘텐츠 마케터이자 SEO 전문가입니다.
사용자의 입력을 바탕으로 **실제로 사람들이 읽고 싶어하는, 가치 있는 콘텐츠**를 생성하세요.

═══════════════════════════════════════
📌 사용자 입력
═══════════════════════════════════════
주제/키워드: ${textInput || '이미지 기반 콘텐츠'}
첨부 이미지: ${images.length}개
${styleInstruction}

═══════════════════════════════════════
🎯 콘텐츠 생성 핵심 원칙
═══════════════════════════════════════

**1. 독자 중심 사고**
- "이 글을 읽는 사람이 무엇을 얻어갈 수 있는가?"를 항상 고민
- 단순 정보 나열 ❌ → 독자의 문제 해결 또는 인사이트 제공 ✅
- 뻔한 내용 ❌ → 구체적인 팁, 경험, 사례 ✅

**2. 구체성과 신뢰성**
- 추상적 표현 ❌ (예: "맛있다", "좋다", "최고다")
- 구체적 묘사 ✅ (예: "첫 입에 느껴지는 바삭한 식감과 고소한 참기름 향")
- 가능하면 숫자, 데이터, 구체적 사례 포함
- 근거 없는 과장 금지

**3. 자연스러운 흐름**
- 서론-본론-결론의 명확한 구조
- 문단 간 자연스러운 연결 (전환어 활용)
- 읽기 쉬운 문장 (한 문장은 2줄 이내)

**4. 플랫폼별 최적화**
- 각 플랫폼 사용자의 기대와 행동 패턴 고려
- 플랫폼 알고리즘 특성 반영

═══════════════════════════════════════
📝 플랫폼별 상세 요구사항
═══════════════════════════════════════

**[네이버 블로그] (800-1500자)**
- 제목: 검색 키워드 포함 + 클릭 유도 (호기심, 숫자, 구체적 혜택)
- 도입부: 독자의 공감을 얻는 문제 제기 또는 상황 설정
- 본문:
  * 핵심 정보를 소제목(##)으로 구분
  * 각 섹션마다 실질적인 정보 또는 팁 제공
  * 개인 경험이나 구체적 사례 포함
- 마무리: 핵심 요약 + 독자 행동 유도
- 태그: 검색량 높은 키워드 + 롱테일 키워드 조합${images.length > 0 ? `
- 이미지 배치: [IMAGE_1]~[IMAGE_${images.length}] 마커를 내용과 연관된 위치에 삽입` : ''}

**[Instagram/Facebook] (150-300자)**
- 첫 줄: 스크롤을 멈추게 하는 훅 (질문, 충격적 사실, 공감 포인트)
- 본문: 핵심 메시지 1-2개에 집중, 스토리텔링
- 이모지: 과하지 않게 포인트로 활용 (3-5개)
- CTA: 구체적인 행동 유도 (댓글, 저장, 공유)
- 해시태그: 대중적 태그 + 니치 태그 조합

**[X/Twitter] (280자 이내)**
- 임팩트 있는 한 줄 메시지 또는 인사이트
- 트렌드/밈 활용 가능
- 리트윗하고 싶은 가치 있는 내용
- 해시태그는 2-3개만 (과하면 스팸처럼 보임)

**[Threads] (500자 이내)**
- 인스타보다 대화체, 생각을 나누는 느낌
- 의견이나 관점 공유
- 독자와 대화하듯 친근하게
- 스토리텔링 + 인사이트

═══════════════════════════════════════
⚠️ 절대 하지 말아야 할 것
═══════════════════════════════════════
- 키워드 과다 반복 (스팸처럼 보임)
- 근거 없는 "최고", "완벽", "혁신적" 등의 과장
- 복사-붙여넣기 같은 천편일률적인 문구
- 의미 없는 이모지 남발
- 독자에게 도움이 되지 않는 공허한 내용

═══════════════════════════════════════
📤 출력 형식 (JSON)
═══════════════════════════════════════
{
  "analysis": {
    "subject": "핵심 주제",
    "category": "카테고리 (음식/뷰티/여행/IT/라이프스타일/비즈니스 등)",
    "keywords": ["SEO 메인키워드", "연관키워드1", "연관키워드2", "롱테일키워드"],
    "mood": "콘텐츠 분위기",
    "targetAudience": ["주요 타겟층 구체적으로"],
    "highlights": ["차별화 포인트", "핵심 가치"],
    "recommendedTone": "권장 톤앤매너"
  },
  "blog": {
    "title": "클릭하고 싶은 SEO 최적화 제목",
    "content": "가치 있는 블로그 본문 (마크다운 형식)",
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5", "태그6", "태그7"]
  },
  "sns": {
    "content": "Instagram/Facebook용 매력적인 본문",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3", "#해시태그4", "#해시태그5"]
  },
  "x": {
    "content": "X용 임팩트 있는 본문 (280자 이내)",
    "tags": ["#해시태그1", "#해시태그2"]
  },
  "threads": {
    "content": "Threads용 대화체 본문 (500자 이내)",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3"]
  }
}

중요: JSON만 응답하세요.`;

    const contentParts = imageParts.length > 0 ? [prompt, ...imageParts] : prompt;
    const result = await model.generateContent(contentParts);
    const response = result.response.text();

    const jsonMatch = response.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('응답 파싱 실패');
    }

    let content = JSON.parse(jsonMatch[0]);
    const imageDataUrls = await imageDataUrlsPromise;

    // 디버깅: 파싱된 콘텐츠 확인
    console.log('📦 파싱된 콘텐츠 키:', Object.keys(content));
    console.log('📦 X 콘텐츠:', content.x ? '있음' : '없음', content.x);
    console.log('📦 Threads 콘텐츠:', content.threads ? '있음' : '없음', content.threads);

    // 분석 데이터 기본값 설정
    const analysisData = content.analysis || {
      subject: textInput,
      category: '일반',
      keywords: [],
      mood: '친근함',
      targetAudience: ['일반'],
      highlights: [],
      recommendedTone: '친근함'
    };

    // 🔍 품질 검사 활성화
    updateProgress('품질 검사 중...', 'critiquing');
    let critique = await criticAgent.critique(content.blog, content.sns, analysisData, content.x, content.threads);
    let attempts = 1;

    console.log(`🔍 품질 검사 결과 - 블로그: ${critique.blog?.score}점, SNS: ${critique.sns?.score}점, X: ${critique.x?.score}점, Threads: ${critique.threads?.score}점`);

    // 80점 미만이면 재생성 (최대 MAX_ATTEMPTS 회)
    while ((critique.blog.score < 80 || critique.sns.score < 80) && attempts < MAX_ATTEMPTS) {
      attempts++;
      console.log(`🔄 품질 미달로 재생성 중... (시도 ${attempts}/${MAX_ATTEMPTS})`);
      updateProgress(`품질 개선 중... (시도 ${attempts}/${MAX_ATTEMPTS})`, 'writing');

      // 피드백을 반영하여 재생성
      const feedback = {
        blog: critique.blog.score < 80 ? critique.blog.improvements : null,
        sns: critique.sns.score < 80 ? critique.sns.improvements : null
      };

      const improvedContent = await writerAgent.generateContent(analysisData, feedback, images.length);

      // 기존 콘텐츠 업데이트
      if (feedback.blog) {
        content.blog = improvedContent.blog;
      }
      if (feedback.sns) {
        content.sns = improvedContent.sns;
      }
      // X와 Threads도 업데이트
      if (improvedContent.x) {
        content.x = improvedContent.x;
      }
      if (improvedContent.threads) {
        content.threads = improvedContent.threads;
      }

      // 다시 품질 검사
      updateProgress('재검사 중...', 'critiquing');
      critique = await criticAgent.critique(content.blog, content.sns, analysisData, content.x, content.threads);
      console.log(`🔍 재검사 결과 - 블로그: ${critique.blog?.score}점, SNS: ${critique.sns?.score}점`);
    }

    updateProgress('완료!', 'complete');

    return {
      success: true,
      blog: content.blog,
      sns: content.sns,
      x: content.x,
      threads: content.threads,
      analysis: analysisData,
      critique: critique,
      uploadedImages: imageDataUrls,
      metadata: {
        attempts: attempts,
        finalScores: {
          blog: critique.blog?.score,
          sns: critique.sns?.score,
          x: critique.x?.score,
          threads: critique.threads?.score
        }
      }
    };

  } catch (error) {
    console.error('❌ 콘텐츠 생성 오류:', error);
    throw error;
  }
};
