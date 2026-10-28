import requests
import time
from modules.config import (
    NVD_API_KEY,
    NVD_DELAY,
    NVD_PAGE_SIZE as PAGE_SIZE,
    NVD_MAX_DEMO as MAX_DEMO,
    NVD_CVE_URL,
    NVD_CPE_URL,
)
from .base import BaseFetcher


def _get_headers():
    if NVD_API_KEY:
        return {"apiKey": NVD_API_KEY}
    return {}


class CVEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("cve")
        self.base_url = NVD_CVE_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.get(
                self.base_url,
                params={"resultsPerPage": 1},
                headers=_get_headers(),
                timeout=30,
            )
            data = resp.json()
            if data.get("vulnerabilities"):
                return data["vulnerabilities"][0]["cve"]["lastModified"]
        except Exception as e:
            print(f"[cve] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        all_cves = []
        start_index = 0
        resp = requests.get(
            self.base_url,
            params={"resultsPerPage": 1, "startIndex": 0},
            headers=_get_headers(),
            timeout=30,
        )
        try:
            total = resp.json().get("totalResults", 0)
        except Exception as e:
            print(
                f"[cve] Error fetching total results: {e}, status: {resp.status_code}"
            )
            return []
        print(f"[cve] Total CVEs available: {total:,}")
        print(f"[cve] Demo mode: fetching first {MAX_DEMO} records")
        time.sleep(NVD_DELAY)
        while len(all_cves) < MAX_DEMO:
            batch_size = min(PAGE_SIZE, MAX_DEMO - len(all_cves))
            print(f"[cve] Page: records {start_index} to {start_index + batch_size}")
            resp = requests.get(
                self.base_url,
                params={"resultsPerPage": batch_size, "startIndex": start_index},
                headers=_get_headers(),
                timeout=60,
            )
            try:
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(
                    f"[cve] Error: {e}, status: {resp.status_code}, body: {resp.text[:200]}"
                )
                break
            vulnerabilities = data.get("vulnerabilities", [])
            if not vulnerabilities:
                break
            all_cves.extend(vulnerabilities)
            print(f"[cve] Collected: {len(all_cves)}")
            if len(all_cves) >= MAX_DEMO:
                break
            start_index += batch_size
            time.sleep(NVD_DELAY)
        return all_cves


class CPEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("cpe")
        self.base_url = NVD_CPE_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.get(
                self.base_url,
                params={"resultsPerPage": 1},
                headers=_get_headers(),
                timeout=30,
            )
            data = resp.json()
            if data.get("products"):
                return data["products"][0]["cpe"]["lastModified"]
        except Exception as e:
            print(f"[cpe] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        all_cpes = []
        start_index = 0
        resp = requests.get(
            self.base_url,
            params={"resultsPerPage": 1, "startIndex": 0},
            headers=_get_headers(),
            timeout=30,
        )
        try:
            total = resp.json().get("totalResults", 0)
        except Exception as e:
            print(
                f"[cpe] Error fetching total results: {e}, status: {resp.status_code}"
            )
            return []
        print(f"[cpe] Total CPEs available: {total:,}")
        print(f"[cpe] Demo mode: fetching first {MAX_DEMO} records")
        time.sleep(NVD_DELAY)
        while len(all_cpes) < MAX_DEMO:
            batch_size = min(PAGE_SIZE, MAX_DEMO - len(all_cpes))
            print(f"[cpe] Page: records {start_index} to {start_index + batch_size}")
            resp = requests.get(
                self.base_url,
                params={"resultsPerPage": batch_size, "startIndex": start_index},
                headers=_get_headers(),
                timeout=60,
            )
            try:
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(
                    f"[cpe] Error: {e}, status: {resp.status_code}, body: {resp.text[:200]}"
                )
                break
            products = data.get("products", [])
            if not products:
                break
            all_cpes.extend(products)
            print(f"[cpe] Collected: {len(all_cpes)}")
            if len(all_cpes) >= MAX_DEMO:
                break
            start_index += batch_size
            time.sleep(NVD_DELAY)
        return all_cpes
