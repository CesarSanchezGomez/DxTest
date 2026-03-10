from typing import Dict, List, Optional, Set
import logging

from ...constants import ELEMENT_ORDER
from .field_filter import FieldFilter
from .field_finder import GoldenRecordFieldFinder
from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class ElementProcessor:
    """Procesa elementos según jerarquía del Golden Record."""

    def __init__(self, target_countries: Optional[List[str]] = None):
        if target_countries and isinstance(target_countries, str):
            target_countries = [target_countries]

        self.field_filter = FieldFilter()
        self.global_field_ids: Set[str] = set()
        self.target_countries = [c.upper() for c in target_countries] if target_countries else None

    def _normalize_country_code(self, country_code: str) -> str:
        return country_code.strip().upper()

    def _should_include_country(self, country_code: str) -> bool:
        if not self.target_countries:
            return True
        return self._normalize_country_code(country_code) in self.target_countries

    def process_model(self, parsed_model: Dict) -> Dict:
        try:
            structure = parsed_model.get("structure", {})
            self.global_field_ids.clear()

            sdm_elements = GoldenRecordFieldFinder.find_all_elements(structure, origin_filter="sdm")
            all_elements = GoldenRecordFieldFinder.find_all_elements(structure)
            non_csf_elements = [
                elem for elem in all_elements
                if GoldenRecordFieldFinder.get_element_origin(elem) != "csf"
            ]

            global_elements_dict = {}
            for elem in sdm_elements + non_csf_elements:
                elem_id = elem.get("technical_id") or elem.get("id", "")
                if elem_id and elem_id not in global_elements_dict:
                    origin = GoldenRecordFieldFinder.get_element_origin(elem) or "sdm"
                    global_elements_dict[elem_id] = {"node": elem, "origin": origin}

            country_nodes = self._find_country_nodes(structure)

            filtered_country_nodes = [
                cn for cn in country_nodes
                if (cc := self._get_country_code(cn)) and self._should_include_country(cc)
            ]

            country_specific_elements = {}
            for country_node in filtered_country_nodes:
                country_code = self._get_country_code(country_node)
                if not country_code:
                    continue

                csf_elements_in_country = GoldenRecordFieldFinder.find_all_elements(
                    country_node, origin_filter="csf",
                )

                for elem in csf_elements_in_country:
                    elem_id = elem.get("technical_id") or elem.get("id", "")
                    if elem_id:
                        clean_elem_id = elem_id.replace("_csf", "")
                        country_element_id = f"{country_code}_{clean_elem_id}"
                        country_specific_elements[country_element_id] = {
                            "node": elem, "origin": "csf", "country_code": country_code,
                        }

            all_elements_list = []

            for elem_id, elem_data in global_elements_dict.items():
                processed = self._process_element(
                    elem_data["node"], elem_id, origin=elem_data["origin"],
                    is_country_specific=False, country_code=None,
                )
                if processed["field_count"] > 0:
                    all_elements_list.append(processed)

            for country_elem_id, elem_data in country_specific_elements.items():
                processed = self._process_element(
                    elem_data["node"], country_elem_id, origin=elem_data["origin"],
                    is_country_specific=True, country_code=elem_data["country_code"],
                )
                if processed["field_count"] > 0:
                    all_elements_list.append(processed)

            format_groups_by_country = {}
            for country_node in filtered_country_nodes:
                country_code = self._get_country_code(country_node)
                if not country_code:
                    continue
                fgs = self._find_format_groups(country_node)
                if fgs:
                    format_groups_by_country[country_code] = fgs

            return {
                "elements": all_elements_list,
                "global_processing": self.target_countries is None,
                "processed_countries": [self._get_country_code(node) for node in filtered_country_nodes],
                "format_groups": format_groups_by_country,
            }

        except Exception as e:
            raise ElementNotFoundError(f"Error processing model: {str(e)}") from e

    def _find_country_nodes(self, node: Dict) -> List[Dict]:
        countries = []
        if "country" in node.get("tag", "").lower():
            countries.append(node)
        for child in node.get("children", []):
            countries.extend(self._find_country_nodes(child))
        return countries

    def _get_country_code(self, country_node: Dict) -> Optional[str]:
        country_code = country_node.get("technical_id")
        if country_code:
            return country_code

        attributes = country_node.get("attributes", {}).get("raw", {})
        for attr_key in ["id", "countryCode", "country-code", "code"]:
            country_code = attributes.get(attr_key)
            if country_code:
                return country_code

        labels = country_node.get("labels", {})
        if labels and isinstance(labels, dict):
            for code, label in labels.items():
                if code and code != "default" and len(code) <= 3:
                    return code

        return None

    def _process_element(
        self, element_node: Dict, element_id: str, origin: str = "",
        is_country_specific: bool = False, country_code: str = None,
    ) -> Dict:

        all_fields = GoldenRecordFieldFinder.find_all_fields(element_node, include_nested=True)

        clean_element_id = element_id
        if is_country_specific and country_code and element_id.startswith(f"{country_code}_"):
            clean_element_id = element_id[len(country_code) + 1:]

        element_fields = []

        for field_node in all_fields:
            field_id = field_node.get("technical_id") or field_node.get("id", "")
            if not field_id:
                continue

            full_field_id = f"{clean_element_id}_{field_id}"
            field_key = f"{full_field_id}_{country_code}" if country_code else full_field_id

            if field_key in self.global_field_ids:
                continue

            include, exclusion_reason = self.field_filter.filter_field(field_node)

            if include:
                self.global_field_ids.add(field_key)
                element_fields.append({
                    "field_id": field_id,
                    "full_field_id": full_field_id,
                    "node": field_node,
                    "origin": origin,
                    "is_country_specific": is_country_specific,
                    "country_code": country_code,
                    "is_business_key": False,
                })

        sorted_fields = sorted(element_fields, key=lambda f: f["field_id"])

        return {
            "element_id": clean_element_id,
            "origin": origin,
            "fields": sorted_fields,
            "is_country_specific": is_country_specific,
            "country_code": country_code,
            "field_count": len(sorted_fields),
        }

    def _find_format_groups(self, country_node: Dict) -> Dict[str, Dict]:
        format_groups = {}
        for child in country_node.get("children", []):
            if child.get("tag") == "format-group":
                fg_id = child.get("attributes", {}).get("raw", {}).get("id")
                if fg_id:
                    format_groups[fg_id] = self._extract_format_group_data(child)
        return format_groups

    def _extract_format_group_data(self, fg_node: Dict) -> Dict:
        formats = []
        for child in fg_node.get("children", []):
            if child.get("tag") == "format":
                formats.append(self._extract_format_data(child))
        return {"formats": formats}

    def _extract_format_data(self, format_node: Dict) -> Dict:
        raw_attrs = format_node.get("attributes", {}).get("raw", {})
        format_id = raw_attrs.get("id")
        instructions = dict(format_node.get("labels", {}))

        display_format = None
        reg_ex = None

        for child in format_node.get("children", []):
            tag = child.get("tag")
            text = child.get("text_content")
            if tag == "display-format":
                display_format = text
            elif tag == "reg-ex":
                reg_ex = text
            elif tag == "instruction" and text and "default" not in instructions:
                instructions["default"] = text

        return {
            "id": format_id,
            "instructions": instructions,
            "display_format": display_format,
            "reg_ex": reg_ex,
        }
