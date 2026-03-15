"""Wrapper de validacion sobre FieldFilter existente → ERROR.

Re-expone las reglas del FieldFilter (visibility, excluded, internal,
deprecated, custom ranges) como ValidationResults formales para que
queden registradas en el reporte, en vez de descartarse silenciosamente.

No duplica la logica de filtrado: usa el FieldFilter existente y traduce
sus exclusion_reasons a resultados de validacion.
"""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext
from ...generators.golden_record.field_filter import FieldFilter


# Mapa de exclusion_reason → (codigo, severity)
_REASON_MAP: dict[str, tuple[str, Severity]] = {
    "visibility='none'":              ("FILTER_001", Severity.WARNING),
    "viewable='false'":               ("FILTER_002", Severity.WARNING),
    "campo técnico interno":          ("FILTER_003", Severity.WARNING),
    "filtered_by_attributes":         ("FILTER_004", Severity.WARNING),
    "filtered_custom_range":          ("FILTER_005", Severity.WARNING),
}


@register_validator
class FieldFilterValidator(BaseValidator):
    """Ejecuta FieldFilter sobre campos del XML y reporta exclusiones.

    Severidad WARNING: informativo. Los campos excluidos no aparecen
    en el golden record pero el usuario debe saber por que.
    """

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []
        field_filter = FieldFilter()

        structure = ctx.parsed_model.get("structure", {})
        if not structure:
            return issues

        self._walk_and_check(structure, field_filter, issues)

        return issues

    def _walk_and_check(
        self, node: dict, field_filter: FieldFilter,
        issues: list[ValidationResult],
    ) -> None:
        tag = node.get("tag", "").lower()

        if "hris-field" in tag or "field" == tag:
            field_id = node.get("technical_id") or node.get("id", "")
            include, reason = field_filter.filter_field(node)

            if not include and reason:
                code, severity = self._resolve_reason(reason)
                issues.append(ValidationResult(
                    severity=severity,
                    code=code,
                    message=f"Campo '{field_id}' excluido: {reason}",
                    field_id=field_id,
                    validator=self.name,
                ))

        for child in node.get("children", []):
            self._walk_and_check(child, field_filter, issues)

    def _resolve_reason(self, reason: str) -> tuple[str, Severity]:
        """Mapea la razon de exclusion a codigo y severidad."""
        for key, (code, severity) in _REASON_MAP.items():
            if key in reason:
                return code, severity

        # Exclusion explicita por ID
        if "explicitly_excluded" in reason:
            return "FILTER_006", Severity.WARNING

        # Visibility no reconocida
        if "visibility=" in reason:
            return "FILTER_007", Severity.WARNING

        return "FILTER_099", Severity.WARNING
