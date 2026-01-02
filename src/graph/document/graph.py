# src/graph/etl/document/graph.py

from langgraph.graph import StateGraph, END

from src.graph.document.nodes.start import DocumentStartNode
from src.graph.document.nodes.review import DocumentReviewNode
from src.graph.document.nodes.extractor import DocumentExtractorNode


def document_start_node(state: dict) -> dict:
    print("➡️ Entrando al subgrafo document: start")
    return DocumentStartNode.execute(state)


def document_review_node(state: dict) -> dict:
    print("➡️ Entrando al subgrafo document: review")
    return DocumentReviewNode.execute(state)


def document_extractor_node(state: dict) -> dict:
    print("➡️ Entrando al subgrafo document: extractor")
    return DocumentExtractorNode.execute(state)


def build_document_graph():
    graph = StateGraph(dict)

    graph.add_node("start", document_start_node)
    graph.add_node("review", document_review_node)
    graph.add_node("extractor", document_extractor_node)

    graph.set_entry_point("start")
    graph.add_edge("start", "review")
    graph.add_edge("review", "extractor")
    graph.add_edge("extractor", END)

    return graph.compile()
