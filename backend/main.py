from fastapi import FastAPI, Response, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from faq import get_answer
from ticket import create_ticket
from auth import oauth, get_current_user, create_user_session, remove_user_session
from database import create_user, authenticate_user, get_user_by_email
import os
import secrets
import time
from llm.graph import graph
from llm.product_rag import row_to_dict, format_products_fast, hybrid_search_products, simple_normalize, filter_by_material_intent

# 상품 검색 질문 유형 분석
def analyze_query_type(question: str):
    """질문에서 원하는 정보 유형 분석"""
    q = question.lower()
    is_price = any(w in q for w in ['얼마', '가격', '비용', '판매가', '얼마야', '얼마예요', '얼마인가'])
    is_material = '소재' in q
    is_weight = any(w in q for w in ['중량', '무게', '몇 그램', '몇g'])
    return is_price, is_material, is_weight

def format_product_response(row, is_price=False, is_material=False, is_weight=False):
    """질문 유형에 맞게 상품 정보 포맷팅"""
    상품명, 중량, 판매가, 소재, 규격, 구성 = row
    
    if is_price and not is_material and not is_weight:
        # 가격만
        return f"📦 {상품명}\n💰 가격: {판매가:,}원\n\n📞 고객센터: 1577-4321"
    elif is_material and not is_price and not is_weight:
        # 소재만
        return f"📦 {상품명}\n🏷️ 소재: {소재}\n\n📞 고객센터: 1577-4321"
    elif is_weight and not is_price and not is_material:
        # 중량만
        return f"📦 {상품명}\n⚖️ 중량: {중량}g\n\n📞 고객센터: 1577-4321"
    else:
        # 전체 정보 (기본)
        return f"📦 상품 정보:\n\n상품명: {상품명}\n💰 가격: {판매가:,}원\n⚖️ 중량: {중량}g\n🏷️ 소재: {소재}\n\n📞 고객센터: 1577-4321"

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 미들웨어 추가
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))

# 한글 인코딩을 위한 JSONResponse 설정
@app.get("/")
def root():
    return JSONResponse(content={"message": "SubBot running"}, media_type="application/json; charset=utf-8")

# Mount static files to serve favicon
app.mount("/static", StaticFiles(directory="../subbot-ui/vite-project/public"), name="static")

class ChatRequest(BaseModel):
    message: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/favicon.ico")
def favicon():
    try:
        return Response(content=open("../subbot-ui/vite-project/public/vite.svg", "rb").read(), media_type="image/svg+xml")
    except FileNotFoundError:
        return Response(content="", media_type="image/x-icon")

# OAuth 로그인 라우트
@app.get("/login")
async def login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/auth"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if user_info:
            user_id = await create_user_session(user_info)
            request.session['user_id'] = user_id
            
            return RedirectResponse(url="/chat.html")
        else:
            raise HTTPException(status_code=400, detail="Failed to get user info")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/logout")
async def logout(request: Request):
    user_id = request.session.get('user_id')
    if user_id:
        await remove_user_session(user_id)
    request.session.clear()
    return RedirectResponse(url="/")

# 일반 회원가입
@app.post("/register")
async def register(req: RegisterRequest):
    try:
        # 이메일 형식 검증
        if "@" not in req.email or "." not in req.email:
            return JSONResponse(
                content={"error": "올바른 이메일 형식이 아닙니다."}, 
                status_code=400,
                media_type="application/json; charset=utf-8"
            )
        
        # 비밀번호 길이 검증
        if len(req.password) < 6:
            return JSONResponse(
                content={"error": "비밀번호는 최소 6자 이상이어야 합니다."}, 
                status_code=400,
                media_type="application/json; charset=utf-8"
            )
        
        # 사용자 생성
        if create_user(req.email, req.password, req.name):
            return JSONResponse(
                content={"message": "회원가입이 완료되었습니다."}, 
                media_type="application/json; charset=utf-8"
            )
        else:
            return JSONResponse(
                content={"error": "이미 존재하는 이메일입니다."}, 
                status_code=400,
                media_type="application/json; charset=utf-8"
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"회원가입 중 오류가 발생했습니다: {str(e)}"}, 
            status_code=500,
            media_type="application/json; charset=utf-8"
        )

# 일반 로그인
@app.post("/login-email")
async def login_email(req: LoginRequest, request: Request):
    try:
        user = authenticate_user(req.email, req.password)
        
        if user:
            # 세션에 사용자 정보 저장
            request.session['user_id'] = user['email']
            request.session['user_name'] = user['name']
            request.session['login_type'] = 'email'
            request.session['remember_login'] = True  # 로그인 유지 플래그
            
            return JSONResponse(
                content={"message": "로그인 성공", "user": user, "remember_login": True}, 
                media_type="application/json; charset=utf-8"
            )
        else:
            return JSONResponse(
                content={"error": "이메일 또는 비밀번호가 올바르지 않습니다."}, 
                status_code=401,
                media_type="application/json; charset=utf-8"
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"로그인 중 오류가 발생했습니다: {str(e)}"}, 
            status_code=500,
            media_type="application/json; charset=utf-8"
        )

