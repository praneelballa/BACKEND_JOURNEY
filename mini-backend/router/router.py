# router/router.py
from router.trie import Trie
from server.response import Response

class Router:
    def __init__(self):
        self.trie = Trie()

    def add_route(self, method: str, path: str, handler):
        self.trie.insert(method, path, handler)

    def dispatch(self, req) -> Response:
        node, handler_map, params = self.trie.search(req.path)
        if not node or not handler_map:
            return Response(404, {"Content-Type": "application/json"}, '{"error": "Route not found"}')

        if req.method not in handler_map:
            allowed = ", ".join(handler_map.keys())
            return Response(405, {"Allow": allowed, "Content-Type": "application/json"}, '{"error": "Method Not Allowed"}')

        req.params = params
        handler = handler_map[req.method]
        return handler(req)