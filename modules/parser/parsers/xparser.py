import xml.etree.ElementTree as ET
from .base import BaseParser


class XMLParser(BaseParser):
    def parse(self) -> list[dict]:
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        def strip_ns(tag: str) -> str:
            if "}" in tag:
                return tag.split("}", 1)[1]
            return tag

        entities = []
        if self.source_name == "cwe":
            for elem in root.iter():
                if strip_ns(elem.tag) == "Weakness":
                    entity = {"@xml_tag": "Weakness", "attribs": elem.attrib}
                    for child in elem:
                        tag = strip_ns(child.tag)
                        if tag == "Description":
                            entity["Description"] = child.text
                    entities.append(entity)
        elif self.source_name == "capec":
            for elem in root.iter():
                if strip_ns(elem.tag) == "Attack_Pattern":
                    entity = {"@xml_tag": "Attack_Pattern", "attribs": elem.attrib}
                    for child in elem:
                        tag = strip_ns(child.tag)
                        if tag == "Description":
                            entity["Description"] = child.text
                    entities.append(entity)
        return entities
