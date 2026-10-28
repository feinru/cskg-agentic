from abc import ABC, abstractmethod
import json
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
        with open(file_path, "w") as f:
            json.dump(data, f)
        print(f"[{self.source_name}] saved: {len(data)} records -> {file_path}")
        return str(file_path)

    def load_from_cache(self) -> list[dict]:
        file_path = CACHE_DIR / f"{self.source_name}.json"
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return []

    def run(self) -> dict:
        if not self.needs_update():
            print(f"[{self.source_name}] Already up-to-date, using cache.")
            data = self.load_from_cache()
            return {
                "source": self.source_name,
                "status": "cached",
                "records": len(data),
                "file_path": str(CACHE_DIR / f"{self.source_name}.json"),
                "error": None,
            }
        try:
            data = self.fetch()
            file_path = self.save_to_cache(data)
            version = self.get_remote_version()
            if version:
                self.save_local_version(version)
            return {
                "source": self.source_name,
                "status": "success",
                "records": len(data),
                "file_path": file_path,
                "error": None,
            }
        except Exception as e:
            return {
                "source": self.source_name,
                "status": "failed",
                "records": 0,
                "file_path": "",
                "error": str(e),
            }
