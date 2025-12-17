# -*- coding: utf-8 -*-
"""
🎨 개선된 카드뉴스 디자인 템플릿 시스템
2024-2025 디자인 트렌드 반영

트렌드 조사 기반:
- Glassmorphism (투명/블러 효과)
- 그라데이션 오버레이
- 대담한 타이포그래피
- 레트로/미래주의
- 매거진/에디토리얼 스타일
- 파스텔 & 뉴트럴 톤
"""

# ==================== 색상 팔레트 시스템 ====================

COLOR_PALETTES = {
    # 🎨 모던 & 미니멀
    "clean_white": {
        "name": "클린 화이트",
        "description": "깔끔하고 전문적인 화이트 베이스",
        "primary": (255, 255, 255),
        "secondary": (245, 245, 247),
        "accent": (0, 0, 0),
        "text_primary": (17, 17, 17),
        "text_secondary": (102, 102, 102),
        "gradient": [((255, 255, 255), (240, 240, 245))],
        "overlay_style": "light"
    },
    "pure_black": {
        "name": "퓨어 블랙",
        "description": "고급스러운 블랙 베이스",
        "primary": (17, 17, 17),
        "secondary": (34, 34, 34),
        "accent": (255, 255, 255),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 180, 180),
        "gradient": [((17, 17, 17), (40, 40, 40))],
        "overlay_style": "dark"
    },
    
    # 🌸 파스텔 톤
    "soft_pink": {
        "name": "소프트 핑크",
        "description": "부드럽고 따뜻한 핑크 파스텔",
        "primary": (255, 228, 230),
        "secondary": (255, 241, 242),
        "accent": (219, 112, 147),
        "text_primary": (80, 50, 60),
        "text_secondary": (150, 100, 120),
        "gradient": [((255, 228, 230), (255, 241, 242)), ((255, 182, 193), (255, 228, 230))],
        "overlay_style": "light"
    },
    "mint_fresh": {
        "name": "민트 프레시",
        "description": "시원하고 상쾌한 민트",
        "primary": (200, 255, 243),
        "secondary": (224, 255, 248),
        "accent": (0, 180, 150),
        "text_primary": (30, 80, 70),
        "text_secondary": (80, 130, 120),
        "gradient": [((200, 255, 243), (176, 224, 230))],
        "overlay_style": "light"
    },
    "lavender_dream": {
        "name": "라벤더 드림",
        "description": "몽환적인 라벤더 톤",
        "primary": (230, 230, 250),
        "secondary": (245, 240, 255),
        "accent": (138, 43, 226),
        "text_primary": (60, 40, 90),
        "text_secondary": (120, 100, 150),
        "gradient": [((230, 230, 250), (255, 240, 245)), ((216, 191, 216), (230, 230, 250))],
        "overlay_style": "light"
    },
    "butter_cream": {
        "name": "버터크림",
        "description": "따뜻한 크림 베이지",
        "primary": (255, 253, 240),
        "secondary": (255, 248, 230),
        "accent": (200, 150, 80),
        "text_primary": (80, 60, 40),
        "text_secondary": (140, 120, 90),
        "gradient": [((255, 253, 240), (255, 245, 220))],
        "overlay_style": "light"
    },
    "sky_blue": {
        "name": "스카이 블루",
        "description": "맑고 청량한 하늘색",
        "primary": (225, 245, 255),
        "secondary": (240, 250, 255),
        "accent": (30, 144, 255),
        "text_primary": (30, 60, 90),
        "text_secondary": (80, 120, 160),
        "gradient": [((225, 245, 255), (200, 230, 255))],
        "overlay_style": "light"
    },
    
    # 🔥 비비드 & 볼드
    "electric_blue": {
        "name": "일렉트릭 블루",
        "description": "강렬한 네온 블루",
        "primary": (0, 102, 255),
        "secondary": (30, 144, 255),
        "accent": (0, 255, 255),
        "text_primary": (255, 255, 255),
        "text_secondary": (200, 230, 255),
        "gradient": [((0, 60, 150), (0, 102, 255)), ((0, 102, 255), (30, 200, 255))],
        "overlay_style": "dark"
    },
    "coral_energy": {
        "name": "코랄 에너지",
        "description": "활기찬 코랄 오렌지",
        "primary": (255, 127, 80),
        "secondary": (255, 160, 122),
        "accent": (255, 69, 0),
        "text_primary": (255, 255, 255),
        "text_secondary": (255, 230, 220),
        "gradient": [((255, 100, 50), (255, 150, 100)), ((255, 127, 80), (255, 99, 71))],
        "overlay_style": "dark"
    },
    "neon_purple": {
        "name": "네온 퍼플",
        "description": "사이버펑크 네온 퍼플",
        "primary": (138, 43, 226),
        "secondary": (186, 85, 211),
        "accent": (255, 0, 255),
        "text_primary": (255, 255, 255),
        "text_secondary": (230, 200, 255),
        "gradient": [((75, 0, 130), (138, 43, 226)), ((138, 43, 226), (186, 85, 211))],
        "overlay_style": "dark"
    },
    "lime_punch": {
        "name": "라임 펀치",
        "description": "신선한 라임 그린",
        "primary": (50, 205, 50),
        "secondary": (124, 252, 0),
        "accent": (0, 255, 127),
        "text_primary": (0, 50, 0),
        "text_secondary": (30, 80, 30),
        "gradient": [((34, 139, 34), (50, 205, 50)), ((50, 205, 50), (144, 238, 144))],
        "overlay_style": "light"
    },
    
    # 🌿 뉴트럴 & 어시
    "warm_sand": {
        "name": "웜 샌드",
        "description": "자연스러운 모래톤 베이지",
        "primary": (237, 224, 212),
        "secondary": (245, 235, 224),
        "accent": (160, 120, 80),
        "text_primary": (60, 50, 40),
        "text_secondary": (120, 100, 80),
        "gradient": [((237, 224, 212), (220, 200, 180))],
        "overlay_style": "light"
    },
    "forest_green": {
        "name": "포레스트 그린",
        "description": "깊은 숲의 녹색",
        "primary": (34, 85, 51),
        "secondary": (46, 125, 50),
        "accent": (144, 238, 144),
        "text_primary": (255, 255, 255),
        "text_secondary": (200, 230, 200),
        "gradient": [((20, 60, 40), (34, 85, 51)), ((34, 85, 51), (46, 125, 50))],
        "overlay_style": "dark"
    },
    "ocean_depth": {
        "name": "오션 뎁스",
        "description": "깊은 바다의 청록",
        "primary": (0, 77, 77),
        "secondary": (0, 102, 102),
        "accent": (64, 224, 208),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 220, 220),
        "gradient": [((0, 50, 60), (0, 77, 77)), ((0, 77, 77), (0, 128, 128))],
        "overlay_style": "dark"
    },
    "terracotta": {
        "name": "테라코타",
        "description": "따뜻한 흙빛 오렌지",
        "primary": (204, 119, 85),
        "secondary": (227, 168, 132),
        "accent": (139, 69, 19),
        "text_primary": (255, 255, 255),
        "text_secondary": (255, 235, 220),
        "gradient": [((160, 82, 45), (204, 119, 85))],
        "overlay_style": "dark"
    },
    
    # ✨ 프리미엄 & 럭셔리
    "gold_luxury": {
        "name": "골드 럭셔리",
        "description": "고급스러운 골드 & 블랙",
        "primary": (20, 20, 20),
        "secondary": (40, 40, 40),
        "accent": (212, 175, 55),
        "text_primary": (212, 175, 55),
        "text_secondary": (180, 150, 80),
        "gradient": [((10, 10, 10), (30, 30, 30))],
        "overlay_style": "dark"
    },
    "rose_gold": {
        "name": "로즈 골드",
        "description": "세련된 로즈 골드",
        "primary": (30, 25, 25),
        "secondary": (50, 40, 40),
        "accent": (183, 110, 121),
        "text_primary": (255, 230, 230),
        "text_secondary": (200, 160, 170),
        "gradient": [((20, 15, 15), (40, 30, 30))],
        "overlay_style": "dark"
    },
    "silver_frost": {
        "name": "실버 프로스트",
        "description": "차가운 실버 톤",
        "primary": (192, 192, 192),
        "secondary": (220, 220, 220),
        "accent": (105, 105, 105),
        "text_primary": (40, 40, 40),
        "text_secondary": (80, 80, 80),
        "gradient": [((180, 180, 185), (210, 210, 215))],
        "overlay_style": "light"
    },
    
    # 🌈 그라데이션 스페셜
    "sunset_glow": {
        "name": "선셋 글로우",
        "description": "따뜻한 노을 그라데이션",
        "primary": (255, 154, 86),
        "secondary": (255, 206, 86),
        "accent": (255, 94, 98),
        "text_primary": (255, 255, 255),
        "text_secondary": (255, 240, 230),
        "gradient": [((255, 94, 98), (255, 154, 86)), ((255, 154, 86), (255, 206, 86))],
        "overlay_style": "dark"
    },
    "aurora_borealis": {
        "name": "오로라",
        "description": "신비로운 오로라 그라데이션",
        "primary": (67, 206, 162),
        "secondary": (24, 90, 157),
        "accent": (147, 112, 219),
        "text_primary": (255, 255, 255),
        "text_secondary": (220, 240, 255),
        "gradient": [((24, 90, 157), (67, 206, 162)), ((67, 206, 162), (147, 112, 219))],
        "overlay_style": "dark"
    },
    "cotton_candy": {
        "name": "코튼캔디",
        "description": "달콤한 핑크-블루 그라데이션",
        "primary": (255, 182, 193),
        "secondary": (173, 216, 230),
        "accent": (255, 105, 180),
        "text_primary": (60, 40, 70),
        "text_secondary": (100, 80, 110),
        "gradient": [((255, 182, 193), (255, 218, 233)), ((173, 216, 230), (255, 182, 193))],
        "overlay_style": "light"
    },
}


