"""Local Anthropic-API proxy that lets Claude Code drive OpenRouter models.

Claude Code talks to this server as if it were the Anthropic API. Requests for the models in
C.OPENROUTER_ROUTES get provider pinning and reasoning settings, an OpenRouter key the session never sees,
and a per-session JSON-lines log with usage and cost taken from the streamed reply.
"""

import argparse
import hashlib
import http.client
import json
import os
import re
import threading
import time
import urllib.parse
from email.utils import parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bench import config as C
from bench.common import utc_now

UPSTREAM = "https://openrouter.ai/api"  # tests point this at a local fake
RETRY_STATUS = (429, 500, 502, 503, 504)
RETRY_WAITS = (10, 20, 40, 80, 160, 300, 300, 300)
MAX_RETRY_AFTER = 300
UPSTREAM_TIMEOUT = 600
ERROR_TEXT_LIMIT = 2000
NON_STREAM_LIMIT = 4 * 1024 * 1024
HEALTH_PATH = "/nb39-health"
SESSION_HEADER = "x-nb39-session"
USAGE_FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "thinking_tokens")
DROPPED_REQUEST_HEADERS = {"host", "content-length", "accept-encoding", "connection", "keep-alive", "transfer-encoding",
                           "authorization", "x-api-key", SESSION_HEADER, "proxy-authorization", "proxy-connection", "te", "upgrade"}
DROPPED_RESPONSE_HEADERS = {"connection", "keep-alive", "transfer-encoding", "content-length", "proxy-authenticate", "te", "trailer", "upgrade"}
SESSION_PATTERN = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")

LOG_LOCK = threading.Lock()
START_LOCK = threading.Lock()
SERVERS = {}


def api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key and os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
                key = winreg.QueryValueEx(handle, "OPENROUTER_API_KEY")[0]
        except OSError:
            pass
    return (key or "").strip() or None


def log_path(author, task, kind):
    return C.WORK / "openrouter" / author / f"{task}.{kind}.jsonl"


def session_log_path(session):
    """Log file for an x-nb39-session value; anything malformed goes to a shared file, never to a computed path."""
    parts = session.split("/") if session and SESSION_PATTERN.fullmatch(session) else None
    if parts is None or any(set(part) == {"."} for part in parts):
        return C.WORK / "openrouter" / "unattributed.jsonl"
    return log_path(*parts)


def write_log(session, entry):
    line = json.dumps(entry, ensure_ascii=True, sort_keys=True)
    key = api_key()
    if key:
        line = line.replace(key, "<redacted>")
    path = session_log_path(session)
    with LOG_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line + "\n")


def retry_wait(index, retry_after):
    """Seconds to wait before retry number `index`; a usable Retry-After header overrides the schedule."""
    if retry_after:
        try:
            seconds = float(retry_after)
        except ValueError:
            try:
                seconds = (parsedate_to_datetime(retry_after).timestamp() - time.time())
            except (TypeError, ValueError):
                seconds = 0
        if seconds > 0:
            return min(seconds, MAX_RETRY_AFTER)
    return RETRY_WAITS[index]


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


