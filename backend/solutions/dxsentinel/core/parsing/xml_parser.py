from typing import Dict, List, Optional, Any, Tuple
import xml.etree.ElementTree as ET

from .xml_elements import XMLNode, XMLDocument, NodeType
from .xml_normalizer import XMLNormalizer
from .xml_loader import XMLLoader
from ..constants import (
    LABEL_PATTERNS,
    LANGUAGE_PATTERN,
    HRIS_ELEMENT_PATTERN,
    get_injectable_fields,
    get_injected_field_labels,
)


class XMLParser:
    """Parser agnóstico que se adapta a la estructura del XML."""

    def __init__(self):
        self._current_depth = 0
        self._node_count = 0

    def parse_document(self, root: ET.Element, source_name: Optional[str] = None) -> XMLDocument:
        self._current_depth = 0
        self._node_count = 0

        namespaces = self._extract_all_namespaces(root)
        version, encoding = self._extract_xml_declaration_metadata(root)

        root_node = self._parse_element(
            element=root, parent=None, sibling_order=0, depth=0, namespaces=namespaces,
        )

        return XMLDocument(
            root=root_node, source_name=source_name,
            namespaces=namespaces, version=version, encoding=encoding,
        )

    def _parse_element(
        self, element: ET.Element, parent: Optional[XMLNode],
        sibling_order: int, depth: int, namespaces: Dict[str, str],
    ) -> XMLNode:
        self._node_count += 1

        tag = self._extract_tag_name(element)
        attributes = self._extract_attributes(element)
        labels = self._extract_labels(element, attributes, namespaces)
        namespace = self._extract_namespace(element, namespaces)

        node = XMLNode(
            tag=tag, technical_id=None, attributes=attributes, labels=labels,
            children=[], parent=parent, depth=depth, sibling_order=sibling_order,
            namespace=namespace, text_content=self._extract_text_content(element),
            node_type=NodeType.UNKNOWN,
        )

        fields_to_inject = self._get_fields_to_inject(node)
        injected_count = 0

        for field_id in fields_to_inject:
            injected_field = self._create_date_field_node(field_id)
            injected_field.parent = node
            injected_field.depth = depth + 1
            injected_field.sibling_order = injected_count
            node.children.append(injected_field)
            injected_count += 1

        child_index = injected_count
        for child_elem in element:
            child_tag = self._extract_tag_name(child_elem)
            if not self._is_label_element(child_tag, child_elem):
                child_node = self._parse_element(
                    element=child_elem, parent=node,
                    sibling_order=child_index, depth=depth + 1,
                    namespaces=namespaces,
                )
                node.children.append(child_node)
                child_index += 1

        return node

    def _extract_tag_name(self, element: ET.Element) -> str:
        tag = element.tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]
        return tag

    def _extract_attributes(self, element: ET.Element) -> Dict[str, str]:
        attributes = {}
        for key, value in element.attrib.items():
            if "}" in key:
                _, attr_name = key.split("}", 1)
                attributes[attr_name] = value.strip()
            else:
                attributes[key] = value.strip()
        return attributes

    def _extract_labels(
        self, element: ET.Element, attributes: Dict[str, str],
        namespaces: Dict[str, str],
    ) -> Dict[str, str]:
        labels = {}

        for child in element:
            if self._is_label_element(self._extract_tag_name(child), child):
                lang_key = None
                for attr_name, attr_value in child.attrib.items():
                    if "lang" in attr_name.lower() or "language" in attr_name.lower():
                        lang_key = attr_value.strip().lower()
                        break

                if child.text and child.text.strip():
                    label_text = child.text.strip()
                    if lang_key and LANGUAGE_PATTERN.match(lang_key):
                        labels[lang_key] = label_text
                    else:
                        labels[f"label_{self._extract_tag_name(child)}"] = label_text

        for attr_name, attr_value in attributes.items():
            if any(pattern.match(attr_name.lower()) for pattern in LABEL_PATTERNS.values()):
                if "lang" not in attr_name.lower() and "language" not in attr_name.lower():
                    labels[f"attr_{attr_name}"] = attr_value.strip()

        return labels

    def _is_label_element(self, tag_name: str, element: ET.Element) -> bool:
        tag_lower = tag_name.lower()

        if any(pattern.match(tag_lower) for pattern in LABEL_PATTERNS.values()):
            return True

        if element.text and element.text.strip():
            text = element.text.strip()
            if 2 <= len(text) <= 100 and not text.startswith("http"):
                attrs = self._extract_attributes(element)
                if any("lang" in key.lower() or "language" in key.lower() for key in attrs):
                    return True

        return False

    def _extract_text_content(self, element: ET.Element) -> Optional[str]:
        if element.text:
            text = element.text.strip()
            if text:
                return text
        if element.tail:
            tail = element.tail.strip()
            if tail:
                return tail
        return None

    def _extract_namespace(self, element: ET.Element, namespaces: Dict[str, str]) -> Optional[str]:
        if "}" in element.tag:
            ns_url = element.tag.split("}", 1)[0][1:]
            for prefix, url in namespaces.items():
                if url == ns_url:
                    return prefix
            return ns_url
        return None

    def _extract_all_namespaces(self, root: ET.Element) -> Dict[str, str]:
        namespaces = {"xml": "http://www.w3.org/XML/1998/namespace"}

        def extract_from_element(elem: ET.Element):
            if "}" in elem.tag:
                ns_url = elem.tag.split("}", 1)[0][1:]
                if ns_url not in namespaces.values():
                    prefix = f"ns{len(namespaces)}"
                    namespaces[prefix] = ns_url

            for key, value in elem.attrib.items():
                if "}" in key:
                    ns_url = key.split("}", 1)[0][1:]
                    if ns_url not in namespaces.values():
                        prefix = f"ns{len(namespaces)}"
                        namespaces[prefix] = ns_url
                if key.startswith("xmlns:"):
                    prefix = key.split(":", 1)[1]
                    namespaces[prefix] = value
                elif key == "xmlns":
                    namespaces["default"] = value

            for child in elem:
                extract_from_element(child)

        extract_from_element(root)
        return namespaces

    def _extract_xml_declaration_metadata(self, root: ET.Element) -> Tuple[Optional[str], Optional[str]]:
        version = None
        encoding = None
        for attr_name, attr_value in root.attrib.items():
            attr_lower = attr_name.lower()
            if "version" in attr_lower:
                version = attr_value
            elif "encoding" in attr_lower:
                encoding = attr_value
        return version, encoding

    def _get_fields_to_inject(self, node: XMLNode) -> List[str]:
        if not HRIS_ELEMENT_PATTERN.match(node.tag):
            return []
        element_id = node.technical_id or node.attributes.get("id")
        if element_id:
            return get_injectable_fields(element_id)
        return []

    def _create_date_field_node(self, field_id: str) -> XMLNode:
        attributes = {"id": field_id, "visibility": "view", "required": "true"}
        labels = get_injected_field_labels(field_id)
        return XMLNode(
            tag="hris-field", technical_id=field_id, attributes=attributes,
            labels=labels, children=[], parent=None, depth=0,
            sibling_order=0, namespace=None, text_content=None,
            node_type=NodeType.FIELD,
        )


