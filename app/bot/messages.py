"""
Message utilities for the Feishu bot.
This module handles sending messages to users through the Feishu API.
"""
import json
import uuid
from typing import Optional, Dict, Any

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from utils.lark_client import get_lark_client
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
    client = get_lark_client()
    
    # 准备消息内容
    if message_type == "text":
        content_dict = {"text": content}
        content = json.dumps(content_dict)
    
    # 确定接收ID类型
    receive_id_type = "chat_id" if is_chat_id else "open_id"
    
    # 构造请求对象
    request = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receiver_id)
            .msg_type(message_type)
            .content(content)
            .uuid(str(uuid.uuid4()))
            .build()) \
        .build()
    
    try:
        # 发起请求
        response = client.im.v1.message.create(request)
        
        # 处理响应
        if response.success():
            return {
                "code": 0,
                "data": response.data,
                "msg": "success"
            }
        else:
            print(f"Error sending message: code={response.code}, msg={response.msg}")
            return {
                "code": response.code,
                "msg": response.msg,
                "error": True
            }
    except Exception as e:
        # 记录错误并继续（不让消息错误打断流程）
        print(f"Exception sending message: {str(e)}")
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
    client = get_lark_client()
    
    # 确定接收ID类型
    receive_id_type = "chat_id" if is_chat_id else "open_id"
    
    # 将卡片内容转换为JSON字符串
    card_content_str = json.dumps(card_content)
    
    # 构造请求对象
    request = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receiver_id)
            .msg_type("interactive")
            .content(card_content_str)
            .uuid(str(uuid.uuid4()))
            .build()) \
        .build()
    
    try:
        # 发起请求
        response = client.im.v1.message.create(request)
        
        # 处理响应
        if response.success():
            return {
                "code": 0,
                "data": response.data,
                "msg": "success"
            }
        else:
            print(f"Error sending card message: code={response.code}, msg={response.msg}")
            return {
                "code": response.code,
                "msg": response.msg,
                "error": True
            }
    except Exception as e:
        # 记录错误并继续
        print(f"Exception sending card message: {str(e)}")
        return {"error": str(e)}

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
