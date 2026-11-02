"""Render definitions and illustrations for every style and every audit rule."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parent
AUDIT=ROOT/'data/expanded_audit'
MODELS=['gpt-6.1-sol','gpt-6.1-terra','claude-opus-5-5','claude-sonnet-5-5']
SHORT=['Sol','Terra','Opus','Sonnet']


def read_csv(name):
    with (AUDIT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def md_table(headers,rows):
    def cell(x):return str(x).replace('|','/').replace('\n','<br>')
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(cell(x) for x in row)+' |' for row in rows])


def audit_report_section():
    with (ROOT/'data/decision_audit/counts.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    summary=json.loads((ROOT/'data/decision_audit/summary.json').read_text(encoding='utf-8'));assert summary['complete']
    selected=[('negative_contrast','Unnecessary negative contrast'),('engagement_close','Generic engagement close'),
              ('clipped_rhythm','Repeated clipped rhythm'),('single_sentence_paragraphs','One-sentence paragraphs'),
              ('bold_leadins','Bold list labels'),('hashtag_tail','Generic hashtag tail')]
    def count(model,ident):return next(r for r in rows if r['writer_model']==model and r['style_id']==ident and r['zone']=='whole')
    table=md_table(['Decisions API pattern label',*SHORT],[[label,*[count(model,ident)['posts_labelled_present']+'/100' for model in MODELS]] for ident,label in selected])
    ordinary='; '.join(label+': '+', '.join(count(m,ident)['posts_labelled_present'] for m in MODELS) for ident,label in selected[:2])
    return '''### Forty patterns classified through the Decisions API

The [40-pattern guide](data/expanded_audit/STYLE_GUIDE.md) defines each pattern, explains its editing risk and gives an authored illustration, a clearer rewrite and a useful exception. It reuses the eight contextual criteria from [notebook 15](../15-analytical-writing-style/) and its [validation study](../17-writing-validation-extension/), then adds sourced candidates. Definitions are ours; classifications of the 400 posts come from the decision model, not manual annotation or regex inference.

The pinned classifier is `openai/gpt-6-luna-decisions-20261006`, called through OpenRouter's Decisions endpoint with fallback disabled. Each post receives 40 independent yes/no probability questions in each of six locations: whole post, opening paragraph, transition starts, point endings, conclusion and closing sentence. Two requests of 120 questions share the identical post, article and rubric. The writer's identity and previous drafts are withheld. The [frozen protocol](data/decision_audit/protocol.json) contains exact definitions and thresholds; [OpenAI's guide](https://developers.openai.com/api/docs/guides/decisions#ask-multiple-questions) explains independent questions. The API has no exposed effort setting; all four original writers used high effort.

```mermaid
flowchart LR
    A["400 saved posts + their source articles"] --> D1["Decisions API, request 1 per post<br/>whole / opening / transitions<br/>120 independent probabilities"]
    A --> D2["Decisions API, request 2 per post<br/>point endings / conclusion / closing<br/>120 independent probabilities"]
    D1 -. "wait; same input, no answer history" .-> D2
    D1 --> C["96,000 cached probabilities<br/>model labels and uncertainty"]
    D2 --> C
```

One post may have several labels. A pattern is labelled present at probability at least 0.5. The data also retain counts at 0.8, absences at 0.2 or below, and every intermediate probability. These thresholds were frozen before classification; they are descriptive operating choices, not calibrated guarantees. The 40-pattern analysis remains exploratory because its taxonomy was chosen after the writing run, and has no human gold labels.

![Six model-assigned pattern frequencies out of 100 posts per writer; classifier estimates rather than human judgments.](figures/main_expanded_styles.png)

'''+table+f'''

Each cell is a count of whole posts labelled by the classifier at the fixed 0.5 threshold. In Sol, Terra, Opus, Sonnet order, {ordinary}. Those are model estimates of the defined patterns; a lower count does not establish better writing. The guide shows all 40 definitions and counts, including zeroes.

The run returned {summary['valid_answers']:,}/{summary['predicate_answers']:,} readable predicate answers in {summary['requests']} requests, with {summary['whole_region_conflicting_labels']} cases where a region was positive while its whole-post label was negative. Independent answers need not be logically consistent. [These disagreements](data/decision_audit/region_consistency.csv) are preserved without manual correction; whole-post counts remain the directly returned whole-post judgments. Probabilities have not been calibrated against readers.

The [full classification table](data/decision_audit/classifications.csv) links every probability to its post, pattern and location. [Counts](data/decision_audit/counts.csv) include readable/missing totals, topic support, threshold sensitivity and article-bootstrap intervals. [Turn](data/decision_audit/by_turn.csv) and [family](data/decision_audit/by_family.csv) tables expose both family members. The earlier 70-rule [surface audit](data/expanded_audit/counts.csv) remains a diagnostic; keyword or layout matches do not assign these labels.
'''


def main():
    catalog=json.loads((AUDIT/'criteria.json').read_text(encoding='utf-8'))
    rows=read_csv('counts.csv');examples=read_csv('match_examples.csv')
    with (ROOT/'data/decision_audit/counts.csv').open(encoding='utf-8',newline='') as f:decision_counts=list(csv.DictReader(f))
    decision_summary=json.loads((ROOT/'data/decision_audit/summary.json').read_text(encoding='utf-8'))
    new_path=ROOT/'data/plain_prose_v2/decisions/counts.csv'
    intervention_counts=None
    if new_path.exists():
        with new_path.open(encoding='utf-8',newline='') as f:intervention_counts=list(csv.DictReader(f))
    source={x['id']:x for x in catalog['sources']}
    def cite(ids):return ', '.join('['+i+': '+source[i]['title']+']('+source[i]['url']+')' for i in ids)
    parts=['''# A guide to recurring AI writing patterns

This guide explains 40 patterns an editor may want to review in a LinkedIn draft. It gives definitions, reasons, examples and clearer alternatives. The first eight criteria come from the repository's earlier writing studies. The other patterns combine published research, editorial observations and explicit measurement choices for this study.

Every example labelled **Illustration** below is an authored teaching example, with invented facts used only to explain the pattern. It is not a response from a tested model or a factual claim about a real release. The suggested rewrites demonstrate an editing choice, not a universal rule. Measured excerpts, where available, are separately labelled and linked to stable response IDs.

The 400 posts were already collected before this guide and its 70 additional rules were defined. This is an exploratory audit. The original 111-entry inventory and its preregistered results remain unchanged. The guide is not an authorship detector, and recurring does not mean annoying to every reader. The categories overlap, so their counts must not be added into a score of bad writing. Each post's pattern labels come from the pinned Decisions API classifier, not manual classification or the surface counters.

## How to use the examples

First identify what the sentence needs to communicate. Then ask whether its wording or layout helps that task. A contrast can correct a real misconception. A short paragraph can help a phone reader. A technical noun can be more precise than a longer plain-language substitute. Remove a device when it adds little in that passage, rather than applying a ban to every occurrence.

The earlier validation study is a reason for this care: fresh model judges raised prose concerns on only 1.6% of opinions on previously flagged passages, compared with 1.2% on unflagged passages. Those are model judgments, not a human verdict. This study likewise reports its Decisions API classifications as model estimates. [Notebook 17](../../../17-writing-validation-extension/README.md) explains the earlier result.

## How the multi-label classification works

The classifier is `openai/gpt-6-luna-decisions-20261006` through OpenRouter, with fallback disabled. Each of the 400 posts is evaluated for all 40 patterns in six locations. Each yes/no probability is independent: a post can have several patterns, and the probabilities do not sum to one. A label uses p ≥ 0.5; p ≥ 0.8, p ≤ 0.2 and the ambiguous middle band are also retained. These thresholds were fixed before classification, but have not been calibrated against a human-labelled corpus. Definitions and useful exceptions form the rubric; formatting labels describe structure while contextual criteria ask whether the stated prose problem occurs.

The classifier sees the post and its source article, with no writer identity or previous drafts. It receives no tools or search. The intended poster supplied no biography. Whole-post judgments are primary; location judgments can disagree and are retained separately. Model labels are not independently verified defects. The separate surface measurements below are diagnostics and never determine an API label. [Protocol](../decision_audit/protocol.json), [all probabilities](../decision_audit/classifications.csv), [counts](../decision_audit/counts.csv).

## Contents
''']
    if intervention_counts is not None:
        parts[0]=parts[0].replace('The 400 posts were already collected before this guide and its 70 additional rules were defined.',
            'The 400 minimal-request posts were collected before this guide and its 70 surface rules were defined. A further 400 posts use the explicit prose prompt on the same sources.')
        parts[0]=parts[0].replace('Each of the 400 posts is evaluated for all 40 patterns in six locations.',
            'Each of the 800 posts across both prompt conditions is evaluated for all 40 patterns in six locations.')
        parts[0]=parts[0].replace('## Contents',
            'The per-pattern tables compare minimal request → explicit prose prompt, with 100 posts per writer in each condition. The unchanged classifier receives neither the condition nor its generating prompt. [Paired results](../prompt_comparison/patterns.csv) and [worked comparisons](../../README.md) show the intervention. Literal surface diagnostics and measured excerpts below retain their original minimal-request scope.\n\n## Contents')
    for i,style in enumerate(catalog['styles'],1):
        parts.append(f"{i}. [{style['name']}](#{style['id'].replace('_','-')})")
    parts.append('\n[All 70 counting rules](#all-70-counting-rules) · [Sources and evidence strength](#sources-and-evidence-strength) · [Reproduce](#reproduce)\n')
    for i,style in enumerate(catalog['styles'],1):
        es=[e for e in catalog['entries'] if e['style_id']==style['id']]
        parts.append(f"\n<a id=\"{style['id'].replace('_','-')}\"></a>\n\n## {i}. {style['name']}\n\n"
              f"**Definition.** {style['definition']}\n\n**Why review it?** {style['explanation']}\n\n"
              f"**Illustration.** {style['illustrative_example'].replace(chr(10), ' / ')}\n\n"
              f"**Clearer alternative.** {style['clearer_rewrite']}\n\n"
              f"**When it can help.** {style['useful_when']}\n\n**Basis.** {cite(style['source_ids'])}. The definition and editing explanation here are the study author's operational interpretation.\n")
        judged=[next(r for r in decision_counts if r['writer_model']==m and r['zone']=='whole' and r['style_id']==style['id']) for m in MODELS]
        if intervention_counts is not None:
            new=[next(r for r in intervention_counts if r['writer_model']==m and r['zone']=='whole' and r['style_id']==style['id']) for m in MODELS]
            parts.append('**Decisions API labels: minimal request → explicit prompt.** Each cell reports the two counts out of 100 whole posts per writer. These are model estimates under an unchanged rubric, not verified faults.\n')
            parts.append(md_table(['Cutoff',*SHORT],[[cut,*[b[field]+' → '+n[field] for b,n in zip(judged,new)]] for cut,field in [('p ≥ 0.5','posts_labelled_present'),('p ≥ 0.8','high_confidence_present')]])+'\n')
        else:
            parts.append('**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.\n')
            parts.append(md_table(SHORT,[[r['posts_labelled_present']+' ('+r['high_confidence_present']+')' for r in judged]])+'\n')
        if not es:
            parts.append('**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.\n')
            continue
        parts.append('**What is counted.** '+ '; '.join('`'+e['id']+'`: '+e['definition'] for e in es)+ '\n')
        selected=es if len(es)<=4 else es[:3]
        values=[]
        for e in selected:
            vals=[next(r for r in rows if r['model']==m and r['zone']=='whole' and r['criterion_id']==e['id']) for m in MODELS]
            is_fraction=e['id'].endswith('_share')
            values.append([e['label']+(' (mean share)' if is_fraction else ''),
                           *[f"{float(v['mean_value']):.1%}" if is_fraction else v['posts_containing']+'/100' for v in vals]])
        parts.append(md_table(['Observed surface measure',*SHORT],values)+'\n')
        parts.append('These are descriptions of the saved posts, not counts of justified faults. '+
                     ('Only the first three rules are displayed here; the complete table below includes the others. ' if len(es)>4 else '')+
                     'All wording rules also retain source-matching checks in [counts.csv](counts.csv).\n')
        matches=[x for x in examples if x['style_id']==style['id']]
        if matches:
            ex=matches[0]
            quote='\n'.join('> '+line if line else '>' for line in ex['normalized_context'].strip().splitlines())
            parts.append(f"**Measured excerpt, not the teaching example.** `{ex['post_id']}`, first saved positive example in deterministic order:\n\n{quote}\n\nCase and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.\n")
        else:parts.append('No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.\n')
    parts.append('''\n## All 70 counting rules

Every added rule is defined below and has its own illustration. These illustrations demonstrate positive matches. Exact regular expressions are saved in [criteria.json](criteria.json); all zeroes, model counts, locations and source-absence denominators are in [counts.csv](counts.csv). The 21 `jw_` rules are exact forms from Juzek and Ward's Appendix A. Several overlap with the original inventory; they are included for a faithful, separate check of that historical list, not as 21 new independent habits.

The noun-suffix, comma-plus-ing, three-span coordination, range and first-person rules are deliberately labelled **proxies**: they find text worth inspecting, not a linguistic parse, a false claim or a bad sentence. Broad proxy presence can saturate. For example, a nominal-suffix token appears in 398/400 posts. Many ordinary technical nouns meet that suffix rule, so this does not show that 398 posts are badly written. Layout fractions report their average value, rather than claiming that any nonzero share is excessive.
''')
    parts.append(md_table(['ID','Definition / exact scope','Illustration','Evidence source IDs'],[
        ['`'+e['id']+'`',e['definition'],'`'+e['illustrative_example'].replace('`','\\`')+'`',', '.join(e['source_ids'])]
        for e in catalog['entries']]))
    parts.append('''\n## Sources and evidence strength

Links and relevant source passages were checked November 1, 2026 in Toronto (November 2 UTC). Bibliographic dates are distinct from this access date. The source ledger classifies empirical research separately from editorial preferences. Research on scientific abstracts and older model generations does not validate a current LinkedIn claim. Practitioner sites and Wikipedia advice pages supply candidates only. Their authorship-detection, training-data and engagement claims are not adopted. Short paraphrases and original teaching examples are used; full source pages are not redistributed.
''')
    parts.append(md_table(['ID','Source','Type','Relevant passage / use'],[
        [x['id'],'['+x['title']+']('+x['url']+')',x['kind'],x['locator']+'. '+x['finding']] for x in catalog['sources']]))
    parts.append('''\n## Reproduce

From the experiment folder, run `python expanded_audit.py` and `python build_style_guide.py`. These commands read saved responses and make no model calls. The embedded notebook replays analysis without importing repository helpers. When full article files are absent, the frozen [source checks](source_overlap.json) verify the criteria and response fingerprints before replaying paired source-presence counts.

The surface audit adds no model calls. The minimal-request classifier uses 800 requests and returns 96,000 independent probabilities, with no new post generation. [Classifier usage](../decision_audit/usage.csv) retains native token/cost records; unavailable cache counters remain missing. [Per-post surface measures](per_post.csv), [per-turn diagnostics](by_turn.csv), [family diagnostics](by_family.csv), [summary](summary.json) and [protocol history](../PROTOCOL.md) preserve the distinct methods. Family rows expose both tested member models; two models do not represent every member of a provider's family. The original [111-entry inventory](../prose_lexicon.json) and [fixed counts](../main/fixed_prose_counts.csv) remain separately available.
''')
    parts.append(f"\nMinimal-request classifier reported cost: ${decision_summary['reported_cost_usd']:.6f}. This is separate from the original writers' usage. The endpoint exposes no effort control, and returned cache counters for {decision_summary['cache_read_counter_available_requests']}/800 requests. Missing counters do not mean zero reuse. Minimal-request region/whole label conflicts: {decision_summary['whole_region_conflicting_labels']}; these are not manually repaired.\n")
    if intervention_counts is not None:
        extra=json.loads((ROOT/'data/plain_prose_v2/decisions/summary.json').read_text(encoding='utf-8'))
        parts.append(f"\nThe explicit-prompt classifier adds {extra['requests']} requests, {extra['predicate_answers']:,} probabilities and ${extra['reported_cost_usd']:.6f} reported cost. Its region/whole conflicts are {extra['whole_region_conflicting_labels']}. Both conditions retain raw answers; no manual relabelling is applied. The prompt was designed after observing baseline habits and provides no human quality result.\n")
    text='\n'.join(parts).rstrip()+'\n'
    (AUDIT/'STYLE_GUIDE.md').write_text(text,encoding='utf-8')
    print('Style guide bytes:',len(text.encode()))


if __name__=='__main__':main()
