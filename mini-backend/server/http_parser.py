# server/http_parser.py

class Request:
    def __init__(self, method: str, path: str, version: str, headers: dict, body: bytes):
        self.method = method.upper()
        self.path = path
        self.version = version
        self.headers = headers
        self.body = body
        self.params = {}
        self.json = None
        self.user = None  # Authenticated claims

class HTTPParser:
    @staticmethod
    def parse(raw_data: bytes) -> Request:
        delimiter = b"\r\n\r\n"
        if delimiter not in raw_data:
            raise ValueError("Malformed HTTP request: missing header-body boundary")

        header_part, body_part = raw_data.split(delimiter, 1)
        header_lines = header_part.decode("iso-8859-1").split("\r\n")

        # Parse Request Line
        request_line = header_lines[0].split(" ")
        if len(request_line) < 3:
            raise ValueError("Malformed request line")
        method, path, version = request_line[0], request_line[1], request_line[2]

        # Parse Headers
        headers = {}
        for line in header_lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        # Handle Content-Length extraction
        content_length = int(headers.get("content-length", 0))
        body = body_part[:content_length]

        return Request(method, path, version, headers, body)