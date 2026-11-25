def wilson(k, n):
    if not n:
        return (float('nan'), float('nan'))
    z = 1.959963984540054
    p = k / n
    den = 1 + z*z/n
    mid = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return mid-half, mid+half

def interval(values, label):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return (np.nan, np.nan)
    rng = np.random.default_rng(int(digest([SEED, label])[:16], 16))
    boot = a[rng.integers(0, len(a), size=(BOOTSTRAPS, len(a)))].mean(axis=1)
    return tuple(np.quantile(boot, [.025, .975]))

def collapse_method(item, method, index, reader):
    def rows(name, condition='alone'):
        return [index[(item['item_id'], condition, name, order)] for order in ['AB', 'BA']]
    if method.startswith('alone:') or method.startswith('reasons:'):
        condition, name = method.split(':', 1)
        return pair_state(rows(name, condition), reader)
    if method.startswith('trust:'):
        return pair_state(rows(method.split(':', 1)[1]), reader)
    if method in ['revise', 'revise+human']:
        a, b = [pair_state(rows(n, 'revise'), reader) for n in STRONG]
        return 'missing' if 'missing' in (a,b) else a if a in ('A', 'B') and a == b else 'unresolved'
    if method == 'confidence':
        winners = []
        for order in ['AB', 'BA']:
            a, b = [index[(item['item_id'], 'alone', n, order)] for n in STRONG]
            if a[reader+'_canonical'] is None or b[reader+'_canonical'] is None:
                return 'missing'
            ca, cb = a[reader+'_confidence'], b[reader+'_confidence']
            winners.append(a[reader+'_canonical'] if a[reader+'_canonical']==b[reader+'_canonical'] or ca > cb else b[reader+'_canonical'] if cb > ca else 'split')
        return winners[0] if winners[0] == winners[1] else 'split'
    return 'human' if method == 'human' else 'split'

def method_calls(method, iid, index):
    if method.startswith(('alone:', 'reasons:')):
        condition, name = method.split(':', 1)
        return [index[(iid, condition, name, o)] for o in ['AB', 'BA']]
    if method in ['revise', 'revise+human']:
        return [index[(iid, 'revise', n, o)] for n in STRONG for o in ['AB', 'BA']]
    return []

def item_outcomes(items, rows, routes):
    index = {(r['item_id'], r['condition'], r['judge'], r['order']): r for r in rows}
    byid = {i['item_id']: i for i in items}
    methods = ['alone:'+n for n in [*WEAK, 'Decisions', *THIRD]] + ['reasons:'+n for n in WEAK] + ['revise', 'revise+human', 'confidence', 'trust:Opus', 'trust:Sol', 'coin', 'human']
    out = []
    for route in routes:
        iid = route['item_id']
        item = byid[iid]
        base_calls = [index[(iid, 'alone', n, o)] for n in STRONG for o in ['AB', 'BA']]
        for reader in ['lenient', 'strict']:
            for method in methods:
                state = None
                extra = []
                if route['route'] == 'disagreed':
                    state = collapse_method(item, method, index, reader)
                    extra = method_calls(method, iid, index)
                elif route['route'] == 'agreed':
                    a, b = [pair_state([index[(iid, 'alone', n, o)] for o in ['AB', 'BA']], reader) for n in STRONG]
                    state = a if a in ('A', 'B') and a == b else 'missing'
                else:
                    state = 'human'
                for variant in ['failure', 'coin']:
                    unread = state == 'missing'
                    unresolved = state == 'unresolved'
                    person = state == 'human' or ((unresolved or unread) and method == 'revise+human' and route['route']=='disagreed')
                    score = 1. if person else .5 if state == 'split' or (unread and variant == 'coin') else float(state == item['better'])
                    out.append(dict(**route, reader=reader, method=method, unreadable_policy=variant, state=state,
                                    score=score, readable=not unread and not unresolved,
                                    wrong=int(state in ('A', 'B') and state != item['better']), unreadable=int(unread),
                                    split=int(state == 'split'), unresolved=int(unresolved), human_reviews=int(person),
                                    logical_calls=4+len(extra), extra_logical_calls=len(extra),
                                    model_attempts=sum(r['attempts'] for r in base_calls+extra),
                                    incremental_model_attempts=sum(r['attempts'] for r in base_calls+extra if r['origin']=='34'),
                                    model_cost_usd=sum(r['cost_usd'] for r in base_calls+extra),
                                    cli_estimated_list_usd=sum(r['cli_estimated_list_usd'] for r in base_calls+extra),
                                    extra_cost_usd=sum(r['cost_usd'] for r in extra),
                                    extra_cli_estimated_list_usd=sum(r['cli_estimated_list_usd'] for r in extra)))
    return pd.DataFrame(out)

