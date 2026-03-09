import os
import tempfile
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from backend.solutions.dxmodels.models import (
    ProcesamientoRequest,
    ProcesamientoCompletoRequest,
    ProcesamientoResponse,
)
from backend.solutions.dxmodels import services as proc

router = APIRouter(prefix="/api/dxmodels", tags=["dxmodels-api"])


@router.post("/process/cdm", response_model=ProcesamientoResponse)
async def process_cdm(request: ProcesamientoRequest):
    try:
        resultado = proc.procesar_cdm(request.xml_content, request.idiomas)
        return ProcesamientoResponse(success=True, resultado=resultado, message="CDM procesado exitosamente")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/sdm", response_model=ProcesamientoResponse)
async def process_sdm(request: ProcesamientoRequest):
    try:
        resultado = proc.procesar_sdm(request.xml_content, request.idiomas)
        return ProcesamientoResponse(success=True, resultado=resultado, message="SDM procesado exitosamente")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/csf", response_model=ProcesamientoResponse)
async def process_csf(request: ProcesamientoRequest):
    if not request.paises:
        raise HTTPException(status_code=400, detail="Se requiere al menos un pais para CSF")
    try:
        resultado = proc.procesar_csf(request.xml_content, request.paises, request.idiomas)
        return ProcesamientoResponse(success=True, resultado=resultado, message="CSF procesado exitosamente")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process/full")
async def process_full(request: ProcesamientoCompletoRequest):
    try:
        resultados = proc.procesar_data_model_completo(
            cdm_xml=request.cdm_xml,
            csf_cdm_xml=request.csf_cdm_xml,
            sdm_xml=request.sdm_xml,
            csf_sdm_xml=request.csf_sdm_xml,
            paises=request.paises,
            idiomas=request.idiomas,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            zip_path = tmp.name

        with zipfile.ZipFile(zip_path, "w") as zf:
            for nombre, contenido in resultados.items():
                if contenido:
                    zf.writestr(f"{nombre}_depurado.xml", contenido)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="data_models_depurados.zip",
            background=BackgroundTask(os.unlink, zip_path),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
