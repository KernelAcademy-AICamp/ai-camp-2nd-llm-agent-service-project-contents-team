from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
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
import unicodedata
from supabase import create_client, Client

# DB 및 인증 모듈 임포트
from ..database import get_db
from ..models import User, ContentGenerationSession, GeneratedCardnewsContent
from ..auth import get_current_user

# 개선된 템플릿 시스템 임포트
from ..utils.cardnews_templates_improved import (
    DESIGN_TEMPLATES as IMPROVED_TEMPLATES,
    COLOR_PALETTES,
    LAYOUT_STYLES,
    TEMPLATE_CATEGORIES,
    get_template,
    get_palette,
    get_layout,
    get_frontend_template_list,
    get_templates_by_category
)
from ..utils.cardnews_renderer import (
    CardNewsRenderer as ImprovedRenderer,
    GradientGenerator,
    EffectsProcessor,
    CardRenderer,
    DecorationRenderer
)

# ==================== 이모지 처리 유틸리티 ====================

def strip_markdown(text: str) -> str:
    """
    텍스트에서 마크다운 문법을 제거합니다.
    **굵은 글씨**, *기울임*, `코드` 등의 마크다운 문법을 평문으로 변환합니다.
    """
    if not text:
        return text

    # **굵은 글씨** → 굵은 글씨
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # *기울임* → 기울임
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # __굵은 글씨__ → 굵은 글씨
    text = re.sub(r'__(.+?)__', r'\1', text)
    # _기울임_ → 기울임
    text = re.sub(r'_(.+?)_', r'\1', text)
    # `코드` → 코드
    text = re.sub(r'`(.+?)`', r'\1', text)
    # ~~취소선~~ → 취소선
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # [링크텍스트](URL) → 링크텍스트
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # # 헤더 → 헤더 (줄 시작의 # 제거)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    return text.strip()


def strip_emojis(text: str) -> str:
    """
    텍스트에서 이모지를 제거합니다.
    폰트가 이모지를 지원하지 않아 렌더링 문제가 발생하는 것을 방지합니다.

    주의: 한글(AC00-D7AF), 영문, 숫자, 기본 문장부호는 보존합니다.
    """
    if not text:
        return text

    # 이모지 범위를 정규식으로 정의 (한글/영문/숫자에 영향 없는 범위만)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 이모티콘 (스마일리)
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U0001F900-\U0001F9FF"  # 보충 기호 및 픽토그램
        "\U0001FA00-\U0001FA6F"  # 체스 기호
        "\U0001FA70-\U0001FAFF"  # 기호 및 픽토그램 확장-A
        "\U0001F000-\U0001F02F"  # 마작 타일
        "\U0001F0A0-\U0001F0FF"  # 트럼프 카드
        "\U00002702-\U000027B0"  # 딩뱃 (일부)
        "\U0000FE00-\U0000FE0F"  # 변형 선택자
        "\U0001F200-\U0001F251"  # 기타 기호 (한글 범위 제외)
        "]+",
        flags=re.UNICODE
    )

    # 이모지 제거
    cleaned = emoji_pattern.sub('', text)

    # 연속된 공백을 하나로 정리
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def has_emoji(text: str) -> bool:
    """텍스트에 이모지가 포함되어 있는지 확인합니다."""
    if not text:
        return False

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 이모티콘 (스마일리)
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U0001F900-\U0001F9FF"  # 보충 기호 및 픽토그램
        "\U0001FA00-\U0001FA6F"  # 체스 기호
        "\U0001FA70-\U0001FAFF"  # 기호 및 픽토그램 확장-A
        "\U0001F000-\U0001F02F"  # 마작 타일
        "\U0001F0A0-\U0001F0FF"  # 트럼프 카드
        "\U0001F200-\U0001F251"  # 기타 기호
        "]+",
        flags=re.UNICODE
    )

    return bool(emoji_pattern.search(text))


# ==================== 이미지 밝기 분석 유틸리티 ====================

def analyze_image_brightness(image: Image.Image) -> float:
    """
    이미지의 평균 밝기를 분석합니다.

    Returns:
        0.0 ~ 1.0 사이의 값 (0=어두움, 1=밝음)
    """
    # RGB로 변환
    if image.mode != 'RGB':
        img = image.convert('RGB')
    else:
        img = image

    # 이미지 크기가 크면 축소하여 빠르게 계산
    if img.width > 200 or img.height > 200:
        img = img.resize((200, 200), Image.Resampling.LANCZOS)

    # 픽셀 데이터 가져오기
    pixels = list(img.getdata())

    # 평균 밝기 계산 (가중 평균: 인간 눈의 민감도 반영)
    # Y = 0.299*R + 0.587*G + 0.114*B
    total_brightness = 0
    for r, g, b in pixels:
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        total_brightness += brightness

    avg_brightness = total_brightness / len(pixels)

    # 0~255 -> 0~1 정규화
    return avg_brightness / 255.0


def get_overlay_and_text_colors(image: Image.Image) -> dict:
    """
    이미지 밝기에 따라 오버레이 색상과 텍스트 색상을 결정합니다.

    Returns:
        {
            "overlay_color": (r, g, b),
            "overlay_opacity": float,
            "text_color": "white" | "black",
            "card_bg_color": (r, g, b),
            "card_opacity": float,
            "is_dark_image": bool
        }
    """
    brightness = analyze_image_brightness(image)

    # 밝기 임계값 (0.5 기준으로 밝음/어두움 구분)
    is_dark = brightness < 0.45

    if is_dark:
        # 어두운 이미지: 밝은(흰색) 오버레이 + 검은색 텍스트
        return {
            "overlay_color": (255, 255, 255),
            "overlay_opacity": 0.25,  # 밝은 오버레이는 약하게
            "text_color": "black",
            "card_bg_color": (255, 255, 255),
            "card_opacity": 0.35,
            "is_dark_image": True,
            "brightness": brightness
        }
    else:
        # 밝은 이미지: 어두운(검은색) 오버레이 + 흰색 텍스트
        return {
            "overlay_color": (0, 0, 0),
            "overlay_opacity": 0.35,
            "text_color": "white",
            "card_bg_color": (0, 0, 0),
            "card_opacity": 0.35,
            "is_dark_image": False,
            "brightness": brightness
        }


def generate_harmonious_palette(base_color: tuple, num_colors: int = 5) -> list:
    """
    기준 색상에서 조화로운 색상 팔레트 생성

    Args:
        base_color: 기준 RGB 색상 (첫 페이지에서 추출한 색상)
        num_colors: 생성할 색상 개수

    Returns:
        list of RGB tuples - 각 페이지에 사용할 조화로운 색상들
    """
    import colorsys

    r, g, b = base_color
    # RGB -> HSV 변환 (0-1 범위)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    palette = []

    # 색상 조화 전략들
    strategies = [
        # 1. 유사색 (Analogous) - 색상환에서 인접한 색
        lambda h, i: ((h + 0.08 * i) % 1.0, max(0.3, s * 0.9), min(1.0, v * 1.05)),
        # 2. 보색 방향으로 약간 이동
        lambda h, i: ((h + 0.15 * i) % 1.0, max(0.25, s * 0.85), min(1.0, v * 1.1)),
        # 3. 채도/명도 변화
        lambda h, i: (h, max(0.2, s - 0.1 * i), min(1.0, v + 0.05 * i)),
        # 4. 트라이어드 방향
        lambda h, i: ((h + 0.33 * (i % 2)) % 1.0, max(0.3, s * 0.95), min(1.0, v)),
    ]

    for i in range(num_colors):
        if i == 0:
            # 첫 번째는 기준 색상과 유사하지만 약간 다른 톤
            new_h = h
            new_s = max(0.25, min(1.0, s * 0.95))
            new_v = max(0.3, min(1.0, v * 1.02))
        else:
            # 페이지별로 다양한 전략 적용
            strategy_idx = i % len(strategies)
            new_h, new_s, new_v = strategies[strategy_idx](h, i)

        # HSV -> RGB 변환
        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        palette.append((int(new_r * 255), int(new_g * 255), int(new_b * 255)))

    return palette


