from typing import Dict, List, Set, Optional
from ..models.validation_error import ValidationError
from ..models.error_severity import ErrorSeverity
from .messages import ContentMessages
from .validators.entity_analyzer import EntityAnalyzer
from .validators.type_validator import TypeValidator
from .validators.email_validator import EmailValidator
from .validators.length_validator import LengthValidator
from .validators.entity_completeness_validator import EntityCompletenessValidator
from .validators.required_validator import RequiredValidator
from .validators.character_validator import CharacterValidator
from .validators.duplicate_person_id_validator import DuplicatePersonIdValidator
from .validators.national_id_format_validator import NationalIdFormatValidator
from .country.mex.curp_validator import CURPValidator
from .country.mex.work_permit_validator import WorkPermitValidator


class GoldenRecordValidator:
    MULTI_VALUE_DELIMITER = "|"

    MULTI_VALUE_ENTITIES = {
        "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
        "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
        "payComponentRecurring", "payComponentNonRecurring"
    }

    def __init__(self, metadata: Dict):
        self.metadata = metadata
        self.field_catalog = metadata.get("field_catalog", {})
        self.business_keys = metadata.get("business_keys", {})

        self.entity_analyzer = EntityAnalyzer(self.field_catalog)
        self.type_validator = TypeValidator()
        self.email_validator = EmailValidator()
        self.length_validator = LengthValidator()
        self.character_validator = CharacterValidator()
        self.completeness_validator = EntityCompletenessValidator(
            self.entity_analyzer,
            self.field_catalog
        )
        self.required_validator = RequiredValidator(self.entity_analyzer)
        self.duplicate_validator = DuplicatePersonIdValidator()
        self.country_codes: List[str] = metadata.get("country_codes") or []
        self.language_code: str = metadata.get("language_code") or ""

        format_groups = metadata.get("format_groups", {})
        self.national_id_validator = NationalIdFormatValidator(format_groups, self.country_codes)
        self.curp_validator = CURPValidator(self.country_codes, self.language_code)
        self.work_permit_validator = WorkPermitValidator(self.country_codes)

        self.empty_entities_global: Set[str] = set()

    def validate(self, csv_data: List[Dict], headers: List[str]) -> List[ValidationError]:
        errors = []

        if not csv_data or len(csv_data) == 0:
            errors.append(ValidationError(
                code="NO_DATA_ROWS",
                message=ContentMessages.no_data_rows(),
                severity=ErrorSeverity.ERROR
            ))
            return errors

        non_empty_rows = []
        for row in csv_data:
            if any(value and str(value).strip() for value in row.values()):
                non_empty_rows.append(row)

        if not non_empty_rows:
            errors.append(ValidationError(
                code="NO_DATA_ROWS",
                message=ContentMessages.no_data_rows(),
                severity=ErrorSeverity.ERROR
            ))
            return errors

        self._analyze_empty_entities(non_empty_rows)

        duplicate_errors = self.duplicate_validator.validate(non_empty_rows, headers)
        errors.extend(duplicate_errors)

        for row_idx, row in enumerate(non_empty_rows):
            row_errors = self._validate_row(row, row_idx, headers)
            errors.extend(row_errors)

        return errors

    def _analyze_empty_entities(self, csv_data: List[Dict]):
        entity_fields = self.entity_analyzer.get_entity_fields()

        for entity_id in entity_fields.keys():
            if self.entity_analyzer.is_entity_empty_globally(csv_data, entity_id):
                self.empty_entities_global.add(entity_id)

    def _validate_row(self, row: Dict, row_idx: int, headers: List[str]) -> List[ValidationError]:
        errors = []
        person_id = self._extract_person_id(row)

        context = {
            'row_index': row_idx + 3,
            'person_id': person_id,
            'empty_entities_global': self.empty_entities_global
        }

        entity_validation, validated_required = self.completeness_validator.validate(row, context)
        errors.extend(entity_validation)

        for header in headers:
            value = row.get(header)
            field_meta = self.field_catalog.get(header, {})

            if not field_meta:
                continue

            entity_id = field_meta.get("element", "")
            field_id = field_meta.get("field", "")
            data_type = field_meta.get("data_type", "string")
            is_required = field_meta.get("required", False)
            max_length = field_meta.get("max_length")
            is_multi_value = entity_id in self.MULTI_VALUE_ENTITIES

            if entity_id in self.empty_entities_global:
                continue

            if self.entity_analyzer.is_entity_empty_for_row(row, entity_id):
                continue

            field_context = {
                'row_index': row_idx + 3,
                'column_name': header,
                'entity_id': entity_id,
                'field_id': field_id,
                'person_id': person_id,
                'expected_type': data_type,
                'max_length': max_length,
                'country_codes': self.country_codes,
            }

            if is_required and header not in validated_required:
                err = self.required_validator.validate(value, field_context)
                if err:
                    errors.append(err)
                    continue

            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue

            if EmailValidator.is_email_field(header):
                email_errors = self._validate_email_field(
                    value, field_context, is_multi_value
                )
                errors.extend(email_errors)

            values = self._split_multi_value(str(value)) if is_multi_value else [str(value)]

            curp_validated_for_field = False

            for single_value in values:
                single_value = single_value.strip()
                if not single_value:
                    continue

                char_context = {
                    'column_name': header,
                    'entity_id': entity_id,
                    'field_id': field_id,
                    'row_index': row_idx + 3,
                    'person_id': person_id
                }
                char_errors = self.character_validator.validate(single_value, char_context)
                errors.extend(char_errors)

                type_errors = self.type_validator.validate(single_value, field_context)
                errors.extend(type_errors)

                if (entity_id == NationalIdFormatValidator.TARGET_ENTITY_ID
                        and field_id == NationalIdFormatValidator.TARGET_FIELD_ID
                        and self.national_id_validator.has_rules()):
                    nat_id_errors = self.national_id_validator.validate(single_value, field_context)
                    errors.extend(nat_id_errors)

                    if (not nat_id_errors
                            and self.curp_validator.is_active()
                            and not curp_validated_for_field):
                        curp_errors = self.curp_validator.validate_row(
                            single_value, row, field_context
                        )
                        errors.extend(curp_errors)
                        curp_validated_for_field = True

                if max_length:
                    length_errors = self.length_validator.validate(single_value, field_context)
                    errors.extend(length_errors)

        # Validación de workPermitInfo (RFC/NSS): opera sobre la fila completa
        if (self.work_permit_validator.is_active()
                and WorkPermitValidator.TARGET_ENTITY not in self.empty_entities_global
                and not self.entity_analyzer.is_entity_empty_for_row(
                    row, WorkPermitValidator.TARGET_ENTITY
                )):
            work_permit_errors = self.work_permit_validator.validate_row(row, context)
            errors.extend(work_permit_errors)

        return errors

    def _validate_email_field(
            self, value: str, context: dict, is_multi_value: bool
    ) -> List[ValidationError]:
        errors = []
        values = self._split_multi_value(value) if is_multi_value else [value]

        for email in values:
            email = email.strip()
            if not email:
                continue

            email_errors = self.email_validator.validate(email, context)
            errors.extend(email_errors)

        return errors

    def _split_multi_value(self, value: str) -> List[str]:
        if self.MULTI_VALUE_DELIMITER in value:
            return [v.strip() for v in value.split(self.MULTI_VALUE_DELIMITER)]
        return [value]

    def _extract_person_id(self, row: Dict) -> Optional[str]:
        for key in ["personInfo_person-id-external", "personalInfo_person-id-external"]:
            if key in row and row[key]:
                val = str(row[key]).strip()
                if self.MULTI_VALUE_DELIMITER in val:
                    val = val.split(self.MULTI_VALUE_DELIMITER)[0].strip()
                return val
        return None
