#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
상품 정보 챗봇 - shop.db에서 직접 데이터 조회 (LLM 없음)
"""

import sqlite3
import pandas as pd
import os
from typing import Dict, List

class DirectProductChatBot:
    def __init__(self):
        # shop.db 연결 (절대 경로 사용)
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "shop.db")
        self.conn = sqlite3.connect(db_path)
        self._cache = {}  # 검색 결과 캐시
    
    def get_product_info(self, product_name: str) -> str:
        """상품명으로 관련 정보 검색"""
        try:
            # 키워드 분리 검색
            keywords = product_name.split()
            
            all_results = []
            for keyword in keywords:
                if len(keyword.strip()) > 0:
                    query = """
                        SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재 
                        FROM products 
                        WHERE 상품명 LIKE ? 
                        AND [ 판매가 ] IS NOT NULL 
                        AND CAST([ 판매가 ] AS INTEGER) > 0
                        ORDER BY CAST([ 판매가 ] AS INTEGER) DESC
                        LIMIT 3
                    """
                    
                    df = pd.read_sql(query, self.conn, params=[f"%{keyword.strip()}%"])
                    if len(df) > 0:
                        all_results.extend(df.to_dict('records'))
            
            # 중복 제거
            unique_results = []
            seen_names = set()
            for item in all_results:
                if item['상품명'] not in seen_names:
                    unique_results.append(item)
                    seen_names.add(item['상품명'])
            
            if unique_results:
                df_result = pd.DataFrame(unique_results[:5])
                return self._format_product_response(df_result, product_name)
            else:
                return self._no_product_response(product_name)
                
        except Exception as e:
            return f"오류 발생: {e}"
    
    def _format_product_response(self, df: pd.DataFrame, search_term: str) -> str:
        """상품 정보 응답 포맷팅"""
        response = f"🔍 '{search_term}' 관련 상품 정보입니다:\n\n"
        
        for idx, row in df.iterrows():
            response += f"📦 {idx+1}. {row['상품명']}\n"
            response += f"   💰 가격: {row['판매가']:,}원\n"
            response += f"   ⚖️  중량: {row['중량']}g\n"
            response += f"   🏷️  소재: {row['소재']}\n\n"
        
        response += f"💡 더 자세한 정보는 문의해주세요.\n"
        response += f"📞 고객센터: 1577-4321"
        
        return response
    
    def _no_product_response(self, product_name: str) -> str:
        """상품이 없을 때 응답"""
        return f"""❌ '{product_name}'에 대한 상품을 찾을 수 없습니다.

💡 검색 팁:
• 정확한 상품명 입력 (예: '토끼 골드', '은메달')
• 연도 포함 검색 (예: '2023 골드', '2024 메달')
• 소재로 검색 (예: '금바', '은메달', '골드바')

📞 직접 문의: 1577-4321
📧 이메일: support@subbot.com"""


📞 고객센터: 1577-4321"""
        
        # 상품 검색
        products = self._search_products(product_name)
        
        if not products:
            return f"""❌ '{product_name}' 상품을 찾을 수 없습니다.

💡 검색 팁:
• '토끼 골드', '은메달', '금바' 등으로 검색
• 연도 포함: '2023 골드', '2024 메달'

📞 직접 문의: 1577-4321"""
        
        # 가격 정보 포맷팅
        response = f"💰 '{product_name}' 관련 상품 가격 정보:\n\n"
        
        for i, product in enumerate(products[:5], 1):
            response += f"📦 {i}. {product['상품명']}\n"
            response += f"   💵 가격: {product['판매가']:,}원\n"
            response += f"   ⚖️  중량: {product['중량']}g\n"
            response += f"   🏷️  소재: {product['소재']}\n\n"
        
        response += f"💡 더 자세한 정보는 문의해주세요.\n"
        response += f"📞 고객센터: 1577-4321"
        
        return response
    
    def _get_product_response(self, query: str) -> str:
        """상품 정보 응답"""
        product_name = self._extract_product_name(query)
        
        if not product_name:
            return """📦 상품 정보 문의

찾으시는 상품명을 말씀해주세요.

💡 예시:
• '토끼 골드 정보'
• '은메달 상품'
• '2023 금바'

📞 고객센터: 1577-4321"""
        
        products = self._search_products(product_name)
        
        if not products:
            return f"""❌ '{product_name}' 상품을 찾을 수 없습니다.

💡 검색 팁:
• '토끼', '골드', '메달', '은', '금' 등 키워드로 검색
• 연도와 동물: '2023 토끼', '2024 용'

📞 직접 문의: 1577-4321"""
        
        response = f"📦 '{product_name}' 관련 상품 정보:\n\n"
        
        for i, product in enumerate(products[:3], 1):
            response += f"📦 {i}. {product['상품명']}\n"
            response += f"   💰 가격: {product['판매가']:,}원\n"
            response += f"   ⚖️  중량: {product['중량']}g\n"
            response += f"   🏷️  소재: {product['소재']}\n"
            response += f"   📐 규격: {product.get('규격', '정보 없음')}\n\n"
        
        response += f"💡 더 자세한 정보는 문의해주세요.\n"
        response += f"📞 고객센터: 1577-4321"
        
        return response
    
        
    def _search_products(self, product_name: str) -> List[Dict]:
        """상품 검색 (캐시 사용)"""
        if product_name in self._cache:
            return self._cache[product_name]
        
        try:
            query = """
                SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
                FROM products 
                WHERE 상품명 LIKE ? 
                AND [ 판매가 ] IS NOT NULL 
                AND CAST([ 판매가 ] AS INTEGER) > 0
                ORDER BY CAST([ 판매가 ] AS INTEGER) DESC
                LIMIT 10
            """
            
            df = pd.read_sql(query, self.conn, params=[f"%{product_name}%"])
            
            if len(df) > 0:
                results = df.to_dict('records')
                self._cache[product_name] = results
                return results
            
            return []
            
        except Exception as e:
            print(f"검색 오류: {e}")
            return []
    
    def _get_greeting_response(self) -> str:
        """인사 응답"""
        return """👋 안녕하세요! 상품 정보 챗봇입니다.

무엇을 도와드릴까요?

💡 질문 예시:
• '토끼 골드 가격'
• '은메달 정보'
• '2023 금바'

📞 고객센터: 1577-4321"""
    
    def _get_default_response(self, query: str) -> str:
        """기본 응답"""
        return f"""❓ '{query}'에 대한 응답을 찾을 수 없습니다.

💡 도움이 필요하시면:
• 상품명 + '가격' 또는 '정보'로 질문
• '토끼 골드 가격'처럼 구체적으로 질문

📞 직접 문의: 1577-4321
📧 이메일: support@subbot.com"""

# 전역 인스턴스
product_chatbot = DirectProductChatBot()
