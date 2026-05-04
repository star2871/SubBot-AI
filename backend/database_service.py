# 데이터베이스 서비스 레이어
from sqlalchemy.orm import Session
from database_models import User, Conversation, Message, Ticket, FagDocument, FagChunk
from database_config import get_db
from datetime import datetime
from typing import Optional, List

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, external_id: str, name: str, email: str, role: str = 'user') -> User:
        """사용자 생성"""
        user = User(
            external_id=external_id,
            name=name,
            email=email,
            role=role
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_external_id(self, external_id: str) -> Optional[User]:
        """외부 ID로 사용자 조회 (OAuth용)"""
        return self.db.query(User).filter(User.external_id == external_id).first()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """사용자 정보 업데이트"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user

class ConversationService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        """대화 생성"""
        conversation = Conversation(
            user_id=user_id,
            title=title or "새 대화",
            status='active'
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_user_conversations(self, user_id: int) -> List[Conversation]:
        """사용자의 대화 목록 조회"""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.started_at.desc()).all()
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """대화 조회"""
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def end_conversation(self, conversation_id: int) -> bool:
        """대화 종료"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.ended_at = datetime.utcnow()
            conversation.status = 'archived'
            self.db.commit()
            return True
        return False

class MessageService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(self, conversation_id: int, user_id: int, 
                    sender_type: str, content: str, route: str = 'unknown') -> Message:
        """메시지 생성"""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            sender_type=sender_type,
            content=content,
            route=route
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """대화의 메시지 목록 조회"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
    
    def get_user_messages(self, user_id: int, limit: int = 50) -> List[Message]:
        """사용자의 메시지 목록 조회"""
        return self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

class TicketService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_ticket(self, user_id: int, conversation_id: int, 
                    message_id: int = None, summary: str = None,
                    priority: str = 'medium') -> Ticket:
        """티켓 생성"""
        ticket = Ticket(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            summary=summary,
            priority=priority,
            status='open'
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
    
    def get_user_tickets(self, user_id: int) -> List[Ticket]:
        """사용자의 티켓 목록 조회"""
        return self.db.query(Ticket).filter(
            Ticket.user_id == user_id
        ).order_by(Ticket.created_at.desc()).all()
    
    def update_ticket_status(self, ticket_id: int, status: str) -> bool:
        """티켓 상태 업데이트"""
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            ticket.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

class FAQService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(self, title: str, raw_text: str, 
                      category: str = None, source: str = None,
                      language: str = 'ko') -> FagDocument:
        """FAQ 문서 생성"""
        document = FagDocument(
            title=title,
            raw_text=raw_text,
            category=category,
            source=source,
            language=language
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def create_chunk(self, document_id: int, chunk_index: int, 
                   content: str, embedding_vector_id: str = None) -> FagChunk:
        """FAQ 청크 생성"""
        chunk = FagChunk(
            fag_documents_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding_vector_id=embedding_vector_id
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk
    
    def get_documents_by_category(self, category: str) -> List[FagDocument]:
        """카테고리별 FAQ 문서 조회"""
        return self.db.query(FagDocument).filter(
            FagDocument.category == category
        ).all()
    
    def search_documents(self, keyword: str) -> List[FagDocument]:
        """키워드로 FAQ 문서 검색"""
        return self.db.query(FagDocument).filter(
            FagDocument.raw_text.ilike(f'%{keyword}%')
        ).all()

# 서비스 팩토리 함수
def get_user_service(db: Session) -> UserService:
    return UserService(db)

def get_conversation_service(db: Session) -> ConversationService:
    return ConversationService(db)

def get_message_service(db: Session) -> MessageService:
    return MessageService(db)

def get_ticket_service(db: Session) -> TicketService:
    return TicketService(db)

def get_faq_service(db: Session) -> FAQService:
    return FAQService(db)
