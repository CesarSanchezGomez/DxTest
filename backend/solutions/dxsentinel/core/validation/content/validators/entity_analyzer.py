from typing import Dict, List, Set
from collections import defaultdict


class EntityAnalyzer:

    def __init__(self, field_catalog: Dict):
        self.field_catalog = field_catalog
        self._entity_fields_cache = None

    def get_entity_fields(self) -> Dict[str, List[str]]:
        if self._entity_fields_cache is not None:
            return self._entity_fields_cache

        entity_fields = defaultdict(list)
        for column, meta in self.field_catalog.items():
            entity_id = meta.get("element", "")
            if entity_id:
                entity_fields[entity_id].append(column)

        self._entity_fields_cache = dict(entity_fields)
        return self._entity_fields_cache

    def is_entity_empty_for_row(self, row: Dict, entity_id: str) -> bool:
        entity_fields = self.get_entity_fields()
        columns = entity_fields.get(entity_id, [])

        if not columns:
            return True

        for col in columns:
            value = row.get(col)
            if not self._is_value_empty(value):
                return False

        return True

    def is_entity_empty_globally(self, csv_data: List[Dict], entity_id: str) -> bool:
        entity_fields = self.get_entity_fields()
        columns = entity_fields.get(entity_id, [])

        if not columns:
            return True

        for row in csv_data:
            for col in columns:
                value = row.get(col)
                if not self._is_value_empty(value):
                    return False

        return True

    def get_required_fields_for_entity(self, entity_id: str) -> List[str]:
        entity_fields = self.get_entity_fields()
        columns = entity_fields.get(entity_id, [])

        required = []
        for col in columns:
            meta = self.field_catalog.get(col, {})
            if meta.get("required", False):
                required.append(col)

        return required

    def _is_value_empty(self, value) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False
