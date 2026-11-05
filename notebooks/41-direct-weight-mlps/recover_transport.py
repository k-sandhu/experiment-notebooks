"""One explicitly documented transport recovery, no test feedback or weight repair."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import experiment as e

def recover(key,low_effort=False):
    original=e.DATA/'responses'/key
    prior=json.loads((original/'response.json').read_text(encoding='utf-8'))
    out=e.DATA/'recovery'/(key+'-low' if low_effort else key);out.mkdir(parents=True,exist_ok=True)
    request=copy.deepcopy(prior['request'])
    request['recovery_of']=prior['cache_key']
    if key=='gemini':
        relaxed={'type':'object','additionalProperties':False,'required':['weights'],
                 'properties':{'weights':{'type':'array','items':{'type':'number'}}}}
        request['schema']=relaxed
        request['body']['requests'][0]['body']['response_format']['json_schema']['schema']=relaxed
        request['body']['requests'][0]['custom_id']='digits-v1-gemini-schema-recovery'
        request['recovery_reason']='Provider rejected exact-length grammar before decoding any token. Same prompt; final 6570 count still strictly checked.'
        if low_effort:
            previous=json.loads((e.DATA/'recovery/gemini/response.json').read_text(encoding='utf-8'))
            request['recovery_of']=previous['cache_key']
            request['body']['requests'][0]['body']['reasoning']['effort']='low'
            request['body']['requests'][0]['custom_id']='digits-v1-gemini-low-output-recovery'
            request['config']['effort']='low'
            request['recovery_reason']='Prior high-effort schema recovery exhausted 32768 emitted tokens in reasoning, with no final weights. Same user prompt and validator, low reasoning effort, one final transport/output-budget attempt.'
    else:
        session=next(ev['session_id'] for ev in prior['events'] if ev.get('type')=='result')
        cmd=e.cli_command(key,out)
        cmd[cmd.index('--effort')+1]='high'
        cmd[cmd.index('--max-budget-usd')+1]='20.0'
        cmd+=['--resume',session]
        request['command']=cmd;request['config']['effort']='high';request['output_token_cap']=128000
        request['prompt']='Continue the unfinished weight-authoring task in this saved conversation. Return only the complete requested JSON object with all 6570 numerical weights for the same fixed digit classifier. The dataset, architecture and preprocessing in the original prompt still apply. No tools or intermediate evaluation are available. No test results or other models\' answers are supplied.'
        request['recovery_reason']='Continue persisted context after output/budget exhaustion; no task feedback. High effort and 128000 output cap; report separately from original xhigh failure.'
    keyhash=e.sha(json.dumps(request,sort_keys=True));cache=out/'response.json'
    if cache.exists():
        record=json.loads(cache.read_text(encoding='utf-8'));assert record['cache_key']==keyhash
    else:
        assert not (out/'started.json').exists(),'Unresolved recovery; do not regenerate'
        e.dump(out/'request.json',request);e.dump(out/'started.json',{'cache_key':keyhash,'started_utc':e.utc()})
        print('RECOVERY START '+key,flush=True)
        record=e.run_openrouter(key,out,request) if key=='gemini' else e.run_cli(key,out,request)
        record.update(cache_key=keyhash,request=request)
        e.dump(cache,record)
        (out/'weights_output.json').write_text(record.get('answer',''),encoding='utf-8')
        (out/'reasoning.txt').write_text(record.get('reasoning',''),encoding='utf-8')
        e.trace_call(keyhash,e.MODELS[key],request,record)
    result=e.validate_and_score(key,record,out_override=out)
    print(json.dumps({'recovery':key,'format_failure':result['format_failure'],'test':result.get('test',{}).get('accuracy')}),flush=True)

if __name__=='__main__':
    import sys
    if '--gemini-low' in sys.argv:recover('gemini',low_effort=True)
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            for future in [pool.submit(recover,key) for key in ['gemini','opus']]:future.result()
