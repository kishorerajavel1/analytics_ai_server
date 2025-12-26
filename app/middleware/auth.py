from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request, status


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for OPTIONS and /auth routes
        if request.method == "OPTIONS" or request.url.path.startswith("/auth/demo-login") or request.url.path.startswith("/health"):
            return await call_next(request)
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth header is missing or invalid!")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth header format is invalid")

        token = auth_header.split(" ")[1]

        supabase_client = request.app.state.db_manager.client

        try:
            user = supabase_client.auth.get_user(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        request.state.user = user
        request.state.user_id = user.user.id

        return await call_next(request)
