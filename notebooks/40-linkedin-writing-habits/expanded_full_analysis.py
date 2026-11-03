"""Deterministic, source-free replay of the expanded-prompt comparison."""
from collections import Counter, defaultdict
import csv
from pathlib import Path
import re
import numpy as np
import smoke_study as s
import full_free_classification as c
import expanded_full_study as w

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/expanded_full_comparison'
N_BOOTSTRAP=2000
SEED=20261102
THRESHOLDS=[.2,.5,.8]
MODELS=s.MODELS


def interval(values):
    values=np.asarray(values,dtype=float)
    if not len(values):return None,None
    rng=np.random.default_rng(SEED)
    draws=values[rng.integers(0,len(values),(N_BOOTSTRAP,len(values)))].mean(axis=1)
    return [float(x) for x in np.quantile(draws,[.025,.975])]


def grams(text,disjoint=False):
    found=set()
    for chunk in text.splitlines() if disjoint else [text]:
        words=s.words(s.normalise(chunk))
        for n in range(2,9):found.update(' '.join(words[i:i+n]) for i in range(len(words)-n+1))
    return found


def regions(text):
    zones=c.body_zones(text)
    zones['opening_sentence']=s.sentences(zones['opening_paragraph'])[0] if zones['opening_paragraph'] else ''
    zones['opening_30_words']=' '.join(text.split()[:30])
    return zones


def formatting(text):
    paragraphs=[p for p in re.split(r'\n\s*\n',text.strip()) if p.strip()]
    return dict(words=len(s.words(text)),paragraphs=len(paragraphs),
        one_sentence_paragraphs=sum(len(s.sentences(p))==1 for p in paragraphs),
        hashtags=len(re.findall(r'(?<!\w)#[\w]+',text)),bold_spans=len(re.findall(r'\*\*[^\n]+?\*\*',text)),
        bullet_lines=len(re.findall(r'^\s*(?:[-*•]|\d+[.)])\s+',text,re.M)),
        emoji_codepoints=sum(0x1F300<=ord(ch)<=0x1FAFF or 0x2600<=ord(ch)<=0x27BF for ch in text),
        em_dashes=text.count('—'),exclamation_marks=text.count('!'),
        closing_question=int(text.rstrip().endswith('?')),
        not_just_phrases=len(re.findall(r'\bnot\s+(?:just|only)\b|\bmore\s+than\s+just\b',text,re.I)))


def load_data():
    articles=s.load(ROOT/'data/main/articles.json')
    records={};cases={}
    for condition,folder in [('baseline',ROOT/'data/main'),('expanded',w.OUT)]:
        for path in sorted((folder/'responses').glob('*/*/*.json')):
            if '.started.' in path.name:continue
            r=s.load(path);key=(condition,r['item_id'],r['requested_model'],r['turn'])
            records[key]=r
    for path in sorted((c.OUT/'cases').glob('*/*/*/*.json')):
        r=s.load(path);cases[(r['condition'],r['item_id'],r['writer_model'],r['turn'])]=r
    return articles,records,cases


def text_for(condition,r):
    if r['status']!='ok' or not r['text']:return None,False
    if condition=='baseline':return s.split_response(r['text'])['body'],True
    return (r['post_body'],True) if r['post_body'] is not None else (r['text'],False)


