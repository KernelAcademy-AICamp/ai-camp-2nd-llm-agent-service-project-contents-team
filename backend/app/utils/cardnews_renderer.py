# -*- coding: utf-8 -*-
"""
🖼️ 카드뉴스 렌더링 유틸리티
개선된 템플릿 시스템을 실제 이미지로 렌더링
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import Tuple, List, Optional
import math

# 기본 상수
CARD_WIDTH = 1080
CARD_HEIGHT = 1080
RENDER_SCALE = 2  # 고해상도 렌더링


class GradientGenerator:
    """다양한 그라데이션 생성"""
    
    @staticmethod
    def linear(
        width: int, height: int,
        start_color: Tuple[int, int, int],
        end_color: Tuple[int, int, int],
        direction: str = "vertical"
    ) -> Image.Image:
        """선형 그라데이션"""
        img = Image.new('RGB', (width, height))
        
        for i in range(height if direction == "vertical" else width):
            ratio = i / (height if direction == "vertical" else width)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            
            if direction == "vertical":
                for j in range(width):
                    img.putpixel((j, i), (r, g, b))
            else:
                for j in range(height):
                    img.putpixel((i, j), (r, g, b))
        
        return img
    
    @staticmethod
    def diagonal(
        width: int, height: int,
        start_color: Tuple[int, int, int],
        end_color: Tuple[int, int, int]
    ) -> Image.Image:
        """대각선 그라데이션"""
        img = Image.new('RGB', (width, height))
        max_dist = math.sqrt(width**2 + height**2)
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt(x**2 + y**2)
                ratio = dist / max_dist
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    @staticmethod
    def radial(
        width: int, height: int,
        center_color: Tuple[int, int, int],
        edge_color: Tuple[int, int, int],
        center: Tuple[float, float] = (0.5, 0.5)
    ) -> Image.Image:
        """방사형 그라데이션"""
        img = Image.new('RGB', (width, height))
        cx, cy = int(width * center[0]), int(height * center[1])
        max_dist = math.sqrt(max(cx, width-cx)**2 + max(cy, height-cy)**2)
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                ratio = min(1.0, dist / max_dist)
                r = int(center_color[0] + (edge_color[0] - center_color[0]) * ratio)
                g = int(center_color[1] + (edge_color[1] - center_color[1]) * ratio)
                b = int(center_color[2] + (edge_color[2] - center_color[2]) * ratio)
                img.putpixel((x, y), (r, g, b))
        
        return img
    
    @staticmethod
    def multi_color(
        width: int, height: int,
        colors: List[Tuple[int, int, int]],
        direction: str = "vertical"
    ) -> Image.Image:
        """다중 색상 그라데이션"""
        if len(colors) < 2:
            return Image.new('RGB', (width, height), colors[0] if colors else (255, 255, 255))
        
        img = Image.new('RGB', (width, height))
        num_segments = len(colors) - 1
        segment_size = (height if direction == "vertical" else width) // num_segments
        
        for seg in range(num_segments):
            start_color = colors[seg]
            end_color = colors[seg + 1]
            start_pos = seg * segment_size
            end_pos = (seg + 1) * segment_size if seg < num_segments - 1 else (height if direction == "vertical" else width)
            
            for i in range(start_pos, end_pos):
                ratio = (i - start_pos) / (end_pos - start_pos) if end_pos > start_pos else 0
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                
                if direction == "vertical":
                    for j in range(width):
                        img.putpixel((j, i), (r, g, b))
                else:
                    for j in range(height):
                        img.putpixel((i, j), (r, g, b))
        
        return img


class EffectsProcessor:
    """시각 효과 처리"""
    
    @staticmethod
    def apply_vignette(img: Image.Image, strength: float = 0.5) -> Image.Image:
        """비네트 효과"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        width, height = img.size
        cx, cy = width // 2, height // 2
        max_dist = math.sqrt(cx**2 + cy**2)
        
        vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                factor = min(1.0, (dist / max_dist) ** 1.5 * strength)
                alpha = int(255 * factor * 0.7)
                vignette.putpixel((x, y), (0, 0, 0, alpha))
        
        return Image.alpha_composite(img, vignette)
    
    @staticmethod
    def apply_blur(img: Image.Image, radius: int = 5) -> Image.Image:
        """가우시안 블러"""
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    @staticmethod
    def apply_overlay(
        img: Image.Image,
        color: Tuple[int, int, int] = (0, 0, 0),
        opacity: float = 0.3
    ) -> Image.Image:
        """색상 오버레이"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        overlay = Image.new('RGBA', img.size, (*color, int(255 * opacity)))
        return Image.alpha_composite(img, overlay)
    
    @staticmethod
    def apply_grain(img: Image.Image, intensity: float = 0.1) -> Image.Image:
        """노이즈/그레인 효과"""
        import random
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = img.load()
        width, height = img.size
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                noise = int(random.uniform(-1, 1) * 255 * intensity)
                r = max(0, min(255, r + noise))
                g = max(0, min(255, g + noise))
                b = max(0, min(255, b + noise))
                pixels[x, y] = (r, g, b)
        
        return img


class CardRenderer:
    """카드 렌더링 (글래스모피즘, 플로팅 등)"""
    
    @staticmethod
    def create_glass_card(
        width: int, height: int,
        corner_radius: int = 20,
        blur_radius: int = 15,
        opacity: float = 0.2,
        border_color: Tuple[int, int, int, int] = (255, 255, 255, 80)
    ) -> Image.Image:
        """글래스모피즘 카드"""
        card = Image.new('RGBA', (width, height), (255, 255, 255, int(255 * opacity)))
        
        # 모서리 라운딩을 위한 마스크
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, width-1, height-1],
            radius=corner_radius,
            fill=255
        )
        
        # 마스크 적용
        card.putalpha(mask)
        
        # 테두리 추가
        draw = ImageDraw.Draw(card, 'RGBA')
        draw.rounded_rectangle(
            [0, 0, width-1, height-1],
            radius=corner_radius,
            outline=border_color,
            width=1
        )
        
        return card
    
    @staticmethod
    def create_floating_card(
        width: int, height: int,
        corner_radius: int = 16,
        shadow_blur: int = 30,
        shadow_opacity: float = 0.2,
        card_color: Tuple[int, int, int] = (255, 255, 255),
        card_opacity: float = 0.9
    ) -> Tuple[Image.Image, Image.Image]:
        """플로팅 카드 (카드 + 그림자)"""
        # 그림자 생성
        shadow_size = shadow_blur * 2
        shadow = Image.new('RGBA', (width + shadow_size * 2, height + shadow_size * 2), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [shadow_size, shadow_size, width + shadow_size, height + shadow_size],
            radius=corner_radius,
            fill=(0, 0, 0, int(255 * shadow_opacity))
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        
        # 카드 생성
        card = Image.new('RGBA', (width, height), (*card_color, int(255 * card_opacity)))
        
        # 모서리 라운딩
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, width-1, height-1],
            radius=corner_radius,
            fill=255
        )
        card.putalpha(mask)
        
        return card, shadow


class DecorationRenderer:
    """장식 요소 렌더링"""
    
    @staticmethod
    def draw_line_accent(
        draw: ImageDraw.Draw,
        position: str,
        color: Tuple[int, int, int],
        thickness: int,
        length: int,
        card_width: int,
        card_height: int
    ):
        """라인 악센트"""
        if position == "bottom_center":
            x1 = (card_width - length) // 2
            x2 = x1 + length
            y = card_height - 80
            draw.line([(x1, y), (x2, y)], fill=color, width=thickness)
        elif position == "top_center":
            x1 = (card_width - length) // 2
            x2 = x1 + length
            y = 80
            draw.line([(x1, y), (x2, y)], fill=color, width=thickness)
    
    @staticmethod
    def draw_corner_brackets(
        draw: ImageDraw.Draw,
        color: Tuple[int, int, int],
        thickness: int,
        size: int,
        margin: int,
        card_width: int,
        card_height: int
    ):
        """코너 브라켓"""
        # 좌상단
        draw.line([(margin, margin), (margin + size, margin)], fill=color, width=thickness)
        draw.line([(margin, margin), (margin, margin + size)], fill=color, width=thickness)
        
        # 우상단
        draw.line([(card_width - margin - size, margin), (card_width - margin, margin)], fill=color, width=thickness)
        draw.line([(card_width - margin, margin), (card_width - margin, margin + size)], fill=color, width=thickness)
        
        # 좌하단
        draw.line([(margin, card_height - margin), (margin + size, card_height - margin)], fill=color, width=thickness)
        draw.line([(margin, card_height - margin - size), (margin, card_height - margin)], fill=color, width=thickness)
        
        # 우하단
        draw.line([(card_width - margin - size, card_height - margin), (card_width - margin, card_height - margin)], fill=color, width=thickness)
        draw.line([(card_width - margin, card_height - margin - size), (card_width - margin, card_height - margin)], fill=color, width=thickness)
    
    @staticmethod
    def draw_rounded_border(
        draw: ImageDraw.Draw,
        color: Tuple[int, int, int],
        thickness: int,
        radius: int,
        margin: int,
        card_width: int,
        card_height: int
    ):
        """둥근 테두리"""
        draw.rounded_rectangle(
            [margin, margin, card_width - margin, card_height - margin],
            radius=radius,
            outline=color,
            width=thickness
        )
    
    @staticmethod
    def draw_simple_frame(
        draw: ImageDraw.Draw,
        color: Tuple[int, int, int],
        thickness: int,
        margin: int,
        card_width: int,
        card_height: int
    ):
        """심플 프레임"""
        draw.rectangle(
            [margin, margin, card_width - margin, card_height - margin],
            outline=color,
            width=thickness
        )
    
    @staticmethod
    def draw_circle_accent(
        img: Image.Image,
        position: str,
        color: Tuple[int, int, int],
        size: int,
        opacity: float
    ):
        """원형 악센트"""
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')
        
        width, height = img.size
        positions = {
            "top_right": (width - size // 2, size // 2),
            "top_left": (size // 2, size // 2),
            "bottom_right": (width - size // 2, height - size // 2),
            "bottom_left": (size // 2, height - size // 2),
            "center": (width // 2, height // 2)
        }
        
        cx, cy = positions.get(position, (width - size // 2, size // 2))
        draw.ellipse(
            [cx - size, cy - size, cx + size, cy + size],
            fill=(*color, int(255 * opacity))
        )
        
        return Image.alpha_composite(img.convert('RGBA'), overlay)


class TextEffects:
    """텍스트 효과"""
    
    @staticmethod
    def create_text_shadow(
        text: str,
        font,
        shadow_type: str,
        shadow_color: Tuple[int, int, int],
        intensity: float,
        blur_radius: int = 6,
        offset: Tuple[int, int] = (4, 4)
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """텍스트 그림자 생성"""
        # 임시 이미지로 텍스트 크기 측정
        temp = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 그림자용 이미지 (패딩 포함)
        padding = blur_radius * 3
        shadow_img = Image.new('RGBA', (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        
        alpha = int(255 * intensity)
        shadow_draw.text((padding, padding), text, font=font, fill=(*shadow_color, alpha))
        
        if shadow_type in ["soft", "soft_glow", "gaussian"]:
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        elif shadow_type == "neon":
            # 네온 효과: 여러 번 블러 + 밝은 색상
            for _ in range(3):
                shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=blur_radius // 2))
        elif shadow_type == "drop":
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=blur_radius // 2))
        
        return shadow_img, (padding - offset[0], padding - offset[1])


# ==================== 통합 렌더러 ====================

class CardNewsRenderer:
    """카드뉴스 통합 렌더러"""
    
    def __init__(self, template: dict, palette: dict, layout: dict):
        self.template = template
        self.palette = palette
        self.layout = layout
        self.width = CARD_WIDTH * RENDER_SCALE
        self.height = CARD_HEIGHT * RENDER_SCALE
    
    def create_background(self) -> Image.Image:
        """배경 생성"""
        bg_style = self.template["background_style"]
        bg_type = bg_style.get("type", "solid")
        
        if bg_type == "solid":
            return Image.new('RGB', (self.width, self.height), self.palette["primary"])
        
        elif bg_type == "gradient":
            gradients = self.palette.get("gradient", [])
            if gradients:
                start, end = gradients[0]
                return GradientGenerator.linear(self.width, self.height, start, end, "vertical")
            return Image.new('RGB', (self.width, self.height), self.palette["primary"])
        
        elif bg_type == "multi_gradient":
            colors = [self.palette["primary"], self.palette["secondary"]]
            if self.palette.get("accent"):
                colors.append(self.palette["accent"])
            direction = bg_style.get("direction", "vertical")
            if direction == "diagonal":
                return GradientGenerator.diagonal(self.width, self.height, colors[0], colors[-1])
            return GradientGenerator.multi_color(self.width, self.height, colors, direction)
        
        elif bg_type == "radial":
            return GradientGenerator.radial(
                self.width, self.height,
                self.palette["primary"],
                self.palette["secondary"]
            )
        
        return Image.new('RGB', (self.width, self.height), self.palette["primary"])
    
    def apply_effects(self, img: Image.Image) -> Image.Image:
        """효과 적용"""
        bg_style = self.template["background_style"]
        
        # 블러
        if bg_style.get("blur_radius", 0) > 0:
            img = EffectsProcessor.apply_blur(img, bg_style["blur_radius"])
        
        # 오버레이
        if bg_style.get("overlay_opacity", 0) > 0:
            overlay_color = (0, 0, 0) if self.palette.get("overlay_style") == "dark" else (255, 255, 255)
            img = EffectsProcessor.apply_overlay(img, overlay_color, bg_style["overlay_opacity"])
        
        # 비네트
        if bg_style.get("use_vignette", False):
            img = EffectsProcessor.apply_vignette(img, 0.5)
        
        # 그레인
        if bg_style.get("grain", False):
            img = EffectsProcessor.apply_grain(img, 0.05)
        
        return img
    
    def add_card_layer(self, img: Image.Image) -> Image.Image:
        """카드 레이어 추가"""
        card_style = self.template["card_style"]
        
        if not card_style.get("use_card", False):
            return img
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 카드 크기 계산
        margin = int(self.width * self.layout.get("padding_ratio", 0.08))
        card_width = self.width - margin * 2
        card_height = self.height - margin * 2
        
        if card_style.get("glass_effect", False):
            card = CardRenderer.create_glass_card(
                card_width, card_height,
                corner_radius=int(card_style.get("corner_radius", 20) * RENDER_SCALE),
                blur_radius=card_style.get("glass_blur", 15),
                opacity=card_style.get("glass_opacity", 0.2)
            )
            img.paste(card, (margin, margin), card)
        else:
            card, shadow = CardRenderer.create_floating_card(
                card_width, card_height,
                corner_radius=int(card_style.get("corner_radius", 16) * RENDER_SCALE),
                shadow_blur=int(card_style.get("shadow_blur", 30) * RENDER_SCALE),
                shadow_opacity=card_style.get("shadow_opacity", 0.2),
                card_color=card_style.get("card_color", (255, 255, 255)),
                card_opacity=card_style.get("card_opacity", 0.9)
            )
            
            # 그림자 먼저
            shadow_offset = int(card_style.get("shadow_blur", 30) * RENDER_SCALE)
            img.paste(shadow, (margin - shadow_offset, margin - shadow_offset + 10), shadow)
            # 카드
            img.paste(card, (margin, margin), card)
        
        return img
    
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
        color = decoration.get("color", self.palette["accent"])
        if color == "accent":
            color = self.palette["accent"]
        
        margin = int(self.width * 0.06)
        
        if dec_type == "line_accent":
            DecorationRenderer.draw_line_accent(
                draw,
                decoration.get("position", "bottom_center"),
                color,
                int(decoration.get("thickness", 3) * RENDER_SCALE),
                int(decoration.get("length", 60) * RENDER_SCALE),
                self.width, self.height
            )
        
        elif dec_type == "corner_brackets":
            DecorationRenderer.draw_corner_brackets(
                draw, color,
                int(decoration.get("thickness", 2) * RENDER_SCALE),
                int(decoration.get("size", 30) * RENDER_SCALE),
                margin, self.width, self.height
            )
        
        elif dec_type == "rounded_border":
            DecorationRenderer.draw_rounded_border(
                draw, color,
                int(decoration.get("thickness", 2) * RENDER_SCALE),
                int(decoration.get("radius", 32) * RENDER_SCALE),
                margin, self.width, self.height
            )
        
        elif dec_type == "simple_frame":
            DecorationRenderer.draw_simple_frame(
                draw, color,
                int(decoration.get("thickness", 1) * RENDER_SCALE),
                int(decoration.get("margin", 30) * RENDER_SCALE),
                self.width, self.height
            )
        
        elif dec_type == "circle_accent":
            img = DecorationRenderer.draw_circle_accent(
                img,
                decoration.get("position", "top_right"),
                color,
                int(decoration.get("size", 80) * RENDER_SCALE),
                decoration.get("opacity", 0.3)
            )
        
        return img
    
    def render(self) -> Image.Image:
        """최종 렌더링"""
        # 1. 배경 생성
        img = self.create_background()
        
        # 2. 효과 적용
        img = self.apply_effects(img)
        
        # 3. 카드 레이어
        img = self.add_card_layer(img)
        
        # 4. 장식 요소
        img = self.add_decorations(img)
        
        # 5. 최종 크기 조정
        img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
        
        return img


# ==================== 테스트 ====================

if __name__ == "__main__":
    from cardnews_templates_improved import (
        DESIGN_TEMPLATES, COLOR_PALETTES, LAYOUT_STYLES,
        get_template, get_palette, get_layout
    )
    
    print("🖼️ 카드뉴스 렌더러 테스트")
    print("=" * 50)
    
    # 테스트할 템플릿들
    test_templates = ["minimal_white", "pastel_pink", "neon_cyber", "sunset_dream"]
    
    for template_id in test_templates:
        template = get_template(template_id)
        if not template:
            continue
        
        palette = get_palette(template["palette"])
        layout = get_layout(template["layout"])
        
        renderer = CardNewsRenderer(template, palette, layout)
        img = renderer.render()
        
        filename = f"test_{template_id}.png"
        img.save(filename)
        print(f"✅ {template['name']} → {filename}")
    
    print("\n테스트 완료!")
