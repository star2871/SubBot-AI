import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
# 여러 모델 중 하나를 선택 (phi3:latest가 우선)
MODEL = "phi3:latest"  # phi3 모델로 복원
OLLAMA_PATH = r"C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe"

# Ollama 서비스가 준비될 때까지 대기하는 함수
def wait_for_ollama():
    import time
    max_attempts = 10
    for i in range(max_attempts):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"Ollama 서비스 준비 완료 (시도 {i+1}/{max_attempts})")
                return True
        except:
            pass
        print(f"Ollama 서비스 대기 중... (시도 {i+1}/{max_attempts})")
        time.sleep(2)
    return False

def ask_llm(prompt: str) -> str:
    # 서비스 준비 확인
    if not wait_for_ollama():
        return "Ollama 서비스를 시작할 수 없습니다."
    
    try:
        # 먼저 현재 모델로 시도
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 응답 일관성 향상
                    "top_p": 0.9,
                    "max_tokens": 500,  # 최대 토큰 수 제한
                    "num_ctx": 2048   # 컨텍스트 길이 제한
                }
            }
        )
        
        print(f"Ollama status code: {res.status_code}")  # 디버깅용
        
        if res.status_code == 200:
            data = res.json()
            print(f"Ollama response data: {data}")  # 디버깅용
            
            response = data.get("response", "")
            if response:
                return response.strip()
        
        # 현재 모델이 실패하면 다른 모델로 자동 전환
        print(f"🔄 {MODEL} 모델 실패 - 다른 모델로 전환 시도...")
        fallback_model = auto_switch_model()
        
        # 다른 모델로 재시도
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": fallback_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 500,
                    "num_ctx": 2048
                }
            }
        )
        
        if res.status_code == 200:
            data = res.json()
            response = data.get("response", "")
            if response:
                print(f"✅ {fallback_model} 모델로 성공적으로 응답 생성")
                return response.strip()
        
        return f"API 오류: 모든 모델에서 응답 생성 실패"
        
    except requests.exceptions.Timeout:
        print("Ollama timeout error")
        return "응답 시간 초과 - 다시 시도해주세요."
    except requests.exceptions.ConnectionError:
        print("Ollama connection error")
        return "Ollama 서비스에 연결할 수 없습니다."
    except Exception as e:
        print(f"Ollama API error: {e}")
        return f"오류 발생: {str(e)}"

# 다른 모델 사용 가능한지 확인하는 함수
def check_available_models():
    """사용 가능한 모델 확인"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model.get("name", "") for model in models_data.get("models", [])]
            print(f"✅ 사용 가능한 모델: {available_models}")
            return available_models
        return []
    except:
        return []

# 모델 자동 전환 함수
def auto_switch_model():
    """현재 모델이 작동하지 않으면 다른 모델로 전환"""
    available_models = check_available_models()
    
    # phi3:latest가 있으면 그대로 사용
    if "phi3:latest" in available_models:
        print("✅ phi3:latest 모델 정상 작동 중")
        return "phi3:latest"
    
    # 다른 가벼운 모델 순서대로 시도
    fallback_models = ["llama2:7b", "qwen:7b", "gemma:7b"]
    
    for model in fallback_models:
        if model in available_models:
            print(f"🔄 {model} 모델로 자동 전환")
            return model
    
    print("❌ 사용 가능한 모델 없음")
    return "phi3:latest"  # 기본값 유지