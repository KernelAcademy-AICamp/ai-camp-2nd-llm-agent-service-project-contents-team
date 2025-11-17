const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const Anthropic = require('@anthropic-ai/sdk');
const multer = require('multer');
const Jimp = require('jimp');
const textToImage = require('text-to-image');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5001;

// 업로드 디렉토리 생성
const uploadDir = path.join(__dirname, 'uploads');
const outputDir = path.join(__dirname, 'outputs');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

// Multer 설정 (메모리에 파일 저장)
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB 제한
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = file.mimetype && file.mimetype.startsWith('image/');

    if (mimetype && extname) {
      return cb(null, true);
    } else {
      // 파일 정보 로깅
      console.log('거부된 파일:', file.originalname, 'MIME:', file.mimetype);
      return cb(null, false); // 에러 대신 false 반환
    }
  }
});

// Gemini 클라이언트
const genAI = process.env.GOOGLE_API_KEY
  ? new GoogleGenerativeAI(process.env.GOOGLE_API_KEY)
  : null;

// Middleware
app.use(cors());
app.use(express.json());

// -------------------------------------------
// Gemini 프롬프트 최적화 함수
// -------------------------------------------
async function optimizePromptWithGemini(userPrompt) {
  try {
    if (!genAI) throw new Error('Gemini API 미설정');

    // 최신 지원 모델로 변경 (예: gemini-2.5-flash)
    const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

    const prompt = `You are an expert at creating detailed, high-quality image generation prompts for Stable Diffusion.

User's prompt: "${userPrompt}"

Transform this into an optimized Stable Diffusion prompt with style, lighting, quality, and composition. Under 75 words. English only. Return ONLY the optimized prompt.`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error('Gemini 프롬프트 최적화 실패:', error);
    return userPrompt;
  }
}

