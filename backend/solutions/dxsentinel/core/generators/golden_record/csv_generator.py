from typing import Dict, List, Optional
import csv
import json
from pathlib import Path

from ...constants import ELEMENT_ORDER
from .element_processor import ElementProcessor
from .language_resolver import GoldenRecordLanguageResolver
from ..metadata.metadata_generator import MetadataGenerator
from ..reports.field_report_generator import FieldReportGenerator


class CSVGenerator:
    """Genera CSVs del Golden Record ordenados por elemento."""

    def __init__(self, target_countries: Optional[List[str]] = None, language_code: Optional[str] = None):
        if target_countries and isinstance(target_countries, str):
            target_countries = [target_countries]

        self.processor = ElementProcessor(target_countries=target_countries)
        self.language_resolver = GoldenRecordLanguageResolver()
        self.metadata_gen = MetadataGenerator()
        self.report_gen = FieldReportGenerator()
        self.target_countries = target_countries
        self.language_code = language_code

    def generate(self, golden_record: Dict, output_dir: str) -> tuple[str, str, str]:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.target_countries and len(self.target_countries) == 1:
            filename = f"golden_record_{self.target_countries[0]}_{timestamp}.csv"
        else:
            filename = f"golden_record_{timestamp}.csv"

        output_path = Path(output_dir) / filename
        elements = golden_record.get("elements", [])

        columns, column_metadata = self._consolidate_and_sort_columns(elements)
        language_code = self.language_code or "en-US"
        has_multiple_countries = self.target_countries and len(self.target_countries) > 1

        translated_labels = self._get_translated_labels(column_metadata, language_code, has_multiple_countries)

        with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([col["full_id"] for col in columns])
            writer.writerow([translated_labels.get(col["full_id"], col["field_id"]) for col in columns])

        metadata = self.metadata_gen.generate_metadata(golden_record, columns)

        csv_path = Path(output_path)
        metadata_path = csv_path.parent / f"{csv_path.stem}_metadata.json"
        report_path = csv_path.parent / f"{csv_path.stem}_field_report.xlsx"

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.report_gen.generate(metadata, translated_labels, str(report_path))

        return str(output_path), str(metadata_path), str(report_path)

    def generate_template_csv(self, parsed_model: Dict, output_path: str, language_code: str) -> tuple[str, str]:
        processed_data = self.processor.process_model(parsed_model)
        elements = processed_data.get("elements", [])

        columns, column_metadata = self._consolidate_and_sort_columns(elements)
        has_multiple_countries = self.target_countries and len(self.target_countries) > 1

        translated_labels = self._get_translated_labels(column_metadata, language_code, has_multiple_countries)

        with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([col["full_id"] for col in columns])
            writer.writerow([translated_labels.get(col["full_id"], col["field_id"]) for col in columns])

        metadata = self.metadata_gen.generate_metadata(processed_data, columns)

        csv_path = Path(output_path)
        metadata_path = csv_path.parent / f"{csv_path.stem}_metadata.json"
        report_path = csv_path.parent / f"{csv_path.stem}_field_report.xlsx"

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.report_gen.generate(metadata, translated_labels, str(report_path))

        return output_path, str(report_path)

    def _consolidate_and_sort_columns(self, elements: List[Dict]) -> tuple[List[Dict], Dict[str, List[Dict]]]:
        column_metadata: Dict[str, List[Dict]] = {}
        columns_by_element: Dict[str, Dict[str, Dict]] = {}

        for element in elements:
            element_id = element["element_id"]

            if element_id not in columns_by_element:
                columns_by_element[element_id] = {}

            for field in element["fields"]:
                full_id = field["full_field_id"]

                if full_id not in column_metadata:
                    column_metadata[full_id] = []

                column_metadata[full_id].append({
                    "node": field["node"],
                    "is_country_specific": field.get("is_country_specific", False),
                    "country_code": field.get("country_code"),
                    "element_id": element_id,
                    "field_id": field["field_id"],
                })

                if full_id not in columns_by_element[element_id]:
                    columns_by_element[element_id][full_id] = {
                        "full_id": full_id,
                        "field_id": field["field_id"],
                        "node": field["node"],
                        "is_country_specific": field.get("is_country_specific", False),
                        "country_code": field.get("country_code"),
                        "element_id": element_id,
                    }

        sorted_columns = []

        for element_id in ELEMENT_ORDER:
            if element_id in columns_by_element:
                element_columns = sorted(
                    columns_by_element[element_id].values(),
                    key=lambda col: col["field_id"],
                )
                sorted_columns.extend(element_columns)

        for element_id, columns_dict in columns_by_element.items():
            if element_id not in ELEMENT_ORDER:
                element_columns = sorted(columns_dict.values(), key=lambda col: col["field_id"])
                sorted_columns.extend(element_columns)

        return sorted_columns, column_metadata

    def _get_translated_labels(
        self, column_metadata: Dict[str, List[Dict]],
        language_code: str, has_multiple_countries: bool = False,
    ) -> Dict[str, str]:
        labels_dict = {}
        single_country_mode = self.target_countries and len(self.target_countries) == 1

        for full_id, variants in column_metadata.items():
            if not variants[0]["is_country_specific"]:
                label = self._resolve_field_label(variants[0]["node"], language_code, full_id)
                labels_dict[full_id] = label
            elif has_multiple_countries and len(variants) > 1:
                country_labels = []
                for variant in sorted(variants, key=lambda x: x["country_code"] or ""):
                    label = self._resolve_field_label(variant["node"], language_code, full_id)
                    country_labels.append(f"{variant['country_code']}: {label}")
                labels_dict[full_id] = " | ".join(country_labels)
            else:
                variant = variants[0]
                label = self._resolve_field_label(variant["node"], language_code, full_id)
                if variant["is_country_specific"] and variant["country_code"] and not single_country_mode:
                    labels_dict[full_id] = f"{variant['country_code']}: {label}"
                else:
                    labels_dict[full_id] = label

        return labels_dict

    def _resolve_field_label(self, field_node: Dict, language_code: str, full_field_id: str) -> str:
        field_labels = field_node.get("labels", {})
        label, _ = self.language_resolver.resolve_label(field_labels, language_code)

        if not label:
            parts = full_field_id.split("_")
            label = parts[-1] if parts else full_field_id

        return label
