"""
错误处理工具模块
包含错误识别、诊断和处理的通用功能
"""
import logging
import json
from typing import Dict, Any, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('xiaohuo-bot')

# 飞书API权限错误码映射
PERMISSION_ERROR_CODES = {
    # 通用权限错误
    10002: "权限校验失败",
    10020: "应用未获得授权，请检查应用权限配置",
    
    # 访问令牌相关
    99991663: "应用访问凭证已过期",
    99991664: "应用访问凭证无效",
    
    # 消息相关权限
    20002: "没有发送消息权限",
    22006: "没有获取图片资源权限",
    
    # 群组相关权限
    25002: "没有加入群聊权限",
    25003: "没有获取群信息权限",
    
    # 机器人相关
    22007: "机器人被禁用",
    22008: "机器人未加入群聊"
}

def check_permission_error(response_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    检查API响应是否包含权限错误
    
    Args:
        response_data: API响应数据
        
    Returns:
        Tuple[bool, Optional[str]]: (是否是权限错误, 错误描述)
    """
    code = response_data.get("code", 0)
    
    # 检查是否是已知的权限错误码
    if code in PERMISSION_ERROR_CODES:
        error_msg = PERMISSION_ERROR_CODES[code]
        logger.error(f"飞书API权限错误: {error_msg} (错误码: {code})")
        return True, f"{error_msg} (错误码: {code})"
    
    # 检查错误信息是否包含权限关键词
    msg = response_data.get("msg", "")
    if any(keyword in msg.lower() for keyword in ["权限", "permission", "access", "权利", "禁止", "拒绝"]):
        logger.error(f"可能的权限错误: {msg} (错误码: {code})")
        return True, f"可能的权限问题: {msg} (错误码: {code})"
    
    return False, None

def log_api_error(api_name: str, error: Exception, context: Dict[str, Any] = None):
    """
    记录API错误，并提供诊断信息
    
    Args:
        api_name: API名称
        error: 异常对象
        context: 上下文信息
    """
    if context is None:
        context = {}
    
    error_str = str(error)
    logger.error(f"API错误 [{api_name}]: {error_str}")
    
    # 尝试解析错误响应
    if hasattr(error, 'response') and getattr(error, 'response', None) is not None:
        response = getattr(error, 'response')
        try:
            if hasattr(response, 'text'):
                response_text = getattr(response, 'text', '{}')
                response_data = json.loads(response_text)
                
                is_permission_error, error_msg = check_permission_error(response_data)
                if is_permission_error:
                    return {
                        "success": False,
                        "error": error_msg,
                        "is_permission_error": True
                    }
                
                logger.error(f"API响应详情: {json.dumps(response_data, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"解析错误响应失败: {e}")
    
    # 检查错误字符串中是否包含权限关键词
    if any(keyword in error_str.lower() for keyword in ["权限", "permission", "access", "权利", "禁止", "拒绝"]):
        logger.error("检测到可能的权限问题，请检查应用权限配置")
        return {
            "success": False,
            "error": f"可能的权限问题: {error_str}",
            "is_permission_error": True
        }
    
    return {
        "success": False,
        "error": f"API错误: {error_str}",
        "is_permission_error": False
    }

def format_permission_guide(error_msg: str) -> str:
    """
    根据权限错误提供相应的指导信息
    
    Args:
        error_msg: 错误消息
        
    Returns:
        str: 权限指导信息
    """
    guide = "请在飞书开发者平台检查以下权限配置:\n"
    
    if "消息" in error_msg or "message" in error_msg.lower():
        guide += "- im:message (读取消息)\n"
        guide += "- im:message:send_as_bot (发送消息)\n"
    
    if "图片" in error_msg or "image" in error_msg.lower() or "resource" in error_msg.lower():
        guide += "- im:resource (读取资源)\n"
        guide += "- im:image (获取图片)\n"
    
    if "群" in error_msg or "chat" in error_msg.lower() or "成员" in error_msg:
        guide += "- im:chat (获取群信息)\n"
        guide += "- im:chat:member (读取群成员)\n"
        guide += "- im:chat:member:add (添加群成员)\n"
    
    guide += "\n请确保应用已发布且这些权限已获得审批。"
    return guide
