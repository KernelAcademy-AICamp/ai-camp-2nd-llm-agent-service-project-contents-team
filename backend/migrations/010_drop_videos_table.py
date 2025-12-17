"""
videos 테이블 삭제
- 레거시 Video 모델 사용하지 않음
- 현재 VideoGenerationJob, GeneratedVideo 모델만 사용 중
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """videos 테이블 삭제"""

    with engine.connect() as conn:
        try:
            conn.execute(text("""
                DROP TABLE IF EXISTS videos CASCADE
            """))
            print("✅ videos 테이블 삭제 완료")
        except Exception as e:
            print(f"⚠️ videos 테이블 삭제 실패: {e}")

        conn.commit()

    print("\n🎉 마이그레이션 완료!")
    print("삭제된 테이블: videos")


if __name__ == "__main__":
    run_migration()
