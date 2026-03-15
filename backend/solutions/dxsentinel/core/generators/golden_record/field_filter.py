from typing import Dict, Tuple, Optional, Set
import re

from ...constants import EXCLUDED_FIELD_IDS, EXCLUDED_CUSTOM_RANGES
from .exceptions import FieldFilterError


class FieldFilter:
    """Filtra y clasifica campos según criterios del Golden Record."""

    IDENTIFIER_PATTERNS = [r"id$", r"number$", r"name$", r"code$"]
    DATE_PATTERNS = [r"date$", r"Date$", r"start", r"end", r"effective"]
    CUSTOM_PATTERNS = [r"custom", r"Custom", r"udf", r"UDF"]

    def __init__(self):
        self.identifier_patterns = [re.compile(p, re.IGNORECASE) for p in self.IDENTIFIER_PATTERNS]
        self.date_patterns = [re.compile(p, re.IGNORECASE) for p in self.DATE_PATTERNS]
        self.custom_patterns = [re.compile(p, re.IGNORECASE) for p in self.CUSTOM_PATTERNS]

        self.excluded_patterns = []
        for field_id in EXCLUDED_FIELD_IDS:
            pattern_str = r"^" + re.escape(field_id) + r"$"
            self.excluded_patterns.append(re.compile(pattern_str, re.IGNORECASE))
            if field_id.endswith("Id"):
                pattern_str = r"^" + re.escape(field_id[:-2]) + r"ID$"
                self.excluded_patterns.append(re.compile(pattern_str, re.IGNORECASE))

        self._generated_excluded_custom_fields = self._generate_custom_exclusions()

    def filter_field(self, field_node: Dict) -> Tuple[bool, Optional[str]]:
        """Determina si un campo debe incluirse en el Golden Record."""
        try:
            attributes = field_node.get("attributes", {}).get("raw", {})
            field_id = field_node.get("technical_id") or field_node.get("id", "")

            visibility = attributes.get("visibility", "").lower()
            if visibility == "none":
                return False, "visibility='none'"

            viewable = attributes.get("viewable", "").lower()
            if viewable == "false":
                return False, "viewable='false'"

            if visibility not in ["view", "both", "edit", ""]:
                return False, f"visibility='{visibility}' (not view/both/edit)"

            if self._is_internal_field(field_id, attributes):
                return False, "campo técnico interno"

            if self._is_explicitly_excluded(field_id):
                return False, f"explicitly_excluded: {field_id}"

            if self._is_filtered_attribute(attributes):
                return False, "filtered_by_attributes"

            if self._is_filtered_custom_field(field_id):
                return False, "filtered_custom_range"

            return True, None

        except Exception as e:
            raise FieldFilterError(f"Error filtering field: {str(e)}")

    def _is_explicitly_excluded(self, field_id: str) -> bool:
        return any(pattern.match(field_id) for pattern in self.excluded_patterns)

    def _is_internal_field(self, field_id: str, attributes: Dict) -> bool:
        internal_indicators = ["attachment", "calculated", "sys"]
        field_id_lower = field_id.lower()
        for indicator in internal_indicators:
            if indicator in field_id_lower:
                return True

        field_type = attributes.get("type", "").lower()
        if field_type in ["attachment", "calculated"]:
            return True

        return False

    def _is_filtered_attribute(self, attributes: Dict[str, str]) -> bool:
        if attributes.get("filterable", "").lower() == "false":
            return True
        if attributes.get("deprecated", "").lower() == "true":
            return True
        return False

    def _is_filtered_custom_field(self, field_id: str) -> bool:
        return field_id in self._generated_excluded_custom_fields

    def _generate_custom_exclusions(self) -> Set[str]:
        excluded = set()
        for base_name, start, end in EXCLUDED_CUSTOM_RANGES:
            for num in range(start, end + 1):
                excluded.add(f"{base_name}{num}")
        return excluded

    def classify_field(self, field_node: Dict) -> str:
        field_id = field_node.get("technical_id") or field_node.get("id", "")

        if any(p.search(field_id) for p in self.identifier_patterns):
            return "identifier"
        if any(p.search(field_id) for p in self.date_patterns):
            return "temporal"
        if any(p.search(field_id) for p in self.custom_patterns):
            return "custom"
        return "operational"
