from fastapi import Request, HTTPException, status
from backend.config import get_settings
from backend.core.auth.supabase_client import get_supabase_client

settings = get_settings()


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )

    try:
        supabase = get_supabase_client()
        result = supabase.auth.get_user(token)

        if not result or not result.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido"
            )

        email = result.user.email
        if not email.endswith(f"@{settings.allowed_domain}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo se permite acceso a usuarios de @{settings.allowed_domain}"
            )

        return result.user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
