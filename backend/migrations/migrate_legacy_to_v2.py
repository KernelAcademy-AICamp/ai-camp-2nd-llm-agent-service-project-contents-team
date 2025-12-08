"""
레거시 ai_generated_contents 테이블 데이터를 v2 구조로 마이그레이션

- ai_generated_contents → content_generation_sessions + 플랫폼별 테이블
- 마이그레이션 후 레거시 테이블 데이터 삭제
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import (
    AIGeneratedContent,
    ContentGenerationSession,
    GeneratedBlogContent,
    GeneratedSNSContent,
    GeneratedXContent,
    GeneratedThreadsContent,
    GeneratedImage
)


def migrate_legacy_to_v2():
    """레거시 데이터를 v2 구조로 마이그레이션"""

    db = SessionLocal()

    try:
        # 1. 레거시 데이터 조회
        legacy_contents = db.query(AIGeneratedContent).all()

        if not legacy_contents:
            print("📭 마이그레이션할 레거시 데이터가 없습니다.")
            return

        print(f"📦 마이그레이션 대상: {len(legacy_contents)}개 레코드")

        migrated_count = 0
        error_count = 0

        for legacy in legacy_contents:
            try:
                # 2. 선택된 플랫폼 추정 (데이터 유무로 판단)
                selected_platforms = []
                if legacy.blog_content:
                    selected_platforms.append("blog")
                if legacy.sns_content:
                    selected_platforms.append("sns")
                if legacy.x_content:
                    selected_platforms.append("x")
                if legacy.threads_content:
                    selected_platforms.append("threads")

                # 플랫폼이 하나도 없으면 기본값
                if not selected_platforms:
                    selected_platforms = ["blog", "sns"]

                # 3. 콘텐츠 타입 추정
                has_text = bool(legacy.blog_content or legacy.sns_content)
                has_images = bool(legacy.generated_image_urls and len(legacy.generated_image_urls) > 0)

                if has_text and has_images:
                    content_type = "both"
                elif has_images:
                    content_type = "image"
                else:
                    content_type = "text"

                # 4. 세션 생성
                session = ContentGenerationSession(
                    user_id=legacy.user_id,
                    topic=legacy.input_text or legacy.blog_title or "주제 없음",
                    content_type=content_type,
                    style="casual",  # 레거시에는 스타일 정보가 없으므로 기본값
                    selected_platforms=selected_platforms,
                    analysis_data=legacy.analysis_data,
                    critique_data=legacy.critique_data,
                    generation_attempts=legacy.generation_attempts or 1,
                    status=legacy.status or "generated",
                    created_at=legacy.created_at
                )
                db.add(session)
                db.flush()  # session.id 생성

                # 5. 블로그 콘텐츠 마이그레이션
                if legacy.blog_content:
                    blog = GeneratedBlogContent(
                        session_id=session.id,
                        user_id=legacy.user_id,
                        title=legacy.blog_title or "제목 없음",
                        content=legacy.blog_content,
                        tags=legacy.blog_tags,
                        score=legacy.blog_score,
                        created_at=legacy.created_at
                    )
                    db.add(blog)

                # 6. SNS 콘텐츠 마이그레이션
                if legacy.sns_content:
                    sns = GeneratedSNSContent(
                        session_id=session.id,
                        user_id=legacy.user_id,
                        content=legacy.sns_content,
                        hashtags=legacy.sns_hashtags,
                        score=legacy.sns_score,
                        created_at=legacy.created_at
                    )
                    db.add(sns)

                # 7. X 콘텐츠 마이그레이션
                if legacy.x_content:
                    x = GeneratedXContent(
                        session_id=session.id,
                        user_id=legacy.user_id,
                        content=legacy.x_content,
                        hashtags=legacy.x_hashtags,
                        score=None,  # 레거시에는 X 점수가 없음
                        created_at=legacy.created_at
                    )
                    db.add(x)

                # 8. Threads 콘텐츠 마이그레이션
                if legacy.threads_content:
                    threads = GeneratedThreadsContent(
                        session_id=session.id,
                        user_id=legacy.user_id,
                        content=legacy.threads_content,
                        hashtags=legacy.threads_hashtags,
                        score=None,  # 레거시에는 Threads 점수가 없음
                        created_at=legacy.created_at
                    )
                    db.add(threads)

                # 9. 이미지 마이그레이션
                if legacy.generated_image_urls:
                    for url in legacy.generated_image_urls:
                        image = GeneratedImage(
                            session_id=session.id,
                            user_id=legacy.user_id,
                            image_url=url,
                            prompt=legacy.input_text,
                            created_at=legacy.created_at
                        )
                        db.add(image)

                migrated_count += 1
                print(f"  ✅ ID {legacy.id} 마이그레이션 완료 → Session ID {session.id}")

            except Exception as e:
                error_count += 1
                print(f"  ❌ ID {legacy.id} 마이그레이션 실패: {e}")
                continue

        # 10. 커밋
        db.commit()
        print(f"\n📊 마이그레이션 결과: 성공 {migrated_count}개, 실패 {error_count}개")

        # 11. 레거시 데이터 삭제 확인
        if migrated_count > 0:
            confirm = input("\n🗑️  레거시 데이터를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == "yes":
                deleted_count = db.query(AIGeneratedContent).delete()
                db.commit()
                print(f"✅ 레거시 데이터 {deleted_count}개 삭제 완료")
            else:
                print("⏭️  레거시 데이터 삭제를 건너뛰었습니다.")

        print("\n🎉 마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        print(f"❌ 마이그레이션 중 오류 발생: {e}")
        raise
    finally:
        db.close()


def delete_legacy_data_only():
    """레거시 데이터만 삭제 (이미 마이그레이션된 경우)"""
    db = SessionLocal()

    try:
        count = db.query(AIGeneratedContent).count()
        if count == 0:
            print("📭 삭제할 레거시 데이터가 없습니다.")
            return

        print(f"🗑️  삭제 대상: {count}개 레코드")
        confirm = input("정말 삭제하시겠습니까? (yes/no): ")

        if confirm.lower() == "yes":
            deleted_count = db.query(AIGeneratedContent).delete()
            db.commit()
            print(f"✅ 레거시 데이터 {deleted_count}개 삭제 완료")
        else:
            print("⏭️  삭제를 취소했습니다.")

    except Exception as e:
        db.rollback()
        print(f"❌ 삭제 중 오류 발생: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="레거시 데이터 마이그레이션")
    parser.add_argument("--delete-only", action="store_true", help="레거시 데이터만 삭제")
    args = parser.parse_args()

    if args.delete_only:
        delete_legacy_data_only()
    else:
        migrate_legacy_to_v2()
