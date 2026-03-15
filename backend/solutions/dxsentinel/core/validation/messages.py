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

        # character.py (structure)
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

        # entity_completeness.py
        "INCOMPLETE_ENTITY": "Con datos: {filled}. Faltantes: {missing}",

        # required_fields.py
        "REQUIRED_FIELD_EMPTY": "Campo obligatorio vacio",

        # duplicate_person_id.py
        "DUPLICATE_PERSON_ID": "ID duplicado '{person_id}'. Aparece en las filas: {rows}",

        # email.py
        "INVALID_EMAIL_FORMAT": "Formato invalido. Esperado: usuario@dominio.com",

        # type_validator.py
        "INVALID_DATE_FORMAT": "Formato invalido. Esperado: {expected}",
        "INVALID_INTEGER": "Debe ser numero entero (sin decimales)",
        "INVALID_DECIMAL": "Debe ser numero (puede tener decimales con punto)",
        "INVALID_BOOLEAN": "Valores aceptados: Yes, No, True, False, 1, 0",

        # length.py
        "MAX_LENGTH_EXCEEDED": "Longitud: {actual_length} caracteres. Maximo: {max_length}",

        # character.py (content)
        "INVALID_CHARACTERS": "Caracteres invalidos {chars} en: '{value}'. Problema de encoding",
        "SUSPICIOUS_ENCODING": "Caracteres sospechosos {chars} en: '{value}'. Posible problema de encoding",

        # national_id_format.py
        "INVALID_NATIONAL_ID_FORMAT": "ID nacional invalido para {countries}. Formato esperado: {formats}",

        # no_data_rows
        "NO_DATA_ROWS": "CSV sin datos. Headers y labels correctos pero no hay filas de datos",

        # ── content/country/mex/ ──────────────────────────────────────────
        # curp.py
        "CURP_EMPTY_FIELD": "Campo '{field_name}' esta vacio",
        "CURP_NOT_UPPERCASE": "La CURP no esta en mayusculas",
        "CURP_INVALID_LENGTH": "La CURP debe tener {expected} caracteres. Tiene: {actual}",
        "CURP_INVALID_DATE_FORMAT": "Fecha de nacimiento no es valida (dd/mm/aaaa)",
        "CURP_NAME_MISMATCH": "Las iniciales de nombre y apellidos no coinciden con la CURP",
        "CURP_DATE_MISMATCH": "La fecha de nacimiento no coincide con la CURP",
        "CURP_GENDER_INVALID_VALUE": (
            "El valor del genero no pertenece a ningún valor de la picklist. "
            "Formato de idioma: {language_label}. Valores aceptados: {picklist}"
        ),
        "CURP_GENDER_MISMATCH": (
            "Genero no coincide con CURP. "
            "Formato de idioma: {language_label}. Valores esperados del genero: {picklist}"
        ),
        "CURP_STATE_NOT_IN_PICKLIST": (
            "Inconsistencia en estado de nacimiento: el valor registrado '{region}' "
            "no corresponde a ninguna opcion de la picklist oficial 'state_mex'"
        ),
        "CURP_STATE_FOREIGN_NOT_NE": (
            "Inconsistencia detectada: el pais de nacimiento ({country_of_birth}) "
            "indica origen extranjero, pero la CURP contiene el codigo '{state_in_curp}' en lugar de 'NE'"
        ),
        "CURP_STATE_MEXICO_IS_NE": (
            "El empleado nacio en Mexico (country-of-birth = MEX) "
            "pero la CURP indica nacido en el extranjero (NE). "
            "Debe corresponder a un estado de la Republica Mexicana"
        ),
        "CURP_STATE_MISMATCH": "El lugar de nacimiento no coincide con la CURP",

        # work_permit.py (RFC/NSS)
        "WORK_PERMIT_INCOMPLETE": "workPermitInfo incompleto: falta tipo o numero de documento",
        "WORK_PERMIT_COUNT_MISMATCH": (
            "La cantidad de tipos ({types_count}) y numeros ({numbers_count}) "
            "de documento no coincide"
        ),
        "WORK_PERMIT_RFC_INVALID": (
            "RFC en posicion {position} no tiene formato valido. "
            "Esperado: persona fisica AAAA######AAA (13 chars) o "
            "persona moral AAA######AAA (12 chars)"
        ),
        "WORK_PERMIT_NSS_INVALID": "NSS en posicion {position} no tiene formato valido. Esperado: 11 digitos numericos",
        "WORK_PERMIT_UNKNOWN_TYPE": "Tipo de documento desconocido en posicion {position}: '{value}'",

        # ── engine ───────────────────────────────────────────────────────
        "ENGINE_001": "Validator '{validator}' fallo: {error}",
    }

    @classmethod
    def get(cls, code: str, **kwargs: object) -> str:
        """Obtiene y formatea un mensaje por codigo."""
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
