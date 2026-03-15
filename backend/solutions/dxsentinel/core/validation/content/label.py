"""Validacion de labels multilingues → WARNING."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}(-[A-Za-z]{2,})?$")
_ENCODING_ISSUES = re.compile(r"[\ufffd\ufffe\ufeff]")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@register_validator
class LabelValidator(BaseValidator):
    """Verifica calidad de labels multilingues (WARNING)."""

    modes = ("generation",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []
        lang = ctx.language_code.lower().replace("_", "-")
        base = lang.split("-")[0]

        for col in ctx.columns:
            node = col.get("node", {})
            labels = node.get("labels", {}) if isinstance(node, dict) else {}
            full_id = col.get("full_id", "")
            eid = col.get("element_id", "")
            fid = col.get("field_id", "")

            if not labels:
                issues.append(self._emit(Severity.WARNING, "LABEL_001", element_id=eid, field_id=fid, full_id=full_id))
                continue

            # Idioma faltante
            has_lang = any(
                lk.lower().replace("_", "-") == lang or lk.lower().replace("_", "-").startswith(base)
                for lk in labels
            )
            if not has_lang and "default" not in labels:
                issues.append(self._emit(
                    Severity.WARNING, "LABEL_002",
                    element_id=eid, field_id=fid,
                    full_id=full_id, language=ctx.language_code,
                ))

            # Calidad de labels
            for lk, text in labels.items():
                if not isinstance(text, str):
                    continue
                if not text.strip():
                    issues.append(self._emit(
                        Severity.WARNING, "LABEL_003",
                        element_id=eid, field_id=fid, full_id=full_id, lang_key=lk,
                    ))
                if _CONTROL_CHARS.search(text):
                    issues.append(self._emit(
                        Severity.WARNING, "LABEL_004",
                        element_id=eid, field_id=fid, lang_key=lk, preview=text[:50],
                    ))
                if _ENCODING_ISSUES.search(text):
                    issues.append(self._emit(
                        Severity.WARNING, "LABEL_005",
                        element_id=eid, field_id=fid, lang_key=lk, preview=text[:50],
                    ))

        # Labels duplicados por elemento
        self._check_duplicates(ctx.columns, lang, base, issues)
        # Language codes invalidos
        self._check_lang_codes(ctx.parsed_model, issues)

        return issues

    def _check_duplicates(self, columns: list[dict], lang: str, base: str, issues: list) -> None:
        by_element: dict[str, list[tuple[str, str]]] = {}
        for col in columns:
            eid = col.get("element_id", "")
            labels = (col.get("node") or {}).get("labels", {})
            label = None
            for lk, text in labels.items():
                lk_n = lk.lower().replace("_", "-")
                if lk_n == lang or lk_n.startswith(base):
                    label = text
                    break
            if label is None:
                label = labels.get("default", "")
            if label:
                by_element.setdefault(eid, []).append((col.get("full_id", ""), label))

        for eid, pairs in by_element.items():
            seen: dict[str, str] = {}
            for full_id, label in pairs:
                key = label.strip().lower()
                if key in seen:
                    issues.append(self._emit(
                        Severity.WARNING, "LABEL_006",
                        element_id=eid, field_id=full_id,
                        label=label, first=seen[key], second=full_id,
                    ))
                else:
                    seen[key] = full_id

    def _check_lang_codes(self, parsed_model: dict, issues: list) -> None:
        structure = parsed_model.get("structure", {})
        if not structure:
            return
        invalid: set[str] = set()
        self._collect_invalid(structure, invalid)
        for lang in sorted(invalid):
            issues.append(self._emit(Severity.WARNING, "LABEL_007", lang=lang))

    def _collect_invalid(self, node: dict, invalid: set) -> None:
        for lk in node.get("labels", {}):
            if lk != "default" and not _LANGUAGE_PATTERN.match(lk):
                invalid.add(lk)
        for child in node.get("children", []):
            self._collect_invalid(child, invalid)
