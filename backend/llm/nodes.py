from llm.ollama_client import ask_llm

# 1. Router
def router_node(state):
    question = state["message"]

    prompt = f"""
    classify this into one word:
    faq, billing, technical, unknown

    question: {question}
    """

    category = ask_llm(prompt)

    return {**state, "category": category.lower()}


# 2. FAQ
def faq_node(state):
    question = state["message"]

    answer = ask_llm(f"answer briefly: {question}")

    return {**state, "answer": answer, "confidence": 0.7}


# 3. Billing
def billing_node(state):
    return {
        **state,
        "answer": "결제 관련 문의입니다. 자세한 내용은 계정에서 확인하세요.",
        "confidence": 0.9
    }


# 4. Technical
def technical_node(state):
    answer = ask_llm(f"technical support: {state['message']}")
    return {**state, "answer": answer, "confidence": 0.6}


# 5. Ticket
def ticket_node(state):
    return {
        **state,
        "answer": "문의가 접수되었습니다. 상담원이 확인할 예정입니다.",
        "confidence": 1.0
    }