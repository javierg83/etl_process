# src/graph/etl/nodes/start.py

from src.config import STORAGE,REPOSITORY
import os
import shutil
import sqlite3
import hashlib
from datetime import datetime
from uuid import uuid4

DB_PATH = os.path.join("data", "etl.db")


class StartNode:
    """
    StartNode

    RESPONSABILIDAD
    ----------------
    - Detecta licitaciones disponibles en el directorio repository
    - Selecciona una licitación (primer subdirectorio encontrado)
    - Copia los archivos a storage (si no existen previamente)
    - Registra y sincroniza archivos en base de datos SQLite

    BEHAVIOR / INVARIANTS
    --------------------
    - Si repository está vacío:
        state["status"] = "empty"
        → el grafo NO continúa
    - Si ocurre cualquier error:
        state["status"] = "failed"
        state["error_node"] = "start"
    - Si todo es correcto:
        state["status"] = "ok"

    SIDE EFFECTS
    ------------
    - Escritura en filesystem (storage)
    - Escritura / actualización en SQLite (tabla files)

    STATE OUTPUT
    ------------
    - licitation_id
    - storage_case_path
    - status
    - error (opcional)
    """

    @staticmethod
    def execute(state: dict) -> dict:
        """
        Orquestador del nodo.
        Maneja errores y garantiza que el grafo reciba un state consistente.
        """
        try:
            return StartNode._run(state)
        except Exception as e:
            state["status"] = "failed"
            state["error_node"] = "start"
            state["error"] = str(e)
            print(f"❌ Error en StartNode: {e}")
            return state

    @staticmethod
    def _run(state: dict) -> dict:
        
        subdirs = [
            d for d in os.listdir(REPOSITORY)
            if os.path.isdir(os.path.join(REPOSITORY, d))
        ]

        if not subdirs:
            state["status"] = "empty"
            return state

        licitation_id = subdirs[0]
        state["licitation_id"] = licitation_id

        src_dir = os.path.join(REPOSITORY, licitation_id)
        dst_dir = os.path.join(STORAGE, licitation_id)

        #print(f"🆔 Licitación seleccionada: {licitation_id}")

        if not os.path.exists(dst_dir):
            shutil.copytree(src_dir, dst_dir)
            #print(f"📁 Directorio copiado a storage: {dst_dir}")
        else:
            pass
            #print(f"ℹ️ Directorio ya existe en storage: {dst_dir}")

        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                licitation_id TEXT,
                filename TEXT,
                checksum TEXT,
                status TEXT,
                created_at TEXT,
                processed_at TEXT,
                error TEXT
            )
            """
        )

        now = datetime.utcnow().isoformat()

        for root, _, files in os.walk(src_dir):
            for filename in files:
                src_file = os.path.join(root, filename)
                checksum = StartNode._checksum(src_file)

                cursor.execute(
                    """
                    SELECT checksum FROM files
                    WHERE licitation_id = ? AND filename = ?
                    """,
                    (licitation_id, filename),
                )
                row = cursor.fetchone()

                if row is None:
                    cursor.execute(
                        """
                        INSERT INTO files (
                            id, licitation_id, filename, checksum,
                            status, created_at, processed_at, error
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid4()),
                            licitation_id,
                            filename,
                            checksum,
                            "NEW",
                            now,
                            None,
                            None,
                        ),
                    )
                    print(f"🆕 Archivo registrado: {filename}")
                else:
                    old_checksum = row[0]
                    if old_checksum != checksum:
                        cursor.execute(
                            """
                            UPDATE files
                            SET checksum = ?, status = ?, error = ?
                            WHERE licitation_id = ? AND filename = ?
                            """,
                            (checksum, "NEW", None, licitation_id, filename),
                        )
                        print(f"🔄 Archivo actualizado (checksum): {filename}")

        conn.commit()
        conn.close()

        state["status"] = "ok"
        state["storage_case_path"] = dst_dir

        return state

    @staticmethod
    def _checksum(path: str) -> str:
        """
        Calcula checksum SHA256 de un archivo.
        """
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
