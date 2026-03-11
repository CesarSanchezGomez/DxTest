from typing import Dict, Optional, List
from pathlib import Path

from .csv_generator import CSVGenerator
from .exceptions import GoldenRecordError

__all__ = ["GoldenRecordGenerator", "GoldenRecordError"]


class GoldenRecordGenerator:
    """Genera golden_record_template.csv, metadata JSON y field report XLSX."""

    def __init__(
        self, output_dir: str = "output/golden_record",
        target_countries: Optional[List[str]] = None,
        excluded_entities: Optional[List[str]] = None,
    ):
        self.output_dir = output_dir

        if target_countries and isinstance(target_countries, str):
            target_countries = [target_countries]

        self.target_countries = target_countries
        self.excluded_entities = excluded_entities
        self.csv_gen = CSVGenerator(
            target_countries=target_countries,
            excluded_entities=excluded_entities,
        )

    def generate_template(self, parsed_model: Dict, language_code: str = "en") -> Dict[str, str]:
        """Genera golden_record_template.csv, metadata JSON y field report XLSX."""
        try:
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            language_normalized = language_code.lower().replace("_", "-")

            if self.target_countries:
                if len(self.target_countries) == 1:
                    template_name = f"golden_record_template_{language_normalized}_{self.target_countries[0]}.csv"
                else:
                    countries_str = "_".join(sorted(self.target_countries))
                    template_name = f"golden_record_template_{language_normalized}_{countries_str}.csv"
            else:
                template_name = f"golden_record_template_{language_normalized}.csv"

            template_path = output_dir / template_name

            csv_path, report_path = self.csv_gen.generate_template_csv(
                parsed_model, str(template_path), language_normalized,
            )

            metadata_path = Path(csv_path).parent / f"{Path(csv_path).stem}_metadata.json"

            return {
                "csv": csv_path,
                "metadata": str(metadata_path),
                "report": report_path,
            }

        except Exception as e:
            raise GoldenRecordError(f"Error generating template: {str(e)}") from e
