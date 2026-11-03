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
MODEL_LABELS = {'astra':'Astra','sol':'Sol','opus':'Opus 5.5','muse':'Muse Wonder','nemotron':'Nemotron','gemini':'Gemini batch'}
plt.rcParams.update({'figure.dpi':130,'savefig.dpi':160,'font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.titleweight':'bold','axes.labelsize':10,
                     'figure.facecolor':'white','axes.facecolor':'white'})

def save_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def live_reasoning_logs():
    """Only text the external provider actually emitted. Never infer hidden reasoning."""
    for key in MODEL_LABELS:
        folder=DATA/'responses'/key;events_path=folder/'events.jsonl'
        if not events_path.exists():continue
        events=[]
        for line in events_path.read_text(encoding='utf-8').splitlines():
            try:events.append(json.loads(line))
            except ValueError:pass
        if key=='opus':
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
    for key,label in MODEL_LABELS.items():
        folder=DATA/'responses'/key;path=folder/'results.json'
        result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
        result['label']=label
        result['candidate_folder']=str(folder.relative_to(DATA))
        rp=folder/'reasoning.txt';result['reasoning_characters']=len(rp.read_text(encoding='utf-8')) if rp.exists() else 0
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
        for folder in sorted(indexed_root.iterdir()):
            if not folder.is_dir() or folder.name not in MODEL_LABELS:continue
            key=folder.name;path=folder/'results.json'
            result=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'model_key':key,'format_failure':None,'pending':True}
            result['label']=MODEL_LABELS[key]+' indexed';result['indexed']=True
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
        save_json(DATA/'program_structure.json',structure)
    if parameter_rows:
        fig,ax=plt.subplots(figsize=(10,4));bottom=np.zeros(len(parameter_rows));colours=['#286f9e','#7f9a61','#b7752c']
        for names,label,colour in zip([['W1','b1'],['W2','b2'],['W3','b3']],['Input layer','Second layer','Output layer'],colours):
            counts=np.array([sum(r['nonzero_by_tensor'][k] for k in names) for r in parameter_rows]);ax.bar(range(len(counts)),counts,bottom=bottom,color=colour,label=label);bottom+=counts
        ax.set(xticks=range(len(parameter_rows)),xticklabels=[r['label'] for r in parameter_rows],ylabel='Nonzero values (of 6,570 supplied)',title='The numerical authors use different fractions of the available network')
        ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIGURES/'parameter_use.png',bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,5,figsize=(10,4.5))
    for digit,ax in enumerate(axes.flat):
        i=int(np.flatnonzero(dataset['visible'][:,-1]==digit)[0]);row=dataset['visible'][i]
        ax.imshow(row[:64].reshape(8,8),cmap='Greys',vmin=0,vmax=16,interpolation='nearest')
        ax.set_title(f'Digit {digit}: train-{int(dataset["visible_indices"][i]):04d}',fontsize=9);ax.axis('off')
    fig.suptitle('The visible sample contains ten handwritten digit classes',fontsize=13)
    fig.tight_layout();fig.savefig(FIGURES/'visible_digits.png',bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(13,5));labels=[];heights=[];colours=[]
    for r in results:
        short={'Muse Wonder':'Muse\nWonder','Gemini batch':'Gemini\ninitial','Gemini batch schema retry':'Gemini\nschema retry',
               'Gemini batch low effort':'Gemini\nlow effort','Opus 5.5 continuation':'Opus 5.5\ncontinuation',
               'Gemini batch indexed':'Gemini\nindexed','Nemotron indexed':'Nemotron\nindexed'}
        labels.append(short.get(r['label'],r['label']));heights.append(100*r['test']['accuracy'] if r in valid else 0)
        colours.append('#286f9e' if r in valid else '#c2c8cf')
    labels.append('1-nearest\nneighbour');heights.append(100*baseline['test']['accuracy']);colours.append('#b7752c')
    bars=ax.bar(np.arange(len(labels)),heights,color=colours)
    for i,r in enumerate(results):
        if r in valid:
            lo,hi=np.asarray(r['test']['wilson_95'])*100;h=heights[i]
            ax.errorbar(i,h,yerr=[[h-lo],[hi-h]],fmt='none',ecolor='#172e40',capsize=3)
            ax.text(i,h+3,f'{h:.1f}%',ha='center',fontsize=9)
        else:ax.text(i,3,'Pending' if r.get('pending') else 'Unreadable',rotation=60,ha='center',fontsize=9,color='#525b65')
    ax.text(len(labels)-1,heights[-1]+3,f'{heights[-1]:.1f}%',ha='center',fontsize=9)
    ax.axhline(10,color='#777777',linestyle='--',label='Uniform guess: 10%')
    ax.set(xticks=np.arange(len(labels)),xticklabels=labels,ylim=(0,110),ylabel='Official test images classified correctly (%)')
    ax.set_title('Identical MLP architecture yields different digit-classification accuracy');ax.legend(loc='upper left',fontsize=8)
    ax.text(.01,-.25,'Grey entries have no scored network; their height is not an accuracy estimate.\nIntervals: Wilson 95%, conditional on each fixed submitted network.',transform=ax.transAxes,fontsize=8)
    fig.tight_layout();fig.savefig(FIGURES/'test_accuracy.png',bbox_inches='tight');plt.close(fig)
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
        text='\n'.join(f'{name}: {pred}' for name,pred in case['predictions'].items()) or 'No scored submission yet'
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

def verify_indexed_artifacts():
    checks=[];base=DATA/'indexed'
    if not base.exists():return checks
    for folder in sorted(base.iterdir()):
        assembled=folder/'assembled_response.json'
        if not assembled.exists():continue
        merged={k:{} for k in COUNTS};turns=[]
        for path in sorted(folder.glob('turn-*/response.json')):
            record=json.loads(path.read_text(encoding='utf-8'));entries,issue=indexed_entries(record.get('answer',''))
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
    base=DATA/'indexed'
    if not base.exists():return
    for folder in base.iterdir():
        paths=sorted(folder.glob('turn-*/response.json'))
        if not paths:continue
        records=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
        metadata={'started_utc':records[0]['started_utc'],'finished_utc':records[-1]['finished_utc'],
                  'wall_seconds':sum(r['wall_seconds'] for r in records),'usage':{'per_turn':[r.get('usage') for r in records]},
                  'cost_usd':sum(r.get('cost_usd') or 0 for r in records) if all(r.get('cost_usd') is not None for r in records) else None,
                  'turn_cache_keys':[r['cache_key'] for r in records],'outer_requests':len(records),
                  'provider_errors':[r['error'] for r in records if r.get('error')]}
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
    save_json(DATA/'billing_summary.json',{'google_api_cost_usd':sum(b['cost_usd'] for b in batches),'google_batches':batches,
        'claude_session_list_price_equivalent_usd':max(claude,default=0),'other_cli_charges_usd':None,
        'nemotron_route':'Free-only with zero-price cap and no paid fallback','note':'API charges and CLI list-price equivalents are different measures.'})

if __name__=='__main__':
    summary=make_figures();print(json.dumps({k:v for k,v in summary.items() if k not in ['results']},indent=2))
