import ijson
import requests

from modules.config import CACHE_DIR, D3FEND_MAPPINGS_URL, D3FEND_ONTOLOGY_URL

from .base import BaseFetcher


class D3FENDFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("d3fend")
        self.ontology_url = D3FEND_ONTOLOGY_URL
        self.mappings_url = D3FEND_MAPPINGS_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.head(self.ontology_url, timeout=15)
            last_mod = resp.headers.get("Last-Modified")
            etag = resp.headers.get("ETag")
            if last_mod:
                return last_mod
            if etag:
                return etag.strip('"')
        except (requests.RequestException, OSError, ValueError) as e:
            print(f"[d3fend] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        print(f"[d3fend] Downloading ontology from: {self.ontology_url}")
        resp_ont = requests.get(self.ontology_url, stream=True, timeout=120)
        resp_ont.raise_for_status()

        ttl_path = CACHE_DIR / "d3fend.ttl"
        with open(ttl_path, "wb") as f:
            f.writelines(resp_ont.iter_content(8192))
        print(f"[d3fend] Saved ontology: {ttl_path}")

        print(f"[d3fend] Downloading technique mappings from: {self.mappings_url}")
        resp_map = requests.get(self.mappings_url, stream=True, timeout=60)
        resp_map.raise_for_status()

        map_path = CACHE_DIR / "d3fend_mappings.json"
        with open(map_path, "wb") as f:
            f.writelines(resp_map.iter_content(8192))
        print(f"[d3fend] Saved mappings: {map_path}")

        return [
            {
                "source": "d3fend",
                "file": str(ttl_path),
                "mappings": str(map_path),
            }
        ]

    def run(self) -> dict:
        ttl_path = CACHE_DIR / "d3fend.ttl"
        map_path = CACHE_DIR / "d3fend_mappings.json"
        if not self.needs_update():
            print(f"[{self.source_name}] Already up-to-date, using cache.")
            mappings_count = 0
            if map_path.exists():
                try:
                    with open(map_path, "rb") as f:
                        for _ in ijson.items(f, "results.bindings.item"):
                            mappings_count += 1
                except (OSError, ijson.common.IncompleteJSONError):
                    pass
            return {
                "source": self.source_name,
                "status": "cached",
                "records": mappings_count,
                "file_path": str(ttl_path),
                "error": None,
            }
        try:
            pointer = self.fetch()
            self.save_to_cache(pointer)
            version = self.get_remote_version()
            if version:
                self.save_local_version(version)
            mappings_count = 0
            if map_path.exists():
                try:
                    with open(map_path, "rb") as f:
                        for _ in ijson.items(f, "results.bindings.item"):
                            mappings_count += 1
                except (OSError, ijson.common.IncompleteJSONError):
                    pass
            return {
                "source": self.source_name,
                "status": "success",
                "records": mappings_count,
                "file_path": str(ttl_path),
                "error": None,
            }
        except (requests.RequestException, OSError, RuntimeError, ValueError) as e:
            return {
                "source": self.source_name,
                "status": "failed",
                "records": 0,
                "file_path": "",
                "error": str(e),
            }
