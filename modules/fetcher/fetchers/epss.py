import csv
import gzip
import io

import orjson
import requests

from modules.config import CACHE_DIR, EPSS_FEED_URL, NVD_MAX_DEMO

from .base import BaseFetcher


class EPSSFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("epss")
        self.feed_url = EPSS_FEED_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.head(self.feed_url, timeout=15)
            last_mod = resp.headers.get("Last-Modified")
            etag = resp.headers.get("ETag")
            if last_mod:
                return last_mod
            if etag:
                return etag.strip('"')
            resp = requests.get(self.feed_url, stream=True, timeout=15)
            with gzip.GzipFile(fileobj=resp.raw) as gz:
                first_line = gz.readline().decode("utf-8", errors="ignore").strip()
                if "score_date:" in first_line:
                    return first_line.split("score_date:")[-1].split(",")[0].strip()
        except (requests.RequestException, OSError, ValueError) as e:
            print(f"[epss] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        print(f"[epss] Downloading from: {self.feed_url}")
        resp = requests.get(self.feed_url, stream=True, timeout=120)
        resp.raise_for_status()

        gz_stream = gzip.GzipFile(fileobj=resp.raw)
        reader = io.BufferedReader(gz_stream)

        first_line = reader.readline().decode("utf-8", errors="ignore").strip()
        print(f"[epss] Header info: {first_line}")

        text_stream = io.TextIOWrapper(reader, encoding="utf-8")
        csv_reader = csv.DictReader(text_stream)

        out_file = CACHE_DIR / "epss.json"
        tmp_file = out_file.with_suffix(".tmp")
        limit = NVD_MAX_DEMO
        count = 0
        with open(tmp_file, "w", encoding="utf-8", buffering=2 * 1024 * 1024) as out_f:
            out_f.write("[\n")
            first = True
            for row in csv_reader:
                cve_id = row.get("cve")
                epss_score = row.get("epss")
                percentile = row.get("percentile")
                if not cve_id or not epss_score:
                    continue
                record = {
                    "cve": cve_id,
                    "epss": epss_score,
                    "percentile": percentile,
                }
                if not first:
                    out_f.write(",\n")
                out_f.write(orjson.dumps(record).decode("utf-8"))
                first = False
                count += 1
                if limit and count >= limit:
                    print(f"[epss] Demo cap reached: {count} records")
                    break
            out_f.write("\n]\n")
        tmp_file.replace(out_file)
        print(f"[epss] Streamed {count:,} EPSS records directly to {out_file}")
        return []
