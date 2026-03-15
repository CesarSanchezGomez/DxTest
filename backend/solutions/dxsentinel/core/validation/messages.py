"""Catalogo centralizado de mensajes de validacion.

Cada codigo de validacion tiene un template de mensaje con placeholders.
Los validators usan Messages.get() en lugar de hardcodear strings.
"""

from __future__ import annotations


class Messages:
    """Catalogo de mensajes indexado por codigo de validacion."""

    _CATALOG: dict[str, str] = {
        # ── structure/ ────────────────────────────────────────────────────
        # xml_structure.py
        "STRUCT_001": "Modelo parseado sin nodo root o estructura vacia",
        "STRUCT_002": "Nodo root sin elementos hijos",
        "STRUCT_003": "No se encontraron elementos (hris-element) en el modelo",
        "STRUCT_004": "Element ID contiene caracteres invalidos: '{element_id}'",
        "STRUCT_005": "Elemento duplicado '{key}' aparece {count} veces",
        "STRUCT_006": "Business key '{field_id}' faltante en entidad '{element_id}'",

        # character.py
        "CHAR_001": "Field ID contiene caracteres invalidos: '{field_id}'",
        "CHAR_002": "Full field ID contiene caracteres invalidos: '{full_id}'",
        "CHAR_003": "Caracteres de control en field ID: '{field_id}'",

        # upload.py
        "UPLOAD_001": "Tipo de archivo no soportado: '{filename}'. Solo XML y CSV.",
        "UPLOAD_002": "Archivo XML excede limite de 50MB ({size_mb:.1f}MB)",
        "UPLOAD_003": "Archivo CSV excede limite de 100MB ({size_mb:.1f}MB)",

        # ── content/ ─────────────────────────────────────────────────────
        # field_rules.py
        "FIELD_001": "Tipo declarado '{declared}' no coincide con esperado '{expected}' para {full_id}",
        "FIELD_002": "Campo required con visibility='none': {full_id}",
        "FIELD_003": "Campo tipo picklist sin picklist_id: {full_id}",
        "FIELD_004": "Entidad '{element_id}' procesada sin campos",

        # field_filter.py
        "FILTER_001": "Campo '{field_id}' excluido: visibility='none'",
        "FILTER_002": "Campo '{field_id}' excluido: viewable='false'",
        "FILTER_003": "Campo '{field_id}' excluido: campo tecnico interno",
        "FILTER_004": "Campo '{field_id}' excluido: filtered_by_attributes",
        "FILTER_005": "Campo '{field_id}' excluido: filtered_custom_range",
        "FILTER_006": "Campo '{field_id}' excluido: explicitly_excluded",
        "FILTER_007": "Campo '{field_id}' excluido: visibility='{visibility}'",
        "FILTER_099": "Campo '{field_id}' excluido: {reason}",

        # label.py
        "LABEL_001": "Campo sin labels: {full_id}",
        "LABEL_002": "Sin label para idioma '{language}': {full_id}",
        "LABEL_003": "Label vacio para idioma '{lang_key}': {full_id}",
        "LABEL_004": "Caracteres de control en label ({lang_key}): '{preview}'",
        "LABEL_005": "Problemas de encoding en label ({lang_key}): '{preview}'",
        "LABEL_006": "Label duplicado '{label}' en '{element_id}': campos {first} y {second}",
        "LABEL_007": "Language code invalido en XML: '{lang}' (esperado: xx o xx-XX)",

        # format_group.py
        "FMT_001": "Format group '{group_id}' sin formatos definidos",
        "FMT_002": "Format group '{group_id}' formato '{fmt_id}' sin regex definido",
        "FMT_003": "Format group '{group_id}' formato '{fmt_id}' regex invalido: {error}",
        "FMT_004": "Format group '{group_id}' formato '{fmt_id}' sin display_format",

        # ── country/ ─────────────────────────────────────────────────────
        # mx.py
        "MX_CURP_001": "nationalIdCard para MX: campos faltantes para CURP: {missing}",
        "MX_WP_001": "workPermitInfo para MX: campos faltantes: {missing}",

        # ── engine ───────────────────────────────────────────────────────
        "ENGINE_001": "Validator '{validator}' fallo: {error}",
    }

    @classmethod
    def get(cls, code: str, **kwargs: object) -> str:
        """Obtiene y formatea un mensaje por codigo.

        Si el codigo no existe, retorna el codigo tal cual.
        Si el formateo falla, retorna el template sin formatear.
        """
        template = cls._CATALOG.get(code, code)
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template

    @classmethod
    def has(cls, code: str) -> bool:
        return code in cls._CATALOG
