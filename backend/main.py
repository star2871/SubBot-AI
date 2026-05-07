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
from llm.graph import graph
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

    answer = get_answer(req.message)

    if answer:
        return JSONResponse(content={"answer": answer, "ticket": False}, media_type="application/json; charset=utf-8")
    else:
        ticket = create_ticket(req.message)
        return JSONResponse(content={"answer": ticket, "ticket": True}, media_type="application/json; charset=utf-8")

@app.post("/api/chat")
async def chat_api(req: ChatRequest):
    try:
        # LangGraph 실행
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
            "confidence": result.get("confidence", 0.5)
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
            "confidence": 0.1
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
    
    return {
        "answer": f"'{query}'에 대한 검색 결과입니다.",
        "search_results": search_results,
        "category": "search",
        "confidence": 0.8
    }

from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)