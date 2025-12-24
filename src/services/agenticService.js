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

// JSON 문자열 정제 함수 - AI 응답에서 발생하는 일반적인 JSON 오류 수정
const cleanJsonString = (jsonStr) => {
  let cleaned = jsonStr;

  // 0. 마크다운 코드 블록 제거
  cleaned = cleaned.replace(/```json\s*/g, '').replace(/```\s*/g, '');

  // 1. JSON 문자열 내의 이스케이프되지 않은 줄바꿈을 \\n으로 변환
  // 문자열 값 내부만 처리 (키는 제외)
  cleaned = cleaned.replace(/"([^"\\]*(?:\\.[^"\\]*)*)"/g, (_, content) => {
    // 실제 줄바꿈을 이스케이프된 줄바꿈으로 변환
    const fixedContent = content
      .replace(/\r\n/g, '\\n')
      .replace(/\r/g, '\\n')
      .replace(/\n/g, '\\n')
      .replace(/\t/g, '\\t');
    return `"${fixedContent}"`;
  });

  // 2. 제어 문자 제거 (줄바꿈, 탭 제외)
  cleaned = cleaned.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

  // 3. 마지막 쉼표 제거 (trailing comma)
  cleaned = cleaned.replace(/,(\s*[}\]])/g, '$1');

  // 4. 이스케이프되지 않은 따옴표 수정 (문자열 내부)
  // 예: "내용: "이것"입니다" -> "내용: \"이것\"입니다"
  cleaned = cleaned.replace(/"([^"]*)":\s*"([^"]*)"/g, (_, key, value) => {
    // 값 내부의 이스케이프되지 않은 따옴표를 이스케이프
    const escapedValue = value.replace(/(?<!\\)"/g, '\\"');
    return `"${key}": "${escapedValue}"`;
  });

  return cleaned;
};

// 네트워크 오류 시 재시도하는 래퍼 함수
const withRetry = async (fn, maxRetries = 3, delayMs = 1000) => {
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const isNetworkError =
        error.message?.includes('Failed to fetch') ||
        error.message?.includes('network') ||
        error.message?.includes('NETWORK') ||
        error.message?.includes('timeout') ||
        error.message?.includes('ERR_');

      if (isNetworkError && attempt < maxRetries) {
        console.warn(`네트워크 오류, 재시도 중... (${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
        continue;
      }
      throw error;
    }
  }
  throw lastError;
};

// 불완전한 JSON 배열 수정 함수
const fixIncompleteArray = (jsonStr) => {
  let result = jsonStr;

  // 불완전한 문자열 처리 - 문자열이 중간에 끊긴 경우
  // 마지막으로 올바르게 닫힌 문자열 위치 찾기
  let inString = false;
  let lastValidPos = 0;
  let escapeNext = false;

  for (let i = 0; i < result.length; i++) {
    const char = result[i];

    if (escapeNext) {
      escapeNext = false;
      continue;
    }

    if (char === '\\') {
      escapeNext = true;
      continue;
    }

    if (char === '"') {
      if (!inString) {
        inString = true;
      } else {
        inString = false;
        // 문자열이 제대로 닫혔을 때의 위치 기록
        lastValidPos = i;
      }
    }

    // 문자열 밖에서 구조적 문자가 나오면 유효 위치 업데이트
    if (!inString && (char === ',' || char === ':' || char === '{' || char === '}' || char === '[' || char === ']')) {
      lastValidPos = i;
    }
  }

  // 문자열이 열린 채로 끝났으면 마지막 유효 위치까지만 사용
  if (inString && lastValidPos > 0) {
    // 마지막 유효 위치에서 가장 가까운 쉼표나 여는 괄호 찾기
    const beforeValid = result.substring(0, lastValidPos + 1);
    const lastCommaOrBrace = Math.max(beforeValid.lastIndexOf(','), beforeValid.lastIndexOf('{'), beforeValid.lastIndexOf('['));
    if (lastCommaOrBrace > 0) {
      result = result.substring(0, lastCommaOrBrace + 1);
    }
  }

  // 마지막 따옴표 이후 확인
  const lastQuoteIndex = result.lastIndexOf('"');
  const afterLastQuote = result.substring(lastQuoteIndex + 1);

  // 마지막 따옴표 이후에 닫는 괄호만 있어야 정상
  if (!/^[\s\],}:]*$/.test(afterLastQuote) && lastQuoteIndex > 0) {
    // 불완전한 문자열이 있음 - 마지막 완전한 속성까지만 사용
    // 마지막으로 제대로 된 key-value 쌍 찾기
    const propPattern = /"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\{[^}]*\}|\[[^\]]*\])/g;
    let lastMatch = null;
    let match;
    while ((match = propPattern.exec(result)) !== null) {
      lastMatch = match;
    }

    if (lastMatch) {
      const endPos = lastMatch.index + lastMatch[0].length;
      result = result.substring(0, endPos);
    } else {
      // 정규식 매칭 실패 시 마지막 쉼표까지 자르기
      const lastCommaIndex = result.lastIndexOf(',');
      if (lastCommaIndex > 0) {
        result = result.substring(0, lastCommaIndex);
      }
    }
  }

  // 다시 괄호 수 세기
  const finalOpenBrackets = (result.match(/\[/g) || []).length;
  const finalCloseBrackets = (result.match(/\]/g) || []).length;
  const finalOpenBraces = (result.match(/\{/g) || []).length;
  const finalCloseBraces = (result.match(/\}/g) || []).length;

  // 닫는 대괄호 부족하면 추가
  for (let i = 0; i < finalOpenBrackets - finalCloseBrackets; i++) {
    result += ']';
  }

  // 닫는 중괄호 부족하면 추가
  for (let i = 0; i < finalOpenBraces - finalCloseBraces; i++) {
    result += '}';
  }

  return result;
};

// 안전한 JSON 파싱 함수
// silent: true이면 콘솔 에러 출력 안함
const safeJsonParse = (jsonStr, silent = false) => {
  // 빈 문자열 또는 null/undefined 처리
  if (!jsonStr || typeof jsonStr !== 'string' || jsonStr.trim() === '') {
    throw new Error('빈 응답');
  }

  // 1차 시도: JSON 부분 추출 후 직접 파싱
  const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('JSON 형식을 찾을 수 없음');
  }

  let jsonPart = jsonMatch[0];

  try {
    return JSON.parse(jsonPart);
  } catch (e1) {
    // 2차 시도: 정제 후 파싱
    try {
      const cleaned = cleanJsonString(jsonPart);
      return JSON.parse(cleaned);
    } catch (e2) {
      // 3차 시도: 문자열 값 내 줄바꿈 강제 처리
      try {
        let fixed = jsonPart;
        // 모든 실제 줄바꿈을 이스케이프
        fixed = fixed.replace(/\n/g, '\\n').replace(/\r/g, '\\r');
        return JSON.parse(fixed);
      } catch (e3) {
        // 4차 시도: 불완전한 배열/객체 수정
        try {
          let fixed = jsonPart;
          fixed = fixed.replace(/[\x00-\x1F\x7F]/g, ' ');
          fixed = fixIncompleteArray(fixed);
          fixed = cleanJsonString(fixed);
          return JSON.parse(fixed);
        } catch (e4) {
          // 5차 시도: 문자열 내 특수문자 완전 제거
          try {
            let aggressive = jsonPart;
            // 모든 제어 문자와 문제 되는 문자 제거
            aggressive = aggressive.replace(/[\x00-\x1F\x7F]/g, ' ');
            // 연속 공백 정리
            aggressive = aggressive.replace(/\s+/g, ' ');
            // 불완전한 배열/객체 수정
            aggressive = fixIncompleteArray(aggressive);
            aggressive = cleanJsonString(aggressive);
            return JSON.parse(aggressive);
          } catch (e5) {
            // 6차 시도: 잘린 문자열 값 복구
            try {
              let truncated = jsonPart;
              // 제어 문자 제거
              truncated = truncated.replace(/[\x00-\x1F\x7F]/g, ' ');

              // 잘린 문자열 찾아서 닫기
              // 열린 따옴표 찾기 (이스케이프되지 않은 것만)
              let inStr = false;
              let lastStrStart = -1;
              let escNext = false;

              for (let i = 0; i < truncated.length; i++) {
                if (escNext) {
                  escNext = false;
                  continue;
                }
                if (truncated[i] === '\\') {
                  escNext = true;
                  continue;
                }
                if (truncated[i] === '"') {
                  if (!inStr) {
                    inStr = true;
                    lastStrStart = i;
                  } else {
                    inStr = false;
                  }
                }
              }

              // 문자열이 열린 채로 끝났으면 닫아주기
              if (inStr && lastStrStart >= 0) {
                // 마지막 열린 문자열 앞의 마지막 완전한 속성까지만 사용
                const beforeStr = truncated.substring(0, lastStrStart);
                const lastComma = beforeStr.lastIndexOf(',');
                const cutPoint = Math.max(lastComma, 0);
                if (cutPoint > 0) {
                  truncated = truncated.substring(0, cutPoint);
                } else {
                  // 잘린 문자열에 따옴표 추가
                  truncated = truncated + '"';
                }
              }

              truncated = fixIncompleteArray(truncated);
              return JSON.parse(truncated);
            } catch (e6) {
              if (!silent) {
                console.error('모든 JSON 파싱 시도 실패:', e6.message);
                console.error('원본 JSON (처음 500자):', jsonPart.substring(0, 500));
              }
              throw e6;
            }
          }
        }
      }
    }
  }
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

    const result = await withRetry(() => this.model.generateContent(prompt));
    const response = result.response.text();

    try {
      return safeJsonParse(response);
    } catch {
      return {
        contentType: "일반 콘텐츠",
        needsMultiModalAnalysis: images.length > 0,
        missingInfo: [],
        confidence: 0.5
      };
    }
  }

  async decideNextStep(critiqueResult) {

    const blogScore = critiqueResult.blog.score;
    const snsScore = critiqueResult.sns.score;

    // 둘 다 80점 이상이면 완료
    if (blogScore >= 80 && snsScore >= 80) {
      return { action: 'complete', reason: '품질 기준 달성' };
    }

    // 최대 시도 횟수 초과
    if (this.state.attempts >= this.state.maxAttempts) {
      return { action: 'complete', reason: '최대 재시도 횟수 도달' };
    }

    // 개선 필요
    this.state.attempts++;

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
    const result = await withRetry(() => this.model.generateContent(contentParts));
    const response = result.response.text();

    return safeJsonParse(response);
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
5. **줄바꿈**: 문장이 끝나면(마침표, 물음표, 느낌표 뒤) 반드시 줄바꿈(\\n)을 삽입하여 가독성을 높이세요

**절대 하지 말 것:**
- 키워드 과다 반복
- 의미 없는 이모지 남발
- 뻔하고 공허한 문구

═══════════════════════════════════════
📝 플랫폼별 요구사항
═══════════════════════════════════════

**[네이버 블로그] (800-1500자)**
- 제목: 검색 키워드 포함 + 클릭 유도 (숫자, 질문, 비교 활용)
  · 예: "OO 3가지 비교해봤습니다", "OO 전에 꼭 알아야 할 것"
- 도입 (2-3문장): 독자 공감 유도 또는 문제 제기로 시작
  · "저도 처음엔 몰랐는데요", "이거 고민되시죠?"
- 본문 구조:
  · 소제목(##)으로 섹션 구분 (3-5개)
  · 각 섹션마다 실질적 정보, 경험담, 구체적 팁 제공
  · 나열식 X → 스토리텔링 형식으로 자연스럽게
  · 개인 경험과 솔직한 의견 포함 (신뢰감 상승)
- 마무리: 핵심 요약 1-2줄 + 독자 행동 유도
- 피할 것: 키워드 과다 삽입, 볼드 남발, 광고성 문구, 뻔한 정보
- **키워드 볼드 처리 금지**

**[Instagram/Facebook] (150-300자)**
- 첫 줄이 생명: 스크롤 멈추게 하는 훅 (질문/공감/충격/호기심)
- 본문: 진정성 있는 스토리텔링, 독자와 대화하듯 작성
- 구조: 훅 → 핵심 메시지 → 가치 제공 → CTA
- 이모지: 문단 구분용 + 포인트로 3-5개 (과하면 스팸처럼 보임)
- CTA: 구체적 행동 유도 ("댓글로 알려주세요", "저장해두세요")
- **마크다운 금지**: **굵게**, *기울임* 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 피할 것: 딱딱한 홍보문구, 과장된 표현, 뻔한 내용
- 해시태그: 대중적 태그 + 니치 태그 조합 (5개)

**[X] (280자 이내)**
- 첫 문장이 곧 전부: 스크롤 멈추게 하는 강력한 훅
- 형식: 인사이트/의견/질문/반전 중 하나 선택
- 짧고 임팩트 있게, 단정적인 어조로
- "~입니다", "~해요" 같은 어미 피하고 "~다", "~임" 등 간결체 사용
- **마크다운 금지**: **굵게**, *기울임* 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 이모지는 0-1개만 (없어도 됨)
- 해시태그 2개만 (본문과 분리, 마지막에 배치)
- 리트윗/인용 유도할 만한 가치 제공 (공감, 정보, 재미)

**[Threads] (500자 이내)**
- 문체: 반말 모드 필수 (Threads 특유의 친근한 문화)
  · "~해", "~야", "~지", "~거든", "~잖아" 등 사용
  · "~입니다", "~합니다" 절대 금지
- 톤: 친구한테 카톡하듯, 혼잣말하듯 편하게
  · "솔직히 말하면...", "근데 이거 진짜...", "나만 그런 거 아니지?"
- 내용:
  · 솔직한 의견, 생각, 느낌 공유
  · 개인적인 경험이나 깨달음
  · 공감 포인트 또는 작은 인사이트
  · 질문으로 대화 유도 ("어떻게 생각해?", "다들 어때?")
- 구조: 훅 → 본론(경험/생각) → 마무리 질문 또는 여운
- **마크다운 금지**: **굵게**, *기울임* 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 이모지: 자연스럽게 1-3개 (과하면 어색함)
- 해시태그: 3개 이내
- 피할 것: 딱딱한 정보 전달, 광고 느낌, 존댓말

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
    "content": "개선된 SNS 본문 (마크다운 금지, 순수 텍스트만)",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3", "#해시태그4", "#해시태그5"]
  },
  "x": {
    "content": "개선된 X 본문 (280자 이내, 마크다운 금지)",
    "tags": ["#해시태그1", "#해시태그2"]
  },
  "threads": {
    "content": "개선된 Threads 본문 (500자 이내, 마크다운 금지)",
    "tags": ["#해시태그1", "#해시태그2", "#해시태그3"]
  }
}

JSON만 응답하세요.`;

    const result = await withRetry(() => this.model.generateContent(prompt));
    const response = result.response.text();

    // safeJsonParse를 사용하여 더 강력한 파싱
    return safeJsonParse(response);
  }
}

// ============================================
// 4. Critic Agent
// ============================================
class CriticAgent {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  }

  async critique(content, analysisData, selectedPlatforms = ['blog', 'sns', 'x', 'threads']) {

    // 선택된 플랫폼만 평가 대상에 포함
    const hasBlog = selectedPlatforms.includes('blog') && content.blog;
    const hasSNS = selectedPlatforms.includes('sns') && content.sns;
    const hasX = selectedPlatforms.includes('x') && content.x;
    const hasThreads = selectedPlatforms.includes('threads') && content.threads;

    // 평가할 콘텐츠가 없으면 기본값 반환
    if (!hasBlog && !hasSNS && !hasX && !hasThreads) {
      return { overallRecommendation: '통과' };
    }

    // 평가 대상 콘텐츠 섹션 생성
    const contentSections = [];
    if (hasBlog) {
      contentSections.push(`**[블로그]**
제목: ${content.blog.title}
본문: ${content.blog.content}
태그: ${content.blog.tags?.join(', ') || ''}`);
    }
    if (hasSNS) {
      contentSections.push(`**[SNS (인스타/페이스북)]**
본문: ${content.sns.content}
태그: ${content.sns.tags?.join(', ') || ''}`);
    }
    if (hasX) {
      contentSections.push(`**[X]**
본문: ${content.x.content}
태그: ${content.x.tags?.join(', ') || ''}`);
    }
    if (hasThreads) {
      contentSections.push(`**[Threads]**
본문: ${content.threads.content}
태그: ${content.threads.tags?.join(', ') || ''}`);
    }

    // JSON 출력 형식 생성 (선택된 플랫폼만)
    const outputFormat = {};
    if (hasBlog) {
      outputFormat.blog = {
        score: "총점(0-100)",
        strengths: ["구체적 장점"],
        weaknesses: ["구체적 문제점"],
        improvements: ["구체적 개선 방법"]
      };
    }
    if (hasSNS) {
      outputFormat.sns = {
        score: "총점(0-100)",
        strengths: ["구체적 장점"],
        weaknesses: ["구체적 문제점"],
        improvements: ["구체적 개선 방법"]
      };
    }
    if (hasX) {
      outputFormat.x = {
        score: "총점(0-100)",
        strengths: ["장점"],
        weaknesses: ["문제점"],
        improvements: ["개선 방법"]
      };
    }
    if (hasThreads) {
      outputFormat.threads = {
        score: "총점(0-100)",
        strengths: ["장점"],
        weaknesses: ["문제점"],
        improvements: ["개선 방법"]
      };
    }
    outputFormat.overallRecommendation = "통과/개선필요";

    const prompt = `당신은 엄격한 콘텐츠 품질 평가 전문가입니다.
**실제 사용자들이 읽고 싶어할 가치 있는 콘텐츠인지** 냉정하게 평가하세요.

═══════════════════════════════════════
📌 원본 분석 정보
═══════════════════════════════════════
- 주제: ${analysisData.subject}
- 키워드: ${analysisData.keywords?.join(', ') || ''}
- 타겟: ${analysisData.targetAudience?.join(', ') || ''}

═══════════════════════════════════════
📝 평가 대상 콘텐츠
═══════════════════════════════════════

${contentSections.join('\n\n')}

═══════════════════════════════════════
🔍 상세 평가 기준 (각 항목 0-20점)
═══════════════════════════════════════

**1. 독자 가치 (0-20점)** ⭐ 가장 중요
- 읽는 사람이 얻어가는 실질적 정보/팁/인사이트가 있는가?
- 15점 미만: 공허하고 뻔한 내용
- 15점 이상: 독자에게 도움이 되는 구체적 가치

**2. 구체성 (0-20점)**
- 추상적 표현 대신 구체적 묘사, 숫자, 사례 포함?
- 15점 미만: 추상적이고 모호한 표현 다수
- 15점 이상: 생생하고 구체적인 내용

**3. 신뢰성 (0-20점)**
- 과장/허위 표현 없는가?
- 15점 미만: 과장되거나 신뢰하기 어려움
- 15점 이상: 믿을 수 있고 정직한 톤

**4. 플랫폼 최적화 (0-20점)**
- 각 플랫폼 특성에 맞는 길이/톤/형식?
- 15점 미만: 플랫폼 특성 무시
- 15점 이상: 플랫폼에 최적화됨

**5. 가독성/흐름 (0-20점)**
- 자연스러운 구조와 흐름?
- 15점 미만: 읽기 불편하거나 구조 없음
- 15점 이상: 술술 읽히는 자연스러운 흐름

**[네이버 블로그 전용 추가 평가 기준]**
- 제목 클릭 유도력: 검색 결과에서 클릭하고 싶은 제목인가?
- 도입부 훅: 첫 2-3문장이 계속 읽고 싶게 만드는가?
- 스토리텔링: 나열식이 아닌 자연스러운 흐름으로 풀어썼는가?
- 진정성: 개인 경험, 솔직한 의견이 담겨 있는가?
- 키워드 억지 삽입, 볼드 남발, 광고성 문구면 감점 (-10점 이상)

**[Instagram/Facebook 전용 추가 평가 기준]**
- 첫 줄 훅 파워: 피드에서 스크롤을 멈추게 하는가?
- 진정성: 광고/홍보 느낌이 아닌 진짜 이야기처럼 느껴지는가?
- 스토리텔링: 경험, 발견, 인사이트를 자연스럽게 녹였는가?
- CTA 효과: 댓글/저장/공유를 유도하는 구체적 행동 요청이 있는가?
- 딱딱한 홍보문구, 과장 표현, 정보 나열식이면 감점 (-10점 이상)

**[X 전용 추가 평가 기준]**
- 첫 문장의 훅 파워: 스크롤을 멈추게 하는가?
- 간결체 사용: "~다", "~임" 등 X 특유의 단정적 어조인가?
- 리트윗/인용 가치: 공유하고 싶은 인사이트, 공감, 정보가 있는가?
- 뻔한 내용/광고 느낌이면 감점 (-10점 이상)

**[Threads 전용 추가 평가 기준]**
- 반말 사용: "~해", "~야", "~지" 등 친근한 반말체인가?
- 존댓말("~입니다", "~합니다") 사용시 감점 (-15점)
- 친근함: 친구한테 말하듯 편한 톤인가?
- 공감 유도: 독자가 "맞아 나도!" 할 만한 포인트가 있는가?
- 딱딱한 정보 전달, 광고 느낌이면 감점 (-10점 이상)

═══════════════════════════════════════
📤 평가 결과 (JSON)
═══════════════════════════════════════
${JSON.stringify(outputFormat, null, 2)}

**80점 이상 = 통과, 미만 = 개선 필요**
엄격하게 평가하세요. 평범한 콘텐츠는 70점대입니다.
위에 명시된 플랫폼만 평가하세요.`;

    const result = await withRetry(() => this.model.generateContent(prompt));
    const response = result.response.text();

    try {
      // critique 파싱 실패 시 조용히 기본값 반환 (silent: true)
      return safeJsonParse(response, true);
    } catch {
      // 기본값 반환 (선택된 플랫폼만) - 재시도 위해 점수를 약간 낮춤
      console.log('품질 평가 파싱 실패, 기본값 사용');
      const defaultResult = { overallRecommendation: '통과' };
      if (hasBlog) defaultResult.blog = { score: 75, strengths: ['콘텐츠 생성 완료'], weaknesses: ['품질 평가 데이터 없음'], improvements: [] };
      if (hasSNS) defaultResult.sns = { score: 75, strengths: ['콘텐츠 생성 완료'], weaknesses: ['품질 평가 데이터 없음'], improvements: [] };
      if (hasX) defaultResult.x = { score: 75, strengths: ['콘텐츠 생성 완료'], weaknesses: ['품질 평가 데이터 없음'], improvements: [] };
      if (hasThreads) defaultResult.threads = { score: 75, strengths: ['콘텐츠 생성 완료'], weaknesses: ['품질 평가 데이터 없음'], improvements: [] };
      return defaultResult;
    }
  }
}

// ============================================
// Main Agentic Workflow (with Quality Check)
// ============================================
export const generateAgenticContent = async ({ textInput, images = [], styleTone = '', selectedPlatforms = ['blog', 'sns', 'x', 'threads'], userContext = null }, onProgress) => {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    const criticAgent = new CriticAgent();
    const writerAgent = new WriterAgent();
    const MAX_ATTEMPTS = 3; // 80점 이상이 될 때까지 최대 3회 시도

    const updateProgress = (message, step) => {
      if (onProgress) {
        onProgress({ message, step });
      }
    };

    updateProgress('콘텐츠 생성 중...', 'writing');

    // 사용자 컨텍스트에서 스타일 톤 추출 (온보딩 정보 활용)
    let effectiveStyleTone = styleTone;
    if (userContext) {
      // 사용자가 설정한 텍스트 톤이 있으면 사용
      if (userContext.text_tone) {
        const toneMap = {
          'casual': '친근하고 편안한 말투로',
          'professional': '전문적이고 신뢰감 있는 말투로',
          'friendly': '친근하고 따뜻한 말투로',
          'formal': '격식 있고 정중한 말투로'
        };
        effectiveStyleTone = toneMap[userContext.text_tone] || styleTone;
      }
      // 브랜드 톤이 있으면 추가
      if (userContext.brand_tone) {
        effectiveStyleTone = `${effectiveStyleTone}, ${userContext.brand_tone} 톤으로`;
      }
    }

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
    const styleInstruction = effectiveStyleTone
      ? `\n**글쓰기 스타일**: ${effectiveStyleTone}\n위 스타일을 반드시 적용하여 작성하세요.\n`
      : '';

    // 사용자 컨텍스트 (브랜드/비즈니스 정보) 지시문
    let userContextInstruction = '';
    if (userContext) {
      const contextParts = [];
      if (userContext.brand_name) {
        contextParts.push(`- 브랜드명: ${userContext.brand_name}`);
      }
      if (userContext.business_type) {
        const businessTypeMap = {
          'food': '음식/요식업',
          'tech': 'IT/기술',
          'fashion': '패션/의류',
          'education': '교육',
          'health': '건강/웰빙',
          'beauty': '뷰티/화장품',
          'travel': '여행',
          'finance': '금융/재테크',
          'lifestyle': '라이프스타일'
        };
        contextParts.push(`- 업종: ${businessTypeMap[userContext.business_type] || userContext.business_type}`);
      }
      if (userContext.business_description) {
        contextParts.push(`- 비즈니스 설명: ${userContext.business_description}`);
      }
      if (userContext.target_audience) {
        const ta = userContext.target_audience;
        const targetParts = [];
        if (ta.age_range) targetParts.push(`${ta.age_range}대`);
        if (ta.gender && ta.gender !== 'all') targetParts.push(ta.gender === 'male' ? '남성' : '여성');
        if (ta.interests?.length) targetParts.push(`관심사: ${ta.interests.join(', ')}`);
        if (targetParts.length) {
          contextParts.push(`- 타겟 고객: ${targetParts.join(', ')}`);
        }
      }
      if (userContext.brand_personality) {
        contextParts.push(`- 브랜드 성격: ${userContext.brand_personality}`);
      }
      if (userContext.key_themes?.length) {
        contextParts.push(`- 주요 주제: ${userContext.key_themes.join(', ')}`);
      }
      if (userContext.emotional_tone) {
        contextParts.push(`- 감정적 톤: ${userContext.emotional_tone}`);
      }
      if (userContext.blog_writing_style) {
        contextParts.push(`- 블로그 글쓰기 스타일: ${userContext.blog_writing_style}`);
      }
      if (userContext.instagram_caption_style) {
        contextParts.push(`- 인스타그램 캡션 스타일: ${userContext.instagram_caption_style}`);
      }

      if (contextParts.length > 0) {
        userContextInstruction = `
═══════════════════════════════════════
🏢 브랜드/비즈니스 정보 (온보딩 데이터)
═══════════════════════════════════════
${contextParts.join('\n')}

**중요**: 위 브랜드 정보를 반영하여 일관성 있는 콘텐츠를 작성하세요.
브랜드명이 있다면 자연스럽게 언급하고, 타겟 고객에 맞는 어조와 내용을 사용하세요.
`;
      }
    }

    // 선택된 플랫폼 확인
    const hasBlog = selectedPlatforms.includes('blog');
    const hasSNS = selectedPlatforms.includes('sns');
    const hasX = selectedPlatforms.includes('x');
    const hasThreads = selectedPlatforms.includes('threads');

    // 플랫폼별 요구사항 생성 (선택된 플랫폼만)
    const platformRequirements = [];
    if (hasBlog) {
      platformRequirements.push(`**[네이버 블로그] (800-1500자, 한국어)**
- 제목 작성법:
  · 검색 키워드 자연스럽게 포함
  · 클릭 유도 요소: 숫자("3가지", "5분"), 질문, 비교, 후기
  · 예: "OO 3개월 써본 솔직 후기", "OO vs OO 뭐가 나을까?"
- 도입부 (2-3문장):
  · 독자 공감 유도: "저도 처음엔 몰랐는데요", "이거 고민되시죠?"
  · 또는 문제 제기: "OO 하다가 실패한 적 있으신가요?"
  · 글을 끝까지 읽고 싶게 만드는 훅
- 본문 구조:
  · 소제목(##)으로 3-5개 섹션 구분
  · 각 섹션: 정보 + 개인 경험/의견 조합
  · 나열식 금지 → 스토리텔링으로 자연스럽게 풀어쓰기
  · 구체적 수치, 비교, 사례 포함 (신뢰도 상승)
  · "제가 직접 해보니...", "솔직히 말하면..." 등 진정성 표현
- 마무리:
  · 핵심 내용 1-2줄 요약
  · 독자 행동 유도: "도움이 되셨다면 공감 부탁드려요"
- **줄바꿈**: 문장이 끝나면 반드시 줄바꿈(\\n)을 넣어서 가독성을 높이세요
- 피할 것: 키워드 억지 삽입, 볼드 남발, 광고성 문구, 뻔한 정보 나열
- 태그: 메인 키워드 + 연관 키워드 + 롱테일 키워드 조합 (7개)${images.length > 0 ? `
- 이미지 배치: [IMAGE_1]~[IMAGE_${images.length}] 마커를 내용과 연관된 위치에 삽입` : ''}`);
    }
    if (hasSNS) {
      platformRequirements.push(`**[Instagram/Facebook] (150-300자, 한국어)**
- 첫 줄이 생명: 피드 스크롤을 멈추게 하는 강력한 훅으로 시작
  · 질문형: "혹시 이런 경험 있으세요?"
  · 공감형: "저만 이런 거 아니죠?"
  · 호기심형: "이거 알고 나면 달라져요"
  · 고백형: "솔직히 말하면..."
- 본문 작성법:
  · 진정성 있는 스토리텔링 (경험, 발견, 깨달음 공유)
  · 독자와 1:1 대화하듯 친근하게
  · 핵심 메시지 1-2개에 집중 (여러 개 X)
  · 줄바꿈으로 가독성 확보
- 구조: 훅 → 스토리/정보 → 가치 또는 인사이트 → CTA
- 이모지: 문단 시작점 + 포인트로 3-5개 (과하면 스팸처럼 보임)
- CTA: 구체적 행동 유도 예시
  · "댓글로 여러분 경험도 알려주세요 💬"
  · "나중에 볼 분들 저장 📌"
  · "공감되면 친구 태그해주세요"
- **줄바꿈**: 문장이 끝나면 반드시 줄바꿈(\\n)을 넣어서 가독성을 높이세요
- **마크다운 금지**: **굵게**, *기울임*, ##제목 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 절대 피할 것: 딱딱한 홍보문구, "최고의", "완벽한" 같은 과장, 정보만 나열
- 해시태그: 대중적 태그 3개 + 니치 태그 2개 조합`);
    }
    if (hasX) {
      platformRequirements.push(`**[X/Twitter] (280자 이내, 한국어)**
- 첫 문장이 곧 전부: 스크롤을 멈추게 하는 강력한 훅으로 시작
- 형식 선택: 날카로운 인사이트 / 논쟁적 의견 / 흥미로운 질문 / 예상 못한 반전
- 문체: 짧고 단정적인 어조, "~다", "~임", "~인 듯" 등 간결체 사용
- 피할 것: "~입니다", "~해요" 같은 정중한 어미, 뻔한 정보, 광고 느낌
- 바이럴 요소: 공감 (그거 나만 그래?), 정보 (몰랐던 사실), 재미 (위트 있는 표현)
- 구조: 핵심 메시지 1개 + 부연 1-2문장 (선택)
- **줄바꿈**: 문장이 끝나면 줄바꿈(\\n)을 넣어서 가독성을 높이세요
- **마크다운 금지**: **굵게**, *기울임* 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 해시태그: 2개만, 본문과 분리하여 마지막에 배치
- 이모지: 0-1개만 (과하면 역효과)
- 목표: "이거 리트윗해야겠다" 또는 "인용해서 내 의견 달아야지" 반응 유도`);
    }
    if (hasThreads) {
      platformRequirements.push(`**[Threads] (500자 이내, 한국어)**
- 문체: 반말 모드 필수 (Threads의 핵심 문화)
  · "~해", "~야", "~지", "~거든", "~잖아", "~인 듯" 사용
  · "~입니다", "~합니다" 같은 존댓말 절대 금지
- 톤앤매너:
  · 친구한테 카톡하듯 편하게
  · 혼잣말하듯 생각 공유: "근데 이거 진짜...", "솔직히 말하면..."
  · "나만 그런 거 아니지?", "이거 공감되는 사람?" 같은 공감 유도
- 내용:
  · 솔직한 의견, 생각, 느낌
  · 개인적인 경험이나 작은 깨달음
  · 일상적이지만 공감 가는 포인트
  · 마무리에 질문으로 대화 유도: "어떻게 생각해?", "다들 어때?"
- 구조: 훅 (공감/질문) → 본론 (경험/생각) → 마무리 (질문/여운)
- **줄바꿈**: 문장이 끝나면 반드시 줄바꿈(\\n)을 넣어서 가독성을 높이세요
- **마크다운 금지**: **굵게**, *기울임* 등 마크다운 문법 절대 사용 금지. 순수 텍스트만 작성
- 이모지: 자연스럽게 1-3개 (과하면 오히려 어색함)
- 해시태그: 3개 이내
- 피할 것: 딱딱한 정보 전달, 광고 느낌, 존댓말, 격식체`);
    }

    // JSON 출력 형식 생성 (선택된 플랫폼만)
    const outputFormat = {
      analysis: {
        subject: "핵심 주제",
        category: "카테고리 (음식/뷰티/여행/IT/라이프스타일/비즈니스 등)",
        keywords: ["SEO 메인키워드", "연관키워드1", "연관키워드2", "롱테일키워드"],
        mood: "콘텐츠 분위기",
        targetAudience: ["주요 타겟층 구체적으로"],
        highlights: ["차별화 포인트", "핵심 가치"],
        recommendedTone: "권장 톤앤매너"
      }
    };
    if (hasBlog) {
      outputFormat.blog = {
        title: "클릭하고 싶은 SEO 최적화 제목",
        content: "가치 있는 블로그 본문 (마크다운 형식)",
        tags: ["태그1", "태그2", "태그3", "태그4", "태그5", "태그6", "태그7"]
      };
    }
    if (hasSNS) {
      outputFormat.sns = {
        content: "Instagram/Facebook용 매력적인 본문 (마크다운 금지, 순수 텍스트만)",
        tags: ["#해시태그1", "#해시태그2", "#해시태그3", "#해시태그4", "#해시태그5"]
      };
    }
    if (hasX) {
      outputFormat.x = {
        content: "X용 임팩트 있는 본문 (280자 이내, 마크다운 금지)",
        tags: ["#해시태그1", "#해시태그2"]
      };
    }
    if (hasThreads) {
      outputFormat.threads = {
        content: "Threads용 대화체 본문 (500자 이내, 마크다운 금지)",
        tags: ["#해시태그1", "#해시태그2", "#해시태그3"]
      };
    }

    // ⚡ 단일 API 호출로 분석 + 생성 동시 처리 (강화된 프롬프트 엔지니어링)
    const prompt = `당신은 10년 경력의 전문 콘텐츠 마케터이자 SEO 전문가입니다.
사용자의 입력을 바탕으로 **실제로 사람들이 읽고 싶어하는, 가치 있는 콘텐츠**를 생성하세요.

═══════════════════════════════════════
📌 사용자 입력
═══════════════════════════════════════
주제/키워드: ${textInput || '이미지 기반 콘텐츠'}
첨부 이미지: ${images.length}개
${styleInstruction}
${userContextInstruction}
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
- **중요: 문장이 끝나면(마침표, 물음표, 느낌표 뒤) 반드시 줄바꿈(\\n)을 삽입하여 가독성을 높이세요**

**4. 플랫폼별 최적화**
- 각 플랫폼 사용자의 기대와 행동 패턴 고려
- 플랫폼 알고리즘 특성 반영

═══════════════════════════════════════
📝 플랫폼별 상세 요구사항
═══════════════════════════════════════

${platformRequirements.join('\n\n')}

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
${JSON.stringify(outputFormat, null, 2)}

중요: JSON만 응답하세요. 위에 명시된 플랫폼만 생성하세요.`;

    const contentParts = imageParts.length > 0 ? [prompt, ...imageParts] : prompt;
    const result = await withRetry(() => model.generateContent(contentParts));
    const response = result.response.text();

    let content = safeJsonParse(response);
    const imageDataUrls = await imageDataUrlsPromise;

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

    // 🔍 품질 검사 활성화 (선택된 플랫폼만 평가)
    updateProgress('품질 검사 중...', 'critiquing');
    let critique = await criticAgent.critique(content, analysisData, selectedPlatforms);
    let attempts = 1;

    // 선택된 플랫폼 중 80점 미만인 것이 있으면 재생성
    const needsImprovement = () => {
      return selectedPlatforms.some(p => critique[p] && critique[p].score < 80);
    };

    while (needsImprovement() && attempts < MAX_ATTEMPTS) {
      attempts++;
      const lowScorePlatforms = selectedPlatforms.filter(p => critique[p] && critique[p].score < 80);
      updateProgress(`품질 개선 중... (${lowScorePlatforms.join(', ')}) - 시도 ${attempts}/${MAX_ATTEMPTS}`, 'writing');

      // 피드백을 반영하여 재생성 (선택된 플랫폼 중 80점 미만인 것만)
      const feedback = {};
      selectedPlatforms.forEach(p => {
        if (critique[p] && critique[p].score < 80) {
          feedback[p] = critique[p].improvements;
        }
      });

      const improvedContent = await writerAgent.generateContent(analysisData, feedback, images.length);

      // 기존 콘텐츠 업데이트 (개선된 플랫폼만)
      Object.keys(feedback).forEach(p => {
        if (improvedContent[p]) {
          content[p] = improvedContent[p];
        }
      });

      // 다시 품질 검사
      updateProgress('재검사 중...', 'critiquing');
      critique = await criticAgent.critique(content, analysisData, selectedPlatforms);
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
    throw error;
  }
};
