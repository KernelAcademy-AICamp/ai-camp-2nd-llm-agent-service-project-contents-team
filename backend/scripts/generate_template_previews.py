# -*- coding: utf-8 -*-
"""
템플릿 미리보기 이미지 생성 스크립트
각 템플릿별로 표지(cover)와 내용(content) 페이지 이미지를 생성합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from PIL import Image, ImageDraw, ImageFilter
from app.utils.cardnews_templates_improved import (
    DESIGN_TEMPLATES,
    COLOR_PALETTES,
    LAYOUT_STYLES,
    get_template,
    get_palette,
    get_layout
)
from app.utils.cardnews_renderer import (
    CardNewsRenderer,
    GradientGenerator,
    EffectsProcessor,
    CARD_WIDTH,
    CARD_HEIGHT,
    RENDER_SCALE
)

# 출력 디렉토리
OUTPUT_DIR = BACKEND_DIR / "static" / "template_previews"

# 샘플 텍스트
SAMPLE_COVER = {
    "title": "새로운 시작",
    "subtitle": "특별한 프로모션이 시작됩니다"
}

SAMPLE_CONTENT = {
    "title": "핵심 포인트",
    "bullets": [
        "첫 번째 핵심 내용입니다",
        "두 번째 핵심 내용입니다",
        "세 번째 핵심 내용입니다"
    ]
}

# 미리보기 이미지 크기 (작게 생성)
PREVIEW_WIDTH = 400
PREVIEW_HEIGHT = 400


class PreviewGenerator:
    """템플릿 미리보기 이미지 생성기"""

    def __init__(self, template_id: str):
        self.template_id = template_id
        self.template = get_template(template_id)
        self.palette = get_palette(self.template.get("palette", "clean_white"))
        self.layout = get_layout(self.template.get("layout", "center"))

        # 렌더링 크기
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT

    def load_font(self, size: int, weight: str = "bold"):
        """폰트 로드"""
        from PIL import ImageFont

        # 시스템 폰트 경로 (macOS)
        font_paths = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/NanumGothicBold.ttf",
            "/Library/Fonts/NanumGothic.ttf",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue

        # 기본 폰트
        return ImageFont.load_default()

    def create_background(self) -> Image.Image:
        """배경 이미지 생성"""
        bg_style = self.template.get("background_style", {})
        bg_type = bg_style.get("type", "solid")

        if bg_type == "solid":
            return Image.new('RGB', (self.width, self.height), self.palette["primary"])

        elif bg_type == "gradient":
            gradients = self.palette.get("gradient", [])
            if gradients:
                start, end = gradients[0]
                return GradientGenerator.linear(self.width, self.height, start, end, "vertical")
            return Image.new('RGB', (self.width, self.height), self.palette["primary"])

        return Image.new('RGB', (self.width, self.height), self.palette["primary"])

    def apply_effects(self, img: Image.Image) -> Image.Image:
        """효과 적용"""
        bg_style = self.template.get("background_style", {})

        # 비네트 효과
        if bg_style.get("use_vignette", False):
            img = EffectsProcessor.apply_vignette(img, 0.4)

        return img

    def add_card_layer(self, img: Image.Image) -> Image.Image:
        """카드 레이어 추가 (반투명 박스)"""
        card_style = self.template.get("card_style", {})

        if not card_style.get("use_card", False):
            return img

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 카드 영역 계산
        padding = int(self.width * 0.1)
        card_width = self.width - padding * 2
        card_height = self.height - padding * 2

        # 반투명 카드 생성
        card_color = card_style.get("card_color", (255, 255, 255))
        card_opacity = int(card_style.get("card_opacity", 0.7) * 255)
        corner_radius = card_style.get("corner_radius", 20)

        card = Image.new('RGBA', (card_width, card_height), (*card_color, card_opacity))

        # 라운드 마스크 적용
        mask = Image.new('L', (card_width, card_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), (card_width, card_height)],
            radius=corner_radius,
            fill=255
        )
        card.putalpha(mask)

        img.paste(card, (padding, padding), card)

        return img

    def draw_text_centered(self, draw, text: str, y: int, font, color, max_width: int = None):
        """중앙 정렬 텍스트 그리기"""
        if max_width is None:
            max_width = self.width - 160

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2

        # 텍스트 그림자 (어두운 배경용)
        overlay_style = self.palette.get("overlay_style", "light")
        if overlay_style == "dark" or self._is_dark_background():
            shadow_color = (0, 0, 0, 100)
            draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)

        draw.text((x, y), text, font=font, fill=color)

    def _is_dark_background(self) -> bool:
        """배경이 어두운지 확인"""
        primary = self.palette.get("primary", (255, 255, 255))
        brightness = (primary[0] * 299 + primary[1] * 587 + primary[2] * 114) / 1000
        return brightness < 128

    def generate_cover(self) -> Image.Image:
        """표지 이미지 생성"""
        # 배경 생성
        img = self.create_background()
        img = self.apply_effects(img)
        img = self.add_card_layer(img)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        draw = ImageDraw.Draw(img)

        # 텍스트 스타일
        text_style = self.template.get("text_style", {})
        title_size = int(72 * text_style.get("title_size_ratio", 1.0))
        subtitle_size = int(36 * text_style.get("content_size_ratio", 0.9))

        title_font = self.load_font(title_size, text_style.get("title_weight", "bold"))
        subtitle_font = self.load_font(subtitle_size, text_style.get("content_weight", "regular"))

        # 텍스트 색상
        text_color = self.palette.get("text_primary", (255, 255, 255))
        text_secondary = self.palette.get("text_secondary", (200, 200, 200))

        # 레이아웃에 따른 Y 위치
        layout_pos = self.layout.get("title_y_ratio", 0.35)
        title_y = int(self.height * layout_pos)
        subtitle_y = title_y + title_size + 30

        # 텍스트 그리기
        self.draw_text_centered(draw, SAMPLE_COVER["title"], title_y, title_font, text_color)
        self.draw_text_centered(draw, SAMPLE_COVER["subtitle"], subtitle_y, subtitle_font, text_secondary)

        # 장식 추가
        img = self.add_decorations(img)

        # 리사이즈
        img = img.convert('RGB')
        img = img.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS)

        return img

    def generate_content(self) -> Image.Image:
        """내용 페이지 이미지 생성"""
        # 배경 생성 (색조 변경)
        img = self.create_harmonic_background()
        img = self.apply_effects(img)
        img = self.add_card_layer(img)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        draw = ImageDraw.Draw(img)

        # 텍스트 스타일
        text_style = self.template.get("text_style", {})
        title_size = int(48 * text_style.get("title_size_ratio", 1.0))
        bullet_size = int(32 * text_style.get("content_size_ratio", 0.9))

        title_font = self.load_font(title_size, text_style.get("title_weight", "bold"))
        bullet_font = self.load_font(bullet_size, text_style.get("content_weight", "regular"))

        # 텍스트 색상
        text_color = self.palette.get("text_primary", (255, 255, 255))
        text_secondary = self.palette.get("text_secondary", (200, 200, 200))

        # 제목
        title_y = int(self.height * 0.25)
        self.draw_text_centered(draw, SAMPLE_CONTENT["title"], title_y, title_font, text_color)

        # 불릿 리스트
        bullet_start_y = title_y + title_size + 60
        line_height = bullet_size + 25

        for i, bullet in enumerate(SAMPLE_CONTENT["bullets"]):
            y = bullet_start_y + i * line_height
            bullet_text = f"• {bullet}"

            # 좌측 정렬 (약간의 패딩)
            x = 120

            # 그림자
            if self._is_dark_background():
                draw.text((x + 2, y + 2), bullet_text, font=bullet_font, fill=(0, 0, 0, 100))

            draw.text((x, y), bullet_text, font=bullet_font, fill=text_secondary)

        # 장식 추가
        img = self.add_decorations(img)

        # 리사이즈
        img = img.convert('RGB')
        img = img.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.Resampling.LANCZOS)

        return img

    def create_harmonic_background(self) -> Image.Image:
        """조화로운 색상의 배경 생성 (내용 페이지용)"""
        primary = self.palette.get("primary", (255, 255, 255))
        secondary = self.palette.get("secondary", primary)

        # 색상을 약간 변형
        def shift_hue(rgb, shift=20):
            r, g, b = rgb
            # 간단한 색조 변환
            return (
                min(255, max(0, r + shift)),
                min(255, max(0, g - shift // 2)),
                min(255, max(0, b + shift // 3))
            )

        bg_style = self.template.get("background_style", {})
        bg_type = bg_style.get("type", "solid")

        shifted_primary = shift_hue(primary, 15)

        if bg_type == "gradient":
            return GradientGenerator.linear(
                self.width, self.height,
                shifted_primary,
                secondary,
                "vertical"
            )

        return Image.new('RGB', (self.width, self.height), shifted_primary)

    def add_decorations(self, img: Image.Image) -> Image.Image:
        """장식 요소 추가"""
        decoration = self.template.get("decoration", {})
        if not decoration:
            return img

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        draw = ImageDraw.Draw(img, 'RGBA')
        dec_type = decoration.get("type", "")

        # 색상 처리
        color = decoration.get("color", self.palette.get("accent", (100, 100, 100)))
        if color == "accent":
            color = self.palette.get("accent", (100, 100, 100))

        margin = int(self.width * 0.06)

        if dec_type == "line_accent":
            # 하단 중앙 라인
            line_length = decoration.get("length", 60)
            thickness = decoration.get("thickness", 3)
            x1 = (self.width - line_length) // 2
            x2 = x1 + line_length
            y = self.height - margin - 50
            draw.rectangle([(x1, y), (x2, y + thickness)], fill=color)

        elif dec_type == "corner_brackets":
            # 코너 브라켓
            size = decoration.get("size", 30)
            thickness = decoration.get("thickness", 2)

            # 좌상단
            draw.line([(margin, margin), (margin + size, margin)], fill=color, width=thickness)
            draw.line([(margin, margin), (margin, margin + size)], fill=color, width=thickness)

            # 우상단
            draw.line([(self.width - margin - size, margin), (self.width - margin, margin)], fill=color, width=thickness)
            draw.line([(self.width - margin, margin), (self.width - margin, margin + size)], fill=color, width=thickness)

            # 좌하단
            draw.line([(margin, self.height - margin), (margin + size, self.height - margin)], fill=color, width=thickness)
            draw.line([(margin, self.height - margin - size), (margin, self.height - margin)], fill=color, width=thickness)

            # 우하단
            draw.line([(self.width - margin - size, self.height - margin), (self.width - margin, self.height - margin)], fill=color, width=thickness)
            draw.line([(self.width - margin, self.height - margin - size), (self.width - margin, self.height - margin)], fill=color, width=thickness)

        elif dec_type == "rounded_border":
            # 라운드 테두리
            thickness = decoration.get("thickness", 2)
            radius = decoration.get("radius", 32)
            draw.rounded_rectangle(
                [(margin, margin), (self.width - margin, self.height - margin)],
                radius=radius,
                outline=color,
                width=thickness
            )

        elif dec_type == "simple_frame":
            # 단순 프레임
            thickness = decoration.get("thickness", 1)
            frame_margin = decoration.get("margin", 30)
            draw.rectangle(
                [(frame_margin, frame_margin), (self.width - frame_margin, self.height - frame_margin)],
                outline=color,
                width=thickness
            )

        return img


def generate_all_previews():
    """모든 템플릿의 미리보기 이미지 생성"""
    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("템플릿 미리보기 이미지 생성 시작")
    print("=" * 60)
    print(f"총 템플릿 수: {len(DESIGN_TEMPLATES)}")
    print(f"출력 디렉토리: {OUTPUT_DIR}")
    print()

    success_count = 0
    error_count = 0

    for template_id, template in DESIGN_TEMPLATES.items():
        try:
            print(f"생성 중: {template_id} ({template['name']})")

            generator = PreviewGenerator(template_id)

            # 표지 이미지 생성
            cover_img = generator.generate_cover()
            cover_path = OUTPUT_DIR / f"{template_id}_cover.png"
            cover_img.save(cover_path, "PNG", optimize=True)

            # 내용 페이지 이미지 생성
            content_img = generator.generate_content()
            content_path = OUTPUT_DIR / f"{template_id}_content.png"
            content_img.save(content_path, "PNG", optimize=True)

            print(f"  ✅ 완료: {cover_path.name}, {content_path.name}")
            success_count += 1

        except Exception as e:
            print(f"  ❌ 오류: {template_id} - {str(e)}")
            error_count += 1

    print()
    print("=" * 60)
    print(f"생성 완료: {success_count}개 성공, {error_count}개 실패")
    print(f"총 이미지: {success_count * 2}장")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_previews()
