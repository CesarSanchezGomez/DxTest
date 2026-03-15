"""Upload/download de archivos contra Supabase Storage."""

from __future__ import annotations

from pathlib import Path

from backend.core.auth.supabase_client import get_supabase_client

BUCKET_NAME = "dxsentinel-files"


class SupabaseStorageRepository:

    def __init__(self):
        self._bucket = get_supabase_client().storage.from_(BUCKET_NAME)

    def upload_file(
        self, storage_path: str, file_data: bytes,
        content_type: str = "application/octet-stream", upsert: bool = True,
    ) -> str:
        self._bucket.upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": content_type, "upsert": str(upsert).lower()},
        )
        return storage_path

    def upload_from_local(
        self, storage_path: str, local_path: Path,
        content_type: str = "application/octet-stream", upsert: bool = True,
    ) -> str:
        data = local_path.read_bytes()
        return self.upload_file(storage_path, data, content_type, upsert)

    def download_file(self, storage_path: str) -> bytes:
        return self._bucket.download(storage_path)

    def download_to_temp(self, storage_path: str, suffix: str = "") -> Path:
        import tempfile
        data = self.download_file(storage_path)
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(data)
        tmp.close()
        return Path(tmp.name)

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        result = self._bucket.create_signed_url(storage_path, expires_in)
        return result["signedURL"]

    def list_files(self, folder_path: str) -> list:
        return self._bucket.list(folder_path)

    def delete_file(self, storage_path: str) -> None:
        self._bucket.remove([storage_path])
