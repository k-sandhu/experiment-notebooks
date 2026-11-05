"""Read archived teacher weights, replay inference, and score text without a database."""
from pathlib import Path
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sqlglot
from sqlglot import exp

ROOT=Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA=ROOT/'data';HISTORY=DATA/'history';FIGURES=ROOT/'figures'
plt.rcParams.update({'font.size':10,'figure.dpi':130,'savefig.dpi':160,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white'})

def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def write_json(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def score_sql(text,case):
    result={'parseable_select':False,'schema_match':False,'parse_error':None}
    try:
        nodes=sqlglot.parse(text,read='sqlite',error_level=sqlglot.ErrorLevel.RAISE)
        assert len(nodes)==1 and isinstance(nodes[0],exp.Select),'Not one SELECT statement'
        node=nodes[0];result['parseable_select']=True
        tables=[t.name for t in node.find_all(exp.Table)]
        columns=[c.name if isinstance(c,exp.Column) else None for c in node.expressions]
        prohibited=any(node.args.get(k) for k in ['where','group','having','qualify','order','limit','offset','joins','distinct'])
        result['schema_match']=bool(tables==[case['table']] and columns==case['columns'] and not prohibited
                                   and all(isinstance(c,exp.Column) and not c.table for c in node.expressions))
    except (sqlglot.errors.SqlglotError,AssertionError,ValueError) as exc:result['parse_error']=str(exc).splitlines()[0][:200]
    return result

def tensors_from_response(folder):
    flat=np.asarray(read_json(folder/'generator_weights_output.json')['weights'],dtype=np.float64)
    assert flat.shape==(2208,) and np.isfinite(flat).all()
    arrays={};offset=0
    for item in read_json(HISTORY/'tensor_layout.json'):
        count=item['count'];arrays[item['name']]=flat[offset:offset+count].reshape(item['shape']);offset+=count
    assert offset==2208
    return arrays,flat

def layer_norm(x,gain,bias):
    centred=x-x.mean(axis=-1,keepdims=True)
    return centred/np.sqrt(np.mean(centred**2,axis=-1,keepdims=True)+1e-5)*gain+bias

def forward_logits(ids,arrays,embeddings):
    a=arrays;prefix='transformer.h.0.';f=embeddings@a['projection'];t=len(ids)
    x=f[ids]+a['transformer.wpe.weight'][:t]
    z=layer_norm(x,a[prefix+'ln_1.weight'],a[prefix+'ln_1.bias'])
    q,k,v=np.split(z@a[prefix+'attn.c_attn.weight']+a[prefix+'attn.c_attn.bias'],3,axis=-1)
    q,k,v=[m.reshape(t,2,4).transpose(1,0,2) for m in (q,k,v)]
    scores=(q@k.transpose(0,2,1))/2
    scores=np.where(np.tril(np.ones((t,t),dtype=bool))[None,:,:],scores,-np.inf)
    weights=np.exp(scores-np.max(scores,axis=-1,keepdims=True));weights/=weights.sum(axis=-1,keepdims=True)
    attention=(weights@v).transpose(1,0,2).reshape(t,8)
    x=x+attention@a[prefix+'attn.c_proj.weight']+a[prefix+'attn.c_proj.bias']
    z=layer_norm(x,a[prefix+'ln_2.weight'],a[prefix+'ln_2.bias'])
    z=z@a[prefix+'mlp.c_fc.weight']+a[prefix+'mlp.c_fc.bias']
    z=.5*z*(1+np.tanh(np.sqrt(2/np.pi)*(z+.044715*z**3)))
    x=x+z@a[prefix+'mlp.c_proj.weight']+a[prefix+'mlp.c_proj.bias']
    h=layer_norm(x,a['transformer.ln_f.weight'],a['transformer.ln_f.bias'])
    return h@f.T

def encode_prompt(text,vocab):
    ids=[]
    for piece in re.findall(r'<[A-Z_]+>|[A-Za-z]+|[0-9]+|\s|[^\w\s]|_',text):
        if piece in vocab:ids.append(vocab[piece])
        else:ids.extend(vocab.get(c,vocab['<UNK>']) for c in piece)
    return ids

def greedy_replay(folder,samples):
    a,flat=tensors_from_response(folder);embeddings=np.load(DATA/'frozen_embeddings.npz')['embeddings']
    vocab=read_json(HISTORY/'vocabulary.json');inverse={v:k for k,v in vocab.items()};rows=[]
    for sample in samples:
        ids=encode_prompt(sample['request']['prompt'],vocab);generated=[];eos=False
        for step in range(min(32,64-len(ids))):
            logits=forward_logits(ids,a,embeddings)[-1];assert np.isfinite(logits).all();token=int(logits.argmax())
            if token==vocab['<EOS>']:eos=True;break
            generated.append(token);ids.append(token)
        text=''.join(inverse[t] for t in generated)
        rows.append({'id':sample['case']['id'],'output':text,'matches_archived_output':text==sample['raw_output'],
                     'eos_matches_archive':eos==sample['terminated_with_eos']})
    return rows

def analyse():
    FIGURES.mkdir(exist_ok=True)
    control=read_json(DATA/'context/random10000/results.json')
    assert control['parameter_count']==10000 and sum(control['parameter_breakdown'].values())==10000
    assert control['training_steps']==0 and len(control['generated_token_ids'])==10
    entropy=[r['entropy_bits'] for r in control['trace']]
    fig,ax=plt.subplots(figsize=(9,3.8));ax.plot(range(1,11),entropy,'o-',color='#286f9e',label='Untrained 10,000-parameter model')
    ax.axhline(10,color='#777',linestyle='--',label='Uniform over 1,024 tokens')
    ax.set(xticks=range(1,11),xlabel='Generated token step',ylabel='Next-token entropy (bits)',ylim=(9.995,10.001),title='Random initialization gives almost uniform token scores')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIGURES/'initialization_control.png',bbox_inches='tight');plt.close(fig)
    folders=[('Sol initial',HISTORY),('Sol revision',HISTORY/'round-02/attempt-02'),
             ('Astra unbounded',HISTORY/'round-03-astra/attempt-02'),('Astra bounded',HISTORY/'round-04-astra-bounded'),
             ('Nemotron Super free',HISTORY/'round-05-nemotron-super-free')]
    results=[];examples=[];parity={}
    for name,folder in folders:
        raw=read_json(folder/'raw_outputs.json')['outputs'];arrays,flat=tensors_from_response(folder)
        scored=[score_sql(s['raw_output'],s['case']) for s in raw]
        row={'name':name,'n_cases':len(raw),'correct':sum(r['schema_match'] for r in scored),
             'parseable_selects':sum(r['parseable_select'] for r in scored),
             'unreadable_or_nonselect':sum(not r['parseable_select'] for r in scored),
             'wrong_readable':sum(r['parseable_select'] and not r['schema_match'] for r in scored),
             'eos':sum(s['terminated_with_eos'] for s in raw),'zeros':int(np.sum(flat==0)),
             'zero_percent':float(np.mean(flat==0)*100),'max_abs':float(np.abs(flat).max())}
        results.append(row)
        for sample in raw[:3]:examples.append({'submission':name,'case':sample['case'],'prompt':sample['request']['prompt'],
                                               'raw_output':sample['raw_output'],**score_sql(sample['raw_output'],sample['case'])})
        if name.startswith('Astra'):parity[name]=greedy_replay(folder,raw)
    decoding=read_json(DATA/'diagnostics/decoding_summary.json')
    fig,axes=plt.subplots(1,2,figsize=(11,4.8))
    labels=[r['name'].replace(' ','\n',1) for r in results]
    axes[0].bar(labels,[r['zero_percent'] for r in results],color='#477fa6');axes[0].set(ylabel='Exactly zero values (%)',ylim=(0,100),title='Bounded priors reduce sparsity')
    axes[1].bar(labels,[r['max_abs'] for r in results],color='#a86d3b');axes[1].set_yscale('log');axes[1].set(ylabel='Largest absolute parameter (log scale)',title='Extreme magnitudes disappear')
    fig.tight_layout();fig.savefig(FIGURES/'numerical_priors.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5));ys=np.arange(len(decoding));n=np.array([r['n_outputs'] for r in decoding]);parsed=np.array([r['parseable_select'] for r in decoding])
    ax.barh(ys,parsed/n*100,color='#447eaa',label='Readable SELECT, wrong schema')
    ax.barh(ys,(n-parsed)/n*100,left=parsed/n*100,color='#c8cfd5',label='Unreadable or not SELECT')
    ax.set(yticks=ys,yticklabels=[r['condition'] for r in decoding],xlabel='Generated outputs (%)',xlim=(0,100),title='No decoder condition produced the requested SQL')
    ax.invert_yaxis();ax.legend(loc='lower right',fontsize=8);fig.tight_layout();fig.savefig(FIGURES/'decoding_outcomes.png',bbox_inches='tight');plt.close(fig)
    prior=read_json(HISTORY/'round-04-astra-bounded/prior_adherence.json')
    report={'submissions':results,'worked_examples':examples,'decoding':decoding,'numpy_replay':parity,
            'numpy_exact_matches':{k:sum(r['matches_archived_output'] for r in v) for k,v in parity.items()},
            'bounded_priors_pass':prior['passes_hard_constraints'],'bounded_prior_violations':prior['violations'],
            'sql_execution':False,'teacher_calls_in_replay':0,'all_decoding_outputs':sum(r['n_outputs'] for r in decoding)}
    write_json(DATA/'replay_summary.json',report)
    return report

if __name__=='__main__':
    r=analyse();print(json.dumps({'submissions':r['submissions'],'numpy_exact_matches':r['numpy_exact_matches'],'decoding_outputs':r['all_decoding_outputs']},indent=2))
