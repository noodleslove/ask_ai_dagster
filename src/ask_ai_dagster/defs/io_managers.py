import json
import os
from typing import Any
import dagster as dg
from langchain_core.documents import Document


class DocumentIOManager(dg.IOManager):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def handle_output(self, context: "dg.OutputContext", obj: Any) -> None:
        file_path = os.path.join(
            self.base_dir, f"{context.asset_key.path[-1]}.json"
        )

        serialized_docs = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in obj
        ]

        with open(file_path, "w") as f:
            json.dump(serialized_docs, f)

    def load_input(self, context: "dg.InputContext") -> Any:
        file_path = os.path.join(
            self.base_dir, f"{context.asset_key.path[-1]}.json"
        )
        if not os.path.exists(file_path):
            return []

        with open(file_path, "r") as f:
            serialized_docs = json.load(f)

        return [
            Document(page_content=doc["page_content"], metadata=doc["metadata"])
            for doc in serialized_docs
        ]


@dg.io_manager(config_schema={"base_dir": str})
def document_io_manager(init_context) -> DocumentIOManager:
    return DocumentIOManager(base_dir=init_context.resource_config["base_dir"])
