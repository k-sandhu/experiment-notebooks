"""Free-route multi-label classifications of valid tagged Kimi pilot posts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import threading

import requests
import decision_audit as d
import smoke_study as s
import tagged_kimi_pilot as p

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/free_decision_pilot'
PRIVATE=ROOT/'data/local_inputs/free_decision_pilot'
MODEL='respan/span-01-lite-20260925:free'
PROTOCOL='span-01-lite-free-kimi-v1'
N_POSTS=19
MAX_NEW_CALLS=4
MIN_START_INTERVAL=3.2


def pilot_records():
    return [s.load(path) for path in sorted((p.OUT/'responses').glob('*/*/*.json')) if '.started.' not in path.name]


def register():
    catalogue=s.load(OUT/'catalogue.json')
    endpoint=catalogue['endpoints'][MODEL]['raw']['data']['endpoints'][0]
    assert endpoint['tag']=='respan'
    assert float(endpoint['pricing']['prompt'])==float(endpoint['pricing']['completion'])==0
    old=s.load(ROOT/'data/decision_audit/protocol.json')
    records=pilot_records();valid=[r for r in records if r['post_body'] is not None]
    assert len(records)==20 and len(valid)==N_POSTS
    design=dict(protocol=PROTOCOL,model=MODEL,provider='respan',url=d.DECISION_URL,
                definitions=old['definitions'],zones=d.DECISION_ZONES,threshold=.5,sensitivity_thresholds=[.2,.8],
                rubric_sha256=s.sha(s.canonical(old['definitions'])),
                evidence='Source article and enclosed post only; writer, prompt, prior drafts and condition are withheld.',
                questions_per_request=40,requests_per_post=6,planned_requests=N_POSTS*6,
                post_manifest=[dict(post_id=f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}",
                                    post_sha256=s.sha(r['post_body'])) for r in valid],
                excluded=[dict(post_id=f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}",reason=r['format_status']) for r in records if r['post_body'] is None],
                price_guard='Pinned free model, Respan only, no fallback, provider max_price prompt=0 and completion=0; stop on nonzero native cost.',
                smoke='Sol and Sonnet first posts, whole-post region, reused in the final collection. No label-based rubric changes.',
                failures='One attempt per full request; preserve failed or missing answers as unreadable, never absent.',
                effort='Not exposed by the Decisions endpoint; no effort parameter is sent.',
                comparison='A different classifier from the earlier paid audit. No cross-classifier claim of prompt improvement.',
                authorization='Owner requested free OpenRouter decision models; add only zero-price Span-01 Lite to the repository allowlist.',
                version_limit='One checkpoint with standard and free aliases, not two independent classifiers. Context size is not published in the catalogue.')
    path=OUT/'protocol_40.json'
    if path.exists():
        previous=s.load(path)
        assert all(previous[k]==v for k,v in design.items()),'Classifier plan changed after registration'
    else:s.save(path,dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),**design))
    return design,records


def payload_for(record,batch,protocol,source):
    assert record['post_body'] is not None
    body=dict(record,text=record['post_body'])
    payload=d.decision_payload(body,batch//3,protocol,source)
    zone=protocol['zones'][batch]
    payload['questions']={k:v for k,v in payload['questions'].items() if k.startswith(zone+'__')}
    assert len(payload['questions'])==40
    payload['model']=MODEL
    payload['provider']={'only':['respan'],'order':['respan'],'allow_fallbacks':False,
                         'max_price':{'prompt':0,'completion':0}}
    return payload


def collect(smoke=False,max_new=MAX_NEW_CALLS):
    assert 0<=max_new<=114
    protocol,records=register()
    article=next(a for a in s.load(ROOT/'data/main/articles.json') if a['item_id']=='01-kimi')
    source=(ROOT/article['local_input']).read_text(encoding='utf-8')
    assert s.sha(source)==article['text_sha256']
    records=[r for r in records if r['post_body'] is not None]
    first=[next(r for r in records if r['requested_model']==m and r['turn']==1) for m in [s.MODELS[0],s.MODELS[3]]]
    records=first if smoke else first+[r for r in records if r not in first]
    token=os.environ.get('OPENROUTER_API_KEY');assert token,'OPENROUTER_API_KEY missing'
    p.PROTOCOL=PROTOCOL
    trace=p.make_tracer()
    state={'new':0,'last_start':0.}
    pace=threading.Lock();stop=threading.Event()
    schedule=dict(max_concurrent_requests=2,min_start_interval=MIN_START_INTERVAL,
                  protocol_sha256=s.sha(s.canonical(protocol)),
                  rationale='Transport scheduling after successful smoke; question text, state, definitions and thresholds unchanged.')
    schedule_path=OUT/'scheduling.json'
    if schedule_path.exists():assert s.load(schedule_path)==schedule
    else:s.save(schedule_path,schedule)
    def run(job):
        record,batch=job
        if stop.is_set():return None
        pid=f"{record['item_id']}/{record['requested_model']}/{record['turn']:02d}"
        payload=payload_for(record,batch,protocol,source)
        key=s.sha(s.canonical(payload));path=OUT/'responses_40'/f'{key}.json'
        private=PRIVATE/'cache'/f'{key}.json'
        if path.exists():
            prior=s.load(path)
            assert private.exists() and s.load(private)['request']==payload
            if prior['status']!=200 or not all(a['valid'] for a in prior['parsed'].values()):
                stop.set();return 'An earlier failed request needs review; do not silently retry'
            return None
        marker=OUT/'started'/f'{key}.json'
        if marker.exists():stop.set();return 'Unresolved request; do not retry'
        with pace:
            if stop.is_set() or state['new']>=max_new:return None
            wait=max(0,MIN_START_INTERVAL-(time.monotonic()-state['last_start']))
            if wait:time.sleep(wait)
            if stop.is_set():return None
            state['new']+=1
            started=datetime.now(timezone.utc);tick=time.monotonic();state['last_start']=tick
        s.save(marker,dict(request_sha256=key,post_id=pid,batch=batch,started_at=started.isoformat()))
        s.save(PRIVATE/'started'/f'{key}.json',dict(request_sha256=key,request=payload))
        print('START',pid,'batch',batch,flush=True)
        try:
            result=requests.post(d.DECISION_URL,json=payload,headers={'Authorization':'Bearer '+token},timeout=90)
            status=result.status_code
            try:raw=result.json()
            except ValueError:raw={'unparsed_body':result.text}
        except requests.RequestException as exc:
            status=0;raw={'transport_error':type(exc).__name__}
        ended=datetime.now(timezone.utc)
        parsed=d.parse_decision(raw,payload['questions']) if status==200 else {k:dict(valid=False,probability=None,error=f'HTTP {status}') for k in payload['questions']}
        row=dict(request_sha256=key,requested_model=MODEL,post_id=pid,writer_model=record['requested_model'],
                 turn=record['turn'],batch=batch,question_names=list(payload['questions']),
                 post_sha256=s.sha(record['post_body']),source_sha256=article['text_sha256'],
                 status=status,started_at=started.isoformat(),ended_at=ended.isoformat(),
                 latency_s=time.monotonic()-tick,raw=raw,parsed=parsed,
                 private_cache=private.relative_to(ROOT).as_posix())
        s.save(private,dict(request_sha256=key,request=payload,response=raw,
                           started_at=started.isoformat(),completed_at=ended.isoformat(),
                           reported_cost_usd=raw.get('usage',{}).get('cost')))
        row['request']={**payload,'state':'Publisher-containing state retained in the linked private full-request cache.'}
        row['request_redacted']=True
        s.save(path,row)
        usage=raw.get('usage',{});details=usage.get('input_tokens_details',usage.get('prompt_tokens_details',{}))
        tr=dict(text=json.dumps(raw,ensure_ascii=False),session_id='free-kimi-'+s.sha(pid)[:16],
                input_total=usage.get('input_tokens',usage.get('prompt_tokens')),
                cache_read_tokens=details.get('cached_tokens'),cache_write_tokens=details.get('cache_write_tokens'),
                output_tokens=usage.get('output_tokens',usage.get('completion_tokens')),
                reported_cost_usd=usage.get('cost'),raw_usage=usage,status='ok' if status==200 else 'failed')
        trace_status=trace(key,payload,tr,started,ended)
        s.save(OUT/'tracing'/f'{key}.json',dict(request_sha256=key,status=trace_status))
        marker.unlink();(PRIVATE/'started'/f'{key}.json').unlink()
        print('DONE',pid,batch,'HTTP',status,'valid',sum(v['valid'] for v in parsed.values()),'cost',usage.get('cost'),flush=True)
        if usage.get('cost') is not None and usage['cost']!=0:
            stop.set();return 'Nonzero cost: stop before another request'
        if status!=200 or not all(v['valid'] for v in parsed.values()):
            stop.set();return 'Classifier schema/transport failure; inspect the cached response'
        return None
    jobs=[(r,b) for r in records for b in ([0] if smoke else range(6))]
    with ThreadPoolExecutor(max_workers=2) as pool:
        failures=[error for error in pool.map(run,jobs) if error]
    analyse()
    print('New requests:',state['new'],flush=True)
    if failures:raise RuntimeError('; '.join(failures))


def analyse():
    protocol=s.load(OUT/'protocol_40.json')
    records=[s.load(path) for path in sorted((OUT/'responses_40').glob('*.json'))]
    rows=[]
    for record in records:
        for name,value in record['parsed'].items():
            zone,style=name.split('__',1);prob=value['probability']
            rows.append(dict(post_id=record['post_id'],writer_model=record['writer_model'],turn=record['turn'],
                             zone=zone,style_id=style,probability=prob,valid=value['valid'],error=value['error'],
                             label_at_0_5=prob>=.5 if prob is not None else None,
                             label_at_0_8=prob>=.8 if prob is not None else None,request_sha256=record['request_sha256']))
    assert len({(r['post_id'],r['zone'],r['style_id']) for r in rows})==len(rows)
    counts=[]
    for model in s.MODELS:
        expected=sum(x['post_id'].split('/')[1]==model for x in protocol['post_manifest'])
        for zone in protocol['zones']:
            for style,definition in protocol['definitions'].items():
                part=[r for r in rows if r['writer_model']==model and r['zone']==zone and r['style_id']==style]
                good=[r for r in part if r['valid']]
                counts.append(dict(writer_model=model,zone=zone,style_id=style,name=definition['name'],
                                   planned_readable_posts=expected,readable_answers=len(good),
                                   unreadable_or_missing_answers=expected-len(good),
                                   labelled_at_0_5=sum(r['label_at_0_5'] for r in good),
                                   labelled_at_0_8=sum(r['label_at_0_8'] for r in good)))
    s.write_csv(OUT/'classifications.csv',rows)
    s.write_csv(OUT/'counts.csv',counts)
    by_slot={(r['post_id'],r['zone'],r['style_id']):r for r in rows}
    conflicts=[]
    for r in rows:
        whole=by_slot.get((r['post_id'],'whole',r['style_id']))
        if r['zone']!='whole' and r['valid'] and r['label_at_0_5'] and whole and whole['valid'] and not whole['label_at_0_5']:
            conflicts.append(dict(post_id=r['post_id'],style_id=r['style_id'],zone=r['zone'],
                                  whole_probability=whole['probability'],region_probability=r['probability']))
    if conflicts:s.write_csv(OUT/'region_consistency.csv',conflicts)
    else:(OUT/'region_consistency.csv').write_text('post_id,style_id,zone,whole_probability,region_probability\n',encoding='utf-8')
    costs=[r['raw'].get('usage',{}).get('cost') for r in records]
    usage=[r['raw'].get('usage',{}) for r in records]
    cache_details=[u.get('input_tokens_details',u.get('prompt_tokens_details',{})) for u in usage]
    diagnostics=[s.load(path) for folder in ['responses','diagnostics','controls/responses'] for path in (OUT/folder).glob('*.json')]
    diagnostic_costs=[r.get('response',r.get('raw',{})).get('usage',{}).get('cost') for r in diagnostics]
    whole=[r for r in rows if r['zone']=='whole' and r['valid']]
    summary=dict(model=MODEL,unique_classifier_checkpoints=1,requests=len(records),planned_requests=114,
                 planned_posts=19,excluded_generation_format_failures=protocol['excluded'],
                 answers=len(rows),valid_answers=sum(r['valid'] for r in rows),planned_answers=4560,
                 complete=len(records)==114 and len(rows)==4560 and all(r['valid'] for r in rows),
                 reported_cost_usd=sum(c for c in costs if c is not None),unpriced_requests=sum(c is None for c in costs),
                 whole_region_conflicts=len(conflicts),human_validation=False,
                 whole_post_answers=len(whole),whole_post_flags_at_0_5=sum(r['label_at_0_5'] for r in whole),
                 whole_post_flags_at_0_8=sum(r['label_at_0_8'] for r in whole),
                 native_input_tokens=sum(u.get('input_tokens',u.get('prompt_tokens',0)) for u in usage),
                 cache_read_counter_available_requests=sum('cached_tokens' in v for v in cache_details),
                 cache_write_counter_available_requests=sum('cache_write_tokens' in v for v in cache_details),
                 diagnostic_attempts=len(diagnostics),unpriced_diagnostic_attempts=sum(c is None for c in diagnostic_costs),
                 diagnostic_reported_cost_usd=sum(c for c in diagnostic_costs if c is not None),
                 total_api_attempts=len(records)+len(diagnostics))
    s.save(OUT/'summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['register','smoke','collect','analyse'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS)
    args=parser.parse_args()
    if args.action=='register':register()
    elif args.action=='analyse':analyse()
    else:collect(args.action=='smoke',args.max_new)
