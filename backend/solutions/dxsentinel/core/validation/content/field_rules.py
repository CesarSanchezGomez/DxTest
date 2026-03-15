"""Validacion de coherencia de campos → ERROR."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext


@register_validator
class FieldRulesValidator(BaseValidator):
    """Verifica coherencia de reglas de campos (ERROR)."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for full_id, entry in ctx.field_catalog.items():
            eid = entry.get("element", "")
            fid = entry.get("field", "")

            self._check_type(full_id, entry, eid, fid, issues)
            self._check_required_visibility(full_id, entry, eid, fid, issues)
            self._check_picklist(full_id, entry, eid, fid, issues)

        for elem in ctx.processed_data.get("elements", []):
            if elem.get("field_count", 0) == 0:
                eid = elem.get("element_id", "")
                issues.append(self._emit(Severity.ERROR, "FIELD_004", element_id=eid))

        return issues

    def _check_type(self, full_id: str, entry: dict, eid: str, fid: str, issues: list) -> None:
        from ...constants import get_metadata_type

        declared = entry.get("data_type", "string")
        expected = get_metadata_type(eid, fid)
        if expected and declared != expected:
            issues.append(self._emit(
                Severity.ERROR, "FIELD_001",
                element_id=eid, field_id=fid,
                full_id=full_id, declared=declared, expected=expected,
            ))

    def _check_required_visibility(self, full_id: str, entry: dict, eid: str, fid: str, issues: list) -> None:
        if entry.get("required") and entry.get("visibility") == "none":
            issues.append(self._emit(Severity.ERROR, "FIELD_002", element_id=eid, field_id=fid, full_id=full_id))

    def _check_picklist(self, full_id: str, entry: dict, eid: str, fid: str, issues: list) -> None:
        if entry.get("data_type") == "picklist" and not entry.get("picklist_id"):
            issues.append(self._emit(Severity.ERROR, "FIELD_003", element_id=eid, field_id=fid, full_id=full_id))
