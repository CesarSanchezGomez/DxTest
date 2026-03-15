"""Wrapper de validacion sobre FieldFilter existente → WARNING.

Delega la logica de filtrado al FieldFilter existente y traduce
sus exclusion_reasons a ValidationResults formales.
"""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext
from ...generators.golden_record.field_filter import FieldFilter


# exclusion_reason substring → codigo de mensaje
_REASON_TO_CODE: dict[str, str] = {
    "visibility='none'":     "FILTER_001",
    "viewable='false'":      "FILTER_002",
    "campo técnico interno": "FILTER_003",
    "filtered_by_attributes": "FILTER_004",
    "filtered_custom_range": "FILTER_005",
    "explicitly_excluded":   "FILTER_006",
    "visibility=":           "FILTER_007",
}


@register_validator
class FieldFilterValidator(BaseValidator):
    """Reporta campos excluidos por FieldFilter (WARNING)."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []
        structure = ctx.parsed_model.get("structure", {})
        if not structure:
            return issues

        field_filter = FieldFilter()
        self._walk(structure, field_filter, issues)
        return issues

    def _walk(self, node: dict, ff: FieldFilter, issues: list[ValidationResult]) -> None:
        tag = node.get("tag", "").lower()

        if "hris-field" in tag or tag == "field":
            fid = node.get("technical_id") or node.get("id", "")
            include, reason = ff.filter_field(node)
            if not include and reason:
                code = self._resolve_code(reason)
                issues.append(self._emit(
                    Severity.WARNING, code,
                    field_id=fid, reason=reason, visibility=reason,
                ))

        for child in node.get("children", []):
            self._walk(child, ff, issues)

    @staticmethod
    def _resolve_code(reason: str) -> str:
        for key, code in _REASON_TO_CODE.items():
            if key in reason:
                return code
        return "FILTER_099"
