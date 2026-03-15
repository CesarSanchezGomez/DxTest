"""CRUD contra tablas projects y versions en Supabase.

Tablas requeridas en Supabase (SQL):

    CREATE TABLE projects (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        consultant_email TEXT NOT NULL,
        instance_number TEXT NOT NULL,
        client_name TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now(),
        UNIQUE(consultant_email, instance_number, client_name)
    );

    CREATE TABLE versions (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        version_number INTEGER NOT NULL,
        language_code TEXT NOT NULL DEFAULT 'en-US',
        country_codes TEXT[],
        csv_storage_path TEXT,
        metadata_storage_path TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- RLS policies: cada usuario solo ve sus proyectos
    ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
    ALTER TABLE versions ENABLE ROW LEVEL SECURITY;
"""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.core.auth.supabase_client import get_supabase_client


class SupabaseDBRepository:
    """Operaciones CRUD contra tablas projects y versions."""

    def __init__(self):
        self._client = get_supabase_client()

    # ── Projects ─────────────────────────────────────────────────────────

    def get_or_create_project(
        self, consultant_email: str, instance_number: str, client_name: str,
    ) -> Dict:
        existing = (
            self._client.table("projects")
            .select("*")
            .eq("consultant_email", consultant_email)
            .eq("instance_number", instance_number)
            .eq("client_name", client_name)
            .execute()
        )
        if existing.data:
            return existing.data[0]

        result = (
            self._client.table("projects")
            .insert({
                "consultant_email": consultant_email,
                "instance_number": instance_number,
                "client_name": client_name,
            })
            .execute()
        )
        return result.data[0]

    def list_projects(self, consultant_email: str) -> List[Dict]:
        projects = (
            self._client.table("projects")
            .select("*, versions(version_number, created_at)")
            .eq("consultant_email", consultant_email)
            .order("instance_number")
            .execute()
        )

        result = []
        for project in projects.data or []:
            versions = project.pop("versions", [])
            latest = max(versions, key=lambda v: v["version_number"]) if versions else None
            result.append({
                "id": project["id"],
                "instance_number": project["instance_number"],
                "client_name": project["client_name"],
                "latest_version": latest["version_number"] if latest else 0,
                "created_at": latest["created_at"] if latest else project["created_at"],
                "total_versions": len(versions),
            })
        return result

    # ── Versions ─────────────────────────────────────────────────────────

    def get_next_version_number(self, project_id: str) -> int:
        result = (
            self._client.table("versions")
            .select("version_number")
            .eq("project_id", project_id)
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )
        return (result.data[0]["version_number"] + 1) if result.data else 1

    def create_version(
        self,
        project_id: str,
        version_number: int,
        language_code: str,
        country_codes: Optional[List[str]] = None,
    ) -> Dict:
        result = (
            self._client.table("versions")
            .insert({
                "project_id": project_id,
                "version_number": version_number,
                "language_code": language_code,
                "country_codes": country_codes,
            })
            .execute()
        )
        return result.data[0]

    def update_version_paths(
        self,
        version_id: str,
        csv_storage_path: str,
        metadata_storage_path: str,
    ) -> Dict:
        result = (
            self._client.table("versions")
            .update({
                "csv_storage_path": csv_storage_path,
                "metadata_storage_path": metadata_storage_path,
            })
            .eq("id", version_id)
            .execute()
        )
        return result.data[0]

    def list_versions(
        self,
        consultant_email: str,
        instance_number: Optional[str] = None,
        client_name: Optional[str] = None,
    ) -> List[Dict]:
        query = (
            self._client.table("versions")
            .select("*, projects!inner(consultant_email, instance_number, client_name)")
        )
        query = query.eq("projects.consultant_email", consultant_email)

        if instance_number:
            query = query.eq("projects.instance_number", instance_number)
        if client_name:
            query = query.eq("projects.client_name", client_name)

        result = query.order("created_at", desc=True).execute()

        versions = []
        for row in result.data or []:
            project = row.pop("projects", {})
            versions.append({
                "id": row["id"],
                "project_id": row["project_id"],
                "version_number": row["version_number"],
                "language_code": row["language_code"],
                "country_codes": row["country_codes"],
                "csv_storage_path": row.get("csv_storage_path"),
                "metadata_storage_path": row.get("metadata_storage_path"),
                "created_at": row["created_at"],
                "instance_number": project.get("instance_number"),
                "client_name": project.get("client_name"),
            })
        return versions

    def get_version(self, version_id: str) -> Optional[Dict]:
        result = (
            self._client.table("versions")
            .select("*, projects(consultant_email, instance_number, client_name)")
            .eq("id", version_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_version(self, version_id: str) -> None:
        self._client.table("versions").delete().eq("id", version_id).execute()

    def delete_project_if_empty(self, project_id: str) -> None:
        versions = (
            self._client.table("versions")
            .select("id")
            .eq("project_id", project_id)
            .limit(1)
            .execute()
        )
        if not versions.data:
            self._client.table("projects").delete().eq("id", project_id).execute()