def analyse():
    articles,records,cases=load_data();protocol=s.load(c.OUT/'protocol.json');definitions=protocol['definitions']
    ids=[a['item_id'] for a in articles];post_rows=[];texts={};zone_texts={}
    lex=s.load(ROOT/'data/prose_lexicon.json')['entries'];regex={e['id']:re.compile(e['regex'],re.I) for e in lex}
    for key,r in records.items():
        condition,item,model,turn=key;text,strict=text_for(condition,r)
        if text is None:continue
        texts[key]=text;zone_texts[key]=regions(text)
        post_rows.append(dict(condition=condition,item_id=item,model=model,turn=turn,strict_readable=strict,
                              post_sha256=s.sha(text),input_kind='post' if strict else 'exact_raw_reply',**formatting(text)))
    post_by_key={(r['condition'],r['item_id'],r['model'],r['turn']):r for r in post_rows}
    overlap_path=OUT/'source_overlap.json';overlap=s.load(overlap_path) if overlap_path.exists() else {'topics':{}}
    for article in articles:
        item=article['item_id'];observed=set()
        for key,zones in zone_texts.items():
            if key[1]!=item:continue
            for zone,text in zones.items():observed.update(grams(text,zone in ['transition_starts','point_endings']))
        fingerprint=s.sha('\n'.join(sorted(observed)));path=ROOT/article['local_input']
        if path.exists():
            source=path.read_text(encoding='utf-8');assert s.sha(source)==article['text_sha256']
            source_grams=grams(source)
            info=dict(observed_candidates_sha256=fingerprint,source_sha256=article['text_sha256'],
                      source_present_candidate_hashes=sorted(s.sha(g) for g in observed&source_grams),
                      fixed_counts={e['id']:len(regex[e['id']].findall(s.normalise(source))) for e in lex})
            overlap['topics'][item]=info
        else:
            info=overlap['topics'][item];assert info['observed_candidates_sha256']==fingerprint
            assert info['source_sha256']==article['text_sha256']
    s.save(overlap_path,overlap)
    probabilities=[];conflicts=[]
    for key,case in sorted(cases.items()):
        for name,result in case['answers'].items():
            zone,style=name.split('__',1)
            probabilities.append(dict(condition=key[0],item_id=key[1],model=key[2],turn=key[3],
                strict_readable=case['strict_readable'],input_kind=case['input_kind'],zone=zone,style_id=style,
                valid=result['valid'],probability=result.get('probability'),error=result.get('error','')))
            whole=case['answers'].get('whole__'+style,{})
            if zone!='whole' and result['valid'] and whole.get('valid') and result['probability']>=.5>whole['probability']:
                conflicts.append(dict(condition=key[0],item_id=key[1],model=key[2],turn=key[3],zone=zone,
                    style_id=style,regional_probability=result['probability'],whole_probability=whole['probability']))
    counts=[];comparisons=[]
    # Each predicate uses only the cells for which both conditions have a valid answer.
    # This prevents missing answers or missing tags from becoming negative labels.
    for population in ['strict','raw_sensitivity','raw_without_recovery_block']:
        def eligible(key,case):
            return ((population!='strict' or case['strict_readable']) and
                not (population=='raw_without_recovery_block' and key[1:3]==('14-seti','gpt-6.1-sol')))
        for model in ['all',*MODELS]:
            for zone in protocol['zones']:
                for style,definition in definitions.items():
                    name=zone+'__'+style
                    by_condition={}
                    for condition in ['baseline','expanded']:
                        available={key[1:]:case['answers'][name]['probability'] for key,case in cases.items()
                            if key[0]==condition and (model=='all' or key[2]==model) and eligible(key,case)
                            and case['answers'].get(name,{}).get('valid')}
                        by_condition[condition]=available
                        if population!='raw_without_recovery_block':
                            for threshold in THRESHOLDS:
                                counts.append(dict(population=population,model=model,zone=zone,style_id=style,
                                    name=definition['name'],condition=condition,threshold=threshold,
                                    present=sum(v>=threshold for v in available.values()),readable=len(available),
                                    fraction=sum(v>=threshold for v in available.values())/len(available) if available else None))
                    paired=sorted(set(by_condition['baseline'])&set(by_condition['expanded']))
                    for threshold in THRESHOLDS:
                        a=[by_condition['baseline'][cell]>=threshold for cell in paired]
                        b=[by_condition['expanded'][cell]>=threshold for cell in paired]
                        changes=[np.mean([float(b[i])-float(a[i]) for i,k in enumerate(paired) if k[0]==item])
                                 for item in ids if any(k[0]==item for k in paired)]
                        low,high=interval(changes) if zone=='whole' else (None,None)
                        comparisons.append(dict(population=population,model=model,zone=zone,style_id=style,
                            name=definition['name'],threshold=threshold,paired_posts=len(paired),paired_articles=len(changes),
                            baseline_present=sum(a),expanded_present=sum(b),
                            baseline_fraction=float(np.mean(a)) if a else None,expanded_fraction=float(np.mean(b)) if b else None,
                            post_weighted_change_pp=100*float(np.mean(np.array(b,dtype=float)-a)) if a else None,
                            article_weighted_change_pp=100*float(np.mean(changes)) if changes else None,
                            article_cluster_95_low_pp=100*low if low is not None else None,
                            article_cluster_95_high_pp=100*high if high is not None else None))
    fixed=defaultdict(lambda:dict(posts=0,n=0,occurrences=0,words=0,absent_posts=0,absent_n=0,topics=set()))
    candidates=defaultdict(lambda:dict(posts=set(),topics=set()))
    for key,zones in zone_texts.items():
        condition,item,model,turn=key;source=overlap['topics'][item];present=set(source['source_present_candidate_hashes'])
        for zone,text in zones.items():
            normal=s.normalise(text)
            for entry in lex:
                k=(condition,model,zone,entry['id']);acc=fixed[k];n=len(regex[entry['id']].findall(normal))
                acc['n']+=1;acc['posts']+=int(n>0);acc['occurrences']+=n;acc['words']+=len(s.words(text))
                if n:acc['topics'].add(item)
                if source['fixed_counts'][entry['id']]==0:acc['absent_n']+=1;acc['absent_posts']+=int(n>0)
            for phrase in grams(text,zone in ['transition_starts','point_endings']):
                if s.sha(phrase) in present:continue
                acc=candidates[(condition,model,zone,phrase)];acc['posts'].add((item,turn));acc['topics'].add(item)
    fixed_rows=[dict(condition=k[0],model=k[1],zone=k[2],phrase_id=k[3],posts_containing=v['posts'],
        post_denominator=v['n'],occurrences=v['occurrences'],words=v['words'],distinct_topics=len(v['topics']),
        source_absent_posts=v['absent_posts'],source_absent_denominator=v['absent_n']) for k,v in sorted(fixed.items())]
    phrase_rows=[dict(condition=k[0],model=k[1],zone=k[2],phrase=k[3],words=len(k[3].split()),
        posts_containing=len(v['posts']),distinct_topics=len(v['topics'])) for k,v in candidates.items()
        if len(v['posts'])>=5 and len(v['topics'])>=3]
    phrase_rows.sort(key=lambda r:(r['condition'],r['model'],r['zone'],-r['posts_containing'],-r['words'],r['phrase']))
    family=[]
    index={(r['condition'],r['model'],r['zone'],r['phrase']):r for r in phrase_rows}
    for condition in ['baseline','expanded']:
        for label,members in [('GPT-6.1',MODELS[:2]),('Claude 5.5',MODELS[2:])]:
            for row in phrase_rows:
                if row['condition']!=condition or row['model']!=members[0]:continue
                other=index.get((condition,members[1],row['zone'],row['phrase']))
                if other:family.append(dict(condition=condition,family=label,zone=row['zone'],phrase=row['phrase'],
                    member_1_posts=row['posts_containing'],member_2_posts=other['posts_containing']))
    reference=[]
    for model,zone,phrase in [('gpt-6.1-sol','opening_paragraph','the most interesting'),
        ('gpt-6.1-sol','transition_starts','an important distinction'),
        ('gpt-6.1-terra','closing','how is your'),
        ('claude-opus-5-5','closing','do you think'),('claude-sonnet-5-5','closing','do you think'),
        ('claude-sonnet-5-5','point_endings','stood out to me')]:
        row=dict(model=model,zone=zone,phrase=phrase)
        for condition in ['baseline','expanded']:
            group=[(key,zones) for key,zones in zone_texts.items() if key[0]==condition and key[2]==model]
            row[condition+'_posts']=sum(phrase in grams(zones[zone],zone in ['transition_starts','point_endings'])
                and s.sha(phrase) not in set(overlap['topics'][key[1]]['source_present_candidate_hashes']) for key,zones in group)
            row[condition+'_denominator']=len(group)
        reference.append(row)
    usage=[]
    for condition in ['baseline','expanded']:
        for model in MODELS:
            rs=[r for key,r in records.items() if key[0]==condition and key[2]==model]
            ps=[r for r in post_rows if r['condition']==condition and r['model']==model]
            warm=[r for r in rs if r['turn']>1 and isinstance(r.get('input_total'),int) and isinstance(r.get('cache_read_tokens'),int)]
            denominator=sum(r['input_total'] for r in warm)
            costs=[r.get('reported_cost_usd') for r in rs]
            usage.append(dict(condition=condition,model=model,planned=100,attempted=len(rs),
                completed=sum(r['status']=='ok' for r in rs),strict_readable=sum(r['strict_readable'] for r in ps),
                cli_failures=sum(r['status']!='ok' for r in rs),unattempted=100-len(rs),
                invalid_tag_nonempty=sum(not r['strict_readable'] for r in ps),
                outside_text=sum(bool(r.get('extra_text_present')) for r in rs),
                distinct_outputs=len({r['post_sha256'] for r in ps}),mean_words=float(np.mean([r['words'] for r in ps])) if ps else None,
                within_article_duplicate_pairs=sum(sum(n*(n-1)//2 for n in Counter(s.normalise(texts[key]) for key in texts
                    if key[0]==condition and key[1]==item and key[2]==model).values()) for item in ids),
                mean_words_strict=float(np.mean([r['words'] for r in ps if r['strict_readable']])) if any(r['strict_readable'] for r in ps) else None,
                warm_known_calls=len(warm),warm_unknown_calls=sum(r['turn']>1 for r in rs)-len(warm),
                warm_input_tokens=denominator,warm_cache_read_tokens=sum(r['cache_read_tokens'] for r in warm),
                warm_cache_fraction=sum(r['cache_read_tokens'] for r in warm)/denominator if denominator else None,
                known_reported_cost_usd=sum(x for x in costs if x is not None),
                reported_cost_usd=sum(costs) if costs and all(x is not None for x in costs) else None,
                observed_tool_events=sum(len(r['tool_events']) for r in rs)))
    attempts=[s.load(path) for path in sorted((c.OUT/'attempts').glob('*.json'))]
    api=dict(attempts=len(attempts),statuses=dict(Counter(str(r['status']) for r in attempts)),
        successful=sum(r['status']==200 for r in attempts),
        known_reported_cost_usd=sum(r['response'].get('usage',{}).get('cost') or 0 for r in attempts),
        successful_missing_cost=sum(r['status']==200 and r['response'].get('usage',{}).get('cost') is None for r in attempts),
        failed_missing_cost=sum(r['status']!=200 and r['response'].get('usage',{}).get('cost') is None for r in attempts),
        native_input_tokens=sum(r['response'].get('usage',{}).get('input_tokens') or 0 for r in attempts),
        native_output_tokens=sum(r['response'].get('usage',{}).get('output_tokens') or 0 for r in attempts),
        successful_with_cache_counter=sum('cached_tokens' in r['response'].get('usage',{}).get('input_tokens_details',{}) for r in attempts if r['status']==200),
        cases=len(cases),case_statuses=dict(Counter(r['status'] for r in cases.values())),
        valid_probabilities=sum(r['valid'] for r in probabilities),invalid_probabilities=sum(not r['valid'] for r in probabilities),
        missing_probabilities=sum(240-len(r['answers']) for r in cases.values() if r['status']!='unreadable_generation'),
        regional_positive_whole_negative=len(conflicts))
    for name,rows in [('post_metrics.csv',post_rows),('probabilities.csv',probabilities),('counts.csv',counts),
        ('paired_patterns.csv',comparisons),('region_conflicts.csv',conflicts),('fixed_phrases.csv',fixed_rows),
        ('common_phrases.csv',phrase_rows),('family_phrases.csv',family),('reference_phrases.csv',reference),('usage.csv',usage)]:
        s.write_csv(OUT/name,rows)
    summary=dict(articles=len(articles),planned_responses=800,writer_records=len(records),nonempty_responses=len(texts),
                 generation=usage,classifier=api,patterns=len(definitions),regions=protocol['zones'],
                 bootstrap_draws=N_BOOTSTRAP,bootstrap_unit='article; all available paired cells retained within each sampled article',
                 strict_pairs=sum(r['strict_readable'] for r in post_rows if r['condition']=='expanded'),
                 raw_pairs=sum(r['condition']=='expanded' for r in post_rows),
                 source_free_replay=True,prose_labels='Only the free typed API supplies contextual labels. Literal counters do not assign labels.')
    s.save(OUT/'summary.json',summary)
    print(s.canonical({k:v for k,v in summary.items() if k!='generation'}))
    return summary


if __name__=='__main__':analyse()
