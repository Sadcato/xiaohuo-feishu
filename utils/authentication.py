import hashlib
import hmac
import base64
from fastapi import Request

from config.config import ENCRYPT_KEY

async def verify_feishu_request(request: Request) -> bool:
    if not ENCRYPT_KEY:
        return True
    
    signature = request.headers.get("X-Lark-Signature")
    timestamp = request.headers.get("X-Lark-Request-Timestamp")
    nonce = request.headers.get("X-Lark-Request-Nonce")
    
    if not all([signature, timestamp, nonce]):
        return False
    
    body = await request.body()
    body_str = body.decode("utf-8")
    
    base_string = timestamp + nonce + ENCRYPT_KEY + body_str
    expected_signature = base64.b64encode(
        hmac.new(
            ENCRYPT_KEY.encode(),
            base_string.encode(),
            hashlib.sha256
        ).digest()
    ).decode()
    
    return signature == expected_signature
