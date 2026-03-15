import re
from typing import Dict, List, Optional

from ....models.error_severity import ErrorSeverity
from ....models.validation_error import ValidationError
from ...messages import ContentMessages


class WorkPermitValidator:
    """
    Valida workPermitInfo_document-type y workPermitInfo_document-number.
    Activo solo cuando MEX está en country_codes del metadata.
    """

    TARGET_COUNTRY = "MEX"
    TARGET_ENTITY = "workPermitInfo"

    KEYWORD_RFC = "FEDERAL TAXPAYER REGISTRATION"
    KEYWORD_RFC_ES = "REGISTRO FEDERAL DE CONTRIBUYENTES"
    KEYWORD_IMSS = "IMSS"

    RFC_FISICA_RE = re.compile(r"^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$")
    RFC_MORAL_RE = re.compile(r"^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$")
    NSS_RE = re.compile(r"^\d{11}$")

    def __init__(self, country_codes: List[str]):
        self.active = self.TARGET_COUNTRY in [c.upper() for c in (country_codes or [])]

    def is_active(self) -> bool:
        return self.active

    def validate_row(self, row: Dict, context: Dict) -> List[ValidationError]:
        errors: List[ValidationError] = []

        doc_types_raw = self._get_field(row, "document-type")
        doc_numbers_raw = self._get_field(row, "document-number")

        types_empty = not doc_types_raw
        numbers_empty = not doc_numbers_raw

        if types_empty and numbers_empty:
            return errors

        if types_empty or numbers_empty:
            errors.append(self._err(
                "WORK_PERMIT_INCOMPLETE",
                ContentMessages.work_permit_incomplete(),
                context,
            ))
            return errors

        types = [t.strip() for t in str(doc_types_raw).split("|")]
        numbers = [n.strip() for n in str(doc_numbers_raw).split("|")]

        if len(types) != len(numbers):
            errors.append(self._err(
                "WORK_PERMIT_COUNT_MISMATCH",
                ContentMessages.work_permit_count_mismatch(len(types), len(numbers)),
                context,
            ))
            return errors

        for i, (doc_type, doc_number) in enumerate(zip(types, numbers)):
            position = i + 1
            doc_type_upper = doc_type.upper()

            if self.KEYWORD_RFC in doc_type_upper or self.KEYWORD_RFC_ES in doc_type_upper:
                if not (
                    self.RFC_FISICA_RE.match(doc_number)
                    or self.RFC_MORAL_RE.match(doc_number)
                ):
                    errors.append(self._err(
                        "WORK_PERMIT_RFC_INVALID",
                        ContentMessages.work_permit_rfc_invalid(position),
                        context,
                        field_id="document-number",
                        value=doc_number,
                    ))

            elif self.KEYWORD_IMSS in doc_type_upper:
                if not self.NSS_RE.match(doc_number):
                    errors.append(self._err(
                        "WORK_PERMIT_NSS_INVALID",
                        ContentMessages.work_permit_nss_invalid(position),
                        context,
                        field_id="document-number",
                        value=doc_number,
                    ))

            else:
                errors.append(self._err(
                    "WORK_PERMIT_UNKNOWN_TYPE",
                    ContentMessages.work_permit_unknown_type(position, doc_type),
                    context,
                    field_id="document-type",
                    value=doc_type,
                ))

        return errors

    def _get_field(self, row: Dict, field_id: str) -> Optional[str]:
        suffix = f"_{field_id}"
        for key, value in row.items():
            if self.TARGET_ENTITY in key and key.endswith(suffix):
                if value is None:
                    return None
                val_str = str(value).strip()
                return val_str or None
        return None

    def _err(
        self,
        code: str,
        message: str,
        context: Dict,
        field_id: str = "document-type",
        value: Optional[str] = None,
    ) -> ValidationError:
        return ValidationError(
            code=code,
            message=message,
            severity=ErrorSeverity.ERROR,
            row_index=context.get("row_index"),
            column_name=None,
            entity_id=self.TARGET_ENTITY,
            field_id=field_id,
            person_id=context.get("person_id"),
            value=value[:50] if value else None,
        )
