"""Stream provider-exposed reasoning and unmodified candidate weights from a free model."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
import requests
from experiment import ROOT, PROMPT, SCHEMA, SHAPES, evaluate, dump
from trace_calls import trace

MODEL = "nvidia/nemotron-3.5-super-vl:free"
CANONICAL = "nvidia/nemotron-3.5-super-vl-20261015"
OUT = ROOT / "data" / "nemotron-free"
OUT.mkdir(parents=True,exist_ok=True)
REQUEST = {"model":MODEL,"messages":[{"role":"user","content":PROMPT}],"temperature":0,"max_tokens":65536,
           "reasoning":{"enabled":True,"exclude":False},
           "response_format":{"type":"json_schema","json_schema":{"name":"complete_mlp_weights","strict":True,"schema":SCHEMA}},
           "tool_choice":"none","plugins":[],"provider":{"only":["nvidia"],"allow_fallbacks":False,
           "max_price":{"prompt":0,"completion":0,"request":0}},"stream":True,"stream_options":{"include_usage":True}}
KEY = hashlib.sha256(json.dumps(REQUEST,sort_keys=True).encode()).hexdigest()
CACHE = OUT / "editor_cache.json"


def run():
    if CACHE.exists():
        record = json.loads(CACHE.read_text(encoding="utf-8"))
        assert record["cache_key"] == KEY
        print("Replaying cached response; no fresh model call.",flush=True)
        validate(record)
        return
    base = "https://openrouter.ai/api/v1"
    meta_response = requests.get(base + "/models",timeout=20)
    meta_response.raise_for_status()
    meta = next(m for m in meta_response.json()["data"] if m["id"] == MODEL)
    assert meta["canonical_slug"] == CANONICAL
    assert all(float(meta["pricing"][k])==0 for k in ("prompt","completion"))
    assert "structured_outputs" in meta["supported_parameters"]
    dump(OUT / "model_metadata.json",meta)
    dump(OUT / "request.json",REQUEST)
    events,parts,reasons,details = [],[],[],[]
    finished = False
    error = None
    usage = None
    status_code = None
    t0 = time.monotonic()
    start = dt.datetime.now(dt.timezone.utc)
    first_reasoning = None
    first_content = None
    last_saved = 0
    last_printed = 0
    state = {"status":"running","model":MODEL,"canonical_slug":CANONICAL,"started_utc":start.isoformat(),
             "pid":os.getpid(),"reasoning_characters":0,"weight_response_characters":0,"reasoning_excluded":False,
             "tools_enabled":[],"price_cap":0,"paid_fallback":False}
    dump(OUT / "progress.json",state)
    print(json.dumps(state),flush=True)
    # The JSONL source preserves every provider field, including reasoning_details.
    with (OUT / "stream_events.jsonl").open("w",encoding="utf-8") as raw_log, \
         (OUT / "reasoning.txt").open("w",encoding="utf-8") as reasoning_file, \
         (OUT / "weights_output.json").open("w",encoding="utf-8") as content_file, \
         (OUT / "reasoning_details.jsonl").open("w",encoding="utf-8") as details_file:
        try:
            with requests.post(base + "/chat/completions",json=REQUEST,
                               headers={"Authorization":"Bearer " + os.environ["OPENROUTER_API_KEY"]},
                               stream=True,timeout=(20,120)) as response:
                status_code = response.status_code
                if not response.ok:
                    error = {"http_status":response.status_code,"body":response.text}
                else:
                    response.encoding = "utf-8"
                    for line in response.iter_lines(decode_unicode=True,chunk_size=1):
                        elapsed = time.monotonic()-t0
                        if line and line.startswith("data:"):
                            body = line[5:].strip()
                            if body == "[DONE]":
                                finished = True
                                break
                            event = json.loads(body)
                            events.append(event)
                            raw_log.write(json.dumps({"elapsed_seconds":elapsed,"event":event},ensure_ascii=False)+"\n")
                            raw_log.flush()
                            if event.get("error"):
                                error = event["error"]
                            if event.get("usage"):
                                usage = event["usage"]
                            for choice in event.get("choices",[]):
                                delta = choice.get("delta",{})
                                primary = delta.get("reasoning") or delta.get("reasoning_content")
                                detail_items = delta.get("reasoning_details") or []
                                for item in detail_items:
                                    details.append(item)
                                    details_file.write(json.dumps({"elapsed_seconds":elapsed,"detail":item},ensure_ascii=False)+"\n")
                                if detail_items:
                                    details_file.flush()
                                # A chunk can include the same text in both fields; render it once.
                                reason = primary or "".join(item.get("text",item.get("summary","")) for item in detail_items
                                                             if item.get("type") in ("reasoning.text","reasoning.summary"))
                                if reason:
                                    if first_reasoning is None: first_reasoning = elapsed
                                    reasons.append(reason)
                                    reasoning_file.write(reason)
                                    reasoning_file.flush()
                                    state["reasoning_characters"] += len(reason)
                                content = delta.get("content")
                                if content:
                                    if first_content is None: first_content = elapsed
                                    parts.append(content)
                                    content_file.write(content)
                                    content_file.flush()
                                    state["weight_response_characters"] += len(content)
                        if elapsed-last_saved >= 2:
                            state["elapsed_seconds"] = round(elapsed,2)
                            dump(OUT / "progress.json",state)
                            last_saved = elapsed
                        if line and elapsed-last_printed >= 30:
                            print(json.dumps({k:state[k] for k in ("status","reasoning_characters","weight_response_characters")} |
                                             {"elapsed_seconds":round(elapsed,1)}),flush=True)
                            last_printed = elapsed
        except (requests.RequestException,ValueError) as exc:
            error = {"exception_type":type(exc).__name__,"message":str(exc)}
    end = dt.datetime.now(dt.timezone.utc)
    record = {"cache_key":KEY,"request":REQUEST,"canonical_slug":CANONICAL,"events":events,
              "answer":"".join(parts),"reasoning":"".join(reasons),"reasoning_details":details,
              "stream_complete":finished,"error":error,"usage":usage,"http_status":status_code,
              "started_utc":start.isoformat(),"finished_utc":end.isoformat(),"wall_seconds":time.monotonic()-t0,
              "first_reasoning_seconds":first_reasoning,"first_content_seconds":first_content}
    dump(CACHE,record)
    state.update({"status":"response_finished" if finished else "incomplete","finished_utc":end.isoformat(),
                  "elapsed_seconds":record["wall_seconds"],"usage":usage,"error":error})
    dump(OUT / "progress.json",state)
    trace(KEY,MODEL,REQUEST,{"answer":record["answer"],"exposed_reasoning":record["reasoning"]},start,end,usage)
    validate(record)


def validate(record):
    events = record["events"]
    tool_calls = [c["delta"]["tool_calls"] for e in events for c in e.get("choices",[]) if c.get("delta",{}).get("tool_calls")]
    finish = [c["finish_reason"] for e in events for c in e.get("choices",[]) if c.get("finish_reason")]
    actual_models = sorted({e["model"] for e in events if e.get("model")})
    providers = sorted({e["provider"] for e in events if e.get("provider")})
    error = None
    try:
        assert not record["error"],"Transport/provider error"
        assert record["stream_complete"],"Incomplete response stream"
        assert not tool_calls,"Tool-call output rejected; no tool was executed"
        assert actual_models == [MODEL],"Unexpected model"
        assert providers == ["Nvidia"],"Unexpected provider"
        assert finish and set(finish)=={"stop"},"Incomplete response; finish reasons="+str(finish)
        payload = json.loads(record["answer"])
        assert isinstance(payload,dict) and set(payload)==set(SHAPES),"Wrong tensor keys"
        tensors = {}
        for name,shape in SHAPES.items():
            a = np.asarray(payload[name])
            assert list(a.shape)==shape,"Wrong shape: "+name
            assert a.dtype.kind in "ifu" and np.isfinite(a).all(),"Non-numeric/non-finite value"
            tensors[name] = a.astype(np.float64)
        assert sum(a.size for a in tensors.values())==388
        np.savez(OUT / "candidate.npz",**tensors)
        with np.load(OUT / "candidate.npz") as saved:
            assert all(np.array_equal(saved[name],tensors[name]) for name in SHAPES)
    except (AssertionError,ValueError,TypeError) as exc:
        error = str(exc) or type(exc).__name__
    audit = {"model":MODEL,"canonical_slug":CANONICAL,"actual_models":actual_models,"providers":providers,
             "format_error":error,"finish_reasons":finish,"parameters":388,"training_steps":0,
             "tool_call_events":len(tool_calls),"tester_changed_candidate_weights":False,"saved_values_equal_response":error is None,
             "reasoning_characters":len(record["reasoning"]),"reasoning_details_chunks":len(record["reasoning_details"]),
             "reasoning_excluded":False,"usage":record["usage"],"wall_seconds":record["wall_seconds"],
             "first_reasoning_seconds":record["first_reasoning_seconds"],"first_content_seconds":record["first_content_seconds"]}
    dump(OUT / "audit.json",audit)
    print(json.dumps(audit,indent=2),flush=True)
    if error is None:
        evaluate(out=OUT,model=MODEL,effort="reasoning enabled; provider default",display_name="Nemotron")


if __name__=="__main__":
    run()
