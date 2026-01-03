import os
import re
import unicodedata


class DocumentStartNode:
    """
    DocumentStartNode

    RESPONSABILIDAD
    ----------------
    - Normaliza el nombre del documento/archivo
    - Crea un directorio asociado al nombre normalizado
    - Registra la ruta creada en el state

    BEHAVIOR / INVARIANTS
    --------------------
    - Si ocurre cualquier error:
        state["status"] = "failed"
        state["error_node"] = "document_start"
    - Si todo es correcto:
        state["status"] = "ok"

    STATE OUTPUT
    ------------
    - normalized_name
    - document_dir
    - status
    - error (opcional)
    """

    @staticmethod
    def execute(state: dict) -> dict:
        """
        Orquestador del nodo.
        Maneja errores y garantiza que el grafo reciba un state consistente.
        """
        #print("📄 DocumentStartNode.execute")
        try:
            return DocumentStartNode._run(state)
        except Exception as e:
            state["status"] = "failed"
            state["error_node"] = "document_start"
            state["error"] = str(e)
            print(f"❌ Error en DocumentStartNode: {e}")
            return state

    @staticmethod
    def _run(state: dict) -> dict:


        #print("📦 State recibido:")
        #for k, v in state.items():
        #    print(f"   - {k}: {v}")

        raw_name = state.get("filename")
        if not raw_name:
            raise ValueError("No se encontró 'filename' en el state")
        
        filename = os.path.splitext(raw_name)[0]
        base_path = state.get("base_path")

        if not base_path:
            raise ValueError("No se encontró 'base_path' en el state")

        # --- path documento ---
        document_path = os.path.join(base_path, raw_name)
        # --- Normalización ---
        document_id = DocumentStartNode._normalizar_nombre(filename)
        #print(f"🧹 Nombre normalizado: {normalized_name}")

        # --- Crear directorio ---
        document_folder = os.path.join(base_path, document_id)
        os.makedirs(document_folder, exist_ok=True)

        # --- Mutar state ---

        state["document_id"] = document_id
        state["document_filename"] = filename
        state["document_path"] = document_path
        state["document_folder"] = document_folder
        state["status"] = "ok"

        return state

    @staticmethod
    def _normalizar_nombre(nombre: str) -> str:
        """
        Normaliza el nombre de un archivo o documento eliminando tildes,
        espacios y caracteres especiales.
        """
        nombre = nombre.lower()
        nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
        nombre = re.sub(r"[^\w\s-]", "", nombre)
        nombre = re.sub(r"[-\s]+", "_", nombre)
        return nombre