class Reply:
    """Reads usage, ids and errors out of a reply as it passes through; never holds back bytes."""

    def __init__(self, streaming):
        self.streaming = streaming
        self.buffer, self.raw, self.raw_size = b"", [], 0
        self.event, self.data = None, []
        self.usage = {key: 0 for key in USAGE_FIELDS}
        self.cost = None
        self.message_id = self.stop_reason = self.provider = self.model = self.error = None

    def feed(self, chunk):
        if not self.streaming:
            if self.raw_size < NON_STREAM_LIMIT:
                self.raw.append(chunk)
                self.raw_size += len(chunk)
            return
        self.buffer += chunk
        while True:
            end = self.buffer.find(b"\n")
            if end < 0:
                break
            line, self.buffer = self.buffer[:end].rstrip(b"\r"), self.buffer[end + 1:]
            self.line(line)
        if len(self.buffer) > NON_STREAM_LIMIT:
            self.buffer = b""

    def line(self, line):
        if not line:
            self.dispatch()
        elif line.startswith(b"event:"):
            self.event = line[6:].strip().decode("utf-8", "replace")
        elif line.startswith(b"data:"):
            self.data.append(line[5:].lstrip(b" "))

    def dispatch(self):
        data, name, self.data, self.event = b"\n".join(self.data), self.event, [], None
        if not data:
            return
        try:
            event = json.loads(data)
        except ValueError:
            return
        if isinstance(event, dict):
            self.absorb(event, name)

    def absorb(self, event, name=None):
        kind = event.get("type") or name
        if kind == "error" or name == "error":
            self.error = json.dumps(event, ensure_ascii=True)[:ERROR_TEXT_LIMIT]
        if isinstance(event.get("provider"), str):
            self.provider = event["provider"]
        message = event.get("message") if kind == "message_start" else None
        if isinstance(message, dict):
            self.message_id = message.get("id", self.message_id)
            self.model = message.get("model", self.model)
            if isinstance(message.get("provider"), str):
                self.provider = message["provider"]
            self.absorb_usage(message.get("usage"))
        if kind == "message_delta":
            delta = event.get("delta") or {}
            self.stop_reason = delta.get("stop_reason", self.stop_reason)
            self.absorb_usage(event.get("usage"))

    def absorb_usage(self, usage):
        if not isinstance(usage, dict):
            return
        for key in USAGE_FIELDS[:4]:
            if number(usage.get(key)) is not None:
                self.usage[key] = usage[key]
        details = usage.get("output_tokens_details")
        if isinstance(details, dict) and number(details.get("thinking_tokens")) is not None:
            self.usage["thinking_tokens"] = details["thinking_tokens"]
        if number(usage.get("cost")) is not None:
            self.cost = usage["cost"]

    def close(self):
        if self.streaming:
            if self.buffer.strip():
                self.line(self.buffer.rstrip(b"\r"))
            self.dispatch()
            return
        body = b"".join(self.raw)
        try:
            document = json.loads(body)
        except ValueError:
            return
        if not isinstance(document, dict):
            return
        if document.get("type") == "error" or "error" in document:
            self.error = json.dumps(document, ensure_ascii=True)[:ERROR_TEXT_LIMIT]
        if isinstance(document.get("provider"), str):
            self.provider = document["provider"]
        self.message_id = document.get("id", self.message_id)
        self.model = document.get("model", self.model)
        self.stop_reason = document.get("stop_reason", self.stop_reason)
        self.absorb_usage(document.get("usage"))

    def error_body(self):
        return b"".join(self.raw)[:ERROR_TEXT_LIMIT * 4].decode("utf-8", "replace")[:ERROR_TEXT_LIMIT]


def anthropic_error(kind, message):
    return json.dumps({"type": "error", "error": {"type": kind, "message": message}}).encode()


