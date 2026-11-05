"""Offline checks of the OpenRouter proxy against a fake upstream; no network and no model."""

import hashlib
import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from bench import config as C
from bench import openrouter_proxy as P

KEY = "sk-or-v1-test-SECRET-0123456789"
MODEL = "deepseek/deepseek-v4.1-flash-1017"
SESSION = "deepseek/heat/main"


def sse(name, data):
    return f"event: {name}\ndata: {json.dumps(data)}\n\n".encode()


CANNED = [
    sse("message_start", {"type": "message_start", "message": {
        "id": "gen-123", "type": "message", "role": "assistant", "model": "deepseek/deepseek-v4.1-flash-20261017", "provider": "DeepSeek",
        "content": [], "usage": {"input_tokens": 11, "output_tokens": 1, "cache_read_input_tokens": 0}}}),
    b": OPENROUTER PROCESSING\n\n",
    sse("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "héllo"}}),
    sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn"},
                          "usage": {"input_tokens": 4479, "output_tokens": 76, "output_tokens_details": {"thinking_tokens": 37},
                                    "cache_creation_input_tokens": None, "cache_read_input_tokens": 12, "cost": 0.00071745}}),
    sse("message_stop", {"type": "message_stop"}),
]
CANNED_BYTES = b"".join(CANNED)


