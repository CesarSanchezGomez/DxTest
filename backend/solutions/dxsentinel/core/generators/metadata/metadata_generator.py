from typing import Dict, List, Optional
from datetime import datetime

from ...constants import SAP_ENTITY_CONFIGS, get_metadata_type
from .business_key_resolver import BusinessKeyResolver
from .field_identifier_extractor import FieldIdentifierExtractor
from .field_categorizer import FieldCategorizer


class MetadataGenerator:

    def __init__(self):
        self.key_resolver = BusinessKeyResolver()
        self.field_extractor = FieldIdentifierExtractor()
        self.field_categorizer = FieldCategorizer(SAP_ENTITY_CONFIGS)

    def generate_metadata(self, processed_data: Dict, columns: List[Dict]) -> Dict:
        elements = processed_data.get("elements", [])
        available_headers = [col["full_id"] for col in columns]

        metadata = {
            "version": "2.1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "elements": {},
            "field_catalog": {},
            "business_keys": {},
            "layout_split_config": {},
            "format_groups": self._clean_format_groups(processed_data.get("format_groups", {})),
        }

        for element in elements:
            element_id = element["element_id"]
            element_metadata = self._analyze_element(element)
            metadata["elements"][element_id] = element_metadata

        metadata["field_catalog"] = self._build_field_catalog(columns, metadata["elements"])
        metadata["business_keys"] = self._build_business_keys_mapping(
            metadata["elements"], available_headers,
        )
        metadata["layout_split_config"] = self._build_layout_split_config(
            metadata["elements"], metadata["field_catalog"],
            metadata["business_keys"], columns,
        )

        return metadata

    @staticmethod
    def _clean_format_groups(format_groups: Dict) -> Dict:
        cleaned = {}
        for country_code, groups in format_groups.items():
            cleaned[country_code] = {}
            for group_id, group_data in groups.items():
                formats = group_data.get("formats", [])
                cleaned[country_code][group_id] = {
                    "formats": [
                        {
                            "id": fmt.get("id"),
                            "reg_ex": fmt.get("reg_ex"),
                            "display_format": fmt.get("display_format"),
                        }
                        for fmt in formats
                    ]
                }
        return cleaned

    def _analyze_element(self, element: Dict) -> Dict:
        element_id = element["element_id"]
        fields = element["fields"]
        sap_config = SAP_ENTITY_CONFIGS.get(element_id, {})

        return {
            "element_id": element_id,
            "is_master": sap_config.get("is_master", False),
            "business_keys": sap_config.get("business_keys", []),
            "sap_format_keys": sap_config.get("template", []),
            "references": sap_config.get("references"),
            "field_count": len(fields),
            "description": sap_config.get("description", f"Standard {element_id} entity"),
        }

    def _build_field_catalog(self, columns: List[Dict], elements_meta: Dict) -> Dict:
        catalog = {}

        for column in columns:
            full_field_id = column["full_id"]
            element_id = column["element_id"]
            field_id = column["field_id"]
            node = column.get("node", {})

            raw_attrs = {}
            if isinstance(node, dict):
                attrs = node.get("attributes", {})
                if isinstance(attrs, dict):
                    raw_attrs = attrs.get("raw", attrs)

            is_business_key = self.field_categorizer.is_business_key(element_id, field_id)
            is_hris = self.field_categorizer.is_hris_field(element_id, field_id)

            max_length = None
            max_length_str = raw_attrs.get("max-length") or raw_attrs.get("maxLength")
            if max_length_str:
                try:
                    max_length = int(max_length_str)
                except (ValueError, TypeError):
                    pass

            required_str = raw_attrs.get("required", "").lower()
            is_required = required_str == "true" or is_business_key
            visibility = raw_attrs.get("visibility", "both")

            catalog[full_field_id] = {
                "element": element_id,
                "field": field_id,
                "is_business_key": is_business_key,
                "is_hris_field": is_hris,
                "data_type": self._resolve_data_type(element_id, field_id),
                "category": self._categorize_field(field_id),
                "max_length": max_length,
                "required": is_required,
                "visibility": visibility,
                "picklist_id": self._extract_picklist_id(node),
            }

        return catalog

    def _extract_picklist_id(self, node: Dict) -> Optional[str]:
        if not isinstance(node, dict):
            return None
        for child in node.get("children", []):
            if not isinstance(child, dict):
                continue
            if child.get("tag") == "picklist":
                child_attrs = child.get("attributes", {})
                if isinstance(child_attrs, dict):
                    raw = child_attrs.get("raw", child_attrs)
                    return raw.get("id") or child_attrs.get("id")
        return None

    def _build_business_keys_mapping(self, elements_meta: Dict, available_columns: List[str]) -> Dict:
        mappings = {}

        for elem_id, meta in elements_meta.items():
            business_keys = meta.get("business_keys", [])
            sap_format_keys = meta.get("sap_format_keys", [])
            references = meta.get("references")

            if not business_keys:
                continue

            key_mappings = []
            for golden_key, sap_key in zip(business_keys, sap_format_keys):
                golden_column = self.key_resolver.resolve_golden_column(
                    sap_key, None, available_columns, elem_id,
                )
                if golden_column:
                    key_mappings.append({
                        "golden_column": golden_column,
                        "sap_column": sap_key,
                        "field_name": golden_key,
                        "is_foreign": "." in sap_key,
                    })

            mappings[elem_id] = {
                "business_keys": key_mappings,
                "references": references,
                "is_master": meta.get("is_master", False),
            }

        return mappings

    def _build_layout_split_config(
        self, elements_meta: Dict, field_catalog: Dict,
        business_keys: Dict, all_columns: List[Dict],
    ) -> Dict:
        config = {}
        grouped_by_entity: Dict[str, list] = {}

        for column in all_columns:
            full_field_id = column["full_id"]
            entity_id, field_id, country_code = self.field_extractor.extract_entity_and_field(full_field_id)

            suffix = self.field_extractor.should_split_by_suffix(entity_id, field_id)
            group_key = f"{entity_id}_{suffix}" if suffix else entity_id

            if group_key not in grouped_by_entity:
                grouped_by_entity[group_key] = []
            grouped_by_entity[group_key].append(full_field_id)

        for group_key, fields in grouped_by_entity.items():
            entity_id = group_key
            filename = f"{entity_id}_template.csv"
            business_key_config = business_keys.get(entity_id, {})

            config[group_key] = {
                "element_id": entity_id,
                "group_key": group_key,
                "fields": fields,
                "field_count": len(fields),
                "business_keys": business_key_config.get("business_keys", []),
                "layout_filename": filename,
            }

        return config

    def _resolve_data_type(self, element_id: str, field_id: str) -> str:
        sap_type = get_metadata_type(element_id, field_id)
        if sap_type:
            return sap_type
        return "string"

    def _categorize_field(self, field_id: str) -> str:
        field_lower = field_id.lower()

        if any(k in field_lower for k in ["id", "code", "number"]):
            return "identifier"
        elif "date" in field_lower:
            return "temporal"
        elif "custom" in field_lower or "udf" in field_lower:
            return "custom"
        elif any(k in field_lower for k in ["name", "title", "description"]):
            return "descriptive"
        else:
            return "operational"
