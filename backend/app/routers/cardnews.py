from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import base64
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import io
import os
import requests
from pathlib import Path
from anthropic import Anthropic
import asyncio
import re
import httpx
import google.generativeai as genai

# AI Agents 임포트
from ..agents import AgenticCardNewsWorkflow

router = APIRouter(prefix="/api", tags=["cardnews"])

# ==================== 설정 ====================

# 폰트 디렉토리
FONT_DIR = Path(__file__).parent.parent.parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)

# 카드 크기
CARD_WIDTH = 1080
CARD_HEIGHT = 1080

# 색상 테마 (확장됨)
COLOR_THEMES = {
    "warm": {
        "primary": (255, 139, 90),
        "secondary": (255, 229, 217),
        "accent": (212, 101, 74),
        "text": "white",
        "shadow": (0, 0, 0, 120),
        "gradient_type": "vertical"
    },
    "cool": {
        "primary": (74, 144, 226),
        "secondary": (227, 242, 253),
        "accent": (46, 92, 138),
        "text": "white",
        "shadow": (0, 0, 0, 120),
        "gradient_type": "vertical"
    },
    "vibrant": {
        "primary": (255, 107, 157),
        "secondary": (255, 229, 238),
        "accent": (233, 30, 99),
        "text": "white",
        "shadow": (0, 0, 0, 120),
        "gradient_type": "radial"
    },
    "minimal": {
        "primary": (66, 66, 66),
        "secondary": (245, 245, 245),
        "accent": (33, 33, 33),
        "text": "white",
        "shadow": (0, 0, 0, 120),
        "gradient_type": "vertical"
    },
    "sunset": {
        "primary": (255, 94, 77),
        "secondary": (255, 176, 59),
        "accent": (200, 40, 50),
        "text": "white",
        "shadow": (0, 0, 0, 150),
        "gradient_type": "diagonal"
    },
    "ocean": {
        "primary": (26, 188, 156),
        "secondary": (52, 152, 219),
        "accent": (22, 160, 133),
        "text": "white",
        "shadow": (0, 0, 0, 120),
        "gradient_type": "diagonal"
    },
    "purple": {
        "primary": (142, 68, 173),
        "secondary": (155, 89, 182),
        "accent": (102, 51, 153),
        "text": "white",
        "shadow": (0, 0, 0, 130),
        "gradient_type": "radial"
    },
    "pastel": {
        "primary": (255, 209, 220),
        "secondary": (190, 227, 248),
        "accent": (255, 160, 180),
        "text": "#333333",
        "shadow": (0, 0, 0, 80),
        "gradient_type": "vertical"
    },
    "black": {
        "primary": (0, 0, 0),
        "secondary": (30, 30, 30),
        "accent": (50, 50, 50),
        "text": "white",
        "shadow": (0, 0, 0, 0),
        "gradient_type": "vertical"
    },
    "blue": {
        "primary": (0, 26, 255),
        "secondary": (0, 26, 255),
        "accent": (0, 26, 255),
        "text": "white",
        "shadow": (0, 0, 0, 0),
        "gradient_type": "vertical"
    },
    "orange": {
        "primary": (255, 94, 0),
        "secondary": (255, 94, 0),
        "accent": (255, 94, 0),
        "text": "white",
        "shadow": (0, 0, 0, 0),
        "gradient_type": "vertical"
    }
}

# 용도 맵핑
PURPOSE_MAP = {
    'promotion': '프로모션/할인 홍보',
    'menu': '신메뉴/상품 소개',
    'info': '정보 전달/팁 공유',
    'event': '이벤트/행사 안내'
}

# 배지 텍스트
BADGE_TEXT_MAP = {
    'promotion': '프로모션',
    'menu': '신메뉴',
    'info': '정보',
    'event': '이벤트'
}

# ==================== 폰트 관리 ====================

