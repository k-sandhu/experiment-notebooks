"""Source-free deterministic analysis of the three paid classifiers."""
from collections import Counter, defaultdict
import csv
import itertools
from pathlib import Path
import re
import numpy as np

import smoke_study as s
import paid_decision_study as paid
import expanded_full_analysis as lexical

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/paid_prose_comparison'
THRESHOLDS=[.2,.5,.8]
N_BOOTSTRAP=2000
SEED=20261103
WRITERS=s.MODELS
ZONES=['whole','opening_paragraph','transition_starts','point_endings','conclusion','closing']


def write_rows(path,rows,headers=None):
    iterator=iter(rows);first=next(iterator,None)
    if first is None:
        s.write_csv(path,[])
        if headers:path.write_text(','.join(headers)+'\n',encoding='utf-8',newline='\n')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(first),lineterminator='\n');writer.writeheader();writer.writerow(first)
        writer.writerows(iterator)


def effective_data():
    articles=s.load(ROOT/'data/main/articles.json');records={};texts={};strict={}
    for condition in ['baseline','expanded']:
        for article in articles:
            for writer in WRITERS:
                for turn in range(1,6):
                    key=(condition,article['item_id'],writer,turn)
                    value=paid.record_for(*key);records[key]=value['record'];texts[key]=value['text'];strict[key]=value['strict_readable']
    return articles,records,texts,strict


