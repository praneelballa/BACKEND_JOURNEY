# domain/notes.py
import json
from server.response import Response

NOTES_DB = {}
NOTE_COUNTER = 1

def create_note_handler(req):
    global NOTE_COUNTER
    data = req.json or {}
    content = data.get("content")
    if not content:
        return Response(400, {"Content-Type": "application/json"}, '{"error": "Content required"}')

    note_id = str(NOTE_COUNTER)
    NOTE_COUNTER += 1

    note = {
        "id": note_id,
        "user_id": req.user["sub"],
        "content": content
    }
    NOTES_DB[note_id] = note
    return Response(201, {"Content-Type": "application/json"}, json.dumps(note))

def get_notes_handler(req):
    user_id = req.user["sub"]
    role = req.user.get("role", "user")

    # Admin bypass vs resource ownership check
    if role == "admin":
        user_notes = list(NOTES_DB.values())
    else:
        user_notes = [n for n in NOTES_DB.values() if n["user_id"] == user_id]

    return Response(200, {"Content-Type": "application/json"}, json.dumps(user_notes))

def delete_note_handler(req):
    note_id = req.params.get("id")
    note = NOTES_DB.get(note_id)

    if not note:
        return Response(404, {"Content-Type": "application/json"}, '{"error": "Note not found"}')

    # RBAC: Must be owner or admin
    if note["user_id"] != req.user["sub"] and req.user.get("role") != "admin":
        return Response(403, {"Content-Type": "application/json"}, '{"error": "Forbidden: Access denied"}')

    del NOTES_DB[note_id]
    return Response(204, {}, b"")