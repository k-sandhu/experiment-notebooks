"""Controlled prompt intervention, reusing the frozen CLI and classifier harnesses."""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import json
import smoke_study as s
import full_study as f
import main_analysis as a
import decision_audit as d

ROOT=Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
INTERVENTION=ROOT/'data/plain_prose_v2'
CONDITION='plain-prose-v2-high-conversation'
SMOKE_TOPICS=['01-kimi','14-seti']
N_TOPICS=20
N_POSTS=5
MAX_NEW_CALLS=5
PRIMARY_TARGETS=['hashtag_tail','single_sentence_paragraphs','negative_contrast','clipped_rhythm',
    'additive_contrast','emoji_layout','bold_density','formulaic_framing','invented_experience','bold_leadins']


def register_prompt_study():
    INTERVENTION.mkdir(exist_ok=True)
    articles=s.load(ROOT/'data/main/articles.json')
    raw=(ROOT/'data/prompt_conditions/plain_prose_v2.txt').read_text(encoding='utf-8')
    assert raw.count('{{complete_article_text}}')==1
    template=raw.replace('{{complete_article_text}}','{article}')
    base=s.load(ROOT/'data/main/preregistration.json')
    classifier=s.load(ROOT/'data/decision_audit/protocol.json')
    design=copy.deepcopy(base);design.pop('registered_at_utc',None)
    design.update(protocol=CONDITION,initial_prompt_template=template,
        prompt_file_sha256=s.sha(raw),baseline_protocol_sha256=s.sha(s.canonical(base)),
        classification_protocol_sha256=s.sha(s.canonical(classifier)),
        primary_targets=PRIMARY_TARGETS,additional_target='engagement_close',
        smoke='Two frozen topics, all four writers, five sequential turns: 40 generations. Reuse these same slots in the full 400; no content-based tuning.',
        cost='400 new generation limit; Claude $1 per invocation. 800 classifier requests, existing $5 reported-cost guard. Codex dollars unavailable; no new generation judge.',
        uncertainty='2000 paired article-bootstrap draws. Within each writer keep all five turns per article together; compare matched article means. No significance ranking or independent-phrase claim.',
        comparison='Same articles, writers, CLI controls and short followups. Fresh conversations for this condition. Baseline was collected earlier, so time/backend changes are a confound.',
        classification='Unchanged pinned Decisions model, all 40 definitions, six regions and thresholds .5/.8/.2. No writer identity, condition or prompt in classifier input.',
        quality='Readability, source attribution flags, length and structural compliance; no human quality or engagement outcome. No claim that fewer labels establish better writing.',
        study_status='Prospective intervention on post-baseline-selected targets; exploratory on these 20 frozen topics.')
    path=INTERVENTION/'preregistration.json'
    if path.exists():
        old=s.load(path);assert all(old[k]==v for k,v in design.items()),'Intervention plan changed after registration'
    else:s.save(path,{'registered_at_utc':datetime.now(timezone.utc).isoformat(),**design})
    manifest=INTERVENTION/'articles.json'
    if manifest.exists():assert s.load(manifest)==articles
    else:s.save(manifest,articles)
    dp=INTERVENTION/'decisions/protocol.json'
    if dp.exists():assert s.load(dp)==classifier
    else:s.save(dp,classifier)
    return articles,template


def collect_prompt_study(max_new=MAX_NEW_CALLS,smoke=False):
    articles,template=register_prompt_study()
    s.PROMPT_TEMPLATE=template
    f.MAIN=INTERVENTION;f.PROTOCOL=CONDITION
    selected=[x for x in articles if x['item_id'] in SMOKE_TOPICS] if smoke else articles
    f.preregister=lambda:selected
    f.collect(max_new)


def intervention_records():
    return [s.load(p) for p in sorted((INTERVENTION/'responses').glob('*/*/*.json')) if '.started.' not in p.name]


def configure_prompt_classifier():
    assert (INTERVENTION/'decisions/protocol.json').exists()
    d.DECISIONS=INTERVENTION/'decisions'
    d.decision_records=intervention_records
    d.freeze_decision_protocol=lambda:s.load(INTERVENTION/'decisions/protocol.json')


def classify_prompt_study(posts=2,max_new=4):
    configure_prompt_classifier()
    d.collect_decisions(posts,max_new)


def analyse_prompt_study():
    a.DATA=INTERVENTION
    model_rows=a.analyse()
    summary=s.load(INTERVENTION/'summary.json')
    summary['protocol']=CONDITION
    summary['scope']='Prompt intervention on the same 20 topics; descriptive patterns, not a human quality score.'
    s.save(INTERVENTION/'summary.json',summary)
    configure_prompt_classifier();d.analyse_decisions()
    return model_rows


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['register','smoke','collect','classify','analyse'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS)
    parser.add_argument('--posts',type=int,default=2)
    args=parser.parse_args()
    if args.action=='register':register_prompt_study()
    elif args.action in ['smoke','collect']:collect_prompt_study(args.max_new,args.action=='smoke')
    elif args.action=='classify':classify_prompt_study(args.posts,args.max_new)
    else:analyse_prompt_study()
