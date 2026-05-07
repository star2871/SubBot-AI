#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
간단한 답변 스크립트 - 기본 대화 기능만 유지
"""

import re
from datetime import datetime
from typing import Dict, Optional

class AnswerScripts:
    def __init__(self):
        pass
    
    def get_response(self, question: str) -> Dict:
        """질문에 대한 답변 생성"""
        question_lower = question.lower()
        
        # 상품 키워드가 포함된 질문은 무조건 가격/상품 검색
        product_keywords = ['상품', '골드', '메달', '은', '금', '카드형', '토끼', '용', '뱀', '조폐', '한국조폐공사', '가격', '얼마', '판매가', '비용', '금액', '바']
        
        if any(keyword in question_lower for keyword in product_keywords):
            return self._get_price_response(question)
        
        # 인사
        elif any(keyword in question_lower for keyword in ['안녕', '반가워', '하이', '헬로']):
            return self._get_greeting_response()
        
        # 시간/날씨
        elif any(keyword in question_lower for keyword in ['시간', '날씨', '몇 시', '지금']):
            return self._get_time_weather_response()
        
        # 기본 응답
        else:
            return self._get_default_response(question)
    
    def _get_price_response(self, question: str) -> Dict:
        """가격 답변 (실제 상품 검색)"""
        try:
            from product_db import db
            
            # 키워드 분리 검색
            keywords = question.split()
            all_results = []
            
            for keyword in keywords:
                if len(keyword.strip()) > 0:
                    results = db.search_products(keyword.strip())
                    if results:
                        all_results.extend(results)
            
            # 중복 제거
            unique_results = []
            seen_names = set()
            for item in all_results:
                if item['상품명'] not in seen_names:
                    unique_results.append(item)
                    seen_names.add(item['상품명'])
            
            if unique_results:
                # 가격 정보가 포함된 결과만 필터링
                price_results = [r for r in unique_results if '판매가' in str(r) and r['판매가'] > 0]
                if price_results:
                    answer = f"💰 '{question}' 관련 상품 가격 정보:\n\n"
                    for i, product in enumerate(price_results[:3], 1):
                        answer += f"📦 {i}. {product['상품명']}\n"
                        answer += f"   💵 가격: {product['판매가']:,}원\n"
                        answer += f"   ⚖️  중량: {product['중량']}g\n"
                        answer += f"   🏷️  소재: {product['소재']}\n\n"
                    
                    return {
                        "answer": answer,
                        "category": "price",
                        "confidence": 0.9,
                        "template_used": "price_search"
                    }
            
            # 검색 결과가 없을 때 기본 응답
            answer = f"""💰 가격 문의

'{question}'에 대한 상품을 찾을 수 없습니다.

💡 검색 팁:
• '토끼 골드', '은메달', '금바' 등으로 검색해보세요
• 연도 포함: '2023 골드', '2024 메달'

📞 직접 문의: 1577-4321
📧 이메일: support@subbot.com"""
            
            return {
                "answer": answer,
                "category": "price", 
                "confidence": 0.6,
                "template_used": "price_not_found"
            }
            
        except Exception as e:
            return {
                "answer": f"가격 검색 중 오류 발생: {str(e)}",
                "category": "price",
                "confidence": 0.3,
                "template_used": "price_error"
            }
    
    def _get_product_response(self, question: str) -> Dict:
        """상품 정보 답변 (기본 안내)"""
        answer = """📦 상품 정보 문의

죄송합니다. 현재 상품 정보 검색 기능은 준비 중입니다.

📞 고객센터: 1577-4321
📧 이메일: support@subbot.com
🕐 운영시간: 평일 09:00-18:00

직접 문의하시면 상세한 상품 정보를 안내해드리겠습니다."""
        
        return {
            "answer": answer,
            "category": "product",
            "confidence": 0.8,
            "template_used": "product_basic"
        }
    
    def _get_greeting_response(self) -> Dict:
        """인사 답변"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            greeting = "좋은 아침입니다!"
        elif 12 <= hour < 18:
            greeting = "좋은 오후입니다!"
        else:
            greeting = "좋은 저녁입니다!"
        
        answer = f"""{greeting}

저는 SubBot 고객센터 챗봇입니다.
무엇을 도와드릴까요?

📞 문의전화: 1577-4321
📧 이메일: support@subbot.com"""
        
        return {
            "answer": answer,
            "category": "greeting",
            "confidence": 0.9,
            "template_used": "greeting"
        }
    
    def _get_time_weather_response(self) -> Dict:
        """시간/날씨 답변"""
        now = datetime.now()
        time_str = now.strftime("%Y년 %m월 %d일 %H:%M:%S")
        weekday = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][now.weekday()]
        
        answer = f"""📅 현재 시간 정보

🕐 현재 시간: {time_str}
📅 요일: {weekday}

날씨 정보는 현재 제공되지 않습니다.
다른 문의사항이 있으시면 말씀해주세요."""
        
        return {
            "answer": answer,
            "category": "time_weather",
            "confidence": 0.9,
            "template_used": "time_weather"
        }
    
    def _get_default_response(self, question: str) -> Dict:
        """기본 응답"""
        answer = """🤔 죄송합니다. 질문을 이해하지 못했어요.

도와드릴 수 있는 내용:
- 상품 가격 문의
- 상품 정보 문의
- 고객센터 연결
- 기본 안내

📞 고객센터: 1577-4321
📧 이메일: support@subbot.com

더 자세한 도움이 필요하시면 직접 문의해주세요."""
        
        return {
            "answer": answer,
            "category": "unknown",
            "confidence": 0.3,
            "template_used": "default"
        }

# 전역 인스턴스
answer_scripts = AnswerScripts()
