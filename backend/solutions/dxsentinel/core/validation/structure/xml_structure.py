"""Validacion de estructura del modelo XML → FATAL."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")


@register_validator
class XMLStructureValidator(BaseValidator):
    """Verifica integridad estructural del modelo parseado (FATAL)."""

    modes = ("generation",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []
        structure = ctx.parsed_model.get("structure", {})
        elements = ctx.processed_data.get("elements", [])

        if not structure:
            issues.append(self._emit(Severity.FATAL, "STRUCT_001"))
            return issues

        if not structure.get("children"):
            issues.append(self._emit(Severity.FATAL, "STRUCT_002"))

        if not elements:
            issues.append(self._emit(Severity.FATAL, "STRUCT_003"))
            return issues

        for elem in elements:
            eid = elem.get("element_id", "")
            if eid and not _VALID_ID_PATTERN.match(eid):
                issues.append(self._emit(Severity.FATAL, "STRUCT_004", element_id=eid))

        seen: dict[str, int] = {}
        for elem in elements:
            eid = elem.get("element_id", "")
            cc = elem.get("country_code")
            key = f"{cc}_{eid}" if cc else eid
            seen[key] = seen.get(key, 0) + 1
        for key, count in seen.items():
            if count > 1:
                issues.append(self._emit(Severity.FATAL, "STRUCT_005", element_id=key, key=key, count=count))

        self._check_business_keys(elements, ctx.field_catalog, issues)
        return issues

    def _check_business_keys(self, elements: list[dict], catalog: dict, issues: list) -> None:
        from ...constants import SAP_ENTITY_CONFIGS

        # Indice de field_ids por entity para buscar cross-entity references
        fields_by_entity: dict[str, set[str]] = {}
        for elem in elements:
            e = elem.get("element_id", "")
            fields_by_entity.setdefault(e, set()).update(
                f.get("field_id", "") for f in elem.get("fields", [])
            )

        for elem in elements:
            eid = elem.get("element_id", "")
            config = SAP_ENTITY_CONFIGS.get(eid)
            if not config:
                continue

            field_ids = fields_by_entity.get(eid, set())
            inject = set(config.get("inject", []))
            parent_entity = config.get("references")

            for tpl_key in config.get("template", []):
                if self._is_key_resolvable(
                    tpl_key, eid, field_ids, inject, parent_entity,
                    fields_by_entity, catalog,
                ):
                    continue

                resolved = tpl_key.split(".")[-1] if "." in tpl_key else tpl_key
                issues.append(self._emit(
                    Severity.FATAL, "STRUCT_006",
                    element_id=eid, field_id=resolved,
                ))

    @staticmethod
    def _is_key_resolvable(
        tpl_key: str, eid: str, field_ids: set, inject: set,
        parent_entity: str | None, fields_by_entity: dict, catalog: dict,
    ) -> bool:
        """Verifica si un business key es resoluble desde alguna fuente."""
        # Referencia cross-entity explicita: "personInfo.person-id-external"
        if "." in tpl_key:
            ref_entity, ref_field = tpl_key.split(".", 1)
            ref_fields = fields_by_entity.get(ref_entity, set())
            return (ref_field in ref_fields
                    or f"{ref_entity}_{ref_field}" in catalog
                    or f"{eid}_{ref_field}" in catalog)

        # Campo propio del elemento
        if tpl_key in field_ids or tpl_key in inject or f"{eid}_{tpl_key}" in catalog:
            return True

        # Foreign key implicita: buscar en entidad padre (references)
        if parent_entity:
            parent_fields = fields_by_entity.get(parent_entity, set())
            if (tpl_key in parent_fields
                    or f"{parent_entity}_{tpl_key}" in catalog):
                return True

        # Buscar en cualquier entidad del modelo (campo compartido)
        for entity_fields in fields_by_entity.values():
            if tpl_key in entity_fields:
                return True

        return False
