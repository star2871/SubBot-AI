# 데이터베이스 설정 파일
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base

# 데이터베이스 URL 설정 (개발용 SQLite)
# 실제 운영에서는 PostgreSQL 사용 권장
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./subbot.db")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """데이터베이스 세션을 가져오는 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블이 생성되었습니다.")

# PostgreSQL 설정 예시
# DATABASE_URL = "postgresql://username:password@localhost/subbot_db"
