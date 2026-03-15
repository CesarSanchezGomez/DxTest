"""Genera el layout BasicUserInformation.csv con columnas fijas SAP."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

FILENAME = "BasicUserInformation.csv"

_COLUMNS = [
    "STATUS", "USERID", "USERNAME", "FIRSTNAME", "LASTNAME",
    "GENDER", "EMAIL", "MANAGER", "HR", "DEPARTMENT", "TIMEZONE",
]

_LABELS = {
    "STATUS": "Status", "USERID": "User ID", "USERNAME": "Username",
    "FIRSTNAME": "First Name", "LASTNAME": "Last Name", "GENDER": "Gender",
    "EMAIL": "Email", "MANAGER": "Manager", "HR": "HR",
    "DEPARTMENT": "Department", "TIMEZONE": "Timezone",
}

_ALIASES: Dict[str, List[str]] = {
    "STATUS":         ["STATUS", "status"],
    "USERID":         ["personInfo_person-id-external", "USERID"],
    "USERNAME":       ["USERNAME", "username"],
    "FIRSTNAME":      ["personalInfo_first-name", "FIRSTNAME"],
    "LASTNAME":       ["personalInfo_last-name", "LASTNAME"],
    "GENDER":         ["personalInfo_gender", "GENDER"],
    "EMAIL":          ["emailInfo_email-address", "EMAIL"],
    "_EMAIL_PRIMARY": ["emailInfo_isPrimary"],
    "MANAGER":        ["jobInfo_manager-id", "MANAGER"],
    "HR":             ["HR", "hr"],
    "DEPARTMENT":     ["jobInfo_department", "DEPARTMENT"],
    "TIMEZONE":       ["TIMEZONE", "timezone"],
}

_DEFAULTS = {
    "STATUS": "Active",
    "MANAGER": "NO_MANAGER",
    "HR": "NO_HR",
    "TIMEZONE": "America/Mexico_City",
}

_PIPE = "|"


class BasicUserInfoGenerator:

    def generate(self, golden: Dict, output_dir: Path) -> Optional[str]:
        tech = golden["technical_header"]
        rows = golden["data_rows"]

        col_map = _resolve_map(tech)
        if not col_map:
            return None

        out_cols = [c for c in _COLUMNS if c in col_map or c in _DEFAULTS]
        path = output_dir / FILENAME

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(out_cols)
            w.writerow([_LABELS.get(c, c) for c in out_cols])

            for row in rows:
                out = []
                for col in out_cols:
                    if col == "EMAIL":
                        val = _primary_email(row, col_map)
                        if not val:
                            val = _get(row, col_map, "USERID")
                    elif col in col_map:
                        val = _get(row, col_map, col)
                    else:
                        val = ""

                    if not val.strip() and col in _DEFAULTS:
                        val = _DEFAULTS[col]
                    out.append(val)
                w.writerow(out)

        return str(path)


def _resolve_map(tech: List[str]) -> Dict[str, int]:
    index = {col: i for i, col in enumerate(tech)}
    result: Dict[str, int] = {}
    for bui_col, aliases in _ALIASES.items():
        for alias in aliases:
            if alias in index:
                result[bui_col] = index[alias]
                break
    return result


def _raw(row: List[str], col_map: Dict[str, int], col: str) -> str:
    if col not in col_map:
        return ""
    idx = col_map[col]
    return row[idx] if idx < len(row) else ""


def _get(row: List[str], col_map: Dict[str, int], col: str) -> str:
    val = _raw(row, col_map, col)
    if not val:
        return ""
    return val.split(_PIPE)[0].strip() if _PIPE in val else val


def _primary_email(row: List[str], col_map: Dict[str, int]) -> str:
    addresses_raw = _raw(row, col_map, "EMAIL")
    primary_raw = _raw(row, col_map, "_EMAIL_PRIMARY")

    if not addresses_raw:
        return ""

    addresses = [v.strip() for v in addresses_raw.split(_PIPE)]
    primaries = [v.strip() for v in primary_raw.split(_PIPE)] if primary_raw else []

    for i, flag in enumerate(primaries):
        if flag.lower() == "yes" and i < len(addresses):
            return addresses[i]

    return addresses[0] if addresses else ""
