# Reporting-only analyses added after inspecting the test results.
METHOD_NAMES = {
 'M0':'No guidance', 'M1':'Written rules', 'M2':'8 random past choices',
 'M3':'8 similar past choices', 'M4':'Distilled rubric', 'M5':'Rules + 8 random choices'}

def named_table(frame):
 frame=frame.copy()
 for col in ['method','reference']:
  if col in frame:
   frame[col+'_name']=frame[col].map(METHOD_NAMES).fillna(frame[col])
 return frame

def reader_table(frame):
 frame=frame.copy()
 for col in ['method','reference']:
  if col in frame:
   frame[col]=frame[col].map(METHOD_NAMES).fillna(frame[col])
   frame=frame.drop(columns=[col+'_name'],errors='ignore')
 if 'comparison' in frame:
  frame['comparison']=frame.comparison.map(lambda s:re.sub(r'\bM[0-5]\b',lambda m:METHOD_NAMES[m.group()],s) if isinstance(s,str) else s)
 return frame.rename(columns={**METHOD_NAMES,'m3_minus_m0':'Similar choices minus No guidance'})

def save_named_tables():
 for path in DATA.glob('*.csv'):
  frame=pd.read_csv(path)
  if 'method' in frame or 'reference' in frame:
   # Read as strings to preserve the original numeric representations.
   frame=pd.read_csv(path,dtype=str,keep_default_na=False)
   named_table(frame).to_csv(path,index=False)

def lexical_words(text):
 return re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*",text)

def mean_sentence_length(text):
 sentences=[s for s in re.split(r'[.!?]+(?:[\s\n]+|$)|\n\s*\n',text) if lexical_words(s)]
 return sum(len(lexical_words(s)) for s in sentences)/len(sentences) if sentences else 0.0

def syllables(word):
 word=re.sub('[^a-z]','',word.lower())
 if not word:return 1
 count=len(re.findall('[aeiouy]+',word))
 if word.endswith('e') and not re.search(r'[^aeiouy]le$',word) and count>1:count-=1
 return max(1,count)

def text_reporting(judgments):
 features=[]
 for p in TEST:
  row=dict(pair_id=p['pair_id'],notebook=p['notebook'])
  for side in ['before','after']:
   words=lexical_words(p[side]);row[side+'_words']=len(words)
   row[side+'_mean_sentence_words']=mean_sentence_length(p[side])
   row[side+'_polysyllables_per_100_words']=100*sum(syllables(w)>=3 for w in words)/len(words)
   row[side+'_mechanical_violations']=p[side+'_violations']
  row['length_direction']='shorter' if row['after_words']<row['before_words'] else 'longer' if row['after_words']>row['before_words'] else 'equal'
  features.append(row)
 features=pd.DataFrame(features);features.to_csv(DATA/'text_features.csv',index=False)
 features[['pair_id','notebook','before_words','after_words','length_direction']].to_csv(DATA/'length_direction.csv',index=False)
 baselines=[];decisions=[]
 for name,col in [('Pick the shorter version','words'),('Shorter mean sentence length','mean_sentence_words'),
                  ('Fewer polysyllabic words','polysyllables_per_100_words'),('Mechanical rule checker','mechanical_violations')]:
  before=features['before_'+col];after=features['after_'+col]
  correct=after<before;wrong=after>before;ties=after==before;n=len(features)
  lo,hi=wilson(int(correct.sum()),n);lo=max(0.0,lo);hi=min(1.0,hi)
  dl,dh=wilson(int(correct.sum()),int((~ties).sum()))
  baselines.append(dict(baseline=name,pairs=n,correct=int(correct.sum()),wrong=int(wrong.sum()),undecided=int(ties.sum()),
   unreadable=0,agreement=float(correct.mean()),ci_low=lo,ci_high=hi,decided=int((~ties).sum()),
   decided_agreement=float(correct.sum()/(~ties).sum()) if (~ties).sum() else np.nan,decided_ci_low=dl,decided_ci_high=dh))
  for i,r in features.iterrows():
   decisions.append(dict(pair_id=r.pair_id,baseline=name,before_value=before[i],after_value=after[i],
    choice='accepted' if correct[i] else 'earlier' if wrong[i] else 'undecided'))
 baselines=pd.DataFrame(baselines);baselines.to_csv(DATA/'text_baselines.csv',index=False)
 pd.DataFrame(decisions).to_csv(DATA/'text_baseline_decisions.csv',index=False)
 joined=judgments.merge(features[['pair_id','length_direction']],on='pair_id',validate='many_to_one')
 lengths=summarize(joined,['judge','method','length_direction']).query("parser == 'strict'").copy()
 named_table(lengths).to_csv(DATA/'agreement_by_length_direction.csv',index=False)
 sensitivity=[]
 for sample,frame in [('All 42 pairs',judgments),('Without notebook 26',judgments[~judgments.notebook.str.match(r'notebooks/26-')])]:
  scores=summarize(frame,['judge','method']).query("parser == 'strict'")
  for judge,g in frame.groupby('judge'):
   per=g.groupby(['pair_id','method']).strict_correct.mean().unstack('method')
   delta=per['M3']-per['M0'];lo,hi=ci_boot(delta)
   for r in scores[scores.judge==judge].to_dict('records'):
    r.update(sample=sample,source_groups=frame.notebook.nunique(),reference='M0',comparison='M3 minus M0',
     m3_minus_m0=float(delta.mean()),delta_ci_low=lo,delta_ci_high=hi)
    sensitivity.append(r)
 sensitivity=pd.DataFrame(sensitivity)
 named_table(sensitivity).to_csv(DATA/'sensitivity_without_26.csv',index=False)
 return features,baselines,lengths,sensitivity