def count(value):
    return len(value) if isinstance(value, (list, dict)) else int(bool(value))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "nb39-openrouter-proxy"

    def log_message(self, *args):
        pass

    def send_json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def fail(self, finish, status, body):
        finish()  # log first, so a client that acts on the reply never outruns its log line
        self.send_json(status, body)

    def do_GET(self):
        if self.path == HEALTH_PATH:
            self.send_json(200, json.dumps({"nb39_openrouter_proxy": True, "models": sorted(C.OPENROUTER_ROUTES)}).encode())
        else:
            self.send_json(404, anthropic_error("not_found_error", f"nb39 proxy does not serve GET {self.path}"))

    def read_body(self):
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            parts = []
            while True:
                size = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    while self.rfile.readline().strip():
                        pass
                    return b"".join(parts)
                parts.append(self.rfile.read(size))
                self.rfile.readline()
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_POST(self):
        session = self.headers.get(SESSION_HEADER, "")
        entry = dict(session=session, start_utc=utc_now(), end_utc=None, path=self.path, model=None, provider_requested=None,
                     provider_served=None, status=None, attempts=[], message_id=None, stop_reason=None,
                     usage={key: 0 for key in USAGE_FIELDS}, cost_usd=None, request_sha256=None, request_settings=None,
                     error_text=None, rejected=False)
        state = dict(logged=False)

        def finish():
            if not state["logged"]:
                state["logged"] = True
                entry["end_utc"] = utc_now()
                write_log(session, entry)

        try:
            self.handle_post(entry, finish)
        finally:
            finish()

    def handle_post(self, entry, finish):
        body = self.read_body()
        path = urllib.parse.urlsplit(self.path).path
        try:
            data = json.loads(body)
            model = data.get("model") if isinstance(data, dict) else None
        except ValueError:
            data, model = None, None
        entry["model"] = model if isinstance(model, str) else None
        route = C.OPENROUTER_ROUTES.get(model) if isinstance(model, str) else None
        if route is None or not path.startswith("/v1/") or ".." in path:
            entry.update(rejected=True, status=400)
            entry["error_text"] = f"rejected: model {model!r} (or path {path!r}) is not routed through OpenRouter"
            return self.fail(finish, 400, anthropic_error("invalid_request_error", entry["error_text"]))
        key = api_key()
        if not key:
            entry.update(status=401, error_text="OPENROUTER_API_KEY is not set for the proxy")
            return self.fail(finish, 401, anthropic_error("authentication_error", entry["error_text"]))
        data["provider"] = {"order": [route["provider"]], "allow_fallbacks": False}
        data.pop("thinking", None)
        data["reasoning"] = {"effort": route["reasoning_effort"]}
        forwarded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        entry["provider_requested"] = route["provider"]
        entry["request_sha256"] = hashlib.sha256(forwarded).hexdigest()
        entry["request_settings"] = {**{k: v for k, v in data.items() if k not in ("messages", "system", "tools")},
                                     "messages_count": count(data.get("messages")), "system_count": count(data.get("system")),
                                     "tools_count": count(data.get("tools"))}
        headers = {k: v for k, v in self.headers.items() if k.lower() not in DROPPED_REQUEST_HEADERS}
        headers.update({"Authorization": "Bearer " + key, "Content-Length": str(len(forwarded)), "Accept-Encoding": "identity"})
        response, connection = self.connect(self.path, forwarded, headers, entry)
        if response is None:
            entry["status"] = 502
            entry["error_text"] = ((entry["attempts"][-1]["error"] if entry["attempts"] else "") or "upstream unreachable")[:ERROR_TEXT_LIMIT]
            return self.fail(finish, 502, anthropic_error("api_error", "nb39 proxy could not reach OpenRouter: " + entry["error_text"]))
        try:
            self.relay(response, entry, finish)
        finally:
            connection.close()

    def connect(self, path, body, headers, entry):
        """Open the upstream reply, retrying before a single byte has gone to the client."""
        target = urllib.parse.urlsplit(UPSTREAM)
        connection_class = http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection
        for index in range(len(RETRY_WAITS) + 1):
            attempt = dict(status=None, wait_seconds=None, error=None)
            entry["attempts"].append(attempt)
            connection = connection_class(target.hostname, target.port, timeout=UPSTREAM_TIMEOUT)
            retry_after = None
            try:
                connection.request("POST", target.path.rstrip("/") + path, body=body, headers=headers)
                response = connection.getresponse()
                attempt["status"] = response.status
                if response.status not in RETRY_STATUS or index == len(RETRY_WAITS):
                    return response, connection
                retry_after = response.getheader("Retry-After")
                attempt["error"] = response.read(ERROR_TEXT_LIMIT * 4).decode("utf-8", "replace")[:ERROR_TEXT_LIMIT]
            except (OSError, http.client.HTTPException) as exc:
                attempt["error"] = f"{type(exc).__name__}: {exc}"[:ERROR_TEXT_LIMIT]
                if index == len(RETRY_WAITS):
                    connection.close()
                    return None, None
            connection.close()
            attempt["wait_seconds"] = retry_wait(index, retry_after)
            time.sleep(attempt["wait_seconds"])
        return None, None

    def relay(self, response, entry, finish):
        entry["status"] = response.status
        self.send_response_only(response.status)
        for name, value in response.getheaders():
            if name.lower() not in DROPPED_RESPONSE_HEADERS:
                self.send_header(name, value)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        reply = Reply("text/event-stream" in (response.getheader("Content-Type") or "").lower())
        interrupted = None
        try:
            while True:
                try:
                    chunk = response.read1(65536)
                except (OSError, http.client.HTTPException) as exc:
                    interrupted = f"upstream stream interrupted: {type(exc).__name__}: {exc}"
                    break
                if not chunk:
                    break
                reply.feed(chunk)
                self.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
                self.wfile.flush()
        except OSError as exc:
            interrupted = f"client disconnected: {type(exc).__name__}: {exc}"
            self.close_connection = True
        reply.close()
        entry.update(message_id=reply.message_id, stop_reason=reply.stop_reason, usage=reply.usage, cost_usd=reply.cost,
                     provider_served=reply.provider, model_served=reply.model)
        text = reply.error or (reply.error_body() if response.status != 200 else None)
        entry["error_text"] = "; ".join(filter(None, [text, interrupted]))[:ERROR_TEXT_LIMIT] or None
        # Log before the terminating chunk, so a client that exits on end-of-stream never outruns its log line.
        finish()
        if interrupted:
            self.close_connection = True  # no terminator: the client must see a broken stream, not a clean short one
        else:
            self.wfile.write(b"0\r\n\r\n")


