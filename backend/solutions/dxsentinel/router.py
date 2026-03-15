from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from backend.core.auth.dependencies import get_current_user
from .models import (
    UploadResponse, LanguagesResponse, CountriesResponse,
    EntitiesResponse, ProcessRequest, ProcessResponse,
    SplitRequest, SplitResponse,
)
from .services import FileService, ProcessingService, SplitService, MAX_UPLOAD_SIZE, MAX_CSV_UPLOAD_SIZE
from .project_service import ProjectService

router = APIRouter(prefix="/api/dxsentinel", tags=["dxsentinel"])

_project_service = ProjectService()


# ── File upload/management ───────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos XML")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Archivo excede el limite de 50MB")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Archivo vacio")

    file_id, _ = FileService.save_upload(content, file.filename)
    return UploadResponse(success=True, message="Archivo subido", file_id=file_id, filename=file.filename)


@router.get("/languages/{file_id}", response_model=LanguagesResponse)
async def extract_languages(file_id: str, user=Depends(get_current_user)):
    file_path = FileService.get_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        languages = ProcessingService.extract_languages(file_path)
        return LanguagesResponse(success=True, languages=languages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo idiomas: {str(e)}")


@router.get("/entities/{file_id}", response_model=EntitiesResponse)
async def extract_entities(file_id: str, user=Depends(get_current_user)):
    file_path = FileService.get_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        entities = ProcessingService.extract_entities(file_path)
        return EntitiesResponse(success=True, entities=entities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo entidades: {str(e)}")


@router.get("/countries/{file_id}", response_model=CountriesResponse)
async def extract_countries(file_id: str, user=Depends(get_current_user)):
    file_path = FileService.get_path(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        countries = ProcessingService.extract_countries(file_path)
        return CountriesResponse(success=True, countries=countries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo paises: {str(e)}")


@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str, user=Depends(get_current_user)):
    deleted = FileService.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"success": True, "message": "Archivo eliminado"}


# ── Process (Golden Record generation) ───────────────────────────────────

@router.post("/process", response_model=ProcessResponse)
async def process_files(request: ProcessRequest, user=Depends(get_current_user)):
    main_path = FileService.get_path(request.main_file_id)
    if not main_path:
        raise HTTPException(status_code=404, detail="Archivo principal no encontrado")

    csf_path = None
    if request.csf_file_id:
        csf_path = FileService.get_path(request.csf_file_id)
        if not csf_path:
            raise HTTPException(status_code=404, detail="Archivo CSF no encontrado")

    consultant_email = user.email

    try:
        # 1. Crear proyecto + version en Supabase
        project, version, version_number = _project_service.create_version(
            consultant_email=consultant_email,
            instance_number=request.instance_number,
            client_name=request.client_name,
            language_code=request.language_code,
            country_codes=request.country_codes,
        )

        # 2. Procesar archivos
        result = ProcessingService.process(
            main_file_path=main_path,
            csf_file_path=csf_path,
            language_code=request.language_code,
            country_codes=request.country_codes,
            excluded_entities=request.excluded_entities,
        )

        # 3. Actualizar version con paths de archivos
        _project_service.update_version_paths(
            version_id=version["id"],
            csv_path=result["output_file"],
            metadata_path=result["metadata_file"],
            report_path=result.get("report_file"),
            zip_path=result.get("zip_file"),
            field_count=result["field_count"],
        )

        return ProcessResponse(
            success=True,
            message="Procesamiento completado",
            field_count=result["field_count"],
            processing_time=result["processing_time"],
            download_id=result["download_id"],
            countries_processed=result.get("countries_processed"),
            version_number=version_number,
            instance_number=project["instance_number"],
            client_name=project["client_name"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando: {str(e)}")


@router.get("/download/{download_id}")
async def download_result(download_id: str, user=Depends(get_current_user)):
    zip_path = ProcessingService.get_download_path(download_id)
    if not zip_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
    )


# ── Projects & Versions ─────────────────────────────────────────────────

@router.get("/projects")
async def list_projects(user=Depends(get_current_user)):
    projects = _project_service.list_projects(user.email)
    return {"success": True, "projects": projects}


@router.get("/versions/{instance_number}/{client_name}")
async def list_versions(instance_number: str, client_name: str, user=Depends(get_current_user)):
    versions = _project_service.list_versions(
        consultant_email=user.email,
        instance_number=instance_number,
        client_name=client_name,
    )
    return {"success": True, "versions": versions}


# ── Split ────────────────────────────────────────────────────────────────

@router.post("/split/upload", response_model=UploadResponse)
async def split_upload(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext != "csv":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV")

    content = await file.read()
    if len(content) > MAX_CSV_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Archivo excede el limite de 100MB")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Archivo vacio")

    file_id, _ = SplitService.save_csv_upload(content, file.filename)
    return UploadResponse(success=True, message="Archivo subido", file_id=file_id, filename=file.filename)


@router.post("/split/process", response_model=SplitResponse)
async def split_process(request: SplitRequest, user=Depends(get_current_user)):
    # Obtener version y validar ownership (para metadata)
    version = _project_service.get_version(request.version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version no encontrada")

    project = version.get("projects", {})
    if project.get("consultant_email") != user.email:
        raise HTTPException(status_code=403, detail="No autorizado")

    metadata_path = version.get("metadata_storage_path")
    if not metadata_path:
        raise HTTPException(status_code=400, detail="Version sin metadata generada")

    from pathlib import Path as _Path
    if not _Path(metadata_path).exists():
        raise HTTPException(status_code=404, detail="Archivo metadata no encontrado en disco")

    # CSV subido por el usuario (golden record lleno)
    csv_path = FileService.get_path(request.csv_file_id)
    if not csv_path:
        raise HTTPException(status_code=404, detail="Archivo CSV no encontrado. Sube el golden record lleno primero.")

    try:
        result = SplitService.split(csv_path, _Path(metadata_path))
        return SplitResponse(
            success=True,
            message="Split completado",
            template_count=result["template_count"],
            processing_time=result["processing_time"],
            download_id=result["download_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en split: {str(e)}")


@router.get("/split/download/{download_id}")
async def split_download(download_id: str, user=Depends(get_current_user)):
    zip_path = ProcessingService.get_download_path(download_id)
    if not zip_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
    )
