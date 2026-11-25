"""Deterministic main-study analysis, with offline source-overlap replay."""
from collections import Counter, defaultdict
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
import numpy as np
import smoke_study as s

ROOT=Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA=ROOT/'data/main'
MODELS=s.MODELS.copy()
N_BOOTSTRAP=2000
SEED=20261101


def grams(text, disjoint=False):
    result=set()
    for chunk in text.splitlines() if disjoint else [text]:
        tokens=s.words(s.normalise(chunk))
        for size in range(2,9):
            result.update(' '.join(tokens[i:i+size]) for i in range(len(tokens)-size+1))
    return result


def bootstrap(values):
    array=np.asarray(values,dtype=float)
    if not len(array):return None,None
    rng=np.random.default_rng(SEED)
    samples=array[rng.integers(0,len(array),(N_BOOTSTRAP,len(array)))].mean(axis=1)
    return [float(x) for x in np.quantile(samples,[.025,.975])]


def read_rows(path):
    with path.open(encoding='utf-8',newline='') as handle:return list(csv.DictReader(handle))


def analyse():
    articles=s.load(DATA/'articles.json');by_id={a['item_id']:a for a in articles}
    ids=[a['item_id'] for a in articles]
    records=[s.load(p) for p in sorted((DATA/'responses').glob('*/*/*.json')) if '.started.' not in p.name]
    entries=s.load(ROOT/'data/prose_lexicon.json')['entries']
    patterns={e['id']:re.compile(e['regex'],re.I) for e in entries}
    valid=[r for r in records if r['status']=='ok']
    overlap_path=DATA/'source_overlap.json'
    overlap=s.load(overlap_path) if overlap_path.exists() else {'topics':{}}
    source_info={}
    for item in ids:
        group=[r for r in valid if r['item_id']==item]
        observed=set().union(*(grams(r['text']) for r in group)) if group else set()
        # Disjoint transition windows introduce no artificial cross-window candidates.
        for r in group:
            for zone,text in s.zones(r['text']).items():
                observed.update(grams(text,zone in ['transition_starts','point_endings']))
        fingerprint=s.sha('\n'.join(sorted(observed)))
        path=ROOT/by_id[item]['local_input']
        if path.exists():
            source=path.read_text(encoding='utf-8');assert s.sha(source)==by_id[item]['text_sha256']
            source_normal=s.normalise(source);source_grams=grams(source)
            info={'observed_candidates_sha256':fingerprint,
                  'source_present_candidate_hashes':sorted(s.sha(g) for g in observed&source_grams),
                  'fixed_counts':{e['id']:len(patterns[e['id']].findall(source_normal)) for e in entries}}
            overlap['topics'][item]=info
        else:
            info=overlap['topics'][item]
            assert info['observed_candidates_sha256']==fingerprint,'Outputs/parser changed: source checks need refreezing'
        source_info[item]={'present':set(info['source_present_candidate_hashes']),'fixed':info['fixed_counts']}
    s.save(overlap_path,overlap)
    post_rows=[];cache_rows=[];format_rows=[];phrase_rows=[];phrase_examples=[]
    fixed_acc=defaultdict(list);candidate_acc=defaultdict(lambda:{'posts':set(),'topics':set(),'discovery_posts':set(),'confirmation_posts':set(),'discovery_topics':set(),'confirmation_topics':set()})
    normalized_by_topic=defaultdict(list)
    for r in valid:
        item,model,turn=r['item_id'],r['requested_model'],r['turn']
        post_id=f'{item}/{model}/{turn:02d}'
        segmented=s.split_response(r['text']);zones=s.zones(r['text']);features=s.formatting(r['text'])
        fmt={'post_id':post_id,'item_id':item,'model':model,'turn':turn,'split':r['split'],**features}
        format_rows.append(fmt)
        post_rows.append({'post_id':post_id,'item_id':item,'model':model,'turn':turn,'split':r['split'],
             'session_id':r['session_id'],'status':r['status'],'words':features['words'],
             'raw_sha256':r['text_sha256'],'post_sha256':s.sha(segmented['body']),
             'normalised_post_sha256':s.sha(s.normalise(segmented['body'])),
             'preface':segmented['preface'],'editorial_note':bool(segmented['annotation']),
             'opening':zones['opening_paragraph'],'closing':zones['closing']})
        normalized_by_topic[(model,item)].append(s.normalise(segmented['body']))
        for zone,text in zones.items():
            normal=s.normalise(text);word_count=len(s.words(normal))
            for entry in entries:
                count=len(patterns[entry['id']].findall(normal))
                source_count=source_info[item]['fixed'][entry['id']]
                fixed_acc[(model,zone,entry['id'])].append((item,count,word_count,source_count))
                if count and zone in ['opening_sentence','transition_starts','point_endings','closing','whole']:
                    phrase_examples.append({'post_id':post_id,'model':model,'item_id':item,'turn':turn,'zone':zone,
                        'phrase_id':entry['id'],'occurrences':count,'source_occurrences':source_count,
                        'excerpt':text[:450]})
            for phrase in grams(text,zone in ['transition_starts','point_endings']):
                if s.sha(phrase) in source_info[item]['present']:continue
                acc=candidate_acc[(model,zone,phrase)];split=r['split']
                acc['posts'].add(post_id);acc['topics'].add(item)
                acc[split+'_posts'].add(post_id);acc[split+'_topics'].add(item)
    for r in records:
        cache_rows.append({k:r.get(k) for k in ['requested_model','item_id','turn','status','session_id',
            'input_total','uncached_input_tokens','cache_read_tokens','cache_write_tokens','output_tokens',
            'cache_read_fraction','reported_cost_usd','reported_session_cost_usd','seconds','usage_scope']})
    for (model,zone,phrase_id),vals in sorted(fixed_acc.items()):
        posts=sum(v[1]>0 for v in vals);source_absent=[v for v in vals if v[3]==0]
        by_topic={item:np.mean([v[1]>0 for v in vals if v[0]==item]) for item in ids}
        lo,hi=bootstrap(list(by_topic.values())) if zone=='whole' else (None,None)
        phrase_rows.append({'model':model,'zone':zone,'phrase_id':phrase_id,
             'posts_containing':posts,'readable_posts':len(vals),'post_fraction':posts/len(vals),
             'distinct_topics':len({v[0] for v in vals if v[1]>0}),
             'occurrences':sum(v[1] for v in vals),'words_in_zone':sum(v[2] for v in vals),
             'occurrences_per_1000_words':1000*sum(v[1] for v in vals)/sum(v[2] for v in vals) if sum(v[2] for v in vals) else 0,
             'posts_containing_when_source_absent':sum(v[1]>0 for v in source_absent),
             'source_absent_post_denominator':len(source_absent),
             'article_bootstrap_95_low':lo,'article_bootstrap_95_high':hi})
    candidates=[]
    for (model,zone,phrase),acc in candidate_acc.items():
        if len(acc['posts'])<2:continue
        discovered=len(acc['discovery_posts'])>=5 and len(acc['discovery_topics'])>=3
        confirmed=discovered and len(acc['confirmation_posts'])>=5 and len(acc['confirmation_topics'])>=3
        candidates.append({'model':model,'zone':zone,'phrase':phrase,'words':len(phrase.split()),
             'posts_containing':len(acc['posts']),'distinct_topics':len(acc['topics']),
             'discovery_posts':len(acc['discovery_posts']),'discovery_topics':len(acc['discovery_topics']),
             'confirmation_posts':len(acc['confirmation_posts']),'confirmation_topics':len(acc['confirmation_topics']),
             'status':'confirmed' if confirmed else 'discovered_not_confirmed' if discovered else 'exploratory'})
    candidates.sort(key=lambda r:(r['model'],r['zone'],-r['posts_containing'],-r['words'],r['phrase']))
    shared=[]
    confirmed={(r['model'],r['zone'],r['phrase']):r for r in candidates if r['status']=='confirmed'}
    for family,members in [('GPT-6.1',MODELS[:2]),('Claude 5.5',MODELS[2:])]:
        for model,zone,phrase in list(confirmed):
            if model!=members[0] or (members[1],zone,phrase) not in confirmed:continue
            a,b=confirmed[(members[0],zone,phrase)],confirmed[(members[1],zone,phrase)]
            row={'family':family,'zone':zone,'phrase':phrase,'member_1':members[0],
                 'member_1_posts':a['posts_containing'],'member_2':members[1],'member_2_posts':b['posts_containing'],
                 'criterion':'Source-absent support confirmed separately for both tested models'}
            for other in MODELS:
                row[other]=len(candidate_acc.get((other,zone,phrase),{}).get('posts',set()))
            shared.append(row)
    model_rows=[];format_summary=[];turn_rows=[]
    for model in MODELS:
        rs=[r for r in records if r['requested_model']==model];vs=[r for r in valid if r['requested_model']==model]
        warm=[r for r in vs if r['turn']>1]
        def sum_field(key):
            return sum(r[key] for r in rs) if all(isinstance(r.get(key),(float,int)) for r in rs) else None
        denom=sum(r['input_total'] or 0 for r in vs);cached=sum(r['cache_read_tokens'] or 0 for r in vs)
        wdenom=sum(r['input_total'] or 0 for r in warm)
        rows=[p for p in post_rows if p['model']==model]
        model_rows.append({'model':model,'planned':100,'attempted':len(rs),'readable':len(vs),
             'unreadable_or_protocol_failed':len(rs)-len(vs),'unrequested_after_failure':100-len(rs),
             'wrong_answers':None,'wrong_answers_note':'No single gold post or factual/quality adjudication; not scored.',
             'conversations':len({r['session_id'] for r in vs}),'unique_post_bodies':len({p['normalised_post_sha256'] for p in rows}),
             'within_topic_duplicate_pairs':sum(sum(n*(n-1)//2 for n in Counter(lst).values()) for (m,_),lst in normalized_by_topic.items() if m==model),
             'mean_words':float(np.mean([p['words'] for p in rows])) if rows else None,
             'input_tokens':sum_field('input_total'),'cache_read_tokens':sum_field('cache_read_tokens'),
             'cache_write_tokens':sum_field('cache_write_tokens'),'output_tokens':sum_field('output_tokens'),
             'cache_read_fraction_all':cached/denom if denom else None,
             'cache_read_fraction_turns_2_to_5':sum(r['cache_read_tokens'] or 0 for r in warm)/wdenom if wdenom else None,
             'reported_cost_usd':sum_field('reported_cost_usd'),'seconds':sum(r['seconds'] for r in rs),
             'observed_tool_events':sum(len(r['tool_events']) for r in rs)})
        fs=[r for r in format_rows if r['model']==model]
        for feature in [k for k in fs[0] if k not in ['post_id','item_id','model','turn','split']] if fs else []:
            values=[float(r[feature]) for r in fs]
            topic_means=[np.mean([float(r[feature])>0 for r in fs if r['item_id']==item]) for item in ids]
            lo,hi=bootstrap(topic_means)
            format_summary.append({'model':model,'feature':feature,'posts_containing':sum(v>0 for v in values),
                'post_denominator':len(fs),'post_fraction':float(np.mean(np.array(values)>0)),
                'mean_count':float(np.mean(values)),'article_bootstrap_95_low':lo,'article_bootstrap_95_high':hi})
        for turn in range(1,6):
            part=[r for r in rows if r['turn']==turn]
            partfmt=[r for r in fs if r['turn']==turn]
            turn_rows.append({'model':model,'turn':turn,'posts':len(part),'mean_words':float(np.mean([r['words'] for r in part])) if part else None,
                'closing_question_posts':sum(r['closing_question'] for r in partfmt),
                'emoji_posts':sum(r['emoji_codepoints']>0 for r in partfmt),'hashtags_posts':sum(r['hashtags']>0 for r in partfmt)})
    family_rows=[]
    whole=[r for r in phrase_rows if r['zone']=='whole']
    for entry in entries:
        row={'phrase_id':entry['id']}
        for model in MODELS:
            row[model]=next((r['posts_containing'] for r in whole if r['model']==model and r['phrase_id']==entry['id']),0)
        row['gpt_family_posts']=sum(row[m] for m in MODELS[:2]);row['claude_family_posts']=sum(row[m] for m in MODELS[2:])
        row['scope']='Two tested models per family, conditional on CLI and conversation design'
        family_rows.append(row)
    for name,rows in [('posts.csv',post_rows),('provider_cache_usage.csv',cache_rows),('formatting.csv',format_rows),
        ('fixed_prose_counts.csv',phrase_rows),('fixed_phrase_examples.csv',phrase_examples),('phrase_candidates.csv',candidates),
        ('formatting_summary.csv',format_summary),('turn_summary.csv',turn_rows),('family_fixed_counts.csv',family_rows),('model_summary.csv',model_rows)]:
        s.write_csv(DATA/name,rows)
    s.write_csv(DATA/'family_shared_phrases.csv',shared)
    if not shared:
        with (DATA/'family_shared_phrases.csv').open('w',encoding='utf-8',newline='') as handle:
            csv.writer(handle).writerow(['family','zone','phrase','member_1','member_1_posts','member_2','member_2_posts','criterion',*MODELS])
    gates={'400_responses':len(records)==400,'400_readable':len(valid)==400,
        '80_conversations':len({r['session_id'] for r in valid})==80,
        'no_observed_tools':not any(r['tool_events'] for r in records),
        'high_effort_all':all(r['request']['effort']=='high' for r in records),
        'short_followups_only':all(r['request']['prompt_sha256']==s.sha(s.FOLLOWUP_PROMPT) for r in records if r['turn']>1),
        'one_session_per_model_topic':all(len({r['session_id'] for r in valid if r['requested_model']==model and r['item_id']==item})==1 for model in MODELS for item in ids),
        'source_hashes_match_manifest':all(r['request']['source_sha256']==by_id[r['item_id']]['text_sha256'] for r in records)}
    s.save(DATA/'summary.json',{'protocol':'main-v1-high-conversation-short-followups','models':model_rows,'gates':gates,
        'articles':len(articles),'fixed_candidates':len(entries),'bootstrap_draws':N_BOOTSTRAP,
        'observed_confirmed_candidates':sum(r['status']=='confirmed' for r in candidates),
        'scope':'Descriptive phrase/formatting study. No quality ranking or authorship detector; article clusters are the uncertainty unit.'})
    print(json.dumps({'models':model_rows,'gates':gates},indent=2))
    return model_rows


if __name__=='__main__':analyse()
