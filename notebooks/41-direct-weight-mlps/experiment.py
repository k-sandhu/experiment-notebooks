"""Direct numeric weight submissions only. No training or tester-authored candidate weights."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import zipfile
import numpy as np
import requests

ROOT = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA = ROOT / 'data'
MODELS = {
    'astra': {'backend':'codex', 'model':'gpt-6-astra', 'effort':'xhigh'},
    'sol': {'backend':'codex', 'model':'gpt-6.1-sol', 'effort':'xhigh'},
    'opus': {'backend':'claude', 'model':'claude-opus-5-5', 'effort':'xhigh'},
    'muse': {'backend':'muse', 'model':'muse-wonder-full-1.0', 'effort':'xhigh'},
    'nemotron': {'backend':'openrouter', 'model':'nvidia/nemotron-3.5-super-vl:free', 'canonical':'nvidia/nemotron-3.5-super-vl-20261015'},
    'gemini': {'backend':'batch', 'model':'google/gemini-4-argon:batch', 'canonical':'google/gemini-4-argon-20261013', 'effort':'high'},
}
N_VISIBLE = 2048
MAX_NEW_CALLS = 1
MAX_OUTPUT_TOKENS = 131072
CLAUDE_MAX_BUDGET_USD = 5.0
SEED = 20261103
SHAPES = {'W1':[64,64], 'b1':[64], 'W2':[32,64], 'b2':[32], 'W3':[10,32], 'b3':[10]}
N_PARAMS = sum(int(np.prod(s)) for s in SHAPES.values())
assert N_PARAMS == 6570
SCHEMA = {'type':'object', 'additionalProperties':False, 'required':['weights'], 'properties':{
    'weights':{'type':'array','minItems':N_PARAMS,'maxItems':N_PARAMS,'items':{'type':'number'}}}}
PREPOST = '''import numpy as np
def preprocess(raw_pixels):
    # Exactly 64 integers, row-major flattening of the 8 by 8 image.
    # 0 is blank, 16 is the largest ink count. No fitted transform.
    return np.asarray(raw_pixels, dtype=np.float64) / 16.0
def network(raw_pixels, W1, b1, W2, b2, W3, b3):
    x = preprocess(raw_pixels)
    h1 = np.maximum(x @ W1.T + b1, 0.0)
    h2 = np.maximum(h1 @ W2.T + b2, 0.0)
    return h2 @ W3.T + b3
def postprocess(scores):
    # Digit labels are 0 through 9. Ties choose the lowest index.
    return np.argmax(scores, axis=-1)
'''

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')

def sha(value):
    return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def trace_call(key, config, request, record):
    """One trace per fresh call, silently optional, never called for cache replay."""
    host = os.environ.get('LANGFUSE_HOST','http://localhost:3300').rstrip('/')
    auth = (os.environ.get('LANGFUSE_PUBLIC_KEY',''),os.environ.get('LANGFUSE_SECRET_KEY',''))
    try:
        healthy = requests.get(host+'/api/public/health',timeout=2).ok
    except requests.RequestException:
        healthy = False
    if not healthy or not all(auth): return
    def attr(k,v): return {'key':k,'value':{'stringValue':v if isinstance(v,str) else json.dumps(v,default=str)}}
    notebook = '41-direct-weight-mlps'
    attrs = [attr('langfuse.observation.type','generation'),attr('langfuse.observation.model.name',config['model']),
             attr('langfuse.observation.input',request),attr('langfuse.observation.output',record.get('answer','')),
             attr('langfuse.trace.name','41 direct MLP weights'),attr('langfuse.environment','notebook'),
             attr('langfuse.trace.metadata.notebook',notebook),attr('langfuse.trace.metadata.cache_key',key),
             attr('langfuse.observation.metadata.native_usage',record.get('usage'))]
    if record.get('cost_usd') is not None: attrs.append(attr('langfuse.observation.cost_details',{'total':record['cost_usd']}))
    start = dt.datetime.fromisoformat(record['started_utc']); end = dt.datetime.fromisoformat(record['finished_utc'])
    span = {'traceId':sha(notebook+'|'+key)[:32], 'spanId':sha(notebook+'|'+key+'|gen|0')[:16],
            'name':'Write 6570 MLP parameters','kind':1,'attributes':attrs,
            'startTimeUnixNano':str(int(start.timestamp()*1e9)),'endTimeUnixNano':str(int(end.timestamp()*1e9))}
    try:
        requests.post(host+'/api/public/otel/v1/traces',json={'resourceSpans':[{'resource':{'attributes':[
            attr('service.name','experiment-notebooks')]},'scopeSpans':[{'scope':{'name':notebook},'spans':[span]}]}]},auth=auth,timeout=10)
    except requests.RequestException: pass

def prepare():
    DATA.mkdir(parents=True,exist_ok=True)
    source = DATA/'source'; source.mkdir(exist_ok=True)
    url = 'https://archive.ics.uci.edu/static/public/80/optical+recognition+of+handwritten+digits.zip'
    archive = source/'optdigits.zip'
    if not archive.exists():
        response = requests.get(url,timeout=45); response.raise_for_status(); archive.write_bytes(response.content)
    with zipfile.ZipFile(archive) as z:
        for name in ['optdigits.tra','optdigits.tes','optdigits.names']:
            (source/name).write_bytes(z.read(name))
    train = np.loadtxt(source/'optdigits.tra',delimiter=',',dtype=np.int64)
    test = np.loadtxt(source/'optdigits.tes',delimiter=',',dtype=np.int64)
    assert train.shape == (3823,65) and test.shape == (1797,65)
    rng=np.random.default_rng(SEED); selected=[]
    for label in range(10):
        selected.extend(rng.permutation(np.flatnonzero(train[:,-1]==label))[:N_VISIBLE//10+(label<N_VISIBLE%10)])
    selected=np.asarray(selected);selected=selected[rng.permutation(len(selected))]
    remaining=np.setdiff1d(np.arange(len(train)),selected)
    np.savez_compressed(DATA/'dataset.npz',visible=train[selected],visible_indices=selected,
                        hidden_train=train[remaining],hidden_train_indices=remaining,test=test)
    sample='\n'.join(','.join(map(str,row)) for row in train[selected])+'\n'
    (DATA/'visible_sample.csv').write_text(sample,encoding='utf-8')
    (DATA/'pre_post_processing.py.txt').write_text(PREPOST,encoding='utf-8')
    prompt='''You are the sole numerical weight author for a neural-network classifier.
You have NO tools, code execution, calculator, shell, file access, web, skills, plugins,
MCP or other agents. Reason internally. The tester loads your numerical output unchanged.
It will not train, optimize, correct, fill, truncate or choose any candidate parameter.

TASK: Recognize handwritten digits 0 through 9 from 8 by 8 grayscale ink-count images.
Each CSV line below has 64 pixel values in row-major order, then its integer digit label.
Pixels are integers 0..16, where 0 is blank. The 2048 lines are the ONLY labelled sample
you receive. They were selected, approximately balanced by digit, from the UCI Optical
Recognition of Handwritten Digits official training split. You will be evaluated on its
withheld 1797-image official test split and the 1775 training images not shown here.
Do not output predictions, code or a trained-model download. Your complete numbers must
implement a useful classifier in the fixed MLP below, with no external lookup at inference.

ARCHITECTURE: 64 -> 64 ReLU -> 32 ReLU -> 10 linear scores, float64 computation.
There are exactly 6570 independent editable weights and biases. No other inference
operations are permitted besides the exact preprocessing and postprocessing below.
Sparse constructions and zero biases are allowed; there is no density or Gaussianity
requirement. Prefer numerically moderate coefficients, but every finite value is allowed.

EXACT PREPROCESSING, FORWARD COMPUTATION AND POSTPROCESSING (read, do not execute):
'''+PREPOST+'''
RETURN ONLY {"weights":[6570 explicit finite JSON numbers]}.
Flatten tensors in the following order; flatten each tensor in C/row-major order.
W1 [64,64]: offsets 0..4095, then b1 [64]: 4096..4159;
W2 [32,64]: 4160..6207, then b2 [32]: 6208..6239;
W3 [10,32]: 6240..6559, then b3 [10]: 6560..6569.
Rows of a weight matrix are output neurons; columns are input neurons.
Return ALL 6570 numbers, including zeros. No prose, Markdown, code, formulas, ellipses,
repetition notation, omitted entries, extra keys, or special NaN/Infinity values.
There is one submission and no intermediate feedback. Maximize held-out accuracy.

LABELLED SAMPLE CSV (columns p00,p01,...,p63,label):
'''+sample+'\nEND SAMPLE. Return only the complete JSON weights object.\n'
    (DATA/'prompt.txt').write_text(prompt,encoding='utf-8');dump(DATA/'weights_schema.json',SCHEMA)
    dataset_keys={tuple(row[:64]) for row in train[selected]}
    manifest={'protocol':'digits-v1','prepared_utc':utc(),'source_url':url,
        'source_page':'https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits',
        'creators':'E. Alpaydin and C. Kaynak','source_donation_date':'1998-06-30','licence':'CC BY 4.0',
        'freshness_exception':'User explicitly requested public data. Old public benchmark may have been in teacher training; treat scores as upper bounds.',
        'archive_sha256':sha(archive.read_bytes()),'file_sha256':{name:sha((source/name).read_bytes()) for name in ['optdigits.tra','optdigits.tes','optdigits.names']},
        'architecture':[64,64,32,10],'shapes':SHAPES,'parameters':N_PARAMS,'seed':SEED,
        'n_visible':len(selected),'n_hidden_train':len(remaining),'n_official_test':len(test),
        'visible_class_counts':np.bincount(train[selected,-1],minlength=10).tolist(),
        'test_class_counts':np.bincount(test[:,-1],minlength=10).tolist(),
        'test_pixel_rows_duplicated_in_visible':sum(tuple(row[:64]) in dataset_keys for row in test),
        'prompt_sha256':sha(prompt),'prompt_bytes':len(prompt.encode()),'models':MODELS,
        'no_tools':True,'training_steps':0,'tester_authors_weights':False,'one_submission_per_model':True,
        'primary_metric':'official test accuracy; Wilson 95% interval conditional on this single submitted network',
        'secondary':['visible-sample accuracy','unused-training accuracy','per-class accuracy','confusion matrix','weight statistics'],
        'no_content_retries':True,'no_cancellation_on_task_switch':True,
        'reasoning_policy':'Save raw provider-emitted reasoning, deltas and opaque details; missing reasoning is not reconstructed.',
        'user_authorized_closed_openrouter_exception':'google/gemini-4-argon:batch explicitly requested for this experiment only.'}
    path=DATA/'manifest.json'
    if path.exists(): assert json.loads(path.read_text(encoding='utf-8'))['prompt_sha256']==manifest['prompt_sha256']
    else: dump(path,manifest)
    print(json.dumps({k:manifest[k] for k in ['parameters','n_visible','n_hidden_train','n_official_test','prompt_bytes','test_pixel_rows_duplicated_in_visible']}),flush=True)

def private_dir(key):
    path=Path(tempfile.gettempdir())/'direct-weights-41'/key
    (path/'empty').mkdir(parents=True,exist_ok=True)
    (path/'neutral.txt').write_text('You are a numerical weight author. Return only the requested JSON data.\n',encoding='utf-8')
    dump(path/'empty-mcp.json',{'mcpServers':{}})
    return path

def cli_command(key, out):
    cfg=MODELS[key];private=private_dir(key)
    if cfg['backend']=='codex':
        cmd=json.loads((DATA/'transport'/'codex_template.json').read_text(encoding='utf-8'))
        if '--ephemeral' in cmd:cmd.remove('--ephemeral')
        cmd[cmd.index('-m')+1]=cfg['model'];cmd[cmd.index('-C')+1]=str(private/'empty')
        cmd[cmd.index('--output-schema')+1]=str(DATA/'weights_schema.json')
        for i,arg in enumerate(cmd):
            if arg.startswith('model_reasoning_effort='):cmd[i]='model_reasoning_effort='+json.dumps(cfg['effort'])
            if arg.startswith('model_instructions_file='):cmd[i]='model_instructions_file='+json.dumps(str(private/'neutral.txt'))
        return cmd[:-1]+['-c','model_context_window=1050000','-c','model_auto_compact_token_limit=1000000',
                        '--output-last-message',str(out/'cli_last_message.json'),'-']
    if cfg['backend']=='claude':
        return [shutil.which('claude'),'--print','--model',cfg['model'],'--effort',cfg['effort'],'--tools','',
                '--safe-mode','--disable-slash-commands','--strict-mcp-config','--mcp-config',str(private/'empty-mcp.json'),
                '--disallowedTools','mcp__*','--system-prompt',(private/'neutral.txt').read_text(),
                '--output-format','stream-json','--verbose','--include-partial-messages','--max-budget-usd',str(CLAUDE_MAX_BUDGET_USD)]
    exe=os.environ.get('MUSE_EXECUTABLE') or shutil.which('muse.cmd') or shutil.which('muse')
    return [exe,'exec','--preset','empty','--disable-web-tools','--disable-reminders','--disable-request-user-input',
            '--no-foreign-personal-context','--disable-shell','--disable-write','--model',cfg['model'],
            '--reasoning-effort',cfg['effort'],'--max-model-steps','1','--workspace',str(private/'empty'),
            '--output-schema',str(DATA/'weights_schema.json'),'--prompt-file',str(DATA/'prompt.txt'),'--json']

def parse_cli(backend, events):
    answer='';reasoning=[];usage={};completed=False;tools=[];cost=None;resolved=[];catalogues=[]
    if backend=='codex':
        for e in events:
            if e.get('type')=='item.completed':
                item=e.get('item',{});kind=item.get('type')
                if kind=='agent_message':answer=item.get('text','')
                elif kind=='reasoning' and item.get('text'):reasoning.append(item['text'])
                elif kind not in ['reasoning','error']:tools.append(item)
            if e.get('type')=='turn.completed':usage=e.get('usage',{});completed=True
    elif backend=='claude':
        for e in events:
            if e.get('type')=='system' and e.get('subtype')=='init':
                catalogues.append({k:e.get(k) for k in ['tools','mcp_servers','skills','plugins']});resolved.append(e.get('model'))
            if e.get('type')=='assistant':
                for block in e.get('message',{}).get('content',[]):
                    if block.get('type')=='thinking':reasoning.append(block.get('thinking',''))
                    if block.get('type')=='tool_use':tools.append(block)
            if e.get('type')=='result':
                answer=e.get('result','');usage=e.get('usage',{});cost=e.get('total_cost_usd')
                completed=e.get('subtype')=='success' and not e.get('is_error',False)
    else:
        for e in events:
            kind=e.get('payload_type','');p=e.get('payload',{})
            if kind=='run.terminal.completed':answer=p.get('text','');completed=True
            if kind=='run.usage':usage=p
            if 'reasoning' in kind or 'thinking' in kind:
                reasoning.append(p.get('text') or p.get('delta') or json.dumps(p))
            if kind.startswith('tool.') or 'tool_call' in kind:tools.append(e)
    return dict(answer=answer,reasoning='\n'.join(reasoning),usage=usage,completed=completed,
                tool_events=tools,cost_usd=cost,reported_models=resolved,catalogues=catalogues)

def run_cli(key, out, request):
    cfg=MODELS[key];cmd=request['command'];private=private_dir(key)
    env=os.environ.copy()
    for name in list(env):
        if name.startswith(('CODEX_','CLAUDE_')) or name in ['OPENAI_API_KEY','ANTHROPIC_API_KEY','OPENROUTER_API_KEY']:env.pop(name,None)
    env['PYTHONIOENCODING']='utf-8'
    credential=None
    if cfg['backend']=='codex':
        flags=[]
        for i,arg in enumerate(cmd):
            if arg=='-c':flags.extend(['-c',cmd[i+1]])
        original=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
        env['CODEX_HOME']=str(private)
        pre=subprocess.run([cmd[0],'-C',str(private/'empty')]+flags+['debug','prompt-input','PREFLIGHT; NO MODEL CALL.'],
                           env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
        (out/'preflight.json').write_text(pre.stdout,encoding='utf-8')
        assert pre.returncode==0,pre.stderr
        assert not any(s in pre.stdout for s in ['<skills_instructions>','### Available skills','# AGENTS.md instructions'])
        credential=private/'auth.json';assert not credential.exists(),'Unresolved prior private credential'
        shutil.copyfile(original/'auth.json',credential)
    if cfg['backend']=='claude':env['CLAUDE_CODE_MAX_OUTPUT_TOKENS']=str(request.get('output_token_cap',64000))
    events=[];started=utc();tick=time.monotonic()
    try:
        with (out/'events.jsonl').open('w',encoding='utf-8') as log,(out/'stderr.txt').open('w',encoding='utf-8') as err:
            child=subprocess.Popen(cmd,cwd=private/'empty',env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                   stderr=err,text=True,encoding='utf-8',bufsize=1)
            dump(out/'status.json',{'status':'running','started_utc':started,'pid':child.pid,'model':cfg['model']})
            if cfg['backend']!='muse':child.stdin.write(request['prompt'])
            child.stdin.close()
            for line in child.stdout:
                log.write(line);log.flush()
                try:events.append(json.loads(line))
                except json.JSONDecodeError:pass
            code=child.wait()
    finally:
        if credential is not None and credential.exists():credential.unlink()
    parsed=parse_cli(cfg['backend'],events)
    return dict(parsed,events=events,exit_code=code,started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-tick)

def openrouter_body(key,prompt):
    cfg=MODELS[key]
    body={'model':cfg['model'] if key=='nemotron' else cfg['canonical'],'messages':[{'role':'user','content':prompt}],
          'temperature':0,'max_tokens':MAX_OUTPUT_TOKENS,'reasoning':{'enabled':True,'exclude':False},
          'response_format':{'type':'json_schema','json_schema':{'name':'mlp_weights','strict':True,'schema':SCHEMA}},
          'tool_choice':'none','plugins':[]}
    if key=='gemini':body['reasoning']={'effort':'high','exclude':False}
    return body

def run_openrouter(key,out,request):
    cfg=MODELS[key];headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY']}
    started=utc();tick=time.monotonic();events=[];parts=[];reasons=[];usage={};tools=[];completed=False;error=None
    if cfg['backend']=='batch':
        submit=out/'batch_submission.json'
        if submit.exists():batch=json.loads(submit.read_text(encoding='utf-8'))
        else:
            response=requests.post('https://openrouter.ai/api/v1/batches',headers=headers,json=request['body'],timeout=(30,120))
            batch=response.json();dump(submit,batch)
            assert response.ok,(response.status_code,batch)
        assert batch.get('id'),batch
        dump(out/'status.json',{'status':'batch_pending','id':batch['id'],'started_utc':started})
        with (out/'batch_polls.jsonl').open('a',encoding='utf-8') as log:
            while batch.get('status') not in ['completed','failed','cancelled','expired']:
                time.sleep(30)
                response=requests.get('https://openrouter.ai/api/v1/batches/'+batch['id'],headers=headers,timeout=30)
                response.raise_for_status();batch=response.json()
                log.write(json.dumps(batch,ensure_ascii=False)+'\n');log.flush();dump(out/'batch_latest.json',batch)
        result=(batch.get('results') or [{}])[0]
        data=(result.get('response') or {}).get('body',{})
        dump(out/'batch_result.json',batch);events=[data];usage=data.get('usage',{})
        choice=(data.get('choices') or [{}])[0];message=choice.get('message',{})
        parts=[message.get('content') or ''];reasons=[message.get('reasoning') or message.get('reasoning_content') or '']
        tools=message.get('tool_calls') or [];completed=batch.get('status')=='completed' and choice.get('finish_reason')=='stop'
        error=result.get('error') or batch.get('error')
    else:
        body=request['body']
        with (out/'events.jsonl').open('w',encoding='utf-8') as log,(out/'reasoning.txt').open('w',encoding='utf-8') as reasonlog, \
             (out/'weights_output.json').open('w',encoding='utf-8') as textlog:
            with requests.post('https://openrouter.ai/api/v1/chat/completions',headers=headers,json=body,stream=True,timeout=(30,300)) as response:
                if not response.ok: error={'status':response.status_code,'body':response.text}
                else:
                    for line in response.iter_lines(chunk_size=1,decode_unicode=True):
                        if not line or not line.startswith('data:'):continue
                        if line[5:].strip()=='[DONE]':completed=True;break
                        e=json.loads(line[5:]);events.append(e);log.write(json.dumps(e,ensure_ascii=False)+'\n');log.flush()
                        if e.get('usage'):usage=e['usage']
                        if e.get('error'):error=e['error']
                        for choice in e.get('choices',[]):
                            delta=choice.get('delta',{})
                            content=delta.get('content') or '';reason=delta.get('reasoning') or delta.get('reasoning_content') or ''
                            if not reason:reason=''.join(x.get('text',x.get('summary','')) for x in delta.get('reasoning_details',[]) if x.get('type') in ['reasoning.text','reasoning.summary'])
                            parts.append(content);reasons.append(reason);textlog.write(content);textlog.flush();reasonlog.write(reason);reasonlog.flush()
                            if delta.get('tool_calls'):tools.append(delta['tool_calls'])
                            if choice.get('finish_reason') and choice['finish_reason']!='stop':error={'finish_reason':choice['finish_reason']}
    native_cost=(batch.get('usage') or {}).get('cost') if cfg['backend']=='batch' else usage.get('cost')
    return {'answer':''.join(parts),'reasoning':''.join(reasons),'usage':usage,'completed':completed and not error,
            'tool_events':tools,'events':events,'error':error,'started_utc':started,'finished_utc':utc(),
            'wall_seconds':time.monotonic()-tick,'cost_usd':native_cost}

def collect_one(key):
    cfg=MODELS[key];out=DATA/'responses'/key;out.mkdir(parents=True,exist_ok=True)
    prompt=(DATA/'prompt.txt').read_text(encoding='utf-8')
    assert sha(prompt)==json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))['prompt_sha256']
    request={'config':cfg,'prompt':prompt,'schema':SCHEMA,'tools_enabled':[],'protocol':'digits-v1'}
    if cfg['backend'] in ['codex','claude','muse']:request['command']=cli_command(key,out)
    else:
        meta=requests.get('https://openrouter.ai/api/v1/models',timeout=30).json()['data']
        model=next(m for m in meta if m['id']==cfg['model']);assert model['canonical_slug']==cfg['canonical'];dump(out/'model_metadata.json',model)
        body=openrouter_body(key,prompt)
        if key=='nemotron':
            assert all(float(model['pricing'][k])==0 for k in ['prompt','completion'])
            body.update(provider={'only':['nvidia'],'allow_fallbacks':False,'max_price':{'prompt':0,'completion':0,'request':0}},
                        stream=True,stream_options={'include_usage':True})
        else:body={'endpoint':'/v1/chat/completions','model':cfg['canonical'],
                   'provider':{'only':['google-vertex'],'allow_fallbacks':False},'completion_window':'24h',
                   'requests':[{'custom_id':'digits-v1-gemini','body':body}]}
        request['body']=body
    keyhash=sha(json.dumps(request,sort_keys=True));cache=out/'response.json'
    if cache.exists():
        record=json.loads(cache.read_text(encoding='utf-8'));assert record['cache_key']==keyhash
        validate_and_score(key,record);return
    assert not (out/'started.json').exists(),'Prior request unresolved; inspect logs instead of regenerating'
    dump(out/'request.json',request);dump(out/'started.json',{'started_utc':utc(),'cache_key':keyhash})
    # Health check before a fresh call. Keys are never saved.
    try:requests.get(os.environ.get('LANGFUSE_HOST','http://localhost:3300').rstrip('/')+'/api/public/health',timeout=2)
    except requests.RequestException:pass
    print('START '+key,flush=True)
    try:
        record=run_cli(key,out,request) if cfg['backend'] in ['codex','claude','muse'] else run_openrouter(key,out,request)
    except Exception as exc:
        dump(out/'failure.json',{'exception':type(exc).__name__,'message':str(exc),'at_utc':utc()});raise
    record.update(cache_key=keyhash,request=request);dump(cache,record)
    (out/'weights_output.json').write_text(record.get('answer',''),encoding='utf-8')
    (out/'reasoning.txt').write_text(record.get('reasoning',''),encoding='utf-8')
    trace_call(keyhash,cfg,request,record)
    validate_and_score(key,record)
    print('FINISH '+key,flush=True)

def load_submission(text):
    payload=json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Non-finite JSON value')))
    assert isinstance(payload,dict) and set(payload)=={'weights'},'Wrong JSON keys'
    values=payload['weights'];assert isinstance(values,list),'Weights must be a JSON array'
    assert len(values)==N_PARAMS,f'Expected {N_PARAMS} weights; received {len(values)}'
    assert all(type(v) in [int,float] for v in values),'Non-numeric weight'
    flat=np.asarray(values,dtype=np.float64);assert np.isfinite(flat).all(),'Non-finite weight'
    arrays={};offset=0
    for name,shape in SHAPES.items():
        size=int(np.prod(shape));arrays[name]=flat[offset:offset+size].reshape(shape);offset+=size
    assert np.array_equal(np.concatenate([a.ravel() for a in arrays.values()]),flat)
    return arrays,flat

def forward(raw, arrays):
    x=np.asarray(raw,dtype=np.float64)/16.0
    h1=np.maximum(x@arrays['W1'].T+arrays['b1'],0)
    h2=np.maximum(h1@arrays['W2'].T+arrays['b2'],0)
    return h2@arrays['W3'].T+arrays['b3']

def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    centre=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [centre-half,centre+half]

def validate_and_score(key,record,out_override=None):
    out=Path(out_override) if out_override else DATA/'responses'/key
    result={'model':MODELS[key]['model'],'model_key':key,'format_failure':None,'failure_category':None,'tool_events':len(record.get('tool_events',[])),
            'tester_changed_weights':False,'training_steps':0,'parameters':N_PARAMS,
            'usage':record.get('usage'),'cost_usd':record.get('cost_usd'),'wall_seconds':record.get('wall_seconds'),
            'reasoning_characters':len(record.get('reasoning',''))}
    try:
        assert record.get('completed') and record.get('exit_code',0)==0,'Incomplete or failed model response'
        assert not record.get('tool_events'),'Tool protocol failure'
        for cat in record.get('catalogues',[]):
            assert not any(cat.get(k) for k in ['tools','mcp_servers','skills']),'Nonempty tool/customization catalogue'
            assert all(p.get('path')=='builtin' for p in cat.get('plugins',[])),'Unexpected non-builtin plugin'
        arrays,flat=load_submission(record['answer']);np.savez_compressed(out/'candidate.npz',**arrays)
        with np.load(out/'candidate.npz') as saved:assert all(np.array_equal(saved[k],v) for k,v in arrays.items())
        result['weights']={'zeros':int(np.sum(flat==0)),'max_abs':float(np.abs(flat).max()),'mean':float(flat.mean()),'rms':float(np.sqrt(np.mean(flat**2)))}
        with np.load(DATA/'dataset.npz') as data:
            predictions={}
            for split in ['visible','hidden_train','test']:
                rows=data[split];scores=forward(rows[:,:64],arrays);assert np.isfinite(scores).all(),'Non-finite network scores'
                pred=scores.argmax(axis=1);gold=rows[:,-1];correct=pred==gold
                confusion=np.zeros((10,10),dtype=int);np.add.at(confusion,(gold,pred),1)
                result[split]={'n':len(gold),'correct':int(correct.sum()),'accuracy':float(correct.mean()),
                               'wilson_95':wilson(int(correct.sum()),len(gold)),'confusion':confusion.tolist(),
                               'per_class_accuracy':(np.diag(confusion)/confusion.sum(axis=1)).tolist()}
                predictions[split+'_pred']=pred;predictions[split+'_scores']=scores
            np.savez_compressed(out/'predictions.npz',**predictions)
    except (AssertionError,ValueError,TypeError,OverflowError) as exc:
        result['format_failure']=str(exc) or type(exc).__name__
        category='unreadable_format'
        terminal=[ev for ev in record.get('events',[]) if ev.get('type')=='result']
        finish=[c.get('finish_reason') for ev in record.get('events',[]) for c in ev.get('choices',[]) if c.get('finish_reason')]
        if terminal and terminal[-1].get('safety_stops') and record.get('answer','').strip():category='refusal'
        elif terminal and terminal[-1].get('subtype')=='error_max_budget_usd':category='budget_or_output_stop'
        elif 'length' in finish or (record.get('error') or {}).get('finish_reason')=='length':category='output_limit'
        elif record.get('error'):category='provider_or_transport_failure'
        elif not record.get('completed'):category='incomplete_response'
        elif result['format_failure'].startswith('Expected 6570 weights'):category='wrong_weight_count'
        result['failure_category']=category
    dump(out/'results.json',result)
    dump(out/'status.json',{'status':'scored' if result['format_failure'] is None else 'unreadable','finished_utc':utc(),'format_failure':result['format_failure']})
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','collect','score']);parser.add_argument('--models',nargs='+',default=['astra'],choices=list(MODELS));parser.add_argument('--max-new-calls',type=int,default=MAX_NEW_CALLS)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='collect':
        assert len(args.models)<=args.max_new_calls,'Explicit fresh-call cap required'
        with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
            tasks={pool.submit(collect_one,key):key for key in args.models}
            for task in as_completed(tasks):
                try:task.result()
                except Exception as exc:print(json.dumps({'model':tasks[task],'error':str(exc)}),flush=True)
    else:
        for key in args.models:
            path=DATA/'responses'/key/'response.json'
            if path.exists():print(json.dumps(validate_and_score(key,json.loads(path.read_text(encoding='utf-8')))),flush=True)
