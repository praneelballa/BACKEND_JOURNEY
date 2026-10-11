# server/response.py
STATUS_MESSAGES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    500: "Internal Server Error"
}

class Response:
    def __init__(self, status_code=200, headers=None, body=b""):
        self.status_code = status_code
        self.headers = headers or {}
        if isinstance(body, str):
            self.body = body.encode("utf-8")
        else:
            self.body = body

    def to_bytes(self) -> bytes:
        status_msg = STATUS_MESSAGES.get(self.status_code, "Unknown Status")
        status_line = f"HTTP/1.1 {self.status_code} {status_msg}\r\n"

        # Ensure Content-Length is set if body exists
        if self.body and "Content-Length" not in self.headers:
            self.headers["Content-Length"] = str(len(self.body))
        elif not self.body and "Content-Length" not in self.headers:
            self.headers["Content-Length"] = "0"

        header_lines = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        return f"{status_line}{header_lines}\r\n".encode("utf-8") + self.body