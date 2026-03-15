"""Validacion de format groups por pais → ERROR.

Los format groups definen regex, display_format e instructions para
campos especificos por pais. Si un format group esta incompleto
(sin regex, sin display_format), el split puede generar datos invalidos.
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext


@register_validator
class FormatGroupValidator(BaseValidator):
    """Verifica completitud y validez de format groups → ERROR/WARNING."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for country_code, groups in ctx.format_groups.items():
            self._check_country_groups(country_code, groups, issues)

        return issues

    def _check_country_groups(
        self, country_code: str, groups: dict, issues: list[ValidationResult],
    ) -> None:
        if not groups:
            return

        for group_id, group_data in groups.items():
            formats = group_data.get("formats", [])

            if not formats:
                issues.append(ValidationResult(
                    severity=Severity.WARNING,
                    code="FMT_001",
                    message=f"Format group '{group_id}' sin formatos definidos",
                    country_code=country_code,
                    validator=self.name,
                ))
                continue

            for fmt in formats:
                fmt_id = fmt.get("id", "?")
                reg_ex = fmt.get("reg_ex")
                display_format = fmt.get("display_format")

                if not reg_ex:
                    issues.append(ValidationResult(
                        severity=Severity.ERROR,
                        code="FMT_002",
                        message=(
                            f"Format group '{group_id}' formato '{fmt_id}' "
                            f"sin regex definido"
                        ),
                        country_code=country_code,
                        validator=self.name,
                    ))

                if reg_ex:
                    try:
                        re.compile(reg_ex)
                    except re.error as e:
                        issues.append(ValidationResult(
                            severity=Severity.ERROR,
                            code="FMT_003",
                            message=(
                                f"Format group '{group_id}' formato '{fmt_id}' "
                                f"regex invalido: {e}"
                            ),
                            country_code=country_code,
                            validator=self.name,
                        ))

                if not display_format:
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="FMT_004",
                        message=(
                            f"Format group '{group_id}' formato '{fmt_id}' "
                            f"sin display_format"
                        ),
                        country_code=country_code,
                        validator=self.name,
                    ))
