import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional

# 사용자 데이터 파일 경로
USERS_FILE = "users.json"

def hash_password(password: str) -> str:
    """비밀번호 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict:
    """사용자 데이터 로드"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users: Dict):
    """사용자 데이터 저장"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_user(email: str, password: str, name: str) -> bool:
    """사용자 생성"""
    users = load_users()
    
    # 이메일 중복 확인
    if email in users:
        return False
    
    # 사용자 추가
    users[email] = {
        "email": email,
        "password": hash_password(password),
        "name": name,
        "created_at": str(datetime.now())
    }
    
    save_users(users)
    return True

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """사용자 인증"""
    users = load_users()
    
    if email in users:
        user = users[email]
        if user["password"] == hash_password(password):
            # 비밀번호 제외하고 반환
            return {
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
    
    return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """이메일로 사용자 조회"""
    users = load_users()
    
    if email in users:
        user = users[email]
        return {
            "email": user["email"],
            "name": user["name"],
            "created_at": user["created_at"]
        }
    
    return None