# ==================== 레이아웃 스타일 ====================

LAYOUT_STYLES = {
    # 📐 기본 레이아웃
    "center": {
        "name": "중앙 정렬",
        "description": "제목과 내용이 중앙에 배치",
        "title_position": "center",
        "title_y_ratio": 0.35,
        "content_position": "center",
        "content_y_ratio": 0.55,
        "content_align": "center",
        "padding_ratio": 0.08
    },
    "top_heavy": {
        "name": "상단 강조",
        "description": "제목이 상단, 내용이 하단",
        "title_position": "top",
        "title_y_ratio": 0.15,
        "content_position": "center",
        "content_y_ratio": 0.50,
        "content_align": "center",
        "padding_ratio": 0.08
    },
    "bottom_heavy": {
        "name": "하단 강조",
        "description": "내용이 하단에 집중",
        "title_position": "center",
        "title_y_ratio": 0.25,
        "content_position": "bottom",
        "content_y_ratio": 0.65,
        "content_align": "center",
        "padding_ratio": 0.08
    },
    
    # 📰 매거진 스타일
    "magazine_left": {
        "name": "매거진 좌측",
        "description": "잡지 스타일 좌측 정렬",
        "title_position": "left",
        "title_y_ratio": 0.20,
        "content_position": "left",
        "content_y_ratio": 0.45,
        "content_align": "left",
        "padding_ratio": 0.10
    },
    "magazine_right": {
        "name": "매거진 우측",
        "description": "잡지 스타일 우측 정렬",
        "title_position": "right",
        "title_y_ratio": 0.20,
        "content_position": "right",
        "content_y_ratio": 0.45,
        "content_align": "right",
        "padding_ratio": 0.10
    },
    "editorial": {
        "name": "에디토리얼",
        "description": "편집 디자인 스타일",
        "title_position": "top_left",
        "title_y_ratio": 0.08,
        "content_position": "bottom_left",
        "content_y_ratio": 0.60,
        "content_align": "left",
        "padding_ratio": 0.06
    },
    
    # 🎯 포커스 레이아웃
    "title_focus": {
        "name": "제목 포커스",
        "description": "큰 제목 중심",
        "title_position": "center",
        "title_y_ratio": 0.40,
        "content_position": "bottom",
        "content_y_ratio": 0.75,
        "content_align": "center",
        "padding_ratio": 0.06,
        "title_scale": 1.3
    },
    "content_focus": {
        "name": "내용 포커스",
        "description": "내용 중심 레이아웃",
        "title_position": "top",
        "title_y_ratio": 0.12,
        "content_position": "center",
        "content_y_ratio": 0.45,
        "content_align": "left",
        "padding_ratio": 0.08,
        "content_scale": 1.1
    },
    
    # 🔲 분할 레이아웃
    "split_horizontal": {
        "name": "수평 분할",
        "description": "상하 분할 레이아웃",
        "title_position": "top_half",
        "title_y_ratio": 0.25,
        "content_position": "bottom_half",
        "content_y_ratio": 0.65,
        "content_align": "center",
        "padding_ratio": 0.08,
        "use_divider": True,
        "divider_y": 0.5
    },
    "split_diagonal": {
        "name": "대각선 분할",
        "description": "대각선 구도",
        "title_position": "top_left",
        "title_y_ratio": 0.20,
        "content_position": "bottom_right",
        "content_y_ratio": 0.60,
        "content_align": "right",
        "padding_ratio": 0.08,
        "diagonal": True
    },
    
    # 🃏 카드 스타일
    "card_float": {
        "name": "플로팅 카드",
        "description": "떠있는 카드 느낌",
        "title_position": "center",
        "title_y_ratio": 0.30,
        "content_position": "center",
        "content_y_ratio": 0.55,
        "content_align": "center",
        "padding_ratio": 0.12,
        "card_margin": 0.08,
        "card_radius": 24,
        "card_shadow": True
    },
    "glassmorphism": {
        "name": "글래스모피즘",
        "description": "투명한 유리 효과",
        "title_position": "center",
        "title_y_ratio": 0.30,
        "content_position": "center",
        "content_y_ratio": 0.55,
        "content_align": "center",
        "padding_ratio": 0.10,
        "glass_effect": True,
        "blur_radius": 15,
        "glass_opacity": 0.25
    },
}


