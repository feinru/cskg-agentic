import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "modules" / "fetcher" / "cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)
PARSER_OUTPUT_DIR = BASE_DIR / "modules" / "parser" / "output"
LINKING_OUTPUT_DIR = BASE_DIR / "modules" / "linking" / "output"
VALIDATION_REPORTS_DIR = BASE_DIR / "modules" / "validation" / "output" / "reports"
SPARQL_DATA_DIR = BASE_DIR / "sparql" / "data"

NVD_API_KEY = os.getenv("NVD_API_KEY")
NVD_DELAY = 0.6 if NVD_API_KEY else 6
NVD_PAGE_SIZE = 2000
NVD_MAX_DEMO = int(os.getenv("NVD_MAX_DEMO", "0")) or None

NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_CPE_URL = "https://services.nvd.nist.gov/rest/json/cpes/2.0"

CWE_DOWNLOAD_PAGE = "https://cwe.mitre.org/data/downloads.html"
CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"

CAPEC_DOWNLOAD_PAGE = "https://capec.mitre.org/data/downloads.html"
CAPEC_URL = "https://capec.mitre.org/data/xml/capec_latest.xml"

ICSA_FEED_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_FEED_URL = "https://epss.cyentia.com/epss_scores-current.csv.gz"
D3FEND_ONTOLOGY_URL = "https://d3fend.mitre.org/ontologies/d3fend.ttl"
D3FEND_MAPPINGS_URL = (
    "https://d3fend.mitre.org/ontologies/d3fend/1.6.0/d3fend-full-mappings.json"
)

ATTCK_DIRECT_URLS = {
    "attck_enterprise": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
    "attck_ics": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/ics-attack/ics-attack.json",
    "attck_mobile": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/mobile-attack/mobile-attack.json",
}
ATTCK_VERSION_URLS = {
    "attck_enterprise": "https://api.github.com/repos/mitre-attack/attack-stix-data/commits?path=enterprise-attack/enterprise-attack.json&per_page=1",
    "attck_ics": "https://api.github.com/repos/mitre-attack/attack-stix-data/commits?path=ics-attack/ics-attack.json&per_page=1",
    "attck_mobile": "https://api.github.com/repos/mitre-attack/attack-stix-data/commits?path=mobile-attack/mobile-attack.json&per_page=1",
}

SOURCE_DESCRIPTIONS = {
    "cve": "Known public vulnerabilities and exposures",
    "cpe": "Common Platform Enumeration standard names",
    "cwe": "Common Weakness Enumeration catalog",
    "capec": "Common Attack Pattern Enumeration and Classification",
    "attck_enterprise": "MITRE ATT&CK tactics and techniques (Enterprise)",
    "attck_ics": "MITRE ATT&CK tactics and techniques (ICS/OT)",
    "attck_mobile": "MITRE ATT&CK tactics and techniques (Mobile)",
    "icsa": "CISA Known Exploited Vulnerabilities advisories",
    "epss": "FIRST.org Exploit Prediction Scoring System (EPSS)",
    "d3fend": "MITRE D3FEND defensive cybersecurity ontology and countermeasure matrix",
}

VOCAB_NS = {
    "cve": "http://w3id.org/sepses/vocab/ref/cve#",
    "cwe": "http://w3id.org/sepses/vocab/ref/cwe#",
    "cpe": "http://w3id.org/sepses/vocab/ref/cpe#",
    "capec": "http://w3id.org/sepses/vocab/ref/capec#",
    "icsa": "http://w3id.org/sepses/vocab/ref/icsa#",
    "attck_enterprise": "http://w3id.org/sepses/vocab/ref/attack#",
    "attck_ics": "http://w3id.org/sepses/vocab/ref/attack#",
    "attck_mobile": "http://w3id.org/sepses/vocab/ref/attack#",
    "epss": "http://w3id.org/sepses/vocab/ref/epss#",
    "d3fend": "http://d3fend.mitre.org/ontologies/d3fend.owl#",
}

