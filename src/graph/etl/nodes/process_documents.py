import sqlite3
from src.graph.document.graph import build_document_graph
import os

DB_PATH = os.path.join("data", "etl.db")

class ProcessDocumentsNode:

    """
    ProcessDocumentsNode

    RESPONSABILIDAD
    ----------------
    - Orquesta el procesamiento de documentos asociados a una licitación
    - Recupera desde SQLite todos los archivos con estado 'new' para la licitación actual
    - Ejecuta el subgrafo de documentos una vez por cada archivo
    - Actualiza el estado de cada archivo según el resultado del procesamiento

    BEHAVIOR / INVARIANTS
    --------------------
    - Si no existen archivos con estado 'new':
        → el nodo finaliza sin error
        state["status"] = "processed"
    - Cada archivo se procesa de forma independiente:
        → un error en un archivo NO detiene el procesamiento de los demás
    - Si ocurre un error no controlado a nivel de nodo:
        state["status"] = "error"
        state["error"] contiene el detalle del fallo

    SIDE EFFECTS
    ------------
    - Lectura desde SQLite (tabla files)
    - Escritura / actualización en SQLite:
        - status = processed | error
        - processed_at
        - error (si aplica)
    - Ejecución de subgrafo de documentos (OCR / parsing / chunking / RAG)

    STATE OUTPUT
    ------------
    - licitation_id
    - status
    - error (opcional)
    """

    @staticmethod
    def execute(state: dict) -> dict:
        """
        Orquestador del nodo.
        Maneja errores y controla estado general del nodo.
        """
        try:
            ProcessDocumentsNode._run(state)
            state["status"] = "processed"
        except Exception as e:
            print(f"❌ Error en StartNode: {e}")
            state["status"] = "error"
            state["error"] = str(e)

        return state

    @staticmethod
    def _run(state: dict) -> None:

        print("📦 State recibido:")
        for k, v in state.items():
            print(f"   - {k}: {v}")

        """
        Lógica de negocio:
        - obtiene licitation_id
        - recupera archivos en estado 'new'
        - ejecuta subgrafo por cada archivo
        """
        licitation_id = state.get("licitation_id")
        #print('licitacion ID',licitation_id)

        if not licitation_id:
            raise ValueError("licitation_id no presente en state")

        files = ProcessDocumentsNode._get_new_files(licitation_id)

        if not files:
            print(f"ℹ️ No hay archivos nuevos para licitación {licitation_id}")
            return

        document_graph = build_document_graph()

        for file_row in files:
            file_state = ProcessDocumentsNode._build_file_state(state, file_row)

            try:
                document_graph.invoke(file_state)
                ProcessDocumentsNode._update_file_status(
                    file_row["id"], "processed"
                )
            except Exception as e:
                ProcessDocumentsNode._update_file_status(
                    file_row["id"], "error", str(e)
                )
                print(f"❌ Error procesando archivo {file_row['filename']}")

    @staticmethod
    def _get_new_files(licitation_id: str) -> list[dict]:
        """
        Recupera archivos con status = 'new' desde SQLite
        """

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM files
            WHERE licitation_id = ?
              AND status = 'NEW'
            """,
            (licitation_id,),
        )

        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def _build_file_state(base_state: dict, file_row: dict) -> dict:
        """
        Construye el state que se envía al subgrafo de documentos
        """
        return {
            "base_path": base_state.get('storage_case_path'),
            "filename": file_row["filename"],
        }

    @staticmethod
    def _update_file_status(file_id: str, status: str, error: str | None = None) -> None:
        """
        Actualiza estado del archivo en SQLite
        """
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE files
            SET status = ?,
                processed_at = datetime('now'),
                error = ?
            WHERE id = ?
            """,
            (status, error, file_id),
        )

        conn.commit()
        conn.close()
