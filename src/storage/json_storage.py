import json
import os
from uuid import uuid4


class JsonStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list:
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        return json.loads(content)

    def save(self, data: list) -> None:
        tmp_path = f"{self.file_path}.{uuid4().hex}.tmp"

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp_path, self.file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
