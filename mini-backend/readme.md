# Custom HTTP/1.1 Web Framework & REST API from Scratch

A pure Python HTTP/1.1 web server, router, and REST API built from the ground up using native OS sockets—completely free of third-party frameworks like Flask, FastAPI, or Django.

This project was built to understand backend systems from first principles: demystifying the OSI application layer (Layer 7) and transport layer (Layer 4) boundaries, wire protocol serialization, token-based stateless authentication, and multi-tenant resource access controls.

---

## Architecture Overview

```
[ Client (curl / Browser / Postman) ]
                │
                ▼ (Raw TCP Bytes over Socket)
┌─────────────────────────────────────────────────────────────┐
│ 1. TCP Listener & Connection Acceptor                       │
│    • Binds to 0.0.0.0:8080                                  │
│    • Spawns worker thread per connection                    │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Raw String Buffer)
┌─────────────────────────────────────────────────────────────┐
│ 2. HTTP Protocol Parser                                     │
│    • Splits lines on \r\n and parses \r\n\r\n boundary      │
│    • Extracts Method, Target Path, HTTP/1.1                 │
│    • Extracts Headers (Host, Authorization, Content-Length) │
│    • Extracts Body bytes according to Content-Length        │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Internal Request Object)
┌─────────────────────────────────────────────────────────────┐
│ 3. Prefix Trie Router & Matcher                             │
│    • Matches (METHOD, PATH) -> Handler Function             │
│    • Tokenizes dynamic route parameters (/notes/:id)        │
│    • Traps 404 (Not Found) & 405 (Method Not Allowed)       │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Matched Pipeline Dispatch)
┌─────────────────────────────────────────────────────────────┐
│ 4. Payload Guard & Body Deserializer                        │
│    • Enforces Content-Length <= 1MB (Anti-DoS memory guard) │
│    • Deserializes JSON string into native Python dictionary │
│    • Emits 400 Bad Request on malformed JSON payload        │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Sanitized Request Context)
┌─────────────────────────────────────────────────────────────┐
│ 5. Auth Middleware (@require_auth Guard)                    │
│    • Extracts Authorization: Bearer <token>                 │
│    • Verifies HMAC-SHA256 signature & expiration timestamp  │
│    • Extracts claims (user_id, role) to req.user            │
│    • Emits generic 401 Unauthorized on failures             │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Authorized Execution)
┌─────────────────────────────────────────────────────────────┐
│ 6. Core Business Logic & RBAC Enforcement                   │
│    • In-memory stores (USER_DB, NOTES_DB)                   │
│    • Multi-tenant ownership checks (note.user_id == req.sub)│
│    • Admin role bypass verification                         │
│    • Emits 403 Forbidden on permission violation            │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼ (Internal Entity / Bytes)
┌─────────────────────────────────────────────────────────────┐
│ 7. HTTP Response Formatter & Socket Writer                  │
│    • Constructs HTTP/1.1 Status Line & Response Headers     │
│    • Sets Content-Length header                             │
│    • Writes bytes back to OS Socket and closes connection   │
└─────────────────────────────────────────────────────────────┘

```

---

## Core Engineering Concepts Implemented

### 1. Transport Layer (Layer 4) to Application Layer (Layer 7)

* **Raw OS Sockets**: Binds directly to `0.0.0.0:8080` via Python's `socket` module.
* **TCP Concurrency**: Employs a multi-threaded daemon model (`threading.Thread`) to accept incoming TCP connections without blocking the listener loop.
* **Wire Protocol Boundaries**: Parses raw byte streams by identifying HTTP delimiter boundaries (`\r\n\r\n` separating headers from body) and reading exact body byte offsets according to `Content-Length`.

### 2. Prefix Trie Routing & Dynamic Parameters

