import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse

from backend.config import get_settings
from backend.core.auth.router import router as auth_router
from backend.core.middleware.auth_guard import auth_guard
from backend.hub.router import router as hub_router
from backend.solutions.dxmodels.views import router as dxmodels_views
from backend.solutions.dxmodels.router import router as dxmodels_api

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.middleware("http")(auth_guard)

app.include_router(auth_router)
app.include_router(hub_router)
app.include_router(dxmodels_views)
app.include_router(dxmodels_api)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    path = "frontend/static/images/favicon.ico"
    if os.path.exists(path):
        return FileResponse(path)
    return Response(status_code=204)
