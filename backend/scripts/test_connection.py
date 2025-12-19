"""
데이터베이스 연결 테스트 스크립트
"""
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, DATABASE_URL


def test_connection():
    """
    데이터베이스 연결 테스트
    """
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()

    # 데이터베이스 URL 출력 (비밀번호는 마스킹)
    masked_url = DATABASE_URL
    if "@" in DATABASE_URL:
        parts = DATABASE_URL.split("@")
        user_part = parts[0].split("://")[1].split(":")[0]
        masked_url = DATABASE_URL.replace(
            parts[0].split("://")[1],
            f"{user_part}:****"
        )

    print(f"📍 Database URL: {masked_url}")
    print()

    db = SessionLocal()
    try:
        print("🔄 Connecting to database...")

        # 1. 버전 확인
        result = db.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print("✅ Connection successful!")
        print(f"   PostgreSQL Version: {version[:50]}...")
        print()

        # 2. 현재 데이터베이스 이름
        result = db.execute(text('SELECT current_database();'))
        db_name = result.fetchone()[0]
        print(f"📁 Current database: {db_name}")
        print()

        # 3. 테이블 목록
        result = db.execute(text("""
            SELECT
                table_name,
                (SELECT COUNT(*)
                 FROM information_schema.columns
                 WHERE columns.table_name = tables.table_name
                 AND columns.table_schema = 'public') as column_count
            FROM information_schema.tables tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = result.fetchall()
        if tables:
            print(f"📋 Tables ({len(tables)}):")
            for table_name, col_count in tables:
                print(f"   ├─ {table_name} ({col_count} columns)")
        else:
            print("ℹ️  No tables found (database is empty)")
        print()

        # 4. 연결 정보
        result = db.execute(text("""
            SELECT
                client_addr as ip,
                datname as database,
                usename as user,
                application_name,
                state
            FROM pg_stat_activity
            WHERE pid = pg_backend_pid()
        """))

        conn_info = result.fetchone()
        if conn_info:
            print("🔗 Connection details:")
            print(f"   ├─ IP: {conn_info[0] or 'localhost'}")
            print(f"   ├─ Database: {conn_info[1]}")
            print(f"   ├─ User: {conn_info[2]}")
            print(f"   ├─ Application: {conn_info[3]}")
            print(f"   └─ State: {conn_info[4]}")
        print()

        # 5. 데이터베이스 크기
        result = db.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """))
        db_size = result.fetchone()[0]
        print(f"💾 Database size: {db_size}")
        print()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Connection test failed!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("💡 Troubleshooting tips:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Verify Supabase project is running")
        print("   3. Confirm database name exists")
        print("   4. Verify username and password")
        print()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    test_connection()
