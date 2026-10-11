# main.py
from router.router import Router
from server.socket_server import TCPServer
from middleware.auth_guard import require_auth
from domain.users import register_handler, login_handler
from domain.notes import create_note_handler, get_notes_handler, delete_note_handler

def init_app():
    router = Router()

    # Public Routes
    router.add_route("POST", "/auth/register", register_handler)
    router.add_route("POST", "/auth/login", login_handler)

    # Protected Routes with Auth & RBAC
    router.add_route("POST", "/notes", require_auth(create_note_handler))
    router.add_route("GET", "/notes", require_auth(get_notes_handler))
    router.add_route("DELETE", "/notes/:id", require_auth(delete_note_handler))

    return router

if __name__ == "__main__":
    app_router = init_app()
    server = TCPServer("0.0.0.0", 8080, app_router)
    server.start()