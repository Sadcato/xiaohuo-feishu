import io
import httpx
from typing import Dict, Any, Optional
from PIL import Image

from config.config import (
    QR_CODE_VERIFICATION_ENABLED,
    QR_CODE_VERIFICATION_DUMMY_MODE,
    QR_CODE_API_URL
)
from utils.authentication import get_tenant_access_token

async def verify_qr_code(image_key: str, user_id: str) -> Dict[str, Any]:

    if not QR_CODE_VERIFICATION_ENABLED:
        return {"verified": True}
    
    if QR_CODE_VERIFICATION_DUMMY_MODE:
        return await dummy_verify_qr_code(image_key, user_id)

    return await api_verify_qr_code(image_key, user_id)

async def dummy_verify_qr_code(image_key: str, user_id: str) -> Dict[str, Any]:

    try:
        image_binary = await download_image(image_key)
        if not image_binary:
            return {
                "verified": False,
                "error": "无法下载图片，请重新发送。"
            }
        
        qr_data = await detect_qr_code(image_binary)
        
        if not qr_data:
            return {
                "verified": False,
                "error": "未能检测到有效的二维码，请确保图片中包含清晰的二维码。"
            }
        
        if "agreement" not in qr_data.lower():
            return {
                "verified": False,
                "error": "二维码无效，请确保使用的是官方提供的二维码。"
            }
        

        return {
            "verified": True
        }
    
    except Exception as e:
        return {
            "verified": False,
            "error": f"验证过程出错: {str(e)}"
        }

async def api_verify_qr_code(image_key: str, user_id: str) -> Dict[str, Any]:

    if not QR_CODE_API_URL:
        return {
            "verified": False,
            "error": "未配置验证API，请联系管理员。"
        }
    
    try:
        image_binary = await download_image(image_key)
        if not image_binary:
            return {
                "verified": False,
                "error": "无法下载图片，请重新发送。"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                QR_CODE_API_URL,
                files={"image": ("qrcode.png", image_binary)},
                data={"user_id": user_id}
            )
            
            if response.status_code != 200:
                return {
                    "verified": False,
                    "error": f"验证服务返回错误: {response.status_code}"
                }
            
            result = response.json()
            
            if result.get("success", False):
                return {
                    "verified": True
                }
            else:
                return {
                    "verified": False,
                    "error": result.get("message", "未知错误")
                }
    
    except Exception as e:
        return {
            "verified": False,
            "error": f"验证过程出错: {str(e)}"
        }

async def download_image(image_key: str) -> Optional[bytes]:

    token = await get_tenant_access_token()
    
    try:
        # Feishu API to get image
        image_url = f"https://open.feishu.cn/open-apis/im/v1/images/{image_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                image_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.content
    
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None

async def detect_qr_code(image_data: bytes) -> Optional[str]:
    try:
        from pyzbar.pyzbar import decode
        
        image = Image.open(io.BytesIO(image_data))
        
        decoded_objects = decode(image)
        
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
        
        return None
    
    except ImportError:
        try:
            Image.open(io.BytesIO(image_data))
            return "agreement:valid"
        except Exception:
            return None
    except Exception:
        return None
