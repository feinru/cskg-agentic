import re


def _sanitize_uri_component(value: str) -> str:
    if not value:
        return ""
    value = re.sub("<[^>]+>", "", str(value))
    value = re.sub("[\\x00-\\x1f]", "", value)
    value = re.sub("[\\s\"\\'{}<>|\\\\^`\\[\\]]", "_", value)
    return value


class OntologyMapper:
    def map_entity(self, source_name: str, raw_entity: dict) -> dict:
        mapped = {}
        if source_name == "cve":
            mapped["@type"] = "sepses:CVE"
            cve_data = raw_entity.get("cve", {})
            mapped["sepses:id"] = cve_data.get("id")
            descriptions = cve_data.get("descriptions", [])
            for desc in descriptions:
                if desc.get("lang") == "en":
                    mapped["sepses:description"] = desc.get("value")
                    break
            weaknesses = cve_data.get("weaknesses", [])
            cwe_refs = []
            for w in weaknesses:
                for desc in w.get("description", []):
                    if desc.get("value") and desc.get("value").startswith("CWE-"):
                        cwe_refs.append(f"sepses:{desc.get('value')}")
            if cwe_refs:
                mapped["sepses:hasCWE"] = cwe_refs
        elif source_name == "cwe":
            mapped["@type"] = "sepses:CWE"
            attribs = raw_entity.get("attribs", {})
            mapped["sepses:id"] = f"CWE-{attribs.get('ID')}"
            mapped["sepses:name"] = attribs.get("Name")
            if "Description" in raw_entity:
                mapped["sepses:description"] = raw_entity["Description"]
        elif source_name == "cpe":
            mapped["@type"] = "sepses:CPE"
            cpe_data = raw_entity.get("cpe", {})
            cpe_name = cpe_data.get("cpeName", "")
            mapped["sepses:id"] = cpe_data.get("cpeNameId")
            mapped["sepses:cpe23Uri"] = cpe_name
            if cpe_name:
                cpe_safe = cpe_name.replace(":", "").replace("/", "")
                mapped["__uri_key__"] = _sanitize_uri_component(cpe_safe)
        elif source_name == "capec":
            mapped["@type"] = "sepses:CAPEC"
            attribs = raw_entity.get("attribs", {})
            mapped["sepses:id"] = f"CAPEC-{attribs.get('ID')}"
            mapped["sepses:name"] = attribs.get("Name")
            if "Description" in raw_entity:
                mapped["sepses:description"] = raw_entity["Description"]
        elif source_name == "icsa":
            mapped["@type"] = "sepses:ICSA"
            cve_id = _sanitize_uri_component(raw_entity.get("cveID", ""))
            vendor = _sanitize_uri_component(raw_entity.get("vendorProject", "unknown"))
            product = _sanitize_uri_component(raw_entity.get("product", "unknown"))
            mapped["sepses:cveID"] = raw_entity.get("cveID")
            mapped["sepses:vendorProject"] = raw_entity.get("vendorProject")
            mapped["sepses:product"] = raw_entity.get("product")
            mapped["sepses:vulnerabilityName"] = raw_entity.get("vulnerabilityName")
            icsa_id = f"{vendor}_{product}_{cve_id}".replace(" ", "_")
            mapped["sepses:id"] = icsa_id
            mapped["__uri_key__"] = icsa_id
        elif source_name.startswith("attck"):
            mapped["@type"] = "sepses:AttackPattern"
            if raw_entity.get("type") == "attack-pattern":
                if raw_entity.get("revoked") or raw_entity.get("x_mitre_deprecated"):
                    return {}
                mapped["sepses:id"] = raw_entity.get("id")
                mapped["sepses:name"] = raw_entity.get("name")
                mapped["sepses:description"] = raw_entity.get("description")
                for ext_ref in raw_entity.get("external_references", []):
                    if ext_ref.get("source_name") == "mitre-attack":
                        mapped["sepses:techniqueId"] = ext_ref.get("external_id")
                        mapped["__uri_key__"] = ext_ref.get("external_id")
                        break
            else:
                return {}
        else:
            mapped["@type"] = "sepses:Unknown"
            mapped["raw_data"] = raw_entity
        return {k: v for k, v in mapped.items() if v is not None}