* **Trie-based Route Indexing**: Routes are indexed in a prefix tree data structure instead of flat lists or slow regex matching.
* **Dynamic Parameter Capture**: Segments prefixed with `:param` (e.g., `/notes/:id`) tokenize paths into variables accessible inside request handlers as `req.params["id"]`.
* **RFC Method Standard Compliance**: If a URL path exists in the Trie but the requested HTTP verb is not registered, the router returns a `405 Method Not Allowed` response along with an `Allow` header listing supported verbs.



### 3. Ingress Defense & Deserialization

* **Anti-DoS Memory Guards**: Blocks oversized payloads over 1MB (`413 Payload Too Large`) prior to JSON processing, preventing memory exhaustion attacks.
* **Payload Deserialization**: Deserializes JSON string bytes into Python dictionaries, trapping syntax errors with a standard `400 Bad Request`.



### 4. Cryptographic Authentication & Stateless JWTs

* **Salted Password Hashing**: Passwords are never stored in plain text. They are salted with `os.urandom(16)` and hashed via PBKDF2 (`hashlib.pbkdf2_hmac`) with 100,000 iterations to resist rainbow-table attacks.


* **Stateless Token Generation**: Generates standard 3-part Base64URL JWTs (`header.payload.signature`) signed with HMAC-SHA256. Tokens contain claims (`sub`, `role`, `exp`) allowing the backend to authenticate requests without performing database lookups on every hit.


* **Timing & Enumeration Defense**:
* Employs constant-time string comparison (`hmac.compare_digest`) to prevent timing leak vulnerabilities.


* Emits uniform generic `401 Unauthorized` responses to protect against username enumeration attacks.





### 5. Multi-Tenant Role-Based Access Control (RBAC)

* **Identity vs. Permission**: Validates *who you are* via the authentication token, followed by evaluating *what you are allowed to do* via RBAC policies.


* **Resource Ownership**: Standard users (`role: "user"`) can only read, update, or delete notes where `note.user_id == current_user.id`. Unauthorized access triggers an immediate `403 Forbidden`.


* **Admin Privilege Bypass**: Users with `role: "admin"` possess cross-tenant administrative access to manage or delete any note across the system.



---

## Project Structure

```plaintext
mini-backend/
├── server/
│   ├── socket_server.py      # TCP socket listener & connection thread manager
│   ├── http_parser.py        # HTTP string to Request object parser
│   └── response.py           # HTTP status lines & response byte builder
├── router/
│   ├── trie.py               # Prefix trie supporting dynamic :param segments
│   └── router.py             # Route registration, dynamic matching, 404/405 traps
├── middleware/
│   ├── body_parser.py        # Content-Length 1MB guard & JSON deserializer
│   └── auth_guard.py         # JWT parsing, HMAC verification, @require_auth guard
├── domain/
│   ├── users.py              # User entity, PBKDF2 salted hashing, login/register
│   └── notes.py              # Note entity, multi-tenant CRUD & RBAC checks
└── main.py                   # Application assembly, route registration & server launch

```

---

## API Specification

| Method | Endpoint | Auth Required | Description | Status Codes |
| --- | --- | --- | --- | --- |
| `POST` | `/auth/register` | No | Registers user with salted PBKDF2 hash

 | `201 Created`, `400 Bad Request`, `409 Conflict`<br> |
| `POST` | `/auth/login` | No | Verifies credentials; issues signed JWT

 | `200 OK`, `401 Unauthorized`<br> |
| `POST` | `/notes` | Yes (Bearer) | Creates a note scoped to authenticated user

 | `201 Created`, `400 Bad Request`, `401 Unauthorized`<br> |
| `GET` | `/notes` | Yes (Bearer) | Retrieves notes owned by user (or all if admin)

 | `200 OK`, `401 Unauthorized`<br> |
| `DELETE` | `/notes/:id` | Yes (Bearer) | Deletes note if owner or admin

 | `204 No Content`, `403 Forbidden`, `404 Not Found`<br> |

---

## Getting Started

