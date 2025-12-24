"""
템플릿 갤러리 API 라우터
- 사용자별 탭/템플릿 CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import User, TemplateTab, Template
from ..auth import get_current_user

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ============================================
# Pydantic Schemas
# ============================================

class TabCreate(BaseModel):
    label: str
    icon: str = "📁"

class TabUpdate(BaseModel):
    label: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None

class TabResponse(BaseModel):
    id: int
    tab_key: str
    label: str
    icon: str
    sort_order: int
    template_count: int = 0

    class Config:
        from_attributes = True

class TemplateCreate(BaseModel):
    tab_id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    prompt: str
    icon: str = "📝"

class TemplateUpdate(BaseModel):
    tab_id: Optional[int] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    icon: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    tab_id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    prompt: str
    icon: str
    uses: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# 기본 탭/템플릿 초기화 함수
# ============================================

def initialize_default_tabs_and_templates(db: Session, user_id: int):
    """신규 사용자를 위한 기본 탭과 템플릿 생성"""

    default_tabs = [
        {"tab_key": "promotion", "label": "홍보", "icon": "🎯", "sort_order": 0},
        {"tab_key": "event", "label": "이벤트", "icon": "🎉", "sort_order": 1},
        {"tab_key": "menu", "label": "메뉴", "icon": "🍽️", "sort_order": 2},
        {"tab_key": "info", "label": "정보", "icon": "💡", "sort_order": 3},
        {"tab_key": "how_to", "label": "하우투", "icon": "📝", "sort_order": 4},
    ]

    created_tabs = {}
    for tab_data in default_tabs:
        tab = TemplateTab(user_id=user_id, **tab_data)
        db.add(tab)
        db.flush()
        created_tabs[tab_data["tab_key"]] = tab.id

    default_templates = [
        # 홍보 템플릿
        {"tab_key": "promotion", "name": "신제품 출시 홍보", "category": "신제품 출시", "icon": "🎯",
         "prompt": "제품명: {product}\n핵심 특징: {features}\n타겟 고객: {target}\n\n위 신제품을 매력적으로 홍보해주세요.",
         "description": "AIDA 구조의 신제품 출시 홍보"},
        {"tab_key": "promotion", "name": "할인 프로모션", "category": "할인 프로모션", "icon": "💎",
         "prompt": "프로모션 내용: {promotion}\n할인율: {discount}\n기간: {period}\n\n긴급성과 희소성을 강조하여 즉각적인 행동을 유도하는 프로모션 카드뉴스를 만들어주세요.",
         "description": "긴박감을 주는 할인 프로모션"},
        {"tab_key": "promotion", "name": "브랜드 스토리", "category": "브랜드 홍보", "icon": "🌟",
         "prompt": "브랜드명: {brand}\n핵심 가치: {values}\n창업 스토리: {story}\n\n브랜드의 철학과 가치를 감성적으로 전달하는 스토리텔링 콘텐츠를 만들어주세요.",
         "description": "감성적인 브랜드 스토리텔링"},

        # 이벤트 템플릿
        {"tab_key": "event", "name": "오픈 이벤트", "category": "오프닝 이벤트", "icon": "🎉",
         "prompt": "매장/서비스명: {name}\n오픈 일시: {datetime}\n장소: {location}\n오픈 혜택: {benefits}\n\n오픈을 축하하는 특별 이벤트를 5W1H 구조로 안내해주세요.",
         "description": "오픈 기념 특별 이벤트 안내"},
        {"tab_key": "event", "name": "시즌 이벤트", "category": "시즌 이벤트", "icon": "🎊",
         "prompt": "시즌: {season}\n이벤트 내용: {content}\n참여 방법: {how_to_join}\n경품: {prizes}\n\n시즌의 분위기를 살려 참여 욕구를 높이는 이벤트 카드뉴스를 만들어주세요.",
         "description": "시즌 맞춤 이벤트 홍보"},
        {"tab_key": "event", "name": "SNS 이벤트", "category": "온라인 이벤트", "icon": "🎁",
         "prompt": "이벤트명: {event_name}\n참여 방법: {how_to}\n해시태그: {hashtag}\n경품: {prizes}\n\nSNS 바이럴을 유도하는 재미있는 온라인 이벤트를 안내해주세요.",
         "description": "SNS 바이럴 이벤트"},

        # 메뉴 템플릿
        {"tab_key": "menu", "name": "신메뉴 소개", "category": "신메뉴 소개", "icon": "🍽️",
         "prompt": "메뉴명: {menu_name}\n주재료: {ingredients}\n가격: {price}\n맛 특징: {taste}\n\n새로운 메뉴의 맛과 특징을 감각적으로 묘사하여 식욕을 자극하는 카드뉴스를 만들어주세요.",
         "description": "감각적인 신메뉴 소개"},
        {"tab_key": "menu", "name": "시그니처 메뉴", "category": "시그니처 메뉴", "icon": "☕",
         "prompt": "메뉴명: {menu_name}\n탄생 스토리: {story}\n추천 포인트: {points}\n\n대표 메뉴의 특별함을 스토리텔링으로 전달해주세요.",
         "description": "시그니처 메뉴 스토리텔링"},
        {"tab_key": "menu", "name": "베스트 메뉴 TOP", "category": "베스트 메뉴", "icon": "🍕",
         "prompt": "메뉴 순위: {ranking}\n각 메뉴 특징: {features}\n\n고객들이 가장 사랑하는 인기 메뉴를 순위별로 소개하는 카드뉴스를 만들어주세요.",
         "description": "인기 메뉴 랭킹"},

        # 정보 템플릿
        {"tab_key": "info", "name": "정보 공유", "category": "정보 공유", "icon": "💡",
         "prompt": "주제: {topic}\n핵심 정보: {key_info}\n타겟: {target}\n\n타겟 고객에게 유용한 정보를 알기 쉽게 전달하는 카드뉴스를 만들어주세요.",
         "description": "유용한 정보 공유 콘텐츠"},
        {"tab_key": "info", "name": "FAQ 정리", "category": "Q&A", "icon": "💬",
         "prompt": "주제: {topic}\n자주 묻는 질문들: {questions}\n\n고객들이 자주 묻는 질문과 답변을 명확하게 정리한 카드뉴스를 만들어주세요.",
         "description": "자주 묻는 질문 정리"},
        {"tab_key": "info", "name": "용어 설명", "category": "정보 공유", "icon": "📋",
         "prompt": "용어: {term}\n쉬운 설명: {explanation}\n예시: {example}\n\n어려운 전문 용어를 누구나 이해할 수 있게 쉽게 설명하는 카드뉴스를 만들어주세요.",
         "description": "전문 용어 쉽게 풀기"},

        # 하우투 템플릿
        {"tab_key": "how_to", "name": "사용법 가이드", "category": "사용법 가이드", "icon": "📝",
         "prompt": "제품/서비스명: {name}\n주요 기능: {features}\n타겟 사용자: {target}\n\n초보자도 쉽게 따라할 수 있는 단계별 사용 가이드를 만들어주세요.",
         "description": "단계별 사용법 가이드"},
        {"tab_key": "how_to", "name": "꿀팁 모음", "category": "꿀팁 모음", "icon": "🔧",
         "prompt": "주제: {topic}\n핵심 팁 5가지: {tips}\n\n실생활에 바로 적용할 수 있는 실용적인 꿀팁을 정리해주세요.",
         "description": "실용적인 꿀팁 모음"},
        {"tab_key": "how_to", "name": "문제 해결 가이드", "category": "단계별 설명", "icon": "📌",
         "prompt": "문제 상황: {problem}\n원인: {cause}\n해결 방법: {solution}\n\n자주 발생하는 문제의 해결 방법을 단계별로 안내하는 카드뉴스를 만들어주세요.",
         "description": "문제 해결 단계별 가이드"},
    ]

    for tmpl_data in default_templates:
        tab_key = tmpl_data.pop("tab_key")
        tab_id = created_tabs.get(tab_key)
        if tab_id:
            template = Template(user_id=user_id, tab_id=tab_id, **tmpl_data)
            db.add(template)

    db.commit()


# ============================================
# 탭 API
# ============================================

@router.get("/tabs", response_model=List[TabResponse])
async def get_tabs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 탭 목록 조회 (템플릿 개수 포함)"""
    # 탭이 없으면 기본 탭/템플릿 초기화
    tabs = db.query(TemplateTab).filter(
        TemplateTab.user_id == current_user.id
    ).order_by(TemplateTab.sort_order).all()

    if not tabs:
        initialize_default_tabs_and_templates(db, current_user.id)
        tabs = db.query(TemplateTab).filter(
            TemplateTab.user_id == current_user.id
        ).order_by(TemplateTab.sort_order).all()

    # 각 탭의 템플릿 개수 계산
    result = []
    for tab in tabs:
        template_count = db.query(func.count(Template.id)).filter(
            Template.tab_id == tab.id
        ).scalar()
        result.append(TabResponse(
            id=tab.id,
            tab_key=tab.tab_key,
            label=tab.label,
            icon=tab.icon,
            sort_order=tab.sort_order,
            template_count=template_count
        ))

    return result


