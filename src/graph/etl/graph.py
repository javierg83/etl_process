# src/graph/etl/graph.py

from langgraph.graph import StateGraph, END

from src.graph.etl.nodes.start import StartNode
from src.graph.etl.nodes.cost import CostNode
from src.graph.etl.nodes.process_documents import ProcessDocumentsNode
from src.graph.etl.nodes.cleanup import CleanupNode


def start_node(state: dict) -> dict:
    print("➡️ Entrando al nodo: start")
    return StartNode.execute(state)


def cost_node(state: dict) -> dict:
    print("➡️ Entrando al nodo: cost")
    return CostNode.execute(state)


def process_documents_node(state: dict) -> dict:
    print("➡️ Entrando al nodo: process_documents")
    return ProcessDocumentsNode.execute(state)


def cleanup_node(state: dict) -> dict:
    print("➡️ Entrando al nodo: cleanup")
    return CleanupNode.execute(state)


def route_after_start(state: dict) -> str:
    return "cost" if state.get("status") == "ok" else END


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("start", start_node)
    graph.add_node("cost", cost_node)
    graph.add_node("process_documents", process_documents_node)
    graph.add_node("cleanup", cleanup_node)

    graph.set_entry_point("start")

    graph.add_conditional_edges(
        "start",
        route_after_start,
        {
            "cost": "cost",
            END: END,
        },
    )

    graph.add_edge("cost", "process_documents")
    graph.add_edge("process_documents", "cleanup")
    graph.add_edge("cleanup", END)

    return graph.compile()
