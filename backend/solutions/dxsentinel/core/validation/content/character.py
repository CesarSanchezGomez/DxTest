"""Validacion de caracteres invalidos en datos CSV → ERROR."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

# Caracteres completamente invalidos
_INVALID_CHARS = frozenset({
    "\ufffd",  # Replacement character - indica encoding corrupto
    "\x00",    # NULL byte
})

# Caracteres sospechosos (tipicamente Windows-1252 mal interpretado)
_SUSPICIOUS_CHARS = frozenset({
    "\x80", "\x81", "\x82", "\x83", "\x84", "\x85", "\x86", "\x87",
    "\x88", "\x89", "\x8a", "\x8b", "\x8c", "\x8d", "\x8e", "\x8f",
    "\x90", "\x91", "\x92", "\x93", "\x94", "\x95", "\x96", "\x97",
    "\x98", "\x99", "\x9a", "\x9b", "\x9c", "\x9d", "\x9e", "\x9f",
})

_MULTI_VALUE_ENTITIES = {
    "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
    "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
    "payComponentRecurring", "payComponentNonRecurring",
}


def _detect_problematic_chars(text: str) -> tuple[set, set]:
    invalid = set()
    suspicious = set()
    for char in text:
        if char in _INVALID_CHARS:
            invalid.add(char)
        elif char in _SUSPICIOUS_CHARS:
            suspicious.add(char)
    return invalid, suspicious


def _format_char_repr(chars: set) -> str:
    return ", ".join(repr(c) for c in sorted(chars))


@register_validator
class ContentCharacterValidator(BaseValidator):
    """Detecta caracteres invalidos o sospechosos en datos del CSV."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            for col in ctx.csv_headers:
                value = row.get(col)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    continue

                meta = ctx.field_catalog.get(col, {})
                entity_id = meta.get("element", "")
                field_id = meta.get("field", "")
                is_multi = entity_id in _MULTI_VALUE_ENTITIES

                values = [v.strip() for v in str(value).split("|")] if is_multi else [str(value).strip()]

                for single_value in values:
                    if not single_value:
                        continue

                    invalid_chars, suspicious_chars = _detect_problematic_chars(single_value)
                    preview = single_value[:30] + "..." if len(single_value) > 30 else single_value

                    if invalid_chars:
                        issues.append(self._emit(
                            Severity.ERROR,
                            "INVALID_CHARACTERS",
                            element_id=entity_id,
                            field_id=field_id,
                            row_index=row_index,
                            column_name=col,
                            value=preview,
                            chars=_format_char_repr(invalid_chars),
                        ))
                    elif suspicious_chars:
                        issues.append(self._emit(
                            Severity.ERROR,
                            "SUSPICIOUS_ENCODING",
                            element_id=entity_id,
                            field_id=field_id,
                            row_index=row_index,
                            column_name=col,
                            value=preview,
                            chars=_format_char_repr(suspicious_chars),
                        ))

        return issues
