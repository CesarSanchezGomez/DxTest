from typing import Dict

from ...constants import SAP_ENTITY_CONFIGS


class FieldCategorizer:
    """Categoriza campos como business keys o HRIS fields."""

    KNOWN_HRIS_IDENTIFIERS = {
        "person-id-external", "user-id", "personidexternal", "userid",
    }

    def __init__(self, entity_configs: Dict[str, Dict] = None):
        self.entity_configs = entity_configs or SAP_ENTITY_CONFIGS
        self._build_key_index()

    def _build_key_index(self):
        self.key_index = {}
        for entity_id, config in self.entity_configs.items():
            keys = config.get("business_keys", [])
            sap_keys = config.get("template", [])
            self.key_index[entity_id] = {
                "keys": set(keys),
                "sap_keys": set(sap_keys),
            }

    def is_business_key(self, entity_id: str, field_id: str) -> bool:
        if entity_id not in self.key_index:
            return False

        entity_keys = self.key_index[entity_id]
        field_normalized = self._normalize_field_name(field_id)

        if field_normalized in entity_keys["keys"]:
            return True
        if field_id in entity_keys["sap_keys"]:
            return True

        return False

    def is_hris_field(self, entity_id: str, field_id: str) -> bool:
        field_normalized = self._normalize_field_name(field_id)
        if field_normalized in self.KNOWN_HRIS_IDENTIFIERS:
            if not self.is_business_key(entity_id, field_id):
                return True
        return False

    def _normalize_field_name(self, field_name: str) -> str:
        return field_name.lower().replace("-", "").replace("_", "")
