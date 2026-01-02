# src/graph/etl/nodes/cleanup.py

class CleanupNode:
    @staticmethod
    def execute(state: dict) -> dict:
        #print("➡️ Entrando al nodo: cleanup")
        #print(f"📦 State recibido: {state}")


        # Placeholder: aquí luego se validará si hubo errores antes de borrar
        state["cleanup_done"] = False

        #print(f"🧹 Cleanup ejecutado (dummy): {state['cleanup_done']}")

        return state