def generate_complementary_palette(base_color: tuple, num_colors: int = 5) -> list:
    """
    보색 기반 조화로운 팔레트 생성 (더 대비가 강한 버전)

    Args:
        base_color: 기준 RGB 색상
        num_colors: 생성할 색상 개수

    Returns:
        list of RGB tuples
    """
    import colorsys

    r, g, b = base_color
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    palette = []

    for i in range(num_colors):
        if i == 0:
            # 첫 번째: 기준 색상 톤 변형
            new_h = h
            new_s = max(0.3, s * 0.9)
            new_v = min(0.95, v * 1.05)
        elif i == 1:
            # 두 번째: 유사색 (30도 이동)
            new_h = (h + 0.083) % 1.0
            new_s = max(0.25, s * 0.85)
            new_v = min(0.9, v * 1.1)
        elif i == 2:
            # 세 번째: 반대 유사색 (-30도)
            new_h = (h - 0.083) % 1.0
            new_s = max(0.3, s * 0.95)
            new_v = min(0.85, v)
        elif i == 3:
            # 네 번째: 보색 방향으로 60도
            new_h = (h + 0.167) % 1.0
            new_s = max(0.35, s * 0.8)
            new_v = min(0.9, v * 1.05)
        else:
            # 나머지: 점진적 색상 변화
            shift = 0.05 * (i - 3)
            new_h = (h + shift) % 1.0
            new_s = max(0.25, s * (0.9 - 0.05 * (i - 4)))
            new_v = min(0.95, v * (1 + 0.03 * (i - 4)))

        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, new_s, new_v)
        palette.append((int(new_r * 255), int(new_g * 255), int(new_b * 255)))

    return palette


# AI Agents 임포트
from ..agents import (
    AgenticCardNewsWorkflow,
    extract_dominant_color_from_image,
    get_text_color_for_background,
    adjust_color_for_harmony,
    FONT_PAIRS
)

router = APIRouter(prefix="/api", tags=["cardnews"])

# ==================== Supabase Storage 설정 ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Supabase 클라이언트 초기화
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


async def upload_cardnews_image_to_supabase(
    base64_image: str,
    user_id: int,
    session_id: int,
    page_num: int
) -> str:
    """
    카드뉴스 이미지를 Supabase Storage에 업로드

    Args:
        base64_image: Base64 인코딩된 이미지 (data:image/... 형식)
        user_id: 사용자 ID
        session_id: 세션 ID
        page_num: 페이지 번호

    Returns:
        업로드된 이미지 URL
    """
    if not supabase:
        raise Exception("Supabase client not initialized")

    try:
        # Base64 데이터 추출
        if base64_image.startswith('data:image'):
            image_data = base64_image.split(',')[1]
        else:
            image_data = base64_image

        # Base64를 바이트로 변환
        image_bytes = base64.b64decode(image_data)

        # 파일 경로 생성
        file_path = f"{user_id}/{session_id}/page_{page_num}.png"

        # Supabase Storage에 업로드 (cardnews 버킷)
        result = supabase.storage.from_("cardnews").upload(
            file_path,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": "true"}
        )

        # 공개 URL 생성
        public_url = supabase.storage.from_("cardnews").get_public_url(file_path)

        cardnews_logger.info(f"✅ Supabase 업로드 성공 (page {page_num}): {public_url}")
        return public_url
    except Exception as e:
        cardnews_logger.error(f"Supabase 업로드 실패 (page {page_num}): {e}")
        raise


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

# ==================== 디자인 템플릿 ====================
# 새로운 개선된 템플릿 시스템 사용 (IMPROVED_TEMPLATES)
# 기존 DESIGN_TEMPLATES는 삭제됨

# 디자인 템플릿 목록 (프론트엔드용)
def get_design_templates_list():
    """프론트엔드에 전달할 디자인 템플릿 목록 (새 템플릿만)"""
    return [
        {
            "id": template["id"],
            "name": template["name"],
            "description": template["description"],
            "preview_color": template["preview_color"],
            "category": template.get("category", "minimal")
        }
        for template in IMPROVED_TEMPLATES.values()
    ]


def get_improved_templates_by_category():
    """카테고리별로 그룹화된 개선된 템플릿 목록"""
    return get_frontend_template_list()


