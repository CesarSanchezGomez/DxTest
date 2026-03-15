import re
from typing import Any, Dict, List

from ...models.error_severity import ErrorSeverity
from ...models.validation_error import ValidationError
from ..messages import ContentMessages
from .base_validator import BaseContentValidator


class NationalIdFormatValidator(BaseContentValidator):
    """
    Valida que el valor del campo national-id coincida con al menos uno de los
    patrones de formato definidos en format_groups del metadata para los países
    activos del golden record.
    """

    TARGET_FIELD_ID = "national-id"
    TARGET_ENTITY_ID = "nationalIdCard"
    FORMAT_GROUP_KEY = "national-id"

    def __init__(self, format_groups: Dict, country_codes: List[str]):
        self.country_codes = [c.upper() for c in (country_codes or [])]
        self._compiled: Dict[str, List[Dict]] = self._build_compiled_patterns(
            format_groups or {}
        )

    def _build_compiled_patterns(self, format_groups: Dict) -> Dict[str, List[Dict]]:
        """Precompila las expresiones regulares de cada país."""
        compiled: Dict[str, List[Dict]] = {}
        for country in self.country_codes:
            fg = format_groups.get(country, {}).get(self.FORMAT_GROUP_KEY)
            if not fg:
                continue
            patterns = []
            for fmt in fg.get("formats", []):
                raw_regex = fmt.get("reg_ex")
                if not raw_regex:
                    continue
                try:
                    patterns.append({
                        "regex": re.compile(f"^(?:{raw_regex})$"),
                        "display_format": fmt.get("display_format", ""),
                        "format_id": fmt.get("id", ""),
                    })
                except re.error:
                    pass
            if patterns:
                compiled[country] = patterns
        return compiled

    def has_rules(self) -> bool:
        """True si hay al menos un patrón compilado para algún país activo."""
        return bool(self._compiled)

    def validate(self, value: Any, context: Dict) -> List[ValidationError]:
        if not self._compiled:
            return []

        value_str = str(value).strip()
        if not value_str:
            return []

        # El valor es válido si coincide con el patrón de CUALQUIER país activo
        for patterns in self._compiled.values():
            for pat in patterns:
                if pat["regex"].match(value_str):
                    return []

        # Construir lista de formatos esperados para el mensaje de error
        expected_formats = [
            f"{country}: {pat['display_format']}"
            for country, patterns in self._compiled.items()
            for pat in patterns
            if pat["display_format"]
        ]

        return [ValidationError(
            code="INVALID_NATIONAL_ID_FORMAT",
            message=ContentMessages.invalid_national_id_format(
                value_str,
                self.country_codes,
                expected_formats,
            ),
            severity=ErrorSeverity.ERROR,
            row_index=context.get("row_index"),
            column_name=context.get("column_name"),
            entity_id=context.get("entity_id"),
            field_id=context.get("field_id"),
            person_id=context.get("person_id"),
            value=value_str[:50],
        )]
