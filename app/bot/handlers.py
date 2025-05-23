"""
Event handlers for the Feishu bot.
This module contains the logic for handling different types of events from Feishu.
"""
import json
import base64
from fastapi import HTTPException
from typing import Dict, Any, Optional

from config.config import (
    WELCOME_MESSAGE,
    GROUP_SELECTION_MESSAGE,
    QR_REQUEST_MESSAGE,
    VERIFICATION_SUCCESS_MESSAGE,
    VERIFICATION_FAILURE_MESSAGE,
    GROUP_TYPES
)
from app.bot.messages import (
    send_message,
    send_group_selection_card,
    send_qr_request,
    send_verification_result
)
from app.qrcode.parser import download_image, extract_qr_code
from app.verification.api_client import verify_user_permission
from app.group.manager import add_user_to_group
from utils.redis_client import (
    get_user_state, 
    set_user_state,
    reset_user_state,
    UserState
)
from utils.lark_client import get_lark_client
from utils.error_handler import log_api_error
import logging

# 配置日志
logger = logging.getLogger('xiaohuo-bot')

async def handle_bot_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理来自飞书API的事件
    
    Args:
        event_data: 事件数据
        
    Returns:
        Dict: 返回给飞书的响应
    """
    # Challenge verification (required by Feishu for event subscription setup)
    if "challenge" in event_data:
        return {"challenge": event_data["challenge"]}
    
    # 提取事件类型
    event_type = event_data.get("header", {}).get("event_type", "")
    
    # 处理不同类型的事件
    if event_type == "im.message.receive_v1":
        return await handle_message_event(event_data)
    elif event_type == "im.chat.member.bot.added_v1":
        return await handle_bot_added_event(event_data)
    elif event_type == "im.message.action.v1":
        return await handle_card_action(event_data)
    
    # 未处理的事件类型的默认响应
    return {"code": 0, "msg": "success"}

async def handle_message_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理用户消息事件
    
    Args:
        event_data: 消息事件数据
        
    Returns:
        Dict: 表示成功的响应
    """
    message_data = event_data.get("event", {})
    message_type = message_data.get("message", {}).get("message_type")
    sender_id = message_data.get("sender", {}).get("sender_id", {}).get("open_id")
    
    if not sender_id:
        return {"code": 0, "msg": "success"}
    
    # 获取用户当前状态
    user_state = await get_user_state(sender_id)
    current_state = user_state.get("state", UserState.INITIAL)
    
    # 处理图片消息（可能包含二维码）
    if message_type == "image":
        # 只有当用户正在等待提供二维码时才处理图片
        if current_state == UserState.WAITING_QR_CODE:
            await handle_qr_code_image(message_data, sender_id, user_state)
        else:
            # 如果用户不在等待二维码的状态，提示选择群组类型
            await send_message(sender_id, "请先选择您要加入的群组类型。")
            await send_group_selection_card(sender_id)
            await set_user_state(sender_id, {"state": UserState.WAITING_GROUP_SELECTION})
    
    # 处理文本消息
    elif message_type == "text":
        content = json.loads(
            base64.b64decode(
                message_data.get("message", {}).get("content", "")
            ).decode("utf-8")
        )
        text = content.get("text", "").strip()
        
        # 处理重新选择的请求
        if text in ["重新选择", "重置", "reset"]:
            await reset_user_state(sender_id)
            await send_message(sender_id, "已重置。" + GROUP_SELECTION_MESSAGE)
            await send_group_selection_card(sender_id)
            await set_user_state(sender_id, {"state": UserState.WAITING_GROUP_SELECTION})
            return {"code": 0, "msg": "success"}
        
        # 根据用户当前状态处理文本消息
        if current_state == UserState.INITIAL:
            # 初始状态，发送群组选择卡片
            await send_message(sender_id, WELCOME_MESSAGE)
            await send_group_selection_card(sender_id)
            await set_user_state(sender_id, {"state": UserState.WAITING_GROUP_SELECTION})
        
        elif current_state == UserState.WAITING_GROUP_SELECTION:
            # 尝试从文本中识别群组类型
            group_type = None
            if "选手" in text or "player" in text.lower():
                group_type = "player"
            elif "评委" in text or "judge" in text.lower():
                group_type = "judge"
            
            if group_type:
                # 用户选择了群组类型，更新状态并请求二维码
                await set_user_state(sender_id, {
                    "state": UserState.WAITING_QR_CODE,
                    "group_type": group_type
                })
                await send_qr_request(sender_id, group_type)
            else:
                # 无法识别群组类型，再次发送选择卡片
                await send_message(sender_id, "请选择您要加入的群组类型：")
                await send_group_selection_card(sender_id)
        
        elif current_state == UserState.WAITING_QR_CODE:
            # 提醒用户发送二维码
            group_type = user_state.get("group_type")
            await send_message(sender_id, "请发送您的二维码图片进行验证。")
            await send_qr_request(sender_id, group_type)
        
        else:
            # 未知状态，重置
            await reset_user_state(sender_id)
            await send_message(sender_id, "请选择您要加入的群组类型：")
            await send_group_selection_card(sender_id)
    
    return {"code": 0, "msg": "success"}

