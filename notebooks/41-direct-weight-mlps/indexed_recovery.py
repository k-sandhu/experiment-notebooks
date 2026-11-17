"""Owner-requested indexed JSON and continuation workflow. Never invent a parameter."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import json
import math
import re
from pathlib import Path
import experiment as e
from analysis import indexed_entries, missing_ranges

MAX_NEW_CALLS=1
MAX_CONTINUATIONS=2
COUNTS={name:int(e.np.prod(shape)) for name,shape in e.SHAPES.items()}
INDEX_SCHEMA={'type':'object','additionalProperties':False,'properties':{
    name:{'type':'object','additionalProperties':{'type':'number'}} for name in COUNTS}}
FORMAT='''
OWNER-REQUESTED OUTPUT FORMAT RECOVERY. No classification scores or other authors' weights are supplied.
Continue the original numerical-authoring task. Return only a JSON object containing numbered
parameter objects. Keys MUST be quoted JSON strings, not Python integer keys. Use exactly:
{"W1":{"1":value,...,"4096":value},"b1":{"1":value,...,"64":value},
 "W2":{"1":value,...,"2048":value},"b2":{"1":value,...,"32":value},
 "W3":{"1":value,...,"320":value},"b3":{"1":value,...,"10":value}}
The ellipses above explain the format; your answer must explicitly write EVERY numeric entry.
Indices are ONE-BASED within each tensor, row-major, using the architecture and code in the original task.
W1: 4096 values, b1: 64, W2: 2048, b2: 32, W3: 320, b3: 10. Total 6570.
After reaching the exact final index of a tensor, close its object and move to the next tensor.
After b3 index 10, close the JSON and STOP. Never produce an index outside its stated range.
No prose, predictions, code, symbolic constants, missing-entry shorthand, or omitted zero entries.
Zero is allowed, but only you choose the numerical values. The tester only maps your explicit indices.
If your response reaches an output-size limit, the tester will preserve complete numeric entries and
ask CONTINUE with the remaining indices. Future replies may omit completed tensors and include only
the remaining numbered entries. Do not replace a previously supplied indexed entry. No optimizer,
tools, shell, code execution, files, web, plugins, skills or other agents are available.
'''



def prepare_messages(key):
    original=json.loads((e.DATA/'responses'/key/'response.json').read_text(encoding='utf-8'))
    messages=[{'role':'user','content':original['request']['prompt']}]
    if key=='gemini':
        previous=json.loads((e.DATA/'recovery/gemini-low/response.json').read_text(encoding='utf-8'))
        messages.append({'role':'assistant','content':previous['answer']})
        feedback='Your prior flat JSON contained 6013 values rather than 6570. Its omissions cannot be located reliably by the tester. Supply a NEW complete indexed parameter set, choosing every value yourself; do not assume the old flat vector is complete.'
    else:
        # Only provider-emitted text is available. We do not reconstruct withheld thoughts.
        if original.get('reasoning'):
            messages.append({'role':'assistant','content':'Prior provider-emitted work, with no final weights:\n'+original['reasoning']})
        feedback='The previous response exhausted the output limit while reasoning and emitted no final numerical weights. CONTINUE the task from the available earlier work and now emit the indexed numerical answer.'
    messages.append({'role':'user','content':FORMAT+'\n'+feedback})
    return messages

def collect_indexed(key,max_calls):
    root=e.DATA/'indexed'/key;root.mkdir(parents=True,exist_ok=True)
    messages=prepare_messages(key);merged={name:{} for name in COUNTS};records=[];new_calls=0;issues=[]
    for turn in range(1,MAX_CONTINUATIONS+2):
        out=root/f'turn-{turn:02d}';out.mkdir(exist_ok=True)
        body=e.openrouter_body(key,'');body['messages']=copy.deepcopy(messages)
        body['response_format']['json_schema']['schema']=INDEX_SCHEMA
        body['reasoning']={'enabled':False,'exclude':False}
        if key=='nemotron':body.update(provider={'only':['nvidia'],'allow_fallbacks':False,'max_price':{'prompt':0,'completion':0,'request':0}},stream=True,stream_options={'include_usage':True})
        else:
            # Low effort supported by Gemini. Retain any provider-exposed reasoning.
            body['reasoning']={'effort':'low','exclude':False}
            body={'endpoint':'/v1/chat/completions','model':e.MODELS[key]['canonical'],
                  'provider':{'only':['google-vertex'],'allow_fallbacks':False},'completion_window':'24h',
                  'requests':[{'custom_id':f'digits-indexed-{key}-{turn}','body':body}]}
        request={'protocol':'digits-indexed-v1','config':e.MODELS[key],'body':body,'schema':INDEX_SCHEMA,
                 'tools_enabled':[],'turn':turn,'expected_tensor_counts':COUNTS,'task_feedback':False}
        cache_key=e.sha(json.dumps(request,sort_keys=True));cache=out/'response.json'
        if cache.exists():
            record=json.loads(cache.read_text(encoding='utf-8'));assert record['cache_key']==cache_key
        else:
            assert new_calls<max_calls,'Fresh-call cap reached; rerun explicitly to continue from cached blocks'
            assert not (out/'started.json').exists(),'Unresolved indexed request; do not regenerate'
            e.dump(out/'request.json',request);e.dump(out/'started.json',{'started_utc':e.utc(),'cache_key':cache_key});new_calls+=1
            try:e.requests.get(e.os.environ.get('LANGFUSE_HOST','http://localhost:3300').rstrip('/')+'/api/public/health',timeout=2)
            except e.requests.RequestException:pass
            print(f'INDEXED START {key} {turn}',flush=True)
            record=e.run_openrouter(key,out,request);record.update(cache_key=cache_key,request=request);e.dump(cache,record)
            (out/'weights_output.json').write_text(record.get('answer',''),encoding='utf-8')
            (out/'reasoning.txt').write_text(record.get('reasoning',''),encoding='utf-8')
            e.trace_call(cache_key,e.MODELS[key],request,record)
        records.append(record)
        entries,issue=indexed_entries(record.get('answer',''));conflicts=[]
        provider_error=record.get('error') or {}
        if not record.get('answer') and provider_error.get('code') in [408,429,500,502,503,504]:
            issue={'kind':'provider_temporarily_unavailable','partial':True,'provider_error':provider_error}
        for name,values in entries.items():
            for index,value in values.items():
                if index in merged[name] and merged[name][index]!=value:conflicts.append([name,index])
                else:merged[name][index]=value
        coverage={'turn':turn,'counts':{k:len(v) for k,v in merged.items()},'total':sum(map(len,merged.values())),
                  'expected_total':e.N_PARAMS,'missing_ranges':missing_ranges(merged),'parse_issue':issue,'conflicts':conflicts}
        e.dump(out/'coverage.json',coverage);e.dump(root/'coverage.json',coverage)
        if issue:issues.append(issue)
        if conflicts or (issue and not issue.get('partial')):raise ValueError('Indexed structural error/conflict; no silent repair: '+json.dumps(coverage))
        if not coverage['missing_ranges']:
            flat=[merged[name][i] for name,count in COUNTS.items() for i in range(1,count+1)]
            # Every value has a concrete model-emitted tensor/index source; no filling.
            answer=json.dumps({'weights':flat},separators=(',',':'))
            assembled={'answer':answer,'completed':True,'tool_events':[t for r in records for t in r.get('tool_events',[])],
                       'usage':{'per_turn':[r.get('usage') for r in records]},'cost_usd':sum(r.get('cost_usd') or 0 for r in records) if all(r.get('cost_usd') is not None for r in records) else None,
                       'started_utc':records[0]['started_utc'],'finished_utc':records[-1]['finished_utc'],
                       'wall_seconds':sum(r['wall_seconds'] for r in records),'reasoning':'\n'.join(r.get('reasoning','') for r in records),
                       'request':{'protocol':'digits-indexed-v1','turn_cache_keys':[r['cache_key'] for r in records],'expected_tensor_counts':COUNTS},
                       'assembly':'One-based indices mapped to existing tensor layout, no value changes','source_coverage':coverage}
            e.dump(root/'assembled_response.json',assembled);(root/'weights_output.json').write_text(answer,encoding='utf-8')
            (root/'reasoning.txt').write_text(assembled['reasoning'],encoding='utf-8')
            result=e.validate_and_score(key,assembled,out_override=root)
            print(json.dumps({'indexed_model':key,'turns':turn,'coverage':coverage['total'],'failure':result['format_failure'],'test':result.get('test',{}).get('accuracy')}),flush=True)
            return
        # Follow-up is about output coverage only. No accuracy or parameter suggestions.
        messages.append({'role':'assistant','content':record.get('answer') or '[No final parameter content was emitted.]'})
        messages.append({'role':'user','content':'CONTINUE the same indexed parameter output. Start with the first missing index below. Return a NEW valid JSON object containing ONLY remaining indexed entries. Do not redo completed entries. Do not produce prose or predictions. Missing tensor index ranges: '+json.dumps(coverage['missing_ranges'])})
    e.dump(root/'results.json',{'model':e.MODELS[key]['model'],'model_key':key,'format_failure':'Incomplete indexed coverage after continuation cap',
                              'failure_category':'missing_indexed_values','coverage':coverage,'tester_changed_weights':False})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',default=['gemini'],choices=['gemini','nemotron']);p.add_argument('--max-new-calls',type=int,default=MAX_NEW_CALLS)
    args=p.parse_args()
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        tasks={pool.submit(collect_indexed,key,args.max_new_calls):key for key in args.models}
        for future in as_completed(tasks):
            try:future.result()
            except Exception as exc:
                e.dump(e.DATA/'indexed'/tasks[future]/'failure.json',{'error':str(exc),'at_utc':e.utc()})
                print(json.dumps({'model':tasks[future],'error':str(exc)}),flush=True)
