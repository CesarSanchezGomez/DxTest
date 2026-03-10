from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from .xml_elements import XMLNode, XMLDocument


class XMLNormalizer:
    """Normalizador que conserva metadata y detecta tipos de datos."""

    BOOLEAN_PATTERNS = {
        "true": True, "false": False, "yes": True, "no": False, "1": True, "0": False,
    }

    NUMBER_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")
    ISO_DATE_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$"
    )

    def __init__(self, preserve_all_data: bool = True):
        self.preserve_all_data = preserve_all_data

    def normalize_document(self, document: XMLDocument) -> Dict[str, Any]:
        return {
            "metadata": self._normalize_document_metadata(document),
            "structure": self._normalize_node(document.root),
            "statistics": self._calculate_statistics(document),
        }

    def _normalize_document_metadata(self, document: XMLDocument) -> Dict[str, Any]:
        return {
            "source": document.source_name,
            "namespaces": document.namespaces,
            "version": document.version,
            "encoding": document.encoding,
            "parsed_at": datetime.utcnow().isoformat() + "Z",
        }

    def _normalize_node(self, node: XMLNode) -> Dict[str, Any]:
        return {
            "tag": node.tag,
            "node_type": node.node_type.value,
            "technical_id": node.technical_id,
            "depth": node.depth,
            "sibling_order": node.sibling_order,
            "namespace": node.namespace,
            "text_content": node.text_content,
            "attributes": {
                "raw": node.attributes,
                "normalized": self._normalize_attributes(node.attributes),
            },
            "labels": node.labels,
            "children": [self._normalize_node(child) for child in node.children],
            "has_children": len(node.children) > 0,
            "has_labels": len(node.labels) > 0,
            "has_attributes": len(node.attributes) > 0,
        }

    def _normalize_attributes(self, attributes: Dict[str, str]) -> Dict[str, Any]:
        return {key: self._normalize_value(value) for key, value in attributes.items()}

    def _normalize_value(self, value: str) -> Any:
        if not value or not isinstance(value, str):
            return value

        value_lower = value.lower()
        if value_lower in self.BOOLEAN_PATTERNS:
            return self.BOOLEAN_PATTERNS[value_lower]

        if self.NUMBER_PATTERN.match(value):
            try:
                return float(value) if "." in value else int(value)
            except ValueError:
                pass

        return value

    def _calculate_statistics(self, document: XMLDocument) -> Dict[str, Any]:
        return {
            "total_nodes": self._count_nodes(document.root),
            "unique_tags": self._collect_unique_tags(document.root),
            "attribute_summary": self._summarize_attributes(document.root),
            "label_summary": self._summarize_labels(document.root),
        }

    def _count_nodes(self, node: XMLNode) -> int:
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _collect_unique_tags(self, node: XMLNode) -> List[str]:
        tags = {node.tag}
        for child in node.children:
            tags.update(self._collect_unique_tags(child))
        return sorted(tags)

    def _summarize_attributes(self, node: XMLNode) -> Dict[str, Any]:
        all_attributes: Dict[str, int] = {}

        def collect_attrs(current_node: XMLNode):
            for attr_name in current_node.attributes:
                all_attributes[attr_name] = all_attributes.get(attr_name, 0) + 1
            for child in current_node.children:
                collect_attrs(child)

        collect_attrs(node)
        return {
            "total_unique_attributes": len(all_attributes),
            "most_common": dict(sorted(all_attributes.items(), key=lambda x: x[1], reverse=True)[:10]),
        }

    def _summarize_labels(self, node: XMLNode) -> Dict[str, Any]:
        language_counts: Dict[str, int] = {}

        def collect_labels(current_node: XMLNode):
            for lang in current_node.labels:
                language_counts[lang] = language_counts.get(lang, 0) + 1
            for child in current_node.children:
                collect_labels(child)

        collect_labels(node)
        return {
            "total_languages": len(language_counts),
            "languages": dict(sorted(language_counts.items())),
        }
