from fastapi import Request
from fastapi.responses import RedirectResponse


async def auth_guard(request: Request, call_next):
    public_prefixes = ("/auth/", "/static/", "/favicon.ico")
    if any(request.url.path.startswith(p) for p in public_prefixes):
        return await call_next(request)

    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/auth/login", status_code=302)

    return await call_next(request)
