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
        
        # 가격 관련 질문
        if any(keyword in question_lower for keyword in ['가격', '얼마', '비용', '가격이', '가격']):
            return self._get_price_response(question)
        
        # 상품 관련 질문
        elif any(keyword in question_lower for keyword in ['상품', '제품', '아이템']):
            return self._get_product_response(question)
        
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
        """가격 답변 (기본 안내)"""
        answer = """💰 상품 가격 문의

죄송합니다. 현재 상품 가격 정보 검색 기능은 준비 중입니다.

📞 고객센터: 1577-4321
📧 이메일: support@subbot.com
🕐 운영시간: 평일 09:00-18:00

직접 문의하시면 상세한 가격 정보를 안내해드리겠습니다."""
        
        return {
            "answer": answer,
            "category": "price",
            "confidence": 0.8,
            "template_used": "price_basic"
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
