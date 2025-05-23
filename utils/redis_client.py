"""Redis客户端兼容层
此模块仅作为兼容层，将所有Redis相关调用重定向到memory_store.py
"""

# 从内存存储模块中导入所有必要函数和类
from utils.memory_store import (
    UserState,
    get_user_state,
    set_user_state,
    reset_user_state,
    cache_verification_result,
    get_cached_verification_result,
    close_memory_store as close_redis_client
)

import logging

# 配置日志
logger = logging.getLogger('xiaohuo-bot')

# 记录兼容层被加载
logger.info("使用内存存储替代Redis服务")
