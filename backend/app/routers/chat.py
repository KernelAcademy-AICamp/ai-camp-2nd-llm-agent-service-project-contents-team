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
        db.commit()
        logger.debug(f"사용자 메시지 저장 완료 (message_id: {user_message.id})")

        # Gemini 모델 초기화 (시스템 프롬프트 포함)
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=SYSTEM_PROMPT
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
    """
    try:
        logger.info(f"채팅 세션 목록 조회 (user_id: {current_user.id}, limit: {limit}, offset: {offset})")

        # 전체 세션 수 조회
        total = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == current_user.id
        ).count()

        # 세션 조회 (최신순: updated_at 기준 내림차순, NULL은 맨 뒤로)
        sessions = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == current_user.id
        ).order_by(
            models.ChatSession.updated_at.desc().nullslast()
        ).limit(limit).offset(offset).all()

        # 각 세션의 메시지 수 조회 및 데이터 변환
        sessions_data = []
        for session in sessions:
            message_count = db.query(models.ChatMessage).filter(
                models.ChatMessage.session_id == session.id
            ).count()

            sessions_data.append(ChatSessionInfo(
                id=session.id,
                title=session.title or "새 채팅",
                created_at=session.created_at.isoformat() if session.created_at else "",
                updated_at=session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat(),
                message_count=message_count
            ))

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
    """
    try:
        logger.info(f"세션 메시지 조회 (user_id: {current_user.id}, session_id: {session_id})")

        # 세션 소유권 확인
        session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="세션을 찾을 수 없습니다."
            )

        # 전체 메시지 수 조회
        total = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id
        ).count()

        # 메시지 조회 (시간 순서대로)
        messages = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id
        ).order_by(
            models.ChatMessage.created_at.asc()
        ).limit(limit).offset(offset).all()

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