# ==================== 디자인 템플릿 (조합) ====================

DESIGN_TEMPLATES = {
    # ===== 미니멀 & 클린 =====
    "minimal_white": {
        "id": "minimal_white",
        "name": "미니멀 화이트",
        "category": "minimal",
        "description": "깔끔하고 세련된 화이트 미니멀",
        "preview_color": "#FFFFFF",
        "palette": "clean_white",
        "layout": "center",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.9,
            "letter_spacing": 2,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "solid",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "line_accent",
            "position": "bottom_center",
            "color": "accent",
            "thickness": 3,
            "length": 60
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    "minimal_black": {
        "id": "minimal_black",
        "name": "미니멀 블랙",
        "category": "minimal",
        "description": "모던하고 강렬한 블랙",
        "preview_color": "#111111",
        "palette": "pure_black",
        "layout": "center",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.05,
            "content_weight": "light",
            "content_size_ratio": 0.9,
            "letter_spacing": 3,
            "line_height_ratio": 1.7
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "corner_brackets",
            "color": "accent",
            "thickness": 2,
            "size": 30
        },
        "text_effect": {
            "shadow_type": "subtle",
            "shadow_intensity": 0.3
        }
    },
    
    # ===== 파스텔 & 소프트 =====
    "pastel_pink": {
        "id": "pastel_pink",
        "name": "파스텔 핑크",
        "category": "pastel",
        "description": "부드럽고 달콤한 핑크",
        "preview_color": "#FFE4E6",
        "palette": "soft_pink",
        "layout": "center",
        "text_style": {
            "title_weight": "semibold",
            "title_size_ratio": 0.95,
            "content_weight": "regular",
            "content_size_ratio": 0.85,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 32,
            "shadow_blur": 20,
            "shadow_opacity": 0.1,
            "card_color": (255, 255, 255),
            "card_opacity": 0.7
        },
        "decoration": {
            "type": "rounded_border",
            "color": "accent",
            "thickness": 2,
            "radius": 32
        },
        "text_effect": {
            "shadow_type": "soft_glow",
            "shadow_intensity": 0.4,
            "shadow_color": (255, 200, 200)
        }
    },
    
    "pastel_mint": {
        "id": "pastel_mint",
        "name": "파스텔 민트",
        "category": "pastel",
        "description": "청량하고 상쾌한 민트",
        "preview_color": "#C8FFF3",
        "palette": "mint_fresh",
        "layout": "top_heavy",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 24,
            "shadow_blur": 15,
            "shadow_opacity": 0.08
        },
        "decoration": {
            "type": "circle_accent",
            "position": "top_right",
            "color": "accent",
            "size": 80,
            "opacity": 0.3
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    "pastel_lavender": {
        "id": "pastel_lavender",
        "name": "파스텔 라벤더",
        "category": "pastel",
        "description": "몽환적인 라벤더 드림",
        "preview_color": "#E6E6FA",
        "palette": "lavender_dream",
        "layout": "center",
        "text_style": {
            "title_weight": "medium",
            "title_size_ratio": 0.95,
            "content_weight": "regular",
            "content_size_ratio": 0.85,
            "letter_spacing": 2,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 40,
            "shadow_blur": 25,
            "shadow_opacity": 0.12,
            "card_color": (255, 255, 255),
            "card_opacity": 0.6
        },
        "decoration": {
            "type": "gradient_border",
            "colors": [(216, 191, 216), (230, 230, 250)],
            "thickness": 3
        },
        "text_effect": {
            "shadow_type": "soft_glow",
            "shadow_intensity": 0.3,
            "shadow_color": (200, 180, 220)
        }
    },
    
    "pastel_cream": {
        "id": "pastel_cream",
        "name": "버터 크림",
        "category": "pastel",
        "description": "따뜻하고 포근한 크림",
        "preview_color": "#FFFDF0",
        "palette": "butter_cream",
        "layout": "magazine_left",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "underline",
            "color": "accent",
            "thickness": 4,
            "style": "hand_drawn"
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    # ===== 비비드 & 볼드 =====
    "bold_blue": {
        "id": "bold_blue",
        "name": "볼드 블루",
        "category": "vivid",
        "description": "강렬한 일렉트릭 블루",
        "preview_color": "#0066FF",
        "palette": "electric_blue",
        "layout": "title_focus",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.2,
            "content_weight": "bold",
            "content_size_ratio": 0.95,
            "letter_spacing": 0,
            "line_height_ratio": 1.4
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0.1,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "glow_accent",
            "color": (0, 255, 255),
            "intensity": 0.5,
            "size": 100
        },
        "text_effect": {
            "shadow_type": "neon",
            "shadow_intensity": 1.0,
            "shadow_color": (0, 200, 255)
        }
    },
    
    "bold_coral": {
        "id": "bold_coral",
        "name": "코랄 팝",
        "category": "vivid",
        "description": "활기찬 코랄 에너지",
        "preview_color": "#FF7F50",
        "palette": "coral_energy",
        "layout": "center",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.15,
            "content_weight": "bold",
            "content_size_ratio": 0.95,
            "letter_spacing": -1,
            "line_height_ratio": 1.3
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 16,
            "shadow_blur": 30,
            "shadow_opacity": 0.2,
            "card_color": (255, 255, 255),
            "card_opacity": 0.15
        },
        "decoration": {
            "type": "corner_fill",
            "color": (255, 69, 0),
            "size": 120,
            "opacity": 0.3
        },
        "text_effect": {
            "shadow_type": "drop",
            "shadow_intensity": 1.2,
            "shadow_offset": (4, 4)
        }
    },
    
    "neon_cyber": {
        "id": "neon_cyber",
        "name": "네온 사이버",
        "category": "vivid",
        "description": "사이버펑크 네온 퍼플",
        "preview_color": "#8A2BE2",
        "palette": "neon_purple",
        "layout": "glassmorphism",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.1,
            "content_weight": "medium",
            "content_size_ratio": 0.92,
            "letter_spacing": 2,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0.2,
            "blur_radius": 3,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "glass_effect": True,
            "corner_radius": 20,
            "shadow_blur": 40,
            "shadow_opacity": 0.3,
            "glass_blur": 15,
            "glass_opacity": 0.2
        },
        "decoration": {
            "type": "neon_border",
            "color": (255, 0, 255),
            "thickness": 2,
            "glow_radius": 10
        },
        "text_effect": {
            "shadow_type": "neon",
            "shadow_intensity": 1.5,
            "shadow_color": (255, 100, 255)
        }
    },
    
    "fresh_lime": {
        "id": "fresh_lime",
        "name": "프레시 라임",
        "category": "vivid",
        "description": "상쾌한 라임 그린",
        "preview_color": "#32CD32",
        "palette": "lime_punch",
        "layout": "split_diagonal",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.1,
            "content_weight": "semibold",
            "content_size_ratio": 0.9,
            "letter_spacing": 0,
            "line_height_ratio": 1.4
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "diagonal_stripe",
            "color": (0, 255, 127),
            "thickness": 8,
            "spacing": 40,
            "opacity": 0.2
        },
        "text_effect": {
            "shadow_type": "hard",
            "shadow_intensity": 0.8,
            "shadow_offset": (3, 3)
        }
    },
    
    # ===== 뉴트럴 & 어시 =====
    "natural_sand": {
        "id": "natural_sand",
        "name": "내추럴 샌드",
        "category": "neutral",
        "description": "자연스러운 베이지 톤",
        "preview_color": "#EDE0D4",
        "palette": "warm_sand",
        "layout": "editorial",
        "text_style": {
            "title_weight": "medium",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 2,
            "line_height_ratio": 1.7
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False,
            "texture": "paper"
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "simple_frame",
            "color": "accent",
            "thickness": 1,
            "margin": 30
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    "deep_forest": {
        "id": "deep_forest",
        "name": "딥 포레스트",
        "category": "neutral",
        "description": "깊은 숲의 고요함",
        "preview_color": "#225533",
        "palette": "forest_green",
        "layout": "center",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.05,
            "content_weight": "regular",
            "content_size_ratio": 0.9,
            "letter_spacing": 1,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0.1,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 16,
            "shadow_blur": 25,
            "shadow_opacity": 0.2,
            "card_color": (255, 255, 255),
            "card_opacity": 0.1
        },
        "decoration": {
            "type": "leaf_accent",
            "color": (144, 238, 144),
            "opacity": 0.3
        },
        "text_effect": {
            "shadow_type": "soft",
            "shadow_intensity": 0.6
        }
    },
    
    "ocean_calm": {
        "id": "ocean_calm",
        "name": "오션 캄",
        "category": "neutral",
        "description": "차분한 바다의 깊이",
        "preview_color": "#004D4D",
        "palette": "ocean_depth",
        "layout": "bottom_heavy",
        "text_style": {
            "title_weight": "semibold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 2,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0.05,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 20,
            "shadow_blur": 30,
            "shadow_opacity": 0.15,
            "card_color": (255, 255, 255),
            "card_opacity": 0.08
        },
        "decoration": {
            "type": "wave_pattern",
            "color": (64, 224, 208),
            "opacity": 0.15
        },
        "text_effect": {
            "shadow_type": "soft_glow",
            "shadow_intensity": 0.5,
            "shadow_color": (64, 224, 208)
        }
    },
    
    "warm_terra": {
        "id": "warm_terra",
        "name": "웜 테라코타",
        "category": "neutral",
        "description": "따뜻한 흙빛 무드",
        "preview_color": "#CC7755",
        "palette": "terracotta",
        "layout": "magazine_left",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "geometric_accent",
            "shapes": ["circle", "triangle"],
            "color": (139, 69, 19),
            "opacity": 0.2
        },
        "text_effect": {
            "shadow_type": "drop",
            "shadow_intensity": 0.8
        }
    },
    
    # ===== 프리미엄 & 럭셔리 =====
    "luxury_gold": {
        "id": "luxury_gold",
        "name": "럭셔리 골드",
        "category": "premium",
        "description": "고급스러운 골드 & 블랙",
        "preview_color": "#D4AF37",
        "palette": "gold_luxury",
        "layout": "center",
        "text_style": {
            "title_weight": "medium",
            "title_size_ratio": 1.0,
            "content_weight": "light",
            "content_size_ratio": 0.88,
            "letter_spacing": 4,
            "line_height_ratio": 1.8
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 0,
            "shadow_blur": 0,
            "border_color": (212, 175, 55),
            "border_width": 1
        },
        "decoration": {
            "type": "gold_frame",
            "color": (212, 175, 55),
            "style": "art_deco",
            "thickness": 2
        },
        "text_effect": {
            "shadow_type": "gold_glow",
            "shadow_intensity": 0.6,
            "shadow_color": (212, 175, 55)
        }
    },
    
    "elegant_rose": {
        "id": "elegant_rose",
        "name": "엘레강트 로즈",
        "category": "premium",
        "description": "세련된 로즈 골드",
        "preview_color": "#B76E79",
        "palette": "rose_gold",
        "layout": "center",
        "text_style": {
            "title_weight": "medium",
            "title_size_ratio": 0.95,
            "content_weight": "light",
            "content_size_ratio": 0.85,
            "letter_spacing": 3,
            "line_height_ratio": 1.7
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 30,
            "shadow_blur": 20,
            "shadow_opacity": 0.2,
            "card_color": (255, 255, 255),
            "card_opacity": 0.05
        },
        "decoration": {
            "type": "elegant_border",
            "color": (183, 110, 121),
            "style": "double",
            "thickness": 1
        },
        "text_effect": {
            "shadow_type": "soft_glow",
            "shadow_intensity": 0.4,
            "shadow_color": (183, 110, 121)
        }
    },
    
    "silver_modern": {
        "id": "silver_modern",
        "name": "실버 모던",
        "category": "premium",
        "description": "차갑고 세련된 실버",
        "preview_color": "#C0C0C0",
        "palette": "silver_frost",
        "layout": "editorial",
        "text_style": {
            "title_weight": "semibold",
            "title_size_ratio": 1.0,
            "content_weight": "regular",
            "content_size_ratio": 0.88,
            "letter_spacing": 2,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "gradient",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False,
            "texture": "brushed_metal"
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "metallic_line",
            "color": (105, 105, 105),
            "thickness": 1,
            "style": "parallel"
        },
        "text_effect": {
            "shadow_type": "subtle",
            "shadow_intensity": 0.3
        }
    },
    
    # ===== 그라데이션 스페셜 =====
    "sunset_dream": {
        "id": "sunset_dream",
        "name": "선셋 드림",
        "category": "gradient",
        "description": "따뜻한 노을 그라데이션",
        "preview_color": "#FF9A56",
        "palette": "sunset_glow",
        "layout": "center",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.1,
            "content_weight": "medium",
            "content_size_ratio": 0.92,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "multi_gradient",
            "direction": "diagonal",
            "overlay_opacity": 0.1,
            "blur_radius": 0,
            "use_vignette": True
        },
        "card_style": {
            "use_card": True,
            "glass_effect": True,
            "corner_radius": 24,
            "shadow_blur": 30,
            "shadow_opacity": 0.2,
            "glass_blur": 10,
            "glass_opacity": 0.15
        },
        "decoration": {
            "type": "sun_rays",
            "color": (255, 255, 255),
            "opacity": 0.1
        },
        "text_effect": {
            "shadow_type": "warm_glow",
            "shadow_intensity": 0.8,
            "shadow_color": (255, 150, 100)
        }
    },
    
    "aurora_magic": {
        "id": "aurora_magic",
        "name": "오로라 매직",
        "category": "gradient",
        "description": "신비로운 오로라",
        "preview_color": "#43CEA2",
        "palette": "aurora_borealis",
        "layout": "glassmorphism",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.05,
            "content_weight": "medium",
            "content_size_ratio": 0.9,
            "letter_spacing": 2,
            "line_height_ratio": 1.6
        },
        "background_style": {
            "type": "aurora_gradient",
            "direction": "radial",
            "overlay_opacity": 0.15,
            "blur_radius": 2,
            "use_vignette": True,
            "animation": "shimmer"
        },
        "card_style": {
            "use_card": True,
            "glass_effect": True,
            "corner_radius": 28,
            "shadow_blur": 40,
            "shadow_opacity": 0.25,
            "glass_blur": 20,
            "glass_opacity": 0.2
        },
        "decoration": {
            "type": "aurora_wave",
            "colors": [(67, 206, 162), (24, 90, 157), (147, 112, 219)],
            "opacity": 0.3
        },
        "text_effect": {
            "shadow_type": "multi_glow",
            "shadow_intensity": 0.7,
            "shadow_colors": [(67, 206, 162), (147, 112, 219)]
        }
    },
    
    "candy_pop": {
        "id": "candy_pop",
        "name": "캔디 팝",
        "category": "gradient",
        "description": "달콤한 캔디 그라데이션",
        "preview_color": "#FFB6C1",
        "palette": "cotton_candy",
        "layout": "card_float",
        "text_style": {
            "title_weight": "bold",
            "title_size_ratio": 1.0,
            "content_weight": "medium",
            "content_size_ratio": 0.88,
            "letter_spacing": 1,
            "line_height_ratio": 1.5
        },
        "background_style": {
            "type": "candy_gradient",
            "direction": "horizontal",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 36,
            "shadow_blur": 25,
            "shadow_opacity": 0.15,
            "card_color": (255, 255, 255),
            "card_opacity": 0.7
        },
        "decoration": {
            "type": "bubble_pattern",
            "colors": [(255, 182, 193), (173, 216, 230)],
            "opacity": 0.2,
            "count": 5
        },
        "text_effect": {
            "shadow_type": "soft",
            "shadow_intensity": 0.4
        }
    },
    
    # ===== 매거진 & 에디토리얼 =====
    "magazine_mono": {
        "id": "magazine_mono",
        "name": "매거진 모노",
        "category": "editorial",
        "description": "클래식 매거진 스타일",
        "preview_color": "#2C2C2C",
        "palette": "pure_black",
        "layout": "editorial",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.3,
            "content_weight": "regular",
            "content_size_ratio": 0.85,
            "letter_spacing": 0,
            "line_height_ratio": 1.4,
            "title_transform": "uppercase"
        },
        "background_style": {
            "type": "solid",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "editorial_lines",
            "color": "accent",
            "thickness": 1,
            "style": "grid"
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    "newspaper_classic": {
        "id": "newspaper_classic",
        "name": "뉴스페이퍼",
        "category": "editorial",
        "description": "클래식 신문 스타일",
        "preview_color": "#F5F5F0",
        "palette": "clean_white",
        "layout": "magazine_left",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.2,
            "content_weight": "regular",
            "content_size_ratio": 0.85,
            "letter_spacing": 0,
            "line_height_ratio": 1.5,
            "font_style": "serif"
        },
        "background_style": {
            "type": "paper_texture",
            "overlay_opacity": 0,
            "blur_radius": 0,
            "use_vignette": False
        },
        "card_style": {
            "use_card": False,
            "corner_radius": 0,
            "shadow_blur": 0
        },
        "decoration": {
            "type": "newspaper_frame",
            "color": (0, 0, 0),
            "thickness": 2,
            "style": "double_line"
        },
        "text_effect": {
            "shadow_type": "none",
            "shadow_intensity": 0
        }
    },
    
    # ===== 레트로 & 빈티지 =====
    "retro_70s": {
        "id": "retro_70s",
        "name": "레트로 70s",
        "category": "retro",
        "description": "70년대 레트로 무드",
        "preview_color": "#E07B39",
        "palette": "coral_energy",
        "layout": "center",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.15,
            "content_weight": "bold",
            "content_size_ratio": 0.95,
            "letter_spacing": 2,
            "line_height_ratio": 1.4,
            "font_style": "retro"
        },
        "background_style": {
            "type": "retro_gradient",
            "overlay_opacity": 0.05,
            "blur_radius": 0,
            "use_vignette": True,
            "grain": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 0,
            "shadow_blur": 0,
            "border_color": (255, 255, 255),
            "border_width": 4
        },
        "decoration": {
            "type": "retro_circles",
            "colors": [(255, 69, 0), (255, 165, 0), (255, 215, 0)],
            "opacity": 0.3
        },
        "text_effect": {
            "shadow_type": "retro_offset",
            "shadow_intensity": 1.0,
            "shadow_color": (139, 69, 19),
            "shadow_offset": (4, 4)
        }
    },
    
    "vintage_poster": {
        "id": "vintage_poster",
        "name": "빈티지 포스터",
        "category": "retro",
        "description": "클래식 빈티지 포스터",
        "preview_color": "#D4C4A8",
        "palette": "warm_sand",
        "layout": "title_focus",
        "text_style": {
            "title_weight": "black",
            "title_size_ratio": 1.25,
            "content_weight": "medium",
            "content_size_ratio": 0.9,
            "letter_spacing": 3,
            "line_height_ratio": 1.5,
            "title_transform": "uppercase"
        },
        "background_style": {
            "type": "aged_paper",
            "overlay_opacity": 0.1,
            "blur_radius": 0,
            "use_vignette": True,
            "grain": True,
            "worn_edges": True
        },
        "card_style": {
            "use_card": True,
            "corner_radius": 8,
            "shadow_blur": 20,
            "shadow_opacity": 0.3,
            "card_color": (255, 250, 240),
            "card_opacity": 0.9
        },
        "decoration": {
            "type": "vintage_border",
            "color": (100, 80, 60),
            "style": "ornamental",
            "thickness": 3
        },
        "text_effect": {
            "shadow_type": "vintage",
            "shadow_intensity": 0.6
        }
    },
}


