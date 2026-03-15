"""Validaciones especificas de Mexico → ERROR."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import ValidationContext
from .base import CountryValidator

_CURP_PATTERN = re.compile(r"^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$", re.IGNORECASE)
_RFC_PATTERN = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", re.IGNORECASE)


@register_validator
class MexicoValidator(CountryValidator):
    """Validaciones para Mexico: CURP, RFC, work permit."""

    @property
    def country_code(self) -> str:
        return "MX"

    def validate_country(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for elem in ctx.processed_data.get("elements", []):
            eid = elem.get("element_id", "")
            cc = elem.get("country_code")

            if "nationalIdCard" in eid and (not cc or cc == "MX"):
                self._check_required(elem, {"card-type", "country"}, "MX_CURP_001", issues)

            if "workPermitInfo" in eid and (not cc or cc == "MX"):
                self._check_required(elem, {"document-type", "document-number", "country"}, "MX_WP_001", issues)

        return issues

    def _check_required(self, elem: dict, required: set[str], code: str, issues: list) -> None:
        field_ids = {f.get("field_id", "") for f in elem.get("fields", [])}
        missing = required - field_ids
        if missing:
            issues.append(self._emit(
                Severity.ERROR, code,
                element_id=elem.get("element_id", ""),
                country_code="MX",
                missing=", ".join(sorted(missing)),
            ))
