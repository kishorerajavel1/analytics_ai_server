from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# from app.schemas.chatSchemas import ChatSchema
# from loguru import logger

from app.managers.db import DBManager
from fastapi import HTTPException, Request

from app.services.analytics_generation import AnalyticsGenerationService, DatabaseInfo
from app.services.db_chat import DBChatService, ChatInput

router = APIRouter()


# @router.post("/chat")
# async def chat(request: Request, payload: ChatRequest):
#     try:
#         db_chat: DBChatService = DBChatService()
#         logger.info(f"Chatting for user {request.state.user}")

#         result = db_chat.chat(request=payload)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


class AnalyticsRequest(BaseModel):
    db_info: DatabaseInfo
    dashboard_id: str


@router.post("/analytics")
async def analytics(request: Request, payload: AnalyticsRequest):
    try:
        db: DBManager = request.app.state.db_manager
        analytics_service: AnalyticsGenerationService = AnalyticsGenerationService()
        # logger.info(f"Chatting for user {request.state.user}")

        result = analytics_service.generateDashboardConfig(payload.db_info)

        if isinstance(result, list):
            for item in result:
                item["dashboard_id"] = payload.dashboard_id
                item["user_id"] = request.state.user_id
            db.client.table("dashboard_panels").insert(result).execute()
        else:
            raise HTTPException(
                status_code=500, detail="Generated configuration is not a list of panels")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify(payload: dict[str, str]):
    try:
        db_chat: DBChatService = DBChatService()
        result = db_chat.classify(payload["user_message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generateSQL")
async def generateSQL(payload: ChatInput):
    try:
        db_chat: DBChatService = DBChatService()
        result = db_chat.invoke(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stream")
async def stream_chat(request: Request, payload: ChatInput):
    try:
        assistant = DBChatService()
        return StreamingResponse(
            assistant.stream_response(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
