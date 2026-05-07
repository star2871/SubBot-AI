from llm.ollama_client import ask_llm

# 1. Router
def router_node(state):
    question = state.get("message", "")
    
    if not question.strip():
        return {**state, "category": "unknown"}

    prompt = f"""
    classify this into one word:
    faq, billing, technical, unknown

    question: {question}
    """

    category = ask_llm(prompt)
    
    # 카테고리가 비어있거나 유효하지 않으면 unknown으로 설정
    if not category or category.strip() == "":
        category = "unknown"
    else:
        category = category.lower().strip()
    
    # 유효한 카테고리만 허용
    valid_categories = ["faq", "billing", "technical", "unknown"]
    if category not in valid_categories:
        category = "unknown"

    return {**state, "category": category}


# 2. FAQ
def faq_node(state):
    question = state.get("message", "")
    
    if not question.strip():
        return {**state, "answer": "질문을 입력해주세요.", "confidence": 0.5}
    
    # 답변 스크립트 사용 (간단한 버전)
    from answer_scripts_simple import answer_scripts
    
    # 스크립트 기반 답변 생성
    response_data = answer_scripts.get_response(question)
    
    if response_data["confidence"] > 0.7:  # 신뢰도 높은 답변 우선
        # 대화 내용 저장
        from conversation_db import conv_db
        conv_db.save_conversation(
            user_message=question,
            bot_response=response_data["answer"],
            category=response_data["category"],
            confidence=response_data["confidence"]
        )
        
        return {
            **state,
            "answer": response_data["answer"],
            "category": response_data["category"],
            "confidence": response_data["confidence"],
            "template_used": response_data.get("template_used", "none")
        }
    
    # 이전 대화 내용에서 유사한 질문 검색 (무한 루프 방지)
    from conversation_db import conv_db
    
    # 현재 질문과 마지막 저장된 질문 비교 (무한 루프 방지)
    recent_conversations = conv_db.get_recent_conversations(limit=5)
    
    # 무한 루프 감지: 현재 질문이 최근 질문과 동일하면 캐시 사용 안함
    current_question = question.strip().lower()
    should_use_cache = True
    
    for conv in recent_conversations:
        if conv['user_message'].strip().lower() == current_question:
            should_use_cache = False
            print(f"🚫 무한 루프 감지: 현재 질문과 이전 질문 동일 - 캐시 사용 안함")
            break
    
    if should_use_cache:
        similar_conversations = conv_db.find_similar_conversations(question, limit=3)
        
        if similar_conversations and similar_conversations[0]['similarity_score'] > 0.6:  # 유사도 기준 상향
            # 유사한 대화가 있으면 이전 답변 재사용
            similar = similar_conversations[0]
            return {
                **state, 
                "answer": f"이전에 비슷한 질문에 대한 답변을 찾았습니다:\n\n📝 이전 답변:\n{similar['bot_response']}\n\n💡 이 답변이 도움이 되셨나요? 더 궁금한 점이 있으시면 말씀해주세요.", 
                "confidence": similar['confidence'] * 0.9,  # 이전 답변의 신뢰도 약간 낮춤
                "category": similar['category'],
                "from_cache": True
            }

    # 웹 문제 감지 및 검색 연동
    if any(keyword in question.lower() for keyword in ["문제", "오류", "에러", "안돼", "안됨", "고장", "안되", "실패"]):
        # 문제 관련 키워드가 있으면 자동 검색 제안
        problem_keywords = []
        for keyword in ["골드", "메달", "상품", "결제", "주문", "로그인"]:
            if keyword in question:
                problem_keywords.append(keyword)
        
        if problem_keywords:
            # 관련 상품 검색
            from product_db import db
            search_term = problem_keywords[0]
            results = db.search_products(search_term)
            
            if results:
                search_results = f"🔍 '{search_term}' 관련 상품 정보:\n\n" + "\n\n".join(results[:3])
            else:
                search_results = f"'{search_term}' 관련 상품을 찾을 수 없습니다."
            
            # 웹 검색 제안
            web_search_suggestion = f"\n\n🌐 관련 문제를 웹에서 검색해볼까요? '{question}'에 대한 정보를 찾아드릴게요."
            
            return {
                **state, 
                "answer": f"문제가 발생했군요! 도와드리겠습니다.\n\n{search_results}{web_search_suggestion}", 
                "confidence": 0.8
            }
        else:
            # 일반 웹 검색 제안
            return {
                **state, 
                "answer": f"문제가 발생했군요! '{question}'에 대한 정보를 웹에서 검색해볼까요?", 
                "confidence": 0.7
            }

    # 상품 가격 직접 응답 로직 (우선순위 높음)
    if any(keyword in question for keyword in ["얼마", "가격", "판매가", "비용", "금액"]):
        from product_db import db
        
        # 상품명 추출 - 더 구체적인 패턴으로 검색
        import re
        
        # "2023 계묘년 토끼의 해 카드형 골드 1.87g 얼마야" 같은 패턴에서 상품명 추출
        product_patterns = [
            r'(\d{4}\s*년\s*[\uAC00-\uD7AF]+\s*년\s*[\uAC00-\uD7AF]+\s*의\s*해.*?[\uAC00-\uD7AF]+.*?골드.*?\d+\.?\d*g?)',
            r'([\uAC00-\uD7AF]+\s*메달.*?\d+\.?\d*g?)',
            r'([\uAC00-\uD7AF]+\s*골드.*?\d+\.?\d*g?)',
            r'([\uAC00-\uD7AF]+\s*은.*?\d+\.?\d*g?)',
            r'([\uAC00-\uD7AF]+\s*금.*?\d+\.?\d*g?)',
            r'([\uAC00-\uD7AF]+\s*카드형.*?[\uAC00-\uD7AF]+)',
            r'(\d{4}\s*년.*?[\uAC00-\uD7AF]+)',
            r'([\uAC00-\uD7AF]+\s*바)',
            r'([\uAC00-\uD7AF]+\s*메달)',
            r'([\uAC00-\uD7AF]+\s*코인)'
        ]
        
        matched_product = None
        for pattern in product_patterns:
            match = re.search(pattern, question)
            if match:
                matched_product = match.group(1)
                break
        
        # 패턴 매칭 실패 시 키워드 기반 검색
        if not matched_product:
            # 연도와 동물 조합 찾기
            year_animal_pattern = r'(\d{4})\s*년\s*([\uAC00-\uD7AF]+)'
            year_match = re.search(year_animal_pattern, question)
            if year_match:
                year = year_match.group(1)
                animal = year_match.group(2)
                matched_product = f"{year} {animal}"
            else:
                # 일반 키워드로 상품명 찾기
                for keyword in ["골드", "메달", "은", "금", "토끼", "용", "뱀", "카드형"]:
                    if keyword in question:
                        matched_product = keyword
                        break
        
        if matched_product:
            print(f"💰 상품 가격 검색: '{matched_product}'")
            
            try:
                results = db.search_products(matched_product)
                
                if results:
                    # 가격 정보가 포함된 결과 찾기
                    for result in results:
                        if "판매가" in result or "가격" in result or "원" in result:
                            return {
                                **state, 
                                "answer": f"💰 '{matched_product}'의 가격 정보입니다:\n\n{result}", 
                                "confidence": 0.95
                            }
                    
                    # 가격 정보가 없으면 상품 정보만 제공
                    limited_results = results[:2]
                    answer = f"🔍 '{matched_product}'에 대한 상품 정보입니다:\n\n"
                    answer += "\n\n".join(limited_results)
                    answer += f"\n\n💡 정확한 가격 정보는 위 상품 중 선택하여 말씀해주시면 상세히 안내해드리겠습니다."
                    
                    return {
                        **state, 
                        "answer": answer, 
                        "confidence": 0.9
                    }
                else:
                    return {
                        **state, 
                        "answer": f"죄송하지만 '{matched_product}'에 대한 상품을 찾을 수 없습니다.\n\n💡 팁:\n- '2023 토끼 골드', '은메달', '금바' 등으로 검색해보세요\n- 연도와 동물을 함께 말씀해주시면 더 정확하게 찾을 수 있습니다.", 
                        "confidence": 0.6
                    }
            except Exception as e:
                print(f"❌ 가격 검색 오류: {e}")
                return {
                    **state, 
                    "answer": f"가격 검색 중 오류가 발생했습니다: {str(e)}", 
                    "confidence": 0.3
                }
    
    # 상품 검색 로직 (강화)
    if any(keyword in question for keyword in ["상품", "골드", "메달", "은", "금", "카드형", "토끼", "용", "뱀", "조폐", "한국조폐공사"]):
        from product_db import db
        from conversation_db import conv_db
        
        # 검색 키워드 추출 (우선순위)
        priority_keywords = ["골드", "메달", "은", "금", "카드형", "토끼", "용", "뱀", "조폐", "한국조폐공사", "상품"]
        search_term = None
        
        for keyword in priority_keywords:
            if keyword in question:
                search_term = keyword
                break
        
        # 키워드가 없으면 질문 전체로 검색
        if not search_term:
            search_term = question
        
        print(f"🔍 상품 검색: '{search_term}'")  # 디버깅용
        
        # 이전 상품 검색 기록 확인 (무한 루프 방지)
        recent_conversations = conv_db.get_recent_conversations(limit=3)
        
        # 최근 대화 중 동일한 상품 검색이 있는지 확인
        should_use_cache = True
        for conv in recent_conversations:
            if search_term.lower() in conv['user_message'].lower() and '검색 결과' in conv['bot_response']:
                should_use_cache = False
                print(f"🚫 상품 검색 캐시 방지: 최근에 이미 '{search_term}' 검색함")
                break
        
        if should_use_cache:
            product_history = conv_db.get_product_history(search_term, limit=2)
            
            if product_history:
                # 이전 검색 결과가 있으면 재사용
                history = product_history[0]
                return {
                    **state, 
                    "answer": f"이전에 '{search_term}'에 대해 검색한 기록이 있습니다:\n\n📝 이전 검색 결과:\n{history['bot_response']}\n\n💡 이 정보가 도움이 되셨나요? 더 자세한 정보가 필요하시면 말씀해주세요.", 
                    "confidence": history['confidence'] * 0.9,
                    "category": history['category'],
                    "from_cache": True
                }
        
        try:
            results = db.search_products(search_term)
            
            if results:
                # 결과가 너무 많으면 3개로 제한
                limited_results = results[:3]
                answer = f"🔍 '{search_term}'에 대한 상품 검색 결과입니다 ({len(results)}개 중 {len(limited_results)}개 표시):\n\n"
                answer += "\n\n".join(limited_results)
                
                # 상품 정보 저장
                product_info = {
                    "search_term": search_term,
                    "results_count": len(results),
                    "top_results": limited_results[:2]  # 상위 2개 결과 저장
                }
                
                return {
                    **state, 
                    "answer": answer, 
                    "confidence": 0.9,
                    "product_info": product_info
                }
            else:
                # 대체 검색 시도
                alternative_keywords = ["골드", "메달", "은", "금"]
                for alt_keyword in alternative_keywords:
                    if alt_keyword != search_term:
                        alt_results = db.search_products(alt_keyword)
                        if alt_results:
                            return {
                                **state, 
                                "answer": f"'{search_term}'에 대한 상품을 찾을 수 없습니다. 대신 '{alt_keyword}' 관련 상품을 찾았습니다:\n\n" + "\n\n".join(alt_results[:2]), 
                                "confidence": 0.7
                            }
                
                return {
                    **state, 
                    "answer": f"죄송하지만 '{search_term}'에 대한 상품을 찾을 수 없습니다.\n\n💡 팁:\n- '골드', '메달', '은', '금' 등으로 검색해보세요\n- '토끼', '용', '뱀' 등 연도 동물로 검색해보세요", 
                    "confidence": 0.5
                }
        except Exception as e:
            print(f"❌ 상품 검색 오류: {e}")
            return {
                **state, 
                "answer": f"상품 검색 중 오류가 발생했습니다: {str(e)}", 
                "confidence": 0.3
            }
    
    # 웹 검색 로직 강화
    if "검색" in question or "찾아" in question:
        return {
            **state, 
            "answer": f"'{question}'에 대한 웹 검색을 시작합니다. 관련 정보를 찾아드릴게요.", 
            "confidence": 0.8,
            "trigger_web_search": True  # 웹 검색 트리거 추가
        }
    
    # 간단한 응답 우선 시도
    simple_answers = {
        "안녕": "안녕하세요! 무엇을 도와드릴까요?",
        "hello": "Hello! How can I help you today?",
        "감사": "천만에요! 더 필요한 것이 있으신가요?",
        "thanks": "You're welcome! Is there anything else I can help with?",
        "시간": f"현재 시간은 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} 입니다.",
        "날씨": "죄송하지만 실시간 날씨 정보는 제공할 수 없습니다. 날씨 앱을 확인해주세요.",
        "가격": "가격 정보는 상품별로 다릅니다. 원하시는 상품명을 말씀해주시면 정확한 가격을 안내해드리겠습니다.\n\n💡 예시:\n- '토끼 골드 가격'\n- '은메달 얼마'\n- '금바 가격 알려줘'\n\n📞 가격 문의: 1577-4321",
        "판매가": "판매가 정보는 상품별로 다릅니다. 원하시는 상품명을 말씀해주시면 정확한 판매가를 안내해드리겠습니다.\n\n💡 예시:\n- '토끼 골드 판매가'\n- '은메달 판매가'\n- '금바 판매가 알려줘'\n\n📞 가격 문의: 1577-4321",
        "얼마": "가격 정보는 상품별로 다릅니다. 원하시는 상품명을 말씀해주시면 정확한 가격을 안내해드리겠습니다.\n\n💡 예시:\n- '토끼 골드 얼마'\n- '은메달 얼마'\n- '금바 가격'\n\n📞 가격 문의: 1577-4321",
        "문의": "문의가 접수되었습니다. 상담원이 확인할 예정입니다.\n\n📋 접수 정보:\n✅ 접수 번호: INQ-{__import__('random').randint(10000, 99999)}\n🕐 접수 시간: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n👤 담당자: 자동 배정 중\n\n⏰ 예상 확인 시간:\n- 평일: 1-2시간 내\n- 주말/공휴일: 다음 영업일\n- 긴급 문의: 30분 내 우선 확인\n\n📞 문의 번호: 1577-4321\n📧 이메일: support@subbot.com\n\n💡 현재 진행 상황은 '문의 상태'라고 물어보시면 확인 가능합니다.",
        "접수": "문의가 정상적으로 접수되었습니다. 빠른 시간 내에 상담원이 확인 후 답변드리겠습니다.\n\n📋 접수 정보:\n✅ 접수 번호: INQ-{__import__('random').randint(10000, 99999)}\n🕐 접수 시간: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n👤 담당자: 자동 배정 중\n\n⏰ 예상 응답 시간:\n- 일반 문의: 1-3시간 내\n- 긴급 문의: 30분 내 우선 처리\n- 기술 문의: 기술팀 확인 후 2시간 내\n\n📞 추가 문의: 1577-4321 (내선 3번)\n감사합니다.",
        "상담": "상담원 연결을 준비 중입니다.\n\n⏳ 현재 대기 인원: {__import__('random').randint(1, 5)}명\n⏱️ 예상 대기 시간: {__import__('random').randint(5, 20)}분\n\n잠시만 기다려주시면 친절한 상담으로 연결해드리겠습니다.",
        "오류": "오류를 접수했습니다. 기술지원팀에서 확인 중입니다.\n\n🔧 처리 단계:\n1단계: 오류 접수 완료\n2단계: 기술팀 확인 중 (10-30분)\n3단계: 해결 방안 안내 (30분-2시간)\n\n📞 긴급 기술 지원: 1577-4321 (내선 2번)"
    }
    
    # 간단한 답변 확인
    for key, response in simple_answers.items():
        if key in question.lower():
            return {**state, "answer": response, "confidence": 0.9}
    
    # LLM 응답 시도 (더 짧은 프롬프트)
    answer = ask_llm(f"한 문장으로 답해주세요: {question[:50]}")
    
    if not answer or answer.strip() == "":
        answer = "죄송하지만 답변을 생성할 수 없습니다. 다른 질문을 시도해주세요."

    return {**state, "answer": answer, "confidence": 0.7}


# 3. Billing
def billing_node(state):
    return {
        **state,
        "answer": "결제 관련 문의입니다. 자세한 내용은 계정에서 확인하세요.",
        "confidence": 0.9
    }


# 4. Technical
def technical_node(state):
    question = state.get("message", "")
    
    if not question.strip():
        return {**state, "answer": "기술적 질문을 입력해주세요.", "confidence": 0.5}
    
    answer = ask_llm(f"technical support: {question}")
    
    if not answer or answer.strip() == "":
        answer = "기술 지원 답변을 생성할 수 없습니다."
    
    return {**state, "answer": answer, "confidence": 0.6}


# 5. Ticket
def ticket_node(state):
    return {
        **state,
        "answer": "문의가 접수되었습니다. 상담원이 확인할 예정입니다.",
        "confidence": 1.0
    }