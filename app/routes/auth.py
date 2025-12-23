from app.config import settings
from app.managers.db import DBManager
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.post("/demo-login")
async def demoLogin(request: Request):
    try:
        print(settings.DEMO_ACCOUNT_EMAIL)
        supabase_client = request.app.state.db_manager.client
        response = supabase_client.auth.sign_in_with_password({
            "email": settings.DEMO_ACCOUNT_EMAIL,
            "password": settings.DEMO_ACCOUNT_PASSWORD
        })

        if not response.session:
            raise HTTPException(status_code=401, detail="Demo login failed")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_in": response.session.expires_in,
            "user": response.user
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
