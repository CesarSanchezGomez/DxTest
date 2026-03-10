"""Constantes centralizadas del dominio SAP SuccessFactors para DxSentinel.

Fuente única de verdad para configuraciones que antes estaban dispersas
en xml_parser, metadata_generator, csv_generator, element_processor,
field_filter y field_report_generator.
"""

import re

# ─── Orden jerárquico de elementos ───────────────────────────────────────────
# Usado por: CSVGenerator, ElementProcessor, FieldReportGenerator
ELEMENT_ORDER: list[str] = [
    "personInfo", "personalInfo", "employmentInfo", "jobInfo",
    "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
    "emergencyContactPrimary", "personRelationshipInfo",
    "compInfo", "payComponentRecurring", "payComponentNonRecurring",
    "workPermitInfo", "globalAssignmentInfo", "jobRelationsInfo",
    "imInfo", "pensionPayoutsInfo", "globalInfo", "biographicalInfoLoc",
]

# ─── Parsing: patrones de detección ──────────────────────────────────────────
LABEL_PATTERNS: dict[str, re.Pattern] = {
    "label": re.compile(r".*[Ll]abel.*"),
    "description": re.compile(r".*[Dd]esc.*"),
    "name": re.compile(r".*[Nn]ame.*"),
    "title": re.compile(r".*[Tt]itle.*"),
}

LANGUAGE_PATTERN: re.Pattern = re.compile(r"^[a-z]{2}(-[A-Za-z]{2,})?$")
HRIS_ELEMENT_PATTERN: re.Pattern = re.compile(r".*hris.*element.*", re.IGNORECASE)

# ─── Parsing: inyección de campos de fecha ───────────────────────────────────
# Elementos HRIS que necesitan campos de fecha sintéticos inyectados
# porque el XML no los incluye explícitamente.
ELEMENT_FIELD_MAPPING: dict[str, str | list[str]] = {
    "personalInfo": "start-date",
    "paymentInfo": "effectiveStartDate",
    "employmentInfo": "start-date",
    "globalInfo": "start-date",
    "homeAddress": ["start-date", "address-type"],
    "jobInfo": "start-date",
    "personRelationshipInfo": "start-date",
    "compInfo": ["start-date", "event-reason"],
    "payComponentRecurring": "start-date",
}

# Labels multilingües para los campos inyectados
_DEFAULT_DATE_LABELS: dict[str, str] = {
    "default": "Start Date",
    "en-debug": "Start Date",
    "es-mx": "Fecha del Evento",
    "en-us": "Start Date",
}

INJECTED_FIELD_LABELS: dict[str, dict[str, str]] = {
    "effectiveStartDate": {
        "default": "Effective Start Date",
        "en-debug": "Effective Start Date",
        "es-mx": "Fecha de Inicio Efectiva",
        "en-us": "Effective Start Date",
    },
    "hireDate": {
        "default": "Hire Date",
        "en-debug": "Hire Date",
        "es-mx": "Fecha de Contratación",
        "en-us": "Hire Date",
    },
    "event-reason": {
        "default": "Event Reason",
        "en-debug": "Event Reason",
        "es-mx": "Motivo del Evento",
        "en-us": "Event Reason",
    },
    "address-type": {
        "default": "Address Type",
        "en-debug": "Address Type",
        "es-mx": "Tipo de Dirección",
        "en-us": "Address Type",
    },
}


def get_injected_field_labels(field_id: str) -> dict[str, str]:
    """Retorna labels para un campo inyectado, con fallback a labels de fecha genéricos."""
    return INJECTED_FIELD_LABELS.get(field_id, _DEFAULT_DATE_LABELS.copy())


