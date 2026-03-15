from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from backend.core.auth.dependencies import get_current_user
from .models import (
    UploadResponse, LanguagesResponse, CountriesResponse,
    EntitiesResponse, ProcessRequest, ProcessResponse,
    SplitRequest, SplitResponse,
)
from .services import FileService, ProcessingService, SplitService, MAX_UPLOAD_SIZE, MAX_CSV_UPLOAD_SIZE

router = APIRouter(prefix="/api/dxsentinel", tags=["dxsentinel"])


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

    try:
        result = ProcessingService.process(
            main_file_path=main_path,
            csf_file_path=csf_path,
            language_code=request.language_code,
            country_codes=request.country_codes,
            excluded_entities=request.excluded_entities,
        )
        return ProcessResponse(
            success=True,
            message="Procesamiento completado",
            field_count=result["field_count"],
            processing_time=result["processing_time"],
            download_id=result["download_id"],
            countries_processed=result.get("countries_processed"),
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


@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str, user=Depends(get_current_user)):
    deleted = FileService.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {"success": True, "message": "Archivo eliminado"}


# ── Split endpoints ──────────────────────────────────────────────────────

@router.post("/split/upload", response_model=UploadResponse)
async def split_upload(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV o JSON")

    content = await file.read()
    if len(content) > MAX_CSV_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Archivo excede el limite de 100MB")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Archivo vacio")

    file_id, _ = SplitService.save_csv_upload(content, file.filename)
    return UploadResponse(success=True, message="Archivo subido", file_id=file_id, filename=file.filename)


@router.post("/split/process", response_model=SplitResponse)
async def split_process(request: SplitRequest, user=Depends(get_current_user)):
    csv_path = FileService.get_path(request.csv_file_id)
    if not csv_path:
        raise HTTPException(status_code=404, detail="Archivo CSV no encontrado")

    metadata_path = FileService.get_path(request.metadata_file_id)
    if not metadata_path:
        raise HTTPException(status_code=404, detail="Archivo metadata no encontrado")

    try:
        result = SplitService.split(csv_path, metadata_path)
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