class FontManager:
    """폰트 다운로드 및 로드 관리"""

    FONTS = {
        "rounded_bold": {
            "name": "NotoSansKR-Bold.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
        },
        "rounded_medium": {
            "name": "NotoSansKR-Medium.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Medium.otf"
        },
        "rounded_regular": {
            "name": "NotoSansKR-Regular.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
        },
        "sharp_bold": {
            "name": "BlackHanSans-Regular.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Black.otf"
        },
        "sharp_regular": {
            "name": "NanumGothic-Regular.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
        },
        "modern_bold": {
            "name": "NanumSquareRound-Bold.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
        },
        "modern_regular": {
            "name": "NanumSquareRound-Regular.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
        },
        "cute_bold": {
            "name": "Sunflower-Bold.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
        },
        "cute_regular": {
            "name": "Sunflower-Medium.ttf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Medium.otf"
        }
    }

    @staticmethod
    def download_font(font_name: str, url: str) -> Optional[Path]:
        """폰트 다운로드"""
        font_path = FONT_DIR / font_name
        if font_path.exists():
            return font_path

        try:
            print(f"📥 폰트 다운로드 중: {font_name}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            font_path.write_bytes(response.content)
            print(f"✅ 폰트 다운로드 완료: {font_name}")
            return font_path
        except Exception as e:
            print(f"⚠️ 폰트 다운로드 실패: {e}")
            return None

    @classmethod
    def get_font(cls, font_style: str, font_size: int, weight: str = "light") -> ImageFont.FreeTypeFont:
        """폰트 가져오기

        Args:
            font_style: 폰트 스타일 (rounded, sharp, modern, cute)
            font_size: 폰트 크기
            weight: 폰트 굵기 (light, medium, bold)
        """
        # weight에 따라 폰트 키 결정
        # light: regular 폰트 (얇게)
        # medium: medium 폰트 (중간)
        # bold: bold 폰트 (굵게)

        if weight == "bold":
            font_map = {
                "rounded": "rounded_bold",
                "sharp": "sharp_bold",
                "modern": "modern_bold",
                "cute": "cute_bold"
            }
        elif weight == "medium":
            font_map = {
                "rounded": "rounded_medium",
                "sharp": "sharp_regular",  # sharp는 medium이 없어서 regular 사용
                "modern": "modern_regular",  # modern은 medium이 없어서 regular 사용
                "cute": "cute_regular"
            }
        else:  # light
            font_map = {
                "rounded": "rounded_regular",
                "sharp": "sharp_regular",
                "modern": "modern_regular",
                "cute": "cute_regular"
            }

        font_key = font_map.get(font_style, "rounded_regular")

        # 폰트 다운로드
        font_info = cls.FONTS[font_key]
        font_path = cls.download_font(font_info["name"], font_info["url"])

        # 폰트 로드
        if font_path and font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), font_size)
            except Exception as e:
                print(f"⚠️ 폰트 로드 실패: {e}")

        # 폴백 폰트
        try:
            return ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size)
        except:
            return ImageFont.load_default()

# ==================== AI 콘텐츠 생성 ====================

