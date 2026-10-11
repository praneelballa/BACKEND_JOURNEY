# middleware/auth_guard.py
import hmac
import hashlib
import base64
import json
import time
from server.response import Response

JWT_SECRET = "super-secret-key-12345"

def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def b64_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = b64_encode(json.dumps(payload).encode("utf-8"))
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = b64_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_jwt(token: str):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, sig_b64 = parts
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).digest()
    if not hmac.compare_digest(b64_encode(expected_sig), sig_b64):
        return None
    try:
        payload = json.loads(b64_decode(payload_b64).decode("utf-8"))
        if "exp" in payload and time.time() > payload["exp"]:
            return None
        return payload
    except Exception:
        return None

def require_auth(handler):
    def wrapper(req):
        auth_header = req.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            # Generic 401 response prevents leaking internal validation state
            return Response(401, {"Content-Type": "application/json"}, '{"error": "Authentication failed"}')

        token = auth_header.split(" ", 1)[1].strip()
        claims = verify_jwt(token)
        if not claims:
            return Response(401, {"Content-Type": "application/json"}, '{"error": "Authentication failed"}')

        req.user = claims
        return handler(req)
    return wrapper