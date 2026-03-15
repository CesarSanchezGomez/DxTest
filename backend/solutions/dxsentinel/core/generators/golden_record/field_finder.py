from typing import Dict, List, Optional


class GoldenRecordFieldFinder:
    """Encuentra nodos hris-field y hris-element recursivamente."""

    @staticmethod
    def find_all_fields(node: Dict, include_nested: bool = True) -> List[Dict]:
        fields = []

        if node.get("tag") == "hris-field":
            fields.append(node)

        if include_nested:
            for child in node.get("children", []):
                fields.extend(GoldenRecordFieldFinder.find_all_fields(child, include_nested))
        else:
            for child in node.get("children", []):
                if child.get("tag") == "hris-field":
                    fields.append(child)

        return fields

    @staticmethod
    def find_all_elements(node: Dict, origin_filter: Optional[str] = None) -> List[Dict]:
        elements = []

        if node.get("tag") == "hris-element":
            if origin_filter:
                attributes = node.get("attributes", {}).get("raw", {})
                element_origin = attributes.get("data-origin", "")
                if element_origin == origin_filter:
                    elements.append(node)
            else:
                elements.append(node)

        for child in node.get("children", []):
            elements.extend(GoldenRecordFieldFinder.find_all_elements(child, origin_filter))

        return elements

    @staticmethod
    def get_element_origin(element_node: Dict) -> str:
        attributes = element_node.get("attributes", {}).get("raw", {})
        return attributes.get("data-origin", "")
