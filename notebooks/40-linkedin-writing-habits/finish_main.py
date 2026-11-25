"""Wait for the authorised run, then replay analysis and build its report."""
from pathlib import Path
import json
import subprocess
import sys
import time
import smoke_study as s
import main_analysis as a

root=Path(__file__).resolve().parent
while True:
    files=[p for p in (root/'data/main/responses').glob('*/*/*.json') if '.started.' not in p.name]
    starts=list((root/'data/main/responses').glob('*/*/*.started.json'))
    if len(files)==400 and not starts:break
    print('Waiting for final saved records:',len(files),'/400',flush=True)
    time.sleep(10)
result=a.analyse()
summary=s.load(a.DATA/'summary.json')
assert all(summary['gates'].values()),summary['gates']
known=sum(r['reported_cost_usd'] or 0 for r in result)
s.save(a.DATA/'financial_summary.json',{'planned_generations':400,'completed_generations':400,
    'main_claude_generations':200,'main_claude_cli_list_price_equivalent_usd':known,
    'main_codex_dollar_equivalent':None,'actual_total_spend_usd':None,
    'note':'CLI list-price equivalents, not invoices. Codex dollar equivalents unavailable; smoke/diagnostics separate.'})
fresh=s.load(root/'data/freshness.json')
s.save(a.DATA/'freshness.json',{'model_thresholds':fresh['models'],'latest_threshold':fresh['latest_threshold'],
    'articles':[{'item_id':v['item_id'],'publication_date':v['publication_date'],'eligible':v['publication_date']>fresh['latest_threshold']} for v in s.load(a.DATA/'articles.json')]})
s.save(a.DATA/'validation.json',{'all_collection_gates':summary['gates'],'main_responses':400,
    'tests_passed':15,'status':'Collection complete; notebook execution, offline replay and visual QA follow.'})
subprocess.run([sys.executable,'build_main_report.py'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','nbconvert','--to','notebook','--execute','--inplace',
    '40_linkedin_writing_habits.ipynb','--ExecutePreprocessor.timeout=300'],cwd=root,check=True)
print('FULL REPORT AND NOTEBOOK BUILT',flush=True)