### Prerequisites

* Python 3.10+ (Standard library only; zero external pip dependencies).
* PowerShell, Bash, or any standard terminal with `curl`.

### Running the Server

1. Clone the repository:
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

```


2. Start the TCP server:
```bash
python main.py
# Or using Python Launcher:
py main.py

```


*Terminal Output:*
```plaintext
[*] Server listening on 0.0.0.0:8080

```



---

## Verification & Testing Guide

Run these commands in a separate terminal window to test every architectural layer:

### 1. Register Users (Standard & Admin)

```bash
# Register User Alice
curl.exe -i -X POST http://localhost:8080/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"alice\", \"password\": \"securepassword\", \"role\": \"user\"}"

# Register Admin Bob
curl.exe -i -X POST http://localhost:8080/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"admin_bob\", \"password\": \"adminpassword\", \"role\": \"admin\"}"

```

### 2. Authenticate & Obtain Tokens

```powershell
# PowerShell Native Command
$aliceResponse = Invoke-RestMethod -Uri "http://localhost:8080/auth/login" -Method Post -ContentType "application/json" -Body (@{ username = "alice"; password = "securepassword" } | ConvertTo-Json)
$aliceToken = $aliceResponse.token

$adminResponse = Invoke-RestMethod -Uri "http://localhost:8080/auth/login" -Method Post -ContentType "application/json" -Body (@{ username = "admin_bob"; password = "adminpassword" } | ConvertTo-Json)
$adminToken = $adminResponse.token

```

### 3. Create Note (Authenticated User)

```powershell
$notePayload = @{ content = "Alice private secrets" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/notes" -Method Post -ContentType "application/json" -Headers @{ Authorization = "Bearer $aliceToken" } -Body $notePayload

```

### 4. Test RBAC Cross-Tenant Violation (`403 Forbidden`)

Register an unauthorized user (`eve`) and attempt to delete Alice's note at `/notes/1`:

```powershell
# Register & Login Eve
$eveToken = (Invoke-RestMethod -Uri "http://localhost:8080/auth/login" -Method Post -ContentType "application/json" -Body (@{ username = "eve"; password = "evepassword" } | ConvertTo-Json)).token

# Attempt Deletion (Will fail with 403 Forbidden)
curl.exe -i -X DELETE http://localhost:8080/notes/1 -H "Authorization: Bearer $eveToken"

```

### 5. Test Router Method Mismatch (`405 Method Not Allowed`)

```bash
curl.exe -i -X GET http://localhost:8080/auth/login

```

*Expected Output:* Status `405 Method Not Allowed` with header `Allow: POST`.

### 6. Test Anti-DoS Guard (`413 Payload Too Large`)

```powershell
$oversized = "A" * (1024 * 1024 + 500)
Set-Content -Path "large_payload.txt" -Value $oversized -NoNewline
curl.exe -i -X POST http://localhost:8080/notes -H "Content-Type: application/json" -H "Authorization: Bearer $aliceToken" --data-binary "@large_payload.txt"
Remove-Item "large_payload.txt"

```

*Expected Output:* Status `413 Payload Too Large`.

---

## Future Roadmap & Scaling

* [ ] **Persistent Storage**: Replace volatile in-memory state (`USER_DB`, `NOTES_DB`) with PostgreSQL using a Repository Pattern.


* [ ] **Non-Blocking Async I/O**: Migrate from thread-per-connection sockets to Python's `asyncio` or `selectors` event-loop multiplexing.
* [ ] **HTTP/1.1 Persistent Connections**: Implement `Connection: keep-alive` socket reuse instead of immediate disconnects.


* [ ] **CORS Preflight Middleware**: Handle `OPTIONS` requests, returning `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, and `Access-Control-Allow-Headers`.


* [ ] **Hybrid Token Revocation**: Pair short-lived JWT access tokens with centralized Redis token blocklists for instantaneous session revocation.