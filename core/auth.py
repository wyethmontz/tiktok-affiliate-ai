"""Backend authentication using Supabase JWT tokens."""
from fastapi import Header, HTTPException
from core.db import supabase


async def get_current_user(authorization: str = Header(default="")):
    """FastAPI dependency that validates the Supabase JWT token.

    Usage:
        @app.get("/protected")
        def protected_route(user=Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.replace("Bearer ", "")

    try:
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
