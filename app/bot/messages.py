"""
Message utilities for the Feishu bot.
This module handles sending messages to users through the Feishu API.
"""
import json
import httpx
from typing import Optional, Dict, Any

from config.config import FEISHU_SEND_MESSAGE_URL
from utils.authentication import get_tenant_access_token
from app.bot.cards import (
    create_group_selection_card,
    create_qr_request_card,
    create_verification_result_card
)

async def send_message(
    receiver_id: str, 
    content: str, 
    message_type: str = "text",
    is_chat_id: bool = False
) -> Dict[str, Any]:
    """
    Send a message to a user or chat through Feishu API.
    
    Args:
        receiver_id: ID of the message receiver (open_id or chat_id)
        content: Message content
        message_type: Type of message, default is "text"
        is_chat_id: Whether the receiver_id is a chat_id
        
    Returns:
        Dict: Response from Feishu API
    """
    # Get access token
    token = await get_tenant_access_token()
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Prepare message content
    message_content = content
    if message_type == "text":
        message_content = json.dumps({"text": content})
    
    # Prepare request data
    data = {
        "msg_type": message_type,
        "content": message_content
    }
    
    # Set the receiver ID based on type
    if is_chat_id:
        data["chat_id"] = receiver_id
    else:
        data["open_id"] = receiver_id
    
    # Send the message
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FEISHU_SEND_MESSAGE_URL,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # Log the error and continue (don't let message errors break the flow)
        print(f"Error sending message: {str(e)}")
        return {"error": str(e)}

async def send_card_message(
    receiver_id: str,
    card_content: Dict[str, Any],
    is_chat_id: bool = False
) -> Dict[str, Any]:
    """
    Send an interactive card message to a user or chat.
    
    Args:
        receiver_id: ID of the message receiver (open_id or chat_id)
        card_content: Interactive card content in Feishu card format
        is_chat_id: Whether the receiver_id is a chat_id
        
    Returns:
        Dict: Response from Feishu API
    """
    return await send_message(
        receiver_id,
        json.dumps(card_content),
        message_type="interactive",
        is_chat_id=is_chat_id
    )

async def send_group_selection_card(receiver_id: str) -> Dict[str, Any]:
    """
    发送群组选择卡片
    
    Args:
        receiver_id: 接收者ID (open_id)
        
    Returns:
        Dict: 飞书API响应
    """
    card_content = create_group_selection_card()
    return await send_card_message(receiver_id, card_content)

async def send_qr_request(receiver_id: str, group_type: str) -> Dict[str, Any]:
    """
    发送二维码请求卡片
    
    Args:
        receiver_id: 接收者ID (open_id)
        group_type: 群组类型
        
    Returns:
        Dict: 飞书API响应
    """
    card_content = create_qr_request_card(group_type)
    return await send_card_message(receiver_id, card_content)

async def send_verification_result(
    receiver_id: str, 
    success: bool, 
    message: str = ""
) -> Dict[str, Any]:
    """
    发送验证结果卡片
    
    Args:
        receiver_id: 接收者ID (open_id)
        success: 验证是否成功
        message: 额外消息
        
    Returns:
        Dict: 飞书API响应
    """
    card_content = create_verification_result_card(success, message)
    return await send_card_message(receiver_id, card_content)
