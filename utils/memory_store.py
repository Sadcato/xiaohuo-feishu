"""
内存存储模块，替代Redis用于简单状态管理。
由于二维码只有一分钟有效期，使用内存存储足够满足需求。
"""
from typing import Dict, Any, Optional
from enum import Enum
import time
import logging
import json

# 配置日志
logger = logging.getLogger('xiaohuo-bot')

class UserState(Enum):
    """用户状态枚举"""
    INITIAL = "initial"                # 初始状态
    WAITING_GROUP_SELECTION = "waiting_group_selection"  # 等待选择群组
    WAITING_QR_CODE = "waiting_qr_code"  # 等待提供二维码
    VERIFYING = "verifying"            # 验证中

# 内存存储
_user_states = {}  # 用户ID -> 状态数据
_state_expiry = 60 * 5  # 状态过期时间（5分钟）

async def get_user_state(user_id: str) -> Dict[str, Any]:
    """
    获取用户状态
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 用户状态数据
    """
    # 检查是否存在且未过期
    current_time = time.time()
    state_data = _user_states.get(user_id, {})
    
    if state_data and state_data.get('expire_at', 0) < current_time:
        # 状态已过期，删除并返回初始状态
        if user_id in _user_states:
            del _user_states[user_id]
        return {"state": UserState.INITIAL.value}
    
    # 返回状态，如果不存在则返回初始状态
    return state_data or {"state": UserState.INITIAL.value}

async def set_user_state(user_id: str, state_data: Dict[str, Any]) -> bool:
    """
    设置用户状态
    
    Args:
        user_id: 用户ID
        state_data: 状态数据
        
    Returns:
        bool: 设置是否成功
    """
    # 设置过期时间
    current_time = time.time()
    state_data['expire_at'] = current_time + _state_expiry
    
    # 保存状态
    _user_states[user_id] = state_data
    return True

async def reset_user_state(user_id: str) -> bool:
    """
    重置用户状态
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 重置是否成功
    """
    if user_id in _user_states:
        del _user_states[user_id]
    return True

# 定期清理过期状态
def cleanup_expired_states():
    """清理过期的用户状态"""
    current_time = time.time()
    expired_users = [
        user_id for user_id, data in _user_states.items()
        if data.get('expire_at', 0) < current_time
    ]
    
    for user_id in expired_users:
        del _user_states[user_id]
    
    if expired_users:
        logger.info(f"已清理 {len(expired_users)} 个过期用户状态")

# 验证结果缓存
_verification_cache = {}
_verification_cache_expiry = 60  # 缓存过期时间（秒）

async def cache_verification_result(user_id: str, qr_data: str, group_type: str, result: bool) -> bool:
    """
    缓存验证结果
    
    Args:
        user_id: 用户ID
        qr_data: 二维码数据
        group_type: 群组类型
        result: 验证结果
        
    Returns:
        bool: 缓存是否成功
    """
    key = f"{user_id}:{qr_data}:{group_type}"
    _verification_cache[key] = {
        "result": result,
        "expire_at": time.time() + _verification_cache_expiry
    }
    return True

async def get_cached_verification_result(user_id: str, qr_data: str, group_type: str) -> Optional[bool]:
    """
    获取缓存的验证结果
    
    Args:
        user_id: 用户ID
        qr_data: 二维码数据
        group_type: 群组类型
        
    Returns:
        Optional[bool]: 验证结果，None表示缓存不存在或已过期
    """
    key = f"{user_id}:{qr_data}:{group_type}"
    cache_data = _verification_cache.get(key)
    
    if not cache_data:
        return None
        
    # 检查是否过期
    if cache_data.get("expire_at", 0) < time.time():
        # 过期，删除缓存
        if key in _verification_cache:
            del _verification_cache[key]
        return None
    
    return cache_data.get("result")

# 模拟关闭连接的函数，保持接口兼容
async def close_memory_store():
    """模拟关闭存储连接，实际只是清空内存"""
    _user_states.clear()
    _verification_cache.clear()
    return True
