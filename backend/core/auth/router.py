import time

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from backend.core.auth.supabase_client import get_supabase_client
from backend.core.auth.dependencies import get_current_user
from backend.config import get_settings

ACCESS_TOKEN_MAX_AGE = 3600

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="frontend/templates")
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "supabase_url": settings.supabase_url,
        "supabase_key": settings.supabase_key,
    })


@router.get("/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    return templates.TemplateResponse("auth/callback.html", {
        "request": request,
        "allowed_domain": settings.allowed_domain,
    })


@router.post("/session")
async def create_session(
        access_token: str = Form(...),
        refresh_token: str = Form(None),
        email: str = Form(...),
):
    if not access_token or not email:
        raise HTTPException(status_code=400, detail="Token o email no proporcionado")

    if not email.endswith(f"@{settings.allowed_domain}"):
        raise HTTPException(
            status_code=403,
            detail=f"Solo se permite acceso a usuarios de @{settings.allowed_domain}",
        )

    response = RedirectResponse(url="/", status_code=303)

    expires_at = int(time.time()) + ACCESS_TOKEN_MAX_AGE

    cookie_defaults = dict(httponly=True, secure=True, samesite="lax")
    response.set_cookie(key="access_token", value=access_token, max_age=ACCESS_TOKEN_MAX_AGE, **cookie_defaults)
    if refresh_token:
        response.set_cookie(key="refresh_token", value=refresh_token, max_age=604800, **cookie_defaults)
    response.set_cookie(key="session_expires_at", value=str(expires_at), max_age=ACCESS_TOKEN_MAX_AGE, httponly=False, secure=True, samesite="lax")

    return response


@router.get("/logout")
async def logout(request: Request):
    supabase = get_supabase_client()
    token = request.cookies.get("access_token")
    if token:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post("/refresh")
async def refresh_session(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No hay refresh token disponible")

    try:
        supabase = get_supabase_client()
        result = supabase.auth.refresh_session(refresh_token)

        if not result or not result.session:
            raise HTTPException(status_code=401, detail="No se pudo renovar la sesion")

        new_access = result.session.access_token
        new_refresh = result.session.refresh_token
        expires_at = int(time.time()) + ACCESS_TOKEN_MAX_AGE

        response = JSONResponse({"refreshed": True, "expires_at": expires_at})

        cookie_defaults = dict(httponly=True, secure=True, samesite="lax")
        response.set_cookie(key="access_token", value=new_access, max_age=ACCESS_TOKEN_MAX_AGE, **cookie_defaults)
        if new_refresh:
            response.set_cookie(key="refresh_token", value=new_refresh, max_age=604800, **cookie_defaults)
        response.set_cookie(key="session_expires_at", value=str(expires_at), max_age=ACCESS_TOKEN_MAX_AGE, httponly=False, secure=True, samesite="lax")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/user")
async def get_user_info(user=Depends(get_current_user)):
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at),
            "user_metadata": user.user_metadata,
        }
    }