class Upstream(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        server = self.server
        with server.lock:
            server.seen.append(dict(path=self.path, headers={k.lower(): v for k, v in self.headers.items()}, body=body))
            number = len(server.seen)
        if number <= server.failures:
            payload = json.dumps({"error": {"message": "slow down"}}).encode()
            self.send_response(server.failure_status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        # Cut mid-event and mid-character so the relay and the parser must cope with arbitrary chunk boundaries.
        pieces = [CANNED_BYTES[:40], CANNED_BYTES[40:200], CANNED_BYTES[200:201], CANNED_BYTES[201:]]
        for piece in pieces:
            self.wfile.write(b"%x\r\n%s\r\n" % (len(piece), piece))
            self.wfile.flush()
            time.sleep(0.02)
        self.wfile.write(b"0\r\n\r\n")


def fake_upstream(failures, status=429):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    server.seen, server.lock, server.failures, server.failure_status = [], threading.Lock(), failures, status
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def post(port, body, session=SESSION, path="/v1/messages?beta=true"):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    headers = {"Content-Type": "application/json", "x-nb39-session": session, "Authorization": "Bearer nb39-local-proxy",
               "x-api-key": "client-dummy", "anthropic-version": "2023-06-01"}
    connection.request("POST", path, body=json.dumps(body).encode(), headers=headers)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return response, data


def request_body(model=MODEL):
    return {"model": model, "messages": [{"role": "user", "content": "hi"}], "system": [{"type": "text", "text": "s"}] * 3,
            "tools": [{"name": "Bash"}] * 6, "max_tokens": 32000, "thinking": {"type": "adaptive", "display": "updates"},
            "output_config": {"effort": "high"}, "stream": True}


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        patches = [mock.patch.object(C, "WORK", Path(self.work.name)), mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": KEY}),
                   mock.patch.object(P, "RETRY_WAITS", (0.05, 0.05))]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.addCleanup(self.work.cleanup)

    def run_proxy(self, upstream):
        patch = mock.patch.object(P, "UPSTREAM", f"http://127.0.0.1:{upstream.server_address[1]}")
        patch.start()
        self.addCleanup(patch.stop)
        proxy = P.start(0)
        self.addCleanup(P.stop, proxy)
        self.addCleanup(upstream.server_close)
        self.addCleanup(upstream.shutdown)
        return proxy.server_address[1]

    def log_lines(self):
        path = P.log_path(*SESSION.split("/"))
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_relay_retry_rewrite_and_log(self):
        upstream = fake_upstream(failures=1)
        port = self.run_proxy(upstream)
        response, data = post(port, request_body())
        self.assertEqual(response.status, 200)
        self.assertEqual(data, CANNED_BYTES)  # byte-identical after de-chunking
        self.assertEqual(len(upstream.seen), 2)  # 429, then success
        sent = upstream.seen[-1]
        forwarded = json.loads(sent["body"])
        self.assertEqual(forwarded["provider"], {"order": ["DeepSeek"], "allow_fallbacks": False})
        self.assertNotIn("thinking", forwarded)
        self.assertEqual(forwarded["reasoning"], {"effort": "high"})
        self.assertEqual(forwarded["model"], MODEL)
        self.assertEqual(forwarded["output_config"], {"effort": "high"})
        self.assertEqual(len(forwarded["tools"]), 6)
        self.assertEqual(sent["path"], "/v1/messages?beta=true")
        self.assertEqual(sent["headers"]["authorization"], "Bearer " + KEY)
        for name in ("x-nb39-session", "x-api-key"):
            self.assertNotIn(name, sent["headers"])
        self.assertEqual(sent["headers"]["anthropic-version"], "2023-06-01")
        (line,) = self.log_lines()
        self.assertEqual(line["session"], SESSION)
        self.assertEqual(line["model"], MODEL)
        self.assertEqual(line["provider_requested"], "DeepSeek")
        self.assertEqual(line["provider_served"], "DeepSeek")
        self.assertEqual(line["status"], 200)
        self.assertEqual([a["status"] for a in line["attempts"]], [429, 200])
        self.assertEqual(line["attempts"][0]["wait_seconds"], 0.05)
        self.assertIsNone(line["attempts"][1]["wait_seconds"])
        self.assertIn("slow down", line["attempts"][0]["error"])
        self.assertEqual(line["message_id"], "gen-123")
        self.assertEqual(line["stop_reason"], "end_turn")
        self.assertEqual(line["usage"], dict(input_tokens=4479, output_tokens=76, cache_read_input_tokens=12,
                                             cache_creation_input_tokens=0, thinking_tokens=37))
        self.assertEqual(line["cost_usd"], 0.00071745)
        self.assertEqual(line["request_sha256"], hashlib.sha256(sent["body"]).hexdigest())
        self.assertEqual(line["request_settings"]["max_tokens"], 32000)
        self.assertEqual((line["request_settings"]["messages_count"], line["request_settings"]["system_count"],
                          line["request_settings"]["tools_count"]), (1, 3, 6))
        for name in ("messages", "system", "tools", "thinking"):
            self.assertNotIn(name, line["request_settings"])
        self.assertFalse(line["rejected"])
        self.assertIsNone(line["error_text"])
        self.assertTrue(line["start_utc"] <= line["end_utc"])
        summary = P.summarize(P.log_path(*SESSION.split("/")))
        self.assertEqual((summary["requests"], summary["rejected"], summary["retries"], summary["errors"]), (1, 0, 1, 0))
        self.assertEqual(summary["providers_served"], ["DeepSeek"])

    def test_rejects_other_models_and_never_logs_the_key(self):
        upstream = fake_upstream(failures=0)
        port = self.run_proxy(upstream)
        response, data = post(port, request_body("claude-haiku-5-5"))
        self.assertEqual(response.status, 400)
        error = json.loads(data)
        self.assertEqual(error["type"], "error")
        self.assertEqual(error["error"]["type"], "invalid_request_error")
        self.assertEqual(upstream.seen, [])
        (line,) = self.log_lines()
        self.assertTrue(line["rejected"])
        self.assertEqual(line["status"], 400)
        self.assertEqual(line["model"], "claude-haiku-5-5")
        post(port, request_body())
        post(port, request_body(), session="../../escape/x/y")  # malformed session id must not choose a path
        self.assertTrue((Path(self.work.name) / "openrouter" / "unattributed.jsonl").is_file())
        for path in Path(self.work.name).rglob("*"):
            if path.is_file():
                self.assertNotIn(KEY.encode(), path.read_bytes(), path)
        self.assertNotIn("OPENROUTER_API_KEY", C.session_environment())

    def test_count_tokens_passes_through_with_the_same_rewrite(self):
        upstream = fake_upstream(failures=0)
        port = self.run_proxy(upstream)
        post(port, request_body(), path="/v1/messages/count_tokens")
        self.assertEqual(upstream.seen[0]["path"], "/v1/messages/count_tokens")
        self.assertEqual(json.loads(upstream.seen[0]["body"])["provider"]["order"], ["DeepSeek"])
        response, _ = post(port, request_body(), path="/v2/other")
        self.assertEqual(response.status, 400)

    def test_error_passes_through_after_the_last_retry(self):
        upstream = fake_upstream(failures=99, status=503)
        port = self.run_proxy(upstream)
        response, data = post(port, request_body())
        self.assertEqual(response.status, 503)
        self.assertIn(b"slow down", data)
        self.assertEqual(len(upstream.seen), 3)  # first try plus the two patched waits
        (line,) = self.log_lines()
        self.assertEqual([a["status"] for a in line["attempts"]], [503, 503, 503])
        self.assertEqual(line["status"], 503)
        self.assertIn("slow down", line["error_text"])
        self.assertEqual(P.summarize(P.log_path(*SESSION.split("/")))["errors"], 1)

    def test_connection_errors_are_retried_then_reported(self):
        upstream = fake_upstream(failures=0)
        port = self.run_proxy(upstream)
        upstream.shutdown()
        upstream.server_close()
        response, data = post(port, request_body())
        self.assertEqual(response.status, 502)
        (line,) = self.log_lines()
        self.assertEqual(len(line["attempts"]), 3)
        self.assertTrue(all(a["status"] is None and a["error"] for a in line["attempts"]))

    def test_start_is_idempotent(self):
        first = P.start(0)
        self.addCleanup(P.stop, first)
        port = first.server_address[1]
        self.assertIs(P.start(port), first)

    def test_retry_after_header_overrides_schedule(self):
        self.assertEqual(P.retry_wait(0, "7"), 7)
        self.assertEqual(P.retry_wait(0, "9999"), 300)
        self.assertEqual(P.retry_wait(1, None), 0.05)
        self.assertEqual(P.retry_wait(0, "garbage"), 0.05)


if __name__ == "__main__":
    unittest.main()
