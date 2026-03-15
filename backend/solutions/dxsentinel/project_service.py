"""Orquesta proyectos y versiones: Supabase DB + Supabase Storage."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .repositories.supabase_db import SupabaseDBRepository
from .repositories.supabase_storage import SupabaseStorageRepository

logger = logging.getLogger(__name__)

_INVALID_PATH_CHARS = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']


class ProjectService:

    def __init__(self):
        self._db = SupabaseDBRepository()
        self._storage = SupabaseStorageRepository()

    # ── Proyectos ────────────────────────────────────────────────────────

    def list_projects(self, consultant_email: str) -> List[Dict]:
        return self._db.list_projects(consultant_email)

    # ── Versiones ────────────────────────────────────────────────────────

    def create_version(
        self,
        consultant_email: str,
        instance_number: str,
        client_name: str,
        language_code: str,
        country_codes: Optional[List[str]] = None,
    ) -> tuple[Dict, Dict, int]:
        """Crea proyecto (si no existe) y nueva version."""
        instance_number = _sanitize(instance_number)
        client_name = _sanitize(client_name)

        project = self._db.get_or_create_project(
            consultant_email, instance_number, client_name,
        )
        version_number = self._db.get_next_version_number(project["id"])
        version = self._db.create_version(
            project_id=project["id"],
            version_number=version_number,
            language_code=language_code,
            country_codes=country_codes,
        )
        return project, version, version_number

    def store_outputs(
        self,
        version: Dict,
        project: Dict,
        consultant_email: str,
        csv_path: Path,
        metadata_path: Path,
        report_path: Optional[Path] = None,
    ) -> Dict:
        """Sube CSV y metadata a Supabase Storage y actualiza paths en DB."""
        prefix = _build_storage_prefix(
            consultant_email,
            project["instance_number"],
            project["client_name"],
            version["version_number"],
        )

        csv_storage_path = f"{prefix}/outputs/{csv_path.name}"
        metadata_storage_path = f"{prefix}/outputs/{metadata_path.name}"

        self._storage.upload_from_local(csv_storage_path, csv_path, content_type="text/csv")
        self._storage.upload_from_local(metadata_storage_path, metadata_path, content_type="application/json")

        if report_path and report_path.exists():
            report_storage_path = f"{prefix}/outputs/{report_path.name}"
            self._storage.upload_from_local(
                report_storage_path, report_path,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        self._db.update_version_paths(
            version_id=version["id"],
            csv_storage_path=csv_storage_path,
            metadata_storage_path=metadata_storage_path,
        )

        return {
            "csv_storage_path": csv_storage_path,
            "metadata_storage_path": metadata_storage_path,
        }

    def download_metadata_to_temp(self, metadata_storage_path: str) -> Path:
        """Descarga metadata JSON desde Storage a archivo temporal."""
        return self._storage.download_to_temp(metadata_storage_path, suffix=".json")

    def list_versions(
        self,
        consultant_email: str,
        instance_number: Optional[str] = None,
        client_name: Optional[str] = None,
    ) -> List[Dict]:
        return self._db.list_versions(consultant_email, instance_number, client_name)

    def get_version(self, version_id: str) -> Optional[Dict]:
        return self._db.get_version(version_id)

    # ── Rollback ─────────────────────────────────────────────────────────

    def rollback_version(self, version_id: str, project_id: str) -> None:
        self._db.delete_version(version_id)
        self._db.delete_project_if_empty(project_id)


def _sanitize(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Value cannot be empty")
    for ch in _INVALID_PATH_CHARS:
        stripped = stripped.replace(ch, "_")
    return stripped


def _get_consultant_folder(email: str) -> str:
    return email.split("@")[0].replace(".", "_")


def _get_project_folder(instance_number: str, client_name: str) -> str:
    return f"{instance_number}_{client_name.replace(' ', '')}"


def _build_storage_prefix(
    consultant_email: str, instance_number: str, client_name: str, version_number: int,
) -> str:
    consultant = _get_consultant_folder(consultant_email)
    project = _get_project_folder(instance_number, client_name)
    return f"{consultant}/{project}/v{version_number}"
