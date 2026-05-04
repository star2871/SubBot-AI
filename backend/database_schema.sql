-- SubBot 데이터베이스 스키마
-- PostgreSQL 기준 DDL

-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,  -- OAuth 제공자의 고유 ID (Google, etc.)
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 대화 테이블
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',  -- active, archived, etc.
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL
);

-- 메시지 테이블
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    route VARCHAR(50) DEFAULT 'unknown' CHECK (route IN ('faq', 'billing', 'technical', 'unknown')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 티켓 테이블
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    summary TEXT,
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'closed', 'resolved')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ 문서 테이블
CREATE TABLE fag_documents (
    fag_documents_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    source VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ko',
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ 청크 테이블 (문서를 작은 조각으로 나눈 테이블)
CREATE TABLE fag_chunks (
    id SERIAL PRIMARY KEY,
    fag_documents_id INTEGER REFERENCES fag_documents(fag_documents_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_vector_id VARCHAR(255),  -- 벡터 DB의 ID 참조
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fag_documents_id, chunk_index)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_sender_type ON messages(sender_type);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_tickets_conversation_id ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_fag_documents_category ON fag_documents(category);
CREATE INDEX idx_fag_documents_language ON fag_documents(language);
CREATE INDEX idx_fag_chunks_document_id ON fag_chunks(fag_documents_id);

-- 트리거 생성 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fag_documents_updated_at BEFORE UPDATE ON fag_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 초기 데이터 삽입 (예시)
INSERT INTO users (external_id, name, email, role) VALUES 
('google_123456', '관리자', 'admin@subbot.ai', 'admin');

INSERT INTO fag_documents (title, category, source, language, raw_text) VALUES 
('SubBot 소개', 'general', 'manual', 'ko', 'SubBot은 AI 기반 챗봇 서비스입니다.'),
('계정 관리', 'account', 'manual', 'ko', '사용자는 회원가입을 통해 계정을 생성할 수 있습니다.'),
('결제 문의', 'billing', 'manual', 'ko', '결제 관련 문의는 티켓을 통해 처리됩니다.');
