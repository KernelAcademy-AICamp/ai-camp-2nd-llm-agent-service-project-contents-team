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

router = APIRouter(prefix="/api", tags=["cardnews"])

# ==================== 설정 ====================

# 폰트 디렉토리
FONT_DIR = Path(__file__).parent.parent.parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)

# 카드 크기
CARD_WIDTH = 1080
CARD_HEIGHT = 1080

# 색상 테마
COLOR_THEMES = {
    "warm": {
        "primary": (255, 139, 90),
        "secondary": (255, 229, 217),
        "accent": (212, 101, 74),
        "text": "white",
        "shadow": (0, 0, 0, 120)
    },
    "cool": {
        "primary": (74, 144, 226),
        "secondary": (227, 242, 253),
        "accent": (46, 92, 138),
        "text": "white",
        "shadow": (0, 0, 0, 120)
    },
    "vibrant": {
        "primary": (255, 107, 157),
        "secondary": (255, 229, 238),
        "accent": (233, 30, 99),
        "text": "white",
        "shadow": (0, 0, 0, 120)
    },
    "minimal": {
        "primary": (66, 66, 66),
        "secondary": (245, 245, 245),
        "accent": (33, 33, 33),
        "text": "white",
        "shadow": (0, 0, 0, 120)
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
            "url": "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Bold.ttf"
        },
        "rounded_regular": {
            "name": "NotoSansKR-Regular.ttf",
            "url": "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Regular.ttf"
        },
        "sharp_bold": {
            "name": "BlackHanSans-Regular.ttf",
            "url": "https://github.com/google/fonts/raw/main/ofl/blackhansans/BlackHanSans-Regular.ttf"
        },
        "sharp_regular": {
            "name": "NanumGothic-Regular.ttf",
            "url": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
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
    def get_font(cls, font_style: str, font_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """폰트 가져오기"""
        # 폰트 키 결정
        if font_style == "rounded":
            font_key = "rounded_bold" if bold else "rounded_regular"
        else:  # sharp
            font_key = "sharp_bold" if bold else "sharp_regular"

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

    def __init__(self, theme: dict, font_style: str, purpose: str):
        self.theme = theme
        self.font_style = font_style
        self.purpose = purpose
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

    def add_badge(self, image: Image.Image):
        """배지 추가"""
        draw = ImageDraw.Draw(image)

        # 배지 위치 및 크기
        badge_x, badge_y = 50, 50
        badge_width, badge_height = 180, 70

        # 배지 배경
        draw.rectangle(
            [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
            fill=self.theme["accent"]
        )

        # 배지 하단 라인
        draw.rectangle(
            [(badge_x, badge_y + badge_height), (badge_x + badge_width, badge_y + badge_height + 5)],
            fill=(255, 255, 255)
        )

        # 배지 텍스트
        font = FontManager.get_font(self.font_style, 32, bold=True)
        TextRenderer.draw_text_with_shadow(
            image,
            self.badge_text,
            (badge_x + 20, badge_y + 20),
            font,
            color="white",
            max_width=badge_width - 40,
            shadow=False,
            align="center"
        )

    def add_content(self, image: Image.Image, title: str, description: str, page_num: int = 1):
        """콘텐츠 텍스트 추가"""
        # 제목
        title_font = FontManager.get_font(self.font_style, 80, bold=True)
        TextRenderer.draw_text_with_shadow(
            image,
            title,
            (80, CARD_HEIGHT - 280),
            title_font,
            color=self.theme["text"],
            max_width=CARD_WIDTH - 160,
            shadow=True,
            shadow_color=self.theme["shadow"],
            align="left",
            line_spacing=15
        )

        # 설명
        if description:
            desc_font = FontManager.get_font(self.font_style, 40, bold=False)
            TextRenderer.draw_text_with_shadow(
                image,
                description,
                (80, CARD_HEIGHT - 160),
                desc_font,
                color=self.theme["text"],
                max_width=CARD_WIDTH - 160,
                shadow=True,
                shadow_color=self.theme["shadow"],
                align="left",
                line_spacing=10
            )

        # 페이지 번호
        page_font = FontManager.get_font(self.font_style, 20, bold=False)
        page_text = f"{page_num} / 1"
        TextRenderer.draw_text_with_shadow(
            image,
            page_text,
            (CARD_WIDTH - 120, CARD_HEIGHT - 60),
            page_font,
            color=self.theme["text"],
            shadow=False,
            align="left"
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

        # 배지 추가
        self.add_badge(card)

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
    layoutStyle: str = Form(default="overlay")
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
            builder = CardNewsBuilder(theme, fontStyle, purpose)

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
    layoutStyle: str = Form(default="overlay")
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
        builder = CardNewsBuilder(theme, fontStyle, purpose)

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
