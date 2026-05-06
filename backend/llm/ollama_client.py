import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

def ask_llm(prompt: str) -> str:
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        data = res.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"Ollama API error: {e}")
        return "오류가 발생했습니다."