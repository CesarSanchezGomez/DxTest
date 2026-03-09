from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.auth.dependencies import get_current_user
from backend.hub.registry import get_solutions

router = APIRouter(prefix="/dxmodels", tags=["dxmodels"])
templates = Jinja2Templates(directory="frontend/templates")
templates.env.globals["get_solutions"] = get_solutions

INDIVIDUAL_PAGES = {
    "/cdm": {
        "title": "Corporate Data Model (CDM)",
        "data_model": "cdm",
        "require_countries": False,
    },
    "/csf-cdm": {
        "title": "CSF Corporate Data Model",
        "data_model": "csf_cdm",
        "require_countries": True,
    },
    "/sdm": {
        "title": "Succession Data Model (SDM)",
        "data_model": "sdm",
        "require_countries": False,
    },
    "/csf-sdm": {
        "title": "CSF Succession Data Model",
        "data_model": "csf_sdm",
        "require_countries": True,
    },
}


@router.get("/", response_class=HTMLResponse)
async def dxmodels_home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxmodels/home.html", {
        "request": request,
        "user": user,
    })


for _path, _config in INDIVIDUAL_PAGES.items():
    def _make_handler(cfg: dict):
        async def handler(request: Request, user=Depends(get_current_user)):
            return templates.TemplateResponse("solutions/dxmodels/individual.html", {
                "request": request,
                "user": user,
                **cfg,
            })
        return handler

    router.add_api_route(_path, _make_handler(_config), methods=["GET"])


@router.get("/full", response_class=HTMLResponse)
async def dxmodels_full(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxmodels/full.html", {
        "request": request,
        "user": user,
    })
