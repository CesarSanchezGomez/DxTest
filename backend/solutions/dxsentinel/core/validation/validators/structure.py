"""Validaciones de estructura XML → FATAL."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from .base import BaseValidator, ValidationContext

_VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")


@register_validator
class StructureValidator(BaseValidator):
    """Verifica la integridad estructural del modelo parseado.

    Cualquier fallo aqui es FATAL porque indica que el XML no puede
    procesarse de forma confiable.
    """

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        structure = ctx.parsed_model.get("structure", {})
        elements = ctx.processed_data.get("elements", [])

        self._check_root(structure, issues)
        self._check_elements_exist(elements, issues)
        self._check_duplicate_elements(elements, issues)
        self._check_business_keys(elements, ctx.field_catalog, issues)
        self._check_element_ids_valid(elements, issues)

        return issues

    def _check_root(self, structure: dict, issues: list[ValidationResult]) -> None:
        if not structure:
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="STRUCT_001",
                message="Modelo parseado sin nodo root o estructura vacia",
                validator=self.name,
            ))
            return

        if not structure.get("children"):
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="STRUCT_002",
                message="Nodo root sin elementos hijos",
                validator=self.name,
            ))

    def _check_elements_exist(self, elements: list[dict], issues: list[ValidationResult]) -> None:
        if not elements:
            issues.append(ValidationResult(
                severity=Severity.FATAL,
                code="STRUCT_003",
                message="No se encontraron elementos (hris-element) en el modelo",
                validator=self.name,
            ))

    def _check_duplicate_elements(self, elements: list[dict], issues: list[ValidationResult]) -> None:
        seen: dict[str, int] = {}
        for elem in elements:
            elem_id = elem.get("element_id", "")
            country = elem.get("country_code")
            key = f"{country}_{elem_id}" if country else elem_id
            seen[key] = seen.get(key, 0) + 1

        for key, count in seen.items():
            if count > 1:
                issues.append(ValidationResult(
                    severity=Severity.FATAL,
                    code="STRUCT_004",
                    message=f"Elemento duplicado '{key}' aparece {count} veces",
                    element_id=key,
                    validator=self.name,
                ))

    def _check_business_keys(
        self, elements: list[dict], field_catalog: dict,
        issues: list[ValidationResult],
    ) -> None:
        from ...constants import SAP_ENTITY_CONFIGS

        for elem in elements:
            elem_id = elem.get("element_id", "")
            config = SAP_ENTITY_CONFIGS.get(elem_id)
            if not config:
                continue

            template_keys = config.get("template", [])
            field_ids = {f.get("field_id", "") for f in elem.get("fields", [])}

            for tpl_key in template_keys:
                # Resolver: "personInfo.person-id-external" -> "person-id-external"
                resolved = tpl_key.split(".")[-1] if "." in tpl_key else tpl_key

                if resolved not in field_ids:
                    # Verificar si esta en el catalogo como campo del CSV
                    full_id = f"{elem_id}_{resolved}"
                    if full_id not in field_catalog:
                        issues.append(ValidationResult(
                            severity=Severity.FATAL,
                            code="STRUCT_005",
                            message=f"Business key '{resolved}' faltante en entidad '{elem_id}'",
                            element_id=elem_id,
                            field_id=resolved,
                            validator=self.name,
                        ))

    def _check_element_ids_valid(self, elements: list[dict], issues: list[ValidationResult]) -> None:
        for elem in elements:
            elem_id = elem.get("element_id", "")
            if elem_id and not _VALID_ID_PATTERN.match(elem_id):
                issues.append(ValidationResult(
                    severity=Severity.FATAL,
                    code="STRUCT_006",
                    message=f"Element ID '{elem_id}' contiene caracteres invalidos",
                    element_id=elem_id,
                    validator=self.name,
                ))
