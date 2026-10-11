# middleware/body_parser.py
import json
from server.response import Response

MAX_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1MB

def parse_json_body(req):
    content_length = int(req.headers.get("content-length", 0))
    if content_length > MAX_PAYLOAD_SIZE:
        return Response(413, {"Content-Type": "application/json"}, '{"error": "Payload Too Large"}')

    if content_length > 0:
        content_type = req.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                req.json = json.loads(req.body.decode("utf-8"))
            except Exception:
                return Response(400, {"Content-Type": "application/json"}, '{"error": "Malformed JSON payload"}')
        else:
            req.json = {}
    else:
        req.json = {}
    return None