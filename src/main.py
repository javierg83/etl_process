
import os
from src.config import REPOSITORY, STORAGE
from src.graph.etl.graph import build_graph


def main():


    # 🧱 State inicial del ETL
    state = {
        "licitation_id": None,
        "repository_path": REPOSITORY,
        "storage_path": STORAGE,
    }

    graph = build_graph()
    graph.invoke(state)


if __name__ == "__main__":
    main()
