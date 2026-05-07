import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class ConversationDatabase:
    def __init__(self):
        self.conn = sqlite3.connect("conversations.db")
        self._init_database()
    
    def _init_database(self):
        """대화 데이터베이스 초기화"""
        cursor = self.conn.cursor()
        
        # 대화 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                category TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                product_info TEXT  -- 상품 정보 JSON 저장
            )
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON conversations(category)")
        
        self.conn.commit()
    
    def save_conversation(self, user_message: str, bot_response: str, 
                       category: str = None, confidence: float = None, 
                       session_id: str = None, product_info: Dict = None):
        """대화 내용 저장"""
        cursor = self.conn.cursor()
        
        # 상품 정보를 JSON으로 저장
        product_json = json.dumps(product_info) if product_info else None
        
        cursor.execute("""
            INSERT INTO conversations 
            (user_message, bot_response, category, confidence, session_id, product_info)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_message, bot_response, category, confidence, session_id, product_json))
        
        self.conn.commit()
    
    def get_recent_conversations(self, limit: int = 10, session_id: str = None) -> List[Dict]:
        """최근 대화 내용 조회"""
        cursor = self.conn.cursor()
        
        if session_id:
            cursor.execute("""
                SELECT user_message, bot_response, category, confidence, timestamp, product_info
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, limit))
        else:
            cursor.execute("""
                SELECT user_message, bot_response, category, confidence, timestamp, product_info
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        results = cursor.fetchall()
        conversations = []
        
        for row in results:
            user_msg, bot_resp, category, confidence, timestamp, product_info = row
            
            # 상품 정보 JSON 파싱
            product_data = json.loads(product_info) if product_info else None
            
            conversations.append({
                'user_message': user_msg,
                'bot_response': bot_resp,
                'category': category,
                'confidence': confidence,
                'timestamp': timestamp,
                'product_info': product_data
            })
        
        return conversations
    
    def find_similar_conversations(self, user_message: str, limit: int = 5) -> List[Dict]:
        """유사한 대화 내용 검색"""
        cursor = self.conn.cursor()
        
        # 키워드 기반 검색
        keywords = user_message.split()
        if not keywords:
            return []
        
        # 각 키워드에 대해 검색
        similar_conversations = []
        for keyword in keywords[:3]:  # 최대 3개 키워드만
            cursor.execute("""
                SELECT user_message, bot_response, category, confidence, timestamp, product_info
                FROM conversations 
                WHERE user_message LIKE ? OR bot_response LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))
            
            results = cursor.fetchall()
            for row in results:
                user_msg, bot_resp, category, confidence, timestamp, product_info = row
                
                # 상품 정보 JSON 파싱
                product_data = json.loads(product_info) if product_info else None
                
                similar_conversations.append({
                    'user_message': user_msg,
                    'bot_response': bot_resp,
                    'category': category,
                    'confidence': confidence,
                    'timestamp': timestamp,
                    'product_info': product_data,
                    'similarity_score': self._calculate_similarity(user_message, user_msg)
                })
        
        # 유사도 순으로 정렬
        similar_conversations.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_conversations[:limit]
    
    def _calculate_similarity(self, msg1: str, msg2: str) -> float:
        """메시지 유사도 계산"""
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_product_history(self, product_name: str, limit: int = 5) -> List[Dict]:
        """특정 상품 관련 대화 기록 조회"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT user_message, bot_response, category, confidence, timestamp, product_info
            FROM conversations 
            WHERE user_message LIKE ? OR bot_response LIKE ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (f"%{product_name}%", f"%{product_name}%", limit))
        
        results = cursor.fetchall()
        conversations = []
        
        for row in results:
            user_msg, bot_resp, category, confidence, timestamp, product_info = row
            
            # 상품 정보 JSON 파싱
            product_data = json.loads(product_info) if product_info else None
            
            conversations.append({
                'user_message': user_msg,
                'bot_response': bot_resp,
                'category': category,
                'confidence': confidence,
                'timestamp': timestamp,
                'product_info': product_data
            })
        
        return conversations
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()

# 전역 대화 데이터베이스 인스턴스
conv_db = ConversationDatabase()