# ==================== 템플릿 카테고리 ====================

TEMPLATE_CATEGORIES = {
    "minimal": {
        "name": "미니멀",
        "description": "깔끔하고 세련된 디자인",
        "icon": "◻️",
        "templates": ["minimal_white", "minimal_black"]
    },
    "pastel": {
        "name": "파스텔",
        "description": "부드럽고 따뜻한 색감",
        "icon": "🌸",
        "templates": ["pastel_pink", "pastel_mint", "pastel_lavender", "pastel_cream"]
    },
    "vivid": {
        "name": "비비드",
        "description": "강렬하고 대담한 컬러",
        "icon": "🔥",
        "templates": ["bold_blue", "bold_coral", "neon_cyber", "fresh_lime"]
    },
    "neutral": {
        "name": "뉴트럴",
        "description": "자연스럽고 차분한 톤",
        "icon": "🌿",
        "templates": ["natural_sand", "deep_forest", "ocean_calm", "warm_terra"]
    },
    "premium": {
        "name": "프리미엄",
        "description": "고급스럽고 세련된 스타일",
        "icon": "✨",
        "templates": ["luxury_gold", "elegant_rose", "silver_modern"]
    },
    "gradient": {
        "name": "그라데이션",
        "description": "화려한 색상 전환",
        "icon": "🌈",
        "templates": ["sunset_dream", "aurora_magic", "candy_pop"]
    },
    "editorial": {
        "name": "에디토리얼",
        "description": "매거진 & 신문 스타일",
        "icon": "📰",
        "templates": ["magazine_mono", "newspaper_classic"]
    },
    "retro": {
        "name": "레트로",
        "description": "빈티지 & 복고풍",
        "icon": "📻",
        "templates": ["retro_70s", "vintage_poster"]
    }
}


