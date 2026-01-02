# src/graph/etl/nodes/process_documents.py

from src.graph.document.graph import build_document_graph


class ProcessDocumentsNode:
    @staticmethod
    def execute(state: dict) -> dict:
        #print("➡️ ProcessDocumentsNode.execute llamado")
        #print(f"📦 State recibido en ProcessDocumentsNode: {state}")

        document_graph = build_document_graph()
        document_graph.invoke(state)

        #print("✅ Subgrafo document ejecutado una vez")

        return state
