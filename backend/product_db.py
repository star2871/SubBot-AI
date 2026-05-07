import sqlite3
import pandas as pd
import os

class ProductDatabase:
    def __init__(self):
        # 절대 경로 사용
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "shop.db")
        
        try:
            self.conn = sqlite3.connect(db_path)
            print(f"✅ 데이터베이스 연결 성공: {db_path}")
            self._init_database()
        except Exception as e:
            print(f"❌ 데이터베이스 연결 오류: {e}")
            raise Exception("shop.db 파일을 찾을 수 없거나 연결할 수 없습니다.")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        cursor = self.conn.cursor()
        
        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                일련번호 INTEGER,
                상품명 TEXT,
                중량 REAL,
                판매가 INTEGER,
                소재 TEXT,
                규격 TEXT,
                구성 TEXT,
                상품정보고시 TEXT
            )
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON products(상품명)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_material ON products(소재)")
        
        self.conn.commit()
    
    def search_products(self, keyword):
        """상품명으로 검색 (딕셔너리 리스트 반환)"""
        cursor = self.conn.cursor()
        
        # 상품명, 소재, 구성에서 키워드 검색
        query = """
            SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
            FROM products 
            WHERE 상품명 LIKE ? OR 소재 LIKE ? OR 구성 LIKE ?
            ORDER BY 
                CASE 
                    WHEN 상품명 LIKE ? THEN 1
                    WHEN 소재 LIKE ? THEN 2
                    WHEN 구성 LIKE ? THEN 3
                    ELSE 4
                END,
                [ 판매가 ] ASC
            LIMIT 10
        """
        
        search_pattern = f"%{keyword}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, 
                         search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        
        if not results:
            return []
        
        # 결과 포맷팅 (딕셔너리 리스트)
        formatted_results = []
        for row in results:
            상품명, 중량, 판매가, 소재, 규격, 구성 = row
            
            formatted_result = {
                "상품명": 상품명,
                "중량": 중량,
                "판매가": 판매가,
                "소재": 소재,
                "규격": 규격,
                "구성": 구성
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def get_product_by_name(self, product_name):
        """상품명으로 정확히 검색"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성, 상품정보고시
            FROM products 
            WHERE 상품명 = ?
            LIMIT 1
        """
        
        cursor.execute(query, (product_name,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        상품명, 중량, 판매가, 소재, 규격, 구성, 상품정보고시 = result
        
        return {
            "상품명": 상품명,
            "중량": 중량,
            "판매가": 판매가,
            "소재": 소재,
            "규격": 규격,
            "구성": 구성,
            "상품정보고시": 상품정보고시
        }
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()

# 전역 데이터베이스 인스턴스
db = ProductDatabase()
