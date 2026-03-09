from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.auth.dependencies import get_current_user
from backend.hub.registry import get_solutions

router = APIRouter(tags=["hub"])
templates = Jinja2Templates(directory="frontend/templates")
templates.env.globals["get_solutions"] = get_solutions


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("hub/dashboard.html", {
        "request": request,
        "solutions": get_solutions(),
        "user": user,
    })
