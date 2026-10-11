# domain/users.py
import hashlib
import os
import hmac
import time
from middleware.auth_guard import create_jwt
from server.response import Response

USER_DB = {}

def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return salt, key.hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return hmac.compare_digest(key.hex(), expected_hash)

def register_handler(req):
    data = req.json or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return Response(400, {"Content-Type": "application/json"}, '{"error": "Missing username or password"}')

    if username in USER_DB:
        return Response(409, {"Content-Type": "application/json"}, '{"error": "Resource conflict"}')

    salt, p_hash = hash_password(password)
    user_id = str(len(USER_DB) + 1)
    USER_DB[username] = {
        "id": user_id,
        "username": username,
        "salt": salt,
        "hash": p_hash,
        "role": role
    }
    return Response(201, {"Content-Type": "application/json"}, f'{{"message": "User registered", "id": "{user_id}"}}')

def login_handler(req):
    data = req.json or {}
    username = data.get("username")
    password = data.get("password")

    user = USER_DB.get(username)
    # Generic error and constant-time check to prevent timing leaks
    if not user or not verify_password(password, user["salt"], user["hash"]):
        return Response(401, {"Content-Type": "application/json"}, '{"error": "Authentication failed"}')

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "exp": time.time() + 3600
    }
    token = create_jwt(payload)
    return Response(200, {"Content-Type": "application/json"}, f'{{"token": "{token}"}}')