# ─── Metadata: configuración de business keys SAP ────────────────────────────
SAP_BUSINESS_KEYS: dict[str, dict] = {
    "personInfo": {
        "keys": ["userId", "personIdExternal"],
        "sap_format": ["user-id", "person-id-external"],
        "is_master": True,
        "description": "Master entity - user-id is primary key, person-id-external included",
    },
    "personalInfo": {
        "keys": ["personIdExternal", "startDate"],
        "sap_format": ["personInfo.person-id-external", "start-date"],
        "is_master": False,
        "references": "personInfo",
    },
    "globalInfo": {
        "keys": ["personIdExternal", "startDate", "country"],
        "sap_format": ["personInfo.person-id-external", "start-date", "country"],
        "is_master": False,
        "references": "personInfo",
    },
    "nationalIdCard": {
        "keys": ["personIdExternal", "country", "cardType"],
        "sap_format": ["personInfo.person-id-external", "country", "card-type"],
        "is_master": False,
        "references": "personInfo",
    },
    "homeAddress": {
        "keys": ["personIdExternal", "effectiveStartDate", "addressType"],
        "sap_format": ["personInfo.person-id-external", "start-date", "address-type"],
        "is_master": False,
        "references": "personInfo",
    },
    "phoneInfo": {
        "keys": ["personIdExternal", "phoneType"],
        "sap_format": ["personInfo.person-id-external", "phone-type"],
        "is_master": False,
        "references": "personInfo",
    },
    "emailInfo": {
        "keys": ["personIdExternal", "emailType"],
        "sap_format": ["personInfo.person-id-external", "email-type"],
        "is_master": False,
        "references": "personInfo",
    },
    "imInfo": {
        "keys": ["personIdExternal", "domain"],
        "sap_format": ["personInfo.person-id-external", "domain"],
        "is_master": False,
        "references": "personInfo",
    },
    "emergencyContactPrimary": {
        "keys": ["personIdExternal", "name", "relationship"],
        "sap_format": ["personInfo.person-id-external", "name", "relationship"],
        "is_master": False,
        "references": "personInfo",
    },
    "personRelationshipInfo": {
        "keys": ["personIdExternal", "relatedPersonIdExternal", "startDate"],
        "sap_format": ["personInfo.person-id-external", "related-person-id-external", "start-date"],
        "is_master": False,
        "references": "personInfo",
    },
    "employmentInfo": {
        "keys": ["personIdExternal", "userId"],
        "sap_format": ["person-id-external", "user-id"],
        "is_master": False,
        "references": "personInfo",
    },
    "jobInfo": {
        "keys": ["userId", "startDate", "seqNumber"],
        "sap_format": ["user-id", "start-date", "seq-number", "event-reason"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "compInfo": {
        "keys": ["userId", "startDate", "seqNumber"],
        "sap_format": ["user-id", "start-date", "seq-number", "event-reason"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "payComponentRecurring": {
        "keys": ["userId", "payComponent", "startDate", "seqNumber"],
        "sap_format": ["user-id", "pay-component", "start-date", "seq-number"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "payComponentNonRecurring": {
        "keys": ["userId", "payComponentCode", "payDate"],
        "sap_format": ["user-id", "pay-component-code", "pay-date"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "jobRelationsInfo": {
        "keys": ["userId", "relationshipType", "startDate"],
        "sap_format": ["user-id", "relationship-type", "start-date"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "workPermitInfo": {
        "keys": ["userId", "country", "documentType", "documentNumber", "issueDate"],
        "sap_format": ["user-id", "country", "document-type", "document-number", "issue-date"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "globalAssignmentInfo": {
        "keys": ["userId"],
        "sap_format": ["user-id"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "pensionPayoutsInfo": {
        "keys": ["userId"],
        "sap_format": ["user-id"],
        "is_master": False,
        "references": "employmentInfo",
    },
    "biographicalInfoLoc": {
        "keys": ["personIdExternal", "country"],
        "sap_format": ["personInfo.person-id-external", "country", "user-id"],
        "is_master": False,
        "references": "personInfo",
    },
}

# Campos que deben forzarse a tipo string aunque parezcan numéricos
STRING_OVERRIDE_FIELDS: set[str] = {
    "phone-number", "phonenumber",
    "document-number", "documentnumber",
    "national-id", "nationalid",
    "zip-code", "zipcode", "postal-code",
    "pay-component-code", "paycomponentcode",
}

# ─── Golden Record: campos excluidos ─────────────────────────────────────────
EXCLUDED_FIELD_IDS: set[str] = {
    "companyEntryDate", "departmentEntryDate", "jobEntryDate",
    "locationEntryDate", "positionEntryDate", "terminationDate",
    "timeInCompany", "timeInDepartment", "timeInJob", "end-date",
    "timeInLocation", "timeInPosition", "employmentInfo_lastDateWorked",
    "okToRehire", "regretTermination", "compa-ratio",
    "range-penetration", "date-of-death",
}

EXCLUDED_CUSTOM_RANGES: list[tuple[str, int, int]] = [
    ("custom-string", 16, 20),
    ("custom-string", 81, 100),
]
