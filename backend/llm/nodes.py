from llm.ollama_client import ask_llm

# 1. Router
def router_node(state):
    question = state.get("message", "")
    
    if not question.strip():
        return {**state, "category": "unknown"}

    # 상품 관련 키워드 먼저 확인
    product_keywords = ["상품", "골드", "메달", "은", "금", "카드형", "토끼", "용", "뱀", "조폐", "한국조폐공사", "가격", "얼마", "판매가", "비용", "금액"]
    
    # 상품 관련 질문이면 faq로 분류
    if any(keyword in question for keyword in product_keywords):
        return {**state, "category": "faq"}
    
    # 기타 분류를 위한 LLM 호출
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
    import sqlite3
    import os
    import re
    
    question = state.get("message", "")
    
    if not question.strip():
        return {**state, "answer": "질문을 입력해주세요.", "confidence": 0.5}
    
    # 상품 키워드 확인
    product_keywords = ['상품', '골드', '메달', '은', '금', '카드형', '토끼', '용', '뱀', '조폐', '한국조폐공사', '가격', '얼마', '판매가', '비용', '금액', '바']
    
    if any(keyword in question.lower() for keyword in product_keywords):
        try:
            # 직접 SQL 검색 (main.py /chat과 동일 로직)
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "shop.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query_text = question.strip()
            
            # 질문어 제거
            clean_query = re.sub(r'(?<=[가-힣])(은|는|이|가|을|를|에|의|로|으로|와|과|도|만|까지|부터|에게|께|한테|처럼|보다|마다|말고|커녕)(?![가-힣])', '', query_text)
            clean_query = re.sub(r'(얼마(야|예요|에요|인가|인가요|일까요|죠|니까)?|가격(은|이)?|정보(를|를|은)?|알려(줘|주세요|드려요)?|찾아(줘|주세요)?|검색(해|해줘)?|해(줘|주세요)?)', '', clean_query)
            clean_query = re.sub(r'(은요|는요|이에요|예요|인가요|일까요|까요|해줘|해주세요|주세요|드려요|입니다|입니까|하나요|되나요)', '', clean_query)
            clean_query = re.sub(r'[?.,!…]+$', '', clean_query).strip()
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()
            
            remove_words = ['가격', '얼마', '정보', '알려', '찾아', '검색', '해줘', '해주세요', '주세요', '드려요', '은', '는', '이', '가']
            for word in remove_words:
                clean_query = clean_query.replace(word, '').strip()
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()
            
            normalized_query = re.sub(r'\s+', ' ', query_text.strip())
            normalized_clean = re.sub(r'\s+', ' ', clean_query.strip())
            
            # 1. 정확한 상품명 검색
            exact_result = None
            for search_text in [normalized_query, query_text, normalized_clean, clean_query]:
                if search_text and search_text.strip():
                    cursor.execute("""
                        SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
                        FROM products 
                        WHERE 상품명 = ?
                        AND [ 판매가 ] IS NOT NULL 
                        AND CAST([ 판매가 ] AS INTEGER) > 0
                    """, (search_text.strip(),))
                    exact_result = cursor.fetchone()
                    if exact_result:
                        break
            
            if exact_result:
                상품명, 중량, 판매가, 소재, 규격, 구성 = exact_result
                answer = f"📦 상품 정보:\n\n"
                answer += f"상품명: {상품명}\n"
                answer += f"💰 가격: {판매가:,}원\n"
                answer += f"⚖️  중량: {중량}g\n"
                answer += f"🏷️  소재: {소재}\n\n"
                answer += f"📞 고객센터: 1577-4321"
                conn.close()
                return {**state, "answer": answer, "category": "product", "confidence": 0.95}
            
            # 2. 키워드 AND 검색
            search_keywords = []
            for k in normalized_clean.split():
                k = k.strip()
                if len(k) >= 2 and not k.isdigit():
                    search_keywords.append(k)
            
            if search_keywords:
                conditions = " AND ".join(["상품명 LIKE ?"] * len(search_keywords))
                query = f"""
                    SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
                    FROM products 
                    WHERE {conditions}
                    AND [ 판매가 ] IS NOT NULL 
                    AND CAST([ 판매가 ] AS INTEGER) > 0
                    ORDER BY CAST([ 판매가 ] AS INTEGER) ASC
                    LIMIT 5
                """
                params = [f"%{k}%" for k in search_keywords]
                cursor.execute(query, params)
                and_results = cursor.fetchall()
                
                if and_results:
                    if len(and_results) == 1:
                        상품명, 중량, 판매가, 소재, 규격, 구성 = and_results[0]
                        answer = f"📦 상품 정보:\n\n"
                        answer += f"상품명: {상품명}\n"
                        answer += f"💰 가격: {판매가:,}원\n"
                        answer += f"⚖️  중량: {중량}g\n"
                        answer += f"🏷️  소재: {소재}\n\n"
                        answer += f"📞 고객센터: 1577-4321"
                    else:
                        answer = f"🔍 '{question}' 검색 결과 ({len(and_results)}개):\n\n"
                        for i, row in enumerate(and_results, 1):
                            상품명, 중량, 판매가, 소재, 규격, 구성 = row
                            answer += f"📦 {i}. {상품명}\n"
                            answer += f"   💵 가격: {판매가:,}원\n"
                            answer += f"   ⚖️  중량: {중량}g\n"
                            answer += f"   🏷️  소재: {소재}\n\n"
                        answer += f"📞 고객센터: 1577-4321"
                    
                    conn.close()
                    return {**state, "answer": answer, "category": "product", "confidence": 0.9}
            
            # 3. OR 검색 (fallback)
            or_keywords = [k for k in normalized_clean.split() if len(k.strip()) >= 3 and not k.strip().isdigit()]
            if not or_keywords:
                or_keywords = [k for k in normalized_clean.split() if len(k.strip()) >= 2 and not k.strip().isdigit()]
            
            if or_keywords:
                or_conditions = " OR ".join(["상품명 LIKE ?"] * len(or_keywords))
                or_query = f"""
                    SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
                    FROM products 
                    WHERE ({or_conditions})
                    AND [ 판매가 ] IS NOT NULL 
                    AND CAST([ 판매가 ] AS INTEGER) > 0
                    ORDER BY CAST([ 판매가 ] AS INTEGER) ASC
                    LIMIT 5
                """
                or_params = [f"%{k}%" for k in or_keywords]
                cursor.execute(or_query, or_params)
                or_results = cursor.fetchall()
                
                if or_results:
                    if len(or_results) == 1:
                        상품명, 중량, 판매가, 소재, 규격, 구성 = or_results[0]
                        answer = f"📦 상품 정보:\n\n"
                        answer += f"상품명: {상품명}\n"
                        answer += f"💰 가격: {판매가:,}원\n"
                        answer += f"⚖️  중량: {중량}g\n"
                        answer += f"🏷️  소재: {소재}\n\n"
                        answer += f"📞 고객센터: 1577-4321"
                    else:
                        answer = f"🔍 '{question}' 관련 상품 ({len(or_results)}개):\n\n"
                        for i, row in enumerate(or_results, 1):
                            상품명, 중량, 판매가, 소재, 규격, 구성 = row
                            answer += f"📦 {i}. {상품명}\n"
                            answer += f"   💵 가격: {판매가:,}원\n"
                            answer += f"   ⚖️  중량: {중량}g\n"
                            answer += f"   🏷️  소재: {소재}\n\n"
                        answer += f"📞 고객센터: 1577-4321"
                    
                    conn.close()
                    return {**state, "answer": answer, "category": "product", "confidence": 0.85}
            
            conn.close()
        except Exception as e:
            print(f"faq_node 상품 검색 오류: {e}")
    
    # 기타 질문은 기존 스크립트 사용
    from answer_scripts_simple import answer_scripts
    response_data = answer_scripts.get_response(question)
    
    return {
        **state,
        "answer": response_data["answer"],
        "category": response_data["category"],
        "confidence": response_data["confidence"],
        "template_used": response_data.get("template_used", "none")
    }


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