# ─── Funciones de módulo: parseo multi-archivo y fusión CSF ─────────────────


def parse_multiple_xml_files(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """Parsea múltiples archivos XML y los fusiona en un solo árbol."""
    loader = XMLLoader()
    parser = XMLParser()
    normalizer = XMLNormalizer()
    documents = []

    for file_info in files:
        file_path = file_info["path"]
        file_type = file_info.get("type", "main")
        source_name = file_info.get("source_name", file_path)

        xml_root = loader.load_from_file(file_path, source_name)
        document = parser.parse_document(xml_root, source_name)
        document.file_type = file_type

        if file_type == "main":
            _mark_nodes_origin(document.root, "sdm")

        documents.append(document)

    if len(documents) > 1:
        fused_document = _fuse_csf_with_main(documents)
    else:
        fused_document = documents[0]

    return normalizer.normalize_document(fused_document)


def _fuse_csf_with_main(documents: List[XMLDocument]) -> XMLDocument:
    """Fusiona documentos CSF con el documento principal."""
    main_doc = None
    csf_docs = []

    for doc in documents:
        if getattr(doc, "file_type", "main") == "main":
            main_doc = doc
        else:
            csf_docs.append(doc)

    if not main_doc:
        main_doc = documents[0]

    for csf_doc in csf_docs:
        main_doc = _merge_country_nodes(main_doc, csf_doc)

    return main_doc


def _merge_country_nodes(main_doc: XMLDocument, csf_doc: XMLDocument) -> XMLDocument:
    """Fusiona nodos <country> del CSF con el documento principal."""
    csf_countries = _find_country_nodes(csf_doc.root)
    if not csf_countries:
        return main_doc

    for country_node in csf_countries:
        _insert_country_into_main(main_doc.root, country_node, "csf")

    return main_doc


def _insert_country_into_main(main_root: XMLNode, country_node: XMLNode, origin: str = "csf"):
    """Inserta un nodo país del CSF en la estructura principal."""
    country_code = country_node.technical_id or country_node.attributes.get("id", "UNKNOWN")
    existing_country = _find_country_by_code(main_root, country_code)

    if existing_country:
        _merge_country_content(existing_country, country_node, country_code, origin)
    else:
        cloned_country = _clone_node(country_node, origin=origin, country_code=country_code)
        cloned_country.parent = main_root
        cloned_country.depth = main_root.depth + 1
        cloned_country.sibling_order = len(main_root.children)
        main_root.children.append(cloned_country)


def _find_country_nodes(node: XMLNode) -> List[XMLNode]:
    """Encuentra recursivamente todos los nodos <country> en el árbol."""
    countries = []
    if "country" in node.tag.lower():
        countries.append(node)
    for child in node.children:
        countries.extend(_find_country_nodes(child))
    return countries


def _clone_node(
    node: XMLNode, origin: Optional[str] = None, country_code: Optional[str] = None,
) -> XMLNode:
    """Crea una copia profunda de un nodo, opcionalmente marcando su origen."""
    cloned = XMLNode(
        tag=node.tag, technical_id=node.technical_id,
        attributes=node.attributes.copy(), labels=node.labels.copy(),
        children=[], parent=None, depth=node.depth,
        sibling_order=node.sibling_order, namespace=node.namespace,
        text_content=node.text_content, node_type=node.node_type,
    )

    if origin:
        cloned.attributes["data-origin"] = origin
    if country_code:
        cloned.attributes["data-country"] = country_code

    for child in node.children:
        cloned_child = _clone_node(child, origin=origin, country_code=country_code)
        cloned_child.parent = cloned
        cloned.children.append(cloned_child)

    return cloned


def _find_country_by_code(node: XMLNode, country_code: str) -> Optional[XMLNode]:
    """Busca un nodo país por su código."""
    if "country" in node.tag.lower():
        current_code = node.technical_id or node.attributes.get("id")
        if current_code == country_code:
            return node
    for child in node.children:
        result = _find_country_by_code(child, country_code)
        if result:
            return result
    return None


def _mark_nodes_origin(node: XMLNode, origin: str):
    """Marca recursivamente todos los nodos con su origen."""
    if "data-origin" not in node.attributes:
        node.attributes["data-origin"] = origin

    if "hris" in node.tag.lower() and node.technical_id and origin != "sdm":
        node.technical_id = f"{node.technical_id}_{origin}"

    for child in node.children:
        _mark_nodes_origin(child, origin)


def _merge_country_content(
    existing_country: XMLNode, new_country: XMLNode, country_code: str, origin: str,
):
    """Fusiona el contenido de un país del CSF con uno existente."""
    for new_element in new_country.children:
        if "hris" in new_element.tag.lower() and "element" in new_element.tag.lower():
            element_id = new_element.technical_id or new_element.attributes.get("id")

            existing_element = None
            for child in existing_country.children:
                if (
                    "hris" in child.tag.lower()
                    and "element" in child.tag.lower()
                    and (child.technical_id or child.attributes.get("id")) == element_id
                ):
                    existing_element = child
                    break

            if existing_element:
                _merge_element_fields(existing_element, new_element, country_code, origin)
            else:
                cloned_element = _clone_node(new_element, origin=origin, country_code=country_code)
                cloned_element.parent = existing_country
                cloned_element.depth = existing_country.depth + 1
                cloned_element.sibling_order = len(existing_country.children)

                if origin == "csf":
                    _generate_country_based_ids(cloned_element, country_code, origin)

                existing_country.children.append(cloned_element)


def _merge_element_fields(
    existing_element: XMLNode, new_element: XMLNode, country_code: str, origin: str,
):
    """Fusiona los campos (hris-field) de un elemento por país."""
    for new_field in new_element.children:
        if "hris" in new_field.tag.lower() and "field" in new_field.tag.lower():
            field_id = new_field.technical_id or new_field.attributes.get("id")

            existing_field_found = False
            for existing_field in existing_element.children:
                if (
                    "hris" in existing_field.tag.lower()
                    and "field" in existing_field.tag.lower()
                    and (existing_field.technical_id or existing_field.attributes.get("id")) == field_id
                ):
                    if "data-origin" not in existing_field.attributes:
                        existing_field.attributes["data-origin"] = "sdm"
                    existing_field_found = True
                    break

            if not existing_field_found:
                cloned_field = _clone_node(new_field, origin=origin, country_code=country_code)
                cloned_field.parent = existing_element
                cloned_field.depth = existing_element.depth + 1
                cloned_field.sibling_order = len(existing_element.children)

                if origin == "csf":
                    _generate_country_based_ids(cloned_field, country_code, origin)

                existing_element.children.append(cloned_field)


def _generate_country_based_ids(node: XMLNode, country_code: str, origin: str):
    """Genera IDs basados en país para elementos CSF."""
    if origin == "sdm":
        return

    current_id = node.technical_id or node.attributes.get("id", "")
    if not current_id:
        return

    node.attributes["data-original-id"] = current_id
    full_id = f"{country_code}_{current_id}_{origin}" if origin == "csf" else f"{country_code}_{current_id}"
    node.attributes["data-full-id"] = full_id
    node.technical_id = full_id

    if "hris" in node.tag.lower() and "element" in node.tag.lower():
        for child in node.children:
            if "hris" in child.tag.lower() and "field" in child.tag.lower():
                _generate_country_based_ids(child, country_code, origin)