def phrase_analysis(articles,records,texts,strict):
    zones={key:lexical.regions(text) for key,text in texts.items()};ids=[a['item_id'] for a in articles]
    entries=s.load(ROOT/'data/prose_lexicon.json')['entries'];regex={e['id']:re.compile(e['regex'],re.I) for e in entries}
    path=OUT/'source_overlap.json';overlap=s.load(path) if path.exists() else {'topics':{}}
    for article in articles:
        item=article['item_id'];observed=set()
        for key,region in zones.items():
            if key[1]!=item:continue
            for name,text in region.items():observed.update(lexical.grams(text,name in ['transition_starts','point_endings']))
        fingerprint=s.sha('\n'.join(sorted(observed)));source_path=ROOT/article['local_input']
        if source_path.exists():
            source=source_path.read_text(encoding='utf-8');assert s.sha(source)==article['text_sha256']
            overlap['topics'][item]=dict(observed_candidates_sha256=fingerprint,source_sha256=article['text_sha256'],
                source_present_candidate_hashes=sorted(s.sha(phrase) for phrase in observed&lexical.grams(source)),
                fixed_counts={e['id']:len(regex[e['id']].findall(s.normalise(source))) for e in entries})
        else:
            assert overlap['topics'][item]['observed_candidates_sha256']==fingerprint
            assert overlap['topics'][item]['source_sha256']==article['text_sha256']
    s.save(path,overlap)
    present={item:set(v['source_present_candidate_hashes']) for item,v in overlap['topics'].items()}
    candidates={};fixed=defaultdict(lambda:[0,0,0,0,0,0,0]);metrics=[]
    for key,region in zones.items():
        condition,item,writer,turn=key;topic_bit=1<<ids.index(item)
        metrics.append(dict(condition=condition,item_id=item,model=writer,turn=turn,strict_readable=strict[key],
            input_kind='post' if strict[key] else 'exact_raw_reply',post_sha256=s.sha(texts[key]),**lexical.formatting(texts[key])))
        for name,text in region.items():
            normalized=s.normalise(text);words=len(s.words(text))
            for entry in entries:
                acc=fixed[(condition,writer,name,entry['id'])];count=len(regex[entry['id']].findall(normalized))
                acc[0]+=count>0;acc[1]+=1;acc[2]+=count;acc[3]+=words
                if count:acc[6]|=topic_bit
                if overlap['topics'][item]['fixed_counts'][entry['id']]==0:acc[4]+=count>0;acc[5]+=1
            for phrase in lexical.grams(text,name in ['transition_starts','point_endings']):
                if s.sha(phrase) in present[item]:continue
                acc=candidates.setdefault((condition,writer,name,phrase),[0,0]);acc[0]+=1;acc[1]|=topic_bit
    phrases=[dict(condition=k[0],model=k[1],zone=k[2],phrase=k[3],words=len(k[3].split()),posts_containing=v[0],distinct_topics=v[1].bit_count())
        for k,v in candidates.items() if v[0]>=5 and v[1].bit_count()>=3]
    phrases.sort(key=lambda r:(r['condition'],r['model'],r['zone'],-r['posts_containing'],-r['words'],r['phrase']))
    phrase_index={(r['condition'],r['model'],r['zone'],r['phrase']):r for r in phrases};family_rows=[]
    for family,members in [('GPT-6.1',WRITERS[:2]),('Claude 5.5',WRITERS[2:])]:
        for row in phrases:
            if row['model']!=members[0]:continue
            other=phrase_index.get((row['condition'],members[1],row['zone'],row['phrase']))
            if other:family_rows.append(dict(condition=row['condition'],family=family,zone=row['zone'],phrase=row['phrase'],
                first_member=members[0],first_posts=row['posts_containing'],first_topics=row['distinct_topics'],
                second_member=members[1],second_posts=other['posts_containing'],second_topics=other['distinct_topics']))
    fixed_rows=[dict(condition=k[0],model=k[1],zone=k[2],phrase_id=k[3],posts_containing=v[0],post_denominator=v[1],
        occurrences=v[2],words=v[3],source_absent_posts=v[4],source_absent_denominator=v[5],distinct_topics=v[6].bit_count()) for k,v in sorted(fixed.items())]
    references=[]
    for writer,name,phrase in [('gpt-6.1-sol','opening_paragraph','the most interesting'),('gpt-6.1-sol','transition_starts','an important distinction'),
        ('gpt-6.1-terra','closing','how is your'),('claude-opus-5-5','closing','do you think'),
        ('claude-sonnet-5-5','closing','do you think'),('claude-sonnet-5-5','point_endings','stood out to me')]:
        row=dict(model=writer,zone=name,phrase=phrase)
        for condition in ['baseline','expanded']:
            group=[(key,v) for key,v in zones.items() if key[0]==condition and key[2]==writer]
            row[condition+'_posts']=sum(phrase in lexical.grams(v[name],name in ['transition_starts','point_endings']) and s.sha(phrase) not in present[key[1]] for key,v in group)
            row[condition+'_denominator']=len(group)
        references.append(row)
    for name,rows in [('post_metrics.csv',metrics),('common_phrases.csv',phrases),('family_phrases.csv',family_rows),('fixed_phrases.csv',fixed_rows),('reference_phrases.csv',references)]:
        write_rows(OUT/name,rows)
    usage=[]
    for condition in ['baseline','expanded']:
        for writer in WRITERS:
            group=[r for key,r in records.items() if key[0]==condition and key[2]==writer]
            original=[s.load(path) for path in (ROOT/'data'/('main' if condition=='baseline' else 'simple_prose_v3_full')/'responses').glob('*/'+writer+'/*.json')]
            part=[r for r in metrics if r['condition']==condition and r['model']==writer]
            warm=[r for r in group if r['turn']>1 and isinstance(r.get('input_total'),int) and isinstance(r.get('cache_read_tokens'),int)]
            total=sum(r['input_total'] for r in warm);cache=sum(r['cache_read_tokens'] for r in warm)
            costs=[r.get('reported_cost_usd') for r in group]
            usage.append(dict(condition=condition,model=writer,effective_posts=len(part),strict_readable=sum(r['strict_readable'] for r in part),
                invalid_tag_nonempty=sum(not r['strict_readable'] for r in part),original_cli_failures=sum(r['status']!='ok' for r in original),
                authorized_retry_calls=int(condition=='expanded' and writer=='gpt-6.1-sol'),
                mean_words=float(np.mean([r['words'] for r in part])),warm_known_calls=len(warm),warm_input_tokens=total,
                warm_cache_read_tokens=cache,warm_cache_fraction=cache/total if total else None,
                reported_cost_usd=sum(costs) if all(x is not None for x in costs) else None,
                known_reported_cost_usd=sum(x or 0 for x in costs),distinct_outputs=len({r['post_sha256'] for r in part})))
    write_rows(OUT/'writer_usage.csv',usage)
    return metrics,usage


