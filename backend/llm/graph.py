from langgraph.graph import StateGraph
from llm.nodes import router_node, faq_node, billing_node, technical_node, ticket_node
from typing import TypedDict, Optional

# 상태 구조
class State(TypedDict):
    message: str
    category: Optional[str]
    answer: Optional[str]
    confidence: Optional[float]


def route_decision(state):
    return state.get("category", "unknown")


def confidence_check(state):
    if state.get("confidence", 0) >= 0.6:
        return "end"
    return "ticket"


def build_graph():
    workflow = StateGraph(State)

    # 노드 등록
    workflow.add_node("router", router_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("billing", billing_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("ticket", ticket_node)

    # 시작점
    workflow.set_entry_point("router")

    # router 분기
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "faq": "faq",
            "billing": "billing",
            "technical": "technical",
            "unknown": "faq"
        }
    )

    # 이후 흐름
    workflow.add_conditional_edges(
        "faq",
        confidence_check,
        {
            "end": "__end__",
            "ticket": "ticket"
        }
    )

    workflow.add_edge("billing", "__end__")
    workflow.add_edge("technical", "__end__")
    workflow.add_edge("ticket", "__end__")

    return workflow.compile()


graph = build_graph()