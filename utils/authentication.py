import time
import hashlib
import hmac
import base64
import httpx
from fastapi import Request, HTTPException

from config.config import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_GET_TOKEN_URL, ENCRYPT_KEY

_token_cache = {
    "token": None,
    "expires_at": 0
}

async def get_tenant_access_token():
    global _token_cache
    current_time = time.time()
    
    if _token_cache["token"] and _token_cache["expires_at"] > current_time:
        return _token_cache["token"]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FEISHU_GET_TOKEN_URL,
                json={
                    "app_id": FEISHU_APP_ID,
                    "app_secret": FEISHU_APP_SECRET
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get tenant access token: {result.get('msg')}"
                )
            
            token = result.get("tenant_access_token")
            expires_in = result.get("expire") - 60  # Subtract 60 seconds for safety
            
            # Update cache
            _token_cache = {
                "token": token,
                "expires_at": current_time + expires_in
            }
            
            return token
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tenant access token: {str(e)}"
        )

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
