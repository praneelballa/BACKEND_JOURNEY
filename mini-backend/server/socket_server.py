# server/socket_server.py
import socket
import threading
from server.http_parser import HTTPParser
from server.response import Response
from middleware.body_parser import parse_json_body

class TCPServer:
    def __init__(self, host: str, port: int, router):
        self.host = host
        self.port = port
        self.router = router

    def handle_client(self, client_sock):
        try:
            # Buffer reading
            raw_data = client_sock.recv(65536)
            if not raw_data:
                return

            req = HTTPParser.parse(raw_data)

            # Pre-middleware: payload safety limit & JSON deserializer
            guard_error = parse_json_body(req)
            if guard_error:
                client_sock.sendall(guard_error.to_bytes())
                return

            # Route dispatch
            response = self.router.dispatch(req)
            client_sock.sendall(response.to_bytes())
        except Exception:
            err_resp = Response(500, {"Content-Type": "application/json"}, '{"error": "Internal Server Error"}')
            client_sock.sendall(err_resp.to_bytes())
        finally:
            client_sock.close()

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen(128)
        print(f"[*] Server listening on {self.host}:{self.port}")

        while True:
            client_sock, _ = server_sock.accept()
            worker = threading.Thread(target=self.handle_client, args=(client_sock,))
            worker.daemon = True
            worker.start()