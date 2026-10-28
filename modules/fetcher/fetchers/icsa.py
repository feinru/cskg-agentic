import requests
from modules.config import ICSA_FEED_URL
from .base import BaseFetcher


class ICSAFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("icsa")
        self.feed_url = ICSA_FEED_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.get(self.feed_url, timeout=15)
            return resp.json().get("dateReleased")
        except Exception as e:
            print(f"[icsa] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        print(f"[icsa] Downloading from: {self.feed_url}")
        resp = requests.get(self.feed_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vulnerabilities = data.get("vulnerabilities", [])
        print(f"[icsa] {len(vulnerabilities)} advisories found")
        return vulnerabilities
