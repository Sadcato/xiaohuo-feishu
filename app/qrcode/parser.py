"""
QR code parser module.
This module handles extracting QR code content from images.
"""
import io
from typing import Optional
from PIL import Image

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from utils.lark_client import get_lark_client

async def download_image(image_key: str) -> Optional[bytes]:
    """
    从飞书下载图片
    
    Args:
        image_key: 飞书图片Key
        
    Returns:
        Optional[bytes]: 图片二进制数据，失败返回None
    """
    client = get_lark_client()
    
    try:
        # 构造请求对象
        request = GetImageRequest.builder() \
            .image_key(image_key) \
            .build()
        
        # 发起请求
        response = client.im.v1.image.get(request)
        
        # 处理响应
        if response.success():
            # 将文件对象读取为二进制数据
            return response.file.read()
        else:
            print(f"Error downloading image: code={response.code}, msg={response.msg}")
            return None
    
    except Exception as e:
        print(f"Exception downloading image: {str(e)}")
        return None

async def extract_qr_code(image_data: bytes) -> Optional[str]:
    """
    从图片中提取二维码内容
    
    Args:
        image_data: 图片二进制数据
        
    Returns:
        Optional[str]: 二维码内容，如果无法提取则返回None
    """
    try:
        # 首先尝试使用pyzbar库解析（速度更快，更准确）
        try:
            from pyzbar.pyzbar import decode
            
            # 使用PIL打开图片
            image = Image.open(io.BytesIO(image_data))
            
            # 解析图片中的二维码
            decoded_objects = decode(image)
            
            # 返回第一个解析到的二维码内容
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8')
        except ImportError:
            # 如果pyzbar不可用，尝试使用qrcode库（仅作为备选方案）
            pass
        
        # 备选：使用OpenCV尝试解析
        try:
            import cv2
            import numpy as np
            
            # 将图片数据转换为OpenCV格式
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 使用OpenCV的QRCodeDetector
            qr_detector = cv2.QRCodeDetector()
            data, bbox, _ = qr_detector.detectAndDecode(img)
            
            if data:
                return data
        except ImportError:
            pass
        
        # 如果前面的方法都失败了，返回None
        return None
    
    except Exception as e:
        print(f"Error extracting QR code: {str(e)}")
        return None
