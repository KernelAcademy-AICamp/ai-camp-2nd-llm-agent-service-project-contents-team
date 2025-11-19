from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
import requests
from pathlib import Path
from anthropic import Anthropic
import asyncio

router = APIRouter(prefix="/api", tags=["cardnews"])

# 폰트 디렉토리
FONT_DIR = Path(__file__).parent.parent.parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)

# 색상 테마 설정
COLOR_THEMES = {
    "warm": {
        "primary": (255, 139, 90),
        "secondary": (255, 229, 217),
        "accent": (212, 101, 74),
        "textColor": "white",
        "textColorDark": "#2D1810"
    },
    "cool": {
        "primary": (74, 144, 226),
        "secondary": (227, 242, 253),
        "accent": (46, 92, 138),
        "textColor": "white",
        "textColorDark": "#0D2841"
    },
    "vibrant": {
        "primary": (255, 107, 157),
        "secondary": (255, 229, 238),
        "accent": (233, 30, 99),
        "textColor": "white",
        "textColorDark": "#4A0E2A"
    },
    "minimal": {
        "primary": (66, 66, 66),
        "secondary": (245, 245, 245),
        "accent": (33, 33, 33),
        "textColor": "white",
        "textColorDark": "#212121"
    }
}


async def generate_cardnews_content_from_description(description: str, purpose: str) -> list:
    """사용자 설명을 기반으로 1장의 카드뉴스 콘텐츠를 AI가 생성"""
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            print("⚠️ ANTHROPIC_API_KEY가 설정되지 않음")
            return []

        # Anthropic 클라이언트 생성 (0.39.0 버전 방식)
        from anthropic import Anthropic
        client = Anthropic()

        purpose_map = {
            'promotion': '프로모션/할인 홍보',
            'menu': '신메뉴/상품 소개',
            'info': '정보 전달/팁 공유',
            'event': '이벤트/행사 안내'
        }

        prompt = f"""당신은 SNS 마케팅 전문가입니다. 다음 설명을 바탕으로 1장의 카드뉴스를 기획해주세요.

**사용자 입력**: {description}
**용도**: {purpose_map.get(purpose, purpose)}

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
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)

        if json_match:
            cards = json.loads(json_match.group(0))
            if isinstance(cards, list) and len(cards) == 1:
                print(f"✅ AI가 1장의 카드뉴스 콘텐츠 생성 완료:")
                print(f"   1. {cards[0]['title']} - {cards[0]['description']}")
                return cards
    except Exception as e:
        print(f"⚠️ AI 콘텐츠 생성 실패: {str(e)}")

    return []


async def enhance_content_with_ai(title: str, description: str, purpose: str) -> dict:
    """AI로 카드뉴스 콘텐츠 개선"""
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            return {"title": title, "description": description or ""}

        # Anthropic 클라이언트 생성 (0.39.0 버전 방식)
        from anthropic import Anthropic
        client = Anthropic()

        purpose_map = {
            'promotion': '프로모션/할인 홍보',
            'menu': '신메뉴/상품 소개',
            'info': '정보 전달/팁 공유',
            'event': '이벤트/행사 안내'
        }

        prompt = f"""당신은 전문 마케팅 카피라이터입니다. 다음 카드뉴스 문구를 더 임팩트있고 매력적으로 개선해주세요.

**원본 제목**: {title}
**원본 설명**: {description or '없음'}
**용도**: {purpose_map.get(purpose, purpose)}

**개선 규칙**:
1. 제목: 간결하고 강렬하게 (최대 15자, 핵심 메시지 전달)
2. 설명: 구체적이고 행동을 유도하도록 (최대 35자)
3. 용도에 맞는 톤: {purpose}
4. 이모지 제거, 순수 한글/영문/숫자만 사용
5. 과장 없이 진실되고 신뢰감 있게

