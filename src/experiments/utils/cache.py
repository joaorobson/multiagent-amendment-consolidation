import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class SQLiteLLMCache:
    def __init__(self, db_path: str | Path = "../data/cache/llm_cache.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def build_key(
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> str:
        payload = {
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "schema": (
                response_format.model_json_schema()
                if response_format is not None
                else None
            ),
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(
        self, key: str, response_format: Optional[Type[T]] = None
    ) -> T | str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT response_json FROM llm_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        if response_format is None:
            return row[0]
        return response_format.model_validate_json(row[0])

    def set(self, key: str, model: str, result: BaseModel | str) -> None:
        serialized = (
            result.model_dump_json() if isinstance(result, BaseModel) else result
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO llm_cache (cache_key, model, response_json)
                VALUES (?, ?, ?)
                """,
                (key, model, serialized),
            )