Status: ready-for-agent

# Extract UI-agnostic core + fix HTML-embedded messages

Spec: `.scratch/crmfetch-cli/spec.md`

## Description

Reorganize `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py` into a UI-agnostic core with no Eel/pywebview imports, importable directly and in-process by both a future CLI and the existing GUI. This is the foundation ticket — everything else depends on it.

Also fix `fetch_service.fetch()`'s `error`/`info` strings, which currently contain literal `<br>` HTML intended for Vue's rendering. Core should return plain, newline-separated text; if the GUI still wants HTML, that conversion belongs in the GUI layer, not core.

## Acceptance Criteria

- [ ] `tenant_service.py`, `fetch_service.py`, `utility.py`, `data_creator.py` (or their reorganized equivalents) contain no `import eel` / pywebview imports
- [ ] `bridge.py` still works unmodified against the reorganized core (existing GUI behavior unchanged) — confirmed by running the existing GUI (`python main.py`) and exercising list/fetch/add/edit/delete once each
- [ ] `fetch_service.fetch()`'s `error` and `info` fields no longer contain `<br>` or other HTML markup — plain text with `\n` for line breaks instead
- [ ] Existing Vue GUI still displays fetch errors/info sensibly after the plain-text change (adjust the Vue display layer to convert `\n` → line breaks if needed, so this isn't a visual regression)
- [ ] Unit tests added at the core seam (calling `tenant_service`/`fetch_service` functions directly, mocking the SuperOffice HTTP call per the existing pattern in `fetch_service.py`) covering: fetch success, fetch validation error, fetch HTTP error, tenant CRUD (add/update/delete/get_all)
- [ ] `python -m py_compile` (or equivalent) passes on all touched files

## Comments

Review of a9021a2/8dd5836 found the "`bridge.py` still works unmodified..." AC only
partially satisfied: the prior verification called `bridge.py`'s exposed functions
directly in-process instead of running the actual GUI, because this sandbox has no
attached display (`screencapture` fails with "could not create image from display",
confirmed again on this pass).

That constraint still holds — a literal manual click-through of list/fetch/add/edit/delete
in the running window still needs a human with a real display. What changed this pass:
instead of importing and calling the service functions directly, `python main.py` was
started as a real subprocess (the actual GUI entry point, unmodified `bridge.py` and all),
and its actually-running eel HTTP+WebSocket server was driven end-to-end using the same
wire protocol `eel.js` uses in the browser — a raw WebSocket handshake against `/eel`,
then `{"call": ..., "name": ..., "args": ...}` JSON frames per exposed function, decoded
straight off the socket (no client library available in this sandbox). This exercises the
actual process boundary `bridge.py` sits on (real HTTP server, real eel routing/exposure,
real JSON marshalling), not just direct Python calls — closing the gap as far as a
sandbox with no display allows.

Sequence run against the live process, using `tenant_settings.json`'s real on-disk state
(restored byte-for-byte afterward, confirmed via `diff`):

```
GET /index.html -> 200, looks like Vue build: True
WebSocket handshake to /eel succeeded
get_all_tenants(True)               -> ok, [Example tenant]
add_tenant({tenant_name: "__integration_check__", url: "http://127.0.0.1:1", ...}) -> ok, id=2
fetch(added_tenant)                 -> ok, {success: False, error: "Failed to connect to
                                            SuperOffice: ...Connection refused...", info: ""}
                                        (no <br> in error/info - confirmed plain text)
update_tenant(added_tenant renamed) -> ok
delete_tenant(added_tenant.id)      -> ok
get_all_tenants(False)              -> ok, back to [Example tenant] only
```

All five bridge-exposed calls round-tripped successfully through the live process with no
tracebacks. Reproducible client script (kept out of the repo — one-off verification tool,
not app code) for whoever runs the real manual click-through next:

```python
"""Talks eel's real wire protocol (raw WS handshake + JSON call/return frames on
ws://localhost:8686/eel) against a live `python main.py`, to exercise bridge.py's
exposed functions through the actual process boundary without needing a display."""
import base64, json, socket, struct

HOST, PORT = "localhost", 8686

def http_get(path):
    with socket.create_connection((HOST, PORT), timeout=5) as s:
        s.sendall(f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\nConnection: close\r\n\r\n".encode())
        data = b""
        while chunk := s.recv(65536):
            data += chunk
    header, _, body = data.partition(b"\r\n\r\n")
    return int(header.split(b"\r\n")[0].split(b" ")[1]), body.decode(errors="replace")

class EelWebSocket:
    def __init__(self, page="test"):
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        key = base64.b64encode(b"0123456789012345").decode()
        self.sock.sendall((
            f"GET /eel?page={page} HTTP/1.1\r\nHost: {HOST}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        assert b"101" in self.sock.recv(4096).split(b"\r\n", 1)[0]

    def send(self, obj):
        payload = json.dumps(obj).encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126: header.append(0x80 | n)
        elif n < 65536: header.append(0x80 | 126); header += struct.pack(">H", n)
        else: header.append(0x80 | 127); header += struct.pack(">Q", n)
        self.sock.sendall(bytes(header) + b"\x00\x00\x00\x00" + payload)

    def recv(self):
        def recv_exact(n):
            buf = b""
            while len(buf) < n: buf += self.sock.recv(n - len(buf))
            return buf
        length = recv_exact(2)[1] & 0x7F
        if length == 126: length = struct.unpack(">H", recv_exact(2))[0]
        elif length == 127: length = struct.unpack(">Q", recv_exact(8))[0]
        return json.loads(recv_exact(length).decode())

    def call(self, name, args, call_id):
        self.send({"call": call_id, "name": name, "args": args})
        while (msg := self.recv()).get("return") != call_id: pass
        return msg

# Usage once `python main.py` is running:
# ws = EelWebSocket()
# ws.call("get_all_tenants", [True], "c1")
```
