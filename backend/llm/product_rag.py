from llm.ollama_client import ask_llm

# RAG 포맷팅 전용 모델 — 답변 생성만 담당 (더 가벼운 모델 사용 가능)
RAG_MODEL = "qwen2.5:1.5b"


def row_to_dict(row):
    """SQL tuple 결과를 dict로 변환"""
    return {
        '상품명': row[0],
        '중량': row[1],
        '판매가': row[2],
        '소재': row[3],
        '규격': row[4],
        '구성': row[5]
    }


def format_products_fallback(question: str, products: list, is_single: bool = False) -> str:
    """LLM 실패 시 기존 포맷팅 fallback"""
    if is_single or len(products) == 1:
        p = products[0]
        return (
            f"📦 상품 정보:\n\n"
            f"상품명: {p['상품명']}\n"
            f"💰 가격: {p['판매가']:,}원\n"
            f"⚖️  중량: {p['중량']}g\n"
            f"🏷️  소재: {p['소재']}\n\n"
            f"📞 고객센터: 1577-4321"
        )

    answer = f"🔍 검색 결과 ({len(products)}개):\n\n"
    for i, p in enumerate(products, 1):
        answer += (
            f"📦 {i}. {p['상품명']}\n"
            f"   💵 가격: {p['판매가']:,}원\n"
            f"   ⚖️  중량: {p['중량']}g\n"
            f"   🏷️  소재: {p['소재']}\n\n"
        )
    answer += f"📞 고객센터: 1577-4321"
    return answer


def normalize_material(text: str) -> str:
    """소재 표기를 한글로 변환"""
    if not text:
        return text
    # 대문자로 통일 후 변환
    t = text.upper()
    # 순서 중요 (복합 소재 먼저 처리)
    t = t.replace('AU 999.9', '금 999.9')
    t = t.replace('AU 999', '금 999')
    t = t.replace('AU 585', '금 585(14K)')
    t = t.replace('AU', '금')
    t = t.replace('AG999', '은 999')
    t = t.replace('AG', '은')
    t = t.replace('CU90, ZN10', '동 90%, 아연 10%')
    t = t.replace('CU', '동(구리)')
    t = t.replace('ZN', '아연')
    t = t.replace('NI', '니켈')
    t = t.replace('FE', '철')
    t = t.replace('PD', '팔라듐')
    t = t.replace('PT', '백금')
    return t


def format_products_fast(question: str, products: list) -> str:
    """
    상품 검색 결과를 즉시 포맷팅 (LLM 없음 — 0.1초 이내)
    """
    if not products:
        return None

    is_single = len(products) == 1

    # 단일 상품
    if is_single or len(products) == 1:
        p = products[0]
        return (
            f"📦 {p['상품명']}\n\n"
            f"💰 판매가　　{p['판매가']:,}원\n"
            f"⚖️ 중량　　　{p['중량']}g\n"
            f"🏷️ 소재　　　{normalize_material(p['소재'])}\n\n"
            f"📞 고객센터: 1577-4321"
        )

    # 다중 상품
    answer = f"🔍 검색 결과 ({len(products)}개)\n\n"
    for i, p in enumerate(products, 1):
        answer += (
            f"📦 {i}. {p['상품명']}\n"
            f"   💵 {p['판매가']:,}원    ⚖️ {p['중량']}g    🏷️ {p['소재']}\n\n"
        )
    answer += f"📞 고객센터: 1577-4321"
    return answer


def simple_normalize(question: str) -> str:
    """
    규칙 기반 쿼리 정규화 — LLM 호출 없이 즉시 처리

    예: "뱀띠 금메달 가격" -> "뱀 골드"
    """
    import re
    text = question.lower()

    # 1. 조사/어미/질문어 제거
    text = re.sub(r'(?<=[가-힣])(은|는|이|가|을|를|에|의|로|으로|와|과|도|만|까지|부터|에게|께|한테|처럼|보다|마다|말고|커녕)(?![가-힣])', '', text)
    text = re.sub(r'(얼마(야|예요|에요|인가|인가요|일까요|죠|니까)?|가격(은|이)?|정보(를|는|은)?|알려(줘|주세요|드려요)?|찾아(줘|주세요)?|검색(해|해줘)?|해(줘|주세요)?|있나요|되나요|입니까|입니다|하나요)', '', text)
    text = re.sub(r'(은요|는요|이에요|예요|인가요|일까요|까요|해줘|해주세요|주세요|드려요)', '', text)
    text = re.sub(r'[?.,!…]+$', '', text).strip()

    # 2. 동의어 변환 (한국조폐공사 네이밍 기준)
    synonyms = {
        '뱀띠': '뱀', '뱀의 해': '뱀', '뱀년': '뱀',
        '용띠': '용', '용의 해': '용', '용년': '용',
        '토끼띠': '토끼', '토끼의 해': '토끼',
        '금메달': '골드', '금상품': '골드',
        '은메달': '실버', '은상품': '실버',
        '카드': '카드형',
    }
    # 긴 키워드부터 변환 (부분 겹침 방지)
    for old, new in sorted(synonyms.items(), key=lambda x: -len(x[0])):
        text = text.replace(old, new)

    # 3. 연속 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()

    # 4. 의미없는 토큰 제거 후 반환
    keywords = [k.strip() for k in text.split() if len(k.strip()) >= 1]
    return ' '.join(keywords)