def get_all_template_config(template_id: str) -> dict:
    """
    템플릿 ID로 전체 설정 가져오기
    새 템플릿 시스템만 사용
    """
    # 새 템플릿에서 찾기
    if template_id in IMPROVED_TEMPLATES:
        template = IMPROVED_TEMPLATES[template_id]
        palette = get_palette(template["palette"])
        layout = get_layout(template["layout"])
        return {
            "type": "improved",
            "template": template,
            "palette": palette,
            "layout": layout
        }

    # 기본값 (minimal_white)
    default_template = IMPROVED_TEMPLATES.get("minimal_white", list(IMPROVED_TEMPLATES.values())[0])
    return {
        "type": "improved",
        "template": default_template,
        "palette": get_palette(default_template["palette"]),
        "layout": get_layout(default_template["layout"])
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
        # 마크다운 및 이모지 제거 (폰트 렌더링 문제 방지)
        text = strip_markdown(text)
        text = strip_emojis(text)

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
        shadow_color: tuple = (0, 0, 0, 100),
        max_width: int = None,
        line_height: int = None
    ) -> int:
        """
        Bullet point 렌더링 (• 기호 처리 + 들여쓰기 + 줄바꿈 지원)

        Args:
            max_width: 최대 텍스트 너비 (줄바꿈 기준). None이면 줄바꿈 안 함
            line_height: 줄 높이. None이면 폰트 높이 기반 자동 계산

        Returns:
            렌더링 후 최종 y 위치 (다음 요소 렌더링에 활용)
        """
        draw = ImageDraw.Draw(image, 'RGBA')
        x, y = position

        # "• " 또는 "- " 제거 후 텍스트 추출
        clean_text = text.lstrip('•- ').strip()

        # 마크다운 및 이모지 제거 (폰트 렌더링 문제 방지)
        clean_text = strip_markdown(clean_text)
        clean_text = strip_emojis(clean_text)

        # 들여쓰기 값
        indent = 35 * RENDER_SCALE // 2  # 스케일에 맞게 조정

        # 줄바꿈 처리
        if max_width:
            # 불릿 뒤 텍스트 영역의 최대 너비
            text_max_width = max_width - indent
            wrapped_lines = TextRenderer.wrap_text(clean_text, font, text_max_width, draw)
        else:
            wrapped_lines = [clean_text]

        # 줄 높이 계산
        if line_height is None:
            bbox = draw.textbbox((0, 0), "가Ag", font=font)
            line_height = int((bbox[3] - bbox[1]) * 1.4)  # 폰트 높이의 1.4배

        current_y = y

        for i, line in enumerate(wrapped_lines):
            # 그림자 효과 (옵션)
            if use_shadow:
                shadow_offset = 2
                if i == 0:
                    draw.text((x + shadow_offset, current_y + shadow_offset), bullet_symbol, font=font, fill=shadow_color)
                draw.text((x + indent + shadow_offset, current_y + shadow_offset), line, font=font, fill=shadow_color)

            # 첫 줄에만 Bullet 기호 그리기
            if i == 0:
                draw.text((x, current_y), bullet_symbol, font=font, fill=color)

            # 텍스트 그리기 (들여쓰기)
            draw.text((x + indent, current_y), line, font=font, fill=color)

            current_y += line_height

        return current_y

    @staticmethod
    def draw_structured_content(
        image: Image.Image,
        content: List[str],
        start_y: int,
        font: ImageFont.FreeTypeFont,
        color: str = "white",
        line_spacing: int = 50,
        start_x: int = 100,
        use_shadow: bool = False,
        max_width: int = None
    ) -> int:
        """
        구조화된 콘텐츠 렌더링 (bullet points 배열)

        Args:
            max_width: 최대 텍스트 너비 (줄바꿈 기준). None이면 줄바꿈 안 함

        Returns:
            최종 y 위치 (다음 요소 렌더링에 활용)
        """
        current_y = start_y

        for line in content:
            next_y = TextRenderer.draw_bullet_point(
                image, line, (start_x, current_y), font, color,
                use_shadow=use_shadow,
                max_width=max_width
            )
            # 줄바꿈 지원: draw_bullet_point가 반환한 y 위치 사용
            current_y = next_y + int(line_spacing * 0.3)  # 항목 간 추가 여백

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

    # 동적 폰트 사이즈 설정 (기본값 기준)
    BASE_TITLE_SIZE_FIRST = 88  # 첫 페이지 제목
    BASE_SUBTITLE_SIZE = 48  # 첫 페이지 소제목
    BASE_TITLE_SIZE_CONTENT = 80  # 본문 페이지 제목
    BASE_BULLET_SIZE = 44  # 본문 불릿 텍스트

    # 폰트 사이즈 최소/최대 범위
    MIN_TITLE_SIZE = 48
    MAX_TITLE_SIZE = 88
    MIN_BULLET_SIZE = 28
    MAX_BULLET_SIZE = 44

    def __init__(self, theme: dict, font_style: str, purpose: str, layout_type: str = "bottom", font_weight: str = "light", design_template: str = "default", aspect_ratio: str = "1:1"):
        self.theme = theme
        self.font_style = font_style
        self.purpose = purpose
        self.layout_type = layout_type  # 하위 호환성 유지, 실제로는 미사용 (페이지별 layout 사용)
        self.font_weight = font_weight  # light, medium, bold
        self.badge_text = BADGE_TEXT_MAP.get(purpose, '정보')
        self.scale = RENDER_SCALE  # 2x 렌더링

        # 이미지 비율에 따른 크기 설정
        self.aspect_ratio = aspect_ratio
        if aspect_ratio == "3:4":
            self.card_width = 1080
            self.card_height = 1440  # 3:4 비율
        else:  # 기본 1:1
            self.card_width = CARD_WIDTH
            self.card_height = CARD_HEIGHT
        self.render_width = self.card_width * self.scale
        self.render_height = self.card_height * self.scale

        # 디자인 템플릿 적용 (새 템플릿 시스템 사용)
        self.design_template = IMPROVED_TEMPLATES.get(design_template, IMPROVED_TEMPLATES.get("minimal_white", list(IMPROVED_TEMPLATES.values())[0]))
        self._apply_design_template()

    def _apply_design_template(self):
        """디자인 템플릿 설정을 인스턴스에 적용"""
        template = self.design_template

        # 텍스트 스타일 적용
        text_style = template.get("text_style", {})
        self.title_weight = text_style.get("title_weight", "bold")
        self.content_weight = text_style.get("content_weight", "medium")
        self.title_size_ratio = text_style.get("title_size_ratio", 1.0)
        self.content_size_ratio = text_style.get("content_size_ratio", 1.0)
        self.letter_spacing = text_style.get("letter_spacing", 0)
        self.line_height_ratio = text_style.get("line_height_ratio", 1.4)

        # 배경 스타일 적용
        bg_style = template.get("background_style", {})
        self.overlay_opacity = bg_style.get("overlay_opacity", 0.35)
        self.blur_radius = bg_style.get("blur_radius", 3)
        self.use_vignette = bg_style.get("use_vignette", False)
        self.gradient_overlay = bg_style.get("gradient_overlay", False)
        self.sepia_tone = bg_style.get("sepia_tone", False)

        # 레이아웃 스타일 적용
        layout_style = template.get("layout_style", {})
        self.padding_ratio = layout_style.get("padding_ratio", 1.0)
        self.content_align = layout_style.get("content_align", "center")
        self.title_position = layout_style.get("title_position", "center")

        # 카드 스타일 적용 (새로운 속성)
        card_style = template.get("card_style", {})
        self.corner_radius = card_style.get("corner_radius", 25)
        self.border_width = card_style.get("border_width", 0)
        self.border_color = card_style.get("border_color", None)
        self.card_shadow_blur = card_style.get("shadow_blur", 0)
        self.card_margin_ratio = card_style.get("card_margin_ratio", 1.0)
        self.glass_effect = card_style.get("glass_effect", False)

        # 장식 스타일 적용
        decoration = template.get("decoration", {})
        self.decoration_type = decoration.get("type", None)
        self.decoration_color = decoration.get("color", None)
        self.decoration_thickness = decoration.get("thickness", 0)

        # 텍스트 효과 적용
        text_effect = template.get("text_effect", {})
        self.shadow_type = text_effect.get("shadow_type", "gaussian")
        self.shadow_intensity = text_effect.get("shadow_intensity", 1.0)
        self.text_outline = text_effect.get("outline", False)
        self.outline_width = text_effect.get("outline_width", 0)

    def _calculate_dynamic_font_sizes(
        self,
        title: str,
        content_lines: List[str] = None,
        subtitle: str = None,
        is_first_page: bool = False
    ) -> dict:
        """
        텍스트 양에 따라 폰트 사이즈를 동적으로 계산합니다.
        텍스트가 잘리지 않도록 폰트 크기를 자동 조절합니다.
        이미지 영역(1080x1350)을 벗어나지 않도록 보장합니다.

        Returns:
            dict: title_size, subtitle_size (첫 페이지), bullet_size (본문 페이지)
        """
        title_len = len(title) if title else 0

        # 사용 가능한 높이 (로고 영역 제외): 약 1200px (2x 스케일 기준 2400px)
        # 상단 로고: ~100px, 하단 여백: ~50px
        AVAILABLE_HEIGHT = 1200  # 1x 기준

        if is_first_page:
            # 첫 페이지: 제목 + 소제목
            subtitle_len = len(subtitle) if subtitle else 0
            total_text_len = title_len + subtitle_len

            # 제목 길이 기반 사이즈 조절 (더 적극적으로)
            if title_len <= 8:
                title_size = self.BASE_TITLE_SIZE_FIRST  # 88
            elif title_len <= 12:
                title_size = 76
            elif title_len <= 16:
                title_size = 68
            elif title_len <= 22:
                title_size = 60
            elif title_len <= 30:
                title_size = 52
            else:
                title_size = self.MIN_TITLE_SIZE  # 48

            # 소제목 길이 기반 사이즈 조절 (더 적극적으로)
            if subtitle_len <= 15:
                subtitle_size = self.BASE_SUBTITLE_SIZE  # 48
            elif subtitle_len <= 25:
                subtitle_size = 42
            elif subtitle_len <= 35:
                subtitle_size = 38
            elif subtitle_len <= 50:
                subtitle_size = 34
            else:
                subtitle_size = 30

            # 전체 텍스트 양이 많으면 추가 축소
            if total_text_len > 60:
                title_size = max(self.MIN_TITLE_SIZE, title_size - 8)
                subtitle_size = max(28, subtitle_size - 6)

            return {
                'title_size': title_size,
                'subtitle_size': subtitle_size
            }
        else:
            # 본문 페이지: 제목 + 불릿 포인트
            content_count = len(content_lines) if content_lines else 0
            total_content_len = sum(len(line) for line in content_lines) if content_lines else 0
            max_line_len = max([len(line) for line in content_lines], default=0) if content_lines else 0

            # 제목 길이 기반 사이즈 조절
            if title_len <= 10:
                title_size = self.BASE_TITLE_SIZE_CONTENT  # 80
            elif title_len <= 15:
                title_size = 68
            elif title_len <= 22:
                title_size = 58
            else:
                title_size = self.MIN_TITLE_SIZE  # 48

            # 불릿 개수 및 총 길이 기반 사이즈 조절 (더 세밀하게)
            if content_count <= 2:
                if max_line_len <= 30:
                    bullet_size = self.BASE_BULLET_SIZE  # 44
                elif max_line_len <= 45:
                    bullet_size = 38
                else:
                    bullet_size = 34
            elif content_count <= 3:
                if max_line_len <= 25:
                    bullet_size = 40
                elif max_line_len <= 35:
                    bullet_size = 36
                elif max_line_len <= 50:
                    bullet_size = 32
                else:
                    bullet_size = 28
            elif content_count <= 4:
                if max_line_len <= 25:
                    bullet_size = 36
                elif max_line_len <= 35:
                    bullet_size = 32
                elif max_line_len <= 50:
                    bullet_size = 28
                else:
                    bullet_size = self.MIN_BULLET_SIZE  # 28
            elif content_count <= 5:
                if max_line_len <= 30:
                    bullet_size = 32
                elif max_line_len <= 45:
                    bullet_size = 28
                else:
                    bullet_size = self.MIN_BULLET_SIZE
            else:
                # 6개 이상의 불릿 - 최소 크기
                bullet_size = self.MIN_BULLET_SIZE

            # 총 텍스트 양이 매우 많으면 추가 축소
            if total_content_len > 150:
                title_size = max(self.MIN_TITLE_SIZE, title_size - 8)
                bullet_size = max(self.MIN_BULLET_SIZE, bullet_size - 4)

            return {
                'title_size': title_size,
                'bullet_size': bullet_size
            }

    def prepare_background(
        self,
        background_image: Image.Image,
        apply_blur: bool = False,
        blur_radius: int = 3,
        apply_overlay: bool = True,
        overlay_opacity: float = 0.35,
        overlay_color: tuple = None,  # None이면 이미지 밝기에 따라 자동 결정
        apply_vignette: bool = True,
        vignette_strength: float = 0.4,
        brightness: float = 0.65,
        contrast: float = 1.1,
        saturation: float = 1.1,
        auto_adjust_overlay: bool = True  # 이미지 밝기에 따라 오버레이 자동 조정
    ) -> tuple:
        """
        고급 배경 이미지 준비 (2x 해상도)

        Returns:
            tuple: (이미지, 색상정보 dict) - 색상정보에는 text_color, card_bg_color 등 포함
        """
        # RGB 변환
        if background_image.mode != 'RGB':
            background_image = background_image.convert('RGB')

        # 2x 크기로 조정 (고품질 리샘플링)
        img = background_image.resize((self.render_width, self.render_height), Image.Resampling.LANCZOS)

        # 이미지 밝기 분석 및 색상 결정
        color_info = None
        if auto_adjust_overlay:
            color_info = get_overlay_and_text_colors(img)
            if overlay_color is None:
                overlay_color = color_info["overlay_color"]
                overlay_opacity = color_info["overlay_opacity"]
            print(f"  🎨 이미지 밝기: {color_info['brightness']:.2f}, 텍스트: {color_info['text_color']}")

        # 이미지 보정 (밝기, 대비, 채도)
        img = BackgroundProcessor.enhance_image(img, brightness, contrast, saturation)

        # 세피아 톤 효과 (레트로 빈티지 템플릿)
        if self.sepia_tone:
            img = self._apply_sepia_tone(img)

        # Gaussian Blur (옵션)
        if apply_blur:
            img = BackgroundProcessor.apply_gaussian_blur(img, blur_radius * self.scale)

        # 반투명 오버레이 (텍스트 가독성 향상)
        if apply_overlay:
            final_overlay_color = overlay_color if overlay_color else (0, 0, 0)
            img = BackgroundProcessor.apply_overlay(img, final_overlay_color, overlay_opacity)

        # 그라데이션 오버레이 (그라데이션 드림 템플릿)
        if self.gradient_overlay:
            img = self._apply_gradient_overlay(img)

        # 비네트 효과
        if apply_vignette:
            img = BackgroundProcessor.apply_fast_vignette(img, vignette_strength)

        # RGB로 다시 변환 (alpha 제거)
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (0, 0, 0))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img

        return img, color_info

    def _downscale_to_final(self, image: Image.Image) -> Image.Image:
        """2x 이미지를 1x로 다운스케일 (고품질 안티앨리어싱)"""
        return image.resize((self.card_width, self.card_height), Image.Resampling.LANCZOS)

    def add_logo(self, image: Image.Image):
        """로고 배지 추가 (상단 중앙) - 2x 스케일 대응"""
        import os

        # 현재 이미지 크기에 따라 스케일 결정
        current_width = image.size[0]
        is_2x = current_width == self.render_width

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
            target_width = self.render_width if is_2x else self.card_width
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
        max_width = self.card_width - 160
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
        start_y = (self.card_height - total_height) // 2

        # 위치에 따른 Y 좌표 조정
        if self.layout_type == "top":
            start_y = 150
        elif self.layout_type == "bottom":
            start_y = self.card_height - total_height - 150

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
        # 배경 준비 (튜플 반환: 이미지, 색상정보)
        card, _ = self.prepare_background(background_image, auto_adjust_overlay=False)

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
        text_color: str = None,  # "white" 또는 "black" (None이면 이미지 밝기로 자동 결정)
        show_logo: bool = True  # 첫 페이지는 기본적으로 로고 표시
    ) -> str:
        """
        첫 페이지 전용 렌더링 (제목 + 소제목 + AI 배경 + 반투명 카드)
        Agent가 판단한 layout에 따라 텍스트 위치 조정
        이미지 밝기에 따라 오버레이/텍스트 색상 자동 결정
        2x 고해상도 렌더링 후 다운스케일
        - 로고는 선택적으로 표시 (첫 페이지는 기본: 표시)
        """
        # 배경 준비 (2x 해상도) + 이미지 밝기 분석 (템플릿 설정 적용)
        card, color_info = self.prepare_background(
            background_image,
            apply_blur=self.blur_radius > 0,
            blur_radius=self.blur_radius,
            apply_overlay=True,
            overlay_opacity=self.overlay_opacity,
            apply_vignette=self.use_vignette,
            auto_adjust_overlay=True
        )

        # 로고 추가 (선택적)
        if show_logo:
            self.add_logo(card)

        # 텍스트 색상 결정 (이미지 밝기 기반 자동 결정)
        if text_color:
            actual_text_color = text_color
        elif color_info:
            actual_text_color = color_info["text_color"]
        else:
            actual_text_color = self.theme.get("text", "white")

        # 카드 배경색 결정 (이미지 밝기 기반)
        if color_info:
            card_bg_color = color_info["card_bg_color"]
            card_opacity = color_info["card_opacity"]
        else:
            card_bg_color = (0, 0, 0)
            card_opacity = 0.35

        # 동적 폰트 사이즈 계산 (텍스트 길이에 따라 자동 조절)
        font_sizes = self._calculate_dynamic_font_sizes(
            title=title,
            subtitle=subtitle,
            is_first_page=True
        )
        # 디자인 템플릿의 사이즈 비율 적용
        title_size = int(font_sizes['title_size'] * self.title_size_ratio)
        subtitle_size = int(font_sizes['subtitle_size'] * self.content_size_ratio)

        # 폰트 설정 (2x 스케일 적용) - 동적 사이즈 + 템플릿 weight 사용
        title_font = FontManager.get_font(self.font_style, title_size * self.scale, weight=self.title_weight)
        subtitle_font = FontManager.get_font(self.font_style, subtitle_size * self.scale, weight=self.content_weight)

        # 2x 스케일 기준 치수 (템플릿 패딩 비율 적용)
        margin_x = int(80 * self.scale * self.padding_ratio)
        card_padding = int(45 * self.scale * self.padding_ratio)
        max_width = self.render_width - margin_x * 2 - card_padding * 2

        # 로고 영역 (로고 표시 시만 적용)
        top_margin = int((120 * self.scale) if show_logo else (40 * self.scale))
        bottom_margin = int(40 * self.scale)
        available_height = self.render_height - top_margin - bottom_margin

        # 텍스트 총 높이 계산
        draw = ImageDraw.Draw(card)
        title_lines = TextRenderer.wrap_text(title, title_font, max_width, draw)
        subtitle_lines = TextRenderer.wrap_text(subtitle, subtitle_font, max_width, draw)

        # 라인 높이도 폰트 사이즈에 비례하여 조절 (템플릿 line_height_ratio 적용)
        title_line_height = int((title_size + 18) * self.scale * self.line_height_ratio)
        subtitle_line_height = int((subtitle_size + 14) * self.scale * self.line_height_ratio)
        title_height = len(title_lines) * title_line_height
        subtitle_height = len(subtitle_lines) * subtitle_line_height
        gap = int(25 * self.scale * self.padding_ratio)  # 제목-부제목 간격

        # 전체 콘텐츠 높이
        total_content_height = title_height + gap + subtitle_height

        # 카드 높이 계산 (사용 가능한 전체 높이 사용)
        card_height = total_content_height + card_padding * 2
        max_card_height = available_height - 20 * self.scale

        # 카드가 너무 크면 사용 가능한 최대 높이로 제한
        if card_height > max_card_height:
            card_height = max_card_height

        card_width = self.render_width - margin_x * 2

        # Agent가 판단한 layout에 따라 카드 위치 결정
        if layout == "top":
            card_y = top_margin + 20 * self.scale
        elif layout == "bottom":
            card_y = self.render_height - card_height - bottom_margin
        else:  # center (기본값)
            card_y = top_margin + (available_height - card_height) // 2

        # 반투명 카드 배경 그리기 (이미지 밝기에 따라 색상 자동 결정)
        card = self._draw_content_card(
            card.convert('RGBA'),
            x=margin_x,
            y=int(card_y),
            width=card_width,
            height=int(card_height),
            bg_color=card_bg_color,
            opacity=card_opacity,
            corner_radius=25 * self.scale
        )

        # 제목 Y 위치 (카드 내부)
        title_y = card_y + card_padding

        # 그림자 색상 결정 (텍스트 색상 반대)
        if actual_text_color == "black":
            title_shadow_color = (255, 255, 255, 100)  # 밝은 그림자
            subtitle_shadow_color = (255, 255, 255, 60)
        else:
            title_shadow_color = (0, 0, 0, 140)  # 어두운 그림자
            subtitle_shadow_color = (0, 0, 0, 80)

        # 제목 렌더링 (Gaussian Blur 그림자)
        TextRenderer.draw_text_with_shadow(
            card, title, (margin_x + card_padding, title_y),
            title_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=True,
            use_gaussian_shadow=True,
            blur_radius=10 * self.scale,
            shadow_offset=(5 * self.scale, 5 * self.scale),
            shadow_color=title_shadow_color,
            line_spacing=20 * self.scale
        )

        # 소제목 렌더링 (제목 아래)
        subtitle_y = title_y + title_height + gap
        TextRenderer.draw_text_with_shadow(
            card, subtitle, (margin_x + card_padding, subtitle_y),
            subtitle_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=True,
            use_gaussian_shadow=True,
            blur_radius=6 * self.scale,
            shadow_offset=(3 * self.scale, 3 * self.scale),
            shadow_color=subtitle_shadow_color,
            line_spacing=12 * self.scale
        )

        # 페이지 번호
        self._add_page_number(card, page_num)

        # RGB로 변환 후 다운스케일
        if card.mode == 'RGBA':
            rgb_card = Image.new('RGB', card.size, (0, 0, 0))
            rgb_card.paste(card, mask=card.split()[3])
            card = rgb_card

        final_card = self._downscale_to_final(card)

        # Base64 변환
        buffer = io.BytesIO()
        final_card.save(buffer, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def _apply_sepia_tone(self, image: Image.Image) -> Image.Image:
        """세피아 톤 효과 적용"""
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 세피아 매트릭스 적용
        sepia_data = []
        for r, g, b in image.getdata():
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            sepia_data.append((min(255, tr), min(255, tg), min(255, tb)))

        sepia_image = Image.new('RGB', image.size)
        sepia_image.putdata(sepia_data)
        return sepia_image

    def _apply_gradient_overlay(self, image: Image.Image) -> Image.Image:
        """그라데이션 오버레이 효과 적용"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # 대각선 그라데이션 오버레이 생성
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        width, height = image.size
        # 보라-파랑 그라데이션
        for i in range(height):
            ratio = i / height
            r = int(102 + (118 - 102) * ratio)  # 667EEA -> 764BA2
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            alpha = int(80 * (1 - abs(ratio - 0.5) * 2))  # 중앙에서 가장 진함
            draw.line([(0, i), (width, i)], fill=(r, g, b, alpha))

        return Image.alpha_composite(image, overlay)

    def _draw_decoration(self, image: Image.Image, card_x: int, card_y: int,
                         card_width: int, card_height: int) -> Image.Image:
        """템플릿에 따른 장식 요소 그리기"""
        if not self.decoration_type:
            return image

        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        decoration_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(decoration_layer, 'RGBA')

        # 색상 파싱
        color = self._parse_decoration_color(self.decoration_color)
        thickness = int(self.decoration_thickness * self.scale)

        if self.decoration_type == "line_top":
            # 상단 라인
            line_y = card_y - thickness * 2
            line_width = int(card_width * 0.3)
            line_x = card_x + (card_width - line_width) // 2
            draw.rectangle([line_x, line_y, line_x + line_width, line_y + thickness], fill=color)

        elif self.decoration_type == "line_bottom":
            # 하단 라인
            line_y = card_y + card_height + thickness
            line_width = int(card_width * 0.3)
            line_x = card_x + (card_width - line_width) // 2
            draw.rectangle([line_x, line_y, line_x + line_width, line_y + thickness], fill=color)

        elif self.decoration_type == "corner_accent":
            # 코너 강조
            corner_size = int(40 * self.scale)
            # 좌상단
            draw.rectangle([card_x, card_y, card_x + corner_size, card_y + thickness], fill=color)
            draw.rectangle([card_x, card_y, card_x + thickness, card_y + corner_size], fill=color)
            # 우상단
            draw.rectangle([card_x + card_width - corner_size, card_y, card_x + card_width, card_y + thickness], fill=color)
            draw.rectangle([card_x + card_width - thickness, card_y, card_x + card_width, card_y + corner_size], fill=color)
            # 좌하단
            draw.rectangle([card_x, card_y + card_height - thickness, card_x + corner_size, card_y + card_height], fill=color)
            draw.rectangle([card_x, card_y + card_height - corner_size, card_x + thickness, card_y + card_height], fill=color)
            # 우하단
            draw.rectangle([card_x + card_width - corner_size, card_y + card_height - thickness, card_x + card_width, card_y + card_height], fill=color)
            draw.rectangle([card_x + card_width - thickness, card_y + card_height - corner_size, card_x + card_width, card_y + card_height], fill=color)

        elif self.decoration_type == "frame":
            # 전체 프레임
            draw.rectangle([card_x, card_y, card_x + card_width, card_y + thickness], fill=color)
            draw.rectangle([card_x, card_y + card_height - thickness, card_x + card_width, card_y + card_height], fill=color)
            draw.rectangle([card_x, card_y, card_x + thickness, card_y + card_height], fill=color)
            draw.rectangle([card_x + card_width - thickness, card_y, card_x + card_width, card_y + card_height], fill=color)

        elif self.decoration_type == "neon_border":
            # 네온 테두리 (글로우 효과)
            for i in range(3):
                blur_thickness = thickness + (3 - i) * 4
                alpha = 80 + i * 50
                glow_color = (*color[:3], alpha)
                draw.rounded_rectangle(
                    [card_x - blur_thickness, card_y - blur_thickness,
                     card_x + card_width + blur_thickness, card_y + card_height + blur_thickness],
                    radius=int(self.corner_radius * self.scale) + blur_thickness,
                    outline=glow_color,
                    width=2
                )

        elif self.decoration_type == "vintage_frame":
            # 빈티지 프레임 (이중 테두리)
            outer_offset = thickness * 2
            # 외부 프레임
            draw.rounded_rectangle(
                [card_x - outer_offset, card_y - outer_offset,
                 card_x + card_width + outer_offset, card_y + card_height + outer_offset],
                radius=int(self.corner_radius * self.scale) + outer_offset,
                outline=color,
                width=thickness
            )
            # 내부 프레임
            inner_offset = thickness // 2
            draw.rounded_rectangle(
                [card_x + inner_offset, card_y + inner_offset,
                 card_x + card_width - inner_offset, card_y + card_height - inner_offset],
                radius=max(0, int(self.corner_radius * self.scale) - inner_offset),
                outline=(*color[:3], color[3] // 2),
                width=max(1, thickness // 2)
            )

        return Image.alpha_composite(image, decoration_layer)

    def _parse_decoration_color(self, color_str) -> tuple:
        """장식 색상 문자열을 RGBA 튜플로 변환"""
        if not color_str:
            return (255, 255, 255, 200)

        if color_str == "accent":
            # 테마에서 액센트 색상 가져오기
            return (255, 255, 255, 200)

        if color_str.startswith("rgba"):
            # rgba(255,255,255,0.3) 형식 파싱
            import re
            match = re.match(r'rgba\((\d+),(\d+),(\d+),([\d.]+)\)', color_str.replace(' ', ''))
            if match:
                r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                a = int(float(match.group(4)) * 255)
                return (r, g, b, a)

        if color_str.startswith("#"):
            # HEX 색상 파싱
            hex_color = color_str.lstrip('#')
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b, 255)

        return (255, 255, 255, 200)

    def _draw_content_card(
        self,
        image: Image.Image,
        x: int, y: int, width: int, height: int,
        bg_color: tuple = (255, 255, 255),
        opacity: float = 0.15,
        corner_radius: int = None
    ):
        """반투명 카드 배경 그리기 (라운드 코너 + 테두리 + 그림자)"""
        # 템플릿 설정 사용
        if corner_radius is None:
            corner_radius = int(self.corner_radius * self.scale)

        # RGBA 모드로 변환
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # 그림자 레이어 (카드 그림자가 있는 경우)
        if self.card_shadow_blur > 0:
            shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer, 'RGBA')
            shadow_offset = int(self.card_shadow_blur * 0.3)
            shadow_color = (0, 0, 0, int(80 * (self.card_shadow_blur / 50)))
            shadow_draw.rounded_rectangle(
                [x + shadow_offset, y + shadow_offset, x + width + shadow_offset, y + height + shadow_offset],
                radius=corner_radius,
                fill=shadow_color
            )
            # 블러 효과 (간단하게 여러 레이어로 구현)
            from PIL import ImageFilter
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=self.card_shadow_blur * 0.5))
            image = Image.alpha_composite(image, shadow_layer)

        # 반투명 카드 레이어 생성
        card_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(card_layer, 'RGBA')

        # 글래스 이펙트 (glass_effect가 True인 경우)
        if self.glass_effect:
            # 글래스모피즘: 더 투명하고 흐린 배경
            fill_color = (*bg_color, int(255 * opacity * 0.7))
        else:
            fill_color = (*bg_color, int(255 * opacity))

        # 라운드 사각형 그리기
        draw.rounded_rectangle(
            [x, y, x + width, y + height],
            radius=corner_radius,
            fill=fill_color
        )

        # 테두리 (border_width가 있는 경우)
        if self.border_width > 0 and self.border_color:
            border_color = self._parse_decoration_color(self.border_color)
            draw.rounded_rectangle(
                [x, y, x + width, y + height],
                radius=corner_radius,
                outline=border_color,
                width=int(self.border_width * self.scale)
            )

        # 합성
        result = Image.alpha_composite(image.convert('RGBA'), card_layer)

        # 장식 요소 추가
        result = self._draw_decoration(result, x, y, width, height)

        return result

    def build_content_page(
        self,
        bg_color: tuple,
        title: str,
        content_lines: List[str],
        page_num: int,
        text_color: str = None,  # "white" 또는 "black"
        use_gradient: bool = True,  # 그라데이션 배경 사용 여부
        show_logo: bool = False  # 로고 표시 여부 (기본: 표시 안 함)
    ) -> str:
        """
        본문 페이지 렌더링 (카드 스타일 + 수직 중앙 정렬)
        2x 고해상도 렌더링 후 다운스케일
        - 줄바꿈을 통해 모든 텍스트가 이미지 안에 들어가도록 함
        - 로고는 선택적으로 표시 (기본: 표시 안 함)
        """
        # 배경 생성 (2x 해상도)
        if use_gradient:
            # 그라데이션 배경 (primary → 약간 어두운 색)
            end_color = tuple(max(0, c - 40) for c in bg_color)
            card = BackgroundProcessor.create_fast_gradient(
                self.render_width, self.render_height,
                bg_color, end_color,
                direction=self.theme.get("gradient_type", "vertical")
            )
        else:
            # 단색 배경
            card = Image.new('RGB', (self.render_width, self.render_height), bg_color)

        # 로고 추가 (선택적)
        if show_logo:
            self.add_logo(card)

        # 텍스트 색상 결정
        if text_color:
            actual_text_color = text_color
        else:
            actual_text_color = self.theme.get("text", "white")

        # 동적 폰트 사이즈 계산 (텍스트 양에 따라 자동 조절)
        font_sizes = self._calculate_dynamic_font_sizes(
            title=title,
            content_lines=content_lines,
            is_first_page=False
        )
        # 디자인 템플릿의 사이즈 비율 적용
        title_size = int(font_sizes['title_size'] * self.title_size_ratio)
        bullet_size = int(font_sizes['bullet_size'] * self.content_size_ratio)

        # 폰트 설정 (2x 스케일 적용) - 동적 사이즈 + 템플릿 weight 사용
        title_font = FontManager.get_font(self.font_style, title_size * self.scale, weight=self.title_weight)
        bullet_font = FontManager.get_font(self.font_style, bullet_size * self.scale, weight=self.content_weight)

        # 2x 스케일 기준 치수 (템플릿 패딩 비율 적용)
        margin_x = int(80 * self.scale * self.padding_ratio)
        card_padding = int(50 * self.scale * self.padding_ratio)
        max_width = self.render_width - margin_x * 2 - card_padding * 2

        # 로고 영역 (로고 표시 시만 적용)
        top_margin = int((120 * self.scale) if show_logo else (40 * self.scale))
        bottom_margin = int(40 * self.scale)
        available_height = self.render_height - top_margin - bottom_margin

        # 콘텐츠 높이 사전 계산
        draw = ImageDraw.Draw(card)
        title_lines = TextRenderer.wrap_text(title, title_font, max_width, draw)
        # 템플릿 line_height_ratio 적용
        title_line_height = int((title_size + 16) * self.scale * self.line_height_ratio)
        title_height = len(title_lines) * title_line_height

        # 불릿 텍스트의 줄바꿈을 고려한 총 높이 계산
        bullet_indent = 35 * RENDER_SCALE // 2
        bullet_text_max_width = max_width - bullet_indent - int(40 * self.scale)

        # 각 불릿 라인의 줄바꿈 결과 미리 계산
        wrapped_bullets = []
        for line in content_lines:
            clean_text = line.lstrip('•- ').strip()
            clean_text = strip_markdown(clean_text)
            clean_text = strip_emojis(clean_text)
            lines = TextRenderer.wrap_text(clean_text, bullet_font, bullet_text_max_width, draw)
            wrapped_bullets.append(lines)

        # 불릿 줄 높이 계산 (템플릿 line_height_ratio 적용)
        bbox = draw.textbbox((0, 0), "가Ag", font=bullet_font)
        bullet_single_line_height = int((bbox[3] - bbox[1]) * 1.35 * self.line_height_ratio)

        # 불릿 간 여백 (각 불릿 항목 사이)
        bullet_item_gap = int(20 * self.scale * self.padding_ratio)

        # 총 불릿 영역 높이 계산
        total_bullet_height = 0
        for lines in wrapped_bullets:
            total_bullet_height += len(lines) * bullet_single_line_height + bullet_item_gap

        # 전체 콘텐츠 높이 (제목 + 구분선 + 간격 + 불릿)
        title_bullet_gap = 60 * self.scale  # 구분선 + 간격
        total_content_height = title_height + title_bullet_gap + total_bullet_height

        # 카드 높이 계산 (사용 가능한 전체 높이 사용)
        card_height = total_content_height + card_padding * 2
        max_card_height = available_height - 20 * self.scale

        # 카드가 너무 크면 사용 가능한 최대 높이로 제한
        if card_height > max_card_height:
            card_height = max_card_height

        card_width = self.render_width - margin_x * 2

        # 카드 Y 위치 (수직 중앙)
        card_y = top_margin + (available_height - card_height) // 2

        # 반투명 카드 배경 그리기
        card = self._draw_content_card(
            card.convert('RGBA'),
            x=margin_x,
            y=int(card_y),
            width=card_width,
            height=int(card_height),
            bg_color=(255, 255, 255) if actual_text_color == "black" else (0, 0, 0),
            opacity=0.12,
            corner_radius=25 * self.scale
        )

        # 제목 Y 위치 (카드 내부 상단)
        title_y = card_y + card_padding

        # 제목 렌더링 (중앙 정렬)
        TextRenderer.draw_text_with_shadow(
            card, title, (margin_x + card_padding, title_y),
            title_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=False,
            use_gaussian_shadow=False
        )

        # 구분선 추가
        line_y = title_y + title_height + 20 * self.scale
        line_draw = ImageDraw.Draw(card, 'RGBA')
        line_color = (255, 255, 255, 60) if actual_text_color == "white" else (0, 0, 0, 40)
        line_draw.line(
            [(margin_x + card_padding + 40 * self.scale, line_y),
             (self.render_width - margin_x - card_padding - 40 * self.scale, line_y)],
            fill=line_color,
            width=2 * self.scale
        )

        # Bullet points 렌더링 (구분선 아래) - 줄바꿈 적용
        bullet_y = line_y + 30 * self.scale
        bullet_start_x = margin_x + card_padding + 20 * self.scale
        max_bullet_y = card_y + card_height - card_padding

        current_y = bullet_y
        for i, line in enumerate(content_lines):
            # 카드 영역을 벗어나는지 확인
            if current_y >= max_bullet_y:
                break

            # 줄바꿈을 적용하여 불릿 포인트 렌더링
            next_y = TextRenderer.draw_bullet_point(
                card, line, (bullet_start_x, current_y),
                bullet_font, color=actual_text_color,
                use_shadow=False,
                max_width=max_width - 40 * self.scale,
                line_height=bullet_single_line_height
            )

            # 다음 불릿 항목 시작 위치 (항목 간 여백 추가)
            current_y = next_y + bullet_item_gap

        # 페이지 번호
        self._add_page_number(card, page_num)

        # RGB로 변환 후 다운스케일
        if card.mode == 'RGBA':
            rgb_card = Image.new('RGB', card.size, (0, 0, 0))
            rgb_card.paste(card, mask=card.split()[3])
            card = rgb_card

        final_card = self._downscale_to_final(card)

        # Base64 변환
        buffer = io.BytesIO()
        final_card.save(buffer, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def build_content_page_with_image(
        self,
        background_image: Image.Image,
        title: str,
        content_lines: List[str],
        page_num: int,
        text_color: str = None,
        show_logo: bool = False
    ) -> str:
        """
        AI 이미지를 배경으로 사용하는 본문 페이지 렌더링 (심플 모드)
        - 배경에 블러 효과와 오버레이 적용
        - 반투명 카드 위에 제목 + 불릿 포인트 표시
        """
        # 배경 준비 (블러 + 오버레이 적용)
        card, color_info = self.prepare_background(
            background_image,
            apply_blur=True,
            blur_radius=8,  # 본문 페이지는 블러 강하게
            apply_overlay=True,
            overlay_opacity=0.45,  # 텍스트 가독성을 위해 오버레이 강하게
            apply_vignette=True,
            auto_adjust_overlay=True
        )

        # 로고 추가 (선택적)
        if show_logo:
            self.add_logo(card)

        # 텍스트 색상 결정 (이미지 밝기 기반)
        if text_color:
            actual_text_color = text_color
        elif color_info:
            actual_text_color = color_info["text_color"]
        else:
            actual_text_color = "white"

        # 카드 배경색 결정
        if color_info:
            card_bg_color = color_info["card_bg_color"]
            card_opacity = color_info["card_opacity"]
        else:
            card_bg_color = (0, 0, 0)
            card_opacity = 0.35

        # 동적 폰트 사이즈 계산
        font_sizes = self._calculate_dynamic_font_sizes(
            title=title,
            content_lines=content_lines,
            is_first_page=False
        )
        title_size = int(font_sizes['title_size'] * self.title_size_ratio)
        bullet_size = int(font_sizes['bullet_size'] * self.content_size_ratio)

        # 폰트 설정 (2x 스케일 적용)
        title_font = FontManager.get_font(self.font_style, title_size * self.scale, weight=self.title_weight)
        bullet_font = FontManager.get_font(self.font_style, bullet_size * self.scale, weight=self.content_weight)

        # 2x 스케일 기준 치수
        margin_x = int(80 * self.scale * self.padding_ratio)
        card_padding = int(50 * self.scale * self.padding_ratio)
        max_width = self.render_width - margin_x * 2 - card_padding * 2

        # 로고 영역
        top_margin = int((120 * self.scale) if show_logo else (40 * self.scale))
        bottom_margin = int(40 * self.scale)
        available_height = self.render_height - top_margin - bottom_margin

        # 콘텐츠 높이 사전 계산
        draw = ImageDraw.Draw(card)
        title_lines = TextRenderer.wrap_text(title, title_font, max_width, draw)
        title_line_height = int((title_size + 16) * self.scale * self.line_height_ratio)
        title_height = len(title_lines) * title_line_height

        # 불릿 텍스트 줄바꿈 계산
        bullet_indent = 35 * RENDER_SCALE // 2
        bullet_text_max_width = max_width - bullet_indent - int(40 * self.scale)

        wrapped_bullets = []
        for line in content_lines:
            clean_text = line.lstrip('•- ').strip()
            clean_text = strip_markdown(clean_text)
            clean_text = strip_emojis(clean_text)
            lines = TextRenderer.wrap_text(clean_text, bullet_font, bullet_text_max_width, draw)
            wrapped_bullets.append(lines)

        # 불릿 줄 높이 계산
        bbox = draw.textbbox((0, 0), "가Ag", font=bullet_font)
        bullet_single_line_height = int((bbox[3] - bbox[1]) * 1.35 * self.line_height_ratio)
        bullet_item_gap = int(20 * self.scale * self.padding_ratio)

        total_bullet_height = 0
        for lines in wrapped_bullets:
            total_bullet_height += len(lines) * bullet_single_line_height + bullet_item_gap

        # 전체 콘텐츠 높이
        title_bullet_gap = 60 * self.scale
        total_content_height = title_height + title_bullet_gap + total_bullet_height

        # 카드 높이 계산
        card_height = total_content_height + card_padding * 2
        max_card_height = available_height - 20 * self.scale
        if card_height > max_card_height:
            card_height = max_card_height

        card_width = self.render_width - margin_x * 2
        card_y = top_margin + (available_height - card_height) // 2

        # 반투명 카드 배경 그리기
        card = self._draw_content_card(
            card.convert('RGBA'),
            x=margin_x,
            y=int(card_y),
            width=card_width,
            height=int(card_height),
            bg_color=card_bg_color,
            opacity=card_opacity,
            corner_radius=25 * self.scale
        )

        # 제목 Y 위치
        title_y = card_y + card_padding

        # 그림자 색상 결정
        if actual_text_color == "black":
            title_shadow_color = (255, 255, 255, 100)
        else:
            title_shadow_color = (0, 0, 0, 140)

        # 제목 렌더링 (Gaussian Blur 그림자)
        TextRenderer.draw_text_with_shadow(
            card, title, (margin_x + card_padding, title_y),
            title_font, color=actual_text_color,
            max_width=max_width,
            align="center", shadow=True,
            use_gaussian_shadow=True,
            blur_radius=8 * self.scale,
            shadow_offset=(4 * self.scale, 4 * self.scale),
            shadow_color=title_shadow_color,
            line_spacing=16 * self.scale
        )

        # 구분선 추가
        line_y = title_y + title_height + 20 * self.scale
        line_draw = ImageDraw.Draw(card, 'RGBA')
        line_color = (255, 255, 255, 60) if actual_text_color == "white" else (0, 0, 0, 40)
        line_draw.line(
            [(margin_x + card_padding + 40 * self.scale, line_y),
             (self.render_width - margin_x - card_padding - 40 * self.scale, line_y)],
            fill=line_color,
            width=2 * self.scale
        )

        # Bullet points 렌더링
        bullet_y = line_y + 30 * self.scale
        bullet_start_x = margin_x + card_padding + 20 * self.scale
        max_bullet_y = card_y + card_height - card_padding

        current_y = bullet_y
        for i, line in enumerate(content_lines):
            if current_y >= max_bullet_y:
                break

            next_y = TextRenderer.draw_bullet_point(
                card, line, (bullet_start_x, current_y),
                bullet_font, color=actual_text_color,
                use_shadow=True,
                max_width=max_width - 40 * self.scale,
                line_height=bullet_single_line_height
            )
            current_y = next_y + bullet_item_gap

        # 페이지 번호
        self._add_page_number(card, page_num)

        # RGB로 변환 후 다운스케일
        if card.mode == 'RGBA':
            rgb_card = Image.new('RGB', card.size, (0, 0, 0))
            rgb_card.paste(card, mask=card.split()[3])
            card = rgb_card

        final_card = self._downscale_to_final(card)

        # Base64 변환
        buffer = io.BytesIO()
        final_card.save(buffer, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"

    def _add_page_number(self, image: Image.Image, page_num: int):
        """페이지 번호 추가 (2x 스케일 대응)"""
        # 현재 이미지 크기에 따라 스케일 결정
        current_width = image.size[0]
        is_2x = current_width == self.render_width
        scale = self.scale if is_2x else 1

        draw = ImageDraw.Draw(image, 'RGBA')
        page_font = FontManager.get_font(self.font_style, 20 * scale, weight='regular')

        page_text = f"{page_num}"
        target_width = self.render_width if is_2x else self.card_width
        target_height = self.render_height if is_2x else self.card_height

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


# ==================== 디자인 템플릿 API ====================

@router.get("/cardnews/design-templates")
async def get_design_templates():
    """
    카드뉴스 디자인 템플릿 목록 조회 (기존 + 새 템플릿 통합)

    Returns:
        templates: 사용 가능한 디자인 템플릿 목록
    """
    templates = get_design_templates_list()
    return {
        "success": True,
        "templates": templates
    }


@router.get("/cardnews/design-templates-v2")
async def get_design_templates_v2():
    """
    개선된 디자인 템플릿 목록 조회 (카테고리별 그룹화)

    Returns:
        categories: 카테고리별로 그룹화된 템플릿 목록
    """
    categories = get_improved_templates_by_category()
    return {
        "success": True,
        "categories": categories,
        "total_templates": sum(len(cat["templates"]) for cat in categories)
    }


@router.get("/cardnews/design-templates/{template_id}")
async def get_template_detail(template_id: str):
    """
    특정 템플릿의 상세 정보 조회

    Args:
        template_id: 템플릿 ID

    Returns:
        template: 템플릿 상세 정보 (팔레트, 레이아웃 포함)
    """
    config = get_all_template_config(template_id)

    if config["type"] == "improved":
        template = config["template"]
        palette = config["palette"]
        layout = config["layout"]

        return {
            "success": True,
            "template": {
                "id": template["id"],
                "name": template["name"],
                "category": template["category"],
                "description": template["description"],
                "preview_color": template["preview_color"],
                "palette": {
                    "primary": palette["primary"],
                    "secondary": palette["secondary"],
                    "accent": palette["accent"],
                    "text_primary": palette["text_primary"],
                    "text_secondary": palette["text_secondary"],
                    "gradient": palette.get("gradient", [])
                },
                "layout": {
                    "name": layout["name"],
                    "description": layout["description"],
                    "title_position": layout["title_position"],
                    "content_align": layout["content_align"]
                },
                "text_style": template["text_style"],
                "card_style": template["card_style"],
                "decoration": template.get("decoration", {}),
                "text_effect": template.get("text_effect", {})
            }
        }
    else:
        template = config["template"]
        return {
            "success": True,
            "template": {
                "id": template["id"],
                "name": template["name"],
                "category": "classic",
                "description": template["description"],
                "preview_color": template["preview_color"],
                "text_style": template["text_style"],
                "background_style": template["background_style"],
                "layout_style": template["layout_style"],
                "card_style": template["card_style"],
                "decoration": template.get("decoration", {}),
                "text_effect": template.get("text_effect", {})
            }
        }


@router.get("/cardnews/template-categories")
async def get_template_categories():
    """
    템플릿 카테고리 목록 조회

    Returns:
        categories: 카테고리 정보 목록
    """
    categories = [
        {
            "id": cat_id,
            "name": cat["name"],
            "description": cat["description"],
            "icon": cat["icon"],
            "template_count": len(cat["templates"])
        }
        for cat_id, cat in TEMPLATE_CATEGORIES.items()
    ]

    return {
        "success": True,
        "categories": categories
    }


# ==================== AI Agentic 카드뉴스 생성 (Non-streaming) ====================

@router.post("/generate-agentic-cardnews")
async def generate_agentic_cardnews(
    prompt: str = Form(...),
    purpose: str = Form(default="info"),
    fontStyle: str = Form(default="pretendard"),  # AI가 자동 선택하므로 기본값만 유지
    colorTheme: str = Form(default="warm"),  # 사용자가 선택한 테마 사용 (기본: warm)
    designTemplate: str = Form(default="default"),  # 디자인 템플릿 ID
    aspectRatio: str = Form(default="1:1"),  # 이미지 비율 (1:1 또는 3:4)
    generateImages: bool = Form(default=True),
    layoutType: str = Form(default="bottom"),
    userContext: str = Form(default=None),  # 사용자 컨텍스트 (JSON 문자열)
    saveToDb: bool = Form(default=True),  # DB에 저장할지 여부
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        # 디자인 템플릿 로드 (새 템플릿 시스템 사용)
        import random

        # 'none': 템플릿 없이 AI 이미지 + 심플 텍스트
        # 'auto': 랜덤 템플릿 선택
        # 기타: 지정된 템플릿 사용
        use_simple_mode = (designTemplate == 'none')

        if use_simple_mode:
            # 심플 모드: minimal_white를 기반으로 하되 장식 최소화
            selected_template_id = 'minimal_white'
            template_config = IMPROVED_TEMPLATES.get('minimal_white', list(IMPROVED_TEMPLATES.values())[0])
            template_name = "심플 이미지"
            cardnews_logger.info(f"🖼️ 심플 모드: 템플릿 없이 AI 이미지 + 텍스트")
        elif designTemplate == 'auto' or designTemplate not in IMPROVED_TEMPLATES:
            # 랜덤 템플릿 선택
            template_ids = list(IMPROVED_TEMPLATES.keys())
            selected_template_id = random.choice(template_ids)
            template_config = IMPROVED_TEMPLATES[selected_template_id]
            cardnews_logger.info(f"🎲 자동 템플릿 선택: {selected_template_id}")
            template_name = template_config.get("name", "미니멀 화이트")
        else:
            template_config = IMPROVED_TEMPLATES[designTemplate]
            selected_template_id = designTemplate
            template_name = template_config.get("name", "미니멀 화이트")

        # 콘텐츠 페이지용 조화로운 색상 팔레트 생성
        content_page_count = len(pages) - 1  # 첫 페이지 제외
        if content_page_count > 0:
            color_palette = generate_harmonious_palette(final_bg_color, content_page_count)
            cardnews_logger.info(f"🎨 조화로운 색상 팔레트 생성: {len(color_palette)}개 색상")
            for idx, color in enumerate(color_palette):
                cardnews_logger.info(f"   페이지 {idx + 2}: RGB{color}")
        else:
            color_palette = []

        print("\n📰 최종 카드뉴스 조립 중...")
        print(f"   🎨 기준 배경색: RGB{final_bg_color}")
        print(f"   🎨 콘텐츠 페이지별 조화로운 색상 팔레트 적용")
        print(f"   📝 텍스트색: {text_color} (페이지별 동적 조정)")
        print(f"   🔤 폰트: {font_pair}")
        print(f"   📐 템플릿: {template_name}")
        cardnews_logger.info(f"📐 디자인 템플릿 적용: {selected_template_id} ({template_name})")

        builder = CardNewsBuilder(dynamic_theme, font_pair, purpose, font_weight="regular", design_template=selected_template_id, aspect_ratio=aspectRatio)

        final_cards = []

        # 심플 모드에서 첫 번째 AI 이미지 저장 (내용 페이지 배경으로 재사용)
        first_bg_image = None

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

                # 심플 모드에서 첫 번째 이미지 저장
                if use_simple_mode:
                    first_bg_image = bg_image.copy()

                # 첫 페이지 생성 (Agent가 판단한 layout 사용)
                # 첫 페이지는 AI 이미지가 배경이므로 text_color=None으로 전달하여
                # 이미지 밝기 기반으로 텍스트 색상을 자동 결정하도록 함
                card_base64 = builder.build_first_page(
                    background_image=bg_image,
                    title=page['title'],
                    subtitle=page.get('subtitle', ''),
                    page_num=i + 1,
                    layout=page.get('layout', 'center'),
                    text_color=None  # 이미지 밝기로 자동 결정
                )
                final_cards.append(card_base64)

            else:  # 나머지 페이지: 컬러 배경 또는 AI 이미지 + 제목 + bullet points
                if use_simple_mode and first_bg_image:
                    # 심플 모드: AI 이미지를 배경으로 사용 (블러 처리)
                    print(f"    📍 페이지 {i+1}: 심플 모드 - AI 이미지 배경 사용")
                    card_base64 = builder.build_content_page_with_image(
                        background_image=first_bg_image,
                        title=page['title'],
                        content_lines=page.get('content', ["• 내용이 없습니다"]),
                        page_num=i + 1
                    )
                else:
                    # 일반 모드: 페이지별 조화로운 배경색 적용 (팔레트에서 선택)
                    page_bg_color = color_palette[i - 1] if i - 1 < len(color_palette) else final_bg_color
                    # 해당 배경색에 맞는 텍스트 색상 결정
                    page_text_color = get_text_color_for_background(page_bg_color)

                    print(f"    📍 페이지 {i+1} 배경색: RGB{page_bg_color}, 텍스트: {page_text_color}")

                    # 본문 페이지 생성
                    card_base64 = builder.build_content_page(
                        bg_color=page_bg_color,
                        title=page['title'],
                        content_lines=page.get('content', ["• 내용이 없습니다"]),
                        page_num=i + 1,
                        text_color=page_text_color  # 페이지별 동적 텍스트 색상
                    )
                final_cards.append(card_base64)

            print(f"  ✅ 카드 {i+1} 완성")

        result_log = f"\n{'='*80}\n✅ {len(final_cards)}장의 AI 카드뉴스 생성 완료!\n   📄 페이지: {len(final_cards)}장\n   🎨 배경색: RGB{final_bg_color}\n   📝 텍스트: {text_color}\n   🔤 폰트: {FONT_PAIRS.get(font_pair, {}).get('korean', 'Pretendard')}\n{'='*80}\n"
        print(result_log)
        cardnews_logger.info(result_log)

        # ==================== DB 저장 로직 ====================
        session_id = None
        card_image_urls = []

        if saveToDb:
            try:
                cardnews_logger.info(f"💾 DB 저장 시작: user_id={current_user.id}")
                print(f"\n💾 DB 저장 시작...")

                # 1. ContentGenerationSession 생성
                first_page_title = pages[0].get('title', prompt[:50]) if pages else prompt[:50]
                session = ContentGenerationSession(
                    user_id=current_user.id,
                    topic=prompt,
                    content_type="cardnews",
                    style=selected_style,
                    selected_platforms=["cardnews"],
                    analysis_data=analysis,
                    status="generated"
                )
                db.add(session)
                db.flush()  # session.id 생성을 위해 flush
                session_id = session.id
                cardnews_logger.info(f"✅ 세션 생성: session_id={session_id}")

                # 2. Supabase Storage에 이미지 업로드
                print(f"  ☁️ Supabase Storage 업로드 중...")
                for i, card_base64 in enumerate(final_cards):
                    try:
                        image_url = await upload_cardnews_image_to_supabase(
                            card_base64,
                            current_user.id,
                            session_id,
                            i + 1
                        )
                        card_image_urls.append(image_url)
                        print(f"    ✅ 페이지 {i+1} 업로드 완료")
                    except Exception as upload_error:
                        cardnews_logger.error(f"페이지 {i+1} 업로드 실패: {upload_error}")
                        # 업로드 실패 시 Base64를 그대로 저장하지 않고 빈 URL 추가
                        card_image_urls.append(None)

                # 3. GeneratedCardnewsContent 저장
                design_settings_data = {
                    "bg_color": list(final_bg_color) if isinstance(final_bg_color, tuple) else final_bg_color,
                    "text_color": text_color,
                    "font_korean": FONT_PAIRS.get(font_pair, {}).get('korean', 'Pretendard'),
                    "font_english": FONT_PAIRS.get(font_pair, {}).get('english', 'Inter'),
                    "style": selected_style
                }

                pages_data = [
                    {
                        "page": p['page'],
                        "title": p['title'],
                        "subtitle": p.get('subtitle', ''),
                        "content": p.get('content', []),
                        "layout": p.get('layout', 'center')
                    }
                    for p in pages
                ]

                cardnews_content = GeneratedCardnewsContent(
                    session_id=session_id,
                    user_id=current_user.id,
                    title=first_page_title,
                    prompt=prompt,
                    purpose=purpose,
                    page_count=len(final_cards),
                    card_image_urls=card_image_urls,
                    analysis_data=analysis,
                    pages_data=pages_data,
                    design_settings=design_settings_data,
                    quality_score=quality_report.get('overall_score') if quality_report else None,
                    score=int(quality_report.get('overall_score', 0) * 10) if quality_report and quality_report.get('overall_score') else None
                )
                db.add(cardnews_content)
                db.commit()

                cardnews_logger.info(f"✅ DB 저장 완료: session_id={session_id}, cardnews_id={cardnews_content.id}")
                print(f"  ✅ DB 저장 완료: session_id={session_id}")

            except Exception as db_error:
                cardnews_logger.error(f"DB 저장 실패: {db_error}")
                print(f"  ❌ DB 저장 실패: {db_error}")
                db.rollback()
                # DB 저장 실패해도 생성된 카드뉴스는 반환

        return {
            "success": True,
            "cards": final_cards,
            "card_image_urls": card_image_urls if saveToDb else [],
            "session_id": session_id,
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


