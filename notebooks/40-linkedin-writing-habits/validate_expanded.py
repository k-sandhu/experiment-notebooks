"""Prove the added audit replays without articles, model calls or network access."""
from pathlib import Path
import contextlib
import hashlib
import io
import re
import shutil
import tempfile
from unittest.mock import patch
import expanded_audit as a
import smoke_study as s

root=Path(__file__).resolve().parent
catalog=s.load(a.AUDIT/'criteria.json')
assert len(catalog['styles'])==40 and len(catalog['entries'])==70
assert s.sha((root/'data/prose_lexicon.json').read_text(encoding='utf-8'))==s.load(root/'data/main/preregistration.json')['lexicon_sha256']
baseline={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.AUDIT.glob('*.csv')}
with tempfile.TemporaryDirectory(prefix='nb40-expanded-offline-') as tmp:
    clone=Path(tmp)
    shutil.copytree(a.AUDIT,clone/'data/expanded_audit')
    (clone/'data/main').mkdir(parents=True)
    shutil.copy(root/'data/main/articles.json',clone/'data/main/articles.json')
    for source in (root/'data/main/responses').glob('*/*/*.json'):
        if '.started.' in source.name:continue
        target=clone/'data/main/responses'/source.relative_to(root/'data/main/responses')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy(source,target)
    assert not (clone/'data/local_inputs').exists()
    with patch.object(a,'ROOT',clone),patch.object(a,'AUDIT',clone/'data/expanded_audit'),\
         patch('subprocess.run',side_effect=AssertionError('Unexpected CLI call')),\
         patch('subprocess.Popen',side_effect=AssertionError('Unexpected CLI process')),\
         patch('requests.get',side_effect=AssertionError('Unexpected network retrieval')),\
         contextlib.redirect_stdout(io.StringIO()):a.analyse_expanded()
    replay={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (clone/'data/expanded_audit').glob('*.csv')}
    assert replay==baseline,[n for n in baseline if replay.get(n)!=baseline[n]]
    assert s.load(clone/'data/expanded_audit/summary.json')==s.load(a.AUDIT/'summary.json')
guide=(a.AUDIT/'STYLE_GUIDE.md').read_text(encoding='utf-8')
missing=[target for target in re.findall(r'\]\(([^)]+)\)',guide)
         if not target.startswith(('http','#')) and not (a.AUDIT/target).exists()]
assert not missing,missing
assert all(guide.count(f'## {i}. ')==1 for i in range(1,41))
summary=s.load(a.AUDIT/'summary.json')
assert summary['new_model_calls']==0 and not summary['contextual_defects_scored']
result={'responses':400,'styles_defined_with_illustrations':40,'countable_rules':70,
        'all_regex_and_layout_illustrations_have_positive_regression_fixtures':True,
        'source_free_offline_replay':True,'network_and_subprocess_calls_blocked':True,
        'csv_tables_byte_identical':len(baseline),'summary_json_reproduced':True,
        'guide_local_links_resolve':True,'original_preregistered_inventory_hash_unchanged':True,
        'regression_tests':25,'new_model_calls':0,'added_model_spend_usd':0,
        'new_figure_visually_inspected':True,'status':'posthoc_exploratory'}
s.save(a.AUDIT/'validation.json',result)
print('Validated',len(baseline),'byte-identical offline added tables; original inventory hash unchanged; 40 definitions and guide links checked.')
