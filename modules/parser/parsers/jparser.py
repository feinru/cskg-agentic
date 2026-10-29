from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import ijson
import orjson

from .base import BaseParser


class JSONParser(BaseParser):
    def parse_iter(self) -> Iterator[dict[str, Any]]:
        file_size_mb = self.file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10.0:
            with open(self.file_path, "rb") as f:
                first = f.read(1)
                while first in b" \t\r\n":
                    first = f.read(1)
                f.seek(0)
                if first == b"[":
                    for item in ijson.items(f, "item"):
                        if isinstance(item, dict):
                            yield item
                    return
                elif first == b"{":
                    key_map = {
                        "cve": ("vulnerabilities",),
                        "cpe": ("products",),
                        "icsa": ("vulnerabilities",),
                        "epss": ("scores",),
                    }
                    candidate_keys = list(key_map.get(self.source_name, ()))
                    if self.source_name.startswith("attck"):
                        candidate_keys = ["objects"]
                    for k in ("products", "vulnerabilities", "objects", "scores"):
                        if k not in candidate_keys:
                            candidate_keys.append(k)

                    for key in candidate_keys:
                        try:
                            f.seek(0)
                            gen = ijson.items(f, f"{key}.item")
                            first_item = next(gen)
                            if isinstance(first_item, dict):
                                yield first_item
                            for item in gen:
                                if isinstance(item, dict):
                                    yield item
                            return
                        except (StopIteration, ijson.common.IncompleteJSONError):
                            continue

            if file_size_mb > 50.0:
                print(
                    f"[Parser] WARNING: File {self.file_path.name} ({file_size_mb:.1f} MB) "
                    "could not be streamed via ijson and is too large to load in RAM safely."
                )
                return

        with open(self.file_path, "rb") as f:
            data = orjson.loads(f.read())

        if self.source_name in ("cve", "icsa"):
            if isinstance(data, dict) and "vulnerabilities" in data:
                yield from data["vulnerabilities"]
                return
        elif self.source_name == "cpe":
            if isinstance(data, dict) and "products" in data:
                yield from data["products"]
                return
        elif self.source_name.startswith("attck"):
            if isinstance(data, dict) and "objects" in data:
                yield from data["objects"]
                return
        elif self.source_name == "epss":
            if isinstance(data, list):
                yield from data
                return
            if isinstance(data, dict) and "scores" in data:
                yield from data["scores"]
                return

        if isinstance(data, list):
            yield from data
        elif isinstance(data, dict):
            yield data

    def parse(self) -> list[dict[str, Any]]:
        return list(self.parse_iter())