// -------------------------------------------
// 이미지 생성 엔드포인트
// -------------------------------------------
app.post('/api/generate-image', async (req, res) => {
  const { prompt, model } = req.body;

  if (!prompt) return res.status(400).json({ error: '프롬프트가 필요합니다.' });

  try {
    let optimizedPrompt = prompt;
    let usedGeminiOptimization = false;
    let usedNanovanaAPI = false;
    let imageUrl;

    // -------------------------------------------
    // Nanovana (나노바나나) - Google Gemini 2.5 Flash Image
    // -------------------------------------------
    if (model === 'nanovana') {
      const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;
      if (!GOOGLE_API_KEY) {
        return res.status(500).json({ error: 'Google API 키가 필요합니다. (Gemini 2.5 Flash Image)' });
      }

      console.log('🍌 나노바나나(Gemini 2.5 Flash Image)로 이미지 생성 중...');

      const response = await axios.post(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_API_KEY}`,
        {
          contents: [{
            parts: [{
              text: `Generate an image: ${prompt}`
            }]
          }]
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 120000,
        }
      );

      // Gemini API 응답에서 이미지 추출
      if (response.data && response.data.candidates && response.data.candidates[0]) {
        const candidate = response.data.candidates[0];

        // inline_data에서 이미지 찾기
        if (candidate.content && candidate.content.parts) {
          for (const part of candidate.content.parts) {
            if (part.inline_data && part.inline_data.data) {
              const mimeType = part.inline_data.mime_type || 'image/png';
              imageUrl = `data:${mimeType};base64,${part.inline_data.data}`;
              break;
            }
          }
        }

        if (!imageUrl) {
          console.error('Gemini API 응답:', JSON.stringify(response.data, null, 2));
          throw new Error('Gemini API로부터 이미지를 추출하지 못했습니다.');
        }
      } else {
        console.error('Gemini API 응답:', JSON.stringify(response.data, null, 2));
        throw new Error('Gemini API로부터 유효한 응답을 받지 못했습니다.');
      }

      usedNanovanaAPI = true;
      console.log('✅ 나노바나나 이미지 생성 완료!');
    }
    // -------------------------------------------
    // Gemini + Stable Diffusion 2.1
    // -------------------------------------------
    else if (model === 'gemini') {
      const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;
      if (!HF_API_KEY)
        return res.status(500).json({ error: 'Hugging Face API 키가 없습니다.' });

      if (process.env.GOOGLE_API_KEY) {
        optimizedPrompt = await optimizePromptWithGemini(prompt);
        usedGeminiOptimization = true;
      }

      const response = await axios.post(
        'https://router.huggingface.co/hf-inference/v1/models/stabilityai/stable-diffusion-2-1',
        { inputs: optimizedPrompt },
        {
          headers: {
            Authorization: `Bearer ${HF_API_KEY}`,
            'Content-Type': 'application/json',
          },
          responseType: 'arraybuffer',
          timeout: 120000,
        }
      );

      const base64 = Buffer.from(response.data).toString('base64');
      imageUrl = `data:image/png;base64,${base64}`;
    } else {
      return res.status(400).json({ error: '지원하지 않는 AI 모델입니다.' });
    }

    res.json({
      success: true,
      imageUrl,
      optimizedPrompt: optimizedPrompt !== prompt ? optimizedPrompt : undefined,
      usedGeminiOptimization,
      usedNanovanaAPI,
    });
  } catch (error) {
    console.error('이미지 생성 실패:', error);

    let msg = '이미지 생성 중 오류가 발생했습니다.';
    if (error.response) {
      if (error.response.status === 503) msg = '모델이 로딩 중입니다. 잠시 후 다시 시도하세요.';
      else if (error.response.status === 401) msg = 'API 인증 실패 (API 키 확인).';
      else msg = `API 오류: ${error.response.status}`;
    } else if (error.code === 'ECONNABORTED') msg = '요청 시간이 초과되었습니다.';
    else if (error.request) msg = '서버 연결에 실패했습니다.';

    res.status(500).json({ success: false, error: msg, details: error.message });
  }
});

// -------------------------------------------
// 카드뉴스 생성 엔드포인트
// -------------------------------------------
app.post('/api/generate-cardnews', upload.array('images', 10), async (req, res) => {
  try {
    const { titles, descriptions, fontStyle, colorTheme, purpose, layoutStyle } = req.body;
    const images = req.files;

    if (!images || images.length === 0) {
      return res.status(400).json({ error: '최소 1개 이상의 이미지가 필요합니다.' });
    }

    console.log(`📰 카드뉴스 생성 시작: ${images.length}개 이미지`);
    console.log(`🎨 스타일: 폰트=${fontStyle}, 색상=${colorTheme}, 용도=${purpose}, 레이아웃=${layoutStyle}`);

    const cardWidth = 1080;
    const cardHeight = 1080;
    const cardNewsImages = [];

    // 제목과 설명을 배열로 파싱
    const titleArray = titles ? JSON.parse(titles) : [];
    const descArray = descriptions ? JSON.parse(descriptions) : [];

    // AI로 프롬프트 개선 함수
    const enhanceContentWithAI = async (title, description, purpose) => {
      try {
        const anthropic = new Anthropic({
          apiKey: process.env.ANTHROPIC_API_KEY,
        });

        const purposeMap = {
          'promotion': '프로모션/할인 홍보',
          'menu': '신메뉴/상품 소개',
          'info': '정보 전달/팁 공유',
          'event': '이벤트/행사 안내'
        };

        const prompt = `당신은 전문 마케팅 카피라이터입니다. 다음 카드뉴스 문구를 더 임팩트있고 매력적으로 개선해주세요.

**원본 제목**: ${title}
**원본 설명**: ${description || '없음'}
**용도**: ${purposeMap[purpose] || purpose}

**개선 규칙**:
1. 제목: 간결하고 강렬하게 (최대 15자, 핵심 메시지 전달)
2. 설명: 구체적이고 행동을 유도하도록 (최대 35자)
3. 용도에 맞는 톤: ${purpose === 'promotion' ? '긴급감과 혜택 강조' : purpose === 'menu' ? '호기심과 맛 표현' : purpose === 'info' ? '유익함과 신뢰' : '설렘과 기대감'}
4. 이모지 제거, 순수 한글/영문/숫자만 사용
5. 과장 없이 진실되고 신뢰감 있게

JSON 형식으로만 응답: {"title": "개선된 제목", "description": "개선된 설명", "reasoning": "개선 이유"}`;

        const message = await anthropic.messages.create({
          model: 'claude-3-5-sonnet-20241022',
          max_tokens: 600,
          messages: [{
            role: 'user',
            content: prompt
          }]
        });

        const responseText = message.content[0].text;
        const jsonMatch = responseText.match(/\{[\s\S]*\}/);

        if (jsonMatch) {
          const enhanced = JSON.parse(jsonMatch[0]);
          console.log(`✨ AI 개선 완료:`);
          console.log(`   제목: "${title}" → "${enhanced.title}"`);
          console.log(`   설명: "${description}" → "${enhanced.description}"`);
          console.log(`   이유: ${enhanced.reasoning}`);
          return {
            title: enhanced.title,
            description: enhanced.description
          };
        }
      } catch (error) {
        console.error(`⚠️ AI 개선 실패 (원본 사용):`, error.message);
      }

      return { title, description: description || '' };
    };

    // 색상 테마 설정 (더 선명하고 전문적인 스타일)
    const colorThemes = {
      warm: {
        primary: 0xFF8B5A, // 따뜻한 오렌지
        secondary: 0xFFE5D9, // 연한 살구색
        accent: 0xD4654A, // 진한 오렌지
        textColor: 'white',
        textColorDark: '#2D1810'
      },
      cool: {
        primary: 0x4A90E2, // 선명한 블루
        secondary: 0xE3F2FD, // 연한 블루
        accent: 0x2E5C8A, // 진한 블루
        textColor: 'white',
        textColorDark: '#0D2841'
      },
      vibrant: {
        primary: 0xFF6B9D, // 밝은 핑크
        secondary: 0xFFE5EE, // 연한 핑크
        accent: 0xE91E63, // 진한 핑크
        textColor: 'white',
        textColorDark: '#4A0E2A'
      },
      minimal: {
        primary: 0x424242, // 다크 그레이
        secondary: 0xF5F5F5, // 라이트 그레이
        accent: 0x212121, // 블랙
        textColor: 'white',
        textColorDark: '#212121'
      }
    };

    const selectedTheme = colorThemes[colorTheme] || colorThemes.warm;

    // 각 이미지를 카드뉴스 형태로 처리
    for (let i = 0; i < images.length; i++) {
      const imageBuffer = images[i].buffer;
      const originalTitle = titleArray[i] || `카드 ${i + 1}`;
      const originalDescription = descArray[i] || '';

      // AI로 콘텐츠 개선 (사용자 프롬프트 보충)
      console.log(`\n🤖 AI 카피라이터가 ${i + 1}번째 카드 문구를 개선 중...`);
      const enhanced = await enhanceContentWithAI(originalTitle, originalDescription, purpose);
      const title = enhanced.title;
      const description = enhanced.description;

      // Jimp로 이미지 로드
      let image = await Jimp.read(imageBuffer);
      let baseImage;

      // 레이아웃 스타일에 따라 다른 처리
      if (layoutStyle === 'split') {
        // Split: 이미지는 상단 65%, 텍스트는 하단 35% (선명한 색상 배경)
        baseImage = new Jimp(cardWidth, cardHeight, 0xFFFFFFFF);
        image.cover(cardWidth, Math.floor(cardHeight * 0.65));
        baseImage.composite(image, 0, 0);

        // 하단에 선명한 색상 박스 (그라데이션 없이)
        const splitY = Math.floor(cardHeight * 0.65);
        for (let y = splitY; y < cardHeight; y++) {
          for (let x = 0; x < cardWidth; x++) {
            baseImage.setPixelColor(selectedTheme.primary + 0xFF, x, y);
          }
        }

        // 분할선 추가 (악센트 컬러)
        for (let y = splitY - 5; y < splitY + 5; y++) {
          for (let x = 0; x < cardWidth; x++) {
            baseImage.setPixelColor(selectedTheme.accent + 0xFF, x, y);
          }
        }
        image = baseImage;

      } else if (layoutStyle === 'minimal') {
        // Minimal: 중앙에 작은 이미지 (80%), 여백 많음
        baseImage = new Jimp(cardWidth, cardHeight, 0xF9FAFBFF);
        const imgSize = Math.floor(cardWidth * 0.8);
        const imgPadding = Math.floor((cardWidth - imgSize) / 2);
        image.cover(imgSize, imgSize);
        baseImage.composite(image, imgPadding, imgPadding);
        image = baseImage;

      } else if (layoutStyle === 'magazine') {
        // Magazine: 이미지 전체 + 모서리 프레임
        image.cover(cardWidth, cardHeight);
        image.brightness(-0.1);

        // 프레임 추가 (흰색 테두리)
        const frameWidth = 30;
        for (let i = 0; i < frameWidth; i++) {
          for (let x = i; x < cardWidth - i; x++) {
            image.setPixelColor(0xFFFFFFFF, x, i);
            image.setPixelColor(0xFFFFFFFF, x, cardHeight - 1 - i);
          }
          for (let y = i; y < cardHeight - i; y++) {
            image.setPixelColor(0xFFFFFFFF, i, y);
            image.setPixelColor(0xFFFFFFFF, cardWidth - 1 - i, y);
          }
        }

        // 하단에 반투명 검은 박스
        const textBoxHeight = 250;
        const textBoxY = cardHeight - textBoxHeight - frameWidth;
        for (let y = textBoxY; y < cardHeight - frameWidth; y++) {
          const boxGradient = (y - textBoxY) / textBoxHeight;
          const alpha = Math.floor(200 + boxGradient * 55);
          for (let x = frameWidth; x < cardWidth - frameWidth; x++) {
            const overlayColor = Jimp.rgbaToInt(20, 20, 20, alpha);
            image.setPixelColor(overlayColor, x, y);
          }
        }

      } else {
        // Overlay (default): 전체 화면 이미지 + 하단 색상 박스
        image.cover(cardWidth, cardHeight);
        image.brightness(-0.2);

        // 하단 1/3에 강한 색상 박스 (더 선명하게)
        const boxHeight = Math.floor(cardHeight * 0.4);
        const boxY = cardHeight - boxHeight;

        // 그라데이션으로 자연스럽게 연결
        for (let y = boxY - 100; y < boxY; y++) {
          const gradAlpha = Math.floor(((y - (boxY - 100)) / 100) * 220);
          for (let x = 0; x < cardWidth; x++) {
            const primaryColor = Jimp.intToRGBA(selectedTheme.primary);
            const overlayColor = Jimp.rgbaToInt(primaryColor.r, primaryColor.g, primaryColor.b, gradAlpha);
            const pixelColor = image.getPixelColor(x, y);
            const pixel = Jimp.intToRGBA(pixelColor);
            const overlay = Jimp.intToRGBA(overlayColor);

            const blendedR = Math.floor(pixel.r * (1 - overlay.a / 255) + overlay.r * (overlay.a / 255));
            const blendedG = Math.floor(pixel.g * (1 - overlay.a / 255) + overlay.g * (overlay.a / 255));
            const blendedB = Math.floor(pixel.b * (1 - overlay.a / 255) + overlay.b * (overlay.a / 255));

            image.setPixelColor(Jimp.rgbaToInt(blendedR, blendedG, blendedB, 255), x, y);
          }
        }

        // 완전 불투명한 색상 박스
        for (let y = boxY; y < cardHeight; y++) {
          for (let x = 0; x < cardWidth; x++) {
            image.setPixelColor(selectedTheme.primary + 0xFF, x, y);
          }
        }

        // 상단 악센트 라인 추가
        for (let y = boxY; y < boxY + 8; y++) {
          for (let x = 0; x < cardWidth; x++) {
            image.setPixelColor(selectedTheme.accent + 0xFF, x, y);
          }
        }
      }

      // 한글 텍스트를 이미지로 생성 (text-to-image 사용)

      // 제목 이미지 생성 (더 크고 임팩트 있게)
      const titleDataUri = await textToImage.generate(title, {
        maxWidth: cardWidth - 160,
        fontSize: 80,  // 64에서 80으로 증가
        fontWeight: 'bold',
        lineHeight: 96,
        textColor: 'white',
        bgColor: 'transparent',
        textAlign: 'left',
        verticalAlign: 'top'
      });

      // Data URI를 Buffer로 변환
      const titleBuffer = Buffer.from(titleDataUri.split(',')[1], 'base64');
      const titleImage = await Jimp.read(titleBuffer);
      const titleY = cardHeight - 280;
      image.composite(titleImage, 80, titleY);

      // 설명 추가 (제목 아래, 더 크게)
      if (description) {
        const descDataUri = await textToImage.generate(description, {
          maxWidth: cardWidth - 160,
          fontSize: 40,  // 32에서 40으로 증가
          fontWeight: 'normal',
          lineHeight: 52,
          textColor: 'white',
          bgColor: 'transparent',
          textAlign: 'left',
          verticalAlign: 'top'
        });

        const descBuffer = Buffer.from(descDataUri.split(',')[1], 'base64');
        const descImage = await Jimp.read(descBuffer);
        const descY = cardHeight - 160;
        image.composite(descImage, 80, descY);
      }

      // 페이지 번호 (우측 하단)
      const pageText = `${i + 1} / ${images.length}`;
      const pageDataUri = await textToImage.generate(pageText, {
        fontSize: 20,  // 16에서 20으로 증가
        fontWeight: 'bold',
        textColor: 'white',
        bgColor: 'transparent',
        textAlign: 'center'
      });

      const pageBuffer = Buffer.from(pageDataUri.split(',')[1], 'base64');
      const pageImage = await Jimp.read(pageBuffer);
      image.composite(pageImage, cardWidth - 120, cardHeight - 60);

      // 좌측 상단에 용도 배지 추가 (더 눈에 띄게)
      const badgeText = purpose === 'promotion' ? '프로모션' :
                       purpose === 'menu' ? '신메뉴' :
                       purpose === 'info' ? '정보' : '이벤트';

      // 배지 배경 (악센트 컬러로 변경)
      const badgeWidth = 180;
      const badgeHeight = 70;
      const badgeX = 50;
      const badgeY = 50;

      // 둥근 사각형 배지 배경
      for (let y = badgeY; y < badgeY + badgeHeight; y++) {
        for (let x = badgeX; x < badgeX + badgeWidth; x++) {
          image.setPixelColor(selectedTheme.accent + 0xFF, x, y);
        }
      }

      // 배지 하단에 작은 악센트 바
      for (let y = badgeY + badgeHeight; y < badgeY + badgeHeight + 5; y++) {
        for (let x = badgeX; x < badgeX + badgeWidth; x++) {
          image.setPixelColor(0xFFFFFFFF, x, y);
        }
      }

      // 배지 텍스트 이미지 생성 (더 크게)
      const badgeDataUri = await textToImage.generate(badgeText, {
        fontSize: 32,  // 24에서 32로 증가
        fontWeight: 'bold',
        textColor: 'white',
        bgColor: 'transparent',
        textAlign: 'center'
      });

      const badgeBuffer = Buffer.from(badgeDataUri.split(',')[1], 'base64');
      const badgeImage = await Jimp.read(badgeBuffer);
      // 배지 중앙 정렬
      const badgeTextX = badgeX + Math.floor((badgeWidth - badgeImage.getWidth()) / 2);
      const badgeTextY = badgeY + Math.floor((badgeHeight - badgeImage.getHeight()) / 2);
      image.composite(badgeImage, badgeTextX, badgeTextY);

      // Base64로 변환
      const base64Image = await image.getBase64Async(Jimp.MIME_PNG);
      cardNewsImages.push(base64Image);

      console.log(`✅ 카드 ${i + 1} 생성 완료`);
    }

    res.json({
      success: true,
      message: `${images.length}개의 카드뉴스가 생성되었습니다.`,
      cards: cardNewsImages,
      count: images.length
    });

  } catch (error) {
    console.error('카드뉴스 생성 실패:', error);
    res.status(500).json({
      success: false,
      error: '카드뉴스 생성 중 오류가 발생했습니다.',
      details: error.message
    });
  }
});

// 정적 파일 제공 (outputs 폴더)
app.use('/outputs', express.static(outputDir));

// 헬스 체크
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`🚀 서버가 포트 ${PORT}에서 실행 중입니다.`);
  console.log(`📝 API 엔드포인트: http://localhost:${PORT}/api`);
});
