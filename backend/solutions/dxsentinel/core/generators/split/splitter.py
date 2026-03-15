"""Divide un Golden Record CSV en layouts por entidad SAP.

Optimizacion respecto a DxSentinel: usa directamente la metadata JSON
generada (layout_split_config, business_keys, field_catalog) en lugar
de resolver business keys con logica compleja de fallbacks.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .basic_user_info import BasicUserInfoGenerator

logger = logging.getLogger(__name__)


class GoldenRecordSplitter:
    """Separa el Golden Record en un CSV por entidad + BasicUserInformation."""

    PIPE = "|"

    MULTI_VALUE_ENTITIES = frozenset({
        "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
        "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
    })

    def __init__(self, metadata: Dict):
        self.layout_config = metadata.get("layout_split_config", {})
        self.business_keys = metadata.get("business_keys", {})
        self.field_catalog = metadata.get("field_catalog", {})

    # ── API publica ──────────────────────────────────────────────────────

    def split(self, csv_path: str, output_dir: str) -> List[str]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        golden = self._read_csv(csv_path)
        generated: List[str] = []

        for group_key, config in self.layout_config.items():
            entity_id = config["element_id"]
            columns = self._build_columns(entity_id, config["fields"], golden)

            if not columns:
                continue

            layout_path = out / config["layout_filename"]

            if entity_id in self.MULTI_VALUE_ENTITIES:
                self._write_multivalue(layout_path, columns, golden)
            else:
                self._write_single(layout_path, columns, golden)

            generated.append(str(layout_path))

        bui = BasicUserInfoGenerator().generate(golden, out)
        if bui:
            generated.append(bui)

        return generated

    # ── Lectura del Golden Record ────────────────────────────────────────

    @staticmethod
    def _read_csv(csv_path: str) -> Dict:
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                with open(csv_path, "r", encoding=enc) as f:
                    reader = csv.reader(f)
                    technical = next(reader)
                    descriptive = next(reader)
                    rows = [r for r in reader if r and any(c.strip() for c in r)]
                return {
                    "technical_header": technical,
                    "descriptive_header": descriptive,
                    "data_rows": rows,
                }
            except (UnicodeDecodeError, StopIteration):
                continue
        raise ValueError(f"No se pudo leer {csv_path}")

    # ── Construccion de columnas ─────────────────────────────────────────

    def _build_columns(
        self, entity_id: str, fields: List[str], golden: Dict,
    ) -> List[Dict]:
        header_index = {col: i for i, col in enumerate(golden["technical_header"])}
        desc_header = golden["descriptive_header"]

        bk_list = (
            self.business_keys
            .get(entity_id, {})
            .get("business_keys", [])
        )

        columns: List[Dict] = []
        added_sap: set[str] = set()
        added_golden: set[str] = set()

        # 1. Business keys (orden SAP)
        for bk in bk_list:
            golden_col = bk["golden_column"]
            sap_name = bk["sap_column"]
            idx = header_index.get(golden_col)

            columns.append({
                "sap_name": sap_name,
                "source_idx": idx,
                "descriptive": (
                    desc_header[idx]
                    if idx is not None and idx < len(desc_header)
                    else _humanize(sap_name)
                ),
            })
            added_sap.add(sap_name)
            if golden_col:
                added_golden.add(golden_col)

        # 2. Campos restantes de la entidad
        for field_id in fields:
            if field_id in added_golden:
                continue

            idx = header_index.get(field_id)
            if idx is None:
                continue

            cat = self.field_catalog.get(field_id, {})
            sap_name = cat.get("field", field_id)

            if sap_name in added_sap:
                continue

            is_hris = cat.get("is_hris_field", False)
            descriptive = (
                _humanize(sap_name)
                if is_hris
                else desc_header[idx] if idx < len(desc_header) else sap_name
            )

            columns.append({
                "sap_name": sap_name,
                "source_idx": idx,
                "descriptive": descriptive,
            })
            added_sap.add(sap_name)
            added_golden.add(field_id)

        return columns

    # ── Escritura single-value ───────────────────────────────────────────

    def _write_single(
        self, path: Path, columns: List[Dict], golden: Dict,
    ) -> None:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([c["sap_name"] for c in columns])
            w.writerow([c["descriptive"] for c in columns])

            for row in golden["data_rows"]:
                out = []
                for col in columns:
                    idx = col["source_idx"]
                    if idx is None or idx >= len(row):
                        out.append("")
                    else:
                        val = row[idx]
                        if self.PIPE in val:
                            val = val.split(self.PIPE)[0].strip()
                        out.append(val)
                w.writerow(out)

    # ── Escritura multi-value ────────────────────────────────────────────

    def _write_multivalue(
        self, path: Path, columns: List[Dict], golden: Dict,
    ) -> None:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([c["sap_name"] for c in columns])
            w.writerow([c["descriptive"] for c in columns])

            for row in golden["data_rows"]:
                expanded = self._expand_row(row, columns)
                for out_row in expanded:
                    w.writerow(out_row)

    def _expand_row(
        self, row: List[str], columns: List[Dict],
    ) -> List[List[str]]:
        max_count = 1

        for col in columns:
            idx = col["source_idx"]
            if idx is not None and idx < len(row) and self.PIPE in row[idx]:
                count = row[idx].count(self.PIPE) + 1
                if count > max_count:
                    max_count = count

        if max_count == 1:
            return [self._extract_values(row, columns, 0)]

        return [self._extract_values(row, columns, i) for i in range(max_count)]

    def _extract_values(
        self, row: List[str], columns: List[Dict], index: int,
    ) -> List[str]:
        out: List[str] = []
        for col in columns:
            idx = col["source_idx"]
            if idx is None or idx >= len(row):
                out.append("")
                continue

            val = row[idx]
            if self.PIPE in val:
                parts = val.split(self.PIPE)
                out.append(parts[index].strip() if index < len(parts) else "")
            else:
                out.append(val)
        return out


def _humanize(sap_name: str) -> str:
    """Convierte un nombre SAP a formato legible."""
    _MAP = {
        "user-id": "User ID",
        "person-id-external": "Person ID External",
        "personInfo.person-id-external": "Person ID External",
        "related-person-id-external": "Related Person ID External",
        "start-date": "Start Date",
        "end-date": "End Date",
        "seq-number": "Sequence Number",
        "pay-component": "Pay Component",
        "pay-component-code": "Pay Component Code",
        "pay-date": "Pay Date",
        "email-address": "Email Address",
        "phone-type": "Phone Type",
        "card-type": "Card Type",
        "address-type": "Address Type",
        "country": "Country",
        "relationship": "Relationship",
        "relationship-type": "Relationship Type",
        "name": "Name",
        "domain": "Domain",
        "document-type": "Document Type",
        "document-number": "Document Number",
        "issue-date": "Issue Date",
        "event-reason": "Event Reason",
    }
    return _MAP.get(sap_name, sap_name.replace("-", " ").title())