@router.post("/tabs", response_model=TabResponse)
async def create_tab(
    tab_data: TabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 탭 생성"""
    # 정렬 순서 계산
    max_order = db.query(func.max(TemplateTab.sort_order)).filter(
        TemplateTab.user_id == current_user.id
    ).scalar() or -1

    # tab_key 생성 (label 기반 + timestamp)
    import time
    tab_key = f"{tab_data.label.lower().replace(' ', '_')}_{int(time.time())}"

    tab = TemplateTab(
        user_id=current_user.id,
        tab_key=tab_key,
        label=tab_data.label,
        icon=tab_data.icon,
        sort_order=max_order + 1
    )
    db.add(tab)
    db.commit()
    db.refresh(tab)

    return TabResponse(
        id=tab.id,
        tab_key=tab.tab_key,
        label=tab.label,
        icon=tab.icon,
        sort_order=tab.sort_order,
        template_count=0
    )


@router.put("/tabs/{tab_id}", response_model=TabResponse)
async def update_tab(
    tab_id: int,
    tab_data: TabUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """탭 수정"""
    tab = db.query(TemplateTab).filter(
        TemplateTab.id == tab_id,
        TemplateTab.user_id == current_user.id
    ).first()

    if not tab:
        raise HTTPException(status_code=404, detail="탭을 찾을 수 없습니다")

    if tab_data.label is not None:
        tab.label = tab_data.label
    if tab_data.icon is not None:
        tab.icon = tab_data.icon
    if tab_data.sort_order is not None:
        tab.sort_order = tab_data.sort_order

    db.commit()
    db.refresh(tab)

    template_count = db.query(func.count(Template.id)).filter(
        Template.tab_id == tab.id
    ).scalar()

    return TabResponse(
        id=tab.id,
        tab_key=tab.tab_key,
        label=tab.label,
        icon=tab.icon,
        sort_order=tab.sort_order,
        template_count=template_count
    )


@router.delete("/tabs/{tab_id}")
async def delete_tab(
    tab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """탭 삭제 (해당 탭의 템플릿도 함께 삭제)"""
    tab = db.query(TemplateTab).filter(
        TemplateTab.id == tab_id,
        TemplateTab.user_id == current_user.id
    ).first()

    if not tab:
        raise HTTPException(status_code=404, detail="탭을 찾을 수 없습니다")

    db.delete(tab)
    db.commit()

    return {"message": "탭이 삭제되었습니다"}


# ============================================
# 템플릿 API
# ============================================

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    tab_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 목록 조회 (탭별 필터링 가능)"""
    # 탭이 없으면 기본 탭/템플릿 초기화
    tabs = db.query(TemplateTab).filter(
        TemplateTab.user_id == current_user.id
    ).first()

    if not tabs:
        initialize_default_tabs_and_templates(db, current_user.id)

    query = db.query(Template).filter(Template.user_id == current_user.id)

    if tab_id:
        query = query.filter(Template.tab_id == tab_id)

    templates = query.order_by(Template.created_at.desc()).all()
    return templates


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 템플릿 생성"""
    # 탭 존재 확인
    tab = db.query(TemplateTab).filter(
        TemplateTab.id == template_data.tab_id,
        TemplateTab.user_id == current_user.id
    ).first()

    if not tab:
        raise HTTPException(status_code=404, detail="탭을 찾을 수 없습니다")

    template = Template(
        user_id=current_user.id,
        tab_id=template_data.tab_id,
        name=template_data.name,
        category=template_data.category,
        description=template_data.description,
        prompt=template_data.prompt,
        icon=template_data.icon
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 상세 조회"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")

    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 수정"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")

    # 탭 변경 시 탭 존재 확인
    if template_data.tab_id is not None:
        tab = db.query(TemplateTab).filter(
            TemplateTab.id == template_data.tab_id,
            TemplateTab.user_id == current_user.id
        ).first()
        if not tab:
            raise HTTPException(status_code=404, detail="탭을 찾을 수 없습니다")
        template.tab_id = template_data.tab_id

    if template_data.name is not None:
        template.name = template_data.name
    if template_data.category is not None:
        template.category = template_data.category
    if template_data.description is not None:
        template.description = template_data.description
    if template_data.prompt is not None:
        template.prompt = template_data.prompt
    if template_data.icon is not None:
        template.icon = template_data.icon

    db.commit()
    db.refresh(template)

    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 삭제"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")

    db.delete(template)
    db.commit()

    return {"message": "템플릿이 삭제되었습니다"}


@router.post("/{template_id}/use", response_model=TemplateResponse)
async def use_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 사용 (사용 횟수 증가)"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")

    template.uses = (template.uses or 0) + 1
    db.commit()
    db.refresh(template)

    return template


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """템플릿 복제"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")

    duplicated = Template(
        user_id=current_user.id,
        tab_id=template.tab_id,
        name=f"{template.name} (복사본)",
        category=template.category,
        description=template.description,
        prompt=template.prompt,
        icon=template.icon,
        uses=0
    )
    db.add(duplicated)
    db.commit()
    db.refresh(duplicated)

    return duplicated
