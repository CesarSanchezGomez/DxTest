"""Validaciones de labels → WARNING."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from .base import BaseValidator, ValidationContext


@register_validator
class LabelValidator(BaseValidator):
    """Verifica calidad de labels multilingues.

    Los fallos aqui son WARNING: el proceso continua normalmente.
    """

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        self._check_missing_labels(ctx.columns, ctx.language_code, issues)
        self._check_duplicate_labels(ctx.columns, ctx.language_code, issues)

        return issues

    def _check_missing_labels(
        self, columns: list[dict], language_code: str, issues: list[ValidationResult],
    ) -> None:
        lang_normalized = language_code.lower().replace("_", "-")

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

            # Verificar idioma solicitado (o base)
            has_lang = False
            base_lang = lang_normalized.split("-")[0]
            for lang_key in labels:
                lk = lang_key.lower().replace("_", "-")
                if lk == lang_normalized or lk.startswith(base_lang):
                    has_lang = True
                    break

            if not has_lang and "default" not in labels:
                issues.append(ValidationResult(
                    severity=Severity.WARNING,
                    code="LABEL_002",
                    message=f"Sin label para idioma '{language_code}': {full_id}",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))

            # Labels vacios
            for lang_key, label_text in labels.items():
                if isinstance(label_text, str) and not label_text.strip():
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="LABEL_003",
                        message=f"Label vacio para idioma '{lang_key}': {full_id}",
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))

    def _check_duplicate_labels(
        self, columns: list[dict], language_code: str, issues: list[ValidationResult],
    ) -> None:
        # Agrupar por elemento
        by_element: dict[str, list[tuple[str, str]]] = {}
        lang_normalized = language_code.lower().replace("_", "-")
        base_lang = lang_normalized.split("-")[0]

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
                        code="LABEL_004",
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
