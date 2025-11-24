"""
PostgreSQL 데이터베이스 마이그레이션 스크립트
"""
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app import models  # 모든 모델 import


def create_tables():
    """
    모든 테이블 생성
    """
    print("🔄 Creating tables in PostgreSQL...")

    try:
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")

        # 생성된 테이블 목록 출력
        print("\n📋 Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


def verify_connection():
    """
    데이터베이스 연결 확인
    """
    from sqlalchemy import text
    from app.database import SessionLocal

    print("🔍 Verifying database connection...")

    db = SessionLocal()
    try:
        # PostgreSQL 버전 확인
        result = db.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print(f"✅ Connected to PostgreSQL!")
        print(f"   Version: {version}\n")

        # 기존 테이블 확인
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result.fetchall()]
        if tables:
            print("📋 Existing tables:")
            for table in tables:
                print(f"  - {table}")
        else:
            print("ℹ️  No existing tables found")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    finally:
        db.close()


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("PostgreSQL Migration Tool")
    print("=" * 60)
    print()

    # 1. 연결 확인
    verify_connection()
    print()

    # 2. 테이블 생성 확인
    response = input("Do you want to create tables? (yes/no): ").lower()
    if response in ['yes', 'y']:
        create_tables()
        print()
        print("✅ Migration completed successfully!")
    else:
        print("ℹ️  Migration cancelled")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
