"""
API verification client.
This module handles verification through the external API.
"""
import httpx
from typing import Dict, Any, Optional
import json

from config.config import (
    API_VERIFICATION_ENABLED,
    API_ENDPOINT,
    API_TOKEN,
    EVENT_ID
)
from utils.memory_store import cache_verification_result, get_cached_verification_result

async def verify_user_permission(user_id: str, qr_data: str, group_type: str) -> Dict[str, Any]:
    """
    Args:
        user_id: 用户ID（open_id）
        qr_data: 二维码扫描结果
        group_type: 群组类型（"player"或"judge"）
        
    Returns:
        Dict: 验证结果，包含success和message字段
    """
    if not API_VERIFICATION_ENABLED:
        # 如果API验证未启用，默认返回成功
        return {"success": True, "message": "API验证未启用，默认允许加群"}
    
    # 先检查缓存中是否有结果
    cached_result = await get_cached_verification_result(user_id, qr_data, group_type)
    if cached_result is not None:
        if cached_result:
            return {"success": True, "message": "验证通过（来自缓存）"}
        else:
            return {"success": False, "message": "验证失败（来自缓存）"}
    
    # 调用外部API进行验证
    try:
        # 构建API请求
        url = f"{API_ENDPOINT}?eventId={EVENT_ID}&id={qr_data}"
        headers = {
            "Authorization": API_TOKEN,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=10.0
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_message = f"API返回错误代码: {response.status_code}"
                print(error_message)
                return {"success": False, "message": error_message}
            
            # 解析响应内容
            result = response.json()
            
            # 判断是否有权限
            has_permission = result.get("data", {}).get("status", False)
            
            # 缓存验证结果
            await cache_verification_result(user_id, qr_data, group_type, has_permission)
            
            if has_permission:
                return {"success": True, "message": "验证通过"}
            else:
                return {"success": False, "message": "验证失败，无权限加入该群组"}
    
    except Exception as e:
        error_message = f"API调用出错: {str(e)}"
        print(error_message)
        return {"success": False, "message": error_message}
