import { GoogleGenerativeAI } from '@google/generative-ai';

const API_KEY = process.env.REACT_APP_GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);

// 파일을 base64로 변환하는 헬퍼 함수
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // data:image/jpeg;base64,... 형식에서 base64 부분만 추출
      const base64String = reader.result.split(',')[1];
      resolve(base64String);
    };
    reader.onerror = error => reject(error);
  });
};

// 사용 가능한 모델 목록 확인
export const listAvailableModels = async () => {
  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models?key=${API_KEY}`
    );
    const data = await response.json();
    console.log('Available models:', data);
    return data;
  } catch (error) {
    console.error('Error listing models:', error);
    throw error;
  }
};

export const generateBlogPost = async ({
  industry,
  location,
  purpose,
  targetAudience,
  keywords,
  tone,
  detailMode,
  simpleInput,
  detailedFormData,
  uploadedImages = [],
  imagePreviewUrls = [],
}) => {
  try {
    // API 키 확인
    if (!API_KEY) {
      throw new Error('GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.');
    }

    console.log('API Key exists:', !!API_KEY);
    console.log('Using SDK method...');
    console.log('Detail mode:', detailMode);
    console.log('Simple input:', simpleInput);
    console.log('Detailed form data:', detailedFormData);

    // 상세 정보 문자열 생성
    let detailsSection = '';

    if (detailMode === 'simple' && simpleInput) {
      detailsSection = `\n**상세 정보 (사용자 입력):**\n${simpleInput}\n`;
    } else if (detailMode === 'detailed' && detailedFormData) {
      // 주제에 따라 상세 정보 포맷팅
      if (purpose === 'event' || purpose === '이벤트 공지') {
        const details = [];
        if (detailedFormData.eventName) details.push(`- 이벤트명: ${detailedFormData.eventName}`);
        if (detailedFormData.discountTarget) details.push(`- 할인 대상: ${detailedFormData.discountTarget}`);
        if (detailedFormData.discountRate) details.push(`- 할인율/가격: ${detailedFormData.discountRate}`);
        if (detailedFormData.eventPeriodStart && detailedFormData.eventPeriodEnd) {
          details.push(`- 기간: ${detailedFormData.eventPeriodStart} ~ ${detailedFormData.eventPeriodEnd}`);
        }
        if (detailedFormData.additionalBenefit) details.push(`- 추가 혜택: ${detailedFormData.additionalBenefit}`);
        if (detailedFormData.participationCondition) details.push(`- 참여 조건: ${detailedFormData.participationCondition}`);
        if (detailedFormData.eventEtc) details.push(`- 기타: ${detailedFormData.eventEtc}`);
        if (details.length > 0) {
          detailsSection = `\n**이벤트 상세 정보:**\n${details.join('\n')}\n`;
        }
      } else if (purpose === 'new_menu' || purpose === '신메뉴 공지') {
        const details = [];
        if (detailedFormData.menuName) details.push(`- 메뉴명: ${detailedFormData.menuName}`);
        if (detailedFormData.menuPrice) details.push(`- 가격: ${detailedFormData.menuPrice}`);
        if (detailedFormData.releaseDate) details.push(`- 출시일: ${detailedFormData.releaseDate}`);
        if (detailedFormData.menuDescription) details.push(`- 설명: ${detailedFormData.menuDescription}`);
        if (detailedFormData.menuFeatures) details.push(`- 특징: ${detailedFormData.menuFeatures}`);
        if (details.length > 0) {
          detailsSection = `\n**신메뉴 상세 정보:**\n${details.join('\n')}\n`;
        }
      } else if (purpose === 'service' || purpose === '서비스 설명') {
        const details = [];
        if (detailedFormData.serviceName) details.push(`- 서비스명: ${detailedFormData.serviceName}`);
        if (detailedFormData.serviceContent) details.push(`- 주요 내용: ${detailedFormData.serviceContent}`);
        if (detailedFormData.usageMethod) details.push(`- 이용 방법: ${detailedFormData.usageMethod}`);
        if (detailedFormData.servicePrice) details.push(`- 가격/조건: ${detailedFormData.servicePrice}`);
        if (detailedFormData.serviceContact) details.push(`- 예약/문의: ${detailedFormData.serviceContact}`);
        if (details.length > 0) {
          detailsSection = `\n**서비스 상세 정보:**\n${details.join('\n')}\n`;
        }
      } else if (purpose === 'info_tips' || purpose === '정보 및 팁 공유') {
        const details = [];
        if (detailedFormData.infoTitle) details.push(`- 제목: ${detailedFormData.infoTitle}`);
        if (detailedFormData.infoContent) details.push(`- 내용: ${detailedFormData.infoContent}`);
        const tips = [detailedFormData.tip1, detailedFormData.tip2, detailedFormData.tip3].filter(Boolean);
        if (tips.length > 0) {
          details.push(`- 팁: ${tips.join(', ')}`);
        }
        if (detailedFormData.relatedProduct) details.push(`- 관련 상품: ${detailedFormData.relatedProduct}`);
        if (details.length > 0) {
          detailsSection = `\n**정보 및 팁 상세:**\n${details.join('\n')}\n`;
        }
      } else {
        // 기타
        if (detailedFormData.customContent) {
          detailsSection = `\n**핵심 내용:**\n${detailedFormData.customContent}\n`;
        }
      }
    }

    // 이미지 관련 지침 추가
    const imageInstructions = uploadedImages.length > 0
      ? `\n**이미지 활용:**
- ${uploadedImages.length}개의 이미지가 제공되었습니다
- 각 이미지를 분석하고, 블로그 포스트 내용의 적절한 위치에 자연스럽게 삽입하세요
- 이미지는 마크다운 형식으로 ![이미지 설명](IMAGE_PLACEHOLDER_0), ![이미지 설명](IMAGE_PLACEHOLDER_1) 형식으로 표시하세요
- 첫 번째 이미지는 IMAGE_PLACEHOLDER_0, 두 번째는 IMAGE_PLACEHOLDER_1 식으로 번호를 매기세요
- 이미지 설명은 이미지 내용을 바탕으로 구체적이고 자연스럽게 작성하세요
- 이미지 위치는 문맥의 흐름을 고려하여 가장 적절한 곳에 배치하세요\n`
      : '';

    const prompt = `당신은 전문적인 블로그 콘텐츠 작가입니다. 다음 정보를 바탕으로 SEO 최적화된 고품질 블로그 포스트를 작성해주세요.

**비즈니스 정보:**
- 업종: ${industry}
- 지역: ${location}

**콘텐츠 요구사항:**
- 글의 주제/목적: ${purpose}
- 타겟 고객층: ${Array.isArray(targetAudience) ? targetAudience.join(', ') : targetAudience}
- 핵심 키워드: ${keywords.join(', ')}
- 톤앤 매너: ${tone}
${detailsSection}${imageInstructions}
**작성 지침:**
1. 제목은 클릭을 유도하면서도 검색 최적화가 되어야 합니다
2. 본문은 구조화되고 읽기 쉬워야 합니다 (소제목, 문단 나누기 등)
3. 핵심 키워드는 **절대 볼드 처리하지 말고** 일반 텍스트로 자연스럽게 문맥에 녹여서 작성해주세요
4. 타겟 고객층에게 공감을 얻을 수 있는 내용으로 작성해주세요
5. 지역 특성을 고려한 내용을 포함해주세요
6. 블로그 포스팅에 적합한 길이(800-1500자)로 작성해주세요
7. **상세 정보를 반드시 활용하여 구체적이고 정확한 내용으로 작성해주세요**
8. 본문에서 특정 단어나 키워드를 강조하기 위해 마크다운 문법(**, *, _)을 사용하지 마세요. 오직 제목(##, ###)만 사용 가능합니다

**응답 형식 (JSON):**
{
  "title": "SEO 최적화된 제목",
  "content": "블로그 본문 내용 (마크다운 형식)",
  "tags": ["태그1", "태그2", "태그3", "태그4", "태그5", "태그6", "태그7", "태그8", "태그9", "태그10"]
}

**중요:** tags는 최소 7개, 최대 10개를 생성해주세요. SEO를 고려한 다양한 태그를 포함해주세요.

위 형식으로 JSON만 응답해주세요.`;

    // 이미지를 base64로 변환
    let imageParts = [];
    if (uploadedImages.length > 0) {
      console.log(`Converting ${uploadedImages.length} images to base64...`);
      imageParts = await Promise.all(
        uploadedImages.map(async (file, index) => {
          const base64Data = await fileToBase64(file);
          return {
            inlineData: {
              data: base64Data,
              mimeType: file.type
            }
          };
        })
      );
      console.log('Images converted successfully');
    }

    // SDK 사용 - 최신 모델 사용
    const modelNames = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash'];

    let text = null;
    let lastError = null;

    for (const modelName of modelNames) {
      try {
        console.log(`Trying SDK with model: ${modelName}...`);
        const model = genAI.getGenerativeModel({ model: modelName });

        // 이미지가 있으면 프롬프트와 함께 전달, 없으면 텍스트만
        const contentParts = imageParts.length > 0
          ? [prompt, ...imageParts]
          : prompt;

        const result = await model.generateContent(contentParts);
        const response = await result.response;
        text = response.text();

        if (text) {
          console.log(`✅ Successfully using SDK model: ${modelName}`);
          break;
        }
      } catch (error) {
        console.log(`❌ SDK Model ${modelName} failed:`, error.message);
        lastError = error;
      }
    }

    if (!text) {
      console.error('모든 SDK 모델 시도 실패. 마지막 에러:', lastError);
      throw new Error(`Gemini API Error: ${lastError?.message || '모든 모델에 접근할 수 없습니다.'}`);
    }

    console.log('Generated text:', text);

    // JSON 파싱
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.error('Failed to extract JSON from response:', text);
      throw new Error('Gemini API에서 올바른 형식의 응답을 받지 못했습니다.');
    }

    const parsedResponse = JSON.parse(jsonMatch[0]);
    console.log('Parsed response:', parsedResponse);

    // 업로드된 이미지의 미리보기 URL도 함께 반환
    return {
      ...parsedResponse,
      imageUrls: imagePreviewUrls
    };
  } catch (error) {
    console.error('Error generating blog post:', error);
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name,
    });
    throw error;
  }
};
