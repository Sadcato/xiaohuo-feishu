"""
Lark SDK 客户端工具
提供飞书 API 的客户端实例和相关工具函数
"""
import os
import lark_oapi as lark
from config.config import FEISHU_APP_ID, FEISHU_APP_SECRET

# 缓存客户端实例
_lark_client = None

def get_lark_client():
    """
    获取 Lark 客户端实例（单例模式）
    
    Returns:
        lark.Client: Lark 客户端实例
    """
    global _lark_client
    
    if _lark_client is None:
        _lark_client = lark.Client.builder() \
            .app_id(FEISHU_APP_ID) \
            .app_secret(FEISHU_APP_SECRET) \
            .log_level(lark.LogLevel.INFO) \
            .build()
    
    return _lark_client
