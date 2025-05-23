from typing import Dict, Any, List
import logging
import json

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from config.config import GROUP_TYPES
from utils.lark_client import get_lark_client
from utils.error_handler import log_api_error, format_permission_guide, check_permission_error

# 配置日志
logger = logging.getLogger('xiaohuo-bot')

async def add_user_to_group(user_id: str, group_type: str) -> Dict[str, Any]:
    """
    将用户添加到指定类型的群组
    
    Args:
        user_id: 用户ID (open_id)
        group_type: 群组类型 ("player", "judge")
        
    Returns:
        Dict: 操作结果
    """
    # 确认群组类型存在
    if group_type not in GROUP_TYPES:
        return {
            "success": False,
            "error": f"未知的群组类型: {group_type}"
        }
    
    # 获取该类型的群组ID列表
    chat_ids = GROUP_TYPES[group_type].get("chat_ids", [])
    if not chat_ids:
        return {
            "success": False,
            "error": f"没有配置{GROUP_TYPES[group_type]['name']}的ID，请在config中设置"
        }
    
    client = get_lark_client()
    
    # 记录添加结果
    results = []
    success_count = 0
    
    # 遍历目标群组，将用户添加到每个群组
    permission_error_detected = False
    permission_error_msg = ""
    
    for chat_id in chat_ids:
        try:
            # 构造请求对象
            request = CreateChatMembersRequest.builder() \
                .chat_id(chat_id) \
                .member_id_type("open_id") \
                .request_body(CreateChatMembersRequestBody.builder()
                    .id_list([user_id])
                    .build()) \
                .build()

            # 发起请求
            logger.info(f"添加用户 {user_id} 到群组 {chat_id} ({GROUP_TYPES[group_type]['name']})")
            response = client.im.v1.chat_members.create(request)
            
            # 处理响应
            if response.success():
                success_count += 1
                results.append({"chat_id": chat_id, "success": True})
                logger.info(f"成功添加用户到群组 {chat_id}")
            else:
                # 检查是否是权限错误
                logger.warning(f"添加用户到群组失败: code={response.code}, msg={response.msg}")
                
                if hasattr(response, 'raw') and hasattr(response.raw, 'content'):
                    try:
                        error_data = json.loads(response.raw.content)
                        is_permission_error, error_detail = check_permission_error(error_data)
                        
                        if is_permission_error:
                            permission_error_detected = True
                            permission_error_msg = error_detail
                            logger.error(f"权限错误: {error_detail}")
                    except Exception as parse_err:
                        logger.error(f"解析错误响应失败: {parse_err}")
                
                results.append({
                    "chat_id": chat_id, 
                    "success": False,
                    "error": response.msg,
                    "code": response.code
                })
        
        except Exception as e:
            error_result = log_api_error("add_user_to_group", e, {"chat_id": chat_id, "user_id": user_id})
            
            # 检查是否是权限错误
            if error_result.get("is_permission_error", False):
                permission_error_detected = True
                permission_error_msg = error_result.get("error", str(e))
            
            results.append({
                "chat_id": chat_id,
                "success": False,
                "error": str(e)
            })
    
    # 整体操作结果
    group_name = GROUP_TYPES[group_type]["name"]
    
    # 处理权限错误情况，提供详细指导
    if permission_error_detected:
        # 生成权限指导信息
        guide = format_permission_guide(permission_error_msg)
        error_message = f"添加到{group_name}失败：检测到权限问题，请联系管理员。\n\n【技术详情】\n{permission_error_msg}\n\n【解决指南】\n{guide}"
        
        logger.error(f"权限错误导致无法添加用户: {permission_error_msg}")
        
        return {
            "success": False,
            "error": error_message,
            "is_permission_error": True,
            "details": results
        }
    
    # 正常结果处理
    if success_count == len(chat_ids):
        return {
            "success": True,
            "message": f"您已成功加入{group_name}！"
        }
    elif success_count > 0:
        return {
            "success": True,
            "message": f"您已部分加入{group_name}，成功加入了{success_count}/{len(chat_ids)}个群组",
            "details": results
        }
    else:
        return {
            "success": False,
            "error": f"无法将您添加到{group_name}，请联系管理员",
            "details": results
        }
