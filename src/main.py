import os
from dotenv import load_dotenv

from src.graph.etl.graph import build_graph


def main():
    load_dotenv()

    repository_path = os.getenv("REPOSITORY")
    storage_path = os.getenv("STORAGE")

    if not repository_path:
        raise RuntimeError("REPOSITORY no definido en .env")
    if not storage_path:
        raise RuntimeError("STORAGE no definido en .env")

    # 🧱 State inicial del ETL
    state = {
        "licitation_id": None,
        "repository_path": repository_path,
        "storage_path": storage_path,
    }

    graph = build_graph()
    graph.invoke(state)


if __name__ == "__main__":
    main()
