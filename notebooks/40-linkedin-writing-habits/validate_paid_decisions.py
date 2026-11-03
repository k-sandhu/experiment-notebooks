"""Verify retry provenance, exact paid requests and a portable offline replay."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import smoke_study as s
import full_study as f
import tagged_kimi_pilot as p
import decision_audit as d
import paid_decision_study as paid
import paid_prose_analysis as analysis


MODULE_ALIASES={'smoke_study':['s'],'full_study':['f'],'tagged_kimi_pilot':['p'],
    'expanded_full_study':['w'],'decision_audit':['d'],'full_free_classification':['c','free'],
    'expanded_full_analysis':['lexical'],'paid_decision_study':['paid']}
MODULE_NAMES=['smoke_study','full_study','tagged_kimi_pilot','expanded_full_study','decision_audit',
    'full_free_classification','expanded_full_analysis','retry_failed_generation','paid_decision_study','paid_prose_analysis']


def embedded_setup(root):
    sources={}
    for name in MODULE_NAMES:
        source=(root/(name+'.py')).read_text(encoding='utf-8')
        for dependency,aliases in MODULE_ALIASES.items():
            for alias in aliases:source=source.replace('import '+dependency+' as '+alias+'\n','')
        sources[name]=source
    return '''from pathlib import Path
import types
ROOT=Path.cwd()
MODULES={}
'''+f'EMBEDDED_SOURCES={sources!r}\nALIASES={MODULE_ALIASES!r}\n'+'''for name,source in EMBEDDED_SOURCES.items():
    module=types.ModuleType('embedded_'+name)
    module.__file__=str(ROOT/(name+'.py'))
    for dependency,aliases in ALIASES.items():
        if dependency in MODULES:
            for alias in aliases:module.__dict__[alias]=MODULES[dependency]
    exec(compile(source,module.__file__,'exec'),module.__dict__)
    MODULES[name]=module
'''


def validate():
    root=paid.ROOT;out=analysis.OUT
    retry=s.load(root/'data/simple_prose_v3_retry/response.json')
    original=s.load(root/'data/simple_prose_v3_full/responses/14-seti/gpt-6.1-sol/02.json')
    first=s.load(root/'data/simple_prose_v3_full/responses/14-seti/gpt-6.1-sol/01.json')
    old_request=s.load(root/original['private_cache'])['request']
    full=s.load(root/retry['private_cache']);request=full['request'];fork=s.load(root/'data/simple_prose_v3_retry/fork.json')
    assert s.sha(s.canonical(request))==retry['request_sha256']==full['request_sha256']
    assert request['messages']==old_request['messages'] and request['stdin']==old_request['stdin']
    assert request['command']==s.command('gpt-6.1-sol',True,fork['fork_session_id'])
    assert request['tools']=='disabled' and request['web_search']=='disabled' and request['effort']=='high'
    assert retry['status']=='ok' and retry['text'] and not retry['tool_events']
    assert not original['text'] and original['status']!='ok'
    assert retry['retry_of']==original['request_sha256']
    native=(root/'data/simple_prose_v3_retry/response.jsonl').read_text(encoding='utf-8')
    parsed=f.corrected(s.parse_result('gpt-6.1-sol',native),'gpt-6.1-sol',first['raw_usage'],first.get('reported_session_cost_usd'))
    for name in ['text','raw_usage','input_total','cache_read_tokens','output_tokens','session_id']:
        assert retry[name]==parsed[name],name
    for name,value in p.parse_post(retry['text']).items():assert retry[name]==value
    snapshot=s.json_events((root/'data/local_inputs/simple_prose_v3_retry/restored_prefix.jsonl').read_text(encoding='utf-8'))
    meta=snapshot[0]['payload'];base=meta['history_base'];assert base['thread_id']==first['session_id']
    preserved=root/'data/local_inputs/simple_prose_v3_retry/original_first_turn.jsonl'
    if preserved.exists():source=preserved.read_bytes()
    else:
        source_path=next((Path.home()/'.codex/sessions').rglob('*'+first['session_id']+'*.jsonl'))
        source=source_path.read_bytes()[:base['end_byte_offset']]
    prefix=s.json_events(source.decode('utf-8'))
    assert prefix[-1]['ordinal']+1==base['end_ordinal_exclusive']
    assert prefix[-1]['payload']['type']=='task_complete' and prefix[-1]['payload']['turn_id']==fork['last_included_native_turn_id']
    items=[row['payload'] for row in prefix if row['type']=='response_item']
    assert s.sha(s.canonical(items))==request['native_prefix_sha256']==fork['original_native_prefix_sha256']
    assert sum(item.get('role')=='assistant' and item.get('phase')=='final_answer' for item in items)==1
    print('Retry provenance and original exact prefix passed.',flush=True)
    protocol=s.load(paid.OUT/'protocol.json');assert protocol['definitions']==s.load(root/'data/decision_audit/protocol.json')['definitions']
    articles=s.load(root/'data/main/articles.json');sources={a['item_id']:(root/a['local_input']).read_text(encoding='utf-8') for a in articles}
    attempts={};status=Counter();fresh=0;imports=0
    for path in sorted((paid.OUT/'attempts').glob('*/*.json')):
        row=s.load(path);full=s.load(root/row['private_cache']);payload=full['request'];key=s.sha(s.canonical(payload))
        assert key==row['request_sha256']==full['request_sha256']
        assert full['response']==row['response'] and row['question_names']==list(payload['questions'])
        assert row['request']['state_sha256']==s.sha(payload['state'])
        assert row['request']['questions_sha256']==s.sha(s.canonical(payload['questions']))
        ident=path.parent.name;profile=paid.MODELS[ident]
        assert payload['model']==profile['model'] and payload['provider']=={'order':[profile['provider']],'allow_fallbacks':False}
        if row['status']==200:
            assert row['response']['model']==profile['model'] and row['response']['provider']==profile['native_provider']
        slot=(key,row['attempt_number']);assert slot not in attempts;attempts[slot]=row;status[(ident,row['status'])]+=1
        if row['fresh_call']:fresh+=1
        else:
            imports+=1;assert ident=='gpt' and row['origin']=='reused_exact_historical_request'
            assert s.load(root/'data/local_inputs/decisions'/f'{key}.json')==payload
            assert s.load(root/row['historical_cache'])['raw']==row['response']
    assert imports==800
    def resolve(payload):
        key=s.sha(s.canonical(payload))
        for attempt in range(1,7):
            row=attempts.get((key,attempt))
            if row is None:return {}
            if row['status']==200:return d.parse_decision(row['response'],payload['questions'])
            context=row['status']==400 and 'context' in json.dumps(row['response']).lower()
            if (row['status'] in [413,504] or context) and len(payload['questions'])>4:
                q=list(payload['questions'].items());mid=len(q)//2
                return {**resolve(dict(payload,questions=dict(q[:mid]))),**resolve(dict(payload,questions=dict(q[mid:])))}
            if row['status'] not in [0,429,500,502,503,504]:return {}
        return {}
    cases=0;valid=0;unreadable=0
    for ident in paid.MODELS:
        for entry in protocol['manifest']:
            condition,item,writer,turn=[entry[k] for k in ['condition','item_id','writer_model','turn']]
            value=paid.record_for(condition,item,writer,turn)
            row=s.load(paid.OUT/'cases'/ident/condition/item/writer/f'{turn:02d}.json')
            assert row['input_sha256']==entry['input_sha256']==s.sha(value['text'])
            assert row['writer_request_sha256']==entry['request_sha256']==value['record']['request_sha256']
            assert row['strict_readable']==entry['strict_readable']==value['strict_readable']
            expected={};keys=[]
            for payload in paid.payloads(value['text'],sources[item],protocol,ident):
                keys.append(s.sha(s.canonical(payload)));expected.update(resolve(payload))
            assert row['batch_request_hashes']==keys and row['answers']==expected,row['case_id']
            cases+=1;valid+=sum(x['valid'] for x in expected.values());unreadable+=row['status']!='complete'
    assert cases==2400 and not list((paid.OUT/'started').glob('*.json'))
    controls=0
    for ident in paid.MODELS:
        for fixture in protocol['controls']['fixtures']:
            row=s.load(paid.OUT/'controls'/ident/(fixture['id']+'.json'))
            payload=paid.payloads(fixture['post'],protocol['controls']['source'],protocol,ident)[0]
            payload['questions']={k:v for k,v in payload['questions'].items() if k.startswith('whole__')}
            assert s.sha(s.canonical(payload))==row['request_sha256']
            assert resolve(payload)==row['answers']
            controls+=sum(r['valid'] for r in row['answers'].values())
    assert controls==360
    print('Paid native request/answer reconstruction passed:',cases,'cases;',valid,'valid probabilities.',flush=True)
    excluded={'validation.json','figure_validation.json'}
    expected={path.name:path.read_bytes() for path in out.iterdir() if path.suffix in ['.json','.csv'] and path.name not in excluded}
    with tempfile.TemporaryDirectory(prefix='linkedin40-paid-offline-') as temp:
        portable=Path(temp)
        for folder in ['data/main/responses','data/simple_prose_v3_full/responses','data/simple_prose_v3_full_classifier/cases',
                       'data/paid_decision_full/cases','data/paid_decision_full/attempts','data/paid_decision_full/controls']:
            shutil.copytree(root/folder,portable/folder)
        for file in ['data/main/articles.json','data/prose_lexicon.json','data/paid_decision_full/protocol.json',
                     'data/simple_prose_v3_retry/response.json','data/paid_prose_comparison/source_overlap.json']:
            target=portable/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/file,target)
        setup=embedded_setup(root)
        guard='''import socket, subprocess, requests
def denied(*args,**kwargs):raise AssertionError('Offline notebook attempted an external operation')
socket.create_connection=denied
subprocess.Popen=denied
requests.sessions.Session.request=denied
'''
        runner=portable/'replay.py';runner.write_text(guard+setup+"MODULES['paid_prose_analysis'].analyse()\n",encoding='utf-8')
        result=subprocess.run(['python','-X','utf8',str(runner)],cwd=portable,capture_output=True,text=True,encoding='utf-8')
        if result.returncode:raise RuntimeError(result.stderr[-4000:])
        for name,content in expected.items():assert (portable/'data/paid_prose_comparison'/name).read_bytes()==content,name
    summary=s.load(out/'summary.json')
    report=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),effective_writer_responses=800,authorized_writer_retries=1,
        original_failure_retained=True,native_first_turn_prefix_verified=True,later_drafts_absent_from_retry=True,
        retry_request_and_native_usage_verified=True,paid_classifier_cases=cases,valid_predicates=valid,unreadable_cases=unreadable,
        fresh_http_attempts=fresh,reused_exact_historical_requests=imports,valid_authored_control_probabilities=controls,
        provider_and_pinned_model_verified=True,all_labels_reconstructed_from_native_responses=True,
        native_usage_statuses={ident:{str(code):count for (model,code),count in status.items() if model==ident} for ident in paid.MODELS},
        known_new_classifier_cost_usd=summary['known_new_classifier_cost_usd'],cost_guard_satisfied=summary['known_new_classifier_cost_usd']<=paid.MAX_USD,
        portable_replay_without_sources_private_caches_or_repo_modules=True,network_and_cli_blocked=True,all_analysis_tables_byte_identical=True)
    s.save(out/'validation.json',report);print(json.dumps(report,indent=2));return report


if __name__=='__main__':validate()