def analyse():
    OUT.mkdir(parents=True,exist_ok=True);protocol=s.load(paid.OUT/'protocol.json')
    articles,records,texts,strict=effective_data();assert all(texts.values())
    ids=[a['item_id'] for a in articles];cells=[(item,writer,turn) for item in ids for writer in WRITERS for turn in range(1,6)]
    ci={cell:i for i,cell in enumerate(cells)};styles=list(protocol['definitions']);si={style:i for i,style in enumerate(styles)}
    profiles=list(paid.MODELS);pi={profile:i for i,profile in enumerate(profiles)};zi={zone:i for i,zone in enumerate(ZONES)}
    values=np.full((3,2,400,6,40),np.nan);case_count=Counter();case_status=Counter();conflicts=[]
    for ident in profiles:
        rows=[]
        for path in sorted((paid.OUT/'cases'/ident).glob('*/*/*/*.json')):
            case=s.load(path);condition=case['condition'];arm=['baseline','expanded'].index(condition)
            cell=(case['item_id'],case['writer_model'],case['turn']);index=ci[cell]
            assert case['input_sha256']==s.sha(texts[(condition,*cell)])
            case_count[ident]+=1;case_status[(ident,case['status'])]+=1
            for name,result in case['answers'].items():
                zone,style=name.split('__',1);prob=result.get('probability')
                if result['valid']:values[pi[ident],arm,index,zi[zone],si[style]]=prob
                rows.append(dict(classifier=ident,condition=condition,item_id=cell[0],writer_model=cell[1],turn=cell[2],
                    strict_readable=case['strict_readable'],input_kind=case['input_kind'],zone=zone,style_id=style,
                    valid=result['valid'],probability=prob,error=result.get('error','')))
                whole=case['answers'].get('whole__'+style,{})
                if zone!='whole' and result['valid'] and whole.get('valid') and prob>=.5>whole['probability']:
                    conflicts.append(dict(classifier=ident,condition=condition,item_id=cell[0],writer_model=cell[1],turn=cell[2],zone=zone,
                        style_id=style,regional_probability=prob,whole_probability=whole['probability']))
        write_rows(OUT/('probabilities_'+ident+'.csv'),rows)
    masks={}
    for population in ['strict','raw','raw_without_recovery','raw_common_free']:
        mask=np.array([strict[('baseline',*cell)] and strict[('expanded',*cell)] if population=='strict' else True for cell in cells])
        if population=='raw_without_recovery':mask&=np.array([cell[:2]!=('14-seti','gpt-6.1-sol') for cell in cells])
        if population=='raw_common_free':mask&=np.array([cell!=('14-seti','gpt-6.1-sol',2) for cell in cells])
        masks[population]=mask
    samples={};comparisons=[];counts=[]
    article_index=np.array([ids.index(cell[0]) for cell in cells]);writer_index=np.array([WRITERS.index(cell[1]) for cell in cells])
    for ident in profiles:
        matrix=values[pi[ident]]
        for population,pop_mask in masks.items():
            for writer in ['all',*WRITERS]:
                selected=pop_mask & (writer_index==WRITERS.index(writer) if writer!='all' else True)
                for zone in ZONES:
                    for style in styles:
                        left=matrix[0,:,zi[zone],si[style]];right=matrix[1,:,zi[zone],si[style]]
                        good=selected&np.isfinite(left)&np.isfinite(right);n=int(good.sum())
                        for threshold in THRESHOLDS:
                            a=left[good]>=threshold;b=right[good]>=threshold
                            available_articles=np.unique(article_index[good])
                            changes=np.array([np.mean((right[good&(article_index==item)]>=threshold).astype(float)-(left[good&(article_index==item)]>=threshold)) for item in available_articles])
                            low=high=None
                            if zone=='whole' and len(changes):
                                size=len(changes)
                                if size not in samples:samples[size]=np.random.default_rng(SEED).integers(0,size,(N_BOOTSTRAP,size))
                                low,high=[float(x)*100 for x in np.quantile(changes[samples[size]].mean(axis=1),[.025,.975])]
                            comparisons.append(dict(classifier=ident,population=population,model=writer,zone=zone,style_id=style,
                                name=protocol['definitions'][style]['name'],threshold=threshold,paired_posts=n,paired_articles=len(changes),
                                baseline_present=int(a.sum()),expanded_present=int(b.sum()),baseline_fraction=float(a.mean()) if n else None,
                                expanded_fraction=float(b.mean()) if n else None,post_weighted_change_pp=100*float(b.astype(float).mean()-a.mean()) if n else None,
                                article_weighted_change_pp=100*float(changes.mean()) if len(changes) else None,
                                article_cluster_95_low_pp=low,article_cluster_95_high_pp=high))
                            if population in ['strict','raw']:
                                for arm,label in [(0,'baseline'),(1,'expanded')]:
                                    data=matrix[arm,:,zi[zone],si[style]]
                                    eligible=np.array([strict[(label,*cell)] if population=='strict' else True for cell in cells])
                                    eligible&=writer_index==WRITERS.index(writer) if writer!='all' else True
                                    readable=eligible&np.isfinite(data)
                                    counts.append(dict(classifier=ident,population=population,condition=label,model=writer,zone=zone,style_id=style,
                                        threshold=threshold,present=int((data[readable]>=threshold).sum()),readable=int(readable.sum()),
                                        unavailable=int((eligible&~np.isfinite(data)).sum())))
    write_rows(OUT/'paired_patterns.csv',comparisons);write_rows(OUT/'counts.csv',counts)
    write_rows(OUT/'region_conflicts.csv',conflicts)
    free_values=np.full((2,400,40),np.nan)
    for path in (ROOT/'data/simple_prose_v3_full_classifier/cases').glob('*/*/*/*.json'):
        r=s.load(path);arm=['baseline','expanded'].index(r['condition']);cell=(r['item_id'],r['writer_model'],r['turn'])
        for style in styles:
            value=r['answers'].get('whole__'+style,{})
            if value.get('valid'):free_values[arm,ci[cell],si[style]]=value['probability']
    whole={ident:values[pi[ident],:,:,0,:] for ident in profiles};whole['span_free']=free_values
    agreement=[];shared=[]
    for one,two in itertools.combinations(whole,2):
        for arm,label in [(0,'baseline'),(1,'expanded')]:
            for style in styles:
                a=whole[one][arm,:,si[style]];b=whole[two][arm,:,si[style]]
                mask=masks['raw_common_free']&np.isfinite(a)&np.isfinite(b);aa=a[mask]>=.5;bb=b[mask]>=.5
                observed=float(np.mean(aa==bb)) if len(aa) else None
                chance=float(aa.mean()*bb.mean()+(1-aa.mean())*(1-bb.mean())) if len(aa) else None
                kappa=(observed-chance)/(1-chance) if chance is not None and chance<1 else None
                agreement.append(dict(classifier_1=one,classifier_2=two,condition=label,style_id=style,shared_replies=int(mask.sum()),
                    first_positive=int(aa.sum()),second_positive=int(bb.sum()),disagreements=int((aa!=bb).sum()),agreement=observed,
                    kappa=kappa,kappa_note='Undefined when both label every reply identically with no variation' if kappa is None else 'Agreement, not accuracy'))
    for ident,data in whole.items():
        for style in styles:
            mask=masks['raw_common_free']&np.isfinite(data[0,:,si[style]])&np.isfinite(data[1,:,si[style]])
            shared.append(dict(classifier=ident,style_id=style,paired_posts=int(mask.sum()),
                baseline_present=int((data[0,mask,si[style]]>=.5).sum()),expanded_present=int((data[1,mask,si[style]]>=.5).sum())))
    write_rows(OUT/'classifier_agreement.csv',agreement);write_rows(OUT/'shared_classifier_counts.csv',shared)
    attempts=[s.load(path) for path in sorted((paid.OUT/'attempts').glob('*/*.json'))]
    api=[]
    for ident in profiles:
        group=[r for r in attempts if r['request']['model']==paid.MODELS[ident]['model']]
        fresh=[r for r in group if r['fresh_call']];old=[r for r in group if not r['fresh_call']]
        primary=[r for r in fresh if not r.get('diagnostic')];diagnostics=[r for r in fresh if r.get('diagnostic')]
        usage=[r['response'].get('usage',{}) for r in group]
        details=[u.get('input_tokens_details',u.get('prompt_tokens_details',{})) for u in usage]
        api.append(dict(classifier=ident,model=paid.MODELS[ident]['model'],case_records=case_count[ident],
            complete_cases=case_status[(ident,'complete')],unreadable_cases=case_status[(ident,'classifier_unreadable')],
            valid_probabilities=int(np.isfinite(values[pi[ident]]).sum()),planned_probabilities=192000,
            fresh_http_attempts=len(fresh),fresh_primary_attempts=len(primary),fresh_diagnostic_attempts=len(diagnostics),
            reused_exact_requests=len(old),known_new_cost_usd=sum(r['response'].get('usage',{}).get('cost') or 0 for r in fresh),
            historical_reused_cost_usd=sum(r['response'].get('usage',{}).get('cost') or 0 for r in old),
            new_missing_cost_fields=sum(r['response'].get('usage',{}).get('cost') is None for r in fresh),
            input_tokens=sum(u.get('input_tokens') or 0 for u in usage),output_tokens=sum(u.get('output_tokens') or 0 for u in usage),
            requests_exposing_cache_read=sum('cached_tokens' in x for x in details),
            known_cache_read_tokens=sum(x.get('cached_tokens') or 0 for x in details),
            zero_both_patterns=sum(r['baseline_present']==r['expanded_present']==0 for r in comparisons if r['classifier']==ident and r['population']=='raw' and r['model']=='all' and r['zone']=='whole' and r['threshold']==.5)))
    write_rows(OUT/'classifier_usage.csv',api)
    control_rows=[]
    for path in sorted((paid.OUT/'controls').glob('*/*.json')):
        r=s.load(path)
        for expected,field in [(True,'expected_present'),(False,'expected_absent')]:
            for style in r[field]:
                result=r['answers'].get('whole__'+style,{})
                flag=result['probability']>=.5 if result.get('valid') else None
                control_rows.append(dict(classifier=r['classifier'],control_id=r['control_id'],style_id=style,expected_present=expected,
                    valid=result.get('valid',False),probability=result.get('probability'),label=flag,matches_expectation=flag==expected if flag is not None else None))
    write_rows(OUT/'controls.csv',control_rows)
    metrics,writer_usage=phrase_analysis(articles,records,texts,strict)
    examples=[]
    for item,writer,turn in [('01-kimi',writer,2) for writer in WRITERS]+[('14-seti','gpt-6.1-sol',2),
        ('08-model-spec','claude-sonnet-5-5',3),('12-dartmouth-writing','claude-sonnet-5-5',5),('16-zest','claude-opus-5-5',5)]:
        index=ci[(item,writer,turn)]
        examples.append(dict(item_id=item,writer=writer,turn=turn,baseline=texts[('baseline',item,writer,turn)],
            expanded=texts[('expanded',item,writer,turn)],expanded_format_status=records[('expanded',item,writer,turn)]['format_status'],
            whole_probabilities={ident:{condition:{style:float(whole[ident][arm,index,si[style]]) if np.isfinite(whole[ident][arm,index,si[style]]) else None
                for style in styles} for arm,condition in [(0,'baseline'),(1,'expanded')]} for ident in whole}))
    s.save(OUT/'examples.json',examples)
    summary=dict(complete=sum(case_count.values())==2400,articles=20,effective_responses=800,writer_generation_calls_for_expanded=401,authorized_retries=1,
        successful_retry=True,strict_pairs=int(masks['strict'].sum()),raw_pairs=400,shared_free_comparison_pairs=399,
        classifiers=api,total_valid_probabilities=int(np.isfinite(values).sum()),planned_probabilities=576000,
        known_new_classifier_cost_usd=sum(r['known_new_cost_usd'] for r in api),
        imported_historical_cost_usd=sum(r['historical_reused_cost_usd'] for r in api),
        new_classifier_http_attempts=sum(r['fresh_http_attempts'] for r in api),reused_exact_requests=sum(r['reused_exact_requests'] for r in api),
        regional_positive_whole_negative=len(conflicts),bootstrap_draws=N_BOOTSTRAP,writer_usage=writer_usage,
        controls=control_rows,interpretation='Classifier-specific judgments, no human gold labels or quality score. Missing probabilities are excluded, never absent.')
    s.save(OUT/'summary.json',summary)
    print(s.canonical({k:v for k,v in summary.items() if k not in ['writer_usage','controls']}));return summary


if __name__=='__main__':analyse()
