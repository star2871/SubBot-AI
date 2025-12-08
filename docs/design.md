# **SubBot – AI 고객지원 시스템**

> LangGraph + LangSmith + FastAPI + RAG 기반 고객지원 자동화 프로젝트
> 

## 1. 프로젝트 개요

### 🎯 목적

SubBot은 가상의 SaaS 서비스 제공 기업을 위한 **AI 고객지원 자동화 시스템**입니다.

LangGraph로 **라우팅 → 에이전트 → 티켓 생성** 흐름을 구현하고,

LangSmith로 실행 과정을 **추적·평가**합니다.

### 🧩 핵심 가치

- 단순 LLM 챗봇이 아니라 **프로세스 기반 고객지원 플로우를 자동화**
- RAG 기반 FAQ 답변으로 **정확한 문서 기반 응답 제공**
- 신뢰도(confidence) 낮은 경우 자동 **티켓 생성**
- 관리자 페이지로 **실제 CS 운영 흐름 재현**

## 2. 서비스 기능 구조도

```jsx
[사용자 질문]
       ↓
[Router Node - LLM 분류]
   (faq / billing / technical / unknown)
       ↓
 ┌───────────────┬────────────────┬────────────────┐
 ↓               ↓                ↓                ↓
FAQ Agent    Billing Agent   Technical Agent   Unknown Agent
(RAG)          (API)              (RAG)             (FAQ 처리)
       ↓
[Confidence Check]
     ├── ≥ 0.6 → 답변 반환
     └── < 0.6 → Ticket Agent(요약 생성)
       ↓
[대화 저장 + 티켓 저장]

```

## 3. 사용자 시나리오(SCU – Service Customer Usecase)

### 👤 사용자 유형

1. 고객(User): SaaS 서비스 이용자
2. 관리자(Admin): 고객센터 담당자

---

### ✔ 시나리오 1: 고객 문의 & 자동 답변

1. 고객이 “다음 결제일이 언제인가요?” 질문
2. Router가 billing으로 분류
3. Billing Agent → 내부 API 조회
4. LLM이 자연어 답변 생성
5. confidence ≥ 0.6 → 바로 답변

---

### ✔ 시나리오 2: 애매한 질문 → 티켓 생성

1. 고객이 “계정이 계속 이상해요. 뭐가 문제죠?”
2. Router가 technical 또는 unknown으로 분류
3. FAQ Agent에서 정확한 문서 못 찾음
4. confidence < 0.6
5. Ticket Agent가 요약
6. 관리자 페이지에서 확인 가능

---

## 4. 요구사항 정의 (Functional Requirements)

### ✨ 고객 기능

- 텍스트로 질문 입력
- 답변 실시간 수신
- 답변에는 RAG 기반 문서 사용 가능
- 필요한 경우 티켓을 생성하고 안내받음

---

### ✨ 관리자 기능

- 티켓 리스트 조회
- 각 티켓 클릭 → 상세 대화 및 요약 확인
- 티켓 상태(open/closed) 변경

---

### ✨ 백엔드 기능

- LangGraph 기반 라우팅 및 상태머신
- RAG: 문서 업로드 → 임베딩 → Chroma 저장
- Billing API 흉내내기
- DB 저장(대화, 티켓)

---

### ✨ 시스템 요구사항 (Non-functional)

- 응답 속도 3초 이하
- 재현 가능한 로그 기록(LangSmith)
- LLM 호출 실패 시 graceful fallback
- RAG 문서 버전 관리

---

## 5. 데이터 구조 설계

### 🎲 DB 테이블

![image.png](attachment:77db1452-1cd2-4f8a-9160-17e743496161:image.png)

---

## 6. API 명세

### POST `/api/chat`

**입력**

```jsx
{
  "user_id": "user123",
  "message": "다음 결제일은?"
}
```

출력

```jsx
{
  "answer": "다음 결제일은 1월 15일입니다.",
  "ticket_created": false,
  "route": "billing"
}
```

## **7. 시스템 아키텍처**

```jsx
Frontend(React)
      ↓
FastAPI Backend ───────── LangGraph (state machine)
      ↓                        ↓
   DB(SQLite)               LLM(OpenAI)
      ↓                        ↓
  Admin Page          LangSmith(Tracing/Eval)
      ↓
Ticket List / Logs
```

## 8. 개발 로드맵

### 📅 1주차: 기획/설계

- 서비스 정의
- 와이어프레임(Figma)

https://www.figma.com/make/vFnPSDwGsemKfSg5CDw19R/Customer-Support-Interface?node-id=0-1&t=MPbeNKdXHV3KpwYJ-1

- DB 스키마

![image.png](attachment:77db1452-1cd2-4f8a-9160-17e743496161:image.png)

### 📅 2주차: 백엔드 기반

- FastAPI 기본 구현
- DB, RAG 인덱싱

### 📅 3주차: LangGraph 통합

- router → faq/billing → ticket 처리
- 상태 머신 완성

### 📅 4주차: 프론트 & LangSmith

- React UI
- 관리자 페이지
- LangSmith로 평가 세트 작성

---

## 9. 향후 개선

- 음성 입력
- 멀티턴 대화 개선
- 실사용 SaaS API 연동
- 관리자 피드백 기반 리랭킹