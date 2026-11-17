"""Paid, pinned multi-label classifiers over the same frozen writing comparison."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import shutil
import threading
import time

import requests
import smoke_study as s
import decision_audit as d
import full_free_classification as free
import tagged_kimi_pilot as p

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/paid_decision_full'
PRIVATE=ROOT/'data/local_inputs/paid_decision_full'
PROTOCOL='paid-prose-three-classifiers-v1'
MODELS={
    'gpt':dict(model='openai/gpt-6-luna-decisions-20261006',provider='openai',native_provider='OpenAI'),
    'jev':dict(model='typesafe/jev-1.14-20261014',provider='typesafe',native_provider='TypeSafe'),
    'mercury':dict(model='inception/mercury-decide-20260930',provider='inception',native_provider='Inception')}
N_PAIRS=2
MAX_NEW_CALLS=12
MAX_USD=20.
MAX_WORKERS=12
MIN_INTERVAL=.1
MAX_ATTEMPTS=3
PROVIDER_MIN_INTERVAL={'gpt':0.,'jev':0.,'mercury':0.}


def save(path,value):free.atomic_save(path,value)


def freeze_catalogue():
    path=OUT/'catalogue.json'
    if path.exists():return s.load(path)
    response=requests.get('https://openrouter.ai/api/v1/models',params={'output_modalities':'decisions'},timeout=30)
    response.raise_for_status();catalogue=response.json();models={m['canonical_slug']:m for m in catalogue['data']}
    endpoints={}
    for ident,profile in MODELS.items():
        r=requests.get('https://openrouter.ai/api/v1/models/'+profile['model']+'/endpoints',timeout=30);r.raise_for_status()
        raw=r.json();endpoint=next(x for x in raw['data']['endpoints'] if x['tag']==profile['provider'])
        assert float(endpoint['pricing']['prompt'])>0
        endpoints[ident]=dict(model=models[profile['model']],endpoint=endpoint)
    result=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),source=response.url,models=endpoints)
    save(path,result);return result


def record_for(condition,item,writer,turn):
    if condition=='expanded' and (item,writer,turn)==('14-seti','gpt-6.1-sol',2):
        r=s.load(ROOT/'data/simple_prose_v3_retry/response.json')
        if r['status']!='ok' or not r['text']:return dict(record=r,text=None,input_kind='unreadable_generation',strict_readable=False)
        return dict(record=r,text=r['post_body'] if r['post_body'] is not None else r['text'],
                    input_kind='tagged_post' if r['post_body'] is not None else 'raw_unparsed_response',strict_readable=r['post_body'] is not None)
    return free.record_for(condition,item,writer,turn)


def register():
    catalogue=freeze_catalogue();base=s.load(ROOT/'data/decision_audit/protocol.json')
    articles=s.load(ROOT/'data/main/articles.json');retry=s.load(ROOT/'data/simple_prose_v3_retry/response.json')
    assert retry['status']=='ok' and retry['text']
    manifest=[]
    for article in articles:
        for writer in s.MODELS:
            for turn in range(1,6):
                for condition in ['baseline','expanded']:
                    value=record_for(condition,article['item_id'],writer,turn)
                    assert value['text'] is not None
                    manifest.append(dict(condition=condition,item_id=article['item_id'],writer_model=writer,turn=turn,
                        request_sha256=value['record']['request_sha256'],input_sha256=s.sha(value['text']),
                        input_kind=value['input_kind'],strict_readable=value['strict_readable']))
    controls=s.load(ROOT/'data/free_decision_pilot/controls/protocol.json')
    plan=dict(protocol=PROTOCOL,models=MODELS,articles=articles,definitions=base['definitions'],zones=d.DECISION_ZONES,
        conditions=['baseline','expanded'],writer_models=s.MODELS,turns=5,posts_per_classifier=800,
        planned_cases=2400,planned_predicates=576000,threshold=.5,sensitivity_thresholds=[.2,.8],manifest=manifest,
        writer_recovery='One separately cached retry overlays only expanded/14-seti/gpt-6.1-sol/02. Original failure, original session and all 799 other effective responses remain unchanged.',
        recovery_sensitivity='Exclude the entire Sol SETI block; later original turns did not see the replacement draft.',
        input='Strict analysis uses valid enclosed bodies. Secondary raw analysis preserves every nonempty invalid-tag reply exactly, including any lone closing tag. Never infer a post body.',
        rubric='Unchanged 40 definitions, useful exceptions and per-post rules. Whole-text labels primary; regional formatting diagnostics. No manual labels or combined badness score.',
        batch='Two 120-question requests per case, identical state and disjoint three-region question groups. Transport failures may split batches without changing state or questions.',
        tools='No tools or web search offered. Effort controls are not exposed by this typed endpoint; writer retry remains high.',
        cache_reuse='Import an old OpenAI baseline response only when its full private request exactly equals the new full payload and its hash matches. 800 exact old requests are expected. Imported calls are not fresh spend and emit no live trace.',
        estimated_new_spend_usd=[5,10],maximum_new_spend_usd=MAX_USD,default_pairs=N_PAIRS,default_new_calls=MAX_NEW_CALLS,
        budget='Before each fresh call reserve a conservative quoted-price allowance; account for native costs and retain reservations for unpriced calls. Stop before another call would cross the $20 guard.',
        routing='Dated model and single provider in order, fallback disabled; preserve original OpenAI routing for exact cache matching. Check native returned dated model and provider on every success.',
        scheduling=dict(pair_workers=MAX_WORKERS,max_inflight_per_provider=4,min_start_interval=MIN_INTERVAL,seed=20261103),
        retries='Only transport/429/500/502/503/504, at most three attempts per leaf; honor Retry-After. Split 413/504 or context-length errors if more than four questions. Never retry valid or merely low-confidence labels.',
        smoke='For each paid model, expanded Kimi Sol first post and baseline longest-source Sonnet first post, both 120-question batches. Smoke cases are reused by the full run; no rubric/threshold tuning.',
        controls=controls,control_scope='Same three authored controls as the free pilot, whole-text region only. Fixed expected examples are diagnostics, not human-labelled accuracy or study posts.',
        inference='Paired article-cluster bootstrap with 2000 draws, per classifier. Report all three classifiers separately; no majority vote or manual reconciliation. Free comparison uses the common unretried 399 pairs.',
        caveats='Prompt/taxonomy were selected after inspecting baseline outputs; writer aliases are undated and writer conditions collected at different times. OpenAI baseline labels reuse earlier exact requests. No human writing-quality outcome.')
    path=OUT/'protocol.json'
    if path.exists():assert all(s.load(path)[k]==v for k,v in plan.items()),'Paid protocol changed after registration'
    else:save(path,dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),**plan))
    return plan


def payloads(text,source,protocol,ident):
    profile=MODELS[ident]
    result=[]
    for batch in range(2):
        value=d.decision_payload(dict(text=text),batch,protocol,source,zones=free.body_zones(text))
        value['model']=profile['model'];value['provider']={'order':[profile['provider']],'allow_fallbacks':False}
        result.append(value)
    return result


class Collector:
    def __init__(self,max_new):
        self.protocol=register();self.max_new=max_new
        self.token=os.environ.get('OPENROUTER_API_KEY');assert self.token
        self.sources={a['item_id']:(ROOT/a['local_input']).read_text(encoding='utf-8') for a in self.protocol['articles']}
        assert all(s.sha(self.sources[a['item_id']])==a['text_sha256'] for a in self.protocol['articles'])
        self.gate=threading.Lock();self.key_guard=threading.Lock();self.locks={};self.stop=threading.Event()
        self.semaphores={ident:threading.Semaphore(4) for ident in MODELS}
        self.new=0;self.next_start=0.;self.reserved=0.;self.provider_next={ident:0. for ident in MODELS}
        for ident,interval in PROVIDER_MIN_INTERVAL.items():
            if interval:self.semaphores[ident]=threading.Semaphore(1)
        attempts=[s.load(path) for path in (OUT/'attempts').glob('*/*.json')]
        fresh=[r for r in attempts if r['fresh_call']]
        self.spent=sum(r['response'].get('usage',{}).get('cost') or 0 for r in fresh)
        self.unknown=sum(r['reservation_usd'] for r in fresh if r['response'].get('usage',{}).get('cost') is None)
        self.catalogue=s.load(OUT/'catalogue.json')
        p.PROTOCOL=PROTOCOL;self.trace=p.make_tracer()

    def delay(self,seconds):
        end=time.monotonic()+max(0,seconds)
        while not self.stop.is_set() and time.monotonic()<end:time.sleep(min(10,end-time.monotonic()))

    def import_exact(self,payload,key,ident,path,private):
        if ident!='gpt':return None
        old_path=ROOT/'data/decision_audit/responses'/f'{key}.json'
        wire=ROOT/'data/local_inputs/decisions'/f'{key}.json'
        if not old_path.exists():return None
        assert wire.exists() and s.load(wire)==payload
        old=s.load(old_path);assert old['status']==200
        raw=old['raw'];parsed=d.parse_decision(raw,payload['questions'])
        assert all(v['valid'] for v in parsed.values())
        row=dict(cache_key=key,request_sha256=key,attempt_number=1,status=200,question_names=list(payload['questions']),
            response=raw,started_at=old['started_at_utc'],completed_at=old.get('ended_at_utc'),latency_s=old['latency_s'],
            fresh_call=False,origin='reused_exact_historical_request',historical_cache=old_path.relative_to(ROOT).as_posix(),
            reservation_usd=0,retry_headers={},private_cache=private.relative_to(ROOT).as_posix())
        save(private,dict(cache_key=key,request_sha256=key,attempt_number=1,request=payload,response=raw,
            fresh_call=False,origin=row['origin'],started_at=row['started_at'],reported_cost_usd=raw['usage'].get('cost')))
        self.public_save(path,row,payload)
        row['parsed']=parsed;return row

    def public_save(self,path,row,payload):
        row['request']=dict(model=payload['model'],provider=payload['provider'],state_sha256=s.sha(payload['state']),
            questions_sha256=s.sha(s.canonical(payload['questions'])),note='Full publisher-bearing request and native response retained together in linked private cache.')
        row['request_redacted']=True;save(path,row)

    def request(self,payload,ident,diagnostic=False):
        key=s.sha(s.canonical(payload));profile=MODELS[ident]
        with self.key_guard:lock=self.locks.setdefault(key,threading.Lock())
        with lock:
            for attempt in range(1,MAX_ATTEMPTS+1):
                fresh_attempt=False
                stem=key+f'_a{attempt}';path=OUT/'attempts'/ident/(stem+'.json');private=PRIVATE/'cache'/(stem+'.json')
                if path.exists():
                    row=s.load(path);assert s.load(private)['request']==payload
                    row['parsed']=d.parse_decision(row['response'],payload['questions']) if row['status']==200 else {}
                else:
                    row=self.import_exact(payload,key,ident,path,private) if attempt==1 else None
                    if row is None:
                        price=float(self.catalogue['models'][ident]['endpoint']['pricing']['prompt'])
                        reservation=max(.002,1.5*len(s.canonical(payload).encode('utf-8'))*price)
                        with self.semaphores[ident]:
                            with self.gate:
                                if self.stop.is_set() or self.new>=self.max_new:return {},['request_budget_or_stop']
                                if self.spent+self.unknown+self.reserved+reservation>MAX_USD:
                                    self.stop.set();return {},['dollar_budget_guard']
                                self.delay(max(0,self.next_start-time.monotonic(),self.provider_next[ident]-time.monotonic()))
                                self.new+=1;self.reserved+=reservation;self.next_start=time.monotonic()+MIN_INTERVAL
                                self.provider_next[ident]=time.monotonic()+PROVIDER_MIN_INTERVAL[ident]
                            marker=OUT/'started'/(stem+'.json')
                            if marker.exists():self.stop.set();return {},['unresolved_started_request']
                            start=datetime.now(timezone.utc);tick=time.monotonic()
                            save(marker,dict(request_sha256=key,attempt_number=attempt,started_at=start.isoformat()))
                            save(PRIVATE/'started'/(stem+'.json'),dict(request_sha256=key,attempt_number=attempt,request=payload,started_at=start.isoformat()))
                            headers={}
                            try:
                                fresh_attempt=True
                                r=requests.post(d.DECISION_URL,json=payload,headers={'Authorization':'Bearer '+self.token},timeout=90)
                                status=r.status_code;headers={k:v for k,v in r.headers.items() if k.lower()=='retry-after'}
                                try:raw=r.json()
                                except ValueError:raw={'unparsed_body':r.text}
                            except requests.RequestException as exc:status=0;raw={'transport_error':type(exc).__name__}
                            end=datetime.now(timezone.utc);cost=raw.get('usage',{}).get('cost')
                            cache_key=key+f'#a{attempt}'
                            row=dict(cache_key=cache_key,request_sha256=key,attempt_number=attempt,status=status,
                                question_names=list(payload['questions']),response=raw,started_at=start.isoformat(),completed_at=end.isoformat(),
                                latency_s=time.monotonic()-tick,fresh_call=True,origin='new_paid_request',diagnostic=diagnostic,
                                reservation_usd=reservation,retry_headers=headers,private_cache=private.relative_to(ROOT).as_posix())
                            save(private,dict(cache_key=cache_key,request_sha256=key,attempt_number=attempt,request=payload,response=raw,
                                fresh_call=True,started_at=start.isoformat(),completed_at=end.isoformat(),reported_cost_usd=cost))
                            self.public_save(path,row,payload)
                            with self.gate:
                                self.reserved-=reservation
                                if cost is not None:self.spent+=cost
                                else:self.unknown+=reservation
                            usage=raw.get('usage',{});details=usage.get('input_tokens_details',usage.get('prompt_tokens_details',{}))
                            traced=self.trace(cache_key,payload,dict(text=json.dumps(raw),session_id='paid-'+s.sha(payload['state'])[:20],
                                status='ok' if status==200 else 'failed',input_total=usage.get('input_tokens'),
                                cache_read_tokens=details.get('cached_tokens'),output_tokens=usage.get('output_tokens'),reported_cost_usd=cost),start,end)
                            save(OUT/'tracing'/(stem+'.json'),dict(cache_key=cache_key,status=traced))
                            marker.unlink();(PRIVATE/'started'/(stem+'.json')).unlink()
                            row['parsed']=d.parse_decision(raw,payload['questions']) if status==200 else {}
                            if self.new%100==0:print('FRESH API',self.new,'known new $',round(self.spent,6),flush=True)
                raw=row['response'];status=row['status']
                if status==200:
                    if raw.get('model')!=profile['model'] or raw.get('provider')!=profile['native_provider']:
                        self.stop.set();return {},['model_provider_violation']
                    parsed=row['parsed']
                    return parsed,[] if len(parsed)==len(payload['questions']) and all(v['valid'] for v in parsed.values()) else ['unreadable_typed_answers']
                context_error=status==400 and 'context' in json.dumps(raw).lower()
                if (status in [413,504] or context_error) and len(payload['questions'])>4:
                    entries=list(payload['questions'].items());mid=len(entries)//2
                    left,le=self.request(dict(payload,questions=dict(entries[:mid])),ident,diagnostic)
                    right,re=self.request(dict(payload,questions=dict(entries[mid:])),ident,diagnostic)
                    return {**left,**right},le+re
                if status not in [0,429,500,502,503,504]:return {},[f'HTTP_{status}']
                if attempt<MAX_ATTEMPTS and fresh_attempt:
                    value=next(iter(row['retry_headers'].values()),None)
                    try:seconds=float(value) if value is not None else attempt*3
                    except ValueError:seconds=attempt*3
                    if status==429 and PROVIDER_MIN_INTERVAL[ident]:
                        seconds=max(seconds,45)
                        with self.gate:self.provider_next[ident]=max(self.provider_next[ident],time.monotonic()+seconds)
                    self.delay(seconds)
            return {},['transport_attempts_exhausted']

    def case(self,ident,condition,item,writer,turn):
        path=OUT/'cases'/ident/condition/item/writer/f'{turn:02d}.json';value=record_for(condition,item,writer,turn)
        if path.exists():
            assert s.load(path)['writer_request_sha256']==value['record']['request_sha256'];return True
        answers={};errors=[];keys=[]
        for payload in payloads(value['text'],self.sources[item],self.protocol,ident):
            parsed,failed=self.request(payload,ident);answers.update(parsed);errors.extend(failed);keys.append(s.sha(s.canonical(payload)))
            if self.stop.is_set():break
        if self.stop.is_set() or 'request_budget_or_stop' in errors:return False
        save(path,dict(classifier=ident,case_id='/'.join([ident,condition,item,writer,f'{turn:02d}']),
            condition=condition,item_id=item,writer_model=writer,turn=turn,
            status='complete' if len(answers)==240 and all(v['valid'] for v in answers.values()) else 'classifier_unreadable',
            strict_readable=value['strict_readable'],input_kind=value['input_kind'],writer_request_sha256=value['record']['request_sha256'],
            input_sha256=s.sha(value['text']),source_sha256=value['record'].get('source_sha256',value['record']['request'].get('source_sha256')),
            answers=answers,errors=errors,batch_request_hashes=keys))
        return True


def collect(n_pairs=N_PAIRS,max_new=MAX_NEW_CALLS,smoke=False):
    collector=Collector(max_new);articles=collector.protocol['articles']
    if smoke:
        jobs=[(ident,condition,item,writer,turn) for ident in MODELS for condition,item,writer,turn in [
            ('expanded','01-kimi','gpt-6.1-sol',1),('baseline','09-misalignment-monitoring','claude-sonnet-5-5',1)]]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda job:collector.case(*job),jobs))
        assert all(results) and all(s.load(OUT/'cases'/ident/cond/item/writer/f'{turn:02d}.json')['status']=='complete' for ident,cond,item,writer,turn in jobs)
        save(OUT/'smoke.json',dict(cases=len(jobs),all_readable=True,new_api_attempts=collector.new,known_new_spend_usd=collector.spent))
        print('Smoke passed',len(jobs),'cases; known cumulative new $',collector.spent,flush=True);return
    cells=[(a['item_id'],writer,turn) for a in articles for writer in s.MODELS for turn in range(1,6)]
    random.Random(20261103).shuffle(cells);cells=cells[:n_pairs]
    jobs=[(ident,*cell) for cell in cells for ident in MODELS];random.Random(20261103).shuffle(jobs)
    def run(job):
        ident,item,writer,turn=job;arms=['baseline','expanded'];random.Random(s.sha('/'.join([ident,item,writer,str(turn)]))).shuffle(arms)
        return all(collector.case(ident,arm,item,writer,turn) for arm in arms)
    completed=0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures=[pool.submit(run,job) for job in jobs]
        for future in as_completed(futures):
            try:completed+=bool(future.result())
            except Exception as exc:
                collector.stop.set();save(OUT/'fatal_event.json',dict(type=type(exc).__name__,message=str(exc)));raise
            if completed%25==0:
                save(OUT/'progress.json',dict(completed_pairs=completed,planned_pairs=len(jobs),new_api_attempts=collector.new,
                    known_cumulative_new_spend_usd=collector.spent,updated_at_utc=datetime.now(timezone.utc).isoformat()))
    save(OUT/'collection_state.json',dict(completed_pairs=completed,planned_pairs=len(jobs),new_api_attempts=collector.new,
        known_cumulative_new_spend_usd=collector.spent,unknown_cost_reservations_usd=collector.unknown,stopped=collector.stop.is_set()))
    print('Paid collection returned',completed,'of',len(jobs),'pairs; fresh calls',collector.new,'known cumulative new $',collector.spent,flush=True)


def controls(max_new=MAX_NEW_CALLS):
    collector=Collector(max_new);plan=collector.protocol['controls'];results=[]
    for ident in MODELS:
        for fixture in plan['fixtures']:
            path=OUT/'controls'/ident/(fixture['id']+'.json')
            if path.exists():results.append(s.load(path));continue
            payload=payloads(fixture['post'],plan['source'],collector.protocol,ident)[0]
            payload['questions']={k:v for k,v in payload['questions'].items() if k.startswith('whole__')}
            answers,errors=collector.request(payload,ident,diagnostic=True)
            row=dict(classifier=ident,control_id=fixture['id'],answers=answers,errors=errors,
                     request_sha256=s.sha(s.canonical(payload)),expected_present=fixture.get('expected_present',[]),
                     expected_absent=fixture.get('expected_absent',[]))
            save(path,row);results.append(row)
    assert len(results)==9 and all(len(r['answers'])==40 and all(v['valid'] for v in r['answers'].values()) for r in results)
    print('Authored controls collected; no labels altered. Known cumulative new $',collector.spent,flush=True)


def repair_transport(max_new=MAX_NEW_CALLS):
    global MAX_ATTEMPTS
    assert (OUT/'collection_state.json').exists(),'Finish the initial pass before transport recovery'
    broken=[]
    for path in sorted((OUT/'cases').glob('*/*/*/*/*.json')):
        row=s.load(path)
        if row['status']=='complete':continue
        # Only transport-exhausted cases qualify; never regenerate a typed answer.
        assert row['errors'] and set(row['errors'])=={'transport_attempts_exhausted'},(path,row['errors'])
        broken.append((path,row))
    for ident in MODELS:
        for entry in s.load(OUT/'protocol.json')['manifest']:
            path=OUT/'cases'/ident/entry['condition']/entry['item_id']/entry['writer_model']/f"{entry['turn']:02d}.json"
            if not path.exists():
                broken.append((path,dict(classifier=ident,condition=entry['condition'],item_id=entry['item_id'],
                    writer_model=entry['writer_model'],turn=entry['turn'],
                    case_id='/'.join([ident,entry['condition'],entry['item_id'],entry['writer_model'],f"{entry['turn']:02d}"]),
                    status='unattempted_after_initial_request_cap',errors=['initial_request_cap'])))
    if not broken:print('No transport-exhausted cases remain.');return
    amendment=dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),reason='Observed Mercury 429 and intermittent 502 responses exhausted the first-pass request allowance; finish missing cases and recover exhausted transport leaves. Semantic answers and rubric remain unchanged.',
        case_ids=[row['case_id'] for _,row in broken],extra_attempts_per_failed_leaf=3,total_attempt_cap=6,
        mercury_min_fresh_start_interval_seconds=6,mercury_inflight_requests=1,initial_cooldown_seconds=60,
        retry_backoff_seconds_on_new_429=45,
        preservation='Retain every failed attempt and copy the earlier partial case index before rebuilding from exact cached successful responses plus only missing transport retries.',
        semantic_rules='Never retry a valid response, invalid typed/schema response, or low-confidence label. No manual labels; no taxonomy or threshold change.')
    path=OUT/'transport_repair.json'
    if path.exists():
        previous=s.load(path);assert set(amendment['case_ids'])<=set(previous['case_ids'])
    else:save(path,amendment)
    state=OUT/'first_pass.json'
    if not state.exists():save(state,dict(collection_state=s.load(OUT/'collection_state.json'),broken_cases=len(broken)))
    MAX_ATTEMPTS=6;PROVIDER_MIN_INTERVAL['mercury']=6.
    collector=Collector(max_new)
    collector.delay(60)
    recovered=0
    for path,row in broken:
        history=OUT/'case_history'/path.relative_to(OUT/'cases')
        assert path.resolve().is_relative_to(OUT.resolve()) and history.resolve().is_relative_to(OUT.resolve())
        history.parent.mkdir(parents=True,exist_ok=True)
        existed=path.exists()
        if existed:
            if not history.exists():shutil.copyfile(path,history)
            path.unlink()
        ok=collector.case(row['classifier'],row['condition'],row['item_id'],row['writer_model'],row['turn'])
        if not ok:
            if not path.exists() and history.exists():shutil.copyfile(history,path)
            break
        recovered+=s.load(path)['status']=='complete'
        save(OUT/'repair_progress.json',dict(visited=broken.index((path,row))+1,planned=len(broken),recovered=recovered,
            new_api_attempts=collector.new,known_cumulative_new_spend_usd=collector.spent,updated_at_utc=datetime.now(timezone.utc).isoformat()))
        print('Transport recovery',recovered,'of',len(broken),'new API attempts',collector.new,flush=True)
    save(OUT/'transport_repair_result.json',dict(planned_cases=len(broken),recovered=recovered,new_api_attempts=collector.new,
        known_cumulative_new_spend_usd=collector.spent,stopped=collector.stop.is_set()))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','smoke','controls','collect','repair'])
    parser.add_argument('--pairs',type=int,default=N_PAIRS);parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS)
    args=parser.parse_args()
    if args.action=='register':register()
    elif args.action=='controls':controls(args.max_new)
    elif args.action=='repair':repair_transport(args.max_new)
    else:collect(args.pairs,args.max_new,args.action=='smoke')
