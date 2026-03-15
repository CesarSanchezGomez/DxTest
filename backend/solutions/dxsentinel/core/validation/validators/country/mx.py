"""Validaciones especificas de Mexico → ERROR."""

from __future__ import annotations

import re

from ....validation.registry import register_validator
from ....validation.result import Severity, ValidationResult
from ..base import ValidationContext
from .base import CountryValidator

# CURP: 18 caracteres alfanumericos con estructura definida
_CURP_PATTERN = re.compile(
    r"^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$",
    re.IGNORECASE,
)

# RFC persona fisica: 13 caracteres | RFC persona moral: 12 caracteres
_RFC_PATTERN = re.compile(
    r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$",
    re.IGNORECASE,
)


@register_validator
class MexicoValidator(CountryValidator):
    """Validaciones para Mexico: CURP, RFC, format groups."""

    @property
    def country_code(self) -> str:
        return "MX"

    def validate_country(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        self._check_format_groups(ctx, issues)
        self._check_national_id_config(ctx, issues)
        self._check_work_permit_config(ctx, issues)

        return issues

    def _check_format_groups(self, ctx: ValidationContext, issues: list[ValidationResult]) -> None:
        """Verifica que MX tenga format groups con regex definidos."""
        mx_groups = ctx.format_groups.get("MX", {})

        for group_id, group_data in mx_groups.items():
            formats = group_data.get("formats", [])
            for fmt in formats:
                if not fmt.get("reg_ex"):
                    issues.append(ValidationResult(
                        severity=Severity.ERROR,
                        code="MX_FMT_001",
                        message=(
                            f"Format group '{group_id}' formato '{fmt.get('id')}' "
                            f"sin regex definido"
                        ),
                        country_code="MX",
                        validator=self.name,
                    ))

    def _check_national_id_config(self, ctx: ValidationContext, issues: list[ValidationResult]) -> None:
        """Verifica configuracion de nationalIdCard para MX (CURP)."""
        for elem in ctx.processed_data.get("elements", []):
            elem_id = elem.get("element_id", "")
            country = elem.get("country_code")

            if "nationalIdCard" not in elem_id:
                continue
            if country and country != "MX":
                continue

            field_ids = {f.get("field_id", "") for f in elem.get("fields", [])}

            # CURP requiere card-type y national-id
            required_fields = {"card-type", "country"}
            missing = required_fields - field_ids
            if missing:
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="MX_CURP_001",
                    message=(
                        f"nationalIdCard para MX: campos faltantes para CURP: "
                        f"{', '.join(sorted(missing))}"
                    ),
                    element_id=elem_id,
                    country_code="MX",
                    validator=self.name,
                ))

    def _check_work_permit_config(self, ctx: ValidationContext, issues: list[ValidationResult]) -> None:
        """Verifica configuracion de workPermitInfo para MX."""
        for elem in ctx.processed_data.get("elements", []):
            elem_id = elem.get("element_id", "")
            country = elem.get("country_code")

            if "workPermitInfo" not in elem_id:
                continue
            if country and country != "MX":
                continue

            field_ids = {f.get("field_id", "") for f in elem.get("fields", [])}

            required_fields = {"document-type", "document-number", "country"}
            missing = required_fields - field_ids
            if missing:
                issues.append(ValidationResult(
                    severity=Severity.ERROR,
                    code="MX_WP_001",
                    message=(
                        f"workPermitInfo para MX: campos faltantes: "
                        f"{', '.join(sorted(missing))}"
                    ),
                    element_id=elem_id,
                    country_code="MX",
                    validator=self.name,
                ))
