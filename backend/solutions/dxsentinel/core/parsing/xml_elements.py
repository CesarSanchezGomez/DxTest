from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class NodeType(str, Enum):
    """Tipos de nodos detectados por estructura."""
    ELEMENT = "element"
    FIELD = "field"
    COMPOSITE = "composite"
    ASSOCIATION = "association"
    UNKNOWN = "unknown"

    @classmethod
    def from_structure(cls, tag: str, attributes: Dict[str, str], children: List[XMLNode]) -> NodeType:
        if "isComposite" in attributes and attributes["isComposite"].lower() == "true":
            return cls.COMPOSITE

        if "association" in tag.lower() or "isAssociation" in attributes:
            return cls.ASSOCIATION

        field_indicators = {"type", "label", "name", "id"}
        if any(indicator in str(attributes).lower() for indicator in field_indicators):
            return cls.FIELD

        return cls.ELEMENT


@dataclass
class XMLNode:
    """Representación completa de un nodo XML."""
    tag: str
    technical_id: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    children: List[XMLNode] = field(default_factory=list)
    parent: Optional[XMLNode] = None
    depth: int = 0
    sibling_order: int = 0
    namespace: Optional[str] = None
    text_content: Optional[str] = None
    node_type: NodeType = NodeType.UNKNOWN

    def __post_init__(self):
        self.node_type = NodeType.from_structure(self.tag, self.attributes, self.children)

        if not self.technical_id:
            possible_ids = {"id", "technicalId", "name", "code"}
            for possible_id in possible_ids:
                if possible_id in self.attributes:
                    self.technical_id = self.attributes[possible_id]
                    break

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "technical_id": self.technical_id,
            "attributes": self.attributes,
            "labels": self.labels,
            "node_type": self.node_type.value,
            "namespace": self.namespace,
            "text_content": self.text_content,
            "depth": self.depth,
            "sibling_order": self.sibling_order,
            "children": [child.to_dict() for child in self.children],
        }

    def find_nodes_by_tag(self, tag_pattern: str) -> List[XMLNode]:
        results: List[XMLNode] = []
        if tag_pattern in self.tag:
            results.append(self)
        for child in self.children:
            results.extend(child.find_nodes_by_tag(tag_pattern))
        return results

    def get_attribute(self, attr_name: str, default: Optional[str] = None) -> Optional[str]:
        return self.attributes.get(attr_name, default)


@dataclass
class XMLDocument:
    """Documento XML completo con metadata."""
    root: XMLNode
    source_name: Optional[str] = None
    namespaces: Dict[str, str] = field(default_factory=dict)
    version: Optional[str] = None
    encoding: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "namespaces": self.namespaces,
            "version": self.version,
            "encoding": self.encoding,
            "root": self.root.to_dict(),
        }
