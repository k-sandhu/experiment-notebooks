"""Small review report and figure, built only from cached free-model probabilities."""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import smoke_study as s
import free_decision_pilot as f


def build():
    summary=s.load(f.OUT/'summary.json');assert summary['complete']
    protocol=s.load(f.OUT/'protocol_40.json')
    with (f.OUT/'classifications.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    whole=[r for r in rows if r['zone']=='whole']
    patterns=[]
    for style,definition in protocol['definitions'].items():
        vals=[r for r in whole if r['style_id']==style]
        counts=[sum(float(r['probability'])>=.5 for r in vals if r['writer_model']==model) for model in s.MODELS]
        patterns.append(dict(style_id=style,name=definition['name'],total=sum(counts),
                             at_0_8=sum(float(r['probability'])>=.8 for r in vals),counts=counts))
    patterns.sort(key=lambda r:(-r['total'],r['style_id']))
    s.save(f.OUT/'whole_post_patterns.json',patterns)
    by_style={r['style_id']:r for r in patterns}
    top=[by_style[k] for k in ['repeated_conclusion','negative_contrast','additive_contrast',
                              'generic_benefit','nominalization','formulaic_framing',
                              'single_sentence_paragraphs','invented_experience']]
    control_plan=s.load(f.OUT/'controls/protocol.json')
    controls={r['control_id']:r for r in [s.load(path) for path in (f.OUT/'controls/responses').glob('*.json')]}
    control_rows=[]
    for fixture in control_plan['fixtures']:
        record=controls[fixture['id']]
        for expected,styles in [(True,fixture['expected_present']),(False,fixture.get('expected_absent',[]))]:
            for style in styles:
                probability=record['parsed']['whole__'+style]['probability']
                control_rows.append(dict(control_id=fixture['id'],style_id=style,expected_present=expected,
                                         probability=probability,flag_at_0_5=probability>=.5,
                                         matches_authored_expectation=(probability>=.5)==expected))
    positives=[r for r in control_rows if r['expected_present']]
    negatives=[r for r in control_rows if not r['expected_present']]
    control_summary=dict(positive_expectations=len(positives),positive_flags=sum(r['flag_at_0_5'] for r in positives),
                         negative_expectations=len(negatives),negative_absences=sum(not r['flag_at_0_5'] for r in negatives),
                         unexpected=[r for r in control_rows if not r['matches_authored_expectation']],
                         human_validated=False)
    s.save(f.OUT/'controls/summary.json',control_summary)
    s.write_csv(f.OUT/'controls/expectations.csv',control_rows)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                         'figure.facecolor':'white','axes.facecolor':'white','savefig.dpi':170})
    fig,ax=plt.subplots(figsize=(10.2,5.2))
    y=np.arange(len(top))
    ax.barh(y-.18,[r['total'] for r in top],height=.34,color='#236b8e',label='Probability at least 0.5')
    ax.barh(y+.18,[r['at_0_8'] for r in top],height=.34,color='#b15a2b',hatch='//',label='Probability at least 0.8')
    ax.set_yticks(y,[r['name'] for r in top]);ax.invert_yaxis()
    ax.set_xlim(0,19);ax.set_xticks(range(0,20,2));ax.set_xlabel('Posts flagged by the classifier (19 classified posts)')
    ax.set_title('Only 1 of 760 whole-post judgments is positive at 0.5',loc='left',pad=15)
    for i,r in enumerate(top):
        ax.text(r['total']+.15,i-.18,str(r['total']),va='center',fontsize=9)
        ax.text(r['at_0_8']+.15,i+.18,str(r['at_0_8']),va='center',fontsize=9)
    ax.legend(loc='lower right',fontsize=9);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.tight_layout()
    target=f.ROOT/'figures/free_decision_kimi_flags.png'
    fig.savefig(target,bbox_inches='tight');plt.close(fig)
    headers='| Pattern | Sol / 5 | Terra / 4 | Opus / 5 | Sonnet / 5 | Total / 19 | At 0.8 / 19 |'
    table=[headers,'|---|---:|---:|---:|---:|---:|---:|']
    table += ['| '+r['name']+' | '+' | '.join(str(n) for n in r['counts'])+f" | {r['total']} | {r['at_0_8']} |" for r in patterns if r['total']]
    pid='01-kimi/gpt-6.1-sol/01'
    case=[r for r in rows if r['post_id']==pid and r['style_id']=='negative_contrast']
    example=['| Region | Returned probability | Flag at 0.5 |','|---|---:|---|']
    example += [f"| {r['zone']} | {float(r['probability']):.6f} | {'Yes' if float(r['probability'])>=.5 else 'No'} |" for r in case]
    text=f'''# Free-model classifications of the expanded-prompt Kimi preview

A prose-pattern classifier reads a proposed post and answers separate questions about its wording and layout. A post can receive several labels or none. The labels are judgments from that model, rather than verified writing defects. This preview applies the existing 40-pattern rubric to the saved Kimi posts, without generating another post or running the full 20-topic study.

## What was classified

There are 20 saved generations. Nineteen have a valid `<linkedin_post>` pair. Terra's first response omitted the tags and remains an unreadable format outcome; it is excluded rather than counted as a post with no patterns. The classification denominators are Sol 5, Terra 4, Opus 5 and Sonnet 5. Read [all 20 outputs](../simple_prose_v3_kimi_pilot/outputs.md) beside this audit.

The live [OpenRouter decision catalogue](https://openrouter.ai/api/v1/models?output_modalities=decisions) lists Span-01 Lite under standard and free aliases for one checkpoint. The checked Mercury, Jev and Clef free aliases had no active provider. The dated free route and its zero-price endpoint are frozen in [catalogue.json](catalogue.json). Links and pricing were checked on 2026-11-02.

| Model | Pinned version | Provider and interface | Size and precision | Output settings | Why included |
|---|---|---|---|---|---|
| Respan Span-01 Lite | `respan/span-01-lite-20260925:free`; native replies identify `respan/span-01-lite-20260925` | Respan through OpenRouter `/api/alpha/decisions` | Not published in the checked catalogue | Typed Bernoulli probabilities; no exposed effort setting; no tools/search; provider pinned, fallback disabled and maximum input/output prices zero | The currently available free decision checkpoint |

Each post receives 40 questions in each of six regions: the whole post, opening, transition starts, point endings, conclusion and closing. Regions overlap and the same post is context for each question. This gives 240 probabilities per post and 4,560 in total. The classifier receives the source and post, with writer identity, prompt, previous drafts and previous labels withheld. Full definitions, exceptions and question text are in [protocol_40.json](protocol_40.json); the [style guide](../expanded_audit/STYLE_GUIDE.md) explains each pattern.

## Returned flags

A returned probability of at least 0.5 counts as a flag. The 0.8 column uses a stricter cutoff. Neither cutoff has been calibrated against human judgments. For example, three flagged posts out of five means the classifier marked the pattern in three of that writer's five readable posts; it is not a three-out-of-five writing-quality score.

{chr(10).join(table)}

The table lists nonzero whole-post patterns. All 40 patterns, including zeroes and the region results, remain in [counts.csv](counts.csv), with every probability in [classifications.csv](classifications.csv). Only one of 760 whole-post judgments is positive at 0.5, and none is positive at 0.8. The one flag is repeated conclusion in `01-kimi/gpt-6.1-terra/05`, at probability 0.50605124. This is a near-floor result that cannot rank the writers. A change in classifier could change these counts, so they must not be compared with the earlier paid audit as evidence that the prompt improved.

![Counts of the most frequently flagged prose patterns among 19 Kimi posts, at probability cutoffs 0.5 and 0.8.](../../figures/free_decision_kimi_flags.png)

The horizontal axis counts posts, not occurrences. Blue bars use the 0.5 cutoff and orange hatched bars use 0.8. The rows show the one positive pattern and seven specific concerns; zeroes are tied and are not ranked. Patterns can overlap, so bar lengths must not be summed as a number of defective posts. The disappearance of the only flag at 0.8 shows sensitivity to the threshold, not demonstrated classification accuracy.

## One saved classification

For `{pid}`, one question asks whether the rubric's unnecessary-negative-contrast pattern occurs in the whole post. The definition is: a claim is framed by denying an alternative the reader may never have proposed. Its useful exception is a contrast that corrects an actual misunderstanding. The program keeps the returned probability and applies the cutoff without manually deciding whether the model is right.

{chr(10).join(example)}

This example was fixed to Sol's first Kimi post rather than selected for an extreme score. A region-positive/whole-negative answer is retained as an inconsistency, not silently repaired. Across the full audit there are {summary['whole_region_conflicts']} such conflicts; inspect [region_consistency.csv](region_consistency.csv). Agreement would not by itself establish correctness either.

Ten conflicts concern one-sentence paragraphs, three concern participial clauses and one concerns negative contrast. Region extracts assemble sentence windows, so their layout can contribute to local formatting flags; that is a possible explanation, not a validated cause. In Opus's second post, negative contrast has probability 0.077288285 for the whole post and 0.6805229 for the point-ending extract. The primary table retains the whole-post answer, while the regional disagreement remains visible in the saved data.

## Sanity checks after the near-floor result

Before relying on the near-zero counts, three authored control posts were sent through the same whole-post classifier: an exaggerated rhetorical post, a post with obvious markdown/emoji/hashtag formatting, and a plain factual post. The source and expected patterns were saved before these calls. These controls are separate from the 19 measured posts and are not a human-labelled validation set.

At 0.5, the classifier flagged {control_summary['positive_flags']} of {control_summary['positive_expectations']} intended positive instances and left all {control_summary['negative_absences']} of {control_summary['negative_expectations']} intended negative instances unflagged. It recognized the negative contrast, not-just expansion, engagement close, hashtags, bold formatting, emoji layout and title-case heading controls. It did not flag the intended question-and-answer pivot, assigning it probability 0.06356258. This shows that it can recognize several obvious patterns, while also exposing a missed intended example. It does not validate its judgments on subtle prose. See the [fixtures](controls/protocol.json), [returned probabilities](controls/responses/) and [expectation table](controls/expectations.csv).

## Limits and reproduction

This is one article and one classifier. Five successive drafts within a conversation are not independent topic samples. No human gold labels, factual-accuracy score or engagement outcome was collected, and no writer ranking or full-study prompt improvement is established. The free model's context limit, size, precision and weight openness are not published in the checked catalogue.

All 114 primary requests returned 4,560 readable probabilities and native reported cost zero. One earlier 120-question diagnostic timed out with no cost counter; a separate two-question transport control and the three pattern-control requests succeeded at zero cost. These five diagnostic/control attempts are excluded from style counts. The [protocol](PROTOCOL.md) records the batch amendment, full request caches, blinding and tracing. Native cache-read/write counters were not exposed and are not treated as zero.

Run `python free_decision_pilot.py analyse` and `python build_free_decision_report.py` to rebuild this report from cached replies without model calls. `python validate_free_decision_pilot.py` checks full private request hashes and a source-free, network-blocked replay. Public derivatives redact publisher text; exact wire requests and responses remain together in git-ignored private caches. No paid fallback or new writer generation was used.
'''
    (f.OUT/'REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    print('Saved',f.OUT/'REPORT.md')
    for r in patterns[:8]:print(r['name'],r['total'],r['counts'],r['at_0_8'])


if __name__=='__main__':build()
