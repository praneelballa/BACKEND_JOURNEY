# router/trie.py

class TrieNode:
    def __init__(self):
        self.children = {}
        self.handler_map = {}  # { METHOD: handler }
        self.param_name = None

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, method: str, path: str, handler):
        parts = [p for p in path.strip("/").split("/") if p]
        curr = self.root

        for part in parts:
            if part.startswith(":"):
                param_name = part[1:]
                if ":param" not in curr.children:
                    node = TrieNode()
                    node.param_name = param_name
                    curr.children[":param"] = node
                curr = curr.children[":param"]
            else:
                if part not in curr.children:
                    curr.children[part] = TrieNode()
                curr = curr.children[part]

        curr.handler_map[method.upper()] = handler

    def search(self, path: str):
        parts = [p for p in path.strip("/").split("/") if p]
        curr = self.root
        params = {}

        for part in parts:
            if part in curr.children:
                curr = curr.children[part]
            elif ":param" in curr.children:
                curr = curr.children[":param"]
                params[curr.param_name] = part
            else:
                return None, None, {}

        return curr, curr.handler_map, params