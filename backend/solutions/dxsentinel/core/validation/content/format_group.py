"""Validacion de format groups por pais → ERROR/WARNING."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext


@register_validator
class FormatGroupValidator(BaseValidator):
    """Verifica completitud y validez de format groups."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for cc, groups in ctx.format_groups.items():
            for gid, gdata in (groups or {}).items():
                formats = gdata.get("formats", [])
                if not formats:
                    issues.append(self._emit(Severity.WARNING, "FMT_001", country_code=cc, group_id=gid))
                    continue

                for fmt in formats:
                    fid = fmt.get("id", "?")
                    regex = fmt.get("reg_ex")

                    if not regex:
                        issues.append(self._emit(Severity.ERROR, "FMT_002", country_code=cc, group_id=gid, fmt_id=fid))
                    elif regex:
                        try:
                            re.compile(regex)
                        except re.error as e:
                            issues.append(self._emit(
                                Severity.ERROR, "FMT_003",
                                country_code=cc, group_id=gid, fmt_id=fid, error=str(e),
                            ))

                    if not fmt.get("display_format"):
                        issues.append(self._emit(Severity.WARNING, "FMT_004", country_code=cc, group_id=gid, fmt_id=fid))

        return issues
