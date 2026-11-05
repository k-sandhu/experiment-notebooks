"""Optional tracing; never persist credentials and never trace a cache replay."""
import datetime as dt
import hashlib
import json
import os
import requests

HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3300").rstrip("/")
AUTH = (os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", ""))
ON = False
if all(AUTH):
    try:
        ON = requests.get(HOST + "/api/public/health", timeout=2).ok
    except requests.RequestException:
        pass


def trace(key, model, request, response, start, end, usage=None):
    if not ON:
        return
    def a(k, v):
        return {"key": k, "value": {"stringValue": v if isinstance(v, str) else json.dumps(v)}}
    attrs = [a("langfuse.observation.type", "generation"), a("langfuse.observation.model.name", model),
             a("langfuse.observation.input", request), a("langfuse.observation.output", response),
             a("langfuse.trace.name", "Tiny SQL weights-only experiment"),
             a("langfuse.trace.metadata.cache_key", key), a("langfuse.session.id", "tiny-sql-2208")]
    if usage:
        attrs.append(a("langfuse.observation.usage_details", usage))
    span = {"traceId": hashlib.sha256(f"tiny-sql-2208|{key}".encode()).hexdigest()[:32],
            "spanId": hashlib.sha256(f"tiny-sql-2208|{key}|gen|0".encode()).hexdigest()[:16],
            "name": model, "kind": 1, "startTimeUnixNano": str(int(start.timestamp()*1e9)),
            "endTimeUnixNano": str(int(end.timestamp()*1e9)), "attributes": attrs}
    try:
        requests.post(HOST + "/api/public/otel/v1/traces", auth=AUTH, timeout=10,
                      json={"resourceSpans": [{"resource": {"attributes": [a("service.name", "tiny-model-experiments")]},
                                               "scopeSpans": [{"scope": {"name": "tiny-sql-2208"}, "spans": [span]}]}]})
    except requests.RequestException:
        pass