@app.get("/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if user:
        return JSONResponse(content=user, media_type="application/json; charset=utf-8")
    else:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

# 인증된 사용자만 접근 가능한 채팅 엔드포인트
@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 상품 키워드 확인
    product_keywords = ['상품', '골드', '메달', '은', '금', '카드형', '토끼', '용', '뱀', '조폐', '한국조폐공사', '가격', '얼마', '판매가', '비용', '금액', '바']
    
    if any(keyword in req.message.lower() for keyword in product_keywords):
        # 상품 검색 수행
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "shop.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query_text = req.message.strip()
            
            # 질문/가격 관련 단어 제거 후 상품명 검색
            import re
            # 모든 한글 조사/질문어/어미 제거 (정규표현식으로)
            # - 조사: 은,는,이,가,을,를,에,의,로,으로,와,과,도,만,까지,부터
            # - 질문/어미: 야, 요, 에요, 이에요, 죠, 니까, 을까요, 입니까, 인가요, 해줘, 주세요, 드려요
            clean_query = re.sub(r'(?<=[가-힣])(은|는|이|가|을|를|에|의|로|으로|와|과|도|만|까지|부터|에게|께|한테|처럼|보다|마다|말고|커녕)(?![가-힣])', '', query_text)
            clean_query = re.sub(r'(얼마(야|예요|에요|인가|인가요|일까요|죠|니까)?|가격(은|이)?|정보(를|를|은)?|알려(줘|주세요|드려요)?|찾아(줘|주세요)?|검색(해|해줘)?|해(줘|주세요)?)', '', clean_query)
            clean_query = re.sub(r'(은요|는요|이에요|예요|인가요|일까요|까요|해줘|해주세요|주세요|드려요|입니다|입니까|하나요|되나요)', '', clean_query)
            clean_query = re.sub(r'[?.,!…]+$', '', clean_query).strip()
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()  # 연속 공백 1개로
            
            # remove_words에서 추가 제거
            remove_words = ['가격', '얼마', '정보', '알려', '찾아', '검색', '해줘', '해주세요', '주세요', '드려요', '은', '는', '이', '가']
            for word in remove_words:
                clean_query = clean_query.replace(word, '').strip()
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()
            
            # 1. 먼저 정확한 상품명 검색 (공백 정규화 적용)
            normalized_query = re.sub(r'\s+', ' ', query_text.strip())
            normalized_clean = re.sub(r'\s+', ' ', clean_query.strip())
            normalized_simple = simple_normalize(query_text)
            
            for search_text in [normalized_query, query_text, normalized_clean, clean_query, normalized_simple]:
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
                answer = format_products_fast(req.message, [row_to_dict(exact_result)])
                conn.close()
                return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
            
            # 2. 정확히 일치하지 않으면 키워드 AND 검색 (모든 키워드 포함)
            # 먼저 기존 정규화 키워드로 시도, 실패하면 simple_normalize 키워드로도 시도
            for keyword_source in [normalized_clean, normalized_simple]:
                search_keywords = []
                for k in keyword_source.split():
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
                        and_products = filter_by_material_intent(req.message, [row_to_dict(row) for row in and_results])
                        if and_products:
                            answer = format_products_fast(req.message, and_products)
                            conn.close()
                            return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
            
            # 3. AND 검색도 안 되면 개별 키워드 OR 검색
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
                    or_products = filter_by_material_intent(req.message, [row_to_dict(row) for row in or_results])
                    if or_products:
                        answer = format_products_fast(req.message, or_products)
                        conn.close()
                        return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
            
            # 하이브리드 fallback: LLM 정규화 + 선택
            hybrid_results = hybrid_search_products(cursor, req.message, normalized_clean)
            if hybrid_results:
                answer = format_products_fast(req.message, hybrid_results)
                conn.close()
                return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
            
            conn.close()
        except Exception as e:
            print(f"상품 검색 오류: {e}")

    # 기존 FAQ 검색
    answer = get_answer(req.message)

    if answer:
        return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
    else:
        ticket = create_ticket(req.message)
        return JSONResponse(content={"answer": ticket, "ticket": True}, media_type="application/json; charset=utf-8")

@app.post("/api/chat")
async def chat_api(req: ChatRequest):
    start_time = time.perf_counter()
    try:
        # 상품 키워드 확인 - 직접 DB 검색으로 우회
        product_keywords = ['상품', '골드', '메달', '은', '금', '카드형', '토끼', '용', '뱀', '조폐', '한국조폐공사', '가격', '얼마', '판매가', '비용', '금액', '바']
        
        if any(keyword in req.message.lower() for keyword in product_keywords):
            try:
                import sqlite3
                import re
                
                db_path = os.path.join(os.path.dirname(__file__), "..", "data", "shop.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                query_text = req.message.strip()
                
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
                normalized_simple = simple_normalize(query_text)
                
                # 1. 정확한 상품명 검색
                exact_result = None
                for search_text in [normalized_query, query_text, normalized_clean, clean_query, normalized_simple]:
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
                    answer = format_products_fast(req.message, [row_to_dict(exact_result)])
                    conn.close()
                    return {
                        "answer": answer,
                        "category": "product",
                        "confidence": 0.95
                    }
                
                # 2. 키워드 AND 검색 (기존 + simple_normalize 키워드 모두 시도)
                for keyword_source in [normalized_clean, normalized_simple]:
                    search_keywords = []
                    for k in keyword_source.split():
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
                            and_products = filter_by_material_intent(req.message, [row_to_dict(row) for row in and_results])
                            if and_products:
                                answer = format_products_fast(req.message, and_products)
                                conn.close()
                                return {
                                    "answer": answer,
                                    "category": "product",
                                    "confidence": 0.9
                                }
                
                # 3. OR 검색
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
                        or_products = filter_by_material_intent(req.message, [row_to_dict(row) for row in or_results])
                        if or_products:
                            answer = format_products_fast(req.message, or_products)
                            conn.close()
                            return {
                                "answer": answer,
                                "category": "product",
                                "confidence": 0.85
                            }
                
                # 하이브리드 fallback: LLM 정규화 + 선택
                hybrid_results = hybrid_search_products(cursor, req.message, normalized_clean)
                if hybrid_results:
                    answer = format_products_fast(req.message, hybrid_results)
                    conn.close()
                    return {
                        "answer": answer,
                        "category": "product",
                        "confidence": 0.8
                    }
                
                conn.close()
            except Exception as e:
                print(f"/api/chat 직접 검색 오류: {e}")
        
        # LangGraph 실행 (상품이 아니거나 직접 검색 실패 시)
        result = graph.invoke({"message": req.message})
        
        # 대화 내용 저장
        from conversation_db import conv_db
        conv_db.save_conversation(
            user_message=req.message,
            bot_response=result.get("answer", ""),
            category=result.get("category", "unknown"),
            confidence=result.get("confidence", 0.5),
            session_id=req.session_id if hasattr(req, 'session_id') else None,
            product_info=result.get("product_info")
        )
        
        response_data = {
            "answer": result.get("answer", "죄송합니다. 응답을 생성할 수 없습니다."),
            "category": result.get("category", "unknown"),
            "confidence": result.get("confidence", 0.5),
            "response_time_ms": round((time.perf_counter() - start_time) * 1000)
        }
        
        # 캐시에서 온 답변인지 표시
        if result.get("from_cache"):
            response_data["from_cache"] = True
        
        return response_data
        
    except Exception as e:
        # 에러도 저장
        try:
            from conversation_db import conv_db
            conv_db.save_conversation(
                user_message=req.message,
                bot_response=f"오류 발생: {str(e)}",
                category="error",
                confidence=0.1
            )
        except:
            pass  # 저장 실패 시 무시
        
        return {
            "answer": f"오류가 발생했습니다: {str(e)}",
            "category": "error",
            "confidence": 0.1,
            "response_time_ms": round((time.perf_counter() - start_time) * 1000)
        }

@app.post("/api/search")
async def search_api(req: ChatRequest):
    import requests
    
    query = req.message
    search_results = []
    
    # 다양한 검색 엔진 시도
    search_engines = [
        {
            "name": "Google",
            "url": f"https://www.google.com/search?q={query}"
        },
        {
            "name": "Naver", 
            "url": f"https://search.naver.com/search.naver?query={query}"
        },
        {
            "name": "Daum",
            "url": f"https://search.daum.net/search?w=tot&q={query}"
        }
    ]
    
    for engine in search_engines:
        try:
            response = requests.get(engine["url"], timeout=10)
            if response.status_code == 200:
                search_results.append({
                    "engine": engine["name"],
                    "url": engine["url"],
                    "status": "success",
                    "message": f"{engine['name']} 검색 결과를 찾았습니다."
                })
            else:
                search_results.append({
                    "engine": engine["name"],
                    "status": "error",
                    "message": f"{engine['name']} 검색 실패"
                })
        except Exception as e:
            search_results.append({
                "engine": engine["name"],
                "status": "error", 
                "message": f"{engine['name']} 검색 오류: {str(e)[:50]}"
            })
    
    