# ==================== 헬퍼 함수 ====================

def get_template(template_id: str) -> dict:
    """템플릿 ID로 템플릿 정보 가져오기"""
    return DESIGN_TEMPLATES.get(template_id)


def get_palette(palette_id: str) -> dict:
    """팔레트 ID로 색상 팔레트 가져오기"""
    return COLOR_PALETTES.get(palette_id)


def get_layout(layout_id: str) -> dict:
    """레이아웃 ID로 레이아웃 정보 가져오기"""
    return LAYOUT_STYLES.get(layout_id)


def get_templates_by_category(category: str) -> list:
    """카테고리별 템플릿 목록 가져오기"""
    if category in TEMPLATE_CATEGORIES:
        template_ids = TEMPLATE_CATEGORIES[category]["templates"]
        return [DESIGN_TEMPLATES[tid] for tid in template_ids if tid in DESIGN_TEMPLATES]
    return []


def get_all_templates() -> list:
    """모든 템플릿 목록 가져오기"""
    return list(DESIGN_TEMPLATES.values())


def get_random_template() -> dict:
    """랜덤 템플릿 선택"""
    import random
    return random.choice(list(DESIGN_TEMPLATES.values()))


def get_template_preview_data(template_id: str) -> dict:
    """프론트엔드 미리보기용 데이터"""
    template = get_template(template_id)
    if not template:
        return None
    
    palette = get_palette(template["palette"])
    layout = get_layout(template["layout"])
    
    return {
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
            "text_secondary": palette["text_secondary"]
        },
        "layout": layout["name"],
        "has_card": template["card_style"].get("use_card", False),
        "has_glass": template["card_style"].get("glass_effect", False)
    }


