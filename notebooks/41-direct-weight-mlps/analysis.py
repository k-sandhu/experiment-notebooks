"""Cache-only figures and measurements. No teacher calls and no candidate fitting."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA = ROOT/'data'
FIGURES = ROOT/'figures'
MODEL_LABELS = {'astra':'Astra','sol':'Sol','opus':'Opus 5.5','muse':'Muse Wonder','nemotron':'Nemotron','gemini':'Gemini batch',
                'sonnet':'Sonnet 5.5','haiku':'Haiku 5.5','fable':'Fable 5.1','deepseek':'DeepSeek V4.1 Flash','glm':'GLM-5.3','mimo':'MiMo-V2.6-Pro'}
OPEN_KEYS = ['deepseek','glm','mimo']
FAMILY_LABELS = {'fable':'Fable 5.1','opus':'Opus 5.5 high','sonnet':'Sonnet 5.5','haiku':'Haiku 5.5'}
plt.rcParams.update({'figure.dpi':130,'savefig.dpi':160,'font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.titleweight':'bold','axes.labelsize':10,
                     'figure.facecolor':'white','axes.facecolor':'white'})

def save_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def live_reasoning_logs():
    """Only text the external provider actually emitted. Never infer hidden reasoning."""
    folders=[(key,DATA/'responses'/key) for key in MODEL_LABELS]+[(key,DATA/'claude_family'/key) for key in FAMILY_LABELS]
    for key,folder in folders:
        events_path=folder/'events.jsonl'
        if not events_path.exists():continue
        events=[]
        for line in events_path.read_text(encoding='utf-8').splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
        if key in FAMILY_LABELS:
            chunks=[e.get('event',{}).get('delta',{}).get('thinking','') for e in events
                    if e.get('event',{}).get('delta',{}).get('type')=='thinking_delta']
            full=[b.get('thinking','') for e in events if e.get('type')=='assistant'
                  for b in e.get('message',{}).get('content',[]) if b.get('type')=='thinking' and b.get('thinking','').strip()]
            (folder/'reasoning.txt').write_text('\n'.join(full) if full else ''.join(chunks),encoding='utf-8')
        elif key=='muse':
            chunks=[]
            for e in events:
                p=e.get('payload',{});kind=e.get('payload_type','')
                if 'reasoning' in kind or 'thinking' in kind:
                    value=p.get('text') or p.get('delta')
                    if isinstance(value,str):chunks.append(value)
            if chunks:(folder/'reasoning.txt').write_text(''.join(chunks),encoding='utf-8')

def collect_results():
    results=[]
    for key in ['astra','sol','opus','muse','nemotron','gemini']:
        label=MODEL_LABELS[key];folder=DATA/'responses'/key;path=folder/'results.json'
        result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
        result['label']=label
        result['candidate_folder']=str(folder.relative_to(DATA))
        rp=folder/'reasoning.txt';result['reasoning_characters']=len(rp.read_text(encoding='utf-8')) if rp.exists() else 0
        results.append(result)
    for key,label in FAMILY_LABELS.items():
        folder=DATA/'claude_family'/key;path=folder/'results.json'
        if not folder.exists():continue
        result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
        result['label']=label;result['family']=True
        result['candidate_folder']=str(folder.relative_to(DATA))
        rp=folder/'reasoning.txt';result['reasoning_characters']=len(rp.read_text(encoding='utf-8').strip()) if rp.exists() else 0
        results.append(result)
    for key in OPEN_KEYS:
        folder=DATA/'open_models'/key;path=folder/'results.json'
        if not folder.exists():continue
        result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
        result['label']=MODEL_LABELS[key];result['open']=True
        result['candidate_folder']=str(folder.relative_to(DATA));result['outer_requests']=len(list(folder.glob('call-*/response.json')))
        rp=folder/'reasoning.txt';result['reasoning_characters']=len(rp.read_text(encoding='utf-8').strip()) if rp.exists() else 0
        results.append(result)
    for recovery_key in ['opus','gemini','gemini-low']:
        key=recovery_key.split('-')[0];folder=DATA/'recovery'/recovery_key
        if not folder.exists():continue
        path=folder/'results.json'
        result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
        result['label']=MODEL_LABELS[key]+(' continuation' if key=='opus' else (' low effort' if recovery_key=='gemini-low' else ' schema retry'))
        result['candidate_folder']=str(folder.relative_to(DATA));result['recovery']=True
        rp=folder/'reasoning.txt';result['reasoning_characters']=len(rp.read_text(encoding='utf-8').strip()) if rp.exists() else 0
        results.append(result)
    indexed_root=DATA/'indexed'
    if indexed_root.exists():
        order=['gemini','nemotron','fable','opus','sonnet','haiku']
        for folder in sorted(indexed_root.iterdir(),key=lambda f:order.index(f.name) if f.name in order else len(order)):
            if not folder.is_dir() or folder.name not in MODEL_LABELS:continue
            key=folder.name;path=folder/'results.json'
            result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
            result['label']=MODEL_LABELS[key]+(' high' if key=='opus' else '')+' numbered entries';result['indexed']=True
            result['candidate_folder']=str(folder.relative_to(DATA));result['outer_requests']=len(list(folder.glob('turn-*/response.json')))
            result['reasoning_characters']=len((folder/'reasoning.txt').read_text(encoding='utf-8').strip()) if (folder/'reasoning.txt').exists() else 0
            results.append(result)
    return results

def nearest_neighbour_baseline(dataset):
    visible=dataset['visible'];x=visible[:,:64].astype(float)/16;labels=visible[:,-1]
    metrics={};predictions={}
    for split in ['hidden_train','test']:
        z=dataset[split][:,:64].astype(float)/16;pred=[]
        for i in range(0,len(z),128):
            batch=z[i:i+128];distance=(batch**2).sum(1)[:,None]+(x**2).sum(1)[None,:]-2*batch@x.T
            pred.extend(labels[np.argmin(distance,axis=1)])
        pred=np.asarray(pred);gold=dataset[split][:,-1];predictions[split]=pred
        metrics[split]={'n':len(gold),'correct':int(np.sum(gold==pred)),'accuracy':float(np.mean(gold==pred))}
    np.savez_compressed(DATA/'nearest_neighbour_predictions.npz',**predictions)
    save_json(DATA/'nearest_neighbour_baseline.json',metrics)
    return metrics

def verify_legacy_mlps():
    results=[];legacy=DATA/'legacy'
    points=np.load(legacy/'mlp17/data/evaluation_points.npz')
    for name in ['astra','nemotron-no-reasoning']:
        folder=legacy/'mlp17/data'/name
        if not (folder/'classification.npz').exists():continue
        row={'model':name,'parameters':17}
        for task in ['classification','regression']:
            with np.load(folder/(task+'.npz')) as w:
                x=points[task+'_x'];scores=np.maximum(x@w['W1'].T+w['b1'],0)@w['W2']+w['b2'][0]
            gold=points[task+'_y'];row[task+'_n']=len(gold)
            if task=='classification':row['correct']=int(np.sum((scores>0)==gold));row['accuracy']=float(np.mean((scores>0)==gold))
            else:row['regression_mae']=float(np.mean(np.abs(scores-gold)))
        results.append(row)
    points.close()
    with np.load(legacy/'rings388/data/test_points.npz') as points:
        for name in ['astra','nemotron-free']:
            with np.load(legacy/'rings388/data'/name/'candidate.npz') as w:
                x=points['x'];h1=np.maximum(x@w['W1'].T+w['b1'],0);h2=np.maximum(h1@w['W2'].T+w['b2'],0)
                pred=(h2@w['W3'].T+w['b3']).argmax(axis=1);gold=points['y']
            expected_path=legacy/'rings388/data'/name/'results.json'
            if not expected_path.exists():expected_path=legacy/'rings388/results.json'
            expected=json.loads(expected_path.read_text())
            correct=int(np.sum(pred==gold));assert correct==expected['correct']
            results.append({'model':name,'parameters':388,'classification_n':len(gold),'correct':correct,'accuracy':float(np.mean(pred==gold))})
    save_json(DATA/'legacy_replay.json',results)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,size,chance,title in zip(axes,[17,388],[50,25],['Known opposite-sign rule','Known four-ring rule']):
        subset=[r for r in results if r['parameters']==size]
        ax.bar([r['model'].replace('nemotron-no-reasoning','Nemotron\nreasoning off').replace('nemotron-free','Nemotron free').replace('astra','Astra') for r in subset],
               [100*r['accuracy'] for r in subset],color=['#286f9e','#7f9a61'])
        ax.axhline(chance,color='#777',linestyle='--');ax.set(ylim=(0,110),ylabel='Cases classified correctly (%)',title=f'{size} parameters: {title}')
        for j,r in enumerate(subset):ax.text(j,100*r['accuracy']+3,f"{r['correct']:,}/{r['classification_n']:,}",ha='center',fontsize=9)
    fig.tight_layout();fig.savefig(FIGURES/'legacy_accuracy.png',bbox_inches='tight');plt.close(fig)
    return results

GROUPS = ['First request to each model','Claude models at high effort','Open-weight models, numbered from the start','Retries after a failed first reply']
BLUE,GREY,BROWN,INK = '#286f9e','#9aa3ad','#b7752c','#172e40'
AXIS_CAP = 200000  # Haiku's flat reply (256,483 tokens) is drawn cut at this axis limit and labelled.

def workflow_group(r):
    if r.get('family'):return GROUPS[1]
    if r.get('open'):return GROUPS[2]
    if r.get('recovery') or r.get('indexed'):return GROUPS[3]
    return GROUPS[0]

def failure_note(r):
    """Short reason for a submission that produced no scored network."""
    if r.get('pending'):return 'Still running'
    cat=r.get('failure_category');text=r.get('format_failure') or ''
    if r['model_key']=='gemini' and workflow_group(r)==GROUPS[0]:return 'No weights: provider rejected the output schema'
    if r['model_key']=='haiku' and r.get('family'):return 'No weights: two runs of zeros hit the output cap, then a note'
    if cat=='declined':return 'No weights: declined to write untested weights'
    if cat=='wrong_weight_count':
        m=re.search(r'received (\d+)',text)
        return f'Wrong count: {int(m.group(1)):,} of 6,570 values' if m else 'Wrong number of values'
    return {'budget_or_output_stop':'No weights: reasoning used the whole output allowance',
            'refusal':'No weights: refusal','output_limit':'No weights: output limit reached during reasoning',
            'provider_unavailable':'No weights: three provider timeouts','provider_or_transport_failure':'No weights: provider error',
            'incomplete_response':'No weights: incomplete response','unreadable_format':'Reply did not parse as the JSON contract'}.get(cat,'No usable network')

def ordered_rows(results):
    return [r for g in GROUPS for r in results if workflow_group(r)==g]

def usage_row(r):
    """Native token counters, wall time and reported cost for one submission, without estimating missing values."""
    folder=DATA/r['candidate_folder'];p=folder/'response.json'
    if r.get('indexed') or r.get('open'):p=folder/('assembled_response.json' if (folder/'assembled_response.json').exists() else 'workflow_summary.json')
    native=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    usage=native.get('usage') or {};backend=((native.get('request') or {}).get('config') or {}).get('backend')
    input_tokens=usage.get('input_tokens',usage.get('prompt_tokens'));output_tokens=usage.get('output_tokens',usage.get('completion_tokens'))
    reasoning=usage.get('reasoning_output_tokens',(usage.get('completion_tokens_details') or {}).get('reasoning_tokens'))
    if usage.get('per_turn'):
        reported=[u for u in usage['per_turn'] if u and (u.get('prompt_tokens') is not None or u.get('output_tokens') is not None)]
        def turn_input(u):
            if u.get('prompt_tokens') is not None:return u['prompt_tokens']
            return sum(u.get(k) or 0 for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens'])
        def turn_reasoning(u):
            return (u.get('completion_tokens_details') or {}).get('reasoning_tokens') or (u.get('output_tokens_details') or {}).get('thinking_tokens') or 0
        input_tokens=sum(turn_input(u) for u in reported) if reported else None
        output_tokens=sum(u.get('completion_tokens',u.get('output_tokens',0)) for u in reported) if reported else None
        reasoning=sum(turn_reasoning(u) for u in reported) if reported else None
    if r['model_key']=='muse' and usage.get('models'):
        u=usage['models'][0];input_tokens=u.get('input_tokens');output_tokens=u.get('output_tokens');reasoning=u.get('reasoning_tokens')
    if backend=='claude' and not usage.get('per_turn'):
        # Claude reports cached prompt tokens separately from the uncached remainder.
        input_tokens=sum(usage.get(k) or 0 for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens']) if usage else None
        reasoning=(usage.get('output_tokens_details') or {}).get('thinking_tokens')
    cost=r.get('cost_usd') if r.get('cost_usd') is not None else native.get('cost_usd')
    return {'label':r['label'],'model_key':r['model_key'],'group':workflow_group(r),'usable':r.get('format_failure') is None and not r.get('pending'),
            'pending':bool(r.get('pending')),'failure_category':r.get('failure_category'),
            'input_tokens':input_tokens,'output_tokens':output_tokens,'reasoning_tokens':reasoning,
            'wall_seconds':native.get('wall_seconds') if p.exists() else None,'cost_usd':cost,'evidence':str(p.relative_to(DATA)) if p.exists() else None}

def _group_axis(ax,rows,headers):
    labels=[];weights=[]
    for kind,text in rows:
        labels.append(text);weights.append('bold' if kind=='header' else 'normal')
    ax.set_yticks(range(len(rows)));ax.set_yticklabels(labels);ax.set_ylim(len(rows)-.3,-.7)
    for tick,weight in zip(ax.get_yticklabels(),weights):tick.set_fontweight(weight)
    ax.tick_params(axis='y',length=0)

def accuracy_figure(results,valid,baseline):
    rows=[];items=[]
    for g in GROUPS:
        members=[r for r in results if workflow_group(r)==g]
        if not members:continue
        rows.append(('header',g));items.append(None)
        for r in members:rows.append(('row','   '+r['label']));items.append(r)
    rows.append(('header','Reference that stores the sample'));items.append(None)
    rows.append(('row','   1-nearest neighbour'));items.append('reference')
    fig,ax=plt.subplots(figsize=(10.5,0.34*len(rows)+1.5))
    for y,item in enumerate(items):
        if item is None:continue
        if item=='reference':
            h=100*baseline['test']['accuracy'];ax.barh(y,h,color=BROWN,height=.62)
            ax.text(h+1,y,f"{h:.1f}%  ({baseline['test']['correct']:,}/1,797)",va='center',fontsize=8.5)
        elif item in valid:
            h=100*item['test']['accuracy'];lo,hi=np.asarray(item['test']['wilson_95'])*100
            ax.barh(y,h,color=BLUE,height=.62);ax.errorbar(h,y,xerr=[[h-lo],[hi-h]],fmt='none',ecolor=INK,capsize=2.5,lw=1)
            ax.text(hi+1,y,f"{h:.1f}%  ({item['test']['correct']:,}/1,797)",va='center',fontsize=8.5)
        else:
            ax.plot(0.6,y,marker='x',color=GREY,ms=6,mew=1.5)
            ax.text(2.2,y,failure_note(item),va='center',fontsize=8.5,color='#4b535c',style='italic')
    ax.axvline(10,color='#777777',linestyle='--',lw=1);ax.text(10.6,0,'random guessing, 10%',fontsize=8,color='#555555',va='center')
    best=max(valid,key=lambda r:r['test']['accuracy']) if valid else None
    title=f"{len(valid)} of {len(results)} submissions produced a network that could be scored"
    if best:title+=f"; {best['label']} scored highest ({100*best['test']['accuracy']:.1f}%)"
    ax.set(xlim=(0,112),xlabel='Official test images classified correctly (%), 1,797 images');ax.set_title(title,fontsize=11)
    _group_axis(ax,rows,GROUPS)
    ax.annotate('Bars: one fixed network each, with Wilson 95% intervals over test images. A cross marks a submission with no network to score;\nit is not an accuracy of zero. The reference copies the label of the most similar visible image and is not a directly written network.',
                xy=(0,0),xycoords='axes fraction',xytext=(0,-34),textcoords='offset points',fontsize=7.8,color='#444444',va='top')
    fig.tight_layout();fig.savefig(FIGURES/'test_accuracy.png',bbox_inches='tight');plt.close(fig)

def usage_figure(results,valid):
    ordered=ordered_rows(results);usage=[usage_row(r) for r in ordered]
    rows=[];items=[]
    for g in GROUPS:
        members=[u for u in usage if u['group']==g]
        if not members:continue
        rows.append(('header',g));items.append(None)
        for u in members:rows.append(('row','   '+u['label']));items.append(u)
    fig,ax=plt.subplots(figsize=(10.5,0.34*len(rows)+1.5))
    for y,u in enumerate(items):
        if u is None:continue
        out=u['output_tokens'];rt=u['reasoning_tokens']
        if out is None:
            text=('Still running' if u['pending'] else 'Provider error before any output' if u['failure_category'] in ['provider_unavailable','provider_or_transport_failure']
                  else 'No token count reported')
            ax.text(1000,y,text,va='center',fontsize=8.5,color='#4b535c',style='italic');continue
        rt=min(rt or 0,out);answer=out-rt;cut=out>AXIS_CAP
        colour=BLUE if u['usable'] else GREY
        ax.barh(y,min(rt,AXIS_CAP),color=colour,alpha=.45,height=.62,hatch='///' if not u['usable'] else None,edgecolor='white')
        ax.barh(y,min(answer,AXIS_CAP-min(rt,AXIS_CAP)),left=min(rt,AXIS_CAP),color=colour,height=.62)
        note=f"{out:,} output tokens"+(f", {rt:,} reasoning" if rt else '')+('' if u['usable'] else ' - no network')+(' (bar cut)' if cut else '')
        if cut:ax.text(rt+3000,y,note,va='center',ha='left',fontsize=8.2,color='white')
        else:ax.text(out+1500,y,note,va='center',fontsize=8.2)
    ax.set_xlabel('Output tokens per submission (light: reported reasoning; solid: visible reply)')
    ax.set_xlim(0,AXIS_CAP);ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,_:f'{int(v):,}'))
    known=[u for u in usage if u['output_tokens'] is not None]
    scored=[u['output_tokens'] for u in known if u['usable']]
    limited=[u for u in known if u['failure_category'] in ['budget_or_output_stop','output_limit']]
    title=f"Networks that could be scored used {min(scored):,} to {max(scored):,} output tokens" if scored else 'Output tokens per submission'
    if limited:title+=f"; {len(limited)} failures stopped at an output limit"
    ax.set_title(title,fontsize=11)
    _group_axis(ax,rows,GROUPS)
    fig.tight_layout();fig.savefig(FIGURES/'output_tokens.png',bbox_inches='tight');plt.close(fig)
    return usage

def make_figures():
    FIGURES.mkdir(exist_ok=True);live_reasoning_logs();indexed_workflow_metadata();reported_billing();verify_indexed_artifacts()
    with np.load(DATA/'dataset.npz') as saved:dataset={k:saved[k] for k in saved.files}
    results=collect_results();valid=[r for r in results if not r.get('pending') and r.get('format_failure') is None]
    legacy=verify_legacy_mlps()
    baseline=nearest_neighbour_baseline(dataset)
    parameter_rows=[]
    for r in valid:
        with np.load(DATA/r['candidate_folder']/'candidate.npz') as weights:
            parameter_rows.append({'label':r['label'],'zeros':r['weights']['zeros'],'max_abs':r['weights']['max_abs'],
                'h1_nonzero_rows':int(np.sum(np.any(weights['W1']!=0,axis=1)|(weights['b1']!=0))),
                'h2_nonzero_rows':int(np.sum(np.any(weights['W2']!=0,axis=1)|(weights['b2']!=0))),
                'nonzero_by_tensor':{k:int(np.count_nonzero(weights[k])) for k in weights.files}})
    save_json(DATA/'parameter_use.json',parameter_rows)
    astra_path=DATA/'responses/astra/candidate.npz';sol_path=DATA/'responses/sol/candidate.npz'
    if astra_path.exists() and sol_path.exists():
        structure={'analysis':'Post-hoc interpretation, not teacher reasoning text','identical_downstream':{},'max_identity_error':{}}
        with np.load(astra_path) as first,np.load(sol_path) as second:
            structure['identical_downstream']={k:bool(np.array_equal(first[k],second[k])) for k in ['W2','b2','W3','b3']}
            for name,w in [('Astra',first),('Sol',second)]:
                x=dataset['test'][:,:64].astype(float)/16;h1=np.maximum(x@w['W1'].T+w['b1'],0)
                blocks=h1[:,:40].reshape(-1,10,4)
                interpreted=np.maximum(blocks[:,:,:2].sum(axis=2),blocks[:,:,2:].sum(axis=2))
                h2=np.maximum(h1@w['W2'].T+w['b2'],0);actual=h2@w['W3'].T+w['b3']
                structure['max_identity_error'][name]=float(np.max(np.abs(actual-interpreted)))
        x=dataset['test'][:,:64].astype(float)/16
        claude_paths={'Opus 5.5 high numbered entries':DATA/'indexed/opus/candidate.npz','Sonnet 5.5 numbered entries':DATA/'indexed/sonnet/candidate.npz'}
        structure['template_matching']={}
        for name,path in claude_paths.items():
            if not path.exists():continue
            with np.load(path) as w:
                h1=np.maximum(x@w['W1'].T+w['b1'],0);h2=np.maximum(h1@w['W2'].T+w['b2'],0);actual=h2@w['W3'].T+w['b3']
                if name.startswith('Opus'):
                    # Each digit score is the best of its first-layer template units (two templates for 1, 7 and 9).
                    units={c:[int(u) for u in np.flatnonzero(w['W2'][np.flatnonzero(w['W3'][c])].max(axis=0)>0)] for c in range(10)}
                    interpreted=np.stack([h1[:,units[c]].max(axis=1) for c in range(10)],axis=1)
                    entry={'templates_per_digit':{str(c):len(units[c]) for c in range(10)},'template_units':int(np.sum(np.any(w['W1']!=0,axis=1))),
                           'smallest_template_preactivation':float((x@w['W1'].T+w['b1'])[:,np.any(w['W1']!=0,axis=1)].min())}
                else:
                    # W1 is the identity, so each digit score is one template dot product plus a bias.
                    interpreted=x@w['W2'][:10].T+w['b2'][:10]
                    entry={'first_layer_is_identity':bool(np.array_equal(w['W1'],np.eye(64))),'template_units':int(np.sum(np.any(w['W2']!=0,axis=1)))}
                entry['max_difference_from_full_network']=float(np.max(np.abs(actual-interpreted)))
                structure['template_matching'][name]=entry
        save_json(DATA/'program_structure.json',structure)
    if parameter_rows:
        fig,ax=plt.subplots(figsize=(10,4));bottom=np.zeros(len(parameter_rows));colours=['#286f9e','#7f9a61','#b7752c']
        for names,label,colour in zip([['W1','b1'],['W2','b2'],['W3','b3']],['Input layer','Second layer','Output layer'],colours):
            counts=np.array([sum(r['nonzero_by_tensor'][k] for k in names) for r in parameter_rows]);ax.bar(range(len(counts)),counts,bottom=bottom,color=colour,label=label);bottom+=counts
        for i,total in enumerate(bottom):ax.text(i,total+60,f'{int(total):,}',ha='center',fontsize=8.5)
        ax.axhline(6570,color='#777777',linestyle='--',lw=1);ax.text(len(parameter_rows)-.5,6570+60,'all 6,570 values',ha='right',fontsize=8,color='#555555')
        ax.set(xticks=range(len(parameter_rows)),ylim=(0,7300),ylabel='Nonzero values (of 6,570 supplied)',title='The networks that run use between {:,} and {:,} nonzero values'.format(int(bottom.min()),int(bottom.max())))
        ax.set_xticklabels([r['label'] for r in parameter_rows],rotation=20,ha='right')
        ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIGURES/'parameter_use.png',bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,5,figsize=(10,4.5))
    for digit,ax in enumerate(axes.flat):
        i=int(np.flatnonzero(dataset['visible'][:,-1]==digit)[0]);row=dataset['visible'][i]
        ax.imshow(row[:64].reshape(8,8),cmap='Greys',vmin=0,vmax=16,interpolation='nearest')
        ax.set_title(f'Digit {digit}: train-{int(dataset["visible_indices"][i]):04d}',fontsize=9);ax.axis('off')
    fig.suptitle('The visible sample contains ten handwritten digit classes',fontsize=13)
    fig.tight_layout();fig.savefig(FIGURES/'visible_digits.png',bbox_inches='tight');plt.close(fig)
    accuracy_figure(results,valid,baseline)
    usage=usage_figure(results,valid)
    save_json(DATA/'usage_summary.json',usage)
    example_ids=[];selection=[]
    def add(i,why):
        if int(i) not in example_ids:example_ids.append(int(i));selection.append(why)
    add(0,'First official test item, fixed ordinary case')
    if valid:
        lead=sorted(valid,key=lambda r:(-r['test']['accuracy'],r['model_key']))[0]
        with np.load(DATA/lead['candidate_folder']/'predictions.npz') as p:pred=p['test_pred'];scores=p['test_scores']
        gold=dataset['test'][:,-1]
        for mask,why in [(pred==gold,'First correct case for highest observed score'),(pred!=gold,'First error for highest observed score')]:
            indices=np.flatnonzero(mask)
            if len(indices):add(indices[0],why)
        sorted_scores=np.sort(scores,axis=1);add(np.argmin(sorted_scores[:,-1]-sorted_scores[:,-2]),'Smallest uncalibrated top-two score margin')
        if len(valid)>1:
            with np.load(DATA/valid[0]['candidate_folder']/'predictions.npz') as p:one=p['test_pred']
            with np.load(DATA/valid[1]['candidate_folder']/'predictions.npz') as p:two=p['test_pred']
            indices=np.flatnonzero(one!=two)
            if len(indices):add(indices[0],'First disagreement between first two readable model submissions')
    for i in range(len(dataset['test'])):
        if len(example_ids)>=5:break
        add(i,'First unused official test item to complete five distinct examples')
    examples=[]
    for i,why in zip(example_ids,selection):
        row={'id':f'test-{i:04d}','index':i,'gold':int(dataset['test'][i,-1]),'selection':why,'predictions':{}}
        for r in valid:
            with np.load(DATA/r['candidate_folder']/'predictions.npz') as p:row['predictions'][r['label']]=int(p['test_pred'][i])
        examples.append(row)
    save_json(DATA/'worked_examples.json',examples)
    fig,axes=plt.subplots(1,len(examples),figsize=(12,4))
    for ax,case in zip(np.atleast_1d(axes),examples):
        ax.imshow(dataset['test'][case['index'],:64].reshape(8,8),cmap='Greys',vmin=0,vmax=16);ax.axis('off')
        ax.set_title(f'{case["id"]}\nGold {case["gold"]}',fontsize=10)
        short=lambda n:n.replace(' numbered entries','').replace(' high','').replace(' batch','')
        text='\n'.join(f"{short(name)}: {pred}"+('' if pred==case['gold'] else ' (wrong)') for name,pred in case['predictions'].items()) or 'No scored submission yet'
        ax.text(.5,-.08,text,ha='center',va='top',transform=ax.transAxes,fontsize=9)
    fig.suptitle('Traceable test images expose successes, errors and disagreements');fig.tight_layout()
    fig.savefig(FIGURES/'worked_examples.png',bbox_inches='tight');plt.close(fig)
    if valid:
        lead=sorted(valid,key=lambda r:(-r['test']['accuracy'],r['model_key']))[0];cm=np.asarray(lead['test']['confusion'])
        fig,ax=plt.subplots(figsize=(7,6));im=ax.imshow(cm,cmap='Blues')
        for i in range(10):
            for j in range(10):
                if cm[i,j]:ax.text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=8,color='white' if cm[i,j]>cm.max()/2 else '#222')
        ax.set(xticks=range(10),yticks=range(10),xlabel='Predicted digit',ylabel='Gold digit',title=f'{lead["label"]}: which digit classes are confused')
        fig.colorbar(im,ax=ax,label='Number of official test images');fig.tight_layout();fig.savefig(FIGURES/'confusion.png',bbox_inches='tight');plt.close(fig)
    summary={'results':results,'nearest_neighbour':baseline,'legacy_replay':legacy,'readable_submissions':len(valid),
             'unreadable_submissions':sum(not r.get('pending') and r.get('format_failure') is not None for r in results),
             'pending_submissions':sum(bool(r.get('pending')) for r in results),'n_test':1797}
    save_json(DATA/'study_summary.json',summary)
    return summary



import math,re
COUNTS={"W1":4096,"b1":64,"W2":2048,"b2":32,"W3":320,"b3":10}

def strip_fence(text):
    """Remove one Markdown code fence around a reply (```json ... ```). A transport wrapper, never a value change."""
    t=(text or '').strip()
    if t.startswith('```'):
        t=t.split('\n',1)[1] if '\n' in t else ''
        if t.rstrip().endswith('```'):t=t.rstrip()[:-3]
    return t.strip()

def indexed_entries(text):
    """Parse only unambiguous complete numeric members, even with an unfinished outer JSON.

    A numeric token at end of text is not accepted without its following comma/brace,
    because an output limit could have cut the number itself. No values are inferred.
    """
    text=text.strip();decoder=json.JSONDecoder();pos=0;found={k:{} for k in COUNTS};issue=None
    def whitespace(i):
        while i<len(text) and text[i].isspace():i+=1
        return i
    def take(i):return decoder.raw_decode(text,whitespace(i))
    try:
        pos=whitespace(pos)
        if pos>=len(text) or text[pos]!='{':return found,{'kind':'not_json_object','partial':False}
        pos+=1;seen_tensors=set()
        while True:
            pos=whitespace(pos)
            if pos>=len(text):return found,{'kind':'unfinished_outer_object','partial':True}
            if text[pos]=='}':
                pos=whitespace(pos+1)
                assert pos==len(text),'Text after the JSON object'
                return found,None
            name,pos=take(pos);assert isinstance(name,str) and name in COUNTS,'Unknown tensor name'
            assert name not in seen_tensors,'Duplicate tensor object';seen_tensors.add(name)
            pos=whitespace(pos);assert pos<len(text) and text[pos]==':','Expected tensor colon';pos=whitespace(pos+1)
            assert pos<len(text) and text[pos]=='{','Expected numbered tensor object';pos+=1
            while True:
                pos=whitespace(pos)
                if pos>=len(text):return found,{'kind':'unfinished_tensor','tensor':name,'partial':True}
                if text[pos]=='}':pos+=1;break
                index,pos=take(pos)
                assert isinstance(index,str) and re.fullmatch(r'[1-9][0-9]*',index),'Index must be a one-based integer string'
                number=int(index);assert 1<=number<=COUNTS[name],'Out-of-range index'
                assert number not in found[name],'Duplicate indexed entry within reply'
                pos=whitespace(pos);assert pos<len(text) and text[pos]==':','Expected value colon';value_start=whitespace(pos+1)
                value,end=take(value_start);after=whitespace(end)
                if after>=len(text):return found,{'kind':'numeric_token_without_delimiter','tensor':name,'index':number,'partial':True}
                if text[after] not in ',}':
                    tail=text[value_start:].strip()
                    if re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]*)?(?:[eE][+-]?[0-9]*)?',tail):
                        return found,{'kind':'unfinished_numeric_literal','tensor':name,'index':number,'partial':True}
                    raise AssertionError('Unexpected character after numerical value')
                assert type(value) in [int,float] and math.isfinite(value),'Non-finite or non-numeric value'
                found[name][number]=value
                if text[after]==',':pos=after+1
                else:pos=after+1;break
            pos=whitespace(pos)
            if pos>=len(text):return found,{'kind':'unfinished_outer_object','partial':True}
            if text[pos]==',':pos+=1
            elif text[pos]=='}':
                pos=whitespace(pos+1);assert pos==len(text),'Text after JSON';return found,None
            else:raise AssertionError('Expected tensor separator')
    except json.JSONDecodeError as exc:
        return found,{'kind':'unfinished_or_malformed_token','partial':True,'position':exc.pos}
    except (AssertionError,ValueError,TypeError,OverflowError) as exc:
        return found,{'kind':'invalid_structure','partial':False,'message':str(exc)}

def missing_ranges(merged):
    result={}
    for name,count in COUNTS.items():
        missing=[i for i in range(1,count+1) if i not in merged[name]];ranges=[]
        for i in missing:
            if ranges and i==ranges[-1][1]+1:ranges[-1][1]=i
            else:ranges.append([i,i])
        if ranges:result[name]=ranges
    return result

def call_records(folder):
    return sorted(folder.glob('turn-*/response.json'))+sorted(folder.glob('call-*/response.json'))

def verify_indexed_artifacts():
    checks=[]
    folders=[f for base in [DATA/'indexed',DATA/'open_models'] if base.exists() for f in sorted(base.iterdir()) if f.is_dir()]
    for folder in folders:
        assembled=folder/'assembled_response.json'
        if not assembled.exists():continue
        merged={k:{} for k in COUNTS};turns=[]
        for path in call_records(folder):
            record=json.loads(path.read_text(encoding='utf-8'));entries,issue=indexed_entries(strip_fence(record.get('answer','')))
            for name,values in entries.items():
                for index,value in values.items():
                    assert index not in merged[name] or merged[name][index]==value,'Conflicting teacher entries'
                    merged[name][index]=value
            turns.append({'path':str(path.relative_to(DATA)),'cache_key':record['cache_key'],'parse_issue':issue})
        assert not missing_ranges(merged),'Assembled submission has missing source indices'
        flat=np.array([merged[name][i] for name,count in COUNTS.items() for i in range(1,count+1)],dtype=float)
        saved=json.loads(assembled.read_text(encoding='utf-8'));payload=json.loads(saved['answer'])
        assert np.array_equal(flat,np.asarray(payload['weights'],dtype=float)),'Assembly changed a source value'
        checks.append({'model_key':folder.name,'values_verified':len(flat),'teacher_values_modified':False,'source_turns':turns})
    save_json(DATA/'indexed_provenance_checks.json',checks)
    return checks

def indexed_workflow_metadata():
    folders=[f for base in [DATA/'indexed',DATA/'open_models'] if base.exists() for f in base.iterdir() if f.is_dir()]
    for folder in folders:
        paths=call_records(folder)
        if not paths:continue
        records=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
        metadata={'started_utc':records[0]['started_utc'],'finished_utc':records[-1]['finished_utc'],
                  'wall_seconds':sum(r['wall_seconds'] for r in records),'usage':{'per_turn':[r.get('usage') for r in records]},
                  'cost_usd':sum(r.get('cost_usd') or 0 for r in records) if all(r.get('cost_usd') is not None for r in records) else None,
                  'turn_cache_keys':[r['cache_key'] for r in records],'outer_requests':len(records),
                  'provider_errors':[r['error'] for r in records if r.get('error') and not (r.get('answer') or r.get('reasoning'))]}
        save_json(folder/'workflow_summary.json',metadata)
        p=folder/'results.json'
        if p.exists() and not (folder/'assembled_response.json').exists():
            result=json.loads(p.read_text(encoding='utf-8'))
            if len(metadata['provider_errors'])==len(records):
                result.update(format_failure=f'{len(records)} provider errors before numerical output',failure_category='provider_unavailable')
            result.update(wall_seconds=metadata['wall_seconds'],usage=metadata['usage'],cost_usd=metadata['cost_usd'])
            save_json(p,result)

def reported_billing():
    batches=[]
    for path in sorted(DATA.glob('**/batch_result.json')):
        if 'legacy' in path.parts:continue
        usage=json.loads(path.read_text(encoding='utf-8')).get('usage') or {}
        if usage.get('cost') is None:continue
        cost=float(usage['cost']);batches.append({'source':str(path.relative_to(DATA)),'cost_usd':cost})
        result_path=path.parent/'results.json'
        if result_path.exists():
            result=json.loads(result_path.read_text(encoding='utf-8'));result.update(cost_usd=cost,cost_source='Cached batch_result.json/usage/cost');save_json(result_path,result)
    indexed=DATA/'indexed/gemini'
    costs=[b['cost_usd'] for b in batches if b['source'].startswith(str(Path('indexed/gemini')))]
    if costs and (indexed/'results.json').exists():
        result=json.loads((indexed/'results.json').read_text(encoding='utf-8'));result.update(cost_usd=sum(costs),cost_source='Sum of indexed per-turn batch billing');save_json(indexed/'results.json',result)
    claude=[]
    for area in ['responses','recovery']:
        path=DATA/area/'opus/response.json'
        if path.exists():claude.append(json.loads(path.read_text(encoding='utf-8')).get('cost_usd') or 0)
    family={}
    for key in FAMILY_LABELS:
        path=DATA/'claude_family'/key/'response.json'
        if path.exists():family[key]=json.loads(path.read_text(encoding='utf-8')).get('cost_usd')
    save_json(DATA/'billing_summary.json',{'google_api_cost_usd':sum(b['cost_usd'] for b in batches),'google_batches':batches,
        'claude_session_list_price_equivalent_usd':max(claude,default=0),
        'claude_family_list_price_equivalent_usd':family,'other_cli_charges_usd':None,
        'nemotron_route':'Free-only with zero-price cap and no paid fallback','note':'API charges and CLI list-price equivalents are different measures.'})

if __name__=='__main__':
    summary=make_figures();print(json.dumps({k:v for k,v in summary.items() if k not in ['results']},indent=2))
