"""Matched baseline/expanded audit through the same zero-price decision checkpoint."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import threading
import time

import requests
import smoke_study as s
import decision_audit as d
import tagged_kimi_pilot as p
import expanded_full_study as w

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/simple_prose_v3_full_classifier'
PRIVATE=ROOT/'data/local_inputs/simple_prose_v3_full_classifier'
MODEL='respan/span-01-lite-20260925'
PROTOCOL='full-free-span-v1'
MAX_NEW_CALLS=4
MAX_WORKERS=8
MIN_INTERVAL=.5
CHAR_QUESTION_BUDGET=900000
MAX_ATTEMPTS=3


def atomic_save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.{threading.get_ident()}.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    tmp.replace(path)


def body_zones(text):
    """Apply the existing region definitions without stripping text inside post tags."""
    paragraphs=[v.strip() for v in re.split(r'\n\s*\n',text) if v.strip()]
    substantive=[v for v in paragraphs if not all(word.startswith('#') for word in v.split())]
    starts=[];endings=[]
    for paragraph in substantive:starts.extend(s.sentences(paragraph)[1:])
    starts.extend(substantive[1:])
    for paragraph in substantive[:-1]:endings.append(s.sentences(paragraph)[-1])
    return dict(whole=text,opening_paragraph=paragraphs[0] if paragraphs else '',
                transition_starts='\n'.join(' '.join(value.split()[:12]) for value in starts),
                point_endings='\n'.join(endings),conclusion=substantive[-1] if substantive else '',
                closing=s.sentences(substantive[-1])[-1] if substantive else '')


def register():
    writer=w.register();old=s.load(ROOT/'data/decision_audit/protocol.json')
    plan=dict(protocol=PROTOCOL,model=MODEL,provider='respan',conditions=['baseline','expanded'],
              articles=writer['articles'],models=s.MODELS,turns=5,planned_case_pairs=400,
              definitions=old['definitions'],zones=d.DECISION_ZONES,threshold=.5,sensitivity_thresholds=[.2,.8],
              planned_predicates_per_case=240,planned_cases=800,
              whole_post_labels='Primary; 40 independent pattern probabilities per readable post.',
              regions='Existing six regions retained; regional layout labels are diagnostics because sentence windows alter layout.',
              formats='Baseline uses its frozen literal wrapper/note parser. Expanded primary uses exactly the valid enclosed body.',
              sensitivity='For an invalid-tag but nonempty expanded reply, classify the exact full raw reply separately. Never infer a post body; exclude that row from primary strict-post rates.',
              sensitivity_amendment='Declared after observing early writer tag failures, before any full-run classifier labels. It does not change prompts, regenerate responses or manually assign styles.',
              transport=dict(max_workers=MAX_WORKERS,min_start_interval=MIN_INTERVAL,max_questions=40,
                             char_question_budget=CHAR_QUESTION_BUDGET,max_attempts=MAX_ATTEMPTS),
              batches='Pack the unchanged 240 questions in order with max(4,min(40,floor(900000/state_characters))) questions per request. Split a 504/413 batch in half if more than 4 questions, preserving parent attempts. No valid answer is retried.',
              retries='Only 429/500/502/503/504/transport failures, at most 3 attempts per leaf. Honor Retry-After with chunked waits. All attempts retained; failures are unreadable, not absent.',
              fairness='Stream matched article/model/turn pairs; randomize the two conditions within a pair and the order of pairs with seed 20261102. Source and post only are sent to the classifier.',
              price_guard='Respan only, dated zero-price standard route, maximum prompt/output price zero, no model/provider fallback. Stop on any nonzero reported cost.',
              cache='Full private request and response per attempt; exact-payload hash plus attempt number. Public rows redact source-bearing state. Successful exact requests are replayed without another call.',
              comparability='All primary full-run labels use this standard route and exact region extraction; pilot :free-route labels and earlier paid labels are retained separately.',
              limits='No human gold labels or quality score. Same fixed rubric and uncalibrated .5/.8 thresholds. Article-cluster comparisons; no assumption of independent drafts.')
    path=OUT/'protocol.json'
    if path.exists():
        old=s.load(path);assert all(old[k]==v for k,v in plan.items()),'Full classification plan changed after registration'
    else:atomic_save(path,dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),**plan))
    return plan


def record_for(condition,item,model,turn):
    folder=ROOT/'data/main' if condition=='baseline' else w.OUT
    path=folder/'responses'/item/model/f'{turn:02d}.json'
    if not path.exists():return None
    try:r=s.load(path)
    except json.JSONDecodeError:return None
    if r['status']!='ok' or not r['text']:return dict(record=r,text=None,input_kind='unreadable_generation',strict_readable=False)
    if condition=='baseline':return dict(record=r,text=s.split_response(r['text'])['body'],input_kind='legacy_post',strict_readable=True)
    if r['post_body'] is not None:return dict(record=r,text=r['post_body'],input_kind='tagged_post',strict_readable=True)
    return dict(record=r,text=r['text'],input_kind='raw_unparsed_response',strict_readable=False)


def payloads(text,source,protocol):
    zones=body_zones(text);questions={};template=None
    for batch in range(2):
        value=d.decision_payload(dict(text=text),batch,protocol,source,zones=zones)
        questions.update(value['questions']);template=value
    template['model']=MODEL
    template['provider']={'only':['respan'],'order':['respan'],'allow_fallbacks':False,'max_price':{'prompt':0,'completion':0}}
    size=max(4,min(40,CHAR_QUESTION_BUDGET//max(1,len(template['state']))))
    entries=list(questions.items())
    return [dict(template,questions=dict(entries[i:i+size])) for i in range(0,len(entries),size)]


def collect(max_new=MAX_NEW_CALLS,wait_for_writers=False):
    assert 0<=max_new<=30000
    protocol=register();token=os.environ.get('OPENROUTER_API_KEY');assert token
    article_by_id={a['item_id']:a for a in protocol['articles']}
    sources={a['item_id']:(ROOT/a['local_input']).read_text(encoding='utf-8') for a in protocol['articles']}
    assert all(s.sha(sources[item])==a['text_sha256'] for item,a in article_by_id.items())
    p.PROTOCOL=PROTOCOL;trace=p.make_tracer()
    state={'new':0,'next_start':0.,'complete_pairs':0};gate=threading.Lock();stop=threading.Event()
    per_key={};key_guard=threading.Lock()
    def delay(seconds):
        deadline=time.monotonic()+max(0,seconds)
        while not stop.is_set() and time.monotonic()<deadline:time.sleep(min(20,deadline-time.monotonic()))
    def request(payload):
        key=s.sha(s.canonical(payload))
        with key_guard:lock=per_key.setdefault(key,threading.Lock())
        with lock:
            for attempt in range(1,MAX_ATTEMPTS+1):
                cache_key=key+f'#a{attempt}';stem=key+f'_a{attempt}'
                path=OUT/'attempts'/f'{stem}.json';private=PRIVATE/'cache'/f'{stem}.json'
                if path.exists():
                    row=s.load(path);full=s.load(private)
                    assert full['request']==payload and row['request_sha256']==key
                    row['parsed']=d.parse_decision(row['response'],payload['questions']) if row['status']==200 else {}
                else:
                    with gate:
                        if stop.is_set() or state['new']>=max_new:return {},['request_budget_or_stop']
                        delay(max(0,state['next_start']-time.monotonic()))
                        if stop.is_set():return {},['stopped']
                        state['new']+=1;state['next_start']=time.monotonic()+MIN_INTERVAL
                    marker=OUT/'started'/f'{stem}.json'
                    if marker.exists():return {},['unresolved_started_attempt']
                    start=datetime.now(timezone.utc);tick=time.monotonic()
                    atomic_save(marker,dict(cache_key=cache_key,request_sha256=key,started_at=start.isoformat()))
                    atomic_save(PRIVATE/'started'/f'{stem}.json',dict(cache_key=cache_key,request_sha256=key,request=payload))
                    headers={}
                    try:
                        result=requests.post(d.DECISION_URL,json=payload,headers={'Authorization':'Bearer '+token},timeout=90)
                        status=result.status_code
                        headers={k:v for k,v in result.headers.items() if k.lower() in ['retry-after','x-ratelimit-reset','x-ratelimit-limit','x-ratelimit-remaining']}
                        try:raw=result.json()
                        except ValueError:raw={'unparsed_body':result.text}
                    except requests.RequestException as exc:status=0;raw={'transport_error':type(exc).__name__}
                    end=datetime.now(timezone.utc)
                    parsed=d.parse_decision(raw,payload['questions']) if status==200 else {}
                    row=dict(cache_key=cache_key,request_sha256=key,attempt_number=attempt,status=status,
                             started_at=start.isoformat(),completed_at=end.isoformat(),latency_s=time.monotonic()-tick,
                             question_names=list(payload['questions']),response=raw,retry_headers=headers,
                             private_cache=private.relative_to(ROOT).as_posix())
                    atomic_save(private,dict(cache_key=cache_key,request_sha256=key,attempt_number=attempt,
                                            request=payload,response=raw,started_at=start.isoformat(),completed_at=end.isoformat(),
                                            reported_cost_usd=raw.get('usage',{}).get('cost')))
                    row['request']={'model':payload['model'],'provider':payload['provider'],
                                    'state_sha256':s.sha(payload['state']),
                                    'questions_sha256':s.sha(s.canonical(payload['questions'])),
                                    'note':'Full request and response are retained together in the linked private cache.'}
                    row['request_redacted']=True
                    atomic_save(path,row)
                    row['parsed']=parsed
                    usage=raw.get('usage',{});details=usage.get('input_tokens_details',{})
                    trace_status=trace(cache_key,payload,dict(text=json.dumps(raw),session_id='full-free-'+s.sha(payload['state'])[:20],
                        status='ok' if status==200 else 'failed',input_total=usage.get('input_tokens'),
                        cache_read_tokens=details.get('cached_tokens'),output_tokens=usage.get('output_tokens'),
                        reported_cost_usd=usage.get('cost')),start,end)
                    atomic_save(OUT/'tracing'/f'{stem}.json',dict(cache_key=cache_key,status=trace_status))
                    marker.unlink();(PRIVATE/'started'/f'{stem}.json').unlink()
                    if state['new']%50==0:print('API ATTEMPTS',state['new'],'last',status,'questions',len(payload['questions']),flush=True)
                raw=row['response'];status=row['status'];parsed=row['parsed'];cost=raw.get('usage',{}).get('cost')
                if cost is not None and cost!=0:stop.set();return {},['nonzero_cost_protocol_failure']
                if status==200:
                    if raw.get('model')!='respan/span-01-lite-20260925' or raw.get('provider')!='Respan':
                        stop.set();return {},['model_or_provider_protocol_failure']
                    if all(v['valid'] for v in parsed.values()) and len(parsed)==len(payload['questions']):return parsed,[]
                    return parsed,['unreadable_typed_answers']
                if status in [413,504] and len(payload['questions'])>4:
                    entries=list(payload['questions'].items());middle=len(entries)//2
                    left,le=request(dict(payload,questions=dict(entries[:middle])))
                    right,re=request(dict(payload,questions=dict(entries[middle:])))
                    return {**left,**right},le+re
                if status not in [0,429,500,502,503,504]:return {},[f'HTTP_{status}']
                if attempt<MAX_ATTEMPTS:
                    value=next((v for k,v in row['retry_headers'].items() if k.lower()=='retry-after'),None)
                    try:seconds=float(value) if value is not None else 5*attempt
                    except ValueError:seconds=5*attempt
                    with gate:state['next_start']=max(state['next_start'],time.monotonic()+seconds)
                    delay(seconds)
            return {},['transient_attempts_exhausted']
    def case(condition,item,model,turn):
        path=OUT/'cases'/condition/item/model/f'{turn:02d}.json'
        value=record_for(condition,item,model,turn)
        if value is None:return False
        if path.exists():
            saved=s.load(path)
            assert saved['writer_request_sha256']==value['record']['request_sha256']
            return True
        pid=f'{condition}/{item}/{model}/{turn:02d}'
        if value['text'] is None:
            atomic_save(path,dict(case_id=pid,condition=condition,item_id=item,writer_model=model,turn=turn,
                                 status='unreadable_generation',strict_readable=False,input_kind=value['input_kind'],
                                 writer_request_sha256=value['record']['request_sha256'],answers={},errors=['unreadable_generation']))
            return True
        answers={};errors=[];batch_keys=[]
        for payload in payloads(value['text'],sources[item],protocol):
            parsed,failures=request(payload);answers.update(parsed);errors.extend(failures)
            batch_keys.append(s.sha(s.canonical(payload)))
            if stop.is_set():break
        if 'request_budget_or_stop' in errors or stop.is_set():return False
        atomic_save(path,dict(case_id=pid,condition=condition,item_id=item,writer_model=model,turn=turn,
                             status='complete' if len(answers)==240 and all(v['valid'] for v in answers.values()) else 'classifier_unreadable',
                             strict_readable=value['strict_readable'],input_kind=value['input_kind'],
                             writer_request_sha256=value['record']['request_sha256'],input_sha256=s.sha(value['text']),
                             source_sha256=article_by_id[item]['text_sha256'],answers=answers,errors=errors,batch_request_hashes=batch_keys))
        return True
    def pair(cell):
        item,model,turn=cell
        arms=['baseline','expanded'];random.Random(s.sha('/'.join([item,model,str(turn)]))).shuffle(arms)
        return all(case(arm,item,model,turn) for arm in arms)
    cells=[(a['item_id'],model,turn) for a in protocol['articles'] for model in s.MODELS for turn in range(1,6)]
    random.Random(20261102).shuffle(cells)
    pending=set(cells);active={};completed=set();last_progress=0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        while pending or active:
            writers_done=(w.OUT/'collection_events.json').exists()
            for cell in cells:
                if len(active)>=MAX_WORKERS or stop.is_set():break
                if cell not in pending:continue
                item,model,turn=cell
                if record_for('expanded',item,model,turn) is None:
                    if writers_done:pending.remove(cell);completed.add(cell)
                    continue
                active[pool.submit(pair,cell)]=cell;pending.remove(cell)
            if active:
                done,_=wait(active,timeout=5,return_when=FIRST_COMPLETED)
                for future in done:
                    cell=active.pop(future)
                    try:
                        if future.result():completed.add(cell)
                        else:pending.add(cell)
                    except Exception as exc:
                        stop.set();atomic_save(OUT/'fatal_event.json',dict(cell=cell,error=str(exc)))
            elif not wait_for_writers or writers_done:break
            else:time.sleep(5)
            if time.monotonic()-last_progress>10:
                atomic_save(OUT/'progress.json',dict(completed_pairs=len(completed),planned_pairs=400,
                    active_pairs=len(active),pending_pairs=len(pending),fresh_api_attempts=state['new'],writers_finished=writers_done,
                    updated_at_utc=datetime.now(timezone.utc).isoformat()))
                last_progress=time.monotonic()
            if stop.is_set() or state['new']>=max_new:break
    atomic_save(OUT/'collection_state.json',dict(completed_pairs=len(completed),remaining_pairs=len(pending),
        new_api_attempts=state['new'],stopped=stop.is_set(),writers_finished=(w.OUT/'collection_events.json').exists()))
    print('CLASSIFIER RETURNED',state,'completed pairs',len(completed),'remaining',len(pending),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','collect'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS);parser.add_argument('--wait-for-writers',action='store_true')
    args=parser.parse_args()
    if args.action=='register':register()
    else:collect(args.max_new,args.wait_for_writers)
