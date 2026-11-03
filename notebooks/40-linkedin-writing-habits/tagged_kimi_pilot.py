"""Twenty-call preview of the tagged prose prompt; no full-study entry point."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time

import smoke_study as s
import full_study as f

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data/simple_prose_v3_kimi_pilot'
PRIVATE = ROOT / 'data/local_inputs/simple_prose_v3_kimi_pilot'
NOTEBOOK = '40-linkedin-writing-habits'
MODELS = list(s.MODELS)
N_POSTS = 5
MAX_NEW_CALLS = 1
PROTOCOL = 'simple-prose-v3-kimi-tagged-pilot'


def parse_post(raw):
    """Separate a single tagged post without guessing when tags are ambiguous."""
    tags = re.findall(r'</?linkedin_post\b[^>]*>', raw, flags=re.I)
    match = re.fullmatch(r'(.*?)<linkedin_post>(.*?)</linkedin_post>(.*?)', raw, flags=re.S)
    if tags != ['<linkedin_post>', '</linkedin_post>'] or not match or not match[2].strip():
        return dict(post_body=None, text_before=None, text_after=None,
                    format_status='invalid_tags', extra_text_present=None)
    before, body, after = match.groups()
    extra = bool(before.strip() or after.strip())
    return dict(post_body=body.strip(), text_before=before, text_after=after,
                format_status='extra_text' if extra else 'ok', extra_text_present=extra)


def register():
    article = next(x for x in s.load(ROOT/'data/main/articles.json') if x['item_id']=='01-kimi')
    source = (ROOT/article['local_input']).read_text(encoding='utf-8')
    assert s.sha(source)==article['text_sha256']
    initial = (ROOT/'data/prompt_conditions/simple_prose_v3.txt').read_text(encoding='utf-8')
    followup = (ROOT/'data/prompt_conditions/simple_prose_v3_followup.txt').read_text(encoding='utf-8')
    assert initial.count('{{complete_article_text}}')==1
    versions = {name:subprocess.run([s.shutil.which(name+'.cmd') or s.shutil.which(name), '--version'],
                    capture_output=True, text=True, check=True).stdout.strip() for name in ['codex','claude']}
    design = dict(protocol=PROTOCOL, models=MODELS, effort='high', article=article,
                  initial_template=initial, followup=followup, initial_sha256=s.sha(initial),
                  followup_sha256=s.sha(followup), posts_per_model=N_POSTS, planned_calls=20,
                  cli_versions=versions, classification_calls=0,
                  design='One new conversation per model; turns 2-5 use only the exact saved follow-up.',
                  failures='No content retries. Retain tag failures and outside text. Stop a model on CLI, tool or session failure.',
                  independence='Standalone posts are requested; prior drafts remain visible within a conversation.',
                  cache='Private hash-keyed records hold full requests and responses together. Public derivatives redact publisher input.',
                  scope='Kimi preview only. Do not start the 20-topic study from this script.')
    path = OUT/'preregistration.json'
    if path.exists():
        old=s.load(path)
        assert all(old[k]==v for k,v in design.items()), 'Pilot changed after registration'
    else:
        s.save(path, dict(registered_at_utc=datetime.now(timezone.utc).isoformat(), **design))
    return design, source


def make_tracer():
    """Optional local OTLP tracing, with stable IDs shared by the backfill helper."""
    import requests
    host=os.environ.get('LANGFUSE_HOST','http://localhost:3300').rstrip('/')
    auth=(os.environ.get('LANGFUSE_PUBLIC_KEY',''),os.environ.get('LANGFUSE_SECRET_KEY',''))
    try:
        enabled=all(auth) and requests.get(host+'/api/public/health',timeout=2).ok
    except requests.RequestException:
        enabled=False

    def trace(key, request, response, start, end):
        if not enabled:
            return 'unavailable'
        def attr(k,v):
            return {'key':k,'value':{'stringValue':v if isinstance(v,str) else json.dumps(v,default=str)}}
        inp=response.get('input_total'); cached=response.get('cache_read_tokens')
        usage={}
        writes=response.get('cache_write_tokens')
        if isinstance(inp,int) and isinstance(cached,int):
            usage.update(input=inp-cached-(writes or 0),input_cache_read=cached)
            if isinstance(writes,int):usage['input_cache_creation']=writes
        output=response.get('output_tokens')
        native=response.get('raw_usage',{})
        reasoning=response.get('per_turn_usage',{}).get('reasoning_output_tokens')
        if reasoning is None:
            reasoning=native.get('output_tokens_details',{}).get('thinking_tokens',native.get('reasoning_output_tokens'))
        if isinstance(output,int):usage['output']=output-(reasoning or 0)
        if isinstance(reasoning,int):usage['output_reasoning']=reasoning
        attrs=[attr('langfuse.observation.type','generation'),
               attr('langfuse.observation.model.name',request['model']),
               attr('langfuse.observation.input',request),
               attr('langfuse.observation.output',response['text']),
               attr('langfuse.trace.name','40 '+PROTOCOL),
               attr('langfuse.environment','notebook'),
               attr('langfuse.trace.metadata.notebook',NOTEBOOK),
               attr('langfuse.trace.metadata.cache_key',key),
               attr('langfuse.session.id',NOTEBOOK+'/'+response['session_id']),
               attr('langfuse.observation.metadata.condition',PROTOCOL),
               attr('langfuse.observation.usage_details',usage)]
        cost=response.get('reported_cost_usd')
        if cost is not None:attrs.append(attr('langfuse.observation.cost_details',{'total':cost}))
        if response['status']!='ok':
            attrs.extend([attr('langfuse.observation.level','ERROR'),attr('langfuse.observation.status_message',response['status'])])
        span=dict(traceId=hashlib.sha256(f'{NOTEBOOK}|{key}'.encode()).hexdigest()[:32],
                  spanId=hashlib.sha256(f'{NOTEBOOK}|{key}|gen|0'.encode()).hexdigest()[:16],
                  name=PROTOCOL,kind=1,attributes=attrs,
                  startTimeUnixNano=str(int(start.timestamp()*1e9)),endTimeUnixNano=str(int(end.timestamp()*1e9)))
        body={'resourceSpans':[{'resource':{'attributes':[attr('service.name','experiment-notebooks')]},
                              'scopeSpans':[{'scope':{'name':NOTEBOOK},'spans':[span]}]}]}
        try:
            result=requests.post(host+'/api/public/otel/v1/traces',json=body,auth=auth,timeout=10)
            return 'sent' if result.ok else 'failed'
        except requests.RequestException:
            return 'failed'
    return trace


def full_cache_record(key, request, response):
    """Expose per-turn usage and known cost in the common backfill cache layout."""
    native=response.get('raw_usage',{})
    reasoning=response.get('per_turn_usage',{}).get('reasoning_output_tokens')
    if reasoning is None:
        reasoning=native.get('output_tokens_details',{}).get('thinking_tokens',native.get('reasoning_output_tokens'))
    usage={'prompt_tokens':response.get('input_total'),
           'cached_input_tokens':response.get('cache_read_tokens'),
           'cache_write_input_tokens':response.get('cache_write_tokens'),
           'completion_tokens':response.get('output_tokens'),'reasoning_output_tokens':reasoning}
    return dict(request_sha256=key,request=request,response=response,
                usage={k:v for k,v in usage.items() if isinstance(v,int)},
                reported_cost_usd=response.get('reported_cost_usd'))


def collect(max_new=MAX_NEW_CALLS, design=None, source=None, write_export=True,
            continue_capacity_failures=False):
    assert 0<=max_new<=20
    if design is None:design,source=register()
    assert source is not None
    item_id=design['article']['item_id']
    initial=design['initial_template'].replace('{{complete_article_text}}',source)
    isolation=s.isolation_dir()
    s.isolation_dir=lambda:isolation
    trace=make_tracer()
    lock=threading.Lock(); counter={'new':0};events=[]

    def worker(model):
        session=None;previous_usage={};previous_cost=0.0;history=[]
        for turn in range(1,N_POSTS+1):
            prompt=initial if turn==1 else design['followup']
            messages=history+[{'role':'user','content':prompt}]
            cmd=s.command(model,conversation=True,session_id=session)
            request=dict(protocol=PROTOCOL,model=model,effort='high',turn=turn,
                         item_id=item_id,source_sha256=design['article']['text_sha256'],
                         system_prompt=s.NEUTRAL,stdin=prompt,messages=messages,command=cmd,
                         cwd=str(isolation),prior_session_id=session,tools='disabled',web_search='disabled',
                         history_representation='Exact user and visible assistant text; native CLI manages thinking and runtime metadata.')
            key=s.sha(s.canonical(request))
            private=PRIVATE/'cache'/f'{key}.json'
            stem=OUT/'responses'/item_id/model/f'{turn:02d}'
            public_path=stem.with_suffix('.json')
            if public_path.exists():
                record=s.load(public_path)
                assert record['request_sha256']==key and private.exists()
                cached=s.load(private)
                assert cached['request']==request and cached['response']['text']==record['text']
            else:
                if stem.with_suffix('.started.json').exists():
                    raise RuntimeError(f'Unresolved request: {model}/{turn}; do not regenerate')
                with lock:
                    if counter['new']>=max_new:return
                    counter['new']+=1
                start=datetime.now(timezone.utc);tick=time.monotonic()
                s.save(stem.with_suffix('.started.json'),dict(request_sha256=key,started_at=start.isoformat()))
                s.save(PRIVATE/'started'/f'{key}.json',dict(request_sha256=key,request=request,started_at=start.isoformat()))
                print('START',model,turn,flush=True)
                timed_out=False
                with stem.with_suffix('.jsonl').open('w',encoding='utf-8') as out,stem.with_suffix('.stderr.txt').open('w',encoding='utf-8') as err:
                    child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=isolation,
                        env=s.clean_env(),text=True,encoding='utf-8',errors='replace',
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0)
                    try:child.communicate(prompt,timeout=s.TIMEOUT_SECONDS)
                    except subprocess.TimeoutExpired:
                        timed_out=True
                        if os.name=='nt':subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20)
                        else:child.kill()
                        child.wait(timeout=20)
                end=datetime.now(timezone.utc)
                raw=stem.with_suffix('.jsonl').read_text(encoding='utf-8')
                record=f.corrected(s.parse_result(model,raw),model,previous_usage,previous_cost)
                status='ok' if child.returncode==0 and record['completed'] and record['text'] and not timed_out else 'unreadable_or_failed'
                if record['tool_events']:status='tool_protocol_violation'
                if any(cat.get('tools') or cat.get('mcp_servers') or cat.get('skills') for cat in record['catalogues']):status='catalogue_protocol_violation'
                if session is not None and record['session_id']!=session:status='session_protocol_violation'
                record.update(parse_post(record['text']))
                record.update(status=status,requested_model=model,item_id=item_id,turn=turn,effort='high',
                              request_sha256=key,prompt_sha256=s.sha(prompt),source_sha256=design['article']['text_sha256'],
                              started_at=start.isoformat(),ended_at=end.isoformat(),seconds=time.monotonic()-tick,
                              exit_code=child.returncode,timeout=timed_out,
                              private_cache=private.relative_to(ROOT).as_posix())
                s.save(private,full_cache_record(key,request,record))
                # Public derivative contains full template/settings, without redistributing the publisher's article.
                public_request=dict(request)
                public_request['stdin']=design['initial_template'] if turn==1 else prompt
                public_request['messages']=[dict(m,content=design['initial_template']) if i==0 else m for i,m in enumerate(messages)]
                record.update(request=public_request,request_redacted=True,
                              request_redaction='Initial article text is replaced by its template placeholder; full request and response are in the private hash-keyed cache.')
                s.save(public_path,record)
                trace_status=trace(key,request,record,start,end)
                s.save(OUT/'tracing'/f'{key}.json',dict(request_sha256=key,status=trace_status))
                stem.with_suffix('.started.json').unlink()
                (PRIVATE/'started'/f'{key}.json').unlink()
                print('DONE',model,turn,status,record['format_status'],f"{record['seconds']:.1f}s",flush=True)
            if record['status']!='ok':
                native=stem.with_suffix('.jsonl').read_text(encoding='utf-8')
                if (continue_capacity_failures and not record['text'] and record['exit_code']==1
                        and 'Selected model is at capacity.' in native and session==record['session_id']):
                    # Retain the failed slot. Resume later numbered turns without a fabricated
                    # assistant message or another attempt at the failed generation.
                    history=messages
                    continue
                raise RuntimeError(f"{model}/{turn}: {record['status']}")
            history=messages+[{'role':'assistant','content':record['text']}]
            session=record['session_id'];previous_usage=record['raw_usage'];previous_cost=record.get('reported_session_cost_usd')

    with ThreadPoolExecutor(max_workers=len(MODELS)) as pool:
        futures={pool.submit(worker,model):model for model in MODELS}
        for future in as_completed(futures):
            try:future.result()
            except Exception as exc:
                events.append(dict(model=futures[future],error=str(exc)))
                print('ERROR',futures[future],str(exc),flush=True)
    s.save(OUT/'collection_events.json' if write_export else OUT/'collection_events'/f'{item_id}.json',events)
    if write_export:export()
    print('NEW CALLS',counter['new'],'ERRORS',len(events),flush=True)
    return dict(new_calls=counter['new'],errors=events)


def export():
    records=[s.load(p) for p in sorted((OUT/'responses').glob('*/*/*.json')) if '.started.' not in p.name]
    usage=[];preview=['# Expanded-constraints Kimi pilot\n\nTwenty requested posts: four models, five successive standalone drafts each. These are generated outputs for review.\n']
    for model in MODELS:
        part=sorted([r for r in records if r['requested_model']==model],key=lambda r:r['turn'])
        preview.append(f'## {model}\n')
        for r in part:
            warning='Tag format failure: raw response shown below.\n\n' if r['post_body'] is None else ''
            preview.append(f"### Post {r['turn']}\n\n{warning}{r['post_body'] if r['post_body'] is not None else r['text']}\n")
            if r['extra_text_present']:
                preview.append('Text before the post:\n\n'+r['text_before']+'\n\nText after the post:\n\n'+r['text_after']+'\n')
        warm=[r for r in part if r['turn']>1]
        total=sum(r['input_total'] or 0 for r in warm)
        reads=sum(r['cache_read_tokens'] or 0 for r in warm)
        costs=[r.get('reported_cost_usd') for r in part]
        usage.append(dict(model=model,posts=len(part),distinct_posts=len({s.normalise(r['post_body'] or r['text']) for r in part}),
                          valid_tagged_posts=sum(r['post_body'] is not None for r in part),
                          outside_text_posts=sum(bool(r['extra_text_present']) for r in part),
                          invalid_tag_posts=sum(r['post_body'] is None for r in part),
                          warm_input_tokens=total,warm_cache_read_tokens=reads,warm_cache_read_fraction=reads/total if total else None,
                          reported_cost_usd=sum(costs) if costs and all(c is not None for c in costs) else None))
    summary=dict(protocol=PROTOCOL,total_responses=len(records),successful_cli_responses=sum(r['status']=='ok' for r in records),
                 models=usage,classification_calls=0,
                 known_reported_writer_cost_usd=sum(r['reported_cost_usd'] or 0 for r in records),
                 actual_total_cost='Unknown; Codex dollar equivalents are unavailable.')
    s.save(OUT/'summary.json',summary)
    (OUT/'outputs.md').write_text('\n'.join(preview),encoding='utf-8',newline='\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['collect','export'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS)
    args=parser.parse_args()
    if args.action=='collect':collect(args.max_new)
    else:export()
