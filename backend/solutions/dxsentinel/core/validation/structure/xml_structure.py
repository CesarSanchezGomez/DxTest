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

        for elem in elements:
            eid = elem.get("element_id", "")
            config = SAP_ENTITY_CONFIGS.get(eid)
            if not config:
                continue
            field_ids = {f.get("field_id", "") for f in elem.get("fields", [])}
            for tpl_key in config.get("template", []):
                resolved = tpl_key.split(".")[-1] if "." in tpl_key else tpl_key
                if resolved not in field_ids and f"{eid}_{resolved}" not in catalog:
                    issues.append(self._emit(
                        Severity.FATAL, "STRUCT_006",
                        element_id=eid, field_id=resolved,
                    ))
