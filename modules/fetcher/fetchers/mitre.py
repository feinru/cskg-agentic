import requests
import zipfile
import re
from pathlib import Path
from modules.config import (
    CWE_DOWNLOAD_PAGE,
    CWE_URL,
    CAPEC_DOWNLOAD_PAGE,
    CAPEC_URL,
    CACHE_DIR,
)
from .base import BaseFetcher


class CWEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("cwe")
        self.download_page = CWE_DOWNLOAD_PAGE
        self.base_url = CWE_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.get(self.download_page, timeout=15)
            match = re.search("CWE List Version ([\\d.]+)", resp.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"[cwe] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        zip_path = CACHE_DIR / "cwe.zip"
        print(f"[cwe] Downloading from: {self.base_url}")
        resp = requests.get(self.base_url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        with zipfile.ZipFile(zip_path, "r") as z:
            xml_files = [n for n in z.namelist() if n.endswith(".xml")]
            if not xml_files:
                raise ValueError("No XML file found inside CWE zip")
            xml_file = xml_files[0]
            z.extract(xml_file, CACHE_DIR)
            extracted_path = CACHE_DIR / xml_file
        print(f"[cwe] XML file saved: {extracted_path}")
        return [{"source": "cwe", "file": str(extracted_path)}]


class CAPECFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("capec")
        self.download_page = CAPEC_DOWNLOAD_PAGE
        self.base_url = CAPEC_URL

    def get_remote_version(self) -> str | None:
        try:
            resp = requests.get(self.download_page, timeout=15)
            match = re.search("CAPEC List Version ([\\d.]+)", resp.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"[capec] Failed to check remote version: {e}")
        return None

    def fetch(self) -> list[dict]:
        xml_path = CACHE_DIR / "capec.xml"
        print(f"[capec] Downloading from: {self.base_url}")
        resp = requests.get(self.base_url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(xml_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        print(f"[capec] XML file saved: {xml_path}")
        return [{"source": "capec", "file": str(xml_path)}]