NAMESPACES = {
    "cve": "http://w3id.org/sepses/vocab/ref/cve#",
    "cwe": "http://w3id.org/sepses/vocab/ref/cwe#",
    "capec": "http://w3id.org/sepses/vocab/ref/capec#",
    "cpe": "http://w3id.org/sepses/vocab/ref/cpe#",
    "cvss": "http://w3id.org/sepses/vocab/ref/cvss#",
    "attck": "http://w3id.org/sepses/vocab/ref/attack#",
    "icsa": "http://w3id.org/sepses/vocab/ref/icsa#",
    "epss": "http://w3id.org/sepses/vocab/ref/epss#",
    "d3fend": "http://d3fend.mitre.org/ontologies/d3fend.owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

RESOURCE_BASE = "http://w3id.org/sepses/resource/"

RESOURCE_BASE_MAP = {
    "cve": "http://w3id.org/sepses/resource/cve/",
    "cwe": "http://w3id.org/sepses/resource/cwe/",
    "capec": "http://w3id.org/sepses/resource/capec/",
    "cpe": "http://w3id.org/sepses/resource/cpe/",
    "attck": "http://w3id.org/sepses/resource/attack/",
    "icsa": "http://w3id.org/sepses/resource/icsa/",
    "epss": "http://w3id.org/sepses/resource/epss/",
    "d3fend": "http://d3fend.mitre.org/ontologies/d3fend.owl#",
}

LINKING_RULES = [
    {
        "link_type": "cve2cwe",
        "subject_src": "cve",
        "object_src": "cwe",
        "predicate": "cve:hasCWE",
        "description": "CVE vulnerability linked to CWE weakness",
    },
    {
        "link_type": "cve2cpe",
        "subject_src": "cve",
        "object_src": "cpe",
        "predicate": "cve:hasCPE",
        "description": "CVE vulnerability linked to affected CPE product",
    },
    {
        "link_type": "cwe2capec",
        "subject_src": "cwe",
        "object_src": "capec",
        "predicate": "cwe:hasCAPEC",
        "description": "CWE weakness linked to CAPEC attack pattern",
    },
    {
        "link_type": "capec2attck",
        "subject_src": "capec",
        "object_src": "attck",
        "predicate": "capec:hasRelatedAttackPattern",
        "description": "CAPEC attack pattern linked to MITRE ATT&CK technique",
    },
    {
        "link_type": "icsa2cve",
        "subject_src": "icsa",
        "object_src": "cve",
        "predicate": "icsa:hasCVE",
        "description": "ICSA advisory linked to CVE vulnerability",
    },
    {
        "link_type": "cve2epss",
        "subject_src": "cve",
        "object_src": "epss",
        "predicate": "cve:hasEPSS",
        "description": "CVE vulnerability linked to EPSS exploit probability scores",
    },
    {
        "link_type": "d3fend2attck",
        "subject_src": "d3fend",
        "object_src": "attck",
        "predicate": "d3fend:counters",
        "description": "MITRE D3FEND defensive countermeasure linked to ATT&CK technique",
    },
]

VALIDATION_RULES = {
    "http://w3id.org/sepses/vocab/ref/cve#CVE": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/cve#id": {
                "type": "literal",
                "regex": "^CVE-\\d{4}-\\d{4,}$",
                "severity": "ERROR",
                "description": "CVE identifier must match standard NVD format (CVE-YYYY-NNNN+)",
            },
            "http://w3id.org/sepses/vocab/ref/cve#description": {
                "type": "literal",
                "severity": "WARNING",
                "description": "Detailed description of the cybersecurity vulnerability",
            },
        },
        "links": {
            "http://w3id.org/sepses/vocab/ref/cve#hasCWE": {
                "target_class": "http://w3id.org/sepses/vocab/ref/cwe#CWE",
                "severity": "WARNING",
                "description": "Relation linking CVE vulnerability to associated CWE weakness",
            },
            "http://w3id.org/sepses/vocab/ref/cve#hasCPE": {
                "target_class": "http://w3id.org/sepses/vocab/ref/cpe#CPE",
                "severity": "WARNING",
                "description": "Relation linking CVE vulnerability to affected CPE product",
            },
        },
    },
    "http://w3id.org/sepses/vocab/ref/cwe#CWE": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/cwe#id": {
                "type": "literal",
                "regex": "^CWE-\\d+$",
                "severity": "ERROR",
                "description": "CWE identifier must match standard MITRE format (CWE-ID)",
            },
            "http://w3id.org/sepses/vocab/ref/cwe#name": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Official weakness name",
            },
            "http://w3id.org/sepses/vocab/ref/cwe#description": {
                "type": "literal",
                "severity": "WARNING",
                "description": "Technical description of the weakness",
            },
        },
        "links": {
            "http://w3id.org/sepses/vocab/ref/cwe#hasCAPEC": {
                "target_class": "http://w3id.org/sepses/vocab/ref/capec#CAPEC",
                "severity": "WARNING",
                "description": "Relation linking CWE weakness to related CAPEC attack pattern",
            }
        },
    },
    "http://w3id.org/sepses/vocab/ref/capec#CAPEC": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/capec#id": {
                "type": "literal",
                "regex": "^CAPEC-\\d+$",
                "severity": "ERROR",
                "description": "CAPEC identifier must match standard MITRE format (CAPEC-ID)",
            },
            "http://w3id.org/sepses/vocab/ref/capec#name": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Official name of the attack pattern",
            },
            "http://w3id.org/sepses/vocab/ref/capec#description": {
                "type": "literal",
                "severity": "WARNING",
                "description": "Technical description of the attack pattern",
            },
        },
        "links": {
            "http://w3id.org/sepses/vocab/ref/capec#hasRelatedAttackPattern": {
                "target_class": "http://w3id.org/sepses/vocab/ref/attack#AttackPattern",
                "severity": "WARNING",
                "description": "Relation linking CAPEC attack pattern to related MITRE ATT&CK technique",
            }
        },
    },
    "http://w3id.org/sepses/vocab/ref/cpe#CPE": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/cpe#id": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Unique CPE Name Identifier",
            },
            "http://w3id.org/sepses/vocab/ref/cpe#cpe23Uri": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Formal CPE v2.3 URI string",
            },
        }
    },
    "http://w3id.org/sepses/vocab/ref/icsa#ICSA": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/icsa#cveID": {
                "type": "literal",
                "regex": "^CVE-\\d{4}-\\d{4,}$",
                "severity": "ERROR",
                "description": "Referenced CVE ID in ICSA advisory",
            },
            "http://w3id.org/sepses/vocab/ref/icsa#vendorProject": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Vendor or project name",
            },
            "http://w3id.org/sepses/vocab/ref/icsa#product": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Affected product name",
            },
        },
        "links": {
            "http://w3id.org/sepses/vocab/ref/icsa#hasCVE": {
                "target_class": "http://w3id.org/sepses/vocab/ref/cve#CVE",
                "severity": "WARNING",
                "description": "Relation from ICSA advisory to CVE vulnerability entity",
            }
        },
    },
    "http://w3id.org/sepses/vocab/ref/attack#AttackPattern": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/attack#id": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Technical STIX identifier of the attack pattern",
            },
            "http://w3id.org/sepses/vocab/ref/attack#name": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Name of the ATT&CK technique",
            },
            "http://w3id.org/sepses/vocab/ref/attack#techniqueId": {
                "type": "literal",
                "regex": "^T\\d{4}(?:\\.\\d{3})?$",
                "severity": "ERROR",
                "description": "Official MITRE ATT&CK technique identifier (e.g. T1059)",
            },
        }
    },
    "http://w3id.org/sepses/vocab/ref/epss#EPSS": {
        "mandatory_properties": {
            "http://w3id.org/sepses/vocab/ref/epss#cveID": {
                "type": "literal",
                "regex": "^CVE-\\d{4}-\\d{4,}$",
                "severity": "ERROR",
                "description": "Referenced CVE ID in EPSS prediction",
            },
            "http://w3id.org/sepses/vocab/ref/epss#epssScore": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Exploit Prediction Scoring System probability [0-1]",
            },
            "http://w3id.org/sepses/vocab/ref/epss#epssPercentile": {
                "type": "literal",
                "severity": "WARNING",
                "description": "EPSS percentile rank across all CVEs",
            },
        }
    },
    "http://d3fend.mitre.org/ontologies/d3fend.owl#DefensiveTechnique": {
        "mandatory_properties": {
            "http://www.w3.org/2000/01/rdf-schema#label": {
                "type": "literal",
                "severity": "ERROR",
                "description": "Official name of the D3FEND defensive technique",
            },
        }
    },
}

