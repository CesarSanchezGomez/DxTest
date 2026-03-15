import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import time
import logging
import zipfile

from .core.parsing import parse_successfactors_xml, parse_successfactors_with_csf, parse_multiple_xml_files
from .core.generators.golden_record import GoldenRecordGenerator
from .core.generators.golden_record.element_processor import ElementProcessor
from .core.generators.golden_record.csv_generator import CSVGenerator

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "backend" / "storage" / "dxsentinel"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "output"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def _ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class FileService:
    """Almacenamiento local temporal de archivos XML subidos."""

    @staticmethod
    def save_upload(content: bytes, original_filename: str) -> tuple[str, Path]:
        _ensure_dirs()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
        suffix = Path(original_filename).suffix or ".xml"
        file_path = UPLOAD_DIR / f"{file_id}{suffix}"
        file_path.write_bytes(content)
        return file_id, file_path

    @staticmethod
    def get_path(file_id: str) -> Optional[Path]:
        _ensure_dirs()
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file() and file_path.stem == file_id:
                return file_path
        return None

    @staticmethod
    def delete_file(file_id: str) -> bool:
        path = FileService.get_path(file_id)
        if path and path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def cleanup_old(max_age_hours: int = 1):
        _ensure_dirs()
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff:
                    try:
                        file_path.unlink()
                    except Exception:
                        pass


class ProcessingService:
    """Orquesta: upload → parse → generate metadata + golden record."""

    @staticmethod
    def extract_languages(file_path: Path) -> list[str]:
        """Extrae idiomas disponibles de un archivo SDM."""
        tree = ET.parse(str(file_path))
        root = tree.getroot()

        languages = set()
        ns_uri = "http://www.w3.org/XML/1998/namespace"

        for elem in root.iter():
            lang = elem.get(f"{{{ns_uri}}}lang") or elem.get("lang")
            if lang:
                languages.add(lang.strip())

        return sorted(languages)

    @staticmethod
    def extract_entities(file_path: Path) -> list[str]:
        """Extrae entidades disponibles (hris-element ids) de un archivo SDM."""
        tree = ET.parse(str(file_path))
        root = tree.getroot()

        entities = []
        seen = set()

        for elem in root.iter():
            tag = elem.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]

            if "hris" in tag.lower() and "element" in tag.lower():
                entity_id = elem.get("id")
                if entity_id and entity_id not in seen:
                    seen.add(entity_id)
                    entities.append(entity_id)

        return entities

    @staticmethod
    def extract_countries(file_path: Path) -> list[str]:
        """Extrae países disponibles de un archivo CSF."""
        tree = ET.parse(str(file_path))
        root = tree.getroot()

        countries = set()

        for elem in root.iter():
            tag = elem.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]

            if tag.lower() == "country":
                country_id = elem.get("id")
                if country_id:
                    countries.add(country_id.strip().upper())

        return sorted(countries)

    @staticmethod
    def process(
        main_file_path: Path,
        csf_file_path: Optional[Path],
        language_code: str,
        country_codes: Optional[list[str]],
        excluded_entities: Optional[list[str]] = None,
        output_dir: Optional[Path] = None,
    ) -> dict:
        """Procesa archivos XML y genera golden record + metadata + report."""
        start_time = time.time()

        if output_dir is None:
            _ensure_dirs()
            run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            output_dir = OUTPUT_DIR / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        if country_codes and csf_file_path:
            files = [
                {"path": str(main_file_path), "type": "main", "source_name": main_file_path.name},
                {"path": str(csf_file_path), "type": "csf", "source_name": csf_file_path.name},
            ]
            parsed_model = parse_multiple_xml_files(files)
        elif csf_file_path:
            parsed_model = parse_successfactors_with_csf(str(main_file_path), str(csf_file_path))
        else:
            parsed_model = parse_successfactors_xml(str(main_file_path), main_file_path.name)

        generator = GoldenRecordGenerator(
            output_dir=str(output_dir),
            target_countries=country_codes,
            excluded_entities=excluded_entities,
        )
        result_files = generator.generate_template(
            parsed_model=parsed_model,
            language_code=language_code,
        )

        processing_time = time.time() - start_time

        csv_path = Path(result_files["csv"])
        field_count = 0
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
                if lines:
                    header_fields = lines[0].strip().split(",")
                    field_count = len(header_fields) if header_fields[0] else 0

        # Crear ZIP con los 3 archivos
        zip_name = f"{csv_path.stem}.zip"
        zip_path = output_dir / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_key in ["csv", "metadata", "report"]:
                fpath = Path(result_files[file_key])
                if fpath.exists():
                    zf.write(fpath, fpath.name)

        return {
            "output_file": str(csv_path),
            "metadata_file": result_files["metadata"],
            "report_file": result_files.get("report", ""),
            "zip_file": str(zip_path),
            "download_id": output_dir.name,
            "field_count": field_count,
            "processing_time": round(processing_time, 2),
            "countries_processed": country_codes,
        }

    @staticmethod
    def get_download_path(download_id: str) -> Optional[Path]:
        """Busca el ZIP generado para descarga."""
        _ensure_dirs()
        run_dir = OUTPUT_DIR / download_id
        if not run_dir.exists():
            return None
        for f in run_dir.iterdir():
            if f.suffix == ".zip":
                return f
        return None
