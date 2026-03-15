"""Validaciones de contenido de campos → ERROR."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from .base import BaseValidator, ValidationContext


@register_validator
class ContentValidator(BaseValidator):
    """Verifica coherencia de contenido en campos y atributos.

    Los fallos aqui son ERROR: el golden record se genera pero no se
    permite hacer split hasta corregir.
    """

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        self._check_type_coherence(ctx.field_catalog, issues)
        self._check_required_visibility(ctx.field_catalog, issues)
        self._check_picklist_ids(ctx.field_catalog, issues)
        self._check_empty_elements(ctx.processed_data, issues)

        return issues

    def _check_type_coherence(self, catalog: dict, issues: list[ValidationResult]) -> None:
        from ...constants import get_metadata_type

        for full_id, entry in catalog.items():
            element = entry.get("element", "")
            field_id = entry.get("field", "")
            declared_type = entry.get("data_type", "string")
            expected_type = get_metadata_type(element, field_id)

            if expected_type and declared_type != expected_type:
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="CONTENT_001",
                    message=(
                        f"Tipo declarado '{declared_type}' no coincide con esperado "
                        f"'{expected_type}' para {full_id}"
                    ),
                    element_id=element,
                    field_id=field_id,
                    validator=self.name,
                ))

    def _check_required_visibility(self, catalog: dict, issues: list[ValidationResult]) -> None:
        for full_id, entry in catalog.items():
            if entry.get("required") and entry.get("visibility") == "none":
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="CONTENT_002",
                    message=f"Campo required con visibility='none': {full_id}",
                    element_id=entry.get("element"),
                    field_id=entry.get("field"),
                    validator=self.name,
                ))

    def _check_picklist_ids(self, catalog: dict, issues: list[ValidationResult]) -> None:
        for full_id, entry in catalog.items():
            if entry.get("data_type") == "picklist" and not entry.get("picklist_id"):
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="CONTENT_003",
                    message=f"Campo tipo picklist sin picklist_id: {full_id}",
                    element_id=entry.get("element"),
                    field_id=entry.get("field"),
                    validator=self.name,
                ))

    def _check_empty_elements(self, processed_data: dict, issues: list[ValidationResult]) -> None:
        for elem in processed_data.get("elements", []):
            if elem.get("field_count", 0) == 0:
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="CONTENT_004",
                    message=f"Entidad '{elem.get('element_id')}' procesada sin campos",
                    element_id=elem.get("element_id"),
                    validator=self.name,
                ))
