import collections, difflib, hashlib, json, re, subprocess
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'data'
REPO = ROOT.parents[2]
SEED = 20261030

def git(*args):
    return subprocess.check_output(['git',*args],cwd=REPO).decode('utf-8','replace')

def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def dump(name,x):
    (DATA/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def jsonl(name,rows):
    (DATA/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')

BANNED = r'\b(?:delv(?:e|es|ed|ing)|tapestry|testament|intricate|meticulous(?:ly)?|pivotal|crucial|vital|robust|seamless(?:ly)?|leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|unlock(?:s|ed|ing)?|elevat(?:e|es|ed|ing)|empower(?:s|ed|ing)?|foster(?:s|ed|ing)?|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|realm|landscape|navigate|journey|embark|game.changer|cutting.edge|groundbreaking|transformative|holistic|multifaceted|nuanced|comprehensive|invaluable|vibrant|boasts|notably|additionally|furthermore|moreover|plays a key role|a wide range of|a myriad of|valuable insights)\b'

def violations(s):
    title=0
    for h in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
        ws=re.findall(r'\b[A-Za-z]+\b',h)
        title += len(ws)>2 and sum(w.istitle() for w in ws[1:])/max(len(ws)-1,1)>.7
    banned_no_harness=BANNED.replace('|harness(?:es|ed|ing)?','')
    harness_verbs=len(re.findall(r'\bharness(?:es|ed|ing)?\s+(?:the|a|an|this|these|those|our|its|their)\b',s,re.I))
    return dict(banned_words=len(re.findall(banned_no_harness,s,re.I))+harness_verbs,em_dashes=s.count('—'),
                exclamations=s.count('!'),bold_bullet_leadins=len(re.findall(r'^\s*[-*+]\s+\*\*[^*]+(?::\*\*|\*\*:)',s,re.M)),
                title_case_headings=title,stacked_hedges=len(re.findall(r'\b(?:may potentially|could possibly|might possibly|seems? (?:that )?perhaps|possibly suggest|potentially suggest)\b',s,re.I)))

def paragraphs(s):
    s=re.sub(r'<details\b.*?</details\s*>','',s,flags=re.I|re.S)
    s=re.sub(r'(```|~~~).*?\1','',s,flags=re.S)
    result=[]; buf=[];section=0
    def flush():
        if buf:
            t='\n'.join(buf).strip();buf.clear()
            if t:result.append((t,section))
    for line in s.splitlines():
        st=line.strip()
        if not st:flush();continue
        if re.match(r'^#{1,6}\s',st):flush();section+=1;continue
        if re.match(r'^(?:\||!\[|>|<|\[\^[^]]+\]:|[-*_]{3,}$)',st):flush();section+=1;continue
        if re.match(r'^[-*+]\s+\[[^]]+\]\(',st):flush();continue
        if re.match(r'^[-*+]\s',st):flush()
        buf.append(line.strip())
    flush()
    return result

def tokens(s):
    s=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',s)
    return re.findall(r"[a-z0-9]+(?:['.-][a-z0-9]+)*",s.lower())

def numbers(s):
    # Ignore link destinations; preserve numerical values and percent units.
    s=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',s)
    vals=[]
    for m in re.finditer(r'(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?\s*%?',s):
        t=m.group().strip(); unit='%' if t.endswith('%') else ''
        vals.append(str(Decimal(t.rstrip('%').replace(',','').strip()).normalize())+unit)
    return sorted(vals)

NAMES = ['Claude','Opus','Sonnet','Haiku','GPT','Codex','Muse','Gemini','Qwen','DeepSeek','Llama','Mistral',
         'Mercury','Jev','Clef','Decisions API','OpenRouter','TabPFN','TabICL','Chronos','TimesFM','Moirai',
         'Toto','Lag-Llama','DLinear','MiniLM','BGE','E5','CLIP','ResNet','Florence','Donut','LayoutLM',
         'DocILE','RVL-CDIP','Tobacco3482','CUB','Stanford Cars','DocLayNet','FUNSD','SROIE','FinQA',
         'PubLayNet','MMLU','GSM8K','SWE-bench','HumanEval','OpenML','M4','M5','ETTh1','ETTh2','Electricity',
         'GDELT','FRED','DART','DBpedia','AG News','Amazon','Kaggle','UCI','CIFAR','ImageNet','WikiSQL','Spider']

def names(s):
    return sorted(n.lower() for n in NAMES if re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',s,re.I))

def author_meta(rev,path):
    line=git('log','-1','--format=%H%x1f%aI%x1f%an%x1f%B',rev,'--',path)
    ps=line.split('\x1f',3)
    body=ps[3] if len(ps)>3 else ''
    co=re.findall(r'Co-Authored-By:\s*(.+)',body,re.I)
    ancestry=git('log','origin/main','--first-parent','--ancestry-path',ps[0]+'^..'+rev,'--reverse','--format=%H%x1f%s')
    introduction=next((s for s in ancestry.splitlines() if 'Merge pull request' in s),'')
    branch=introduction.split(' from ',1)[1] if ' from ' in introduction else ''
    evidence=' '.join(co+[ps[2] if len(ps)>2 else '',body,branch])
    vendor='Claude' if re.search(r'claude|anthropic',evidence,re.I) else ('Codex' if re.search(r'codex|openai|gpt-',evidence,re.I) else 'unknown')
    return dict(commit=ps[0],date=ps[1],commit_author=ps[2],coauthors=co,vendor=vendor,message=body.strip(),
                introducing_merge=introduction,branch=branch,attribution='file revision metadata, not verified token-level authorship')

def mine():
    source=git('rev-parse','origin/main').strip()
    log=git('log','origin/main','--first-parent','--since=2026-10-27','--until=2026-10-31','--format=%H%x1f%aI%x1f%s')
    commits=[r.split('\x1f',2) for r in log.splitlines() if re.search(r'rewrite',r,re.I)]
    sources=[]; candidates=[]; seen=set();stats=collections.Counter()
    for commit,date,subject in commits:
        parent=git('rev-parse',commit+'^1').strip()
        paths=[p for p in git('diff','--name-only',parent,commit).splitlines() if p.endswith('README.md')]
        for path in paths:
            # Rewrite branches sometimes touched unrelated root table rows; exclude those.
            if path=='README.md' and 'root-readme' not in subject:continue
            if path=='econ/README.md' and 'econ-readme' not in subject:continue
            try:a=git('show',parent+':'+path);b=git('show',commit+':'+path)
            except subprocess.CalledProcessError:continue
            ba=author_meta(parent,path);aa=author_meta(commit,path)
            pr=re.search(r'pull request #(\d+)',subject)
            entry=dict(path=path,notebook=path.removesuffix('/README.md'),merge_commit=commit,parent=parent,
                       date=date,subject=subject,pr=int(pr[1]) if pr else None,before_author=ba,after_author=aa)
            sources.append(dict(**entry,before_sha256=sha(a),after_sha256=sha(b)))
            snap=DATA/'source_snapshots'/commit[:12];snap.mkdir(parents=True,exist_ok=True)
            stem=path.replace('/','__')
            (snap/(stem+'.before.md')).write_text(a,encoding='utf-8')
            (snap/(stem+'.after.md')).write_text(b,encoding='utf-8')
            aps0=paragraphs(a);bps0=paragraphs(b)
            stats['before_paragraphs']+=len(aps0);stats['after_paragraphs']+=len(bps0)
            def groups(ps):
                out=[];spans=[]
                for i in range(len(ps)):
                    for count in range(1,4):
                        if i+count>len(ps):continue
                        if len({x[1] for x in ps[i:i+count]})>1:continue
                        text='\n\n'.join(x[0] for x in ps[i:i+count])
                        if len(tokens(text))<=250:
                            out.append(text);spans.append(list(range(i,i+count)))
                return out,spans
            aps,asp=groups(aps0);bps,bsp=groups(bps0)
            stats['before_blocks']+=len(aps);stats['after_blocks']+=len(bps)
            at=[tokens(x) for x in aps];bt=[tokens(x) for x in bps]
            ac=[collections.Counter(x) for x in at];bc=[collections.Counter(x) for x in bt]
            an=[numbers(x) for x in aps];bn=[numbers(x) for x in bps]
            am=[names(x) for x in aps];bm=[names(x) for x in bps]
            sim=np.zeros((len(aps),len(bps)))
            for i,x in enumerate(at):
                cx=ac[i]
                for j,y in enumerate(bt):
                    overlap=sum((cx & bc[j]).values())
                    sim[i,j]=2*overlap/max(len(x)+len(y),1)
            choices=[]
            for i in range(len(aps)):
                for j in range(len(bps)):
                    if sim[i,j]>=.35:
                        samefacts=an[i]==bn[j] and am[i]==bm[j]
                        choices.append((samefacts and 30<=len(at[i]) and 30<=len(bt[j]) and sim[i,j]<=.95,float(sim[i,j]),i,j))
            choices.sort(reverse=True)
            used_a=set();used_b=set()
            for factmatch,_,i,j in choices:
                if used_a.intersection(asp[i]) or used_b.intersection(bsp[j]):continue
                used_a.update(asp[i]);used_b.update(bsp[j])
                before,after=aps[i],bps[j];x,y=at[i],bt[j]
                similarity=float(sim[i,j]);ratio=len(y)/max(len(x),1)
                seq=difflib.SequenceMatcher(None,x,y,autojunk=False).ratio()
                why=[]
                if not (30<=len(x)<=250 and 30<=len(y)<=250):why.append('word_count')
                if not .5<=ratio<=2:why.append('length_ratio')
                if before==after or seq>=.98:why.append('identical_or_near_identical')
                if not .35<=similarity<=.95:why.append('similarity_band')
                if seq<.20:why.append('sequence_similarity')
                if numbers(before)!=numbers(after):why.append('numbers_changed')
                if names(before)!=names(after):why.append('names_changed')
                if not ba['date'].startswith('2026-10') or not aa['date'].startswith('2026-10'):why.append('date_filter')
                key=sha(before+'\n'+after)
                if key in seen:why.append('duplicate')
                seen.add(key)
                vb,va=violations(before),violations(after)
                row=dict(**entry,pair_id='p35_'+key[:16],before=before,after=after,before_index=int(i),after_index=int(j),
                         before_words=len(x),after_words=len(y),overlap_similarity=similarity,sequence_similarity=seq,length_ratio=ratio,
                         before_numbers=numbers(before),after_numbers=numbers(after),before_names=names(before),after_names=names(after),
                         before_rules=vb,after_rules=va,before_violations=sum(vb.values()),after_violations=sum(va.values()),
                         before_paragraph_indices=asp[i],after_paragraph_indices=bsp[j],
                         pair_type='mechanical' if sum(va.values())<sum(vb.values()) else 'substantive',
                         eligible=not why,filter_outcomes=why)
                candidates.append(row)
                for w in why:stats[w]+=1
    jsonl('pairs.jsonl',candidates);dump('source_manifest.json',dict(origin_main=source,sources=sources))
    eligible=[r for r in candidates if r['eligible']]
    group=pd.DataFrame(eligible).groupby('notebook').agg(n=('pair_id','size'),mechanical=('pair_type',lambda x:(x=='mechanical').sum()))
    # Choose among random half-notebook splits without consulting model outcomes.
    rng=np.random.default_rng(SEED);best=None
    nbs=sorted(group.index)
    target_test=min(120,len(eligible)//2)
    prior_split=DATA/'split.json'
    fixed_train=set(json.loads(prior_split.read_text(encoding='utf-8'))['train_notebooks']) if prior_split.exists() else None
    for _ in range(1 if fixed_train else 10000):
        train=(fixed_train&set(nbs)) if fixed_train else set(rng.choice(nbs,len(nbs)//2,replace=False));test=set(nbs)-train
        tr=group.loc[sorted(train)];te=group.loc[sorted(test)]
        if tr.n.sum()<44 or (not fixed_train and te.n.sum()<target_test):continue
        diff=abs(tr.mechanical.sum()/tr.n.sum()-te.mechanical.sum()/te.n.sum())
        score=diff+.05*abs(tr.n.sum()-te.n.sum())/group.n.sum()
        if best is None or score<best[0]:best=(score,train,test)
    if best is None:
        raise RuntimeError(f'Insufficient pairs for split: {len(eligible)}; {group.to_dict()}')
    _,train_nbs,test_nbs=best
    train=sorted([r for r in eligible if r['notebook'] in train_nbs],key=lambda r:r['pair_id'])
    pool=sorted([r for r in eligible if r['notebook'] in test_nbs],key=lambda r:r['pair_id'])
    ids=np.random.default_rng(SEED+1).choice(len(pool),min(target_test,len(pool)),replace=False)
    test=sorted([pool[i] for i in ids],key=lambda r:r['pair_id'])
    dev_ids=np.random.default_rng(SEED+2).choice(len(train),min(8,len(train)-40),replace=False)
    dev=[train[i] for i in dev_ids]
    example_pool=[r for r in train if r['pair_id'] not in {x['pair_id'] for x in dev}]
    ex=np.random.default_rng(SEED+3).choice(len(example_pool),40,replace=False)
    rubric=[example_pool[i]['pair_id'] for i in ex]
    jsonl('train_pairs.jsonl',train);jsonl('test_pairs.jsonl',test);jsonl('dev_pairs.jsonl',dev)
    dump('split.json',dict(seed=SEED,train_notebooks=sorted(train_nbs),test_notebooks=sorted(test_nbs),
                           train_pairs=len(train),test_pool=len(pool),test_pairs=len(test),dev_ids=[r['pair_id'] for r in dev],rubric_source_ids=rubric))
    stats.update(readme_transitions=len(sources),aligned_candidates=len(candidates),eligible=len(eligible),train=len(train),test_pool=len(pool),test=len(test))
    dump('filter_counts.json',dict(stats));group.to_csv(DATA/'notebook_counts.csv')
    rules=git('show',source+':AGENTS.md')
    gradual=rules.split('### A gradual opening',1)[1].split('## Rules for notebooks',1)[0]
    style=rules.split('## Writing style',1)[1].split('### Check before you commit',1)[0]
    (DATA/'rules_v1.txt').write_text('### A gradual opening\n'+gradual+'\n## Writing style\n'+style,encoding='utf-8')
    (DATA/'rules_full_snapshot.txt').write_text(rules,encoding='utf-8')
    (DATA/'mechanical_checker_spec.json').write_text(json.dumps(dict(banned_pattern=BANNED,name_lexicon=NAMES,notes='Unweighted counts. Headings are excluded, so Title Case counts are zero. Harness counted only in a simple verb-plus-determiner pattern. Names use a fixed explicit lexicon; equal facts are not guaranteed.'),indent=2),encoding='utf-8')
    print(json.dumps(dict(stats),indent=2));print(group.to_string())

if __name__=='__main__':mine()
