import json
from abc import ABC, abstractmethod

import ijson
import orjson

from modules.config import CACHE_DIR


class BaseFetcher(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.version_file = CACHE_DIR / f"{source_name}.version"

    def get_local_version(self) -> str | None:
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return None

    def save_local_version(self, version: str):
        self.version_file.write_text(version)

    @abstractmethod
    def get_remote_version(self) -> str | None:
        pass

    def needs_update(self) -> bool:
        remote = self.get_remote_version()
        local = self.get_local_version()
        print(f"[{self.source_name}] local: {local} | remote: {remote}")
        if local is None:
            print(f"[{self.source_name}] No local cache found, downloading.")
            return True
        if remote is None:
            print(f"[{self.source_name}] Unable to check remote version, using cache.")
            return False
        return remote != local

    @abstractmethod
    def fetch(self) -> list[dict]:
        pass

    def save_to_cache(self, data: list[dict]) -> str:
        file_path = CACHE_DIR / f"{self.source_name}.json"
        with open(file_path, "wb") as f:
            f.write(orjson.dumps(data))
        print(f"[{self.source_name}] saved: {len(data):,} records -> {file_path}")
        return str(file_path)

    def count_cached_records(self) -> int:
        file_path = CACHE_DIR / f"{self.source_name}.json"
        if not file_path.exists():
            return 0
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb < 5.0:
            try:
                with open(file_path, "rb") as f:
                    data = orjson.loads(f.read())
                if isinstance(data, list):
                    return len(data)
                if isinstance(data, dict):
                    for k in ("vulnerabilities", "products", "objects", "scores"):
                        if k in data and isinstance(data[k], list):
                            return len(data[k])
                    return 1
            except (OSError, json.JSONDecodeError, KeyError):
                return 0
        # Stream-count without loading entire file into memory heap
        count = 0
        try:
            with open(file_path, "rb") as f:
                first = f.read(1)
                while first in b" \t\r\n":
                    first = f.read(1)
                f.seek(0)
                if first == b"[":
                    for _ in ijson.items(f, "item"):
                        count += 1
                    return count
                elif first == b"{":
                    target_key = "objects.item"
                    if self.source_name in ("cve", "icsa"):
                        target_key = "vulnerabilities.item"
                    elif self.source_name == "cpe":
                        target_key = "products.item"
                    elif self.source_name == "epss":
                        target_key = "scores.item"
                    for _ in ijson.items(f, target_key):
                        count += 1
                    return count
        except (OSError, ijson.common.IncompleteJSONError):
            return 0
        return count

    def load_from_cache(self) -> list[dict]:
        file_path = CACHE_DIR / f"{self.source_name}.json"
        if not file_path.exists():
            return []
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10.0:
            return []
        with open(file_path, "rb") as f:
            return orjson.loads(f.read())

    def run(self) -> dict:
        if not self.needs_update():
            print(f"[{self.source_name}] Already up-to-date, using cache.")
            record_count = self.count_cached_records()
            return {
                "source": self.source_name,
                "status": "cached",
                "records": record_count,
                "file_path": str(CACHE_DIR / f"{self.source_name}.json"),
                "error": None,
            }
        try:
            data = self.fetch()
            target_path = CACHE_DIR / f"{self.source_name}.json"
            if data:
                file_path = self.save_to_cache(data)
            else:
                file_path = str(target_path)
            version = self.get_remote_version()
            if version:
                self.save_local_version(version)
            record_count = self.count_cached_records()
            return {
                "source": self.source_name,
                "status": "success",
                "records": record_count,
                "file_path": file_path,
                "error": None,
            }
        except (OSError, RuntimeError, ValueError, KeyError) as e:
            return {
                "source": self.source_name,
                "status": "failed",
                "records": 0,
                "file_path": "",
                "error": str(e),
            }
