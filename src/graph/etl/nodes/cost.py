# src/graph/etl/nodes/cost.py

class CostNode:
    @staticmethod
    def execute(state: dict) -> dict:
        #print("➡️ Entrando al nodo: cost")
        #print(f"📦 State recibido: {state}")

        # Valor dummy de costo para pruebas
        state["cost_total"] = 12345

        #print(f"💰 Costo calculado (dummy): {state['cost_total']}")

        return state
