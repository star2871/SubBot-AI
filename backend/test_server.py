from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Test server running"}

@app.post("/api/chat")
def chat_test():
    return {"answer": "test response", "category": "test", "confidence": 0.9}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