def score_summary(frame, groupcols, label):
    result = []
    for keys, g in frame.groupby(groupcols, dropna=False, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        d = dict(zip(groupcols, keys))
        lo, hi = interval(g.score, label+str(keys))
        readable = g[g.readable]
        d.update(n=len(g), expected_correct=g.score.sum(), accuracy=g.score.mean(), ci_low=lo, ci_high=hi,
                 wrong=int(g.wrong.sum()), unreadable=int(g.unreadable.sum()), splits=int(g.split.sum()),
                 unresolved=int(g.unresolved.sum()), readable_n=len(readable),
                 readable_accuracy=readable.score.mean(), human_reviews=int(g.human_reviews.sum()),
                 logical_calls=int(g.logical_calls.sum()), model_attempts=int(g.model_attempts.sum()),
                 incremental_model_attempts=int(g.incremental_model_attempts.sum()),
                 model_cost_usd=g.model_cost_usd.sum(), cli_estimated_list_usd=g.cli_estimated_list_usd.sum(),
                 extra_logical_calls=int(g.extra_logical_calls.sum()), extra_cost_usd=g.extra_cost_usd.sum(),
                 extra_cli_estimated_list_usd=g.extra_cli_estimated_list_usd.sum(), sparse=len(g)<10,
                 ceiling=bool(g.score.eq(1).all()), floor=bool(g.score.eq(0).all()))
        result.append(d)
    return pd.DataFrame(result)

def summarize_study(items, rows, routes):
    j = pd.DataFrame(rows)
    r = pd.DataFrame(routes)
    outcomes = item_outcomes(items, rows, routes)
    expanded = pd.concat([outcomes.assign(report_cohort='all'), outcomes.assign(report_cohort=outcomes.cohort)], ignore_index=True)
    group = ['report_cohort', 'reader', 'unreadable_policy', 'method']
    tables = dict(item_outcomes=outcomes, full_rules=score_summary(expanded, group, 'full'),
                  tie_breakers=score_summary(expanded[expanded.route.eq('disagreed')], group, 'ties'),
                  family_results=score_summary(expanded[expanded.route.eq('disagreed')], group+['family'], 'family'),
                  trap_results=score_summary(expanded[expanded.route.eq('disagreed')], group+['trap'], 'trap'))
    raw = []
    for reader in ['lenient', 'strict']:
        for keys, g in j.groupby(['cohort', 'condition', 'judge']):
            read = g[reader+'_canonical'].notna()
            correct = g[reader+'_correct'].eq(True)
            peritem=g.assign(_score=correct.astype(float)).groupby('item_id')._score.mean()
            lo, hi = interval(peritem, 'reply'+reader+str(keys))
            raw.append(dict(cohort=keys[0], condition=keys[1], judge=keys[2], reader=reader, judgments=len(g), correct=int(correct.sum()),
                            wrong=int((read & ~correct).sum()), unreadable=int((~read).sum()), accuracy=correct.mean(),
                            readable_accuracy=correct[read].mean(), readable_n=int(read.sum()), ci_low=lo, ci_high=hi))
    tables['reply_summary'] = pd.DataFrame(raw)
    diagnostics = []
    for reader in ['lenient', 'strict']:
        x = j[j[reader+'_canonical'].isna()]
        for keys, g in x.groupby(['cohort', 'condition', 'judge', reader+'_unreadable_type', 'diagnostic_subtype'], dropna=False):
            diagnostics.append(dict(cohort=keys[0], condition=keys[1], judge=keys[2], reader=reader,
                                    unreadable_type=keys[3], diagnostic_subtype=keys[4], count=len(g), sample_key=g.iloc[0].raw_reply_cache_key))
    tables['unreadable_summary'] = pd.DataFrame(diagnostics)
    route_summary = []
    for cohort, x in [('original', r[r.cohort.eq('original')]), ('new', r[r.cohort.eq('new')]), ('all', r)]:
        for family in ['all', *FAMILIES]:
            g = x if family=='all' else x[x.family.eq(family)]
            agreed = g[g.route.eq('agreed')]
            wrong = int(agreed.agreed_correct.eq(False).sum())
            bound = wilson(wrong, len(agreed))[1]
            route_summary.append(dict(cohort=cohort, family=family, items=len(g), agreed=len(agreed), disagreements=int(g.route.eq('disagreed').sum()),
                                      missing=int(g.route.eq('missing').sum()), opus_split=int(g.opus_state.eq('split').sum()), sol_split=int(g.sol_state.eq('split').sum()),
                                      agreed_both_wrong=wrong, agreed_error_95_upper=bound,
                                      disagreement_family_share=(int(g.route.eq('disagreed').sum()) / max(1, int(x.route.eq('disagreed').sum())))))
    tables['route_summary'] = pd.DataFrame(route_summary)
    comparisons = []
    pairs = [('reasons:'+n, 'alone:'+n) for n in WEAK]
    pairs += [(m, 'coin') for m in outcomes.method.unique() if m not in ('coin', 'human')]
    pairs += [('alone:Muse', 'trust:Opus'), ('alone:Sonnet', 'trust:Sol'), ('revise+human', 'human')]
    for cohort in ['original', 'new', 'all']:
        for reader in ['lenient', 'strict']:
            for policy in ['failure', 'coin']:
                selected = outcomes[(outcomes.route=='disagreed') & (outcomes.reader==reader) & (outcomes.unreadable_policy==policy)]
                if cohort != 'all':
                    selected = selected[selected.cohort==cohort]
                wide = selected.pivot(index='item_id', columns='method', values='score')
                for a,b in pairs:
                    if a not in wide or not len(wide):
                        continue
                    delta = wide[a]-wide[b]
                    lo,hi = interval(delta, str([cohort,reader,policy,a,b]))
                    comparisons.append(dict(cohort=cohort, reader=reader, unreadable_policy=policy, method_a=a, method_b=b, n=len(delta),
                                            accuracy_difference=delta.mean(), ci_low=lo, ci_high=hi, a_better=int((delta>0).sum()), b_better=int((delta<0).sum()), equal=int((delta==0).sum())))
    tables['paired_comparisons'] = pd.DataFrame(comparisons)
    index = {(x['item_id'],x['condition'],x['judge'],x['order']):x for x in rows}
    persuasive = []
    revisions = []
    for row in rows:
        if row['condition']=='reasons':
            a,b = [index[(row['item_id'],'alone',n,row['order'])] for n in [row['judge1_name'],row['judge2_name']]]
            wa,wb = a['lenient_canonical'], b['lenient_canonical']
            w = row['lenient_canonical']
            informative = wa is not None and wb is not None and wa != wb
            longer = wa if len(a['lenient_reason'])>len(b['lenient_reason']) else wb if len(a['lenient_reason'])<len(b['lenient_reason']) else None
            confident = wa if a['lenient_confidence']>b['lenient_confidence'] else wb if a['lenient_confidence']<b['lenient_confidence'] else None
            persuasive.append(dict(item_id=row['item_id'], cohort=row['cohort'], family=row['family'], judge=row['judge'], order=row['order'], informative=informative,
                                   readable=w is not None, judge1=row['judge1_name'], judge2=row['judge2_name'], judge1_winner=wa, judge2_winner=wb,
                                   judge1_reason_chars=len(a['lenient_reason']), judge2_reason_chars=len(b['lenient_reason']),
                                   judge1_confidence=a['lenient_confidence'], judge2_confidence=b['lenient_confidence'],
                                   correct=None if w is None else w==row['better'], sided_correct_judge=None if not informative or w is None else w==row['better'],
                                   followed_first=None if not informative or w is None else w==wa,
                                   followed_longer=None if not informative or w is None or longer is None else w==longer,
                                   longer_was_correct=None if not informative or longer is None else longer==row['better'],
                                   followed_confident=None if not informative or w is None or confident is None else w==confident,
                                   confident_was_correct=None if not informative or confident is None else confident==row['better'],
                                   raw_reply_cache_key=row['raw_reply_cache_key']))
        if row['condition']=='revise':
            old=index[(row['item_id'],'alone',row['judge'],row['order'])]
            peer=index[(row['item_id'],'alone','Sol' if row['judge']=='Opus' else 'Opus',row['order'])]
            revisions.append(dict(item_id=row['item_id'], cohort=row['cohort'], family=row['family'], judge=row['judge'], order=row['order'],
                                  old=old['lenient_canonical'], revised=row['lenient_canonical'], peer=peer['lenient_canonical'],
                                  readable=row['lenient_canonical'] is not None, moved=None if row['lenient_canonical'] is None else row['lenient_canonical']!=old['lenient_canonical'],
                                  improved=old['lenient_correct'] is False and row['lenient_correct'] is True,
                                  harmed=old['lenient_correct'] is True and row['lenient_correct'] is False))
    tables['reasons_alignment'] = pd.DataFrame(persuasive)
    tables['revision_moves'] = pd.DataFrame(revisions)
    alignment=[]
    if persuasive:
        for judge,g in tables['reasons_alignment'].groupby('judge'):
            for metric in ['sided_correct_judge','followed_first','followed_longer','followed_confident']:
                values=g[g[metric].notna()]
                # Cluster displayed-order outcomes by item before the interval.
                peritem=values.groupby('item_id')[metric].mean().astype(float)
                lo,hi=interval(peritem,judge+metric)
                alignment.append(dict(judge=judge,metric=metric,orders=len(values),items=len(peritem),share=values[metric].astype(float).mean(),ci_low=lo,ci_high=hi))
    tables['reasons_alignment_summary']=pd.DataFrame(alignment)
    for name,table in tables.items():
        table.to_csv(DATA/(name+'.csv'),index=False)
    return tables

def spend_tables():
    records=[]
    for row in [*CACHE.values(), *NONFINAL]:
        if row.get('origin'):
            continue
        req,o=row['request'],row['response']
        estimate,basis=cli_estimate(row)
        records.append(dict(key=row['key'],model=req['model'],backend=req['backend'],purpose=req['purpose'],attempt=req['attempt'],
                            started_at=o.get('started_at'),completed_at=o.get('completed_at'),status=o.get('status'),finish_reason=o.get('finish_reason'),
                            openrouter_usd=float(o.get('cost') or 0),unpriced_reservation_usd=float(o.get('unpriced_reservation') or 0),
                            cli_estimated_list_usd=float(estimate or 0) if req['backend'] in OPTIONS else 0.,
                            cli_price_basis=basis,latency_s=o.get('latency_s',0),disposition=row.get('disposition','final_cached_attempt')))
    ledger=pd.DataFrame(records)
    ledger.to_csv(DATA/'usage_ledger.csv',index=False)
    if len(ledger):
        spend=ledger.groupby(['model','backend'],as_index=False).agg(calls=('key','size'),openrouter_usd=('openrouter_usd','sum'),unpriced_reservation_usd=('unpriced_reservation_usd','sum'),cli_estimated_list_usd=('cli_estimated_list_usd','sum'),latency_s=('latency_s','sum'))
    else:
        spend=pd.DataFrame()
    spend.to_csv(DATA/'spend_by_model.csv',index=False)
    return ledger,spend

def figures34(tables):
    t=tables['tie_breakers']
    g=t[(t.report_cohort=='all')&(t.reader=='lenient')&(t.unreadable_policy=='failure')].sort_values('accuracy')
    fig,ax=plt.subplots(figsize=(11,8))
    y=np.arange(len(g))
    ax.errorbar(g.accuracy,y,xerr=[g.accuracy-g.ci_low,g.ci_high-g.accuracy],fmt='o',color='#315f9c',capsize=3,label='Unreadable = failure')
    coin=t[(t.report_cohort=='all')&(t.reader=='lenient')&(t.unreadable_policy=='coin')].set_index('method').reindex(g.method)
    ax.scatter(coin.accuracy,y,marker='x',color='#ac5832',label='Unreadable = expected coin')
    ax.set(yticks=y,yticklabels=g.method,xlim=(-.03,1.03),xlabel='Expected correct share of disagreement items',title=f'Tie-breaker accuracy varies on {int(g.n.iloc[0])} strong-judge disagreements')
    ax.axvline(.5,ls='--',color='grey',lw=1);ax.legend(loc='lower right');fig.tight_layout();fig.savefig(FIG/'headline.png');plt.close(fig)
    weak=[*WEAK]
    fig,ax=plt.subplots(figsize=(10,5))
    for offset,condition,marker,color in [(-.13,'alone','o','#315f9c'),(.13,'reasons','s','#ac5832')]:
        a=t[(t.report_cohort=='all')&(t.reader=='lenient')&(t.unreadable_policy=='failure')].set_index('method').reindex([condition+':'+n for n in weak])
        ax.errorbar(np.arange(4)+offset,a.accuracy,yerr=[a.accuracy-a.ci_low,a.ci_high-a.accuracy],fmt=marker,color=color,capsize=3,label=condition)
    ax.set(xticks=range(4),xticklabels=weak,ylabel='Expected correct share (unreadable = failure)',ylim=(-.03,1.03),title='Reading strong reasons changes weak-judge accuracy');ax.legend();fig.tight_layout();fig.savefig(FIG/'reasons_vs_alone.png');plt.close(fig)
    r=tables['route_summary'];g=r[(r.cohort=='all')&(r.family!='all')]
    fig,ax=plt.subplots(figsize=(9,4.5));x=np.arange(len(g))
    ax.bar(x,g.agreed,label='Agreed',color='#315f9c',hatch='//');ax.bar(x,g.disagreements,bottom=g.agreed,label='Disagreed',color='#ac5832',hatch='xx')
    if g.missing.sum():ax.bar(x,g.missing,bottom=g.agreed+g.disagreements,label='Missing',color='grey',hatch='..')
    for pos,row in enumerate(g.itertuples()):ax.text(pos,row.items+2,f'{row.disagreements}/{row.items} disagree',ha='center',fontsize=9)
    ax.set(xticks=x,xticklabels=g.family,ylabel='Items',title='Disagreements are concentrated in particular task families');ax.legend();fig.tight_layout();fig.savefig(FIG/'disagreement_families.png');plt.close(fig)
    f=tables['full_rules'];g=f[(f.report_cohort=='all')&(f.reader=='lenient')&(f.unreadable_policy=='failure')].sort_values('accuracy')
    fig,(ax,cost_ax)=plt.subplots(1,2,figsize=(13,8),sharey=True,gridspec_kw={'width_ratios':[1.1,1.2]})
    y=np.arange(len(g))
    ax.errorbar(g.accuracy,y,xerr=[g.accuracy-g.ci_low,g.ci_high-g.accuracy],fmt='o',color='#315f9c',capsize=3)
    ax.set(yticks=y,yticklabels=g.method,xlim=(-.02,1.03),xlabel='Expected full-rule accuracy')
    cost_ax.barh(y,g.logical_calls,color='#ac5832',hatch='//',height=.6)
    for pos,row in enumerate(g.itertuples()):cost_ax.text(row.logical_calls+max(g.logical_calls)*.025,pos,f'{row.human_reviews} reviews',va='center',fontsize=8)
    cost_ax.set(xlabel='Logical model calls (four base calls per item)',xlim=(0,max(g.logical_calls)*1.35))
    fig.suptitle('Full-rule accuracy, model calls and human reviews differ by tie-breaker');fig.tight_layout();fig.savefig(FIG/'full_rule_cost.png');plt.close(fig)
    q=tables['reply_summary'];g=q[q.reader=='lenient'].groupby(['condition','judge'],as_index=False)[['correct','wrong','unreadable']].sum()
    fig,ax=plt.subplots(figsize=(11,8));bottom=np.zeros(len(g))
    for col,color,hatch in [('correct','#315f9c',''),('wrong','#ac5832','xx'),('unreadable','#a9b1ba','//')]:
        ax.barh(np.arange(len(g)),g[col],left=bottom,color=color,hatch=hatch,label=col);bottom+=g[col].to_numpy()
    ax.set(yticks=range(len(g)),yticklabels=g.condition+': '+g.judge,xlabel='Displayed-order judgments',title='Wrong verdicts and unreadable replies have different causes');ax.legend();fig.tight_layout();fig.savefig(FIG/'reply_outcomes.png');plt.close(fig)
    print('Saved figures:',len(list(FIG.glob('*.png'))))

def worked_cases(items, rows, routes, tables):
    byid={i['item_id']:i for i in items}
    outcomes=tables['item_outcomes'];x=outcomes[(outcomes.reader=='lenient')&(outcomes.unreadable_policy=='failure')&(outcomes.route=='disagreed')]
    selection=[]
    for name,condition in [('reasons_helped',lambda a,b:a==1 and b<1),('reasons_harmed',lambda a,b:a==0 and b>0)]:
        for model in WEAK:
            wide=x[x.method.isin(['reasons:'+model,'alone:'+model])].pivot(index='item_id',columns='method',values='score')
            eligible=[iid for iid,row in wide.iterrows() if condition(row['reasons:'+model],row['alone:'+model])]
            if eligible:selection.append(dict(category=name,model=model,item_id=eligible[0],eligible_n=len(eligible)))
    for route in routes:
        if route['route']=='agreed' and not route['agreed_correct']:
            selection.append(dict(category='both_agreed_wrong',item_id=route['item_id'],eligible_n=sum(r['route']=='agreed' and not r['agreed_correct'] for r in routes)));break
    for family in FAMILIES:
        eligible=[r for r in routes if r['route']=='disagreed' and r['family']==family]
        if eligible:selection.append(dict(category='disagreement_'+family,item_id=eligible[0]['item_id'],eligible_n=len(eligible)))
    success=[r for r in routes if r['route']=='agreed' and r['agreed_correct']]
    if success:selection.append(dict(category='typical_agreement',item_id=success[0]['item_id'],eligible_n=len(success)))
    examples=[]
    for candidate in selection:
        iid=candidate['item_id'];item=byid[iid];replies=[]
        for row in rows:
            if row['item_id']!=iid:continue
            raw=CACHE[row['raw_reply_cache_key']]
            replies.append(dict(**row,prompt=raw['request']['prompt'],raw_text=raw['response']['text'],raw_response=raw['response'].get('raw')))
        examples.append(dict(**candidate,item=item,replies=replies))
    unread=[]
    seen=set()
    for row in rows:
        kind=row['lenient_unreadable_type'];key=(row['judge'],row['condition'],kind,row['diagnostic_subtype'])
        if kind and key not in seen:
            seen.add(key);raw=CACHE[row['raw_reply_cache_key']]
            unread.append(dict(**row,raw_text=raw['response']['text'],diagnostics=response_diagnostics(raw['response'])[:6000]))
    save(DATA/'worked_examples.json',examples)
    save(DATA/'unreadable_examples.json',unread)
    # Compact panels expose the actual better/worse evidence and the cached verdicts.
    import textwrap
    for example in examples[:8]:
        item=example['item'];fig,axes=plt.subplots(1,2,figsize=(12,6))
        import difflib
        good=item['candidates'][item['better']]['text']
        bad=item['candidates']['B' if item['better']=='A' else 'A']['text']
        changes=[line for line in difflib.ndiff(good.split(),bad.split()) if line.startswith(('- ','+ '))]
        for ax,label in zip(axes,['A','B']):
            candidate=item['candidates'][label];check=candidate['check']
            prefix=''
            if item['family']=='instructions':
                prefix='Words counted: '+str(check['word_count'])+'\nRules: '+canonical(check['checks'])+'\nChanged words (better -> worse): '+', '.join(changes[:8])+'\n\n'
            elif item['family']=='code':
                prefix='Hidden tests passed: '+str(check['passed'])+'/'+str(check['total'])+'\nChanged tokens: '+', '.join(changes[:12])+'\n\n'
            text='\n'.join(textwrap.wrap(prefix+candidate['text'][:1700],70))
            ax.text(0,1,text[:2800],va='top',family='monospace',fontsize=7.5,transform=ax.transAxes)
            ax.set_title(f'Answer {label}: '+('passes' if check['correct'] else 'fails')+' exact check',fontsize=11);ax.axis('off')
        fig.suptitle(example['item_id']+' | '+example['category']+' | gold '+item['better']);fig.tight_layout();fig.savefig(FIG/('case_'+example['category']+'_'+example['item_id']+'.png'));plt.close(fig)
    print('Worked-case candidates:',len(examples),'| Unreadable groups:',len(unread))

def validate34(items, rows, routes, tables):
    verify_sources()
    for name,expected in load(DATA/'freeze_record.json')['hashes'].items():
        assert filehash(DATA/name)==expected,name
    assert len(items) in (360,480,600,720),len(items)
    history=load(DATA/'stopping_history.json')
    assert history[-1]['disagreements']>=80 or history[-1]['new_items']==480
    assert all(x['disagreements']<80 for x in history[:-1])
    assert len({r['item_id'] for r in rows if r['condition']!='alone'})==sum(r['route']=='disagreed' for r in routes)
    for item in items:
        for label,c in item['candidates'].items():
            assert check_answer(item,c['text'])['correct']==(label==item['better']),item['item_id']
    if not LIVE:
        assert new_calls==0
        try:requests.get('https://example.com')
        except RuntimeError:pass
        else:raise AssertionError('Offline canary failed')
    ledger,spend=spend_tables()
    assert accounted_openrouter()<=5.
    result=dict(at=now(),mode='live' if LIVE else 'replay',items=len(items),original_items=sum(i['split']=='test' for i in items),
                new_items=sum(i['split']!='test' for i in items),disagreements=sum(r['route']=='disagreed' for r in routes),
                missing=sum(r['route']=='missing' for r in routes),judgments=len(rows),new_calls=new_calls,
                reused_judgments=sum(r['origin']=='33' for r in rows),source_hashes_valid=True,final_item_checks=2*len(items),
                openrouter_accounted_usd=accounted_openrouter(),figures=sorted(p.name for p in FIG.glob('*.png')))
    save(DATA/('live_validation.json' if LIVE else 'replay_validation.json'),result)
    print(json.dumps(result,indent=2));display(spend)
