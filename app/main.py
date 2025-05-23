import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config.config import (
    HOST, PORT, DEBUG, 
    BOT_EVENT_CALLBACK_PATH
)
from app.bot.handlers import handle_bot_event
from utils.authentication import verify_feishu_request
from utils.redis_client import close_redis_client

app = FastAPI(
    title="小火机器人 API",
    description="小火飞书机器人API，用于群组验证和管理",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_client()

@app.get("/")
async def root():
    return {"status": "ok", "message": "小火机器人API正在运行"}

@app.post(BOT_EVENT_CALLBACK_PATH)
async def bot_event(request: Request, authenticated: bool = Depends(verify_feishu_request)):
    if not authenticated:
        pass
    event_data = await request.json()
    return await handle_bot_event(event_data)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
