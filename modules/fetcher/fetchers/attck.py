
import requests

from modules.config import ATTCK_DIRECT_URLS, ATTCK_VERSION_URLS, CACHE_DIR

from .base import BaseFetcher


class ATTCKFetcher(BaseFetcher):
    def __init__(self, variant: str = "enterprise"):
        self.variant = variant
        key = f"attck_{variant}"
        super().__init__(key)

    def get_remote_version(self) -> str | None:
        try:
            url = ATTCK_VERSION_URLS[self.source_name]
            resp = requests.get(url, timeout=15)
            commits = resp.json()
            if isinstance(commits, list) and commits:
                return commits[0]["sha"][:7]
        except (requests.RequestException, OSError, KeyError, ValueError) as e:
            print(f"[{self.source_name}] Failed to check version: {e}")
        return None

    def fetch(self) -> list[dict]:
        url = ATTCK_DIRECT_URLS[self.source_name]
        print(f"[{self.source_name}] Downloading from: {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        file_path = CACHE_DIR / f"{self.source_name}.json"
        with open(file_path, "wb") as f:
            f.writelines(resp.iter_content(8192))
        print(f"[{self.source_name}] Saved: {file_path}")
        return [{"source": self.source_name, "file": str(file_path)}]

    def run(self) -> dict:
        file_path = CACHE_DIR / f"{self.source_name}.json"
        if not self.needs_update():
            print(f"[{self.source_name}] Already up-to-date, using cache.")
            records = self.count_cached_records()
            return {
                "source": self.source_name,
                "status": "cached",
                "records": records,
                "file_path": str(file_path),
                "error": None,
            }
        try:
            self.fetch()
            records = self.count_cached_records()
            version = self.get_remote_version()
            if version:
                self.save_local_version(version)
            return {
                "source": self.source_name,
                "status": "success",
                "records": records,
                "file_path": str(file_path),
                "error": None,
            }
        except (requests.RequestException, OSError, KeyError, ValueError) as e:
            return {
                "source": self.source_name,
                "status": "failed",
                "records": 0,
                "file_path": "",
                "error": str(e),
            }