# ==================== 프론트엔드 API용 데이터 ====================

def get_frontend_template_list() -> list:
    """프론트엔드에 전달할 템플릿 리스트 (미리보기 이미지 URL 포함)"""
    result = []
    for category_id, category in TEMPLATE_CATEGORIES.items():
        category_data = {
            "id": category_id,
            "name": category["name"],
            "description": category["description"],
            "icon": category["icon"],
            "templates": []
        }

        for template_id in category["templates"]:
            template = DESIGN_TEMPLATES.get(template_id)
            if template:
                # 미리보기 이미지 URL
                preview_cover = f"/static/template_previews/{template_id}_cover.png"
                preview_content = f"/static/template_previews/{template_id}_content.png"

                category_data["templates"].append({
                    "id": template["id"],
                    "name": template["name"],
                    "preview_color": template["preview_color"],
                    "description": template["description"],
                    # 미리보기 이미지 URL
                    "preview_images": {
                        "cover": preview_cover,
                        "content": preview_content
                    }
                })

        result.append(category_data)

    return result


if __name__ == "__main__":
    # 테스트 출력
    print("=" * 60)
    print("🎨 개선된 카드뉴스 템플릿 시스템")
    print("=" * 60)
    
    print(f"\n📊 통계:")
    print(f"  - 색상 팔레트: {len(COLOR_PALETTES)}개")
    print(f"  - 레이아웃 스타일: {len(LAYOUT_STYLES)}개")
    print(f"  - 디자인 템플릿: {len(DESIGN_TEMPLATES)}개")
    print(f"  - 카테고리: {len(TEMPLATE_CATEGORIES)}개")
    
    print(f"\n📁 카테고리별 템플릿:")
    for cat_id, cat in TEMPLATE_CATEGORIES.items():
        print(f"  {cat['icon']} {cat['name']}: {len(cat['templates'])}개")
        for tid in cat['templates']:
            template = DESIGN_TEMPLATES.get(tid)
            if template:
                print(f"      - {template['name']}")
