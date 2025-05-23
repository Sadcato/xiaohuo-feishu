import httpx
from typing import Dict, Any

from config.config import (
    FEISHU_BASE_URL,
    FEISHU_ADD_USER_TO_GROUP_URL,
    GROUP_TYPES
)
from utils.authentication import get_tenant_access_token

async def add_user_to_group(user_id: str, group_type: str) -> Dict[str, Any]:
    

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
    
    token = await get_tenant_access_token()
    
    # 记录添加结果
    results = []
    success_count = 0
    
    # 遍历目标群组，将用户添加到每个群组
    for chat_id in chat_ids:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{FEISHU_ADD_USER_TO_GROUP_URL}/{chat_id}/members",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    json={
                        "id_list": [user_id],
                        "member_type": "user"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == 0:
                    success_count += 1
                    results.append({"chat_id": chat_id, "success": True})
                else:
                    results.append({
                        "chat_id": chat_id, 
                        "success": False,
                        "error": result.get("msg", "未知错误")
                    })
        
        except Exception as e:
            results.append({
                "chat_id": chat_id,
                "success": False,
                "error": str(e)
            })
    
    # 整体操作结果
    group_name = GROUP_TYPES[group_type]["name"]
    
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
