"""Constantes centralizadas del dominio SAP SuccessFactors para DxSentinel.

Fuente única de verdad para configuraciones de entidades, tipos de dato,
business keys, y campos inyectables. Reemplaza las constantes que antes
estaban dispersas en xml_parser, metadata_generator, csv_generator,
element_processor, field_filter y field_report_generator.
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

# ─── Labels multilingües para campos inyectados ──────────────────────────────
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
    return INJECTED_FIELD_LABELS.get(field_id, _DEFAULT_DATE_LABELS.copy())


# ─── Configuración de entidades SAP SuccessFactors ──────────────────────────
#
# Estructura por entidad:
#   business_keys  — nombres de campo SAP API
#   template       — nombres XML/golden record para las business keys
#   is_master      — True si es entidad raíz (default False)
#   references     — entidad padre (None si es master)
#   inject_override — campos a inyectar si la derivación automática no aplica
#   field_types    — dict agrupado por tipo SAP (solo tipos NO-STRING)
#   ranges         — (prefijo, inicio, fin, tipo) para campos numerados
#   alt_type_overrides — excepciones de tipo para variantes -alt1/-alt2
#
# Convención: solo se listan campos cuyo tipo NO es STRING.
# Cualquier campo conocido de la entidad que no aparezca aquí es STRING.
# Para entidades desconocidas, get_field_type() retorna None.

SAP_ENTITY_CONFIGS: dict[str, dict] = {
    # ── personInfo (master) ──────────────────────────────────────────────────
    "personInfo": {
        "business_keys": ["userId", "personIdExternal"],
        "template": ["user-id", "person-id-external"],
        "is_master": True,
        "references": None,
        "description": "Master entity - user-id is primary key",
        "field_types": {
            "DATE": ["date-of-birth", "date-of-death"],
            "LONG": ["attachment-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── personalInfo ─────────────────────────────────────────────────────────
    "personalInfo": {
        "business_keys": ["personIdExternal", "startDate"],
        "template": ["personInfo.person-id-external", "start-date"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": [
                "aboriginal-person", "challenge-status", "disabled-veteran",
                "medal-veteran", "protected-veteran", "separated-veteran",
                "veteran", "visible-minority",
            ],
            "DATE": [
                "certificate-start-date", "certificate-end-date",
                "date-of-birth", "date-of-death", "dateOfFirstEntryInFrance",
                "end-date", "expected-retirement-date", "since",
            ],
            "LONG": ["attachment-id"],
            "PICKLIST": ["marital-status", "name-prefix", "partner-name-prefix"],
        },
        "ranges": [
            ("custom-string", 1, 30, "STRING"),
            ("custom-date", 1, 20, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── employmentInfo ───────────────────────────────────────────────────────
    "employmentInfo": {
        "business_keys": ["personIdExternal", "userId"],
        "template": ["person-id-external", "user-id"],
        "references": "personInfo",
        "inject_override": ["start-date"],
        "field_types": {
            "BOOLEAN": [
                "eligibleForStock", "employeeFirstEmployment",
                "isContingentWorker", "isPrimary",
            ],
            "DATE": [
                "benefits-eligibility-start-date", "companyExitDate",
                "originalStartDate", "primaryEmploymentDate",
                "professionalServiceDate", "seniorityDate",
                "serviceDate", "start-date",
            ],
            "LONG": ["initialOptionGrant", "initialStockGrant"],
        },
        "ranges": [
            ("custom-string", 1, 15, "STRING"),
            ("custom-string", 21, 80, "STRING"),
            ("custom-date", 1, 5, "DATE"),
            ("custom-date", 21, 30, "DATE"),
            ("custom-date", 41, 65, "DATE"),
            ("custom-long", 1, 10, "LONG"),
            ("custom-double", 1, 10, "DOUBLE"),
        ],
    },
    # ── jobInfo ──────────────────────────────────────────────────────────────
    "jobInfo": {
        "business_keys": ["userId", "startDate", "seqNumber"],
        "template": ["user-id", "start-date", "seq-number", "event-reason"],
        "references": "employmentInfo",
        "inject_override": ["start-date"],
        "field_types": {
            "BOOLEAN": [
                "is-competition-clause-active", "is-cross-border-worker",
                "is-eligible-for-benefit", "is-eligible-for-car",
                "is-eligible-for-financial-plan", "is-fulltime-employee",
                "is-home-worker", "is-shift-employee",
                "is-side-line-job-allowed", "is-volunteer",
                "triggerMatrixRelationSync",
            ],
            "DATE": [
                "contract-end-date", "expected-return-date", "hireDate",
                "probation-period-end-date", "companyEntryDate",
                "locationEntryDate", "departmentEntryDate",
                "jobEntryDate", "positionEntryDate",
                "payScaleLevelEntryDate",
            ],
            "LONG": [
                "attachment-id", "event-reason", "job-request-number",
                "position", "seq-number",
            ],
            "DOUBLE": [
                "fte", "pm-form", "shift-factor", "shift-rate",
                "standard-hours",
            ],
        },
        "ranges": [
            ("custom-string", 1, 160, "STRING"),
            ("custom-date", 1, 50, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── homeAddress ──────────────────────────────────────────────────────────
    "homeAddress": {
        "business_keys": ["personIdExternal", "effectiveStartDate", "addressType"],
        "template": ["personInfo.person-id-external", "start-date", "address-type"],
        "references": "personInfo",
        "field_types": {
            "DATE": ["end-date"],
            "LONG": ["attachment-id", "item-id"],
        },
        "ranges": [
            ("address", 1, 25, "STRING"),
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-double", 1, 20, "DOUBLE"),
            ("custom-long", 1, 20, "LONG"),
        ],
        "alt_type_overrides": {
            "custom-long-alt2": "DOUBLE",
        },
    },
    # ── phoneInfo ────────────────────────────────────────────────────────────
    "phoneInfo": {
        "business_keys": ["personIdExternal", "phoneType"],
        "template": ["personInfo.person-id-external", "phone-type"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": ["isPrimary"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── emailInfo ────────────────────────────────────────────────────────────
    "emailInfo": {
        "business_keys": ["personIdExternal", "emailType"],
        "template": ["personInfo.person-id-external", "email-type"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": ["isPrimary"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── nationalIdCard ───────────────────────────────────────────────────────
    "nationalIdCard": {
        "business_keys": ["personIdExternal", "country", "cardType"],
        "template": ["personInfo.person-id-external", "country", "card-type"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": ["isPrimary", "isTemporary"],
            "DATE": ["start-date", "end-date"],
            "LONG": ["attachment-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── emergencyContactPrimary ──────────────────────────────────────────────
    "emergencyContactPrimary": {
        "business_keys": ["personIdExternal", "name", "relationship"],
        "template": ["personInfo.person-id-external", "name", "relationship"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": [
                "isAddSameAsEmployee", "isDependent", "isDisabled",
                "isEmergencyContact", "isStudent",
            ],
            "DATE": ["dateOfBirth"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── personRelationshipInfo ───────────────────────────────────────────────
    "personRelationshipInfo": {
        "business_keys": ["personIdExternal", "relatedPersonIdExternal", "startDate"],
        "template": ["personInfo.person-id-external", "related-person-id-external", "start-date"],
        "references": "personInfo",
        "field_types": {
            "BOOLEAN": [
                "is-accompanying-dependent", "is-address-same-as-person",
                "is-beneficiary",
            ],
            "LONG": ["item-id", "attachment-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 20, "DATE"),
            ("custom-long", 1, 20, "LONG"),
        ],
    },
    # ── compInfo ─────────────────────────────────────────────────────────────
    "compInfo": {
        "business_keys": ["userId", "startDate", "seqNumber"],
        "template": ["user-id", "start-date", "seq-number", "event-reason"],
        "references": "employmentInfo",
        "field_types": {
            "BOOLEAN": [
                "is-eligible-for-benefits", "is-eligible-for-car",
                "is-eligible-for-leave-loading",
                "is-highly-compensated-employee", "is-insider",
            ],
            "DOUBLE": [
                "benefits-rate", "compa-ratio", "pensionable-salary",
                "proration-factor", "range-penetration",
            ],
            "LONG": ["attachment-id", "compensation-structure", "seq-number"],
        },
        "ranges": [
            ("custom-string", 1, 100, "STRING"),
            ("custom-date", 1, 30, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── payComponentRecurring ────────────────────────────────────────────────
    "payComponentRecurring": {
        "business_keys": ["userId", "payComponent", "startDate", "seqNumber"],
        "template": ["user-id", "pay-component", "start-date", "seq-number"],
        "references": "employmentInfo",
        "field_types": {
            "DATE": ["no-changes-until-date"],
            "DOUBLE": ["calculated-amount", "number-of-units", "paycompvalue"],
            "LONG": ["attachment-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── payComponentNonRecurring ─────────────────────────────────────────────
    "payComponentNonRecurring": {
        "business_keys": ["userId", "payComponentCode", "payDate"],
        "template": ["user-id", "pay-component-code", "pay-date"],
        "references": "employmentInfo",
        "field_types": {
            "DATE": [
                "non-recurring-pay-period-end-date",
                "non-recurring-pay-period-start-date",
                "pay-date", "sent-to-payroll",
            ],
            "DOUBLE": ["calculated-amount", "number-of-units", "value"],
            "LONG": ["attachment-id", "reference-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 50, "DOUBLE"),
        ],
    },
    # ── workPermitInfo ───────────────────────────────────────────────────────
    "workPermitInfo": {
        "business_keys": ["userId", "country", "documentType", "documentNumber", "issueDate"],
        "template": ["user-id", "country", "document-type", "document-number", "issue-date"],
        "references": "employmentInfo",
        "field_types": {
            "BOOLEAN": ["is-validated"],
            "DATE": ["expiration-date", "issue-date"],
            "LONG": ["attachment-id"],
        },
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── globalAssignmentInfo ─────────────────────────────────────────────────
    "globalAssignmentInfo": {
        "business_keys": ["userId"],
        "template": ["user-id"],
        "references": "employmentInfo",
        "field_types": {
            "DATE": ["end-date", "planned-end-date", "payroll-end-date"],
        },
        "ranges": [
            ("custom-string", 101, 120, "STRING"),
            ("custom-date", 31, 40, "DATE"),
            ("custom-long", 21, 30, "LONG"),
            ("custom-double", 21, 30, "DOUBLE"),
        ],
    },
    # ── jobRelationsInfo ─────────────────────────────────────────────────────
    "jobRelationsInfo": {
        "business_keys": ["userId", "relationshipType", "startDate"],
        "template": ["user-id", "relationship-type", "start-date"],
        "references": "employmentInfo",
        "field_types": {},
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── globalInfo ───────────────────────────────────────────────────────────
    "globalInfo": {
        "business_keys": ["personIdExternal", "startDate", "country"],
        "template": ["personInfo.person-id-external", "start-date", "country"],
        "references": "personInfo",
        "field_types": {
            "DATE": ["end-date"],
            "LONG": ["attachment-id"],
        },
        "ranges": [
            ("genericString", 1, 30, "STRING"),
            ("genericDate", 1, 20, "DATE"),
            ("genericNumber", 1, 40, "LONG"),
            ("custom-string", 1, 30, "STRING"),
            ("custom-date", 1, 20, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── imInfo ───────────────────────────────────────────────────────────────
    "imInfo": {
        "business_keys": ["personIdExternal", "domain"],
        "template": ["personInfo.person-id-external", "domain"],
        "references": "personInfo",
        "field_types": {},
        "ranges": [
            ("custom-string", 1, 20, "STRING"),
            ("custom-date", 1, 10, "DATE"),
            ("custom-long", 1, 20, "LONG"),
            ("custom-double", 1, 20, "DOUBLE"),
        ],
    },
    # ── pensionPayoutsInfo ───────────────────────────────────────────────────
    "pensionPayoutsInfo": {
        "business_keys": ["userId"],
        "template": ["user-id"],
        "references": "employmentInfo",
        "field_types": {},
        "ranges": [],
    },
    # ── biographicalInfoLoc ──────────────────────────────────────────────────
    "biographicalInfoLoc": {
        "business_keys": ["personIdExternal", "country"],
        "template": ["personInfo.person-id-external", "country", "user-id"],
        "references": "personInfo",
        "field_types": {},
        "ranges": [],
    },
    # ── paymentInfo (sin business keys SAP, solo inyección) ──────────────────
    "paymentInfo": {
        "business_keys": [],
        "template": [],
        "references": None,
        "inject_override": ["effectiveStartDate"],
        "field_types": {},
        "ranges": [],
    },
}

# ─── Campos de identidad/referencia (no requieren inyección sintética) ───────
# Estos campos existen como nodos regulares en el XML y no necesitan
# ser creados artificialmente por el parser.
_NON_INJECTABLE_FIELDS: set[str] = {
    "user-id", "person-id-external", "seq-number",
    "related-person-id-external",
    "country", "card-type", "phone-type", "email-type", "domain",
    "name", "relationship", "relationship-type",
    "document-type", "document-number", "issue-date",
    "pay-component", "pay-component-code", "pay-date",
}

# ─── Índice invertido de tipos (construido al importar) ──────────────────────
_FIELD_TYPE_INDEX: dict[str, dict[str, str]] = {}
_RANGE_FIELD_PATTERN: re.Pattern = re.compile(r"^(.+?)(\d+)$")


def _build_field_type_index():
    for entity, config in SAP_ENTITY_CONFIGS.items():
        index: dict[str, str] = {}
        for sap_type, fields in config.get("field_types", {}).items():
            for field in fields:
                index[field] = sap_type
        _FIELD_TYPE_INDEX[entity] = index


_build_field_type_index()

# ─── Mapping tipo SAP → tipo metadata ───────────────────────────────────────
_SAP_TO_METADATA_TYPE: dict[str, str] = {
    "STRING": "string",
    "DATE": "date",
    "LONG": "integer",
    "DOUBLE": "decimal",
    "BOOLEAN": "boolean",
    "PICKLIST": "picklist",
}


# ─── Funciones de acceso ────────────────────────────────────────────────────

def get_entity_config(entity: str) -> dict | None:
    return SAP_ENTITY_CONFIGS.get(entity)


def get_field_type(entity: str, field_id: str) -> str | None:
    """Resuelve el tipo SAP de un campo para una entidad dada.

    Orden de resolución:
    1. Lookup directo en field_types
    2. Match en ranges (prefijo + número)
    3. Variantes -alt1/-alt2 (mismo tipo que campo base, salvo override)
    4. Default STRING para entidades conocidas
    """
    if entity not in SAP_ENTITY_CONFIGS:
        return None

    index = _FIELD_TYPE_INDEX.get(entity, {})
    config = SAP_ENTITY_CONFIGS[entity]
    ranges = config.get("ranges", [])
    alt_overrides = config.get("alt_type_overrides", {})

    # 1. Lookup directo
    if field_id in index:
        return index[field_id]

    # 2. Detectar variante -alt1/-alt2
    alt_suffix = None
    base_field = field_id
    for suffix in ("-alt1", "-alt2"):
        if field_id.endswith(suffix):
            alt_suffix = suffix
            base_field = field_id[: -len(suffix)]
            break

    if alt_suffix:
        if base_field in index:
            override_key = f"{base_field}{alt_suffix}"
            if override_key in alt_overrides:
                return alt_overrides[override_key]
            return index[base_field]

    # 3. Match en ranges
    target = base_field if alt_suffix else field_id
    match = _RANGE_FIELD_PATTERN.match(target)
    if match:
        prefix, num = match.group(1), int(match.group(2))
        for r_prefix, r_start, r_end, r_type in ranges:
            if prefix == r_prefix and r_start <= num <= r_end:
                if alt_suffix:
                    override_key = f"{r_prefix}{alt_suffix}"
                    if override_key in alt_overrides:
                        return alt_overrides[override_key]
                return r_type

    # 4. Default STRING para entidades conocidas
    return "STRING"


def get_metadata_type(entity: str, field_id: str) -> str | None:
    """Retorna el tipo de metadata (lowercase) para un campo SAP."""
    sap_type = get_field_type(entity, field_id)
    if sap_type:
        return _SAP_TO_METADATA_TYPE.get(sap_type, "string")
    return None


def get_injectable_fields(entity: str) -> list[str]:
    """Deriva los campos que necesitan inyección sintética en el XML.

    Para la mayoría de entidades se calcula automáticamente:
    campos del template que no son cross-references (con .) ni campos
    de identidad conocidos (_NON_INJECTABLE_FIELDS).

    Entidades con inject_override usan esa lista directamente.
    """
    config = SAP_ENTITY_CONFIGS.get(entity)
    if not config:
        return []
    if "inject_override" in config:
        return list(config["inject_override"])
    return [
        f for f in config["template"]
        if "." not in f and f not in _NON_INJECTABLE_FIELDS
    ]


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
