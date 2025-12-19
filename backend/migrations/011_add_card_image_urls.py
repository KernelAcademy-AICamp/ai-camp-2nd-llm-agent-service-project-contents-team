"""
published_contents 테이블에 card_image_urls 컬럼 추가
- 카드뉴스 이미지 URL 배열 저장을 위한 JSON 컬럼
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """card_image_urls 컬럼 추가"""

    with engine.connect() as conn:
        # card_image_urls 컬럼 추가 (JSON 타입)
        conn.execute(text("""
            ALTER TABLE published_contents
            ADD COLUMN IF NOT EXISTS card_image_urls JSON
        """))

        print("card_image_urls 컬럼 추가 완료")

        conn.commit()

    print("\n마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
