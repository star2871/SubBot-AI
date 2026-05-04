from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255))
    status = Column(String(50), default='active')
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender_type = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    route = Column(String(50), default='unknown')  # faq, billing, technical, unknown
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    tickets = relationship("Ticket", back_populates="message")

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=True)
    summary = Column(Text)
    status = Column(String(50), default='open')  # open, in_progress, closed, resolved
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="tickets")
    message = relationship("Message", back_populates="tickets")

class FagDocument(Base):
    __tablename__ = 'fag_documents'
    
    fag_documents_id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100))
    source = Column(String(255))
    language = Column(String(10), default='ko')
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    chunks = relationship("FagChunk", back_populates="document", cascade="all, delete-orphan")

class FagChunk(Base):
    __tablename__ = 'fag_chunks'
    
    id = Column(Integer, primary_key=True)
    fag_documents_id = Column(Integer, ForeignKey('fag_documents.fag_documents_id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_vector_id = Column(String(255))  # 벡터 DB의 ID 참조
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    document = relationship("FagDocument", back_populates="chunks")

# 데이터베이스 연결 설정
DATABASE_URL = "postgresql://username:password@localhost/subbot_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
