from pathlib import Path
import gzip,json
import pandas as pd

root=Path(__file__).resolve().parents[1]
data=root/'data'
construction=[]
if (data/'exam_v1.jsonl').exists():
    with (data/'exam_v1.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            item=json.loads(line);good=item['candidates'][item['better']];bad=item['candidates']['B' if item['better']=='A' else 'A']
            construction.append(dict(item_id=item['item_id'],cohort='original' if item['split']=='test' else 'new',family=item['family'],
                                     error_source=item['error_source'],trap=bool(item['tags']['trap']),better_construction=good['construction'],
                                     better_writer=good['writer_name'],worse_construction=bad['construction'],
                                     failed_hidden_tests=bad['check']['total']-bad['check']['passed'] if item['family']=='code' else None,
                                     word_delta=bad['check']['word_count']-good['check']['word_count'] if item['family']=='instructions' else None))
    construction_frame=pd.DataFrame(construction)
    construction_frame.to_csv(data/'item_construction.csv',index=False)
    construction_frame.groupby(['cohort','family','error_source','better_construction'],as_index=False).agg(items=('item_id','size'),traps=('trap','sum')).to_csv(data/'construction_summary.csv',index=False)
import os,subprocess,sys,tempfile
tempfile.tempdir=str((data/'tmp').resolve())
CODE_OBSERVER_RUNNER = "import json,sys,builtins,types\nrequest=json.load(sys.stdin)\nreal_import=builtins.__import__\nallowed={'math','decimal','fractions','collections','itertools','functools','datetime','calendar','re','statistics','bisect','heapq','operator','string','typing','copy','json','ast','dataclasses','numbers','unicodedata'}\ndef guarded(name,*a,**kw):\n if name.split('.')[0] not in allowed: raise ImportError('blocked import')\n return real_import(name,*a,**kw)\nb=dict(vars(builtins));b['__import__']=guarded\nfor k in ['open','input','eval','exec','compile','breakpoint']:b.pop(k,None)\nmodule=types.ModuleType('candidate');module.__dict__['__builtins__']=b;sys.modules['candidate']=module;ns=module.__dict__\ntry:\n exec(request['source'],ns)\n for index,test in enumerate(request['tests']):\n  before=json.dumps(test['input'],sort_keys=True)\n  try:\n   value=ns['solve'](test['input'])\n   result=dict(value_repr=repr(value),value_type=type(value).__name__,input_after=test['input'],input_mutated=before!=json.dumps(test['input'],sort_keys=True))\n  except Exception as exc:result=dict(error=type(exc).__name__,message=str(exc)[:400])\n  if index==request['target']:\n   print(json.dumps(result,ensure_ascii=False));break\nexcept Exception as exc:print(json.dumps(dict(error=type(exc).__name__,message=str(exc)[:400])))\n"

def observe_existing_code_test(item):
    bad=item['candidates']['B' if item['better']=='A' else 'A']
    target=next(index for index,passed in enumerate(bad['check']['checks']) if not passed)
    test=item['hidden_tests'][target]
    out=dict(item_id=item['item_id'],test_index=target,preceding_tests_executed=target,input=test['input'],expected=test['expected'],better=item['better'])
    for label,candidate in item['candidates'].items():
        request=dict(source=candidate['text'],tests=item['hidden_tests'],target=target)
        try:
            with tempfile.TemporaryDirectory(prefix='nb34_audit_') as folder:
                env={'SYSTEMROOT':os.environ.get('SYSTEMROOT','C:/Windows'),'NO_COLOR':'1'}
                process=subprocess.run([sys.executable,'-X','utf8','-E','-P','-c',CODE_OBSERVER_RUNNER],input=json.dumps(request),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,cwd=folder,timeout=4)
            out[label]=json.loads(process.stdout)
        except Exception as exc:out[label]=dict(error=type(exc).__name__,message=str(exc)[:400])
    return out

j=pd.read_csv(data/'judgments.csv')
routes=pd.read_csv(data/'routing.csv')
counts=[]
for keys,g in j.groupby(['cohort','condition','judge']):
    counts.append(dict(cohort=keys[0],condition=keys[1],judge=keys[2],logical_requests=len(g),
                       invocation_attempts=int(g.attempts.sum()),reused_requests=int(g.origin.astype(str).eq('33').sum()),
                       local_requests=int(g.origin.astype(str).eq('34').sum()),
                       local_attempts=int(g.loc[g.origin.astype(str).eq('34'),'attempts'].sum())))
pd.DataFrame(counts).to_csv(data/'call_counts.csv',index=False)
selected=set(routes.loc[routes.route.eq('disagreed'),'item_id'])
coverage=[]
for reader in ['lenient','strict']:
    for keys,g in j[j.item_id.isin(selected)].groupby(['condition','judge']):
        items=g.assign(readable=g[reader+'_canonical'].notna()).groupby('item_id').readable.agg(['any','all'])
        coverage.append(dict(reader=reader,condition=keys[0],judge=keys[1],disagreement_items=len(items),
                             items_read_at_least_one_order=int(items['any'].sum()),items_read_both_orders=int(items['all'].sum()),
                             readable_order_replies=int(g[reader+'_canonical'].notna().sum())))
pd.DataFrame(coverage).to_csv(data/'coverage_by_model_condition.csv',index=False)
cache={}
for path in [data/'cache_from_33.jsonl.gz',data/'cache_requests.jsonl.gz',data/'cache_requests.jsonl']:
    if not path.exists():continue
    with (gzip.open(path,'rt',encoding='utf-8') if path.suffix=='.gz' else path.open(encoding='utf-8')) as stream:
        for line in stream:
            r=json.loads(line);cache[r['key']]=r
used=set(j.raw_reply_cache_key)
signatures={(cache[k]['request']['model'],cache[k]['request']['backend'],cache[k]['request']['purpose']) for k in used}
costs=[]
for k,row in cache.items():
    req,o=row['request'],row['response'];backend=req['backend']
    if (req['model'],backend,req['purpose']) not in signatures:continue
    unpriced=backend=='claude' and o.get('list_cost_usd') is None or backend=='codex' and not o.get('usage')
    costs.append(dict(key=k,is_final=k in used,model=req['model'],backend=backend,origin='33' if row.get('origin') else '34',
                      missing_cli_price_or_usage=bool(unpriced),muse_proxy_only=backend=='muse',
                      missing_openrouter_cost=backend in ('openrouter','decisions') and o.get('cost') is None))
pd.DataFrame(costs).groupby(['model','backend','origin'],as_index=False).agg(
    invocation_attempts=('key','size'),selected_final_requests=('is_final','sum'),missing_cli_price_or_usage=('missing_cli_price_or_usage','sum'),
    muse_proxy_only=('muse_proxy_only','sum'),missing_openrouter_cost=('missing_openrouter_cost','sum')).to_csv(data/'cost_completeness.csv',index=False)
print('Supplemental call counts, coverage and cost completeness saved')

local_attempts=[r for r in cache.values() if not r.get('origin')]
if (data/'nonfinal_attempts.jsonl').exists():
    local_attempts.extend(json.loads(s) for s in (data/'nonfinal_attempts.jsonl').read_text(encoding='utf-8').splitlines() if s.strip())
spans=[]
for row in local_attempts:
    out=row['response']
    if out.get('started_at') and out.get('completed_at'):
        spans.append((pd.Timestamp(out['started_at']),pd.Timestamp(out['completed_at'])))
periods=[]
for start,end in sorted(spans):
    if not periods or (start-periods[-1]['end_utc']).total_seconds()>3600:
        periods.append(dict(start_utc=start,end_utc=end,returned_attempts=1))
    else:
        periods[-1]['end_utc']=max(periods[-1]['end_utc'],end)
        periods[-1]['returned_attempts']+=1
for p in periods:p['wall_span_seconds']=(p['end_utc']-p['start_utc']).total_seconds()
period_frame=pd.DataFrame(periods)
period_frame.to_csv(data/'collection_periods.csv',index=False)
print('Observed invocation periods (split after >1 hour without invocations):')
print(period_frame.to_string(index=False))
print('Sum of observed period wall spans, seconds:',period_frame.wall_span_seconds.sum())

import hashlib,numpy as np
outcomes=pd.read_csv(data/'item_outcomes.csv')
paired_families=[]
for cohort in ['original','new','all']:
    base=outcomes[outcomes.route.eq('disagreed')]
    if cohort!='all':base=base[base.cohort.eq(cohort)]
    for (reader,policy,family),group in base.groupby(['reader','unreadable_policy','family']):
        wide=group.pivot(index='item_id',columns='method',values='score')
        for model in ['Haiku','Luna','Granite 8B','DeepSeek 763B']:
            a,b='reasons:'+model,'alone:'+model
            delta=(wide[a]-wide[b]).to_numpy(dtype=float)
            label=json.dumps([3410302026,cohort,reader,policy,family,model],separators=(',',':'))
            rng=np.random.default_rng(int(hashlib.sha256(label.encode()).hexdigest()[:16],16))
            boot=delta[rng.integers(0,len(delta),size=(5000,len(delta)))].mean(axis=1)
            low,high=np.quantile(boot,[.025,.975])
            paired_families.append(dict(cohort=cohort,reader=reader,unreadable_policy=policy,family=family,
                model=model,n=len(delta),accuracy_difference=float(delta.mean()),ci_low=low,ci_high=high,
                reasons_better=int((delta>0).sum()),alone_better=int((delta<0).sum()),equal=int((delta==0).sum()),sparse=len(delta)<10))
pd.DataFrame(paired_families).to_csv(data/'paired_family_comparisons.csv',index=False)
print('Planned paired reasons-versus-alone comparisons by family saved')

import difflib,textwrap
import matplotlib.pyplot as plt

examples=json.loads((data/'worked_examples.json').read_text(encoding='utf-8'))
if (data/'exam_v1.jsonl').exists():
    existing={(e['category'],e['item_id']) for e in examples}
    controls={}
    for family in ['code','worked','instructions','grounded']:
        pool=routes[routes.family.eq(family)&routes.route.eq('agreed')&routes.opus_state.eq(routes.better)]
        original=pool[pool.cohort.eq('original')]
        if len(original):pool=original
        if len(pool):
            iid=pool.sort_values('item_id').iloc[0].item_id;category='agreement_control_'+family
            if (category,iid) not in existing:controls[iid]=dict(category=category,eligible_n=len(pool))
    with (data/'exam_v1.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            item=json.loads(line);iid=item['item_id']
            if iid not in controls:continue
            replies=json.loads(j[j.item_id.eq(iid)].to_json(orient='records',double_precision=15))
            for reply in replies:
                record=cache[reply['raw_reply_cache_key']]
                reply.update(origin=str(reply['origin']),prompt=record['request']['prompt'],raw_text=record['response']['text'],raw_response=record['response'].get('raw'))
            examples.append(dict(item_id=iid,item=item,replies=replies,selection='First original agreed-and-correct case within family, if available.',**controls[iid]))
    (data/'worked_examples.json').write_text(json.dumps(examples,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
seen=set()
code_audits=[]
for example in examples:
    item=example['item'];iid=item['item_id']
    if iid in seen:continue
    seen.add(iid)
    good=item['candidates'][item['better']]
    bad=item['candidates']['B' if item['better']=='A' else 'A']
    words_a=good['text'].split();words_b=bad['text'].split()
    changes=[op for op in difflib.SequenceMatcher(None,words_a,words_b).get_opcodes() if op[0]!='equal']
    if changes:
        _,a,b,c,d=changes[0]
        excerpt_good=' '.join(words_a[max(0,a-12):min(len(words_a),max(a,b)+12)])
        excerpt_bad=' '.join(words_b[max(0,c-12):min(len(words_b),max(c,d)+12)])
    else:
        excerpt_good=good['text'][:300];excerpt_bad=bad['text'][:300]
    check_good=good['check'];check_bad=bad['check']
    if item['family']=='instructions':
        evidence=f"Words: better {check_good['word_count']}, worse {check_bad['word_count']}. Required: {item['rules']['min_words']} to {item['rules']['max_words']}."
    elif item['family']=='code':
        evidence=f"Hidden tests: better {check_good['passed']}/{check_good['total']}; worse {check_bad['passed']}/{check_bad['total']}."
        audit=observe_existing_code_test(item);code_audits.append(audit)
        worse_label='B' if item['better']=='A' else 'A'
        evidence+=' Existing failing test input (excerpt): '+repr(audit['input'])[:120]+'. Expected '+repr(audit['expected'])[:100]+'; worse returned '+audit[worse_label].get('value_repr',audit[worse_label].get('error','unavailable'))[:100]+'.'
        if audit[worse_label].get('input_mutated'):evidence+=' The worse candidate mutated the input.'
    else:
        evidence='Exact target: '+str(item.get('exact_answer',''))[:180]
    fig,(left,right)=plt.subplots(1,2,figsize=(10,7),gridspec_kw={'width_ratios':[1.2,1]})
    left.axis('off');right.axis('off')
    body='TASK EXCERPT\n'+textwrap.fill(item['task'][:280],46)+'\n\nCHECKER\n'+textwrap.fill(evidence,46)+'\n\nBETTER ANSWER, DIFFERENCE CONTEXT\n'+textwrap.fill(excerpt_good[:260],46)+'\n\nWORSE ANSWER, DIFFERENCE CONTEXT\n'+textwrap.fill(excerpt_bad[:260],46)
    left.text(0,1,body,va='top',fontsize=10.5,transform=left.transAxes)
    verdicts=[]
    for name,condition in [('Opus','alone'),('Sol','alone'),('Haiku','reasons'),('Luna','reasons'),('Granite 8B','reasons'),('DeepSeek 763B','reasons')]:
        subset=[r for r in example['replies'] if r['judge']==name and r['condition']==condition]
        if not subset:continue
        values={r['order']:r['lenient_canonical'] or 'unreadable' for r in subset}
        verdicts.append([name,condition,values.get('AB',''),values.get('BA','')])
    if verdicts:
        tab=right.table(cellText=verdicts,colLabels=['Judge','Condition','AB order','BA order'],cellLoc='center',loc='center',colWidths=[.31,.23,.23,.23])
        tab.auto_set_font_size(False);tab.set_fontsize(9.5);tab.scale(1,2.3)
    right.set_title('Canonical verdicts in both answer orders',fontsize=10.5)
    fig.suptitle(iid+': exact checker prefers '+item['better'],fontsize=13)
    fig.tight_layout();fig.savefig(root/'figures'/('readable_case_'+iid+'.png'));plt.close(fig)
print('Readable case panels saved:',len(seen))
(data/'code_case_audits.json').write_text(json.dumps(code_audits,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
