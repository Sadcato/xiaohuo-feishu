import uvicorn
import time
import threading
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.config import (
    HOST, PORT, DEBUG, 
    BOT_EVENT_CALLBACK_PATH
)
from app.bot.handlers import handle_bot_event
from utils.authentication import verify_feishu_request
from utils.memory_store import close_memory_store, cleanup_expired_states

# 配置日志
logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('xiaohuo-bot')

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

# 后台线程：定期清理过期状态
cleanup_thread = None
shutdown_flag = False

def cleanup_thread_func():
    global shutdown_flag
    while not shutdown_flag:
        try:
            cleanup_expired_states()
        except Exception as e:
            logger.error(f"状态清理出错: {e}")
        # 每60秒清理一次
        time.sleep(60)

@app.on_event("startup")
async def startup_event():
    global cleanup_thread, shutdown_flag
    # 重置关闭标志
    shutdown_flag = False
    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_thread_func, daemon=True)
    cleanup_thread.start()
    logger.info("应用已启动，状态清理线程已开始运行")

@app.on_event("shutdown")
async def shutdown_event():
    global shutdown_flag
    # 设置关闭标志
    shutdown_flag = True
    # 关闭内存存储
    await close_memory_store()
    logger.info("应用已关闭，资源已清理")

@app.get("/")
async def root():
    return {"status": "ok", "message": "小火机器人API正在运行"}

@app.post(BOT_EVENT_CALLBACK_PATH)
async def bot_event(request: Request, authenticated: bool = Depends(verify_feishu_request)):
    # 处理认证失败的情况
    if not authenticated:
        raise HTTPException(status_code=401, detail="未授权的请求")
        
    # 解析事件数据
    event_data = await request.json()
    return await handle_bot_event(event_data)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
