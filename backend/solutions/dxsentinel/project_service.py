"""Orquesta proyectos y versiones: Supabase DB + filesystem local."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .repositories.supabase_db import SupabaseDBRepository

logger = logging.getLogger(__name__)

_INVALID_PATH_CHARS = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']


class ProjectService:

    def __init__(self):
        self._db = SupabaseDBRepository()

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
        """Crea proyecto (si no existe) y nueva version. Retorna (project, version, version_number)."""
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

    def update_version_paths(
        self,
        version_id: str,
        csv_path: str,
        metadata_path: str,
        report_path: Optional[str] = None,
        zip_path: Optional[str] = None,
        field_count: int = 0,
    ) -> Dict:
        return self._db.update_version_paths(
            version_id=version_id,
            csv_storage_path=csv_path,
            metadata_storage_path=metadata_path,
            report_storage_path=report_path,
            zip_storage_path=zip_path,
            field_count=field_count,
        )

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
