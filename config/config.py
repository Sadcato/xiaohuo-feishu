"""
Configuration settings for the Feishu bot application.
All configurable parameters are centralized here.
"""
import os
from dotenv import load_dotenv

# Try to load environment variables from .env file if it exists
load_dotenv()

# Feishu Bot Credentials
# 必须在环境变量中设置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# Feishu API Endpoints
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"
FEISHU_GET_TOKEN_URL = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
FEISHU_SEND_MESSAGE_URL = f"{FEISHU_BASE_URL}/im/v1/messages"
FEISHU_ADD_USER_TO_GROUP_URL = f"{FEISHU_BASE_URL}/im/v1/chats"  # /{chat_id}/members

# Bot Configuration
BOT_NAME = "小火验证机器人"
WELCOME_MESSAGE = "你好！我是小火验证机器人。请问您想加入哪一类群组？"
GROUP_SELECTION_MESSAGE = "请选择您想加入的群组类型："
VERIFICATION_SUCCESS_MESSAGE = "验证成功！您已被添加到群组。"
VERIFICATION_FAILURE_MESSAGE = "验证失败！您没有权限加入该群组。"
QR_REQUEST_MESSAGE = "请发送您的二维码进行验证。"

# 群组类型配置
GROUP_TYPES = {
    "player": {
        "name": "选手群",
        "description": "比赛选手交流群组",
        "chat_ids": [
            # 在这里填写选手群的chat_id列表
            # "oc_abcdefg123456"
        ]
    },
    "judge": {
        "name": "评委群",
        "description": "比赛评委交流群组",
        "chat_ids": [
            # 在这里填写评委群的chat_id列表
            # "oc_hijklmn789012"
        ]
    }
}

# API Verification Configuration
API_VERIFICATION_ENABLED = True
API_ENDPOINT = os.getenv("API_ENDPOINT", "")
API_TOKEN = os.getenv("API_TOKEN", "")
EVENT_ID = os.getenv("EVENT_ID", "")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "5"))  # Connection timeout in seconds
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "xiaohuo:")

# Cache TTLs (in seconds)
USER_STATE_TTL = 60 * 60  # 1 hour
VERIFICATION_RESULT_TTL = 60 * 60 * 24  # 24 hours

# Webhook Configuration
VERIFICATION_CALLBACK_PATH = "/api/bot/verification_callback"
BOT_EVENT_CALLBACK_PATH = "/api/bot/event_callback"
ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")  # For event subscription encryption

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