class Server(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


def probe(port):
    """True when a proxy of this kind already answers on the port; raises if something else does."""
    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", HEALTH_PATH)
        response = connection.getresponse()
        body = response.read()
        connection.close()
    except (OSError, http.client.HTTPException):
        return False
    try:
        if response.status == 200 and json.loads(body).get("nb39_openrouter_proxy"):
            return True
    except (ValueError, AttributeError):
        pass
    raise RuntimeError(f"Port {port} is in use by something that is not the nb39 OpenRouter proxy")


def start(port=None):
    """Run the proxy in a daemon thread and return the server (None when another process already serves the port)."""
    port = C.OPENROUTER_PROXY_PORT if port is None else port
    with START_LOCK:
        if port in SERVERS:
            return SERVERS[port]
        if port and probe(port):
            return None
        if not api_key():
            raise RuntimeError("OPENROUTER_API_KEY is not set (process environment or Windows user environment)")
        try:
            server = Server(("127.0.0.1", port), Handler)
        except OSError:
            if port and probe(port):
                return None
            raise
        threading.Thread(target=server.serve_forever, name=f"nb39-openrouter-proxy-{port}", daemon=True).start()
        SERVERS[server.server_address[1]] = server
        return server


def stop(server):
    SERVERS.pop(server.server_address[1], None)
    server.shutdown()
    server.server_close()


def summarize(path):
    """Totals over one session's proxy log, as stored in the session's meta."""
    result = dict(requests=0, rejected=0, retries=0, errors=0, providers_served=set(),
                  usage={key: 0 for key in USAGE_FIELDS}, cost_usd=0.0)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            result["requests"] += 1
            if entry.get("rejected"):
                result["rejected"] += 1
                continue
            result["retries"] += max(0, len(entry.get("attempts", [])) - 1)
            result["errors"] += entry.get("status") != 200 or bool(entry.get("error_text"))
            if entry.get("provider_served"):
                result["providers_served"].add(entry["provider_served"])
            for key in USAGE_FIELDS:
                result["usage"][key] += (entry.get("usage") or {}).get(key) or 0
            result["cost_usd"] += entry.get("cost_usd") or 0.0
    result["providers_served"] = sorted(result["providers_served"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=C.OPENROUTER_PROXY_PORT)
    args = parser.parse_args()
    if start(args.port) is None:
        print(f"Proxy already running on port {args.port}")
        return
    print(f"nb39 OpenRouter proxy on http://127.0.0.1:{args.port}; logs in {C.WORK / 'openrouter'}", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