def method_costs(jobs):
 rows=[]
 for job in jobs:
  rec=CACHE[digest(make_request(job['judge'],job['prompt'],job['purpose']))]
  attempts=rec['attempts'];backend=rec['request']['backend']
  usage_attempt,u=next(((i+1,a['usage']) for i,a in enumerate(attempts) if a.get('usage') and ('input_tokens' in a['usage'] or 'prompt_tokens' in a['usage'])),(0,{}))
  if backend=='claude' and 'input_tokens' in u:
   tokens=sum(u.get(k,0) or 0 for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens'])
   source='Recorded input + cache creation + cache read tokens'
  elif 'input_tokens' in u or 'prompt_tokens' in u:
   tokens=u.get('input_tokens',u.get('prompt_tokens'));source='Recorded input tokens (cached tokens included)'
  else:tokens=len(job['prompt'])/4;source='Prompt characters / 4; usage missing'
  costs=[]
  for a in attempts:
   usage=a.get('usage') or {}
   if backend=='codex':
    inp=usage.get('input_tokens',0);cached=usage.get('cached_input_tokens',0);out=usage.get('output_tokens',0)
    cost=((inp-cached)*2+cached*.1+out*10)/1e6 if usage else None
   elif backend=='claude':cost=a.get('list_cost_usd')
   else:cost=a.get('reported_usd')
   costs.append(cost)
  elapsed=(datetime.fromisoformat(attempts[-1]['collected_at'])-datetime.fromisoformat(attempts[0]['started_at'])).total_seconds()
  rows.append(dict(key=rec['key'],judge=job['judge'],method=job['method'],prompt_tokens=tokens,prompt_token_source=source,prompt_usage_attempt=usage_attempt,
   prompt_token_fallback=not bool(u),seconds=elapsed,transport_seconds=sum(a.get('latency_s',0) for a in attempts),
   attempts=len(attempts),known_cost_usd=sum(c for c in costs if c is not None),unpriced_attempts=sum(c is None for c in costs),
   cost_source='OpenRouter reported cost' if backend=='openrouter' else 'Claude CLI total_cost_usd' if backend=='claude' else 'Sol $2/$0.10/$10 per million uncached/cached input/output tokens'))
 detail=pd.DataFrame(rows);named_table(detail).to_csv(DATA/'method_cost_requests.csv',index=False)
 summary=[]
 for (judge,method),g in detail.groupby(['judge','method']):
  summary.append(dict(judge=judge,method=method,requests=len(g),mean_prompt_tokens=float(g.prompt_tokens.mean()),
   prompt_token_source='; '.join(sorted(g.prompt_token_source.unique())),prompt_token_fallback_requests=int(g.prompt_token_fallback.sum()),
   median_seconds=float(g.seconds.median()),mean_seconds=float(g.seconds.mean()),seconds_basis='First attempt start to final attempt completion, including retry waits; queue time excluded',
   dollars_per_100_judgments=float(g.known_cost_usd.sum()/len(g)*100),known_cost_usd=float(g.known_cost_usd.sum()),
   unpriced_attempts=int(g.unpriced_attempts.sum()),cost_source=g.cost_source.iloc[0],attempts=int(g.attempts.sum()),
   attempts_per_request=float(g.attempts.mean()),cost_note='Known reported/valued cost only; unpriced attempts excluded and counted separately'))
 summary=pd.DataFrame(summary);named_table(summary).to_csv(DATA/'method_cost.csv',index=False)
 return summary

print('Reporting labels, frozen-text baselines, source sensitivity and cost helpers defined.')

_original_display=display
def display(*objects,**kwargs):
 return _original_display(*(reader_table(o) if isinstance(o,pd.DataFrame) else o for o in objects),**kwargs)

def json_records(frame):
 return frame.astype(object).where(pd.notna(frame),'').to_dict('records')

def ci_boot(values,seed=SEED):
 values=np.asarray(values,dtype=float);values=values[np.isfinite(values)]
 if not len(values):return (float('nan'),float('nan'))
 rng=np.random.default_rng(seed)
 boot=values[rng.integers(0,len(values),size=(BOOTSTRAPS,len(values)))].mean(axis=1)
 return tuple(np.quantile(boot,[.025,.975]))

def wilson(k,n):
 if not n:return (float('nan'),float('nan'))
 z=1.959963984540054;p=k/n;den=1+z*z/n
 c=(p+z*z/(2*n))/den;d=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return c-d,c+d

def collect_rows(jobs):
 rows=[]
 for job in jobs:
  key=digest(make_request(job['judge'],job['prompt'],job['purpose']));rec=CACHE[key];out=rec['response'];p=LOOKUP[job['pair_id']]
  expected='B' if job['order']=='before_first' else 'A'
  row={k:job[k] for k in ['pair_id','judge','method','order','purpose']}
  row.update(key=key,notebook=p['notebook'],pair_type=p['pair_type'],expected=expected,
   before_author=p['before_author']['vendor'],after_author=p['after_author']['vendor'],
   before_words=p['before_words'],after_words=p['after_words'],prompt_chars=len(job['prompt']),attempts=len(rec['attempts']),
   latency_s=sum(a.get('latency_s',0) for a in rec['attempts']),final_latency_s=out.get('latency_s'),
   raw_reply=out.get('text',''),reported_usd=sum(a.get('reported_usd') or 0 for a in rec['attempts']),
   cli_list_cost_reported_usd=sum(a.get('list_cost_usd') or 0 for a in rec['attempts']))
  for name,lenient in [('strict',False),('lenient',True)]:
   parsed=parse_reply(out,lenient)
   row.update({name+'_'+k:v for k,v in parsed.items()})
   row[name+'_correct']=parsed['valid'] and parsed['better']==expected
   row[name+'_selected_accepted']=parsed['better']==expected if parsed['valid'] else None
  rows.append(row)
 return pd.DataFrame(rows).sort_values(['judge','method','pair_id','order']).reset_index(drop=True)

def summarize(frame,groups):
 out=[]
 for keys,g in frame.groupby(groups,dropna=False):
  if not isinstance(keys,tuple):keys=(keys,)
  for parser in ['strict','lenient']:
   valid=g[parser+'_valid'];correct=g[parser+'_correct'];n=len(g)
   per=g.assign(value=correct.astype(float)).groupby('pair_id').value.mean()
   low,high=ci_boot(per)
   both=g.groupby('pair_id').agg(correct=(parser+'_correct','all'),valid=(parser+'_valid','all'))
   bl,bh=wilson(int(both.correct.sum()),len(both))
   valid_per=g[valid].assign(value=g.loc[valid,parser+'_correct'].astype(float)).groupby('pair_id').value.mean()
   # Ratio bootstrap keeps the two orders of an item in one resampling unit.
   count=g.assign(c=correct.astype(int),v=valid.astype(int)).groupby('pair_id')[['c','v']].sum().to_numpy()
   rng=np.random.default_rng(SEED);idx=rng.integers(0,len(count),size=(BOOTSTRAPS,len(count)))
   samples=count[idx].sum(axis=1);ratios=np.divide(samples[:,0],samples[:,1],out=np.full(BOOTSTRAPS,np.nan),where=samples[:,1]>0)
   rl,rh=np.nanquantile(ratios,[.025,.975]) if np.isfinite(ratios).any() else (np.nan,np.nan)
   row=dict(zip(groups,keys));row.update(parser=parser,pairs=g.pair_id.nunique(),calls=n,readable=int(valid.sum()),
    unreadable=int((~valid).sum()),wrong=int((valid&~correct).sum()),correct=int(correct.sum()),
    agreement=float(correct.mean()),ci_low=low,ci_high=high,
    readable_agreement=float(correct.sum()/valid.sum()) if valid.sum() else np.nan,readable_ci_low=rl,readable_ci_high=rh,
    right_both=int(both.correct.sum()),right_both_agreement=float(both.correct.mean()),both_ci_low=bl,both_ci_high=bh,
    both_readable=int(both.valid.sum()),ceiling=bool(correct.mean()>=.98),floor=bool(correct.mean()<=.02))
   for failure in ['empty','no_parseable_json','schema_failure','refusal','timeout','transport_error']:
    row[failure]=int((g[parser+'_failure']==failure).sum())
   out.append(row)
 return pd.DataFrame(out)

def analyze(judgments):
 summaries=summarize(judgments,['judge','method']);summaries.to_csv(DATA/'summary.csv',index=False)
 by_type=summarize(judgments,['judge','method','pair_type']);by_type.to_csv(DATA/'summary_by_type.csv',index=False)
 by_source=summarize(judgments,['judge','method','notebook']);by_source.to_csv(DATA/'summary_by_notebook.csv',index=False)
 by_author=[]
 for col in ['before_author','after_author']:
  tab=summarize(judgments,['judge','method',col]);tab['author_side']=col;tab=tab.rename(columns={col:'author'});by_author.append(tab)
 by_author=pd.concat(by_author,ignore_index=True);by_author.to_csv(DATA/'summary_by_author.csv',index=False)
 baseline=[]
 for kind,pairs in [('all',TEST),('mechanical',[p for p in TEST if p['pair_type']=='mechanical']),('substantive',[p for p in TEST if p['pair_type']=='substantive'])]:
  n=len(pairs);correct=sum(p['after_violations']<p['before_violations'] for p in pairs)
  wrong=sum(p['after_violations']>p['before_violations'] for p in pairs);ties=n-correct-wrong;lo,hi=wilson(correct,n)
  baseline.append(dict(pair_type=kind,pairs=n,correct=correct,wrong=wrong,undecided=ties,unreadable=0,
                       agreement=correct/n if n else np.nan,decided_agreement=correct/(n-ties) if n>ties else np.nan,ci_low=lo,ci_high=hi))
 baseline=pd.DataFrame(baseline);baseline.to_csv(DATA/'baseline_summary.csv',index=False)
 comparisons=[];orders=[]
 from scipy.stats import binomtest
 for parser in ['strict','lenient']:
  per=judgments.groupby(['judge','method','pair_id'])[parser+'_correct'].mean().unstack('method')
  both=judgments.groupby(['judge','method','pair_id'])[parser+'_correct'].all().unstack('method')
  for judge in JUDGES:
   for m0,m1 in itertools.combinations(METHODS,2):
    g=per.loc[judge];delta=g[m1]-g[m0];lo,hi=ci_boot(delta)
    b=both.loc[judge];gain=int((b[m1]&~b[m0]).sum());loss=int((b[m0]&~b[m1]).sum())
    # Notebook cluster sensitivity preserves every pair within a sampled source group.
    cluster=pd.DataFrame(dict(delta=delta,notebook=[LOOKUP[i]['notebook'] for i in delta.index])).groupby('notebook').delta.agg(['sum','count']).to_numpy()
    rng=np.random.default_rng(SEED);ix=rng.integers(0,len(cluster),size=(BOOTSTRAPS,len(cluster)));z=cluster[ix].sum(axis=1)
    cl,ch=np.quantile(z[:,0]/z[:,1],[.025,.975])
    comparisons.append(dict(judge=judge,parser=parser,reference=m0,method=m1,pairs=len(delta),delta=float(delta.mean()),
      ci_low=lo,ci_high=hi,source_cluster_ci_low=cl,source_cluster_ci_high=ch,improved_pairs=int((delta>0).sum()),
      worsened_pairs=int((delta<0).sum()),equal_pairs=int((delta==0).sum()),both_gain=gain,both_loss=loss,
      mcnemar_exact_p=binomtest(gain,gain+loss,.5).pvalue if gain+loss else 1.0))
   for method in METHODS:
    g=judgments[(judgments.judge==judge)&(judgments.method==method)]
    c=g.pivot(index='pair_id',columns='order',values=parser+'_correct')
    v=g.pivot(index='pair_id',columns='order',values=parser+'_valid')
    b=g.pivot(index='pair_id',columns='order',values=parser+'_better')
    readable=v.all(axis=1);same_choice=(c[ORDERS[0]]==c[ORDERS[1]])&readable
    delta=c['after_first'].astype(float)-c['before_first'].astype(float);lo,hi=ci_boot(delta)
    counts=g.assign(v=g[parser+'_valid'].astype(int),a=(g[parser+'_better']=='A').astype(int)).groupby('pair_id')[['a','v']].sum().to_numpy()
    rng=np.random.default_rng(SEED);idx=rng.integers(0,len(counts),size=(BOOTSTRAPS,len(counts)));z=counts[idx].sum(axis=1)
    ar=np.divide(z[:,0],z[:,1],out=np.full(BOOTSTRAPS,np.nan),where=z[:,1]>0);al,ah=np.nanquantile(ar,[.025,.975])
    orders.append(dict(judge=judge,method=method,parser=parser,pairs=len(c),both_readable=int(readable.sum()),
      consistent=int(same_choice.sum()),consistency_on_readable=float(same_choice.sum()/readable.sum()) if readable.sum() else np.nan,
      choose_A_rate=float((g[parser+'_better']=='A').sum()/g[parser+'_valid'].sum()) if g[parser+'_valid'].sum() else np.nan,
      choose_A_ci_low=al,choose_A_ci_high=ah,always_A=int(((b[ORDERS[0]]=='A')&(b[ORDERS[1]]=='A')&readable).sum()),
      always_B=int(((b[ORDERS[0]]=='B')&(b[ORDERS[1]]=='B')&readable).sum()),
      after_first_minus_before_first=float(delta.mean()),ci_low=lo,ci_high=hi,
      before_first_agreement=float(c['before_first'].mean()),after_first_agreement=float(c['after_first'].mean())))
 comparisons=pd.DataFrame(comparisons);comparisons.to_csv(DATA/'paired_comparisons.csv',index=False)
 orders=pd.DataFrame(orders);orders.to_csv(DATA/'order_summary.csv',index=False)
 reasons=[]
 for _,r in judgments.iterrows():
  if not r.lenient_valid:continue
  row=dict(pair_id=r.pair_id,judge=r.judge,method=r.method,order=r.order,selected_accepted=r.lenient_correct,reason=r.lenient_reason)
  row.update({k:bool(re.search(pattern,r.lenient_reason,re.I)) for k,pattern in REASON_CATEGORIES.items()});reasons.append(row)
 reasons=pd.DataFrame(reasons);reasons.to_csv(DATA/'reason_codes.csv',index=False)
 rs=reasons.groupby(['judge','method'])[list(REASON_CATEGORIES)].agg(['sum','mean'])
 rs.columns=['_'.join(c) for c in rs.columns];rs.reset_index().to_csv(DATA/'reason_summary.csv',index=False)
 method_scores=summaries[summaries.parser=='strict'].groupby('method').agreement.mean()
 best=method_scores.sort_values(ascending=False,kind='stable').index[0]
 hard=judgments[judgments.method==best].groupby('pair_id').agg(agreement=('strict_correct','mean'),
   wrong=('strict_correct',lambda x:int((~x).sum())),readable=('strict_valid','sum'),judgments=('strict_correct','size'))
 hard['notebook']=[LOOKUP[i]['notebook'] for i in hard.index];hard['pair_type']=[LOOKUP[i]['pair_type'] for i in hard.index]
 hard.sort_values(['agreement','pair_id']).to_csv(DATA/'hard_pairs.csv')
 method_detail=judgments.groupby(['judge','method']).agg(prompt_chars_mean=('prompt_chars','mean'),prompt_chars_max=('prompt_chars','max'),
   mean_latency_s=('latency_s','mean'),median_latency_s=('latency_s','median'),sum_latency_s=('latency_s','sum'),
   mean_attempts=('attempts','mean'),openrouter_usd=('reported_usd','sum'),cli_reported_list_usd=('cli_list_cost_reported_usd','sum')).reset_index()
 method_detail.to_csv(DATA/'method_resources.csv',index=False)
 candidates=[]
 ranked=list(hard.sort_values(['agreement','pair_id']).index)
 successes=hard[hard.agreement>=.75]
 if len(successes):
  median_words=np.median([LOOKUP[i]['before_words'] for i in successes.index])
  success_id=min(successes.index,key=lambda i:(abs(LOOKUP[i]['before_words']-median_words),i))
 else:success_id=hard.sort_values(['agreement','pair_id'],ascending=[False,True]).index[0]
 selected=[('end_to_end',sorted(hard.index)[0]),('typical_success',success_id)]
 selected += [('difficult_or_failure',i) for i in ranked[:4]]
 disagreement=judgments.groupby('pair_id').strict_correct.mean().sort_values(key=lambda x:(x-.5).abs())
 selected += [('disagreement',disagreement.index[0])]
 for kind,pid in selected:
  candidates.append(dict(category=kind,pair=LOOKUP[pid],best_method=best,judgments=json_records(judgments[judgments.pair_id==pid])))
 save_json('worked_examples.json',candidates)
 unreadable=json_records(judgments[~judgments.strict_valid].head(12));save_json('unreadable_examples.json',unreadable)
 save_json('headline.json',dict(test_pairs=len(TEST),train_pairs=len(TRAIN),dev_pairs=len(DEV),test_notebooks=len(SPLIT['test_notebooks']),
  training_notebooks=len(SPLIT['train_notebooks']),best_method_pooled_exploratory=best,
  pooled_method_agreement=method_scores.to_dict(),test_judgments=len(judgments),
  strict_unreadable=int((~judgments.strict_valid).sum()),lenient_unreadable=int((~judgments.lenient_valid).sum()),
  strict_wrong=int((judgments.strict_valid&~judgments.strict_correct).sum()),
  lenient_wrong=int((judgments.lenient_valid&~judgments.lenient_correct).sum())))
 display(summaries[summaries.parser=='strict'][['judge','method','pairs','correct','wrong','unreadable','agreement','ci_low','ci_high','readable_agreement','right_both_agreement']].round(3))
 return summaries,by_type,baseline,comparisons,orders,reasons


def plot_results(judgments,summaries,by_type,baseline,comparisons,orders,reasons):
 import textwrap
 markers=['o','s','^','D']
 labels=[textwrap.fill(METHOD_NAMES[m],18) for m in METHODS]
 def ticks(ax,methods=METHODS):
  ax.set_xticks(range(len(methods)),[textwrap.fill(METHOD_NAMES[m],18) for m in methods],rotation=25,ha='right')
  ax.set_xlabel('Guidance method')
 def save(fig,name):
  fig.tight_layout();fig.savefig(FIG/name);plt.close(fig)
 fig,axes=plt.subplots(2,2,figsize=(13,10),sharey=True)
 for ax,judge in zip(axes.flat,JUDGES):
  for parser,marker,ls in [('strict','o','-'),('lenient','x','--')]:
   g=summaries[(summaries.judge==judge)&(summaries.parser==parser)].set_index('method').loc[METHODS]
   ax.errorbar(range(6),100*g.agreement,yerr=[100*(g.agreement-g.ci_low),100*(g.ci_high-g.agreement)],fmt=marker,ls=ls,capsize=3,label=parser.capitalize())
  ax.axhline(50,color='#777',ls=':',label='50% reference')
  ax.set(title=judge,ylim=(0,105),ylabel='Agreement with accepted text (%)');ticks(ax)
 axes.flat[0].legend(fontsize=10,loc='lower left')
 fig.suptitle('Similar past choices raised Opus 5.5 and GPT-6.1 Sol agreement;\nHaiku and Qwen stayed near chance',fontsize=15)
 save(fig,'agreement.png')
 fig,ax=plt.subplots(figsize=(12,6))
 g=comparisons[(comparisons.parser=='strict')&(comparisons.reference=='M0')]
 for i,(judge,marker) in enumerate(zip(JUDGES,markers)):
  s=g[g.judge==judge].set_index('method').loc[METHODS[1:]];x=np.arange(5)+(i-1.5)*.12
  ax.errorbar(x,100*s.delta,yerr=[100*(s.delta-s.ci_low),100*(s.ci_high-s.delta)],fmt=marker,capsize=3,label=judge)
 ax.axhline(0,color='black',ls='--');ticks(ax,METHODS[1:])
 ax.set(ylabel='Change versus No guidance (percentage points)',title='Clear gains from past choices were confined to Opus 5.5 and Sol')
 ax.legend(fontsize=10);save(fig,'paired_changes.png')
 fig,axes=plt.subplots(2,2,figsize=(11,9),sharey=True)
 for ax,judge in zip(axes.flat,JUDGES):
  for method,marker,ls in [('M0','o','-'),('M3','s','--')]:
   g=length_agreement[(length_agreement.judge==judge)&(length_agreement.method==method)].set_index('length_direction').reindex(['shorter','longer'])
   ax.errorbar([0,1],100*g.agreement,yerr=[100*(g.agreement-g.ci_low),100*(g.ci_high-g.agreement)],fmt=marker,ls=ls,capsize=4,label=METHOD_NAMES[method])
  ax.plot([0,1],[100,0],marker='X',ls=':',color='#555',label='Pick the shorter version')
  counts=text_features.length_direction.value_counts()
  ax.set(title=judge,xticks=[0,1],xticklabels=[f'Accepted shorter\n({counts.get("shorter",0)} pairs)',f'Accepted longer\n({counts.get("longer",0)} pairs)'],
   ylim=(-5,105),ylabel='Strict agreement, both orders (%)',xlabel='Accepted version relative to earlier version')
 axes.flat[0].legend(fontsize=9,loc='lower left')
 fig.suptitle('All four judges agreed more often when the accepted passage was longer\nunder No guidance and 8 similar past choices',fontsize=14)
 save(fig,'length_direction.png')
 fig,axes=plt.subplots(1,2,figsize=(14,6))
 for judge,marker in zip(JUDGES,markers):
  g=orders[(orders.judge==judge)&(orders.parser=='strict')].set_index('method').loc[METHODS]
  axes[0].plot(range(6),100*g.consistency_on_readable,marker=marker,label=judge)
  axes[1].plot(range(6),100*(1-g.choose_A_rate),marker=marker,label=judge)
 axes[0].set(title='Opus 5.5 and Sol usually kept their choice\nwhen the order flipped',ylabel='Same text in both readable orders (%)',ylim=(0,105))
 axes[1].axhline(50,color='#777',ls=':')
 axes[1].set(title='Haiku and Qwen favoured\nthe second version shown',ylabel='Second version chosen among readable replies (%)',ylim=(0,100))
 for ax in axes:ticks(ax)
 axes[0].legend(fontsize=9,loc='lower left');save(fig,'order_bias.png')
 reason_mean=reasons.groupby('method')[list(REASON_CATEGORIES)].mean().reindex(METHODS)
 fig,ax=plt.subplots(figsize=(12,5));im=ax.imshow(reason_mean.T*100,vmin=0,vmax=100,cmap='Blues',aspect='auto')
 for i in range(len(REASON_CATEGORIES)):
  for j in range(6):
   value=100*reason_mean.iloc[j,i];ax.text(j,i,f'{value:.0f}%',ha='center',va='center',color='white' if value>65 else 'black')
 ax.set(yticks=range(len(REASON_CATEGORIES)),yticklabels=[x.replace('_',' ') for x in REASON_CATEGORIES],title='Judges most often cited plain wording and structure');ticks(ax)
 fig.colorbar(im,ax=ax,label='Readable reasons mentioning category (%)');save(fig,'reason_categories.png')
 fig,axes=plt.subplots(1,2,figsize=(14,6))
 for judge,marker in zip(JUDGES,markers):
  g=method_cost[method_cost.judge==judge].set_index('method').loc[METHODS]
  axes[0].plot(range(6),g.mean_prompt_tokens,marker=marker,label=judge)
  axes[1].plot(range(6),g.dollars_per_100_judgments,marker=marker,label=judge)
 axes[0].set(ylabel='Mean prompt tokens per judgment')
 axes[1].set(ylabel='List-price dollars per 100 judgments\n(USD, known cost; log scale)',yscale='log')
 for ax in axes:ticks(ax)
 axes[0].legend(fontsize=9);axes[1].legend(fontsize=9)
 fig.suptitle('Examples lengthened prompts; Opus had the highest cost per judgment',fontsize=15)
 save(fig,'method_time.png')
 example_titles={
  'p35_013acf7a7ae6e42b':'Opus and Sol chose the accepted passage in both orders',
  'p35_247121cf9fd8fe1e':'Opus and Haiku chose the accepted passage in both orders',
  'p35_423116db367e7c1c':'All three CLI judges preferred the earlier caption in both orders'}
 for ex in read_json('worked_examples.json')[:3]:
  p=ex['pair'];g=judgments[(judgments.pair_id==p['pair_id'])&(judgments.method==ex['best_method'])]
  counts=g.groupby('judge').strict_correct.sum()
  texts=['\n\n'.join(textwrap.fill(re.sub(r'\s+',' ',s),56) for s in p[side].split('\n\n')) for side in ['before','after']]
  lines=max(t.count('\n')+1 for t in texts);height=max(2.2,lines*.235+1.05)
  fig=plt.figure(figsize=(14,height))
  axes=[fig.add_axes([left,.37/height,.465,(height-1.05)/height]) for left in [.015,.52]]
  for ax,side,text in zip(axes,['before','after'],texts):
   ax.text(0,1,text,ha='left',va='top',fontsize=14,transform=ax.transAxes)
   ax.set_title('Earlier version' if side=='before' else 'Accepted version',fontsize=14);ax.axis('off')
  fig.suptitle(p['pair_id']+': '+example_titles.get(p['pair_id'],f'Accepted passage chosen in both orders by {int((counts==2).sum())} of four judges'),fontsize=14)
  fig.text(.05,.01,'8 similar past choices; accepted choices out of 2 orders: '+'; '.join(f'{j}: {int(counts.get(j,0))}/2' for j in JUDGES),fontsize=11)
  fig.savefig(FIG/('example_'+p['pair_id']+'.png'));plt.close(fig)
 print('Saved nine reporting figures; display cells appear beside their sections.')

def costs_and_validation(jobs,judgments):
 usage=[]
 job_by_key={digest(make_request(j['judge'],j['prompt'],j['purpose'])):j for j in jobs}
 for rel in ['development_judgments.csv','pre_freeze_v0/smoke_judgments.csv']:
  path=DATA/rel
  if path.exists():
   for r in pd.read_csv(path).to_dict('records'):job_by_key.setdefault(r['key'],r)
 for key,record in CACHE.items():
  for i,a in enumerate(record['attempts']):
   req=record['request'];u=a.get('usage',{}) or {};backend=req['backend']
   inp=u.get('input_tokens',u.get('prompt_tokens',0)) or 0;out=u.get('output_tokens',u.get('completion_tokens',0)) or 0
   cached=u.get('cached_input_tokens',u.get('cache_read_input_tokens',0)) or 0
   estimate=a.get('list_cost_usd')
   if backend=='codex':estimate=((inp-cached)*2+cached*.1+out*10)/1e6 if u else None
   job=job_by_key.get(key,{})
   usage.append(dict(key=key,judge=req['judge'],model=req['model'],backend=backend,purpose=req['purpose'],
     method=job.get('method',''),pair_id=job.get('pair_id',''),attempt=i+1,input_tokens=inp,output_tokens=out,cached_input_tokens=cached,
     reported_usd=a.get('reported_usd'),reserved_usd=a.get('reserved_usd',0),cli_estimated_list_usd=estimate,cli_unpriced_attempt=(backend!='openrouter' and estimate is None),
     latency_s=a.get('latency_s',0),started_at=a.get('started_at'),collected_at=a.get('collected_at'),error=a.get('error'),pending=a.get('pending',False)))
 usage=pd.DataFrame(usage).sort_values(['key','attempt']).reset_index(drop=True);usage.to_csv(DATA/'request_usage.csv',index=False)
 group=usage.groupby(['judge','model','backend','purpose','method'],dropna=False).agg(calls=('key','size'),requests=('key','nunique'),
   input_tokens=('input_tokens','sum'),output_tokens=('output_tokens','sum'),openrouter_usd=('reported_usd','sum'),
   cli_estimated_list_usd=('cli_estimated_list_usd','sum'),cli_unpriced_attempts=('cli_unpriced_attempt','sum'),total_latency_s=('latency_s','sum'),mean_latency_s=('latency_s','mean')).reset_index()
 group.to_csv(DATA/'cost_summary.csv',index=False)
 or_rows=usage[usage.backend=='openrouter'];cli_rows=usage[usage.backend!='openrouter']
 spend=dict(openrouter_reported_usd=float(or_rows.reported_usd.sum()),openrouter_charged_or_reserved_usd=or_spend_bound(),
   openrouter_cap_usd=MAX_OPENROUTER_USD,cli_calls=len(cli_rows),cli_estimated_list_usd=float(cli_rows.cli_estimated_list_usd.sum()),
   total_attempts=len(usage),requests=len(CACHE),new_attempts_this_execution=NEW_CALLS,cli_unpriced_attempts=int(cli_rows.cli_unpriced_attempt.sum()),
   summed_request_latency_s=float(usage.latency_s.sum()),
   note='CLI list-price estimates are known-token valuations, not subscription invoices; attempts without usage are unpriced and counted separately. Codex uses $2/$0.10/$10 per million uncached input/cached input/output tokens. Claude uses CLI-reported total_cost_usd.')
 save_json('spend.json',spend);display(group.round(4));print(json.dumps(spend,indent=2))
 freeze=read_json('freeze.json')
 validation=dict(offline_replay=not LIVE,new_calls=NEW_CALLS,zero_live_calls_on_replay=(not LIVE and NEW_CALLS==0),
  cache_keys_valid=all(r['key']==digest(r['request']) for r in CACHE.values()),
  frozen_files_match=all(file_hash(DATA/p)==h for p,h in freeze['files'].items()),
  judgments_expected=len(TEST)*len(JUDGES)*len(METHODS)*2,judgments_actual=len(judgments),
  no_duplicate_judgments=not judgments.duplicated(['pair_id','judge','method','order']).any(),
  train_test_notebooks_disjoint=not bool(set(SPLIT['train_notebooks'])&set(SPLIT['test_notebooks'])),
  all_requests_complete=all(CACHE[digest(make_request(j['judge'],j['prompt'],j['purpose']))]['complete'] for j in jobs),
  openrouter_cap_passed=or_spend_bound()<=MAX_OPENROUTER_USD,
  no_pending_attempts=not any(a.get('pending') for r in CACHE.values() for a in r['attempts']))
 assert validation['cache_keys_valid'] and validation['frozen_files_match'] and validation['no_duplicate_judgments']
 assert validation['judgments_expected']==validation['judgments_actual'] and validation['all_requests_complete'] and validation['no_pending_attempts']
 if not LIVE:assert validation['zero_live_calls_on_replay']
 save_json('validation.json',validation);print(json.dumps(validation,indent=2))
 return usage,spend,validation

print('Scoring, interval, analysis and plotting helpers defined.')