VIRTUOSO_HOST = os.environ.get("VIRTUOSO_HOST", "localhost")
VIRTUOSO_SPARQL = f"http://{VIRTUOSO_HOST}:8890/sparql"
VIRTUOSO_CONTAINER = os.environ.get("VIRTUOSO_CONTAINER", "cskg-sparql")
GRAPH_BASE = "http://w3id.org/sepses/graph/"


class _FetcherRegistry(dict):
    def __init__(self):
        super().__init__()
        self._initialized = False

    def _init(self):
        if not self._initialized:
            self._initialized = True
            from modules.fetcher.fetchers.attck import ATTCKFetcher
            from modules.fetcher.fetchers.d3fend import D3FENDFetcher
            from modules.fetcher.fetchers.epss import EPSSFetcher
            from modules.fetcher.fetchers.icsa import ICSAFetcher
            from modules.fetcher.fetchers.mitre import CAPECFetcher, CWEFetcher
            from modules.fetcher.fetchers.nvd import CPEFetcher, CVEFetcher

            self.update(
                {
                    "cwe": CWEFetcher,
                    "capec": CAPECFetcher,
                    "attck_enterprise": lambda: ATTCKFetcher("enterprise"),
                    "attck_ics": lambda: ATTCKFetcher("ics"),
                    "attck_mobile": lambda: ATTCKFetcher("mobile"),
                    "icsa": ICSAFetcher,
                    "epss": EPSSFetcher,
                    "d3fend": D3FENDFetcher,
                    "cve": CVEFetcher,
                    "cpe": CPEFetcher,
                }
            )

    def get(self, key, default=None):
        self._init()
        return super().get(key, default)

    def keys(self):
        self._init()
        return super().keys()

    def values(self):
        self._init()
        return super().values()

    def items(self):
        self._init()
        return super().items()

    def __iter__(self):
        self._init()
        return super().__iter__()

    def __getitem__(self, key):
        self._init()
        return super().__getitem__(key)

    def __len__(self):
        self._init()
        return super().__len__()


FETCHER_REGISTRY = _FetcherRegistry()
