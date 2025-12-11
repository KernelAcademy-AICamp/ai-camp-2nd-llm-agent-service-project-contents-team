"""
published_contents 테이블에 uploaded_image_url 컬럼 추가
- Instagram 발행 시 직접 업로드한 이미지 URL 저장을 위한 컬럼
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """uploaded_image_url 컬럼 추가"""

    with engine.connect() as conn:
        # uploaded_image_url 컬럼 추가
        conn.execute(text("""
            ALTER TABLE published_contents
            ADD COLUMN IF NOT EXISTS uploaded_image_url VARCHAR(500)
        """))

        print("uploaded_image_url 컬럼 추가 완료")

        conn.commit()

    print("\n마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
