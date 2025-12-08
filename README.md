# SubBot 🧠  
AI 기반 SaaS 고객센터 자동화 서비스 (LangGraph + RAG + QLoRA + Docker)

> 구독형 SaaS 서비스 **SubBox**를 가정하고,  
> 고객 문의를 자동으로 처리하는 **엔드 투 엔드 AI 고객센터**를 구현한 프로젝트입니다.  
> 기획 → 설계 → ERD → LLM + RAG → LangGraph → SFT(QLoRA) → Docker 배포까지 전 과정을 다룹니다.

---

## ✨ 프로젝트 개요

- **목표**  
  - 단순 챗봇이 아니라, 실제 고객센터처럼
    - 문의 유형 라우팅 (FAQ / 결제 / 기술 / 일반)
    - FAQ 문서 기반 RAG 답변
    - 신뢰도 낮을 시 사람 검토용 티켓 생성
    - 관리자 페이지에서 티켓 관리
  - 이 모든 흐름을 **LangGraph**로 정의하고,  
    **LangSmith**로 모니터링하며,  
    **Qwen2-7B + QLoRA**로 도메인 특화 SFT까지 수행

- **핵심 키워드**
  - LangGraph / LangChain / LangSmith
  - RAG (bge-m3 임베딩 + Chroma)
  - Qwen2-7B-Instruct SFT (QLoRA)
  - FastAPI 백엔드, React 프론트
  - PostgreSQL + Docker / docker-compose

---

## 🧩 주요 기능

1. **고객 채팅 인터페이스**
   - 사용자가 질문 입력 → LangGraph 플로우 실행
   - FAQ / 결제 / 기술 / 일반 문의 자동 분류
   - RAG 기반 문서 검색 후 답변 생성

2. **티켓 자동 생성**
   - LLM 답변 신뢰도 낮거나, 모호한 문의 → 티켓로 전환
   - 요약/카테고리/우선순위 자동 생성

3. **관리자(Admin) 페이지**
   - 티켓 목록 조회
   - 티켓 상세(대화 로그, 요약) 조회
   - 티켓 상태 변경(open / closed 등)

4. **RAG 기반 FAQ 검색**
   - `faq_documents` / `faq_chunks` 테이블 + 벡터 DB(Chroma)
   - bge-m3 임베딩 + (선택) bge-reranker 리랭킹

5. **도메인 특화 SFT (Qwen2-7B + QLoRA)**
   - 고객센터 Q/A 100+ JSONL 데이터 직접 구축
   - Hugging Face + TRL + QLoRA로 SFT
   - Base vs SFT 모델 응답 비교

---

## 🏗 아키텍처

```text
[Frontend (React)]
       ↓  (REST)
[FastAPI Backend]  ─────→  [PostgreSQL]
       ↓
   [LangGraph App] ─────────→ [LLM (Qwen2-7B)]
       ↓                     [Embeddings (bge-m3)]
   [RAG Layer] ─────────────→ [Chroma Vector DB]

관측/분석: LangSmith
배포: Docker + docker-compose