def hybrid_search_products(cursor, question: str, normalized_clean: str) -> list:
    """
    하이브리드 상품 검색 (A + B)

    흐름:
    1. 정규화된 쿼리로 AND 검색
    2. 정규화된 쿼리로 OR 검색
    3. 전체 상품 목록에서 LLM이 선택

    Args:
        cursor: sqlite3 cursor
        question: 사용자 원본 질문
        normalized_clean: 기존 정규화된 질문 (조사 제거된 것)

    Returns:
        검색된 상품 dict 리스트 (없으면 빈 리스트)
    """
    import re

    # 1단계: 규칙 기반 쿼리 정규화 (LLM 없이 즉시)
    llm_normalized = simple_normalize(question)
    print(f"[hybrid] 원본: '{question}' -> 정규화: '{llm_normalized}'")

    # 정규화된 키워드로 검색
    keywords = [k.strip() for k in llm_normalized.split() if len(k.strip()) >= 2 and not k.strip().isdigit()]
    if not keywords:
        keywords = [k.strip() for k in llm_normalized.split() if len(k.strip()) >= 1]

    # 1-A: 정규화 AND 검색
    if keywords:
        conditions = " AND ".join(["상품명 LIKE ?"] * len(keywords))
        and_query = f"""
            SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
            FROM products
            WHERE {conditions}
            AND [ 판매가 ] IS NOT NULL
            AND CAST([ 판매가 ] AS INTEGER) > 0
            ORDER BY CAST([ 판매가 ] AS INTEGER) ASC
            LIMIT 5
        """
        params = [f"%{k}%" for k in keywords]
        cursor.execute(and_query, params)
        and_results = cursor.fetchall()
        if and_results:
            return [row_to_dict(row) for row in and_results]

    # 1-B: 정규화 OR 검색 (LIMIT 높게 + Python에서 키워드 매칭 점수 정렬)
    or_keywords = [k for k in llm_normalized.split() if len(k.strip()) >= 2 and not k.strip().isdigit()]
    if not or_keywords:
        or_keywords = [k for k in llm_normalized.split() if len(k.strip()) >= 1]

    if or_keywords:
        or_conditions = " OR ".join(["상품명 LIKE ?"] * len(or_keywords))
        or_query = f"""
            SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
            FROM products
            WHERE ({or_conditions})
            AND [ 판매가 ] IS NOT NULL
            AND CAST([ 판매가 ] AS INTEGER) > 0
            LIMIT 100
        """
        or_params = [f"%{k}%" for k in or_keywords]
        cursor.execute(or_query, or_params)
        or_results = cursor.fetchall()
        if or_results:
            candidates = [row_to_dict(row) for row in or_results]

            # 키워드 매칭 점수 계산 (더 많은 키워드가 포함된 상품을 앞에)
            def score_product(p):
                name = p.get('상품명', '')
                return sum(1 for k in or_keywords if k in name)

            candidates.sort(key=score_product, reverse=True)
            return candidates[:5]

    # 2단계: 전체 상품 목록에서 Python 점수 기반 선택 (최후의 수단)
    cursor.execute("""
        SELECT 상품명, 중량, [ 판매가 ] as 판매가, 소재, 규격, 구성
        FROM products
        WHERE [ 판매가 ] IS NOT NULL
        AND CAST([ 판매가 ] AS INTEGER) > 0
        LIMIT 50
    """)
    all_results = cursor.fetchall()
    if all_results:
        all_products = [row_to_dict(row) for row in all_results]
        # 질문과 가장 유사한 상품 선택 (키워드 매칭 점수)
        question_keywords = [k for k in llm_normalized.split() if len(k) >= 2]
        def score_all(p):
            name = p.get('상품명', '')
            return sum(1 for k in question_keywords if k in name)
        all_products.sort(key=score_all, reverse=True)
        return [all_products[0]]

    return []