class AIContentGenerator:
    """AI를 사용한 카드뉴스 콘텐츠 생성"""

    @staticmethod
    async def generate_cardnews_content(description: str, purpose: str) -> List[dict]:
        """사용자 설명을 기반으로 1장의 카드뉴스 콘텐츠 생성"""
        try:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_key:
                print("⚠️ ANTHROPIC_API_KEY가 설정되지 않음")
                return []

            client = Anthropic()

            prompt = f"""당신은 SNS 마케팅 전문가입니다. 다음 설명을 바탕으로 1장의 카드뉴스를 기획해주세요.

**사용자 입력**: {description}
**용도**: {PURPOSE_MAP.get(purpose, purpose)}

**카드뉴스 구성 가이드**:
- 핵심 메시지를 간결하고 임팩트 있게 전달
- 관심을 끄는 제목과 행동을 유도하는 설명

**작성 규칙**:
- 제목: 간결하고 임팩트 있게 (최대 15자)
- 설명: 구체적이고 매력적으로 (최대 35자)
- 이모지 제거, 순수 한글/영문/숫자만 사용

JSON 배열 형식으로만 응답:
[
  {{"title": "카드 제목", "description": "카드 설명"}}
]"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # JSON 추출
            json_match = re.search(r'\[[\s\S]*\]', response_text)

            if json_match:
                cards = json.loads(json_match.group(0))
                if isinstance(cards, list) and len(cards) == 1:
                    print(f"✅ AI가 1장의 카드뉴스 콘텐츠 생성 완료:")
                    print(f"   1. {cards[0]['title']} - {cards[0]['description']}")
                    return cards

            print("⚠️ AI 응답 형식이 올바르지 않음")
            return []

        except Exception as e:
            print(f"⚠️ AI 콘텐츠 생성 실패: {str(e)}")
            return []

# ==================== 텍스트 렌더링 ====================

class TextRenderer:
    """텍스트를 이미지에 렌더링"""

    @staticmethod
    def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
        """텍스트를 줄바꿈 처리"""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]

    @staticmethod
    def draw_text_with_shadow(
        image: Image.Image,
        text: str,
        position: tuple,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        max_width: Optional[int] = None,
        shadow: bool = True,
        shadow_color: tuple = (0, 0, 0, 120),
        align: str = "left",
        line_spacing: int = 10
    ):
        """그림자가 있는 텍스트 그리기"""
        draw = ImageDraw.Draw(image, 'RGBA')

        # 텍스트 줄바꿈
        if max_width:
            lines = TextRenderer.wrap_text(text, font, max_width, draw)
        else:
            lines = [text]

        # 각 줄 그리기
        y = position[1]
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 정렬에 따라 x 위치 조정
            x = position[0]
            if align == "center" and max_width:
                x = position[0] + (max_width - text_width) // 2
            elif align == "right" and max_width:
                x = position[0] + max_width - text_width

            # 그림자 효과
            if shadow:
                shadow_offset = 3
                for offset_x in range(-shadow_offset, shadow_offset + 1):
                    for offset_y in range(-shadow_offset, shadow_offset + 1):
                        if offset_x == 0 and offset_y == 0:
                            continue
                        draw.text(
                            (x + offset_x, y + offset_y),
                            line,
                            fill=shadow_color,
                            font=font
                        )

            # 메인 텍스트
            draw.text((x, y), line, fill=color, font=font)

            # 다음 줄 위치
            y += text_height + line_spacing

# ==================== 카드 빌더 ====================

class CardNewsBuilder:
    """카드뉴스 이미지 생성"""

    def __init__(self, theme: dict, font_style: str, purpose: str, layout_type: str = "bottom", font_weight: str = "light"):
        self.theme = theme
        self.font_style = font_style
        self.purpose = purpose
        self.layout_type = layout_type  # top, center, bottom
        self.font_weight = font_weight  # light, medium, bold
        self.badge_text = BADGE_TEXT_MAP.get(purpose, '정보')

    def prepare_background(self, background_image: Image.Image) -> Image.Image:
        """배경 이미지 준비"""
        # RGB 변환
        if background_image.mode != 'RGB':
            background_image = background_image.convert('RGB')

        # 크기 조정
        img = background_image.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

        # 어둡게 처리
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.6)

        return img

    def add_logo(self, image: Image.Image):
        """로고 배지 추가"""
        import os

        # 로고 파일 경로
        logo_path = os.path.join(os.path.dirname(__file__), "../../../public/logo192.png")

        # 프로젝트 루트 기준 경로도 시도
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "../../../../public/logo192.png")

        if not os.path.exists(logo_path):
            # 절대 경로로 시도
            logo_path = "/Users/ohhwayoung/Desktop/ai-content/ai-camp-2nd-llm-agent-service-project-contents-team/public/logo192.png"

        try:
            # 로고 이미지 로드
            logo = Image.open(logo_path).convert("RGBA")

            # 로고 크기 조정 (60x60)
            logo_size = 60
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # 로고 위치 (상단 가운데)
            logo_x = (CARD_WIDTH - logo_size) // 2
            logo_y = 40

            # 로고 붙이기 (투명도 유지)
            image.paste(logo, (logo_x, logo_y), logo)
        except Exception as e:
            print(f"로고 로드 실패: {e}")

    def add_content(self, image: Image.Image, title: str, description: str, page_num: int = 1):
        """콘텐츠 텍스트 추가 (위치 선택 가능)"""

        # 폰트 사이즈 축소
        title_font = FontManager.get_font(self.font_style, 48, weight=self.font_weight)
        desc_font = FontManager.get_font(self.font_style, 28, weight=self.font_weight)

        # 위치에 따른 Y 좌표 설정
        if self.layout_type == "top":
            title_y = 150
            desc_y = 220
        elif self.layout_type == "bottom":
            title_y = CARD_HEIGHT - 250
            desc_y = CARD_HEIGHT - 180
        else:  # center (기본값)
            title_y = CARD_HEIGHT // 2 - 30
            desc_y = CARD_HEIGHT // 2 + 40

        align = "center"

        # 제목 (중앙 정렬)
        TextRenderer.draw_text_with_shadow(
            image,
            title,
            (80, title_y),
            title_font,
            color=self.theme["text"],
            max_width=CARD_WIDTH - 160,
            shadow=False,
            align=align,
            line_spacing=12
        )

        # 설명 (중앙 정렬)
        if description:
            TextRenderer.draw_text_with_shadow(
                image,
                description,
                (80, desc_y),
                desc_font,
                color=self.theme["text"],
                max_width=CARD_WIDTH - 160,
                shadow=False,
                align=align,
                line_spacing=8
            )

    def build_card(
        self,
        background_image: Image.Image,
        title: str,
        description: str,
        page_num: int = 1
    ) -> Image.Image:
        """완전한 카드 생성"""
        # 배경 준비
        card = self.prepare_background(background_image)

        # 로고 추가
        self.add_logo(card)

        # 콘텐츠 추가
        self.add_content(card, title, description, page_num)

        return card

# ==================== API 엔드포인트 ====================

@router.post("/generate-cardnews-stream")
async def generate_cardnews_stream(
    images: List[UploadFile] = File(...),
    titles: str = Form(...),
    descriptions: str = Form(...),
    fontStyle: str = Form(default="rounded"),
    colorTheme: str = Form(default="warm"),
    purpose: str = Form(default="promotion"),
    layoutStyle: str = Form(default="overlay"),
    layoutType: str = Form(default="bottom")
):
    """카드뉴스 스트리밍 생성 API"""

    async def event_stream():
        try:
            # 검증
            if not images or len(images) == 0:
                yield f"data: {json.dumps({'type': 'error', 'message': '최소 1개 이상의 이미지가 필요합니다.'})}\n\n"
                return

            # 상태 전송
            yield f"data: {json.dumps({'type': 'status', 'message': 'AI가 카드뉴스 콘텐츠를 분석하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.1)

            # JSON 파싱
            title_array = json.loads(titles)
            user_description = title_array[0] if len(title_array) > 0 else ""

            # AI 콘텐츠 생성
            ai_cards = await AIContentGenerator.generate_cardnews_content(user_description, purpose)

            if not ai_cards or len(ai_cards) != 1:
                yield f"data: {json.dumps({'type': 'error', 'message': 'AI 콘텐츠 생성에 실패했습니다.'})}\n\n"
                return

            # 배경 이미지 로드
            image_data = await images[0].read()
            background_image = Image.open(io.BytesIO(image_data))

            # 테마 선택
            theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])

            # 카드 빌더 생성
            builder = CardNewsBuilder(theme, fontStyle, purpose, layoutType)

            # 카드 생성
            for i, card_content in enumerate(ai_cards):
                yield f"data: {json.dumps({'type': 'status', 'message': '카드 생성 중...'})}\n\n"

                title = card_content["title"]
                description = card_content["description"]

                # 카드 생성
                card_image = builder.build_card(background_image, title, description, i + 1)

                # Base64 변환
                buffer = io.BytesIO()
                card_image.save(buffer, format="PNG")
                base64_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

                # 카드 전송
                yield f"data: {json.dumps({'type': 'card', 'index': i, 'card': base64_image})}\n\n"
                await asyncio.sleep(0.1)

            # 완료 메시지
            yield f"data: {json.dumps({'type': 'complete', 'message': '카드뉴스 생성이 완료되었습니다!'})}\n\n"

        except Exception as e:
            print(f"스트리밍 카드뉴스 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/generate-cardnews")
async def generate_cardnews(
    images: List[UploadFile] = File(...),
    titles: str = Form(...),
    descriptions: str = Form(...),
    fontStyle: str = Form(default="rounded"),
    colorTheme: str = Form(default="warm"),
    purpose: str = Form(default="promotion"),
    layoutStyle: str = Form(default="overlay"),
    layoutType: str = Form(default="bottom")
):
    """카드뉴스 생성 API (비스트리밍)"""
    try:
        if not images or len(images) == 0:
            raise HTTPException(status_code=400, detail="최소 1개 이상의 이미지가 필요합니다.")

        print(f"📰 카드뉴스 생성 시작")
        print(f"🎨 스타일: 폰트={fontStyle}, 색상={colorTheme}, 용도={purpose}")

        # JSON 파싱
        title_array = json.loads(titles)
        user_description = title_array[0] if len(title_array) > 0 else ""

        # AI 콘텐츠 생성
        print(f"\n🤖 AI가 '{user_description}'를 기반으로 1장의 카드뉴스 콘텐츠를 생성 중...")
        ai_cards = await AIContentGenerator.generate_cardnews_content(user_description, purpose)

        if not ai_cards or len(ai_cards) != 1:
            raise HTTPException(status_code=500, detail="AI 콘텐츠 생성에 실패했습니다.")

        # 배경 이미지 로드
        image_data = await images[0].read()
        background_image = Image.open(io.BytesIO(image_data))

        # 테마 선택
        theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])

        # 카드 빌더 생성
        builder = CardNewsBuilder(theme, fontStyle, purpose, layoutType)

        # 카드 생성
        card_news_images = []
        for i, card_content in enumerate(ai_cards):
            print(f"\n📄 {i + 1}번째 카드 생성 중...")

            title = card_content["title"]
            description = card_content["description"]

            # 카드 생성
            card_image = builder.build_card(background_image, title, description, i + 1)

            # Base64 변환
            buffer = io.BytesIO()
            card_image.save(buffer, format="PNG")
            base64_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            card_news_images.append(base64_image)

            print(f"✅ 카드 {i + 1} 생성 완료")

        print(f"\n✅ 총 {len(card_news_images)}장의 카드뉴스 생성 완료\n")

        return {
            "success": True,
            "images": card_news_images,
            "count": len(card_news_images)
        }

    except Exception as e:
        print(f"카드뉴스 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"카드뉴스 생성 중 오류가 발생했습니다: {str(e)}")


# ==================== AI Agentic 카드뉴스 생성 (스트리밍) ====================

@router.post("/generate-agentic-cardnews-stream")
async def generate_agentic_cardnews_stream(
    prompt: str = Form(...),
    purpose: str = Form(default="info"),
    fontStyle: str = Form(default="rounded"),
    colorTheme: str = Form(default="warm"),
    generateImages: bool = Form(default=True),
    layoutType: str = Form(default="bottom"),
    fontWeight: str = Form(default="light")
):
    """
    AI Agentic 방식으로 카드뉴스 자동 생성 (스트리밍)

    실시간으로 AI 처리 과정을 사용자에게 전달
    """

    async def event_stream():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': '🤖 AI가 프롬프트를 분석하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.1)

            # Step 1: 요청 분석
            from ..agents import OrchestratorAgent
            orchestrator = OrchestratorAgent()
            analysis = await orchestrator.analyze_user_request(prompt, purpose)

            yield f"data: {json.dumps({'type': 'analysis', 'data': analysis})}\n\n"
            page_count = analysis.get('page_count', 5)
            yield f"data: {json.dumps({'type': 'status', 'message': f'📋 {page_count}페이지 카드뉴스를 기획합니다...'})}\n\n"
            await asyncio.sleep(0.1)

            # Step 2: 콘텐츠 기획
            from ..agents import ContentPlannerAgent
            planner = ContentPlannerAgent()
            pages = await planner.plan_cardnews_pages(prompt, analysis)

            for i, page in enumerate(pages):
                yield f"data: {json.dumps({'type': 'page_planned', 'page': i+1, 'title': page['title'], 'content': page['content']})}\n\n"
                await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'status', 'message': '🎨 각 페이지의 고유한 비주얼 프롬프트를 생성합니다...'})}\n\n"

            # Step 3: 비주얼 프롬프트 생성
            from ..agents import VisualDesignerAgent
            designer = VisualDesignerAgent()
            pages = await designer.generate_page_visuals(pages, analysis.get('style', 'modern'))

            for i, page in enumerate(pages):
                yield f"data: {json.dumps({'type': 'prompt_generated', 'page': i+1, 'prompt': page.get('image_prompt', ''), 'log': page.get('prompt_generation_log', '')})}\n\n"
                await asyncio.sleep(0.1)

            # Step 4: 품질 검증
            yield f"data: {json.dumps({'type': 'status', 'message': '🔍 콘텐츠 품질을 검증하고 있습니다...'})}\n\n"
            from ..agents import QualityAssuranceAgent
            qa = QualityAssuranceAgent()
            quality_report = await qa.validate_and_improve(pages, prompt, analysis)

            yield f"data: {json.dumps({'type': 'quality_report', 'score': quality_report.get('overall_score', 0)})}\n\n"

            # Step 5: 이미지 생성
            yield f"data: {json.dumps({'type': 'status', 'message': '🖼️ 각 페이지의 배경 이미지를 생성합니다...'})}\n\n"

            background_images = []
            google_api_key = os.getenv('GOOGLE_API_KEY')

            for i, page in enumerate(pages):
                yield f"data: {json.dumps({'type': 'status', 'message': f'📸 페이지 {i+1} 이미지 생성 중... ({i+1}/{len(pages)})'})}\n\n"

                try:
                    if generateImages and google_api_key:
                        image_url = await generate_background_image_with_gemini(
                            page.get('image_prompt', page.get('visual_concept', 'modern background'))
                        )
                        background_images.append(image_url)
                    else:
                        background_images.append(create_fallback_background(colorTheme))
                except Exception as e:
                    print(f"  ⚠️ 페이지 {i+1} 이미지 생성 실패: {e}")
                    background_images.append(create_fallback_background(colorTheme))

                yield f"data: {json.dumps({'type': 'image_generated', 'page': i+1})}\n\n"
                await asyncio.sleep(0.1)

            # Step 6: 최종 카드 조립
            yield f"data: {json.dumps({'type': 'status', 'message': '📰 최종 카드뉴스를 조립하고 있습니다...'})}\n\n"

            theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])
            builder = CardNewsBuilder(theme, fontStyle, purpose, layoutType, fontWeight)

            for i, (page, bg_image_data) in enumerate(zip(pages, background_images)):
                # 배경 이미지 로드
                if bg_image_data.startswith('data:image'):
                    image_data = bg_image_data.split(',')[1]
                    bg_image = Image.open(io.BytesIO(base64.b64decode(image_data)))
                else:
                    response = requests.get(bg_image_data, timeout=30)
                    bg_image = Image.open(io.BytesIO(response.content))

                # 카드 생성 (사용자 프롬프트만 표시, AI 생성 title/content 제거)
                card = builder.build_card(bg_image, prompt, "", i + 1)

                # Base64 변환
                buffer = io.BytesIO()
                card.save(buffer, format="PNG")
                card_base64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

                yield f"data: {json.dumps({'type': 'card', 'index': i, 'card': card_base64, 'title': page['title']})}\n\n"
                await asyncio.sleep(0.1)

            # 완료
            result = {
                'type': 'complete',
                'count': len(pages),
                'quality_score': quality_report.get('overall_score'),
                'target_audience': analysis.get('target_audience'),
                'tone': analysis.get('tone')
            }
            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            print(f"\n❌ AI 카드뉴스 스트리밍 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ==================== AI Agentic 카드뉴스 생성 (Non-streaming) ====================

@router.post("/generate-agentic-cardnews")
async def generate_agentic_cardnews(
    prompt: str = Form(...),
    purpose: str = Form(default="info"),
    fontStyle: str = Form(default="rounded"),
    colorTheme: str = Form(default="warm"),
    generateImages: bool = Form(default=True),
    layoutType: str = Form(default="bottom")
):
    """
    AI Agentic 방식으로 카드뉴스 자동 생성

    사용자가 입력한 프롬프트를 기반으로:
    1. AI가 페이지별 내용 구성
    2. 각 페이지의 비주얼 컨셉 생성
    3. 품질 검증 및 개선
    4. 최종 카드뉴스 이미지 생성

    Args:
        prompt: 사용자 입력 프롬프트 (예: "새로운 카페 오픈 홍보")
        purpose: 목적 (promotion/menu/info/event)
        fontStyle: 폰트 스타일 (rounded/sharp)
        colorTheme: 색상 테마 (warm/cool/vibrant/minimal)
        generateImages: 배경 이미지 자동 생성 여부
    """
    try:
        print("\n" + "="*80)
        print("🤖 AI Agentic 카드뉴스 생성 시작")
        print(f"📝 프롬프트: {prompt}")
        print(f"🎯 목적: {purpose}")
        print("="*80 + "\n")

        # Step 1: AI Agentic 워크플로우 실행
        workflow = AgenticCardNewsWorkflow()
        result = await workflow.execute(prompt, purpose)

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"AI 워크플로우 실패: {result.get('error', '알 수 없는 오류')}"
            )

        analysis = result['analysis']
        pages = result['pages']
        quality_report = result['quality_report']

        # Step 2: 배경 이미지 생성 (옵션)
        print("\n🖼️ 배경 이미지 생성 중...")
        background_images = []

        if generateImages:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key:
                for i, page in enumerate(pages):
                    try:
                        print(f"  📸 페이지 {i+1} 이미지 생성 중...")
                        image_url = await generate_background_image_with_gemini(
                            page.get('image_prompt', page.get('visual_concept', 'modern background'))
                        )
                        background_images.append(image_url)
                        print(f"  ✅ 페이지 {i+1} 이미지 생성 완료")
                    except Exception as e:
                        print(f"  ⚠️ 페이지 {i+1} 이미지 생성 실패: {e}")
                        # 폴백: 단색 배경 생성
                        background_images.append(create_fallback_background(colorTheme))
            else:
                print("  ⚠️ Google API Key 없음, 단색 배경 사용")
                for _ in pages:
                    background_images.append(create_fallback_background(colorTheme))
        else:
            # 단색 배경 사용
            for _ in pages:
                background_images.append(create_fallback_background(colorTheme))

        # Step 3: 최종 카드뉴스 생성
        print("\n📰 최종 카드뉴스 조립 중...")
        theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])
        builder = CardNewsBuilder(theme, fontStyle, purpose, layoutType)

        final_cards = []
        for i, (page, bg_image_data) in enumerate(zip(pages, background_images)):
            print(f"  🎨 카드 {i+1}/{len(pages)} 생성 중...")

            # 배경 이미지 로드
            if bg_image_data.startswith('data:image'):
                # Base64 디코딩
                image_data = bg_image_data.split(',')[1]
                bg_image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            else:
                # URL에서 다운로드
                response = requests.get(bg_image_data, timeout=30)
                bg_image = Image.open(io.BytesIO(response.content))

            # 카드 생성 (사용자 프롬프트만 표시, AI 생성 title/content 제거)
            card = builder.build_card(
                bg_image,
                prompt,
                "",
                i + 1
            )

            # Base64 변환
            buffer = io.BytesIO()
            card.save(buffer, format="PNG")
            card_base64 = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            final_cards.append(card_base64)

            print(f"  ✅ 카드 {i+1} 완성")

        print("\n" + "="*80)
        print(f"✅ {len(final_cards)}장의 AI 카드뉴스 생성 완료!")
        print("="*80 + "\n")

        return {
            "success": True,
            "cards": final_cards,
            "count": len(final_cards),
            "analysis": {
                "page_count": analysis.get('page_count'),
                "target_audience": analysis.get('target_audience'),
                "tone": analysis.get('tone'),
                "style": analysis.get('style')
            },
            "quality_score": quality_report.get('overall_score') if quality_report else None,
            "pages_info": [
                {
                    "page": p['page'],
                    "title": p['title'],
                    "content": p['content']
                }
                for p in pages
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ AI 카드뉴스 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"AI 카드뉴스 생성 중 오류: {str(e)}"
        )


async def generate_background_image_with_gemini(prompt: str) -> str:
    """Gemini 2.0 Flash로 배경 이미지 생성"""
    google_api_key = os.getenv('GOOGLE_API_KEY')

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={google_api_key}",
            json={
                "contents": [{
                    "parts": [{
                        "text": f"Generate an image: {prompt}"
                    }]
                }]
            },
            headers={"Content-Type": "application/json"}
        )

    if response.status_code != 200:
        raise Exception(f"Gemini API 오류: {response.status_code}")

    data = response.json()

    # 이미지 추출
    if data.get("candidates") and len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        if candidate.get("content") and candidate["content"].get("parts"):
            for part in candidate["content"]["parts"]:
                if part.get("inline_data") and part["inline_data"].get("data"):
                    mime_type = part["inline_data"].get("mime_type", "image/png")
                    image_data = part["inline_data"]["data"]
                    return f"data:{mime_type};base64,{image_data}"

    raise Exception("Gemini에서 이미지를 추출할 수 없습니다")


def create_fallback_background(color_theme: str) -> str:
    """폴백용 단색 배경 생성"""
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES["warm"])

    # 단색 배경 생성 (그라데이션 제거)
    primary = theme["primary"]
    img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=primary)

    # Base64 변환
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
