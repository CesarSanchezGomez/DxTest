from typing import List, Optional


class ContentMessages:

    @staticmethod
    def incomplete_entity(entity: str, field: str, filled: List[str], missing: List[str]) -> str:
        filled_display = ', '.join(filled[:3])
        if len(filled) > 3:
            filled_display += f' (+{len(filled) - 3})'

        missing_display = ', '.join(missing)

        return f"Con datos: {filled_display}. Faltantes: {missing_display}"

    @staticmethod
    def required_field_empty(field: str) -> str:
        return "Campo obligatorio vacío"

    @staticmethod
    def invalid_email(email: str, field: str) -> str:
        return f"Formato inválido. Esperado: usuario@dominio.com"

    @staticmethod
    def invalid_date(
        value: str,
        field: str,
        expected_label: Optional[str] = None,
        country_codes: Optional[List[str]] = None,
    ) -> str:
        if expected_label and country_codes:
            countries = ', '.join(c.upper() for c in country_codes)
            return f"Formato inválido. Esperado: {expected_label} ({countries})"
        return "Formato inválido. Esperados: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY"

    @staticmethod
    def invalid_integer(value: str, field: str) -> str:
        return "Debe ser número entero (sin decimales)"

    @staticmethod
    def invalid_decimal(value: str, field: str) -> str:
        return "Debe ser número (puede tener decimales con punto)"

    @staticmethod
    def invalid_boolean(value: str, field: str) -> str:
        return "Valores aceptados: Yes, No, True, False, 1, 0"

    @staticmethod
    def max_length_exceeded(value: str, field: str, max_length: int, actual_length: int) -> str:
        return f"Longitud: {actual_length} caracteres. Máximo: {max_length}"

    @staticmethod
    def invalid_characters_in_data(chars: str, value_preview: str) -> str:
        return f"Caracteres inválidos {chars} en: '{value_preview}'. Problema de encoding"

    @staticmethod
    def suspicious_encoding_in_data(chars: str, value_preview: str) -> str:
        return f"Caracteres sospechosos {chars} en: '{value_preview}'. Posible problema de encoding"

    @staticmethod
    def no_data_rows() -> str:
        return "CSV sin datos. Headers y labels correctos pero no hay filas de datos para procesar"

    @staticmethod
    def duplicate_person_id(person_id: str, row_indices: list) -> str:
        rows_display = ', '.join(str(r) for r in row_indices)
        return f"ID duplicado '{person_id}'. Aparece en las filas: {rows_display}"

    # ── CURP ──────────────────────────────────────────────────────────

    @staticmethod
    def curp_empty_field(field_name: str) -> str:
        return f"Campo '{field_name}' está vacío"

    @staticmethod
    def curp_not_uppercase() -> str:
        return "La CURP no está en mayúsculas"

    @staticmethod
    def curp_invalid_length(actual: int, expected: int) -> str:
        return f"La CURP debe tener {expected} caracteres. Tiene: {actual}"

    @staticmethod
    def curp_invalid_date_format() -> str:
        return "Fecha de nacimiento no es válida (dd/mm/aaaa)"

    @staticmethod
    def curp_field_mismatch(field_name: str) -> str:
        return f"La {field_name} no coincide con la CURP"

    @staticmethod
    def curp_gender_mismatch(valid_values: list) -> str:
        values_str = ", ".join(valid_values)
        return (
            f"Género no coincide con CURP. "
            f"SAP usa valores system-defined: {values_str} (M=Male→H, F=Female→M en CURP)"
        )

    @staticmethod
    def curp_gender_invalid_value(valid_values: list) -> str:
        values_str = ", ".join(valid_values)
        return (
            f"El valor del género no es válido. "
            f"SAP usa valores system-defined: {values_str} (Male/Female). "
            f"No configurar como picklist."
        )

    @staticmethod
    def curp_state_foreign_not_ne(country_of_birth: str, state_in_curp: str) -> str:
        return (
            f"El empleado nació en el extranjero ({country_of_birth}) "
            f"pero la CURP tiene código de estado '{state_in_curp}'. "
            "Debe ser 'NE' (Nacido en el Extranjero)"
        )

    @staticmethod
    def curp_state_mexico_is_ne() -> str:
        return (
            "El empleado nació en México (country-of-birth = MEX) "
            "pero la CURP indica nacido en el extranjero (NE). "
            "Debe corresponder a un estado de la República Mexicana"
        )

    @staticmethod
    def curp_state_not_in_picklist(region: str) -> str:
        return (
            f"Inconsistencia en estado de nacimiento: el valor registrado '{region}' "
            "no corresponde a ninguna opción de la picklist oficial 'state_mex'. "
        )

    @staticmethod
    def curp_state_picklist_foreign_mismatch(country_of_birth: str, curp_state: str) -> str:
        return (
            f"Inconsistencia detectada: el país de nacimiento registrado ({country_of_birth}) "
            f"indica origen extranjero, pero la CURP contiene el código '{curp_state}' en lugar de 'NE'. "
        )

    # ── workPermitInfo ────────────────────────────────────────────────

    @staticmethod
    def work_permit_incomplete() -> str:
        return "workPermitInfo incompleto: falta tipo o número de documento"

    @staticmethod
    def work_permit_count_mismatch(types_count: int, numbers_count: int) -> str:
        return (
            f"La cantidad de tipos ({types_count}) y números ({numbers_count}) "
            "de documento no coincide"
        )

    @staticmethod
    def work_permit_rfc_invalid(position: int) -> str:
        return (
            f"RFC en posición {position} no tiene formato válido. "
            "Esperado: persona física AAAA######AAA (13 chars) o "
            "persona moral AAA######AAA (12 chars)"
        )

    @staticmethod
    def work_permit_nss_invalid(position: int) -> str:
        return f"NSS en posición {position} no tiene formato válido. Esperado: 11 dígitos numéricos"

    @staticmethod
    def work_permit_unknown_type(position: int, doc_type: str) -> str:
        return f"Tipo de documento desconocido en posición {position}: '{doc_type}'"

    # ── National ID ───────────────────────────────────────────────────

    @staticmethod
    def invalid_national_id_format(
        value: str,
        country_codes: List[str],
        expected_formats: List[str],
    ) -> str:
        countries = ", ".join(c.upper() for c in country_codes)
        if expected_formats:
            formats_str = " | ".join(expected_formats)
            return f"ID nacional inválido para {countries}. Formato esperado: {formats_str}"
        return f"ID nacional inválido para {countries}"
