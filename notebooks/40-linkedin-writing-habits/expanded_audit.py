"""Replay the post-hoc style audit without a model, network or full source files."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import re
import unicodedata
import numpy as np
import smoke_study as s

ROOT=Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
AUDIT=ROOT/'data/expanded_audit'
AUDIT_SEED=20261102
AUDIT_BOOTSTRAPS=2000


def audit_normal(text):
    """Normalize punctuation/case; retain line boundaries so patterns cannot bridge them."""
    value=unicodedata.normalize('NFKC',text).replace('\u2019',"'").lower()
    return '\n'.join(re.sub(r'[^\S\n]+',' ',line).strip() for line in value.splitlines())


def maximal_runs(flags,minimum=3):
    runs=[];start=None
    for i,flag in enumerate([*flags,False]):
        if flag and start is None:start=i
        elif not flag and start is not None:
            if i-start>=minimum:runs.append((start,i))
            start=None
    return runs


def audit_layout(text):
    lines=text.splitlines()
    mark=r'(?:[-*\u2022]|\d+[.)]|[\U0001F300-\U0001FAFF\u2600-\u27BF])\s+'
    marked=[bool(re.match(r'^\s*'+mark,l)) for l in lines]
    list_runs=maximal_runs(marked,1)
    bold=re.findall(r'\*\*(.+?)\*\*|__(.+?)__',text)
    bold_words=sum(len(s.words(a or b)) for a,b in bold)
    word_count=len(s.words(text))
    paras=[p.strip() for p in re.split(r'\n\s*\n',text) if p.strip()]
    substantive=[p for p in paras if not all(w.startswith('#') for w in p.split())]
    eligible=[p for p in substantive if not any(re.match(r'^\s*'+mark,l) for l in p.splitlines())]
    # A list or hashtag block breaks a run rather than being silently removed.
    one=[p in eligible and len(s.sentences(p))==1 for p in paras]
    sentence_groups=[]
    for p in substantive:
        if any(re.match(r'^\s*'+mark,l) for l in p.splitlines()):sentence_groups.append([False])
        else:sentence_groups.append([1<=len(s.words(x))<=6 for x in s.sentences(p)])
    # Paragraph boundaries do not break sentence cadence; list blocks do.
    short=[flag for group in sentence_groups for flag in group]
    stop={'a','an','and','as','at','by','for','from','in','of','on','or','the','to','with'}
    headings=re.findall(r'^\s*#{1,6}\s+(.+)$',text,re.M)
    def title_case(line):
        ws=re.findall(r'[A-Za-z]+',line)
        return len(ws)>=3 and all(w[0].isupper() for w in ws if w.lower() not in stop)
    return {
      'bold_spans':len(bold),
      'bold_leadins':len(re.findall(r'^\s*'+mark+r'\*\*[^*\n]+(?::\*\*|\*\*\s*:)',text,re.M)),
      'bold_word_share':bold_words/word_count if word_count else 0,
      'emoji_prefixed_lines':len(re.findall(r'^\s*[\U0001F300-\U0001FAFF\u2600-\u27BF]',text,re.M)),
      'headings':len(headings),'title_case_headings':sum(title_case(x) for x in headings),
      'three_item_lists':sum(b-a==3 for a,b in list_runs),
      'single_sentence_paragraph_share':sum(len(s.sentences(p))==1 for p in eligible)/len(eligible) if eligible else 0,
      'single_sentence_run3':len(maximal_runs(one)),
      'short_sentence_run3':len(maximal_runs(short)),
      'horizontal_rules':len(re.findall(r'^\s*(?:-{3,}|\*{3,}|_{3,})\s*$',text,re.M)),
      'code_fences':len(re.findall(r'^\s*```',text,re.M)),
      'placeholder':len(re.findall(r'\[(?:insert|add|your)[^\]\n]{1,100}\]',text,re.I)),
      'em_dashes':text.count('\u2014'),'exclamations':text.count('!'),
      'hashtags':len(re.findall(r'(?<!\w)#[\w]+',text))}


def audit_matches(entry,text):
    """Return normalized spans for literal regex rules; layout has its own measures."""
    return list(re.finditer(entry['regex'],audit_normal(text),re.I))


def audit_intervals(values):
    a=np.asarray(values,dtype=float)
    if not len(a):return None,None
    rng=np.random.default_rng(AUDIT_SEED)
    draws=a[rng.integers(0,len(a),(AUDIT_BOOTSTRAPS,len(a)))].mean(axis=1)
    return [float(v) for v in np.quantile(draws,[.025,.975])]


def analyse_expanded():
    catalog=s.load(AUDIT/'criteria.json');entries=catalog['entries']
    criteria_hash=s.sha(s.canonical(catalog))
    articles=s.load(ROOT/'data/main/articles.json');by_id={a['item_id']:a for a in articles}
    records=[s.load(p) for p in sorted((ROOT/'data/main/responses').glob('*/*/*.json')) if '.started.' not in p.name]
    assert len(records)==400 and all(r['status']=='ok' for r in records)
    fingerprint=s.sha(s.canonical([(r['item_id'],r['requested_model'],r['turn'],r['text_sha256']) for r in records]))
    overlap_path=AUDIT/'source_overlap.json'
    old=s.load(overlap_path) if overlap_path.exists() else {}
    overlap={'criteria_sha256':criteria_hash,'corpus_sha256':fingerprint,'topics':{}}
    for item,article in by_id.items():
        path=ROOT/article['local_input']
        if path.exists():
            source=path.read_text(encoding='utf-8');assert s.sha(source)==article['text_sha256']
            overlap['topics'][item]={'source_sha256':article['text_sha256'],
                'regex_counts':{e['id']:len(audit_matches(e,source)) for e in entries if e['kind']=='regex'}}
        else:
            assert old['criteria_sha256']==criteria_hash and old['corpus_sha256']==fingerprint,'Changed criteria/corpus require source checks'
            assert old['topics'][item]['source_sha256']==article['text_sha256']
            overlap['topics'][item]=old['topics'][item]
    s.save(overlap_path,overlap)
    acc=defaultdict(list);examples=[];per_post=[]
    for r in records:
        item,model,turn=r['item_id'],r['requested_model'],r['turn']
        pid=f'{item}/{model}/{turn:02d}'
        post={'post_id':pid,'item_id':item,'model':model,'turn':turn}
        for zone,text in s.zones(r['text']).items():
            layout=audit_layout(text);nwords=len(s.words(text))
            normal=audit_normal(text)
            for e in entries:
                if e['kind']=='layout' and zone!='whole':continue
                matches=audit_matches(e,text) if e['kind']=='regex' else []
                value=len(matches) if e['kind']=='regex' else layout[e['id']]
                source_count=overlap['topics'][item]['regex_counts'].get(e['id'])
                acc[(model,zone,e['id'])].append((item,turn,value,nwords,source_count))
                if zone=='whole':
                    post[e['id']]=value
                    # Three first positive posts per model/rule, deterministic, not a representative sample.
                    if matches and sum(x['model']==model and x['criterion_id']==e['id'] for x in examples)<3:
                        match=matches[0]
                        examples.append({'post_id':pid,'item_id':item,'model':model,'turn':turn,
                            'criterion_id':e['id'],'style_id':e['style_id'],'source_match_count':source_count,
                            'normalized_match':match.group(),
                            'normalized_context':normal[max(0,match.start()-90):min(len(normal),match.end()+130)],
                            'contextual_defect_assessed':False})
        per_post.append(post)
    rows=[];by_entry={e['id']:e for e in entries}
    for (model,zone,ident),values in sorted(acc.items()):
        e=by_entry[ident];fraction=ident.endswith('_share');positive=[v for v in values if v[2]>0]
        absent=[v for v in values if v[4]==0] if e['kind']=='regex' else []
        topic_means=[np.mean([v[2]>0 for v in values if v[0]==item]) for item in by_id]
        lo,hi=audit_intervals(topic_means) if zone=='whole' else (None,None)
        rows.append({'model':model,'zone':zone,'criterion_id':ident,'label':e['label'],
            'style_id':e['style_id'],'kind':e['kind'],'value_unit':'fraction' if fraction else 'count',
            'posts_containing':len(positive),'readable_posts':len(values),'post_fraction':len(positive)/len(values),
            'distinct_topics':len({v[0] for v in positive}),
            'total_value':sum(v[2] for v in values),'mean_value':np.mean([v[2] for v in values]),
            'occurrences_per_1000_words':1000*sum(v[2] for v in values)/sum(v[3] for v in values) if not fraction and sum(v[3] for v in values) else None,
            'source_absent_posts_containing':sum(v[2]>0 for v in absent) if e['kind']=='regex' else None,
            'source_absent_post_denominator':len(absent) if e['kind']=='regex' else None,
            'article_bootstrap_95_low':lo,'article_bootstrap_95_high':hi,
            'analysis_status':'posthoc_exploratory','contextual_defects_scored':False})
    turn_rows=[]
    for model in s.MODELS:
        for e in entries:
            for turn in range(1,6):
                vals=[p[e['id']] for p in per_post if p['model']==model and p['turn']==turn]
                turn_rows.append({'model':model,'criterion_id':e['id'],'turn':turn,'posts':len(vals),
                                  'posts_containing':sum(v>0 for v in vals),'mean_value':np.mean(vals)})
    family_rows=[]
    for name,members in [('OpenAI',s.MODELS[:2]),('Anthropic',s.MODELS[2:])]:
        for e in entries:
            member=[next(r for r in rows if r['model']==m and r['zone']=='whole' and r['criterion_id']==e['id']) for m in members]
            family_rows.append({'family':name,'criterion_id':e['id'],
               'member_1':members[0],'member_1_posts':member[0]['posts_containing'],
               'member_2':members[1],'member_2_posts':member[1]['posts_containing'],
               'pooled_posts_containing':sum(r['posts_containing'] for r in member),'pooled_posts':200,
               'interpretation':'two tested models; not a vendor-wide inference'})
    for name,table in [('counts.csv',rows),('per_post.csv',per_post),('match_examples.csv',examples),('by_turn.csv',turn_rows),('by_family.csv',family_rows)]:
        s.write_csv(AUDIT/name,table)
    summary={'version':catalog['version'],'responses':len(records),'criteria':len(entries),'explained_styles':len(catalog['styles']),
             'sources':len(catalog['sources']),'criteria_sha256':criteria_hash,'corpus_sha256':fingerprint,
             'new_model_calls':0,'added_model_spend_usd':0,'new_judge_calls':0,
             'contextual_defects_scored':False,'original_111_inventory_changed':False,
             'posthoc':True,'heldout_confirmation_claimed':False,
             'guide_examples':'Authored illustrations, not model output. Measured excerpts are in match_examples.csv.'}
    s.save(AUDIT/'summary.json',summary)
    print(json.dumps(summary,indent=2))
    return rows


if __name__=='__main__':analyse_expanded()
