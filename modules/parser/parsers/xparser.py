from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from typing import Any

from .base import BaseParser


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class XMLParser(BaseParser):
    def parse_iter(self) -> Iterator[dict[str, Any]]:
        target_tag = "Weakness" if self.source_name == "cwe" else "Attack_Pattern"
        context = ET.iterparse(str(self.file_path), events=("end",))
        for _, elem in context:
            if _strip_ns(elem.tag) == target_tag:
                entity: dict[str, Any] = {
                    "@xml_tag": target_tag,
                    "attribs": dict(elem.attrib),
                }
                for child in elem:
                    tag = _strip_ns(child.tag)
                    if tag == "Description":
                        entity["Description"] = child.text
                yield entity
                elem.clear()

    def parse(self) -> list[dict[str, Any]]:
        return list(self.parse_iter())

