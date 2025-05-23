import json
from typing import Any, Dict, Optional
import aioredis

from config.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
    REDIS_TIMEOUT,
    REDIS_PREFIX,
    USER_STATE_TTL,
    VERIFICATION_RESULT_TTL
)

# 用户状态枚举
class UserState:
    INITIAL = "initial"  # 初始状态
    WAITING_GROUP_SELECTION = "waiting_group_selection"  # 等待选择群组
    WAITING_QR_CODE = "waiting_qr_code"  # 等待提供二维码
    VERIFYING = "verifying"  # 验证中

# Redis
_redis_client = None

async def get_redis_client():
    """
    获取Redis客户端的单例实例
    
    Returns:
        Redis: Redis客户端实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
            password=REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=REDIS_TIMEOUT
        )
    return _redis_client

async def close_redis_client():
    """关闭Redis客户端连接"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

# 用户状态管理
async def get_user_state(user_id: str) -> Dict[str, Any]:
    """
    获取用户当前状态
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 用户状态信息
    """
    redis = await get_redis_client()
    key = f"{REDIS_PREFIX}user:{user_id}:state"
    state = await redis.get(key)
    
    if state:
        try:
            return json.loads(state)
        except json.JSONDecodeError:
            pass
    
    # 默认状态
    return {
        "state": UserState.INITIAL,
        "group_type": None,
        "qr_data": None
    }

async def set_user_state(user_id: str, state_data: Dict[str, Any]) -> bool:
    """
    设置用户状态
    
    Args:
        user_id: 用户ID
        state_data: 状态数据
        
    Returns:
        bool: 操作是否成功
    """
    redis = await get_redis_client()
    key = f"{REDIS_PREFIX}user:{user_id}:state"
    
    try:
        await redis.setex(
            key,
            USER_STATE_TTL,
            json.dumps(state_data)
        )
        return True
    except Exception as e:
        print(f"Error setting user state: {str(e)}")
        return False

async def reset_user_state(user_id: str) -> bool:
    """
    重置用户状态到初始状态
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 操作是否成功
    """
    return await set_user_state(user_id, {"state": UserState.INITIAL})

# 验证结果缓存
async def cache_verification_result(user_id: str, qr_data: str, group_type: str, result: bool) -> bool:
    """
    缓存验证结果
    
    Args:
        user_id: 用户ID
        qr_data: 二维码数据
        group_type: 群组类型
        result: 验证结果
        
    Returns:
        bool: 操作是否成功
    """
    redis = await get_redis_client()
    key = f"{REDIS_PREFIX}verification:{user_id}:{qr_data}:{group_type}"
    
    try:
        await redis.setex(
            key,
            VERIFICATION_RESULT_TTL,
            "1" if result else "0"
        )
        return True
    except Exception as e:
        print(f"Error caching verification result: {str(e)}")
        return False

async def get_cached_verification_result(user_id: str, qr_data: str, group_type: str) -> Optional[bool]:
    """
    获取缓存的验证结果
    
    Args:
        user_id: 用户ID
        qr_data: 二维码数据
        group_type: 群组类型
        
    Returns:
        Optional[bool]: 验证结果，None表示缓存中没有结果
    """
    redis = await get_redis_client()
    key = f"{REDIS_PREFIX}verification:{user_id}:{qr_data}:{group_type}"
    
    result = await redis.get(key)
    
    if result is not None:
        return result == "1"
    
    return None
