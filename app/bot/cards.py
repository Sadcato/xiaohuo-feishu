from typing import Dict, Any

def create_group_selection_card() -> Dict[str, Any]:
    """
    创建群组选择卡片，让用户选择要加入的群组类型
    
    Returns:
        Dict: 群组选择卡片内容
    """
    return {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "群组类型选择"
            },
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "请选择您想加入的群组类型："
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "选手群"
                        },
                        "type": "primary",
                        "value": {
                            "type": "group_selection",
                            "group_type": "player"
                        }
                    },
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "评委群"
                        },
                        "type": "primary",
                        "value": {
                            "type": "group_selection",
                            "group_type": "judge"
                        }
                    }
                ]
            },
            {
                "tag": "hr"
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "lark_md",
                        "content": "选择后，请根据提示发送您的二维码进行验证。"
                    }
                ]
            }
        ]
    }

def create_qr_request_card(group_type: str) -> Dict[str, Any]:
    group_name = "选手群" if group_type == "player" else "评委群"
    
    return {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "二维码验证"
            },
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"您选择了加入**{group_name}**\n\n请上传您的二维码进行验证。验证成功后，您将被自动添加到对应的群组。"
                }
            },
            {
                "tag": "hr"
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "lark_md",
                        "content": "请确保您的二维码清晰可见。如需重新选择群组类型，请回复「重新选择」。"
                    }
                ]
            }
        ]
    }

def create_verification_result_card(success: bool, message: str = "") -> Dict[str, Any]:

    if success:
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "验证成功"
                },
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**验证成功！**\n\n{message}"
                    }
                }
            ]
        }
    else:
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "验证失败"
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**验证失败**\n\n{message}\n\n如需重新选择群组类型，请回复「重新选择」。"
                    }
                }
            ]
        }
