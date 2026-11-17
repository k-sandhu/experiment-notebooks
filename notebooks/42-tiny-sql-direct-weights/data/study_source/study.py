"""Exploratory weight diagnostics and fixed-checkpoint decoding experiments. No optimizer or weight editing."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import logging
import math
import platform
from pathlib import Path
import sys
import time
import numpy as np
import torch
from safetensors.torch import load_file
from scipy.optimize import linprog
import sqlglot
from sqlglot import exp
logging.getLogger('sqlglot').setLevel(logging.CRITICAL)
from transformers import RepetitionPenaltyLogitsProcessor, NoRepeatNGramLogitsProcessor, SuppressTokensLogitsProcessor
from transformers import TopPLogitsWarper, TemperatureLogitsWarper

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
SQL=BASE/'tiny-sql-2208'
MLP=BASE/'mlp-rings-388'
CHECKPOINT=SQL/'round-03-astra'/'attempt-02'/'astra_candidate.safetensors'
sys.path.insert(0,str(SQL))
from model_and_test import load_model,vocabulary,encode,decode,schema_prompt
from trace_calls import trace
torch.set_num_threads(1)
DATA=ROOT/'data'
FIGURES=ROOT/'figures'
DATA.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)
CASES=json.loads((SQL/'generation_inputs.json').read_text(encoding='utf-8'))
VOCAB=vocabulary()
INVERSE={i:t for t,i in VOCAB.items()}
CHECKPOINT_HASH=hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def basic(a):
    a=np.asarray(a,dtype=np.float64)
    v=a.ravel();nz=np.abs(v[v!=0]);s=np.linalg.svd(a,compute_uv=False) if a.ndim==2 else None
    result={'n':v.size,'shape':list(a.shape),'zeros':int((v==0).sum()),'zero_fraction':float((v==0).mean()),
            'unique_values':len(np.unique(v)),'mean':float(v.mean()),'std':float(v.std()),'rms':float(np.sqrt(np.mean(v*v))),
            'min':float(v.min()),'max':float(v.max()),'max_abs':float(np.abs(v).max()),
            'min_abs_nonzero':float(nz.min()) if len(nz) else None}
    if s is not None:
        w=s/s.sum() if s.sum() else s
        result.update({'rank_numeric':int(np.linalg.matrix_rank(a)),'rank_relative_1e_8':int((s>s[0]*1e-8).sum()) if s[0] else 0,
                       'singular_values':s.tolist(),'stable_rank':float(np.sum(s*s)/(s[0]*s[0])) if s[0] else 0,
                       'effective_rank':float(np.exp(-np.sum(w[w>0]*np.log(w[w>0])))) if w.sum() else 0})
    return result


def manual_forward(model,ids):
    p=dict(model.named_parameters())
    f=model.frozen_embeddings@p['projection']
    x=f[ids]+p['transformer.wpe.weight'][:len(ids)]
    def ln(y,prefix):
        c=y-y.mean(-1,keepdim=True)
        return c/torch.sqrt((c*c).mean(-1,keepdim=True)+1e-5)*p[prefix+'.weight']+p[prefix+'.bias']
    a=ln(x,'transformer.h.0.ln_1')
    q,k,v=(a@p['transformer.h.0.attn.c_attn.weight']+p['transformer.h.0.attn.c_attn.bias']).split(8,dim=-1)
    q,k,v=[t.reshape(len(ids),2,4).transpose(0,1) for t in (q,k,v)]
    scores=q@k.transpose(-1,-2)/2
    mask=torch.ones(len(ids),len(ids),dtype=torch.bool).triu(1)
    attention=scores.masked_fill(mask,float('-inf')).softmax(-1)
    c=(attention@v).transpose(0,1).reshape(len(ids),8)
    x=x+c@p['transformer.h.0.attn.c_proj.weight']+p['transformer.h.0.attn.c_proj.bias']
    a=ln(x,'transformer.h.0.ln_2')
    a=a@p['transformer.h.0.mlp.c_fc.weight']+p['transformer.h.0.mlp.c_fc.bias']
    a=.5*a*(1+torch.tanh(math.sqrt(2/math.pi)*(a+.044715*a**3)))
    x=x+a@p['transformer.h.0.mlp.c_proj.weight']+p['transformer.h.0.mlp.c_proj.bias']
    h=ln(x,'transformer.ln_f')
    return h@f.T,attention


def desired(case):
    return 'select '+','.join('"'+c+'"' for c in case['columns'])+' from "'+case['table']+'";'


def diagnostics():
    start=time.monotonic()
    m=load_model(CHECKPOINT)
    state=load_file(str(CHECKPOINT))
    weights={k:v.numpy() for k,v in state.items() if k!='frozen_embeddings'}
    mlp_file=np.load(MLP/'data'/'astra'/'candidate.npz')
    mlp={k:mlp_file[k] for k in mlp_file.files}
    reference=load_file(str(DATA/'reference'/'model.safetensors'))
    ref_core={k:v.double().numpy() for k,v in reference.items() if 'embed_' not in k}
    stats={label:{k:basic(v) for k,v in values.items()} for label,values in [('sql',weights),('mlp',mlp),('reference_core',ref_core)]}
    stats['summary']={label:basic(np.concatenate([v.ravel() for v in values.values()])) for label,values in [('sql',weights),('mlp',mlp),('reference_core',ref_core)]}
    dump(DATA/'weight_stats.json',stats)
    parity=[];first=[];attention_records=[]
    f=state['frozen_embeddings'].numpy()@weights['projection']
    ef=f/np.max(np.abs(f))
    with torch.inference_mode():
        for case in CASES[:16]:
            ids=encode(schema_prompt(case['table'],case['columns']),VOCAB)
            z=m(torch.tensor([ids]))[0]
            manual,a=manual_forward(m,ids)
            delta=(z-manual).abs()
            # Scale-free comparison is necessary because logits are exceptionally small.
            rel=float(delta.max()/z.abs().max().clamp_min(1e-300))
            parity.append({'case_id':case['id'],'max_abs_difference':float(delta.max()),'max_relative_to_logit_max':rel})
            assert rel<1e-6,'Reference equations disagree with GPT2 scaffold'
            logits=z[-1];prob=logits.softmax(-1);idx=logits.argsort(descending=True)[:12]
            first.append({'case':case,'min_logit':float(logits.min()),'max_logit':float(logits.max()),
                          'std_logit':float(logits.std()),'entropy_nats':float(-(prob*prob.log()).sum()),
                          'max_probability':float(prob.max()),'uniform_probability':1/len(VOCAB),
                          'top_tokens':[{'token':INVERSE[int(i)],'id':int(i),'logit':float(logits[i])} for i in idx]})
            for head in range(2):
                last=a[head,-1].numpy();ent=float(-(last[last>0]*np.log(last[last>0])).sum())
                attention_records.append({'case_id':case['id'],'head':head,'entropy_nats':ent,
                                          'prompt_tokens':[INVERSE[i] for i in ids],'attention_from_last_position':last.tolist(),
                                          'max_attention':float(last.max())})
    dump(DATA/'parity.json',parity)
    dump(DATA/'first_token_logits.json',first)
    dump(DATA/'attention.json',attention_records)
    gamma=state['transformer.ln_f.weight'].numpy();beta=state['transformer.ln_f.bias'].numpy()
    hidden_bound=float(np.max(np.abs(gamma))*math.sqrt(8)+np.linalg.norm(beta))
    max_f_norm=float(np.linalg.norm(f,axis=1).max())
    dump(DATA/'logit_scale_bound.json',{'final_hidden_l2_upper_bound':hidden_bound,
                                       'max_effective_embedding_l2_norm':max_f_norm,
                                       'absolute_logit_upper_bound':hidden_bound*max_f_norm,
                                       'float64_machine_epsilon':float(np.finfo(np.float64).eps),
                                       'derivation':'LayerNorm normalized input has L2 norm less than sqrt(8); use max(abs(gamma))*sqrt(8)+norm(beta), then Cauchy-Schwarz with each output embedding.'})
    cast={}
    for label,values in [('sql',weights),('mlp',mlp)]:
        v=torch.from_numpy(np.concatenate([a.ravel() for a in values.values()]))
        low=v.half()
        cast[label]={'total_values':v.numel(),'nonfinite_in_float16':int((~torch.isfinite(low)).sum()),
                     'nonzero_values_rounded_to_zero_in_float16':int(((v!=0)&(low==0)).sum())}
    dump(DATA/'float16_representability.json',cast)
    # Numeric geometry probe: maximize the minimum token advantage over all alternatives,
    # for zero-mean hidden directions in a bounded box. This is not an exact reachability proof.
    geometry=[]
    terms=list(dict.fromkeys(['select','from','"',',',';',' ','<EOS>']+[name for c in CASES[:16] for name in [c['table'],*c['columns']]]))
    for term in terms:
        if term not in VOCAB:continue
        i=VOCAB[term];others=np.arange(len(VOCAB))!=i
        difference=ef[others]-ef[i]
        aub=np.column_stack([difference,np.ones(len(difference))])
        obj=np.zeros(9);obj[-1]=-1
        equality=np.zeros((1,9));equality[0,:8]=1
        lp=linprog(obj,A_ub=aub,b_ub=np.zeros(len(difference)),A_eq=equality,b_eq=[0],
                   bounds=[(-math.sqrt(8),math.sqrt(8))]*8+[(None,None)],method='highs')
        geometry.append({'token':term,'id':i,'lp_success':bool(lp.success),
                         'maximum_scaled_margin':float(lp.x[-1]) if lp.success else None,
                         'positive_margin_at_1e_8':bool(lp.success and lp.x[-1]>1e-8),
                         'effective_embedding_norm':float(np.linalg.norm(f[i]))})
    dump(DATA/'output_geometry.json',{'method':'Max-margin numerical probe on globally rescaled effective embeddings, zero-mean bounded hidden direction; necessary geometry diagnostic, not an exact floating-point impossibility certificate.',
                                    'effective_embedding_rank':int(np.linalg.matrix_rank(f)),'tokens':geometry})
    # Correct-query likelihood uses teacher forcing; it is diagnostic, not generation accuracy.
    forced=[]
    with torch.inference_mode():
        for case in CASES:
            prefix=encode(schema_prompt(case['table'],case['columns']),VOCAB)
            target=encode(desired(case),VOCAB)+[VOCAB['<EOS>']]
            ids=prefix+target[:-1]
            if len(ids)>64:continue
            z=m(torch.tensor([ids]))[0,len(prefix)-1:]
            for step,token in enumerate(target):
                scores=z[step];lp=scores.log_softmax(-1)
                forced.append({'case_id':case['id'],'step':step,'expected_token':INVERSE[token],
                               'rank':int((scores>scores[token]).sum())+1,'probability':float(lp[token].exp()),
                               'log_probability':float(lp[token]),'top_token':INVERSE[int(scores.argmax())]})
    dump(DATA/'teacher_forced_tokens.json',forced)
    # Float32 is a numerical portability diagnostic; original candidate files remain unchanged.
    m32=load_model(CHECKPOINT).float()
    precision=[]
    with torch.inference_mode():
        for case in CASES[:16]:
            prefix=encode(schema_prompt(case['table'],case['columns']),VOCAB)
            outs=[]
            for model in [m,m32]:
                ids=list(prefix);new=[];eos=False;finite=True
                for _ in range(min(32,64-len(ids))):
                    z=model(torch.tensor([ids]))[0,-1]
                    if not torch.isfinite(z).all():finite=False;break
                    token=int(z.argmax())
                    if token==VOCAB['<EOS>']:eos=True;break
                    new.append(token);ids.append(token)
                outs.append({'output':decode(new,VOCAB),'ids':new,'eos':eos,'finite':finite})
            precision.append({'case':case,'float64':outs[0],'float32':outs[1],'identical_ids':outs[0]['ids']==outs[1]['ids']})
    dump(DATA/'precision.json',precision)
    # Successful MLP: quantify its one-dimensional radial feature and output thresholds.
    theta=np.linspace(0,2*np.pi,36000,endpoint=False)
    circle=np.column_stack([np.cos(theta),np.sin(theta)])
    h1=np.maximum(0,circle@mlp['W1'].T+mlp['b1'])
    h2=np.maximum(0,h1@mlp['W2'].T+mlp['b2'])
    radial=h2@mlp['W3'][1]
    row_error=max(float(np.max(np.abs(mlp['W3'][k]-k*mlp['W3'][1]))) for k in range(4))
    structure={'hidden_biases_all_zero':bool(np.all(mlp['b1']==0) and np.all(mlp['b2']==0)),
               'W1_row_norms':np.linalg.norm(mlp['W1'],axis=1).tolist(),'W1_directions_degrees':np.degrees(np.arctan2(mlp['W1'][:,1],mlp['W1'][:,0])).tolist(),
               'W2_rank':int(np.linalg.matrix_rank(mlp['W2'])),'W3_rank':int(np.linalg.matrix_rank(mlp['W3'])),
               'maximum_residual_from_W3_row_k_equals_k_times_row1':row_error,
               'b3':mlp['b3'].tolist(),'radial_feature_thresholds':(mlp['b3'][:-1]-mlp['b3'][1:]).tolist(),
               'unit_circle_angular_samples':len(theta),'radial_feature_min':float(radial.min()),'radial_feature_max':float(radial.max()),
               'radial_feature_max_absolute_error':float(np.abs(radial-1).max()),
               'note':'Output scores are approximately k*radial_feature+b3[k]. Zero hidden biases make the radial feature positively homogeneous.'}
    dump(DATA/'mlp_structure.json',structure)
    dump(DATA/'environment.json',{'python':sys.version,'platform':platform.platform(),'torch_threads':1,
                                 'packages':{p:importlib.metadata.version(p) for p in ['torch','numpy','scipy','matplotlib','sqlglot','transformers','safetensors']},
                                 'checkpoint_sha256':CHECKPOINT_HASH,'diagnostic_wall_seconds':time.monotonic()-start})
    print(json.dumps({'stage':'diagnostics_complete','sql_stats':stats['summary']['sql'],'mlp_structure':structure,
                      'first_logits':first[0],'positive_geometry_tokens':[x['token'] for x in geometry if x['positive_margin_at_1e_8']]},indent=2),flush=True)


def score_text(text,case):
    result={'parseable_select':False,'schema_match':False,'parse_error':None,'tables':None,'columns':None}
    try:
        nodes=sqlglot.parse(text,read='sqlite',error_level=sqlglot.ErrorLevel.RAISE)
        assert len(nodes)==1 and isinstance(nodes[0],exp.Select),'Not one SELECT statement'
        node=nodes[0];result['parseable_select']=True
        tables=[t.name for t in node.find_all(exp.Table)]
        columns=[c.name if isinstance(c,exp.Column) else None for c in node.expressions]
        result.update(tables=tables,columns=columns)
        # A conservative AST match for the specified simple projection task; no SQL execution.
        prohibited=any(node.args.get(k) for k in ['where','group','having','qualify','order','limit','offset','joins','distinct'])
        result['schema_match']=bool(tables==[case['table']] and columns==case['columns'] and not prohibited
                                    and all(isinstance(c,exp.Column) and not c.table for c in node.expressions))
    except (sqlglot.errors.SqlglotError,AssertionError,ValueError) as exc:
        result['parse_error']=str(exc).splitlines()[0][:250] or type(exc).__name__
    return result


def processors(config):
    result=[]
    if config.get('suppress_special'):
        result.append(SuppressTokensLogitsProcessor([i for token,i in VOCAB.items() if token.startswith('<') and token.endswith('>') and token!='<EOS>']))
    if config.get('no_repeat_ngram'):
        result.append(NoRepeatNGramLogitsProcessor(config['no_repeat_ngram']))
    return result


def processed(ids,z,config,prompt_length):
    scores=z[None].clone()
    ids_tensor=torch.tensor([ids])
    if config.get('repetition_penalty'):
        used=ids[prompt_length:] if config.get('generated_only_penalty') else ids
        if used:scores=RepetitionPenaltyLogitsProcessor(config['repetition_penalty'])(torch.tensor([used]),scores)
    for proc in processors(config):scores=proc(ids_tensor,scores)
    return scores[0]


def generate_one(m,case,config,seed=0):
    prefix=encode(schema_prompt(case['table'],case['columns']),VOCAB)
    if config.get('beam'):
        # Four-beam search on explicitly normalized log-probabilities. No grammar or schema mask.
        beams=[(list(prefix),[],0.,False)]
        with torch.inference_mode():
            for step in range(min(32,64-len(prefix))):
                candidates=[]
                for ids,new,score,done in beams:
                    if done:candidates.append((ids,new,score,done));continue
                    z=m(torch.tensor([ids]))[0,-1]
                    z=processed(ids,z,config,len(prefix))
                    gain=config.get('logit_gain',1.)
                    lp=(z*gain).log_softmax(-1)
                    vals,indices=lp.topk(config['beam'])
                    for val,token in zip(vals.tolist(),indices.tolist()):
                        stop=token==VOCAB['<EOS>']
                        candidates.append((ids+[token],new+([] if stop else [token]),score+val,stop))
                candidates.sort(key=lambda x:x[2]/max(1,len(x[1]))**1.,reverse=True)
                beams=candidates[:config['beam']]
                if all(x[3] for x in beams):break
        ids,new,score,done=beams[0]
        return new,done,[]
    ids=list(prefix);new=[];eos=False;steps=[]
    rng=torch.Generator().manual_seed(seed)
    with torch.inference_mode():
        for step in range(min(32,64-len(prefix))):
            z=m(torch.tensor([ids]))[0,-1]
            if not torch.isfinite(z).all():raise ValueError('Non-finite logits')
            scores=processed(ids,z,config,len(prefix))*config.get('logit_gain',1.)
            if config.get('sample'):
                scores=TemperatureLogitsWarper(config['temperature'])(torch.tensor([ids]),scores[None])
                scores=TopPLogitsWarper(config['top_p'])(torch.tensor([ids]),scores)[0]
                token=int(torch.multinomial(scores.softmax(-1),1,generator=rng))
            else:token=int(scores.argmax())
            steps.append({'step':step+1,'token_id':token,'token':INVERSE[token],
                          'raw_logit_std':float(z.std()),'raw_top_probability':float(z.softmax(-1).max())})
            if token==VOCAB['<EOS>']:eos=True;break
            new.append(token);ids.append(token)
    return new,eos,steps


def decoding():
    m=load_model(CHECKPOINT)
    logit_std=json.loads((DATA/'first_token_logits.json').read_text())[0]['std_logit']
    gain=1/logit_std
    configs=[{'name':'greedy'},
             {'name':'greedy_trim_stop','cleanup':True},
             {'name':'suppress_special','suppress_special':True},
             {'name':'repetition_1.2','suppress_special':True,'repetition_penalty':1.2},
             {'name':'repetition_generated_only','suppress_special':True,'repetition_penalty':1.2,'generated_only_penalty':True},
             {'name':'no_repeat_trigram','suppress_special':True,'no_repeat_ngram':3},
             {'name':'combined','suppress_special':True,'repetition_penalty':1.2,'no_repeat_ngram':3},
             {'name':'sample_standard','suppress_special':True,'sample':True,'temperature':.7,'top_p':.9,'seeds':[0,1,2]},
             {'name':'beam4_standard','suppress_special':True,'beam':4,'no_repeat_ngram':3},
             {'name':'sample_calibrated_DIAGNOSTIC','suppress_special':True,'sample':True,'temperature':.7,'top_p':.9,'logit_gain':gain,'seeds':[0,1,2]},
             {'name':'beam4_calibrated_DIAGNOSTIC','suppress_special':True,'beam':4,'no_repeat_ngram':3,'logit_gain':gain}]
    dump(DATA/'decoder_protocol.json',{'study_type':'Exploratory, fixed-checkpoint diagnostic; existing outputs were inspected before these conditions were chosen.',
                                     'conditions_fixed_before_sweep':configs,'n_schemas':len(CASES),'max_new_tokens':32,'context_limit':64,
                                     'scoring':'SQLGlot SQLite parse + conservative AST schema match. No database or query execution.',
                                     'calibration':'Diagnostic gain is inverse first-prompt logit standard deviation; no task-score tuning and no weights changed.',
                                     'extra_fresh_model_calls':0,'checkpoint_sha256':CHECKPOINT_HASH})
    cache=DATA/'generations';cache.mkdir(exist_ok=True)
    baseline_known=json.loads((SQL/'round-03-astra'/'attempt-02'/'raw_outputs.json').read_text())['outputs']
    baseline_known={x['case']['id']:x for x in baseline_known}
    records=[];summary=[];baseline_cache={}
    for config in configs:
        group=[]
        for seed in config.get('seeds',[0]):
            for index,case in enumerate(CASES):
                request={'model':'local/astra-sql-2208','checkpoint_sha256':CHECKPOINT_HASH,'prompt':schema_prompt(case['table'],case['columns']),
                         'decoding':config,'seed':seed,'max_new_tokens':32,'context_limit':64,'dtype':'float64','sql_execution':False}
                key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
                path=cache/(key+'.json')
                if path.exists():sample=json.loads(path.read_text(encoding='utf-8'))
                else:
                    start=dt.datetime.now(dt.timezone.utc)
                    if config.get('cleanup'):
                        original=baseline_cache[case['id']]
                        raw_ids,eos,steps=original['generated_ids'],original['eos'],original['steps']
                    else:
                        raw_ids,eos,steps=generate_one(m,case,config,seed)
                    raw=decode(raw_ids,VOCAB)
                    text=raw
                    if config.get('cleanup'):
                        text=text.strip()
                        if ';' in text:text=text[:text.index(';')+1]
                    sample={'case':case,'request':request,'cache_key':key,'generated_ids':raw_ids,'raw_output':raw,
                            'scored_output':text,'eos':eos,'steps':steps,'score':score_text(text,case)}
                    dump(path,sample)
                    if not config.get('cleanup'):
                        trace(key,'local/astra-sql-2208',request,raw,start,dt.datetime.now(dt.timezone.utc),{'input':len(encode(request['prompt'],VOCAB)),'output':len(raw_ids)})
                if config['name']=='greedy' and case['id'] in baseline_known:
                    assert sample['raw_output']==baseline_known[case['id']]['raw_output'],'Greedy replay changed original output'
                if config['name']=='greedy':baseline_cache[case['id']]=sample
                group.append(sample);records.append(sample)
                if (index+1)%40==0:print(json.dumps({'condition':config['name'],'seed':seed,'completed_cases':index+1,'total_cases':len(CASES)}),flush=True)
        readable=sum(x['score']['parseable_select'] for x in group)
        correct=sum(x['score']['schema_match'] for x in group)
        n=len(group)
        counts={'condition':config['name'],'n_outputs':n,'n_schemas':len(CASES),'parseable_select':readable,
                'unreadable_sql':n-readable,'schema_match':correct,'wrong_readable':readable-correct,
                'schema_match_on_readable':correct/readable if readable else None,'eos':sum(x['eos'] for x in group),
                'adjacent_repeated_tokens':sum(sum(a==b for a,b in zip(x['generated_ids'],x['generated_ids'][1:])) for x in group),
                'examples':[{'case':x['case'],'output':x['scored_output'],'score':x['score']} for x in group[:3]]}
        summary.append(counts)
        dump(DATA/'decoding_summary.json',summary)
        print(json.dumps({k:v for k,v in counts.items() if k!='examples'}),flush=True)
    dump(DATA/'all_generations.json',records)
    assert hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()==CHECKPOINT_HASH


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['diagnostics','decoding']);a=p.parse_args()
    {'diagnostics':diagnostics,'decoding':decoding}[a.action]()
