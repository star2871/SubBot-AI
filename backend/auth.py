import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# OAuth 설정
config = Config(environ={
    'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID', ''),
    'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET', ''),
})

oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# 사용자 세션 저장소 (간단한 메모리 저장소)
user_sessions = {}

async def get_current_user(request):
    """현재 로그인된 사용자 정보 가져오기"""
    login_type = request.session.get('login_type')
    
    if login_type == 'email':
        # 일반 이메일 로그인 사용자
        user_id = request.session.get('user_id')
        user_name = request.session.get('user_name')
        if user_id and user_name:
            return {
                'id': user_id,
                'email': user_id,
                'name': user_name,
                'picture': None
            }
    else:
        # OAuth 로그인 사용자
        user_id = request.session.get('user_id')
        if user_id and user_id in user_sessions:
            return user_sessions[user_id]
    
    return None

async def create_user_session(user_info):
    """사용자 세션 생성"""
    user_id = user_info['sub']  # Google의 고유 ID
    user_sessions[user_id] = {
        'id': user_id,
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture']
    }
    return user_id

async def remove_user_session(user_id):
    """사용자 세션 제거"""
    if user_id in user_sessions:
        del user_sessions[user_id]
