"""Validacion de labels multilingues → WARNING.

Integra la logica de validacion de idiomas que existia en
xml_parser.py (_extract_labels, LANGUAGE_PATTERN) y la extiende
con verificaciones de calidad (duplicados, encoding).
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

# Patron de idiomas validos (del xml_parser.py original)
_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}(-[A-Za-z]{2,})?$")

# Caracteres de encoding problematicos
_ENCODING_ISSUES = re.compile(r"[\ufffd\ufffe\ufeff]")

# Caracteres de control (excepto tab/newline/carriage return)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@register_validator
class LabelValidator(BaseValidator):
    """Verifica calidad de labels multilingues → WARNING."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        self._check_missing_labels(ctx.columns, ctx.language_code, issues)
        self._check_label_quality(ctx.columns, issues)
        self._check_duplicate_labels(ctx.columns, ctx.language_code, issues)
        self._check_language_codes(ctx.parsed_model, issues)

        return issues

    def _check_missing_labels(
        self, columns: list[dict], language_code: str, issues: list[ValidationResult],
    ) -> None:
        lang_normalized = language_code.lower().replace("_", "-")
        base_lang = lang_normalized.split("-")[0]

        for col in columns:
            node = col.get("node", {})
            labels = node.get("labels", {}) if isinstance(node, dict) else {}
            full_id = col.get("full_id", "")
            element_id = col.get("element_id", "")
            field_id = col.get("field_id", "")

            if not labels:
                issues.append(ValidationResult(
                    severity=Severity.WARNING,
                    code="LABEL_001",
                    message=f"Campo sin labels: {full_id}",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))
                continue

            has_lang = any(
                lk.lower().replace("_", "-") == lang_normalized
                or lk.lower().replace("_", "-").startswith(base_lang)
                for lk in labels
            )

            if not has_lang and "default" not in labels:
                issues.append(ValidationResult(
                    severity=Severity.WARNING,
                    code="LABEL_002",
                    message=f"Sin label para idioma '{language_code}': {full_id}",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))

    def _check_label_quality(self, columns: list[dict], issues: list[ValidationResult]) -> None:
        for col in columns:
            node = col.get("node", {})
            labels = node.get("labels", {}) if isinstance(node, dict) else {}
            element_id = col.get("element_id", "")
            field_id = col.get("field_id", "")

            for lang_key, label_text in labels.items():
                if not isinstance(label_text, str):
                    continue

                if not label_text.strip():
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="LABEL_003",
                        message=f"Label vacio para idioma '{lang_key}': {col.get('full_id', '')}",
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))

                if _CONTROL_CHARS.search(label_text):
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="LABEL_004",
                        message=f"Caracteres de control en label ({lang_key}): '{label_text[:50]}'",
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))

                if _ENCODING_ISSUES.search(label_text):
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="LABEL_005",
                        message=f"Problemas de encoding en label ({lang_key}): '{label_text[:50]}'",
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))

    def _check_duplicate_labels(
        self, columns: list[dict], language_code: str, issues: list[ValidationResult],
    ) -> None:
        lang_normalized = language_code.lower().replace("_", "-")
        base_lang = lang_normalized.split("-")[0]

        by_element: dict[str, list[tuple[str, str]]] = {}

        for col in columns:
            element_id = col.get("element_id", "")
            node = col.get("node", {})
            labels = node.get("labels", {}) if isinstance(node, dict) else {}

            label = None
            for lang_key, text in labels.items():
                lk = lang_key.lower().replace("_", "-")
                if lk == lang_normalized or lk.startswith(base_lang):
                    label = text
                    break
            if label is None:
                label = labels.get("default", "")

            if label:
                by_element.setdefault(element_id, []).append((col.get("full_id", ""), label))

        for element_id, field_labels in by_element.items():
            seen: dict[str, str] = {}
            for full_id, label in field_labels:
                label_lower = label.strip().lower()
                if label_lower in seen:
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="LABEL_006",
                        message=(
                            f"Label duplicado '{label}' en '{element_id}': "
                            f"campos {seen[label_lower]} y {full_id}"
                        ),
                        element_id=element_id,
                        field_id=full_id,
                        validator=self.name,
                    ))
                else:
                    seen[label_lower] = full_id

    def _check_language_codes(self, parsed_model: dict, issues: list[ValidationResult]) -> None:
        """Verifica que los language codes del XML cumplan el patron valido."""
        structure = parsed_model.get("structure", {})
        if not structure:
            return

        invalid_langs = set()
        self._collect_invalid_langs(structure, invalid_langs)

        for lang in sorted(invalid_langs):
            issues.append(ValidationResult(
                severity=Severity.WARNING,
                code="LABEL_007",
                message=f"Language code invalido en XML: '{lang}' (esperado: xx o xx-XX)",
                validator=self.name,
            ))

    def _collect_invalid_langs(self, node: dict, invalid: set) -> None:
        for lang_key in node.get("labels", {}):
            if lang_key != "default" and not _LANGUAGE_PATTERN.match(lang_key):
                invalid.add(lang_key)
        for child in node.get("children", []):
            self._collect_invalid_langs(child, invalid)
