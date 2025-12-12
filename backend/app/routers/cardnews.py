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
        # Pretendard (현대적, 가독성 우수)
        "pretendard_bold": {
            "name": "Pretendard-Bold.otf",
            "url": "https://cdn.jsdelivr.net/gh/fonts-archive/Pretendard/Pretendard-Bold.otf"
        },
        "pretendard_medium": {
            "name": "Pretendard-Medium.otf",
            "url": "https://cdn.jsdelivr.net/gh/fonts-archive/Pretendard/Pretendard-Medium.otf"
        },
        "pretendard_regular": {
            "name": "Pretendard-Regular.otf",
            "url": "https://cdn.jsdelivr.net/gh/fonts-archive/Pretendard/Pretendard-Regular.otf"
        },

        # Noto Sans KR (Google 웹폰트)
        "noto_sans_kr_bold": {
            "name": "NotoSansKR-Bold.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
        },
        "noto_sans_kr_medium": {
            "name": "NotoSansKR-Medium.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Medium.otf"
        },
        "noto_sans_kr_regular": {
            "name": "NotoSansKR-Regular.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
        },

        # Spoqa Han Sans (기업용, 깔끔함)
        "spoqa_bold": {
            "name": "SpoqaHanSansNeo-Bold.otf",
            "url": "https://cdn.jsdelivr.net/gh/spoqa/spoqa-han-sans@latest/Subset/SpoqaHanSansNeo/SpoqaHanSansNeo-Bold.otf"
        },
        "spoqa_medium": {
            "name": "SpoqaHanSansNeo-Medium.otf",
            "url": "https://cdn.jsdelivr.net/gh/spoqa/spoqa-han-sans@latest/Subset/SpoqaHanSansNeo/SpoqaHanSansNeo-Medium.otf"
        },
        "spoqa_regular": {
            "name": "SpoqaHanSansNeo-Regular.otf",
            "url": "https://cdn.jsdelivr.net/gh/spoqa/spoqa-han-sans@latest/Subset/SpoqaHanSansNeo/SpoqaHanSansNeo-Regular.otf"
        },

        # 기존 폰트 유지 (호환성)
        "rounded_bold": {
            "name": "NotoSansKR-Bold-Legacy.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"
        },
        "rounded_medium": {
            "name": "NotoSansKR-Medium-Legacy.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Medium.otf"
        },
        "rounded_regular": {
            "name": "NotoSansKR-Regular-Legacy.otf",
            "url": "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
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
    def get_font(cls, font_style: str, font_size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
        """폰트 가져오기

        Args:
            font_style: 폰트 스타일 (pretendard, noto_sans_kr, spoqa, rounded)
            font_size: 폰트 크기
            weight: 폰트 굵기 (regular, medium, bold)
        """
        # weight에 따라 폰트 키 결정
        # regular: 기본 폰트
        # medium: 중간 굵기
        # bold: 굵은 폰트

        if weight == "bold":
            font_map = {
                "pretendard": "pretendard_bold",
                "noto_sans_kr": "noto_sans_kr_bold",
                "spoqa": "spoqa_bold",
                "rounded": "rounded_bold",  # 호환성 유지
            }
        elif weight == "medium":
            font_map = {
                "pretendard": "pretendard_medium",
                "noto_sans_kr": "noto_sans_kr_medium",
                "spoqa": "spoqa_medium",
                "rounded": "rounded_medium",  # 호환성 유지
            }
        else:  # regular
            font_map = {
                "pretendard": "pretendard_regular",
                "noto_sans_kr": "noto_sans_kr_regular",
                "spoqa": "spoqa_regular",
                "rounded": "rounded_regular",  # 호환성 유지
            }

        font_key = font_map.get(font_style, "pretendard_regular")  # 기본 폰트를 Pretendard로 변경

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

    @staticmethod
    def draw_bullet_point(
        image: Image.Image,
        text: str,
        position: tuple,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        bullet_symbol: str = "•"
    ):
        """Bullet point 렌더링 (• 기호 처리 + 들여쓰기)"""
        draw = ImageDraw.Draw(image, 'RGBA')
        x, y = position

        # "• " 또는 "- " 제거 후 텍스트 추출
        clean_text = text.lstrip('•- ').strip()

        # Bullet 기호 그리기
        draw.text((x, y), bullet_symbol, font=font, fill=color)

        # 텍스트 그리기 (들여쓰기 30px)
        draw.text((x + 35, y), clean_text, font=font, fill=color)

    @staticmethod
    def draw_structured_content(
        image: Image.Image,
        content: List[str],
        start_y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        line_spacing: int = 50,
        start_x: int = 100
    ) -> int:
        """
        구조화된 콘텐츠 렌더링 (bullet points 배열)

        Returns:
            최종 y 위치 (다음 요소 렌더링에 활용)
        """
        current_y = start_y

        for line in content:
            TextRenderer.draw_bullet_point(
                image, line, (start_x, current_y), font, color
            )
            current_y += line_spacing

        return current_y

# ==================== 카드 빌더 ====================

class CardNewsBuilder:
    """카드뉴스 이미지 생성"""

    def __init__(self, theme: dict, font_style: str, purpose: str, layout_type: str = "bottom", font_weight: str = "light"):
        self.theme = theme
        self.font_style = font_style
        self.purpose = purpose
        self.layout_type = layout_type  # 하위 호환성 유지, 실제로는 미사용 (페이지별 layout 사용)
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
        """로고 배지 추가 (상단 중앙)"""
        import os

        # 로고 파일 경로 (ddukddak_white.png 사용)
        logo_path = os.path.join(os.path.dirname(__file__), "../../../public/ddukddak_white.png")

        # 프로젝트 루트 기준 경로도 시도
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "../../../../public/ddukddak_white.png")

        if not os.path.exists(logo_path):
            # 절대 경로로 시도
            logo_path = "/Users/ohhwayoung/Desktop/ai-content/ai-camp-2nd-llm-agent-service-project-contents-team/public/ddukddak_white.png"

        try:
            # 로고 이미지 로드
            logo = Image.open(logo_path).convert("RGBA")

            # 로고 크기 조정 (가로 비율 유지, 높이 50px 기준)
            logo_height = 50
            aspect_ratio = logo.width / logo.height
            logo_width = int(logo_height * aspect_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # 로고 위치 (상단 중앙)
            logo_x = (CARD_WIDTH - logo_width) // 2
            logo_y = 30

            # 로고 붙이기 (투명도 유지)
            image.paste(logo, (logo_x, logo_y), logo)
        except Exception as e:
            print(f"로고 로드 실패: {e}")

    def add_content(self, image: Image.Image, title: str, description: str, page_num: int = 1):
        """콘텐츠 텍스트 추가 (정중앙 배치)"""

        # 폰트 사이즈 축소 (36px로 줄임)
        title_font = FontManager.get_font(self.font_style, 36, weight=self.font_weight)
        desc_font = FontManager.get_font(self.font_style, 22, weight=self.font_weight)

        # 텍스트 높이 계산을 위한 임시 draw 객체
        draw = ImageDraw.Draw(image)

        # 제목 텍스트 줄바꿈 처리
        max_width = CARD_WIDTH - 160
        title_lines = TextRenderer.wrap_text(title, title_font, max_width, draw) if title else []
        desc_lines = TextRenderer.wrap_text(description, desc_font, max_width, draw) if description else []

        # 각 줄의 높이 계산
        title_line_height = 44  # 폰트 크기 + 여백
        desc_line_height = 30

        # 전체 텍스트 블록 높이 계산
        total_height = 0
        if title_lines:
            total_height += len(title_lines) * title_line_height
        if desc_lines:
            total_height += 20  # 제목과 설명 사이 간격
            total_height += len(desc_lines) * desc_line_height

        # 정중앙 Y 좌표 계산
        start_y = (CARD_HEIGHT - total_height) // 2

        # 위치에 따른 Y 좌표 조정
        if self.layout_type == "top":
            start_y = 150
        elif self.layout_type == "bottom":
            start_y = CARD_HEIGHT - total_height - 150

        align = "center"
        current_y = start_y

        # 제목 (중앙 정렬)
        if title:
            TextRenderer.draw_text_with_shadow(
                image,
                title,
                (80, current_y),
                title_font,
                color=self.theme["text"],
                max_width=max_width,
                shadow=False,
                align=align,
                line_spacing=8
            )
            current_y += len(title_lines) * title_line_height + 20

        # 설명 (중앙 정렬)
        if description:
            TextRenderer.draw_text_with_shadow(
                image,
                description,
                (80, current_y),
                desc_font,
                color=self.theme["text"],
                max_width=max_width,
                shadow=False,
                align=align,
                line_spacing=6
            )

    def build_card(
        self,
        background_image: Image.Image,
        title: str,
        description: str,
        page_num: int = 1
    ) -> Image.Image:
        """완전한 카드 생성 (기존 방식)"""
        # 배경 준비
        card = self.prepare_background(background_image)

        # 로고 추가
        self.add_logo(card)

        # 콘텐츠 추가
        self.add_content(card, title, description, page_num)

        return card

    def build_first_page(
        self,
        background_image: Image.Image,
        title: str,
        subtitle: str,
        page_num: int = 1,
        layout: str = "center"
    ) -> str:
        """
        첫 페이지 전용 렌더링 (제목 + 소제목 + AI 배경)
        Agent가 판단한 layout에 따라 텍스트 위치 조정
        """
        # 배경 준비
        card = self.prepare_background(background_image)

        # 로고 추가
        self.add_logo(card)

        # 폰트 설정 (2배 크기)
        title_font = FontManager.get_font(self.font_style, 96, weight='bold')
        subtitle_font = FontManager.get_font(self.font_style, 56, weight='medium')

        # 텍스트 총 높이 계산
        draw = ImageDraw.Draw(card)
        title_lines = TextRenderer.wrap_text(title, title_font, CARD_WIDTH - 120, draw)
        subtitle_lines = TextRenderer.wrap_text(subtitle, subtitle_font, CARD_WIDTH - 120, draw)

        title_height = len(title_lines) * 60  # 폰트 크기 + 여백
        subtitle_height = len(subtitle_lines) * 36
        total_height = title_height + subtitle_height + 20  # 제목-부제목 간격

        # Agent가 판단한 layout에 따라 시작 위치 결정
        if layout == "top":
            title_y = CARD_HEIGHT // 3  # 1/3 지점 (360px)
        elif layout == "bottom":
            title_y = CARD_HEIGHT - total_height - 150  # 하단
        else:  # center (기본값)
            title_y = (CARD_HEIGHT - total_height) // 2  # 중앙

        # 제목 렌더링 (중앙 정렬 수정: x 시작점을 60으로)
        TextRenderer.draw_text_with_shadow(
            card, title, (60, title_y),
            title_font, color=self.theme["text"],
            max_width=CARD_WIDTH - 120,
            align="center", shadow=True,
            line_spacing=24
        )

        # 소제목 렌더링 (제목 아래)
        subtitle_y = title_y + title_height + 40
        TextRenderer.draw_text_with_shadow(
            card, subtitle, (60, subtitle_y),
            subtitle_font, color=self.theme["text"],
            max_width=CARD_WIDTH - 120,
            align="center", shadow=False,
            line_spacing=16
        )

        # 페이지 번호
        self._add_page_number(card, page_num)

        # Base64 변환
        import io
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def build_content_page(
        self,
        bg_color: tuple,
        title: str,
        content_lines: List[str],
        page_num: int
    ) -> str:
        """
        본문 페이지 렌더링 (섹션 제목 + bullet points + 컬러 배경)
        모든 본문 페이지는 상단(1/3 지점)에서 시작
        """
        # 컬러 배경 생성
        card = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), bg_color)

        # 로고 추가
        self.add_logo(card)

        # 폰트 설정 (2배 크기)
        title_font = FontManager.get_font(self.font_style, 72, weight='bold')
        bullet_font = FontManager.get_font(self.font_style, 48, weight='regular')

        # 섹션 제목 (1/3 지점에서 시작, 중앙 정렬 수정)
        title_y = CARD_HEIGHT // 3  # 360px (1/3 지점)
        TextRenderer.draw_text_with_shadow(
            card, title, (60, title_y),
            title_font, color=self.theme["text"],
            max_width=CARD_WIDTH - 120,
            align="center", shadow=False
        )

        # Bullet points 렌더링 (제목 아래)
        bullet_y = title_y + 120  # 제목 아래 120px 간격
        TextRenderer.draw_structured_content(
            card, content_lines, bullet_y,
            bullet_font, color=self.theme["text"],
            line_spacing=120, start_x=100
        )

        # 페이지 번호
        self._add_page_number(card, page_num)

        # Base64 변환
        import io
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def _add_page_number(self, image: Image.Image, page_num: int):
        """페이지 번호 추가"""
        draw = ImageDraw.Draw(image, 'RGBA')
        page_font = FontManager.get_font(self.font_style, 20, weight='regular')

        page_text = f"{page_num}"
        draw.text(
            (CARD_WIDTH - 50, CARD_HEIGHT - 40),
            page_text,
            fill=self.theme.get("text", "white"),
            font=page_font
        )

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

        # Step 2: 배경 이미지 생성 (첫 페이지만 AI 이미지, 나머지는 컬러 배경)
        print("\n🖼️ 배경 이미지 생성 중...")
        background_images = []

        if generateImages:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key:
                for i, page in enumerate(pages):
                    if i == 0:  # 첫 페이지만 AI 이미지 생성
                        try:
                            print(f"  📸 페이지 1 AI 이미지 생성 중...")
                            image_url = await generate_background_image_with_gemini(
                                page.get('image_prompt', page.get('visual_concept', 'modern background'))
                            )
                            background_images.append(image_url)
                            print(f"  ✅ 페이지 1 AI 이미지 생성 완료")
                        except Exception as e:
                            print(f"  ⚠️ 페이지 1 이미지 생성 실패: {e}")
                            # 폴백: 단색 배경 생성
                            background_images.append(create_fallback_background(colorTheme))
                    else:  # 나머지 페이지는 컬러 배경
                        print(f"  🎨 페이지 {i+1} 컬러 배경 생성 중...")
                        background_images.append(create_fallback_background(colorTheme))
                        print(f"  ✅ 페이지 {i+1} 컬러 배경 생성 완료")
            else:
                print("  ⚠️ Google API Key 없음, 모든 페이지 단색 배경 사용")
                for _ in pages:
                    background_images.append(create_fallback_background(colorTheme))
        else:
            # 단색 배경 사용
            print("  ℹ️ 이미지 생성 비활성화, 모든 페이지 단색 배경 사용")
            for _ in pages:
                background_images.append(create_fallback_background(colorTheme))

        # Step 3: 최종 카드뉴스 생성
        print("\n📰 최종 카드뉴스 조립 중...")
        theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])
        # layoutType 제거: 첫 페이지는 Agent가 판단, 나머지는 상단 고정
        builder = CardNewsBuilder(theme, "pretendard", purpose, font_weight="regular")

        final_cards = []
        for i, (page, bg_image_data) in enumerate(zip(pages, background_images)):
            print(f"  🎨 카드 {i+1}/{len(pages)} 생성 중...")

            if i == 0:  # 첫 페이지: AI 이미지 + 제목 + 소제목
                # 배경 이미지 로드
                if bg_image_data.startswith('data:image'):
                    image_data = bg_image_data.split(',')[1]
                    bg_image = Image.open(io.BytesIO(base64.b64decode(image_data)))
                else:
                    response = requests.get(bg_image_data, timeout=30)
                    bg_image = Image.open(io.BytesIO(response.content))

                # 첫 페이지 생성 (Agent가 판단한 layout 사용)
                card_base64 = builder.build_first_page(
                    background_image=bg_image,
                    title=page['title'],
                    subtitle=page.get('subtitle', ''),
                    page_num=i + 1,
                    layout=page.get('layout', 'center')  # Agent가 결정한 layout
                )
                final_cards.append(card_base64)

            else:  # 나머지 페이지: 컬러 배경 + 제목 + bullet points
                # 컬러 배경 사용
                bg_color = theme.get("primary", (255, 94, 77))

                # 본문 페이지 생성
                card_base64 = builder.build_content_page(
                    bg_color=bg_color,
                    title=page['title'],
                    content_lines=page.get('content', ["• 내용이 없습니다"]),
                    page_num=i + 1
                )
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
                    "subtitle": p.get('subtitle', ''),
                    "content": p.get('content', [])
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
    """Gemini 2.5 Flash Image로 배경 이미지 생성 (image.py와 동일)"""
    google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')  # image.py와 동일한 키 사용

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={google_api_key}",
            json={
                "contents": [{
                    "parts": [{
                        "text": f"Generate an image without any text or words: {prompt}. The image should be a clean background with no typography, letters, or textual elements."
                    }]
                }]
            },
            headers={"Content-Type": "application/json"}
        )

    if response.status_code != 200:
        raise Exception(f"Gemini API 오류: {response.status_code}")

    data = response.json()

    # 이미지 추출 (image.py와 동일: camelCase 사용)
    if data.get("candidates") and len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        if candidate.get("content") and candidate["content"].get("parts"):
            for part in candidate["content"]["parts"]:
                if part.get("inlineData") and part["inlineData"].get("data"):
                    mime_type = part["inlineData"].get("mimeType", "image/png")
                    image_data = part["inlineData"]["data"]
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


