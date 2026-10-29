from __future__ import annotations

import collections
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import orjson
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from modules.config import (
    CACHE_DIR,
    NVD_API_KEY,
    NVD_CPE_URL,
    NVD_CVE_URL,
)
from modules.config import (
    NVD_MAX_DEMO as MAX_DEMO,
)
from modules.config import (
    NVD_PAGE_SIZE as PAGE_SIZE,
)

from .base import BaseFetcher


class SlidingWindowRateLimiter:
    def __init__(self, max_calls: int, period_seconds: float) -> None:
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.timestamps: collections.deque[float] = collections.deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                while (
                    self.timestamps
                    and (now - self.timestamps[0]) >= self.period_seconds
                ):
                    self.timestamps.popleft()

                if len(self.timestamps) < self.max_calls:
                    self.timestamps.append(now)
                    return

                wait_time = self.period_seconds - (now - self.timestamps[0]) + 0.05
            time.sleep(max(0.02, wait_time))


def _get_headers() -> dict[str, str]:
    if NVD_API_KEY:
        return {"apiKey": NVD_API_KEY}
    return {}


def _create_http_session(pool_size: int) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        pool_connections=pool_size,
        pool_maxsize=pool_size,
        max_retries=retries,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _fetch_page_worker(
    session: requests.Session,
    base_url: str,
    source_name: str,
    item_key: str,
    start_index: int,
    batch_size: int,
    rate_limiter: SlidingWindowRateLimiter,
    checkpoint_file: Path,
    max_retries: int = 5,
) -> int:
    if checkpoint_file.exists() and checkpoint_file.stat().st_size > 10:
        return 0

    headers = _get_headers()
    params = {"resultsPerPage": batch_size, "startIndex": start_index}

    for attempt in range(max_retries):
        rate_limiter.acquire()
        t0 = time.monotonic()
        try:
            resp = session.get(base_url, params=params, headers=headers, timeout=90)
            elapsed = time.monotonic() - t0

            if resp.status_code == 200:
                body = resp.json()
                items: list[dict[str, Any]] = body.get(item_key, [])

                tmp_file = checkpoint_file.with_suffix(".tmp")
                with open(tmp_file, "wb") as f:
                    f.write(orjson.dumps(items))
                tmp_file.replace(checkpoint_file)

                return len(items)

            if resp.status_code in (403, 429, 503):
                backoff = min(60.0, (2**attempt) * 5.0)
                print(
                    f"[{source_name}] Rate/load limited ({resp.status_code}) on index {start_index}. "
                    f"Backing off {backoff:.1f}s (attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(backoff)
            else:
                print(
                    f"[{source_name}] HTTP {resp.status_code} on index {start_index}: {resp.text[:150]}"
                )
                time.sleep(3.0)

        except requests.RequestException as exc:
            elapsed = time.monotonic() - t0
            backoff = min(30.0, (attempt + 1) * 4.0)
            print(
                f"[{source_name}] Network error on index {start_index} after {elapsed:.1f}s: {exc}. "
                f"Retrying in {backoff:.1f}s..."
            )
            time.sleep(backoff)

    print(
        f"[{source_name}] Failed to fetch page starting at {start_index} after {max_retries} attempts."
    )
    return 0


def _fetch_nvd_concurrent(
    base_url: str,
    source_name: str,
    item_key: str,
) -> list[dict[str, Any]]:
    session = _create_http_session(pool_size=12)
    headers = _get_headers()

    try:
        resp = session.get(
            base_url,
            params={"resultsPerPage": 1, "startIndex": 0},
            headers=headers,
            timeout=45,
        )
        total = resp.json().get("totalResults", 0)
    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"[{source_name}] Error probing total results: {e}")
        return []

    target_total = MAX_DEMO if (MAX_DEMO is not None and MAX_DEMO > 0) else total
    if target_total < total:
        print(
            f"[{source_name}] Capped mode: fetching first {target_total:,} of {total:,} records"
        )
    else:
        print(f"[{source_name}] Full dataset mode: fetching all {total:,} records")

    if NVD_API_KEY:
        max_workers = int(os.getenv("NVD_WORKERS", "6"))
        rate_limiter = SlidingWindowRateLimiter(max_calls=40, period_seconds=30.0)
    else:
        max_workers = 1
        rate_limiter = SlidingWindowRateLimiter(max_calls=4, period_seconds=30.0)

    checkpoint_dir = CACHE_DIR / f".{source_name}_pages"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    page_indices = list(range(0, target_total, PAGE_SIZE))
    total_pages = len(page_indices)

    completed_indices: set[int] = set()
    pending_indices: list[int] = []

    for idx in page_indices:
        chk_file = checkpoint_dir / f"page_{idx:08d}.json"
        if chk_file.exists() and chk_file.stat().st_size > 10:
            completed_indices.add(idx)
        else:
            pending_indices.append(idx)

    cached_count = len(completed_indices)
    if cached_count > 0:
        print(
            f"[{source_name}] Resuming from checkpoint: {cached_count}/{total_pages} pages already on disk."
        )

    if pending_indices:
        print(
            f"[{source_name}] Dispatching {len(pending_indices)} pending pages "
            f"across {max_workers} worker threads..."
        )

        worker_session = _create_http_session(pool_size=max_workers * 2)
        start_time = time.monotonic()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    _fetch_page_worker,
                    worker_session,
                    base_url,
                    source_name,
                    item_key,
                    idx,
                    min(PAGE_SIZE, target_total - idx),
                    rate_limiter,
                    checkpoint_dir / f"page_{idx:08d}.json",
                ): idx
                for idx in pending_indices
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    num_items = future.result()
                    completed_indices.add(idx)
                    done_count = len(completed_indices)
                    pct = (done_count / total_pages) * 100.0
                    print(
                        f"[{source_name}] Progress: page {done_count}/{total_pages} "
                        f"({pct:.1f}%) | index {idx:,} saved {num_items:,} items"
                    )
                except (requests.RequestException, OSError, RuntimeError) as exc:
                    print(f"[{source_name}] Exception on page index {idx}: {exc}")

        total_elapsed = time.monotonic() - start_time
        print(
            f"[{source_name}] Completed fetching {len(pending_indices)} pages in {total_elapsed:.1f}s."
        )

    # Stream assemble directly to CACHE_DIR / f"{source_name}.json" without loading entire dataset into RAM
    cache_file = CACHE_DIR / f"{source_name}.json"
    tmp_cache = cache_file.with_suffix(".tmp")
    total_records = 0
    print(f"[{source_name}] Stream assembling {total_pages} pages into {cache_file}...")
    with open(tmp_cache, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
        out_f.write("[\n")
        first_item = True
        for idx in sorted(page_indices):
            chk_file = checkpoint_dir / f"page_{idx:08d}.json"
            if not chk_file.exists():
                continue
            with open(chk_file, "rb") as pf:
                page_data = orjson.loads(pf.read())
            if isinstance(page_data, list):
                for item in page_data:
                    if not first_item:
                        out_f.write(",\n")
                    out_f.write(orjson.dumps(item).decode("utf-8"))
                    first_item = False
                    total_records += 1
        out_f.write("\n]\n")
    tmp_cache.replace(cache_file)
    print(f"[{source_name}] Stream assembled {total_records:,} records -> {cache_file}")
    return []


class CVEFetcher(BaseFetcher):
    def __init__(self) -> None:
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
            total = data.get("totalResults", 0)
            if data.get("vulnerabilities"):
                last_mod = data["vulnerabilities"][0]["cve"]["lastModified"]
                return f"{total}_{last_mod}"
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"[cve] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict[str, Any]]:
        return _fetch_nvd_concurrent(
            base_url=self.base_url,
            source_name="cve",
            item_key="vulnerabilities",
        )


class CPEFetcher(BaseFetcher):
    def __init__(self) -> None:
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
            total = data.get("totalResults", 0)
            if data.get("products"):
                last_mod = data["products"][0]["cpe"]["lastModified"]
                return f"{total}_{last_mod}"
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"[cpe] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict[str, Any]]:
        return _fetch_nvd_concurrent(
            base_url=self.base_url,
            source_name="cpe",
            item_key="products",
        )
