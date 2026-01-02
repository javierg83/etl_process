# src/graph/etl/nodes/start.py

class StartNode:
    @staticmethod
    def execute(state: dict) -> dict:
        #print("🟢 StartNode.execute llamado")
        #print(f"📦 State recibido: {state}")

        # Placeholder: aquí luego se resolverá la selección de la licitación
        state["licitation_id"] = state.get("licitation_id")

        #print(f"🆔 Licitation ID actual: {state['licitation_id']}")

        return state