JSON 형식으로만 응답: {{"title": "개선된 제목", "description": "개선된 설명", "reasoning": "개선 이유"}}"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text
        # JSON 추출
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)

        if json_match:
            enhanced = json.loads(json_match.group(0))
            print(f"✨ AI 개선 완료:")
            print(f"   제목: \"{title}\" → \"{enhanced['title']}\"")
            print(f"   설명: \"{description}\" → \"{enhanced['description']}\"")
            return {
                "title": enhanced["title"],
                "description": enhanced["description"]
            }
    except Exception as e:
        print(f"⚠️ AI 개선 실패 (원본 사용): {str(e)}")

    return {"title": title, "description": description or ""}


def download_font(font_name: str, url: str) -> Path:
    """구글 폰트 다운로드"""
    font_path = FONT_DIR / font_name
    if not font_path.exists():
        try:
            print(f"📥 폰트 다운로드 중: {font_name}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            font_path.write_bytes(response.content)
            print(f"✅ 폰트 다운로드 완료: {font_name}")
        except Exception as e:
            print(f"⚠️ 폰트 다운로드 실패: {e}")
            return None
    return font_path


def get_font(font_style: str, font_size: int, bold: bool = False):
    """폰트 스타일에 따라 적절한 폰트 반환"""

    # 폰트 URL (Google Fonts - 무료 한글 폰트)
    fonts = {
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

    # 폰트 선택
    if font_style == "rounded":
        font_key = "rounded_bold" if bold else "rounded_regular"
    else:  # sharp
        font_key = "sharp_bold" if bold else "sharp_regular"

    font_info = fonts[font_key]
    font_path = download_font(font_info["name"], font_info["url"])

    if font_path and font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), font_size)
        except Exception as e:
            print(f"⚠️ 폰트 로드 실패: {e}")

    # 폴백: 시스템 폰트
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", font_size)
    except:
        return ImageFont.load_default()


