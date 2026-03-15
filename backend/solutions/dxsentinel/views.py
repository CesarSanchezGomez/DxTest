from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.auth.dependencies import get_current_user
from backend.hub.registry import get_solutions

router = APIRouter(prefix="/dxsentinel", tags=["dxsentinel"])
templates = Jinja2Templates(directory="frontend/templates")
templates.env.globals["get_solutions"] = get_solutions


@router.get("/", response_class=HTMLResponse)
async def dx_sentinel_home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxsentinel/home.html", {
        "request": request,
        "user": user,
    })


@router.get("/upload", response_class=HTMLResponse)
async def dx_sentinel_upload(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxsentinel/upload.html", {
        "request": request,
        "user": user,
    })


@router.get("/split", response_class=HTMLResponse)
async def dx_sentinel_split(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxsentinel/split.html", {
        "request": request,
        "user": user,
    })
