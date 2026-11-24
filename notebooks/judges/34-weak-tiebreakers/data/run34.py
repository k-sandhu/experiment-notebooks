import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
try:
    for name in ['setup34.py','transport34.py','generator34.py','from_33/reading_rules_v1.py','design34.py','analysis34.py']:
        exec(compile((Path('data')/name).read_text(encoding='utf-8'),name,'exec'))
    if os.environ.get('NB_STAGE')=='development':
        dev=[json.loads(s) for s in (DATA/'from_33/exam_v1.jsonl').read_text(encoding='utf-8').splitlines()]
        dev=[i for i in dev if i['split']=='dev']
        strong=run_parallel(baseline_job,[(i,n,'dev10d') for i in dev for n in STRONG],'Development strong cache')
        route=routing(dev,strong);ids={r['item_id'] for r in route if r['route']=='disagreed'}
        selected=[i for i in dev if i['item_id'] in ids]
        idx={(r['item_id'],r['judge'],r['order']):r for r in strong}
        alone=run_parallel(baseline_job,[(i,n,'dev10d') for i in selected for n in [*WEAK,'Decisions',*THIRD]],'Development alone')
        contextual=run_parallel(contextual_job,[(i,n,c,idx) for i in selected for c,names in [('reasons',WEAK),('revise',STRONG)] for n in names],'Development context')
        items,rows,routes=dev,strong+alone+contextual,route
        pd.DataFrame(rows).to_csv(DATA/'development_judgments.csv',index=False)
        save(DATA/'development_routes.json',routes)
        log('development_collection_complete',items=len(dev),disagreements=len(ids),context_judgments=len(contextual),
            unreadable_context=sum(bool(r['lenient_unreadable_type']) for r in contextual),generator_changes='none')
        print('Development items',len(dev),'disagreements',len(ids),'unreadable context',sum(bool(r['lenient_unreadable_type']) for r in contextual),flush=True)
    else:
        items,rows,routes=run_study()
    if PROFILE=='smoke' or os.environ.get('NB_STAGE')=='development':
        DATA=DATA/'smoke';FIG=FIG/'smoke';DATA.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
    tables=summarize_study(items,rows,routes)
    figures34(tables)
    worked_cases(items,rows,routes,tables)
    if PROFILE=='full' and os.environ.get('NB_STAGE')!='development':validate34(items,rows,routes,tables)
    print('RUN COMPLETE',flush=True)
except Exception as exc:
    if type(exc).__name__=='CollectorQuotaStop':quota_handoff()
    raise
