from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.auth.dependencies import get_current_user

router = APIRouter(prefix="/dx-sentinel", tags=["dx-sentinel"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def dx_sentinel_home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("solutions/dxsentinel/home.html", {
        "request": request,
        "user": user,
    })
