"""Retry the single empty CLI failure from its original, unmodified history."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

import smoke_study as s
import full_study as f
import tagged_kimi_pilot as p

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/simple_prose_v3_retry'
PRIVATE=ROOT/'data/local_inputs/simple_prose_v3_retry'
PROTOCOL='expanded-v3-authorized-empty-failure-retry'
MODEL='gpt-6.1-sol'
ITEM='14-seti'
TURN=2
MAX_NEW_CALLS=1


def register():
    old=s.load(ROOT/'data/simple_prose_v3_full/responses'/ITEM/MODEL/'02.json')
    assert old['status']!='ok' and not old['text']
    previous=s.load(ROOT/'data/simple_prose_v3_full/responses'/ITEM/MODEL/'01.json')
    request=s.load(ROOT/old['private_cache'])['request']
    session_path=next((Path.home()/'.codex/sessions').rglob('*'+previous['session_id']+'*.jsonl'))
    rows=s.json_events(session_path.read_text(encoding='utf-8'))
    first=next(row['payload']['turn_id'] for row in rows if row['type']=='event_msg' and row['payload'].get('type')=='task_complete')
    design=dict(protocol=PROTOCOL,item_id=ITEM,model=MODEL,turn=TURN,effort='high',maximum_fresh_generation_calls=1,
        retry_of=old['request_sha256'],original_session_id=previous['session_id'],last_included_native_turn_id=first,
        source_sha256=old['source_sha256'],stdin_sha256=s.sha(request['stdin']),
        cli_version=subprocess.check_output([s.shutil.which('codex.cmd'),'--version'],text=True).strip(),
        method='Use the installed Codex app-server CLI thread/fork lastTurnId operation only to restore the first completed turn. Generate using codex exec resume, high effort, original exact continuation, all tools/search disabled.',
        original_preservation='Do not change original session, failed response or later successful turns. Store the retry separately and use one explicit overlay for subsequent paid classification.',
        deviation='The replacement is a fork at the original first-turn boundary, collected later. The existing turns 3–5 remain on their original branch and did not see the replacement. Retain an analysis excluding this entire model/article block.',
        failures='One fresh generation attempt. Do not retry for prose, missing tags or classifier labels. Preserve any new failure.',
        cache='Full exact request and response together, keyed by request hash; publisher-bearing control transcripts remain private.')
    path=OUT/'protocol.json'
    if path.exists():assert all(s.load(path)[k]==v for k,v in design.items())
    else:s.save(path,dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),**design))
    return design,old,previous,request,session_path


def restore_prefix(design,previous,source_path):
    saved=OUT/'fork.json'
    if saved.exists():return s.load(saved)
    original_bytes=source_path.read_bytes()
    opts=s.codex_options()
    opts=[x for x in opts if x not in ['--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral','--strict-config']]
    command=[s.shutil.which('codex.cmd'),'app-server','--stdio',*opts]
    PRIVATE.mkdir(parents=True,exist_ok=True)
    transcript=PRIVATE/'control.jsonl';error=PRIVATE/'control.stderr.txt'
    inbox=queue.Queue()
    with error.open('w',encoding='utf-8') as stderr,transcript.open('w',encoding='utf-8') as log:
        child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,
            text=True,encoding='utf-8',errors='replace',cwd=s.isolation_dir(),env=s.clean_env())
        def reader():
            for line in child.stdout:
                log.write(line);log.flush()
                try:inbox.put(json.loads(line))
                except ValueError:pass
            inbox.put({'transport_closed':True})
        threading.Thread(target=reader,daemon=True).start()
        def rpc(ident,method,params):
            child.stdin.write(json.dumps(dict(id=ident,method=method,params=params))+'\n');child.stdin.flush()
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                row=inbox.get(timeout=max(.1,deadline-time.monotonic()))
                if row.get('transport_closed'):raise RuntimeError('Native control process exited; inspect private stderr')
                if row.get('id')==ident:
                    if 'error' in row:raise RuntimeError('Native session-control failure; inspect private control transcript')
                    return row['result']
            raise TimeoutError('Native session-control timeout')
        try:
            rpc(1,'initialize',dict(clientInfo=dict(name='linkedin40-recovery',version='1.0'),capabilities=dict(experimentalApi=True)))
            child.stdin.write(json.dumps(dict(method='initialized',params={}))+'\n');child.stdin.flush()
            result=rpc(2,'thread/fork',dict(threadId=design['original_session_id'],lastTurnId=design['last_included_native_turn_id'],
                cwd=str(s.isolation_dir()),model=MODEL,baseInstructions=s.NEUTRAL,developerInstructions='',
                config={'model_reasoning_effort':'high','web_search':'disabled','project_doc_max_bytes':0,'personality':'none'},
                ephemeral=False))
        finally:
            try:child.stdin.close()
            except OSError:pass
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20)
                child.wait(timeout=10)
    assert source_path.read_bytes()==original_bytes,'Original session changed during fork'
    return validate_fork(design,previous,source_path,result,original_bytes)


def validate_fork(design,previous,source_path,result,original_bytes):
    saved=OUT/'fork.json'
    thread=result['thread'];fork_path=Path(thread['path'])
    native=s.json_events(fork_path.read_text(encoding='utf-8'))
    source=s.json_events(original_bytes.decode('utf-8'))
    cutoff=next(i for i,r in enumerate(source) if r['type']=='event_msg' and r['payload'].get('type')=='task_complete' and r['payload']['turn_id']==design['last_included_native_turn_id'])
    original_items=[r['payload'] for r in source[:cutoff+1] if r['type']=='response_item']
    fork_items=[r['payload'] for r in native if r['type']=='response_item']
    meta=native[0]['payload'];base=meta.get('history_base')
    if not fork_items and base:
        assert base['thread_id']==previous['session_id']
        assert base['end_ordinal_exclusive']==source[cutoff]['ordinal']+1
        prefix=s.json_events(original_bytes[:base['end_byte_offset']].decode('utf-8'))
        (PRIVATE/'original_first_turn.jsonl').write_bytes(original_bytes[:base['end_byte_offset']])
        assert prefix==source[:cutoff+1]
        fork_items=[r['payload'] for r in prefix if r['type']=='response_item']
    assert len(thread['turns'])==1 and thread['turns'][0]['id']==design['last_included_native_turn_id']
    assert original_items==fork_items,'Fork did not preserve the exact original first-turn message prefix'
    assistants=[r for r in fork_items if r.get('role')=='assistant' and r.get('phase')=='final_answer']
    assert len(assistants)==1
    text=''.join(block.get('text','') for block in assistants[0]['content'])
    assert text==previous['text']
    (PRIVATE/'restored_prefix.jsonl').write_bytes(fork_path.read_bytes())
    info=dict(original_session_id=previous['session_id'],fork_session_id=thread['id'],last_included_native_turn_id=design['last_included_native_turn_id'],
        exact_native_response_items_checked=True,original_session_unchanged=True,prior_assistant_messages=1,
        original_native_prefix_sha256=s.sha(s.canonical(original_items)),
        local_fork_path=str(fork_path),lazy_history_base=base,
        control_method='thread/fork lastTurnId; no model turn is started by the session-control CLI')
    s.save(saved,info);return info


def collect(max_new=MAX_NEW_CALLS):
    design,old,previous,old_request,source_path=register()
    target=OUT/'response.json'
    if target.exists():print('Existing retry retained; no fresh generation.');return s.load(target)
    assert max_new==1
    if (OUT/'generation.started.json').exists():raise RuntimeError('Unresolved retry start; inspect native output before any new call')
    fork=restore_prefix(design,previous,source_path)
    command=s.command(MODEL,conversation=True,session_id=fork['fork_session_id'])
    request=dict(old_request,protocol=PROTOCOL,command=command,prior_session_id=fork['fork_session_id'],
        retry_of=old['request_sha256'],native_prefix_sha256=fork['original_native_prefix_sha256'])
    key=s.sha(s.canonical(request));private=PRIVATE/'cache'/f'{key}.json'
    start=datetime.now(timezone.utc);tick=time.monotonic();trace=p.make_tracer()
    s.save(OUT/'generation.started.json',dict(request_sha256=key,started_at=start.isoformat()))
    s.save(PRIVATE/'started'/f'{key}.json',dict(request_sha256=key,request=request,started_at=start.isoformat()))
    print('Retrying',ITEM,MODEL,TURN,'from exact first-turn prefix',flush=True)
    with (OUT/'response.jsonl').open('w',encoding='utf-8') as out,(OUT/'response.stderr.txt').open('w',encoding='utf-8') as err:
        child=subprocess.run(command,input=request['stdin'],stdout=out,stderr=err,cwd=s.isolation_dir(),env=s.clean_env(),
                             text=True,encoding='utf-8',errors='replace',timeout=s.TIMEOUT_SECONDS)
    end=datetime.now(timezone.utc);raw=(OUT/'response.jsonl').read_text(encoding='utf-8')
    record=f.corrected(s.parse_result(MODEL,raw),MODEL,previous['raw_usage'],previous.get('reported_session_cost_usd'))
    status='ok' if child.returncode==0 and record['completed'] and record['text'] else 'unreadable_or_failed'
    if record['tool_events'] or any(cat.get('tools') or cat.get('mcp_servers') or cat.get('skills') for cat in record['catalogues']):status='tool_protocol_violation'
    assert record['session_id']==fork['fork_session_id']
    record.update(p.parse_post(record['text']))
    record.update(status=status,requested_model=MODEL,item_id=ITEM,turn=TURN,effort='high',retry_of=old['request_sha256'],
        request_sha256=key,prompt_sha256=s.sha(request['stdin']),source_sha256=old['source_sha256'],
        started_at=start.isoformat(),ended_at=end.isoformat(),seconds=time.monotonic()-tick,exit_code=child.returncode,
        timeout=False,private_cache=private.relative_to(ROOT).as_posix())
    s.save(private,p.full_cache_record(key,request,record))
    public=dict(request);template=s.load(ROOT/'data/simple_prose_v3_full/preregistration.json')['initial_template']
    public['messages']=[dict(m,content=template) if i==0 else m for i,m in enumerate(request['messages'])]
    record.update(request=public,request_redacted=True)
    s.save(target,record)
    p.PROTOCOL=PROTOCOL
    traced=trace(key,request,record,start,end);s.save(OUT/'tracing.json',dict(request_sha256=key,status=traced))
    (OUT/'generation.started.json').unlink();(PRIVATE/'started'/f'{key}.json').unlink()
    (OUT/'OUTPUT.md').write_text('# Retry of the empty SETI generation\n\n'+(record['post_body'] or record['text'])+'\n',encoding='utf-8',newline='\n')
    print('Retry result:',status,record['format_status'],'words',len(s.words(record['text'])),flush=True)
    return record


if __name__=='__main__':collect()
