import re
import xml.etree.ElementTree as ET
from typing import List, Optional

XML_LANG_KEY = "{http://www.w3.org/XML/1998/namespace}lang"
DEBUG_LANG = "en-DEBUG"

MODEL_TAGS = {
    "cdm": "corporate-data-model",
    "sdm": "succession-data-model",
}


def _normalize_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [i for i in value if isinstance(i, str) and i.strip()]
    return []


def _ensure_debug_language(idiomas: Optional[List[str]]) -> List[str]:
    result = set(idiomas) if idiomas else set()
    result.add(DEBUG_LANG)
    return list(result)


def _strip_comments_and_clean(xml_str: str) -> str:
    if not xml_str or not xml_str.strip():
        raise ValueError("El XML esta vacio")
    cleaned = re.sub(r"<!--.*?-->", "", xml_str, flags=re.DOTALL)
    cleaned = re.sub(r"^\s*<\?xml.*?\?>\s*", "", cleaned, flags=re.DOTALL)
    return "\n".join(ln for ln in cleaned.splitlines() if ln.strip())


def _filter_by_language(elem, idiomas: List[str]):
    for child in list(elem):
        _filter_by_language(child, idiomas)
        lang = child.attrib.get(XML_LANG_KEY)
        if lang is not None and lang not in idiomas:
            elem.remove(child)


def _parse_and_filter(xml_section: str, idiomas: List[str]) -> str:
    try:
        root = ET.fromstring(f"<root>{xml_section}</root>")
    except ET.ParseError as e:
        raise ValueError(f"Error de parseo XML: {e}")

    for elem in root.iter():
        _filter_by_language(elem, idiomas)

    return "".join(ET.tostring(e, encoding="unicode") for e in root)


def _procesar_modelo(xml_str: str, tag: str, idiomas: Optional[List[str]] = None) -> str:
    idiomas = _ensure_debug_language(idiomas)
    xml_clean = _strip_comments_and_clean(xml_str)

    inicio = xml_clean.find(f"<{tag}")
    if inicio == -1:
        raise ValueError(f"El XML no corresponde a un {tag}")

    contenido_antes = xml_clean[:inicio]
    contenido_limpio = _parse_and_filter(xml_clean[inicio:], idiomas)

    return f"{contenido_antes}\n{contenido_limpio}".strip()


def procesar_cdm(xml_str: str, idiomas: Optional[List[str]] = None) -> str:
    return _procesar_modelo(xml_str, MODEL_TAGS["cdm"], idiomas)


def procesar_sdm(xml_str: str, idiomas: Optional[List[str]] = None) -> str:
    return _procesar_modelo(xml_str, MODEL_TAGS["sdm"], idiomas)


def _detectar_tipo_csf(xml_clean: str) -> str:
    inicio = xml_clean.find("<country-specific-fields")
    fin = xml_clean.find("</country-specific-fields>")
    if inicio == -1 or fin == -1:
        raise ValueError("CSF invalido: falta country-specific-fields")

    fragmento = xml_clean[inicio: fin + len("</country-specific-fields>")]
    try:
        root = ET.fromstring(f"<root>{fragmento}</root>")
    except ET.ParseError as e:
        raise ValueError(f"CSF invalido: error de parseo - {e}")

    csf = root.find("country-specific-fields")
    if csf is None:
        raise ValueError("CSF invalido: estructura incorrecta")

    if csf.find(".//format-group") is not None:
        return "csf_sdm"
    if csf.find(".//hris-element") is not None:
        return "csf_cdm"

    raise ValueError("CSF invalido: tipo no determinado")


def procesar_csf(
        xml_str: str,
        paises: Optional[List[str]] = None,
        idiomas: Optional[List[str]] = None,
        tipo_esperado: Optional[str] = None,
) -> str:
    idiomas = _ensure_debug_language(idiomas)
    xml_clean = _strip_comments_and_clean(xml_str)

    tipo_detectado = _detectar_tipo_csf(xml_clean)
    if tipo_esperado and tipo_detectado != tipo_esperado:
        raise ValueError(f"CSF incorrecto. Esperado: {tipo_esperado}, detectado: {tipo_detectado}")

    tag_open = "<country-specific-fields"
    tag_close = "</country-specific-fields>"
    inicio = xml_clean.find(tag_open)
    fin = xml_clean.find(tag_close)
    if inicio == -1 or fin == -1:
        raise ValueError("El XML no corresponde a un Country Specific Fields valido")

    contenido_antes = xml_clean[:inicio]
    fragmento = xml_clean[inicio: fin + len(tag_close)]

    try:
        root = ET.fromstring(f"<root>{fragmento}</root>")
    except ET.ParseError as e:
        raise ValueError(f"Error al parsear CSF: {e}")

    csf = root.find("country-specific-fields")
    if csf is None:
        raise ValueError("Estructura CSF invalida")

    paises_norm = _normalize_list(paises)
    for country in list(csf.findall("country")):
        if paises_norm and country.attrib.get("id") not in paises_norm:
            csf.remove(country)
            continue
        for elem in country.iter():
            _filter_by_language(elem, idiomas)

    contenido_limpio = "".join(ET.tostring(e, encoding="unicode") for e in root)
    return f"{contenido_antes}\n{contenido_limpio}".strip()


def procesar_data_model_completo(
        cdm_xml: Optional[str],
        csf_cdm_xml: Optional[str],
        sdm_xml: Optional[str],
        csf_sdm_xml: Optional[str],
        *,
        paises: Optional[List[str]] = None,
        idiomas: Optional[List[str]] = None,
) -> dict:
    idiomas_norm = _ensure_debug_language(_normalize_list(idiomas))
    paises_norm = _normalize_list(paises)

    processors = {
        "cdm": lambda: procesar_cdm(cdm_xml, idiomas_norm) if cdm_xml else "",
        "csf_cdm": lambda: procesar_csf(csf_cdm_xml, paises_norm, idiomas_norm,
                                        tipo_esperado="csf_cdm") if csf_cdm_xml else "",
        "sdm": lambda: procesar_sdm(sdm_xml, idiomas_norm) if sdm_xml else "",
        "csf_sdm": lambda: procesar_csf(csf_sdm_xml, paises_norm, idiomas_norm,
                                        tipo_esperado="csf_sdm") if csf_sdm_xml else "",
    }

    return {key: fn() for key, fn in processors.items()}
