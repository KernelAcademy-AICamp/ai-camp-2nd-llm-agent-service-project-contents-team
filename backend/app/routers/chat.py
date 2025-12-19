from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path
from datetime import datetime, timezone
import google.generativeai as genai
from ..logger import get_logger
from ..database import get_db
from .. import models, auth

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["chat"]
)

# Gemini 설정
GEMINI_API_KEY = os.getenv('REACT_APP_GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 시스템 프롬프트 로드
def load_system_prompt() -> str:
    """
    시스템 프롬프트 파일을 읽어옵니다.
    """
    prompt_file = Path(__file__).parent.parent / "system_prompts" / "chat_assistant.txt"
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.warning(f"시스템 프롬프트 파일을 찾을 수 없습니다: {prompt_file}")
        return "당신은 콘텐츠 크리에이터 서비스의 친절한 AI 어시스턴트입니다."
    except Exception as e:
        logger.error(f"시스템 프롬프트 로드 실패: {e}", exc_info=True)
        return "당신은 콘텐츠 크리에이터 서비스의 친절한 AI 어시스턴트입니다."

SYSTEM_PROMPT = load_system_prompt()
logger.info(f"시스템 프롬프트 로드 완료 ({len(SYSTEM_PROMPT)} 글자)")


def build_user_context(user: models.User, db: Session) -> str:
    """
    사용자 프로필 및 활동 정보를 기반으로 컨텍스트 문자열 생성
    """
    context_parts = ["\n\n## 현재 대화 중인 사용자 정보"]

    # 기본 프로필 정보
    context_parts.append(f"- **이름**: {user.username}")
    if user.full_name:
        context_parts.append(f"- **전체 이름**: {user.full_name}")
    context_parts.append(f"- **이메일**: {user.email}")

    # 비즈니스 정보
    if user.brand_name or user.business_type or user.business_description:
        context_parts.append("\n### 비즈니스 정보")
        if user.brand_name:
            context_parts.append(f"- **브랜드명**: {user.brand_name}")
        if user.business_type:
            context_parts.append(f"- **업종**: {user.business_type}")
        if user.business_description:
            context_parts.append(f"- **비즈니스 설명**: {user.business_description}")

    # 타겟 고객 정보
    if user.target_audience:
        context_parts.append("\n### 타겟 고객")
        target = user.target_audience
        if isinstance(target, dict):
            if target.get('age_range'):
                context_parts.append(f"- **연령대**: {target['age_range']}")
            if target.get('gender'):
                context_parts.append(f"- **성별**: {target['gender']}")
            if target.get('interests'):
                interests = ", ".join(target['interests']) if isinstance(target['interests'], list) else target['interests']
                context_parts.append(f"- **관심사**: {interests}")

    # 온보딩 상태
    if not user.onboarding_completed:
        context_parts.append("\n⚠️ **참고**: 사용자가 아직 온보딩을 완료하지 않았습니다. 필요시 온보딩 완료를 권장해주세요.")

    # 활동 통계
    try:
        # 채팅 세션 수
        chat_count = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == user.id
        ).count()

        # 콘텐츠 수
        content_count = db.query(models.Content).filter(
            models.Content.user_id == user.id
        ).count()

        # 동영상 수
        video_count = db.query(models.Video).filter(
            models.Video.user_id == user.id
        ).count()

        if chat_count > 0 or content_count > 0 or video_count > 0:
            context_parts.append("\n### 서비스 활동 내역")
            if chat_count > 0:
                context_parts.append(f"- **채팅 세션**: {chat_count}개")
            if content_count > 0:
                context_parts.append(f"- **생성한 콘텐츠**: {content_count}개")
            if video_count > 0:
                context_parts.append(f"- **생성한 동영상**: {video_count}개")
    except Exception as e:
        logger.warning(f"사용자 활동 통계 조회 실패: {e}")

    # 브랜드 분석 정보
    try:
        brand_analysis = db.query(models.BrandAnalysis).filter(
            models.BrandAnalysis.user_id == user.id
        ).first()

        if brand_analysis:
            context_parts.append("\n### 브랜드 분석 정보")
            if brand_analysis.brand_tone:
                context_parts.append(f"- **브랜드 톤앤매너**: {brand_analysis.brand_tone}")
            if brand_analysis.brand_personality:
                context_parts.append(f"- **브랜드 성격**: {brand_analysis.brand_personality}")
            if brand_analysis.emotional_tone:
                context_parts.append(f"- **감정적 톤**: {brand_analysis.emotional_tone}")

            # 플랫폼별 분석 상태
            platforms = []
            if brand_analysis.blog_analysis_status == "completed":
                platforms.append("블로그")
            if brand_analysis.instagram_analysis_status == "completed":
                platforms.append("인스타그램")
            if brand_analysis.youtube_analysis_status == "completed":
                platforms.append("유튜브")

            if platforms:
                context_parts.append(f"- **분석 완료 플랫폼**: {', '.join(platforms)}")
    except Exception as e:
        logger.warning(f"브랜드 분석 정보 조회 실패: {e}")

    context_parts.append("\n**중요**: 위 정보를 바탕으로 사용자에게 맞춤형 답변을 제공하세요. 사용자의 비즈니스와 상황에 맞는 구체적인 조언을 해주세요.")

    return "\n".join(context_parts)


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None  # None이면 새 세션 생성
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    session_id: int


class ChatHistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryMessage]
    total: int


class ChatSessionInfo(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionInfo]
    total: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    AI 챗봇 엔드포인트
    사용자 메시지와 대화 히스토리를 받아서 AI 응답 생성
    유저별로 대화 내역을 데이터베이스에 저장
    세션이 없으면 새로 생성
    """
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Gemini API 키가 설정되지 않았습니다."
            )

        logger.info(f"채팅 요청 수신 (user_id: {current_user.id}): {request.message[:50]}...")

        # 세션 처리: 없으면 새로 생성
        if request.session_id:
            # 기존 세션 확인
            session = db.query(models.ChatSession).filter(
                models.ChatSession.id == request.session_id,
                models.ChatSession.user_id == current_user.id
            ).first()

            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="세션을 찾을 수 없습니다."
                )

            # 세션 업데이트 시간 갱신
            session.updated_at = datetime.now(timezone.utc)
            logger.debug(f"기존 세션 사용 (session_id: {session.id})")
        else:
            # 새 세션 생성 (제목은 첫 메시지 앞 30자)
            session_title = request.message[:30] + ("..." if len(request.message) > 30 else "")
            session = models.ChatSession(
                user_id=current_user.id,
                title=session_title
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"새 세션 생성 (session_id: {session.id}, title: {session_title})")

        # 사용자 메시지 DB에 저장
        user_message = models.ChatMessage(
            user_id=current_user.id,
            session_id=session.id,
            role="user",
            content=request.message,
            model="gemini-2.0-flash-exp"
        )
        db.add(user_message)
        # 세션의 updated_at 변경사항도 함께 커밋
        db.add(session)
        db.commit()
        logger.debug(f"사용자 메시지 저장 완료 (message_id: {user_message.id})")

        # 사용자 컨텍스트 생성
        user_context = build_user_context(current_user, db)
        personalized_prompt = f"{SYSTEM_PROMPT}{user_context}"

        logger.debug(f"개인화된 시스템 프롬프트 생성 완료 ({len(personalized_prompt)} 글자)")

        # Gemini 모델 초기화 (개인화된 시스템 프롬프트 포함)
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=personalized_prompt
        )

        # 대화 히스토리를 Gemini 형식으로 변환
        chat_history = []
        for msg in request.history:
            chat_history.append({
                'role': 'user' if msg.role == 'user' else 'model',
                'parts': [msg.content]
            })

        # 채팅 세션 시작 (히스토리 포함)
        chat = model.start_chat(history=chat_history)

        # 응답 생성
        response = chat.send_message(request.message)

        logger.info(f"AI 응답 생성 완료: {len(response.text)} 글자")

        # AI 응답 DB에 저장
        ai_message = models.ChatMessage(
            user_id=current_user.id,
            session_id=session.id,
            role="assistant",
            content=response.text,
            model="gemini-2.0-flash-exp"
        )
        db.add(ai_message)
        db.commit()
        logger.debug(f"AI 응답 저장 완료 (message_id: {ai_message.id})")

        return ChatResponse(response=response.text, session_id=session.id)

    except Exception as e:
        logger.error(f"채팅 처리 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    현재 로그인한 사용자의 채팅 세션 목록 조회
    최신 순으로 정렬 (updated_at 기준)
    단일 쿼리로 최적화 (JOIN 사용)
    """
    try:
        logger.info(f"채팅 세션 목록 조회 (user_id: {current_user.id}, limit: {limit}, offset: {offset})")

        # 전체 세션 수 조회
        total = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == current_user.id
        ).count()

        # 세션 조회와 메시지 수를 한 번에 (subquery 사용으로 N+1 문제 해결)
        from sqlalchemy import func, select

        # 메시지 수를 계산하는 서브쿼리
        message_count_subq = (
            db.query(
                models.ChatMessage.session_id,
                func.count(models.ChatMessage.id).label('message_count')
            )
            .group_by(models.ChatMessage.session_id)
            .subquery()
        )

        # 세션과 메시지 수를 조인하여 한 번에 조회
        sessions_with_count = (
            db.query(
                models.ChatSession,
                func.coalesce(message_count_subq.c.message_count, 0).label('message_count')
            )
            .outerjoin(message_count_subq, models.ChatSession.id == message_count_subq.c.session_id)
            .filter(models.ChatSession.user_id == current_user.id)
            .order_by(models.ChatSession.updated_at.desc().nullslast())
            .limit(limit)
            .offset(offset)
            .all()
        )

        # 데이터 변환
        sessions_data = [
            ChatSessionInfo(
                id=session.id,
                title=session.title or "새 채팅",
                created_at=session.created_at.isoformat() if session.created_at else "",
                updated_at=session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat(),
                message_count=message_count
            )
            for session, message_count in sessions_with_count
        ]

        logger.info(f"채팅 세션 목록 조회 완료 (total: {total}, returned: {len(sessions_data)})")

        return ChatSessionListResponse(sessions=sessions_data, total=total)

    except Exception as e:
        logger.error(f"채팅 세션 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"채팅 세션 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/chat/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_session_messages(
    session_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    특정 세션의 메시지 조회
    시간 순으로 정렬 (created_at 오름차순)
    최적화: 세션 소유권 확인과 메시지 조회를 한 쿼리로 통합
    """
    try:
        logger.info(f"세션 메시지 조회 (user_id: {current_user.id}, session_id: {session_id}, limit: {limit})")

        # 메시지 조회 시 세션 소유권도 함께 확인 (JOIN 사용)
        messages = (
            db.query(models.ChatMessage)
            .join(models.ChatSession)
            .filter(
                models.ChatMessage.session_id == session_id,
                models.ChatSession.user_id == current_user.id
            )
            .order_by(models.ChatMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        if not messages and offset == 0:
            # 메시지가 없으면 세션이 없거나 권한이 없음
            session_exists = db.query(models.ChatSession).filter(
                models.ChatSession.id == session_id,
                models.ChatSession.user_id == current_user.id
            ).first()
            if not session_exists:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

        # 최신순으로 조회했으므로 역순으로 정렬 (오래된 메시지가 먼저)
        messages = list(reversed(messages))
        total = len(messages)  # limit 적용된 결과 수만 반환

        # created_at을 문자열로 변환
        messages_data = [
            ChatHistoryMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                model=msg.model,
                created_at=msg.created_at.isoformat() if msg.created_at else ""
            )
            for msg in messages
        ]

        logger.info(f"세션 메시지 조회 완료 (total: {total}, returned: {len(messages_data)})")

        return ChatHistoryResponse(messages=messages_data, total=total)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 메시지 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"세션 메시지 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    채팅 세션 삭제
    세션과 관련된 모든 메시지도 함께 삭제됩니다.
    """
    try:
        logger.info(f"채팅 세션 삭제 요청 (user_id: {current_user.id}, session_id: {session_id})")

        # 세션 조회 및 소유권 확인
        session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

        # 관련 메시지 먼저 삭제
        deleted_messages = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id
        ).delete()

        # 세션 삭제
        db.delete(session)
        db.commit()

        logger.info(f"채팅 세션 삭제 완료 (session_id: {session_id}, deleted_messages: {deleted_messages})")

        return {"message": "세션이 삭제되었습니다.", "deleted_messages": deleted_messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 세션 삭제 실패: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"세션 삭제 중 오류가 발생했습니다: {str(e)}"
        )
