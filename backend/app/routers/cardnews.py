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
import logging
from datetime import datetime

# AI Agents 임포트
from ..agents import (
    AgenticCardNewsWorkflow,
    extract_dominant_color_from_image,
    get_text_color_for_background,
    adjust_color_for_harmony,
    FONT_PAIRS
)

router = APIRouter(prefix="/api", tags=["cardnews"])

# ==================== 로깅 설정 ====================
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 카드뉴스 전용 로거 설정
cardnews_logger = logging.getLogger("cardnews")
cardnews_logger.setLevel(logging.INFO)

# 파일 핸들러 (날짜별 로그)
log_file = LOG_DIR / f"cardnews_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
cardnews_logger.addHandler(file_handler)

# ==================== 설정 ====================

# 폰트 디렉토리
FONT_DIR = Path(__file__).parent.parent.parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)

# 카드 크기 (고해상도 렌더링용)
RENDER_SCALE = 2  # 2x 해상도로 렌더링 후 다운스케일
CARD_WIDTH = 1080
CARD_HEIGHT = 1080
RENDER_WIDTH = CARD_WIDTH * RENDER_SCALE  # 2160px
RENDER_HEIGHT = CARD_HEIGHT * RENDER_SCALE  # 2160px

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

# ==================== 텍스트 렌더링 (고품질) ====================

class TextRenderer:
    """고품질 텍스트 렌더링 (Gaussian Blur 그림자, 외곽선 지원)"""

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
    def create_gaussian_shadow(
        text: str,
        font: ImageFont.FreeTypeFont,
        shadow_color: tuple = (0, 0, 0, 180),
        blur_radius: int = 8,
        offset: tuple = (4, 4)
    ) -> tuple:
        """Gaussian Blur 그림자 생성 (별도 레이어)"""
        # 텍스트 크기 계산
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 여유 공간 포함한 그림자 레이어 생성
        padding = blur_radius * 3
        shadow_width = text_width + padding * 2
        shadow_height = text_height + padding * 2

        shadow_layer = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)

        # 그림자 텍스트 그리기
        shadow_draw.text((padding, padding), text, font=font, fill=shadow_color)

        # Gaussian Blur 적용
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        return shadow_layer, (padding - offset[0], padding - offset[1])

    @staticmethod
    def draw_text_with_stroke(
        image: Image.Image,
        text: str,
        position: tuple,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        stroke_color: tuple = (0, 0, 0),
        stroke_width: int = 2
    ):
        """외곽선이 있는 텍스트 그리기"""
        draw = ImageDraw.Draw(image, 'RGBA')
        x, y = position

        # 외곽선 그리기 (8방향)
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)

        # 메인 텍스트
        draw.text((x, y), text, font=font, fill=color)

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
        line_spacing: int = 10,
        use_gaussian_shadow: bool = True,  # 새 옵션: Gaussian blur 그림자
        blur_radius: int = 6,  # 블러 강도
        shadow_offset: tuple = (4, 4),  # 그림자 오프셋
        stroke_width: int = 0,  # 외곽선 두께 (0이면 없음)
        stroke_color: tuple = (0, 0, 0),  # 외곽선 색상
        letter_spacing: int = 0  # 자간 조절
    ):
        """고품질 그림자가 있는 텍스트 그리기 (Gaussian Blur 지원)"""
        draw = ImageDraw.Draw(image, 'RGBA')

        # 텍스트 줄바꿈
        if max_width:
            lines = TextRenderer.wrap_text(text, font, max_width, draw)
        else:
            lines = [text]

        # 각 줄 그리기
        y = position[1]
        for line in lines:
            # 자간 적용된 텍스트 처리
            if letter_spacing > 0:
                line = ''.join([c + ' ' * (letter_spacing // 10) for c in line]).strip()

            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 정렬에 따라 x 위치 조정
            x = position[0]
            if align == "center" and max_width:
                x = position[0] + (max_width - text_width) // 2
            elif align == "right" and max_width:
                x = position[0] + max_width - text_width

            # 그림자 효과 (Gaussian Blur 또는 기존 방식)
            if shadow:
                if use_gaussian_shadow:
                    # Gaussian Blur 그림자 (고품질)
                    shadow_layer, offset = TextRenderer.create_gaussian_shadow(
                        line, font, shadow_color, blur_radius, shadow_offset
                    )
                    # 그림자 위치 계산
                    shadow_x = x - offset[0] + shadow_offset[0]
                    shadow_y = y - offset[1] + shadow_offset[1]
                    # 그림자 합성
                    image.paste(shadow_layer, (int(shadow_x), int(shadow_y)), shadow_layer)
                else:
                    # 기존 방식 (빠르지만 품질 낮음)
                    old_shadow_offset = 3
                    for offset_x in range(-old_shadow_offset, old_shadow_offset + 1):
                        for offset_y in range(-old_shadow_offset, old_shadow_offset + 1):
                            if offset_x == 0 and offset_y == 0:
                                continue
                            draw.text(
                                (x + offset_x, y + offset_y),
                                line,
                                fill=shadow_color,
                                font=font
                            )

            # 외곽선 (옵션)
            if stroke_width > 0:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)

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
        bullet_symbol: str = "•",
        use_shadow: bool = False,
        shadow_color: tuple = (0, 0, 0, 100)
    ):
        """Bullet point 렌더링 (• 기호 처리 + 들여쓰기)"""
        draw = ImageDraw.Draw(image, 'RGBA')
        x, y = position

        # "• " 또는 "- " 제거 후 텍스트 추출
        clean_text = text.lstrip('•- ').strip()

        # 그림자 효과 (옵션)
        if use_shadow:
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), bullet_symbol, font=font, fill=shadow_color)
            draw.text((x + 35 + shadow_offset, y + shadow_offset), clean_text, font=font, fill=shadow_color)

        # Bullet 기호 그리기
        draw.text((x, y), bullet_symbol, font=font, fill=color)

        # 텍스트 그리기 (들여쓰기 - 2x 스케일에 맞게 조정)
        indent = 35 * RENDER_SCALE // 2  # 스케일에 맞게 조정
        draw.text((x + indent, y), clean_text, font=font, fill=color)

    @staticmethod
    def draw_structured_content(
        image: Image.Image,
        content: List[str],
        start_y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        line_spacing: int = 50,
        start_x: int = 100,
        use_shadow: bool = False
    ) -> int:
        """
        구조화된 콘텐츠 렌더링 (bullet points 배열)

        Returns:
            최종 y 위치 (다음 요소 렌더링에 활용)
        """
        current_y = start_y

        for line in content:
            TextRenderer.draw_bullet_point(
                image, line, (start_x, current_y), font, color,
                use_shadow=use_shadow
            )
            current_y += line_spacing

        return current_y