async def handle_card_action(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理卡片交互事件
    
    Args:
        event_data: 事件数据
        
    Returns:
        Dict: 表示成功的响应
    """
    action = event_data.get("event", {})
    open_id = action.get("operator", {}).get("operator_id", {}).get("open_id")
    action_value = json.loads(action.get("action", {}).get("value", "{}"))
    
    if not open_id:
        return {"code": 0, "msg": "success"}
    
    # 处理群组选择操作
    if action_value.get("type") == "group_selection":
        group_type = action_value.get("group_type")
        
        if group_type in GROUP_TYPES:
            # 更新用户状态
            await set_user_state(open_id, {
                "state": UserState.WAITING_QR_CODE,
                "group_type": group_type
            })
            
            # 发送二维码请求
            await send_qr_request(open_id, group_type)
        else:
            await send_message(open_id, f"未知的群组类型：{group_type}")
    
    return {"code": 0, "msg": "success"}

async def handle_qr_code_image(message_data: Dict[str, Any], sender_id: str, user_state: Dict[str, Any]) -> None:
    """
    处理可能包含二维码的图片
    
    Args:
        message_data: 包含图片的消息数据
        sender_id: 发送者ID
        user_state: 用户当前状态
    """
    group_type = user_state.get("group_type")
    if not group_type:
        await send_message(sender_id, "请先选择您要加入的群组类型。")
        await send_group_selection_card(sender_id)
        await set_user_state(sender_id, {"state": UserState.WAITING_GROUP_SELECTION})
        return
    
    try:
        # 从消息中获取图片key
        message = message_data.get("message", {})
        content = json.loads(base64.b64decode(message.get("content", "")).decode("utf-8"))
        image_key = content.get("image_key", "")
        
        if not image_key:
            await send_message(sender_id, "无法识别图片，请重新发送二维码。")
            return
        
        # 更新用户状态为验证中
        await set_user_state(sender_id, {
            "state": UserState.VERIFYING,
            "group_type": group_type
        })
        
        # 下载并处理图片
        image_data = await download_image(image_key)
        if not image_data:
            await send_verification_result(
                sender_id, 
                False, 
                "无法下载图片，请重新发送清晰的二维码。"
            )
            await set_user_state(sender_id, {
                "state": UserState.WAITING_QR_CODE,
                "group_type": group_type
            })
            return
        
        # 提取二维码内容
        qr_data = await extract_qr_code(image_data)
        if not qr_data:
            await send_verification_result(
                sender_id,
                False,
                "无法识别二维码，请确保图片中包含清晰的二维码。"
            )
            await set_user_state(sender_id, {
                "state": UserState.WAITING_QR_CODE,
                "group_type": group_type
            })
            return
        
        # 调用API验证权限
        verification_result = await verify_user_permission(sender_id, qr_data, group_type)
        
        if verification_result.get("success", False):
            # 验证成功，添加用户到群组
            logger.info(f"用户 {sender_id} 验证成功，准备添加到{group_type}群组")
            group_result = await add_user_to_group(sender_id, group_type)
            
            if group_result.get("success", False):
                # 添加群组成功
                message = group_result.get("message", "")
                logger.info(f"用户 {sender_id} 成功加入群组")
                await send_verification_result(
                    sender_id,
                    True,
                    message
                )
                # 重置用户状态
                await reset_user_state(sender_id)
            else:
                # 添加群组失败
                error = group_result.get("error", "未知错误")
                
                # 检查是否是权限错误
                if group_result.get("is_permission_error", False):
                    logger.error(f"检测到权限错误: {error}")
                    
                    # 简化错误消息给用户，便于理解
                    user_friendly_error = "由于飞书权限限制，无法将您添加到群组。\n\n请联系管理员检查机器人权限设置。"
                    
                    # 对管理员发送具体错误日志，这里我们使用日志记录
                    admin_error = f"权限错误: {error}"
                    logger.error(admin_error)
                    
                    await send_verification_result(
                        sender_id,
                        False,
                        user_friendly_error
                    )
                else:
                    # 非权限错误
                    await send_verification_result(
                        sender_id,
                        False,
                        f"验证成功，但添加群组失败: {error}"
                    )
                
                # 保持当前状态，以便用户可以重试
                await set_user_state(sender_id, {
                    "state": UserState.WAITING_QR_CODE,
                    "group_type": group_type
                })
        else:
            # 验证失败
            error_message = verification_result.get("message", "验证失败")
            await send_verification_result(
                sender_id,
                False,
                error_message
            )
            # 保持当前状态，以便用户可以重试
            await set_user_state(sender_id, {
                "state": UserState.WAITING_QR_CODE,
                "group_type": group_type
            })
    
    except Exception as e:
        # 处理异常
        await send_verification_result(
            sender_id,
            False,
            f"处理二维码时出错: {str(e)}，请重新发送。"
        )
        # 恢复到等待二维码的状态
        await set_user_state(sender_id, {
            "state": UserState.WAITING_QR_CODE,
            "group_type": group_type
        })

async def handle_bot_added_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理机器人被添加到聊天的事件
    
    Args:
        event_data: 事件数据
        
    Returns:
        Dict: 表示成功的响应
    """
    chat_id = event_data.get("event", {}).get("chat_id")
    
    if chat_id:
        # 发送欢迎消息到聊天
        await send_message(chat_id, WELCOME_MESSAGE, is_chat_id=True)
    
    return {"code": 0, "msg": "success"}
