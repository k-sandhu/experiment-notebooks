"""Validate full writer/native provenance, typed answers and offline replay."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import tempfile
import shutil
import smoke_study as s
import full_study as f
import tagged_kimi_pilot as p
import expanded_full_study as w
import full_free_classification as c
import expanded_full_analysis as a
import decision_audit as d


def validate(writer_only=False):
    protocol=s.load(w.OUT/'preregistration.json');articles=protocol['articles'];writer_count=0;failed=[]
    sessions=set();old_sessions={s.load(path)['session_id'] for path in (w.ROOT/'data/main/responses').glob('*/*/*.json')}
    for article in articles:
        source=(w.ROOT/article['local_input']).read_text(encoding='utf-8');assert s.sha(source)==article['text_sha256']
        for model in s.MODELS:
            session=None;history=[];previous_usage={};previous_cost=0.
            for turn in range(1,6):
                stem=w.OUT/'responses'/article['item_id']/model/f'{turn:02d}'
                r=s.load(stem.with_suffix('.json'));private=s.load(w.ROOT/r['private_cache']);request=private['request']
                assert s.sha(s.canonical(request))==r['request_sha256']==private['request_sha256']
                assert private['response']['text']==r['text']
                prompt=protocol['initial_template'].replace('{{complete_article_text}}',source) if turn==1 else protocol['followup']
                assert request['stdin']==prompt and request['messages']==history+[{'role':'user','content':prompt}]
                assert request['prior_session_id']==session and request['command']==s.command(model,True,session)
                assert request['effort']=='high' and request['tools']=='disabled' and request['web_search']=='disabled'
                assert request['system_prompt']==s.NEUTRAL and request['source_sha256']==article['text_sha256']
                native=stem.with_suffix('.jsonl').read_text(encoding='utf-8')
                parsed=f.corrected(s.parse_result(model,native),model,previous_usage,previous_cost)
                for field in ['text','completed','session_id','raw_usage','input_total','cache_read_tokens','output_tokens','reported_cost_usd']:
                    assert parsed[field]==r[field],(article['item_id'],model,turn,field)
                assert not r['tool_events'] and not any(cat.get('tools') or cat.get('mcp_servers') or cat.get('skills') for cat in r['catalogues'])
                for key,value in p.parse_post(r['text']).items():assert r[key]==value
                history=request['messages']
                if r['status']=='ok':
                    history=history+[{'role':'assistant','content':r['text']}]
                    session=r['session_id'];previous_usage=r['raw_usage'];previous_cost=r.get('reported_session_cost_usd')
                else:
                    assert article['item_id']=='14-seti' and model=='gpt-6.1-sol' and turn==2
                    assert 'Selected model is at capacity.' in native and not r['text'] and r['exit_code']==1
                    failed.append(f"{article['item_id']}/{model}/{turn:02d}")
                assert session not in old_sessions
                sessions.add(session);writer_count+=1
    assert writer_count==400 and len(sessions)==80 and len(failed)==1
    for row in s.load(w.OUT/'imported_pilot.json'):
        assert (w.ROOT/row['source']).read_bytes()==(w.ROOT/row['destination']).read_bytes()
    if writer_only:
        print('Writer provenance passed:',writer_count,'slots,',len(sessions),'sessions; retained failure:',failed)
        return
    audit=s.load(c.OUT/'protocol.json');assert audit['definitions']==s.load(w.ROOT/'data/decision_audit/protocol.json')['definitions']
    sources={x['item_id']:(w.ROOT/x['local_input']).read_text(encoding='utf-8') for x in articles}
    attempts={};statuses=Counter()
    for path in sorted((c.OUT/'attempts').glob('*.json')):
        row=s.load(path);full=s.load(w.ROOT/row['private_cache']);payload=full['request']
        key=s.sha(s.canonical(payload));assert key==row['request_sha256']==full['request_sha256']
        assert row['response']==full['response'] and list(payload['questions'])==row['question_names']
        assert payload['model']==c.MODEL and payload['provider']=={'only':['respan'],'order':['respan'],'allow_fallbacks':False,'max_price':{'prompt':0,'completion':0}}
        assert s.sha(payload['state'])==row['request']['state_sha256']
        assert s.sha(s.canonical(payload['questions']))==row['request']['questions_sha256']
        raw=row['response'];cost=raw.get('usage',{}).get('cost');assert cost is None or cost==0
        if row['status']==200:assert raw['model']==c.MODEL and raw['provider']=='Respan' and cost==0
        slot=(key,row['attempt_number']);assert slot not in attempts;attempts[slot]=row;statuses[str(row['status'])]+=1
    def resolve(payload):
        key=s.sha(s.canonical(payload))
        for attempt in range(1,c.MAX_ATTEMPTS+1):
            row=attempts.get((key,attempt))
            if row is None:return {}
            if row['status']==200:return d.parse_decision(row['response'],payload['questions'])
            if row['status'] in [413,504] and len(payload['questions'])>4:
                entries=list(payload['questions'].items());mid=len(entries)//2
                return {**resolve(dict(payload,questions=dict(entries[:mid]))),**resolve(dict(payload,questions=dict(entries[mid:])))}
            if row['status'] not in [0,429,500,502,503,504]:return {}
        return {}
    case_count=0;answer_count=0
    for article in articles:
        for model in s.MODELS:
            for turn in range(1,6):
                for condition in ['baseline','expanded']:
                    path=c.OUT/'cases'/condition/article['item_id']/model/f'{turn:02d}.json'
                    saved=s.load(path);value=c.record_for(condition,article['item_id'],model,turn)
                    assert saved['writer_request_sha256']==value['record']['request_sha256']
                    assert saved['strict_readable']==value['strict_readable'] and saved['input_kind']==value['input_kind']
                    expected={};batch_keys=[]
                    if value['text'] is not None:
                        assert saved['input_sha256']==s.sha(value['text'])
                        for payload in c.payloads(value['text'],sources[article['item_id']],audit):
                            expected.update(resolve(payload));batch_keys.append(s.sha(s.canonical(payload)))
                        assert batch_keys==saved['batch_request_hashes']
                    assert saved['answers']==expected
                    assert len(expected)==240 if saved['status']=='complete' else True
                    answer_count+=sum(v['valid'] for v in expected.values());case_count+=1
    assert case_count==800 and not list((c.OUT/'started').glob('*.json'))
    # Replay a portable copy with no private source/cache, repository modules, network or CLI.
    tracked=[path for path in a.OUT.iterdir() if path.suffix in ['.csv','.json'] and path.name not in ['validation.json','examples.json','figure_validation.json']]
    expected={path.name:path.read_bytes() for path in tracked}
    with tempfile.TemporaryDirectory(prefix='linkedin-40-full-replay-') as temp:
        portable=Path(temp)
        for folder in ['data/main/responses','data/simple_prose_v3_full/responses','data/simple_prose_v3_full_classifier/cases']:
            shutil.copytree(w.ROOT/folder,portable/folder)
        for file in ['data/main/articles.json','data/prose_lexicon.json','data/simple_prose_v3_full_classifier/protocol.json','data/expanded_full_comparison/source_overlap.json']:
            target=portable/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(w.ROOT/file,target)
        shutil.copytree(c.OUT/'attempts',portable/'data/simple_prose_v3_full_classifier/attempts')
        names=['smoke_study','full_study','tagged_kimi_pilot','expanded_full_study','decision_audit','full_free_classification','expanded_full_analysis']
        aliases={'smoke_study':'s','full_study':'f','tagged_kimi_pilot':'p','expanded_full_study':'w','decision_audit':'d','full_free_classification':'c'}
        code='from pathlib import Path\nimport types, socket, subprocess, requests\nROOT=Path.cwd()\nMODULES={}\n'
        code+='def denied(*args,**kwargs):raise AssertionError("Offline replay attempted external work")\n'
        code+='socket.create_connection=denied\nsubprocess.Popen=denied\nrequests.sessions.Session.request=denied\n'
        for name in names:
            source=(w.ROOT/(name+'.py')).read_text(encoding='utf-8')
            for dependency,alias in aliases.items():source=source.replace('import '+dependency+' as '+alias+'\n','')
            code+=f'module=types.ModuleType({("embedded_"+name)!r})\nmodule.__file__=str(ROOT/{(name+".py")!r})\n'
            for dependency,alias in aliases.items():code+=f'if {dependency!r} in MODULES:module.__dict__[{alias!r}]=MODULES[{dependency!r}]\n'
            code+=f'exec(compile({source!r},module.__file__,"exec"),module.__dict__)\nMODULES[{name!r}]=module\n'
        code+='MODULES["expanded_full_analysis"].analyse()\n'
        runner=portable/'replay.py';runner.write_text(code,encoding='utf-8')
        subprocess.run(['python','-X','utf8',str(runner)],cwd=portable,capture_output=True,text=True,check=True)
        for name,content in expected.items():assert (portable/'data/expanded_full_comparison'/name).read_bytes()==content,name
    result=dict(writer_slots=writer_count,writer_conversations=len(sessions),failed_generations=failed,
                cached_pilot_bytes_identical=True,exact_prompt_history_and_native_counters_checked=True,
                classifier_cases=case_count,valid_predicates=answer_count,http_attempts=len(attempts),http_statuses=dict(statuses),
                native_answer_reconstruction=True,zero_price_provider_guard_checked=True,
                source_and_module_free_replay_identical=True,external_calls_blocked_during_replay=True)
    s.save(a.OUT/'validation.json',result);print(json.dumps(result,indent=2));return result


if __name__=='__main__':validate()