def draw_text_on_image(image: Image.Image, text: str, position: tuple,
                       font_size: int, color: str = "white", max_width: int = None,
                       font_style: str = "rounded", bold: bool = False,
                       shadow: bool = True, align: str = "left"):
    """이미지에 꾸며진 텍스트 그리기"""
    draw = ImageDraw.Draw(image, 'RGBA')

    # 폰트 로드
    font = get_font(font_style, font_size, bold)

    # 텍스트 줄바꿈 처리
    lines = []
    if max_width:
        words = text.split()
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
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

        # 그림자 효과 (더 부드럽게)
        if shadow:
            shadow_offset = max(2, font_size // 20)
            for offset_x in range(-shadow_offset, shadow_offset + 1):
                for offset_y in range(-shadow_offset, shadow_offset + 1):
                    if offset_x == 0 and offset_y == 0:
                        continue
                    draw.text(
                        (x + offset_x, y + offset_y),
                        line,
                        fill=(0, 0, 0, 100),  # 반투명 검은색
                        font=font
                    )

        # 메인 텍스트
        draw.text((x, y), line, fill=color, font=font)

        # 다음 줄 위치
        y += text_height + max(10, font_size // 5)


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
    """카드뉴스 생성 API - 사용자 설명 기반으로 5장의 카드뉴스 자동 생성"""
    try:
        if not images or len(images) == 0:
            raise HTTPException(status_code=400, detail="최소 1개 이상의 이미지가 필요합니다.")

        print(f"📰 카드뉴스 생성 시작")
        print(f"🎨 스타일: 폰트={fontStyle}, 색상={colorTheme}, 용도={purpose}, 레이아웃={layoutStyle}")

        card_width = 1080
        card_height = 1080
        card_news_images = []

        # JSON 파싱
        title_array = json.loads(titles)
        desc_array = json.loads(descriptions)

        # 사용자 입력 (제목이 실제로는 설명 텍스트)
        user_description = title_array[0] if len(title_array) > 0 else ""

        # AI로 1장의 카드뉴스 콘텐츠 생성
        print(f"\n🤖 AI가 '{user_description}'를 기반으로 1장의 카드뉴스 콘텐츠를 생성 중...")
        ai_cards = await generate_cardnews_content_from_description(user_description, purpose)

        if not ai_cards or len(ai_cards) != 1:
            raise HTTPException(status_code=500, detail="AI 콘텐츠 생성에 실패했습니다.")

        # 배경 이미지 로드 (첫 번째 이미지를 모든 카드에 사용)
        image_data = await images[0].read()
        background_image = Image.open(io.BytesIO(image_data))

        # RGB 변환
        if background_image.mode != 'RGB':
            background_image = background_image.convert('RGB')

        # 테마 선택
        selected_theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])

        # 5장의 카드 생성
        for i, card_content in enumerate(ai_cards):
            print(f"\n📄 {i + 1}번째 카드 생성 중...")

            title = card_content["title"]
            description = card_content["description"]

            # 배경 이미지 복사 (모든 카드에 동일한 배경 사용)
            original_image = background_image.copy()

            # 레이아웃별 처리
            if layoutStyle == "overlay":
                # 이미지를 카드 크기로 조정
                img = original_image.resize((card_width, card_height), Image.Resampling.LANCZOS)

                # 어둡게
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.8)

                # 하단 색상 박스 추가
                draw = ImageDraw.Draw(img)
                box_height = int(card_height * 0.4)
                box_y = card_height - box_height

                # 그라데이션 효과
                for y in range(box_y - 100, box_y):
                    alpha = int(((y - (box_y - 100)) / 100) * 220)
                    color = selected_theme["primary"] + (alpha,)
                    draw.rectangle([(0, y), (card_width, y + 1)], fill=color)

                # 완전 불투명 박스
                draw.rectangle(
                    [(0, box_y), (card_width, card_height)],
                    fill=selected_theme["primary"]
                )

                # 악센트 라인
                draw.rectangle(
                    [(0, box_y), (card_width, box_y + 8)],
                    fill=selected_theme["accent"]
                )
            else:
                # 다른 레이아웃도 기본 overlay로 처리
                img = original_image.resize((card_width, card_height), Image.Resampling.LANCZOS)

            # 제목 텍스트 추가 (bold, shadow, left align)
            draw_text_on_image(
                img, title,
                (80, card_height - 280),
                font_size=80,
                color="white",
                max_width=card_width - 160,
                font_style=fontStyle,
                bold=True,
                shadow=True,
                align="left"
            )

            # 설명 텍스트 추가 (regular, shadow, left align)
            if description:
                draw_text_on_image(
                    img, description,
                    (80, card_height - 160),
                    font_size=40,
                    color="white",
                    max_width=card_width - 160,
                    font_style=fontStyle,
                    bold=False,
                    shadow=True,
                    align="left"
                )

            # 페이지 번호 (작은 크기, no shadow)
            page_text = f"{i + 1} / 5"
            draw_text_on_image(
                img, page_text,
                (card_width - 120, card_height - 60),
                font_size=20,
                color="white",
                font_style=fontStyle,
                bold=False,
                shadow=False,
                align="left"
            )

            # 배지 추가
            badge_text = {
                'promotion': '프로모션',
                'menu': '신메뉴',
                'info': '정보',
                'event': '이벤트'
            }.get(purpose, '정보')

            draw = ImageDraw.Draw(img)
            badge_x, badge_y = 50, 50
            badge_width, badge_height = 180, 70

            # 배지 배경 (둥근 모서리 효과)
            draw.rectangle(
                [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                fill=selected_theme["accent"]
            )
            # 하단 악센트 라인
            draw.rectangle(
                [(badge_x, badge_y + badge_height), (badge_x + badge_width, badge_y + badge_height + 5)],
                fill=(255, 255, 255)
            )

            # 배지 텍스트 (bold, centered)
            draw_text_on_image(
                img, badge_text,
                (badge_x + 20, badge_y + 20),
                font_size=32,
                color="white",
                max_width=badge_width - 40,
                font_style=fontStyle,
                bold=True,
                shadow=False,
                align="center"
            )

            # Base64 변환
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            base64_image = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            card_news_images.append(base64_image)

            print(f"✅ 카드 {i + 1} 생성 완료")

        return JSONResponse({
            "success": True,
            "message": f"{len(images)}개의 카드뉴스가 생성되었습니다.",
            "cards": card_news_images,
            "count": len(images)
        })

    except Exception as e:
        print(f"카드뉴스 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"카드뉴스 생성 중 오류가 발생했습니다: {str(e)}")


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
    """카드뉴스 스트리밍 생성 API - 실시간 미리보기 지원"""

    async def event_stream():
        try:
            if not images or len(images) == 0:
                yield f"data: {json.dumps({'type': 'error', 'message': '최소 1개 이상의 이미지가 필요합니다.'})}\n\n"
                return

            # 상태 전송: AI 콘텐츠 생성 중
            yield f"data: {json.dumps({'type': 'status', 'message': 'AI가 카드뉴스 콘텐츠를 분석하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.1)

            # JSON 파싱
            title_array = json.loads(titles)
            user_description = title_array[0] if len(title_array) > 0 else ""

            # AI로 1장의 카드뉴스 콘텐츠 생성
            ai_cards = await generate_cardnews_content_from_description(user_description, purpose)

            if not ai_cards or len(ai_cards) != 1:
                yield f"data: {json.dumps({'type': 'error', 'message': 'AI 콘텐츠 생성에 실패했습니다.'})}\n\n"
                return

            # 배경 이미지 로드
            image_data = await images[0].read()
            background_image = Image.open(io.BytesIO(image_data))
            if background_image.mode != 'RGB':
                background_image = background_image.convert('RGB')

            # 테마 선택
            selected_theme = COLOR_THEMES.get(colorTheme, COLOR_THEMES["warm"])

            card_width = 1080
            card_height = 1080

            # 카드 생성하며 스트리밍
            for i, card_content in enumerate(ai_cards):
                yield f"data: {json.dumps({'type': 'status', 'message': f'카드 생성 중...'})}\n\n"

                title = card_content["title"]
                description = card_content["description"]

                # 배경 이미지 복사
                original_image = background_image.copy()

                # 이미지 처리
                img = original_image.resize((card_width, card_height), Image.Resampling.LANCZOS)

                # 어둡게
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.6)

                # 텍스트 추가
                draw_text_on_image(
                    img, title,
                    (80, card_height - 280),
                    font_size=80,
                    color="white",
                    max_width=card_width - 160,
                    font_style=fontStyle,
                    bold=True,
                    shadow=True,
                    align="left"
                )

                if description:
                    draw_text_on_image(
                        img, description,
                        (80, card_height - 160),
                        font_size=40,
                        color="white",
                        max_width=card_width - 160,
                        font_style=fontStyle,
                        bold=False,
                        shadow=True,
                        align="left"
                    )

                # 페이지 번호
                page_text = f"{i + 1} / 5"
                draw_text_on_image(
                    img, page_text,
                    (card_width - 120, card_height - 60),
                    font_size=20,
                    color="white",
                    font_style=fontStyle,
                    bold=False,
                    shadow=False,
                    align="left"
                )

                # 배지 추가
                badge_text = {
                    'promotion': '프로모션',
                    'menu': '신메뉴',
                    'info': '정보',
                    'event': '이벤트'
                }.get(purpose, '정보')

                draw = ImageDraw.Draw(img)
                badge_x, badge_y = 50, 50
                badge_width, badge_height = 180, 70

                draw.rectangle(
                    [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                    fill=selected_theme["accent"]
                )
                draw.rectangle(
                    [(badge_x, badge_y + badge_height), (badge_x + badge_width, badge_y + badge_height + 5)],
                    fill=(255, 255, 255)
                )

                draw_text_on_image(
                    img, badge_text,
                    (badge_x + 20, badge_y + 20),
                    font_size=32,
                    color="white",
                    max_width=badge_width - 40,
                    font_style=fontStyle,
                    bold=True,
                    shadow=False,
                    align="center"
                )

                # Base64 변환
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
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
