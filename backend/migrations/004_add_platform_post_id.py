"""
published_contents 테이블에 platform_post_id 컬럼 추가
- X 발행 시 post_id 저장을 위한 컬럼
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """platform_post_id 컬럼 추가"""

    with engine.connect() as conn:
        # platform_post_id 컬럼 추가
        conn.execute(text("""
            ALTER TABLE published_contents
            ADD COLUMN IF NOT EXISTS platform_post_id VARCHAR(100)
        """))

        print("platform_post_id 컬럼 추가 완료")

        conn.commit()

    print("\n마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
