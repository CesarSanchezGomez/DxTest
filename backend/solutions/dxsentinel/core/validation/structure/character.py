"""Validacion de caracteres en IDs tecnicos → FATAL."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@register_validator
class CharacterStructureValidator(BaseValidator):
    """Verifica caracteres invalidos en IDs tecnicos (FATAL)."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for col in ctx.columns:
            fid = col.get("field_id", "")
            full = col.get("full_id", "")
            eid = col.get("element_id", "")

            if fid and not _VALID_ID_PATTERN.match(fid):
                issues.append(self._emit(Severity.FATAL, "CHAR_001", element_id=eid, field_id=fid))
            if full and not _VALID_ID_PATTERN.match(full):
                issues.append(self._emit(Severity.FATAL, "CHAR_002", element_id=eid, field_id=fid, full_id=full))
            if fid and _CONTROL_CHARS.search(fid):
                issues.append(self._emit(Severity.FATAL, "CHAR_003", element_id=eid, field_id=fid))

        return issues
