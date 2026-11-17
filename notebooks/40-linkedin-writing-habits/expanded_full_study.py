"""Full expanded-constraints writer collection and deterministic cached export."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import copy
from pathlib import Path
import random
import shutil
import subprocess

import smoke_study as s
import tagged_kimi_pilot as p

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/simple_prose_v3_full'
PRIVATE=ROOT/'data/local_inputs/simple_prose_v3_full'
PILOT=ROOT/'data/simple_prose_v3_kimi_pilot'
PROTOCOL='expanded-prose-v3-full-high'
N_TOPICS=20
N_POSTS=5
MAX_NEW_WRITER_CALLS=5
ARTICLE_WORKERS=2


def register():
    articles=s.load(ROOT/'data/main/articles.json')
    assert len(articles)==N_TOPICS
    for a in articles:assert s.sha((ROOT/a['local_input']).read_text(encoding='utf-8'))==a['text_sha256']
    initial=(ROOT/'data/prompt_conditions/simple_prose_v3.txt').read_text(encoding='utf-8')
    followup=(ROOT/'data/prompt_conditions/simple_prose_v3_followup.txt').read_text(encoding='utf-8')
    pilot=s.load(PILOT/'preregistration.json')
    versions={name:subprocess.run([s.shutil.which(name+'.cmd') or s.shutil.which(name),'--version'],
                    capture_output=True,text=True,check=True).stdout.strip() for name in ['codex','claude']}
    assert initial==pilot['initial_template'] and followup==pilot['followup']
    assert versions==pilot['cli_versions']
    design=dict(protocol=PROTOCOL,models=s.MODELS,effort='high',articles=articles,
                initial_template=initial,followup=followup,initial_sha256=s.sha(initial),followup_sha256=s.sha(followup),
                cli_versions=versions,topics=20,posts_per_model_article=5,planned_posts=400,
                imported_kimi_posts=20,maximum_fresh_writer_calls=380,concurrent_article_blocks=ARTICLE_WORKERS,
                conversations='One explicit conversation per model/article; five sequential turns per block. Fresh blocks except the 20 matching Kimi pilot responses.',
                imports='Import every matching Kimi slot including the tag failure. No quality selection or new generation for those slots.',
                comparison='Original 400 minimal-prompt responses versus this expanded-prompt condition, reclassified through the same zero-price Span-01 Lite checkpoint.',
                classifier='All 40 patterns and six regions. Whole-post labels are primary; assembled regional formatting labels are diagnostics. No new paid classification.',
                formats='Exactly one nonempty tag pair. Preserve raw output and outside text; do not guess a body for invalid tags.',
                failures='No content retries. Record CLI/tool/session failures, invalid tags and unattempted slots separately.',
                caveats='Prompt and targets were chosen after baseline and one-topic pilot inspection. Writer aliases are undated; baseline was collected earlier. No human quality or engagement outcome.',
                inference='Compare readable-post frequencies, retain format failures, use paired article-cluster bootstrap intervals with 2000 draws. No cross-classifier comparison to earlier paid labels.',
                costs='Writer CLIs only, high effort, tools/search disabled, Claude $1 invocation limit. Report unknown Codex dollars and native cache usage. Classifier maximum prices zero.')
    path=OUT/'preregistration.json'
    if path.exists():
        old=s.load(path);assert all(old[k]==v for k,v in design.items()),'Full-run plan changed after registration'
    else:s.save(path,dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),**design))
    return design


def import_pilot(design):
    manifest=[]
    for src in sorted((PILOT/'responses/01-kimi').glob('*/*')):
        if not src.is_file() or '.started.' in src.name:continue
        relative=src.relative_to(PILOT)
        dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==src.read_bytes()
        else:shutil.copyfile(src,dest)
        manifest.append(dict(source=src.relative_to(ROOT).as_posix(),destination=dest.relative_to(ROOT).as_posix(),
                             text_sha256=s.sha(src.read_text(encoding='utf-8'))))
    assert len(list((OUT/'responses/01-kimi').glob('*/*.json')))==20
    s.save(OUT/'imported_pilot.json',manifest)


def collect(max_new=MAX_NEW_WRITER_CALLS):
    assert 0<=max_new<=380
    design=register();import_pilot(design)
    isolation=s.isolation_dir();s.isolation_dir=lambda:isolation
    p.OUT=OUT;p.PRIVATE=PRIVATE;p.PROTOCOL=PROTOCOL
    # Read-only CLI context is shared; each article/model has its own explicit session ID.
    candidates=[a for a in design['articles'] if a['item_id']!='01-kimi']
    random.Random(20261102).shuffle(candidates)
    jobs=[];remaining=max_new
    for article in candidates:
        if remaining<=0:break
        allowance=min(20,remaining);remaining-=allowance
        jobs.append((article,allowance))
    events=[];new=0
    def run(job):
        article,allowance=job
        block=copy.deepcopy(design);block['article']=article
        source=(ROOT/article['local_input']).read_text(encoding='utf-8')
        return article['item_id'],p.collect(allowance,design=block,source=source,write_export=False)
    with ThreadPoolExecutor(max_workers=ARTICLE_WORKERS) as pool:
        futures={pool.submit(run,job):job[0]['item_id'] for job in jobs}
        for future in as_completed(futures):
            try:
                item,result=future.result();new+=result['new_calls'];events.extend(dict(item_id=item,**e) for e in result['errors'])
            except Exception as exc:events.append(dict(item_id=futures[future],error=str(exc)))
    s.save(OUT/'collection_events.json',events)
    export()
    print('FRESH WRITER CALLS',new,'EVENTS',len(events),flush=True)


def records():
    return [s.load(path) for path in sorted((OUT/'responses').glob('*/*/*.json')) if '.started.' not in path.name]


def export():
    data=records();usage=[];post_rows=[]
    text=['# Expanded-constraints full-run posts\n\nFour writers, 20 frozen articles and five successive standalone posts per model/article conversation. Kimi slots are imported from the matching pilot.\n']
    for model in s.MODELS:
        part=[r for r in data if r['requested_model']==model]
        valid=[r for r in part if r['status']=='ok' and r['post_body'] is not None]
        warm=[r for r in part if r['turn']>1]
        total=sum(r['input_total'] or 0 for r in warm);read=sum(r['cache_read_tokens'] or 0 for r in warm)
        costs=[r.get('reported_cost_usd') for r in part]
        usage.append(dict(model=model,planned_posts=100,responses=len(part),tagged_readable_posts=len(valid),
                          cli_failures=sum(r['status']!='ok' for r in part),invalid_tag_posts=sum(r['status']=='ok' and r['post_body'] is None for r in part),
                          unattempted_posts=100-len(part),outside_text_posts=sum(bool(r['extra_text_present']) for r in part),
                          distinct_readable_posts=len({s.normalise(r['post_body']) for r in valid}),
                          mean_words_readable=sum(len(s.words(r['post_body'])) for r in valid)/len(valid) if valid else None,
                          warm_input_tokens=total,warm_cache_read_tokens=read,warm_cache_read_fraction=read/total if total else None,
                          reported_cost_usd=sum(costs) if costs and all(v is not None for v in costs) else None))
        text.append(f'## {model}\n')
        for r in sorted(part,key=lambda r:(r['item_id'],r['turn'])):
            pid=f"{r['item_id']}/{model}/{r['turn']:02d}"
            post_rows.append(dict(post_id=pid,item_id=r['item_id'],writer_model=model,turn=r['turn'],status=r['status'],
                                  format_status=r['format_status'],readable=r['status']=='ok' and r['post_body'] is not None,
                                  words=len(s.words(r['post_body'])) if r['post_body'] is not None else None,
                                  outside_text=bool(r['extra_text_present']),request_sha256=r['request_sha256']))
            warning=(f"CLI generation failure ({r['status']}); no post was returned.\n\n" if r['status']!='ok' else
                     'Tag format failure; exact raw response follows.\n\n' if r['post_body'] is None else '')
            text.append(f"### {r['item_id']}, post {r['turn']}\n\n{warning}{r['post_body'] if r['post_body'] is not None else r['text']}\n")
            if r['extra_text_present']:text.append(f"Outside text before:\n\n{r['text_before']}\n\nOutside text after:\n\n{r['text_after']}\n")
    s.write_csv(OUT/'writer_usage.csv',usage);s.write_csv(OUT/'posts.csv',post_rows)
    summary=dict(protocol=PROTOCOL,planned_posts=400,responses=len(data),complete=len(data)==400,
                 models=usage,known_reported_writer_cost_usd=sum(r['reported_cost_usd'] or 0 for r in data),
                 actual_total_cost='Unknown; Codex dollar equivalents are unavailable.',imported_pilot_posts=20)
    s.save(OUT/'summary.json',summary)
    (OUT/'outputs.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')
    print(s.canonical(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['register','collect','export'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_WRITER_CALLS);args=parser.parse_args()
    if args.action=='register':register()
    elif args.action=='collect':collect(args.max_new)
    else:export()