# ==================== 배경 처리 유틸리티 ====================

class BackgroundProcessor:
    """고급 배경 이미지 처리 (blur, overlay, vignette, gradient)"""

    @staticmethod
    def apply_gaussian_blur(image: Image.Image, radius: int = 3) -> Image.Image:
        """Gaussian Blur 적용"""
        return image.filter(ImageFilter.GaussianBlur(radius=radius))

    @staticmethod
    def apply_overlay(image: Image.Image, color: tuple = (0, 0, 0), opacity: float = 0.4) -> Image.Image:
        """반투명 오버레이 적용"""
        overlay = Image.new('RGBA', image.size, (*color, int(255 * opacity)))
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        return Image.alpha_composite(image, overlay)

    @staticmethod
    def apply_vignette(image: Image.Image, strength: float = 0.5) -> Image.Image:
        """비네트 효과 (가장자리 어둡게)"""
        import math

        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        width, height = image.size
        vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        # 중심점에서 거리에 따라 어두워지는 그라데이션
        center_x, center_y = width // 2, height // 2
        max_distance = math.sqrt(center_x ** 2 + center_y ** 2)

        for y in range(height):
            for x in range(width):
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                # 거리에 따른 어둡기 계산 (중심은 투명, 가장자리는 어둡게)
                factor = min(1.0, (distance / max_distance) ** 1.5 * strength)
                alpha = int(255 * factor * 0.7)
                vignette.putpixel((x, y), (0, 0, 0, alpha))

        return Image.alpha_composite(image, vignette)

    @staticmethod
    def apply_fast_vignette(image: Image.Image, strength: float = 0.5) -> Image.Image:
        """빠른 비네트 효과 (radial gradient 근사)"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        width, height = image.size

        # 간단한 4-corner 어둡게 처리
        vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette, 'RGBA')

        # 외곽 테두리에 반투명 검정 적용 (점진적)
        for i in range(int(min(width, height) * 0.3)):
            alpha = int((1 - i / (min(width, height) * 0.3)) * strength * 100)
            draw.rectangle(
                [i, i, width - i - 1, height - i - 1],
                outline=(0, 0, 0, alpha)
            )

        return Image.alpha_composite(image, vignette)

    @staticmethod
    def create_linear_gradient(
        width: int,
        height: int,
        start_color: tuple,
        end_color: tuple,
        direction: str = "vertical"  # vertical, horizontal, diagonal
    ) -> Image.Image:
        """선형 그라데이션 생성"""
        gradient = Image.new('RGB', (width, height))

        for y in range(height):
            for x in range(width):
                if direction == "vertical":
                    ratio = y / height
                elif direction == "horizontal":
                    ratio = x / width
                else:  # diagonal
                    ratio = (x + y) / (width + height)

                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

                gradient.putpixel((x, y), (r, g, b))

        return gradient

    @staticmethod
    def create_fast_gradient(
        width: int,
        height: int,
        start_color: tuple,
        end_color: tuple,
        direction: str = "vertical"
    ) -> Image.Image:
        """빠른 그라데이션 생성 (numpy 없이)"""
        gradient = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(gradient)

        if direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif direction == "horizontal":
            for x in range(width):
                ratio = x / width
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        else:  # diagonal
            for i in range(width + height):
                ratio = i / (width + height)
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                # 대각선 그리기
                draw.line([(0, i), (i, 0)], fill=(r, g, b))

        return gradient

    @staticmethod
    def create_radial_gradient(
        width: int,
        height: int,
        center_color: tuple,
        edge_color: tuple
    ) -> Image.Image:
        """원형 그라데이션 생성 (빠른 버전)"""
        import math

        gradient = Image.new('RGB', (width, height))
        center_x, center_y = width // 2, height // 2
        max_distance = math.sqrt(center_x ** 2 + center_y ** 2)

        # 최적화: 매 10픽셀마다만 계산하고 나머지는 보간
        step = 5
        for y in range(0, height, step):
            for x in range(0, width, step):
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                ratio = min(1.0, distance / max_distance)

                r = int(center_color[0] + (edge_color[0] - center_color[0]) * ratio)
                g = int(center_color[1] + (edge_color[1] - center_color[1]) * ratio)
                b = int(center_color[2] + (edge_color[2] - center_color[2]) * ratio)

                # step x step 블록 채우기
                for dy in range(step):
                    for dx in range(step):
                        if y + dy < height and x + dx < width:
                            gradient.putpixel((x + dx, y + dy), (r, g, b))

        return gradient

    @staticmethod
    def enhance_image(
        image: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0
    ) -> Image.Image:
        """이미지 보정 (밝기, 대비, 채도)"""
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)

        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)

        if saturation != 1.0:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(saturation)

        return image


# ==================== 카드 빌더 (고품질 2x 렌더링) ====================

class CardNewsBuilder:
    """고품질 카드뉴스 이미지 생성 (2x 해상도 렌더링 + 다운스케일)"""

    def __init__(self, theme: dict, font_style: str, purpose: str, layout_type: str = "bottom", font_weight: str = "light"):
        self.theme = theme
        self.font_style = font_style
        self.purpose = purpose
        self.layout_type = layout_type  # 하위 호환성 유지, 실제로는 미사용 (페이지별 layout 사용)
        self.font_weight = font_weight  # light, medium, bold
        self.badge_text = BADGE_TEXT_MAP.get(purpose, '정보')
        self.scale = RENDER_SCALE  # 2x 렌더링

    def prepare_background(
        self,
        background_image: Image.Image,
        apply_blur: bool = False,
        blur_radius: int = 3,
        apply_overlay: bool = True,
        overlay_opacity: float = 0.35,
        apply_vignette: bool = True,
        vignette_strength: float = 0.4,
        brightness: float = 0.65,
        contrast: float = 1.1,
        saturation: float = 1.1
    ) -> Image.Image:
        """고급 배경 이미지 준비 (2x 해상도)"""
        # RGB 변환
        if background_image.mode != 'RGB':
            background_image = background_image.convert('RGB')

        # 2x 크기로 조정 (고품질 리샘플링)
        img = background_image.resize((RENDER_WIDTH, RENDER_HEIGHT), Image.Resampling.LANCZOS)

        # 이미지 보정 (밝기, 대비, 채도)
        img = BackgroundProcessor.enhance_image(img, brightness, contrast, saturation)

        # Gaussian Blur (옵션)
        if apply_blur:
            img = BackgroundProcessor.apply_gaussian_blur(img, blur_radius * self.scale)

        # 반투명 오버레이 (텍스트 가독성 향상)
        if apply_overlay:
            img = BackgroundProcessor.apply_overlay(img, (0, 0, 0), overlay_opacity)

        # 비네트 효과
        if apply_vignette:
            img = BackgroundProcessor.apply_fast_vignette(img, vignette_strength)

        # RGB로 다시 변환 (alpha 제거)
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (0, 0, 0))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img

        return img

    def _downscale_to_final(self, image: Image.Image) -> Image.Image:
        """2x 이미지를 1x로 다운스케일 (고품질 안티앨리어싱)"""
        return image.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

    def add_logo(self, image: Image.Image):
        """로고 배지 추가 (상단 중앙) - 2x 스케일 대응"""
        import os

        # 현재 이미지 크기에 따라 스케일 결정
        current_width = image.size[0]
        is_2x = current_width == RENDER_WIDTH

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

            # 로고 크기 조정 (2x 스케일 적용)
            base_logo_height = 50
            logo_height = base_logo_height * self.scale if is_2x else base_logo_height
            aspect_ratio = logo.width / logo.height
            logo_width = int(logo_height * aspect_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # 로고 위치 (상단 중앙) - 2x 스케일 적용
            target_width = RENDER_WIDTH if is_2x else CARD_WIDTH
            base_y = 30
            logo_x = (target_width - logo_width) // 2
            logo_y = base_y * self.scale if is_2x else base_y

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
        layout: str = "center",
        text_color: str = None  # "white" 또는 "black"
    ) -> str:
        """
        첫 페이지 전용 렌더링 (제목 + 소제목 + AI 배경)
        Agent가 판단한 layout에 따라 텍스트 위치 조정
        2x 고해상도 렌더링 후 다운스케일
        """
        # 배경 준비 (2x 해상도)
        card = self.prepare_background(background_image)

        # 로고 추가 (2x 스케일)
        self.add_logo(card)

        # 텍스트 색상 결정
        if text_color:
            actual_text_color = text_color
        else:
            actual_text_color = self.theme.get("text", "white")

        # 폰트 설정 (2x 스케일 적용)
        title_font = FontManager.get_font(self.font_style, 96 * self.scale, weight='bold')
        subtitle_font = FontManager.get_font(self.font_style, 56 * self.scale, weight='medium')

        # 2x 스케일 기준 치수
        max_width = RENDER_WIDTH - 120 * self.scale
        margin_x = 60 * self.scale

        # 텍스트 총 높이 계산
        draw = ImageDraw.Draw(card)
        title_lines = TextRenderer.wrap_text(title, title_font, max_width, draw)
        subtitle_lines = TextRenderer.wrap_text(subtitle, subtitle_font, max_width, draw)

        title_line_height = 120 * self.scale  # 폰트 크기 + 여백 (2x)
        subtitle_line_height = 72 * self.scale
        title_height = len(title_lines) * title_line_height
        subtitle_height = len(subtitle_lines) * subtitle_line_height
        gap = 40 * self.scale  # 제목-부제목 간격
        total_height = title_height + subtitle_height + gap

        # Agent가 판단한 layout에 따라 시작 위치 결정 (2x 스케일)
        if layout == "top":
            title_y = RENDER_HEIGHT // 3  # 1/3 지점
        elif layout == "bottom":
            title_y = RENDER_HEIGHT - total_height - 150 * self.scale  # 하단
        else:  # center (기본값)
            title_y = (RENDER_HEIGHT - total_height) // 2  # 중앙

        # 제목 렌더링 (Gaussian Blur 그림자)
        TextRenderer.draw_text_with_shadow(
            card, title, (margin_x, title_y),
            title_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=True,
            use_gaussian_shadow=True,
            blur_radius=12 * self.scale,
            shadow_offset=(6 * self.scale, 6 * self.scale),
            shadow_color=(0, 0, 0, 160),
            line_spacing=24 * self.scale
        )

        # 소제목 렌더링 (제목 아래)
        subtitle_y = title_y + title_height + gap
        TextRenderer.draw_text_with_shadow(
            card, subtitle, (margin_x, subtitle_y),
            subtitle_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=True,
            use_gaussian_shadow=True,
            blur_radius=8 * self.scale,
            shadow_offset=(4 * self.scale, 4 * self.scale),
            shadow_color=(0, 0, 0, 100),
            line_spacing=16 * self.scale
        )

        # 페이지 번호
        self._add_page_number(card, page_num)

        # 다운스케일 (2x → 1x)
        final_card = self._downscale_to_final(card)

        # Base64 변환
        buffer = io.BytesIO()
        final_card.save(buffer, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def build_content_page(
        self,
        bg_color: tuple,
        title: str,
        content_lines: List[str],
        page_num: int,
        text_color: str = None,  # "white" 또는 "black"
        use_gradient: bool = True  # 그라데이션 배경 사용 여부
    ) -> str:
        """
        본문 페이지 렌더링 (섹션 제목 + bullet points + 컬러/그라데이션 배경)
        2x 고해상도 렌더링 후 다운스케일
        """
        # 배경 생성 (2x 해상도)
        if use_gradient:
            # 그라데이션 배경 (primary → 약간 어두운 색)
            end_color = tuple(max(0, c - 40) for c in bg_color)
            card = BackgroundProcessor.create_fast_gradient(
                RENDER_WIDTH, RENDER_HEIGHT,
                bg_color, end_color,
                direction=self.theme.get("gradient_type", "vertical")
            )
        else:
            # 단색 배경
            card = Image.new('RGB', (RENDER_WIDTH, RENDER_HEIGHT), bg_color)

        # 로고 추가 (2x 스케일)
        self.add_logo(card)

        # 텍스트 색상 결정
        if text_color:
            actual_text_color = text_color
        else:
            actual_text_color = self.theme.get("text", "white")

        # 폰트 설정 (2x 스케일 적용)
        title_font = FontManager.get_font(self.font_style, 72 * self.scale, weight='bold')
        bullet_font = FontManager.get_font(self.font_style, 48 * self.scale, weight='regular')

        # 2x 스케일 기준 치수
        margin_x = 60 * self.scale
        max_width = RENDER_WIDTH - 120 * self.scale

        # 섹션 제목 (1/3 지점에서 시작)
        title_y = RENDER_HEIGHT // 3
        TextRenderer.draw_text_with_shadow(
            card, title, (margin_x, title_y),
            title_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=False,
            use_gaussian_shadow=False
        )

        # Bullet points 렌더링 (제목 아래)
        bullet_y = title_y + 120 * self.scale
        bullet_start_x = 100 * self.scale
        bullet_line_spacing = 120 * self.scale
        TextRenderer.draw_structured_content(
            card, content_lines, bullet_y,
            bullet_font, color=actual_text_color,
            line_spacing=bullet_line_spacing, start_x=bullet_start_x,
            use_shadow=False
        )

        # 페이지 번호
        self._add_page_number(card, page_num)

        # 다운스케일 (2x → 1x)
        final_card = self._downscale_to_final(card)

        # Base64 변환
        buffer = io.BytesIO()
        final_card.save(buffer, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def _add_page_number(self, image: Image.Image, page_num: int):
        """페이지 번호 추가 (2x 스케일 대응)"""
        # 현재 이미지 크기에 따라 스케일 결정
        current_width = image.size[0]
        is_2x = current_width == RENDER_WIDTH
        scale = self.scale if is_2x else 1

        draw = ImageDraw.Draw(image, 'RGBA')
        page_font = FontManager.get_font(self.font_style, 20 * scale, weight='regular')

        page_text = f"{page_num}"
        target_width = RENDER_WIDTH if is_2x else CARD_WIDTH
        target_height = RENDER_HEIGHT if is_2x else CARD_HEIGHT

        draw.text(
            (target_width - 50 * scale, target_height - 40 * scale),
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
    fontStyle: str = Form(default="pretendard"),  # AI가 자동 선택하므로 기본값만 유지
    colorTheme: str = Form(default="warm"),  # 사용자가 선택한 테마 사용 (기본: warm)
    generateImages: bool = Form(default=True),
    layoutType: str = Form(default="bottom"),
    userContext: str = Form(default=None)  # 사용자 컨텍스트 (JSON 문자열)
):
    """
    AI Agentic 방식으로 카드뉴스 자동 생성

    개선된 워크플로우:
    1. 정보 확장: 간단한 입력을 풍부한 콘텐츠로 확장
    2. AI가 페이지별 내용 구성 (최소 페이지 수 원칙)
    3. 첫 페이지 썸네일 AI 생성 → 색상 추출
    4. 추출된 색상으로 나머지 페이지 배경색 결정
    5. 배경색에 따라 텍스트 색상(검정/흰색) 자동 결정
    6. AI가 선택한 폰트 적용

    Args:
        prompt: 사용자 입력 프롬프트 (예: "새로운 카페 오픈 홍보")
        purpose: 목적 (promotion/menu/info/event)
        fontStyle: 폰트 스타일 (AI가 자동 선택)
        colorTheme: "auto"면 썸네일에서 추출, 그 외 수동 지정
        generateImages: 배경 이미지 자동 생성 여부
        userContext: 사용자 브랜드/비즈니스 정보 (JSON)
    """
    try:
        # 사용자 컨텍스트 파싱
        user_context_data = None
        if userContext:
            try:
                user_context_data = json.loads(userContext)
                cardnews_logger.info(f"📋 사용자 컨텍스트 로드: {user_context_data.get('brand_name', 'N/A')}")
            except json.JSONDecodeError:
                cardnews_logger.warning("⚠️ 사용자 컨텍스트 파싱 실패")

        log_msg = f"\n{'='*80}\n🤖 AI Agentic 카드뉴스 생성 시작 (개선된 버전)\n📝 프롬프트: {prompt}\n🎯 목적: {purpose}\n🏢 브랜드: {user_context_data.get('brand_name', 'N/A') if user_context_data else 'N/A'}\n{'='*80}\n"
        print(log_msg)
        cardnews_logger.info(log_msg)

        # Step 1: AI Agentic 워크플로우 실행 (정보 확장 포함, 사용자 컨텍스트 전달)
        workflow = AgenticCardNewsWorkflow()
        result = await workflow.execute(prompt, purpose, user_context=user_context_data)

        if not result.get('success'):
            error_msg = f"AI 워크플로우 실패: {result.get('error', '알 수 없는 오류')}"
            cardnews_logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )

        analysis = result['analysis']
        pages = result['pages']
        quality_report = result['quality_report']
        design_settings = result.get('design_settings', {})

        # AI가 선택한 폰트 사용
        font_pair = design_settings.get('font_pair', 'pretendard')
        selected_style = design_settings.get('style', 'modern')

        design_log = f"\n📐 디자인 설정:\n   🔤 폰트: {font_pair} ({FONT_PAIRS.get(font_pair, {}).get('korean', 'Pretendard')})\n   🎨 스타일: {selected_style}"
        print(design_log)
        cardnews_logger.info(design_log)

        # Step 2: 첫 페이지 AI 이미지 생성 → 색상 추출
        cardnews_logger.info("🖼️ 배경 이미지 생성 및 색상 추출 중...")
        print("\n🖼️ 배경 이미지 생성 및 색상 추출 중...")
        background_images = []
        dominant_color = None
        adjusted_color = None  # 색상 추출 성공 시에만 설정됨
        text_color = "white"

        # 사용자가 선택한 테마 로드
        user_selected_theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])
        cardnews_logger.info(f"🎨 사용자 선택 테마: {colorTheme} -> RGB{user_selected_theme['primary']}")

        if generateImages:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key and len(pages) > 0:
                # 첫 페이지 AI 이미지 생성
                try:
                    cardnews_logger.info("📸 페이지 1 AI 이미지 생성 중...")
                    print(f"  📸 페이지 1 AI 이미지 생성 중...")
                    first_page = pages[0]
                    thumbnail_url = await generate_background_image_with_gemini(
                        first_page.get('image_prompt', first_page.get('visual_concept', 'modern background'))
                    )
                    background_images.append(thumbnail_url)
                    cardnews_logger.info("✅ 페이지 1 AI 이미지 생성 완료")
                    print(f"  ✅ 페이지 1 AI 이미지 생성 완료")

                    # 썸네일에서 주요 색상 추출
                    cardnews_logger.info("🎨 썸네일에서 색상 추출 중...")
                    print(f"  🎨 썸네일에서 색상 추출 중...")
                    dominant_color = extract_dominant_color_from_image(thumbnail_url)
                    cardnews_logger.info(f"✅ 추출된 주요 색상: RGB{dominant_color}")
                    print(f"  ✅ 추출된 주요 색상: RGB{dominant_color}")

                    # 스타일에 맞게 색상 조정
                    adjusted_color = adjust_color_for_harmony(dominant_color, selected_style)
                    cardnews_logger.info(f"✅ 조정된 배경 색상: RGB{adjusted_color}")
                    print(f"  ✅ 조정된 배경 색상: RGB{adjusted_color}")

                    # 텍스트 색상 결정 (배경 밝기 기반)
                    text_color = get_text_color_for_background(adjusted_color)
                    cardnews_logger.info(f"✅ 텍스트 색상: {text_color}")
                    print(f"  ✅ 텍스트 색상: {text_color}")

                    # 나머지 페이지는 추출된 색상 기반 단색 배경
                    for i in range(1, len(pages)):
                        print(f"  🎨 페이지 {i+1} 컬러 배경 생성 중 (추출된 색상 기반)...")
                        bg_base64 = create_solid_color_background(adjusted_color)
                        background_images.append(bg_base64)
                        print(f"  ✅ 페이지 {i+1} 컬러 배경 생성 완료")

                except Exception as e:
                    cardnews_logger.warning(f"⚠️ 이미지 생성/색상 추출 실패: {e}")
                    print(f"  ⚠️ 이미지 생성/색상 추출 실패: {e}")
                    # 폴백: 사용자가 선택한 테마 사용
                    for _ in pages:
                        background_images.append(create_fallback_background(colorTheme))
                    dominant_color = user_selected_theme["primary"]
                    cardnews_logger.info(f"  🎨 사용자 선택 테마 적용: {colorTheme}")
            else:
                cardnews_logger.warning("⚠️ Google API Key 없음, 사용자 테마 사용")
                print("  ⚠️ Google API Key 없음, 사용자 테마 사용")
                for _ in pages:
                    background_images.append(create_fallback_background(colorTheme))
                dominant_color = user_selected_theme["primary"]
                cardnews_logger.info(f"  🎨 사용자 선택 테마 적용: {colorTheme}")
        else:
            # 이미지 생성 비활성화 - 사용자 선택 테마 사용
            cardnews_logger.info(f"ℹ️ 이미지 생성 비활성화, 사용자 테마 사용: {colorTheme}")
            print(f"  ℹ️ 이미지 생성 비활성화, 사용자 테마 사용: {colorTheme}")
            for _ in pages:
                background_images.append(create_fallback_background(colorTheme))
            dominant_color = user_selected_theme["primary"]

        # 최종 배경색 결정 - 사용자 선택 테마 우선
        if dominant_color and adjusted_color:
            # 색상 추출 성공 시 추출된 색상 사용
            final_bg_color = adjusted_color
            cardnews_logger.info(f"✅ 추출된 색상 사용: RGB{final_bg_color}")
        else:
            # 색상 추출 실패 시 사용자 선택 테마 사용
            final_bg_color = user_selected_theme["primary"]
            cardnews_logger.info(f"✅ 사용자 선택 테마 색상 사용: RGB{final_bg_color} ({colorTheme})")

        # 텍스트 색상 최종 결정
        text_color = get_text_color_for_background(final_bg_color)

        # Step 3: 동적 테마 생성 (사용자 선택 테마의 그라데이션 타입 유지)
        dynamic_theme = {
            "primary": final_bg_color,
            "secondary": tuple(min(255, c + 30) for c in final_bg_color),
            "accent": tuple(max(0, c - 20) for c in final_bg_color),
            "text": text_color,
            "shadow": user_selected_theme.get("shadow", (0, 0, 0, 120)),
            "gradient_type": user_selected_theme.get("gradient_type", "vertical")
        }

        # Step 4: 최종 카드뉴스 생성
        print("\n📰 최종 카드뉴스 조립 중...")
        print(f"   🎨 배경색: RGB{final_bg_color}")
        print(f"   📝 텍스트색: {text_color}")
        print(f"   🔤 폰트: {font_pair}")

        builder = CardNewsBuilder(dynamic_theme, font_pair, purpose, font_weight="regular")

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
                    layout=page.get('layout', 'center'),
                    text_color=text_color  # 동적 텍스트 색상
                )
                final_cards.append(card_base64)

            else:  # 나머지 페이지: 컬러 배경 + 제목 + bullet points
                # 본문 페이지 생성
                card_base64 = builder.build_content_page(
                    bg_color=final_bg_color,
                    title=page['title'],
                    content_lines=page.get('content', ["• 내용이 없습니다"]),
                    page_num=i + 1,
                    text_color=text_color  # 동적 텍스트 색상
                )
                final_cards.append(card_base64)

            print(f"  ✅ 카드 {i+1} 완성")

        result_log = f"\n{'='*80}\n✅ {len(final_cards)}장의 AI 카드뉴스 생성 완료!\n   📄 페이지: {len(final_cards)}장\n   🎨 배경색: RGB{final_bg_color}\n   📝 텍스트: {text_color}\n   🔤 폰트: {FONT_PAIRS.get(font_pair, {}).get('korean', 'Pretendard')}\n{'='*80}\n"
        print(result_log)
        cardnews_logger.info(result_log)

        return {
            "success": True,
            "cards": final_cards,
            "count": len(final_cards),
            "analysis": {
                "page_count": analysis.get('page_count'),
                "target_audience": analysis.get('target_audience'),
                "tone": analysis.get('tone'),
                "style": analysis.get('style'),
                "font_pair": font_pair
            },
            "design_settings": {
                "bg_color": final_bg_color,
                "text_color": text_color,
                "font_korean": FONT_PAIRS.get(font_pair, {}).get('korean', 'Pretendard'),
                "font_english": FONT_PAIRS.get(font_pair, {}).get('english', 'Inter'),
                "style": selected_style
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
        error_msg = f"\n❌ AI 카드뉴스 생성 실패: {str(e)}"
        print(error_msg)
        cardnews_logger.error(error_msg)
        import traceback
        tb = traceback.format_exc()
        cardnews_logger.error(tb)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"AI 카드뉴스 생성 중 오류: {str(e)}"
        )


async def generate_background_image_with_gemini(prompt: str) -> str:
    """Gemini 2.5 Flash Image로 배경 이미지 생성 (image.py와 동일)"""
    google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')  # image.py와 동일한 키 사용

    # 텍스트 없는 배경 이미지 생성을 위한 강화된 프롬프트
    no_text_instruction = """CRITICAL REQUIREMENTS:
- ABSOLUTELY NO TEXT, LETTERS, WORDS, NUMBERS, or TYPOGRAPHY of any kind
- NO logos, watermarks, signatures, or any written elements
- Pure visual imagery only - abstract patterns, gradients, textures, or scenic backgrounds
- Clean, minimal design suitable as a background for overlaid text
- High quality, professional aesthetic"""

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={google_api_key}",
            json={
                "contents": [{
                    "parts": [{
                        "text": f"{no_text_instruction}\n\nImage concept: {prompt}"
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


def create_fallback_background(color_theme: str, use_gradient: bool = True) -> str:
    """폴백용 배경 생성 (그라데이션 또는 단색)"""
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES["warm"])
    primary = theme["primary"]

    if use_gradient:
        # 그라데이션 배경 (primary → 약간 어두운 색)
        end_color = tuple(max(0, c - 40) for c in primary)
        direction = theme.get("gradient_type", "vertical")
        img = BackgroundProcessor.create_fast_gradient(
            CARD_WIDTH, CARD_HEIGHT,
            primary, end_color,
            direction=direction
        )
    else:
        # 단색 배경
        img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=primary)

    # Base64 변환
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def create_solid_color_background(color: tuple, use_gradient: bool = True, gradient_type: str = "vertical") -> str:
    """RGB 튜플로 배경 생성 (그라데이션 또는 단색)"""
    if use_gradient:
        # 그라데이션 배경 (primary → 약간 어두운 색)
        end_color = tuple(max(0, c - 40) for c in color)
        img = BackgroundProcessor.create_fast_gradient(
            CARD_WIDTH, CARD_HEIGHT,
            color, end_color,
            direction=gradient_type
        )
    else:
        # 단색 배경
        img = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=color)

    # Base64 변환
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def create_gradient_background(
    start_color: tuple,
    end_color: tuple,
    direction: str = "vertical",
    width: int = CARD_WIDTH,
    height: int = CARD_HEIGHT
) -> str:
    """그라데이션 배경 생성"""
    img = BackgroundProcessor.create_fast_gradient(
        width, height,
        start_color, end_color,
        direction=direction
    )

    # Base64 변환
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


