"""Render the current three-paid-classifier explanation and portable notebook."""
from pathlib import Path
import re
import nbformat
import pandas as pd

import smoke_study as s
import paid_prose_analysis as analysis
import validate_paid_decisions as validation

ROOT=Path(__file__).resolve().parent
OUT=analysis.OUT
SHORT={'gpt-6.1-sol':'Sol','gpt-6.1-terra':'Terra','claude-opus-5-5':'Opus','claude-sonnet-5-5':'Sonnet'}
JUDGES={'gpt':'OpenAI Decisions','jev':'Jev 1.14','mercury':'Mercury Decide','span_free':'Span-01 Lite (free)'}


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',
        *['| '+' | '.join(str(value).replace('|','\\|').replace('\n',' ') for value in row)+' |' for row in rows]])


def quote(text):return '\n'.join('> '+line if line else '>' for line in text.strip().splitlines())


PLOTS=r'''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'figure.dpi':140,'savefig.dpi':170,'font.family':'DejaVu Sans','font.size':10,
 'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.titlesize':13,
 'figure.facecolor':'white','axes.facecolor':'white','axes.labelcolor':'#303841'})
BLUE='#396B9D';ORANGE='#C46B36';GRAY='#77838E'
patterns=pd.read_csv(OUT/'paired_patterns.csv');usage=pd.read_csv(OUT/'writer_usage.csv')
metrics=pd.read_csv(OUT/'post_metrics.csv');api=pd.read_csv(OUT/'classifier_usage.csv')
fig,axes=plt.subplots(1,2,figsize=(11,4.8))
for ax,pop,title in [(axes[0],'strict','Valid tagged bodies'),(axes[1],'raw','All nonempty replies')]:
 part=patterns.query("population==@pop and model=='all' and zone=='whole' and threshold==0.5 and style_id=='negative_contrast'").set_index('classifier').loc[CLASSIFIERS]
 x=np.arange(3);ax.bar(x-.18,100*part.baseline_fraction,.34,color=BLUE,label='Minimal request')
 ax.bar(x+.18,100*part.expanded_fraction,.34,color=ORANGE,label='Expanded constraints')
 for i,(_,r) in enumerate(part.iterrows()):ax.text(i,max(100*r.baseline_fraction,100*r.expanded_fraction)+3,f'{int(r.baseline_present)} → {int(r.expanded_present)}',ha='center')
 ax.set_xticks(x,[JUDGES[x].replace(' ','\n',1) for x in CLASSIFIERS]);ax.set_ylim(0,105)
 ax.set_ylabel('Paired replies labelled present (%)');ax.set_title(f'{title}\nn = {int(part.paired_posts.iloc[0])} pairs')
 ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0].legend(fontsize=9);fig.suptitle('All three paid classifiers label fewer negative contrasts',fontsize=15,fontweight='bold')
fig.tight_layout();fig.savefig(FIG/'paid_prose_contrasts.png',bbox_inches='tight');plt.close(fig)

targets=['negative_contrast','additive_contrast','formulaic_framing','single_sentence_paragraphs','bold_density',
         'engagement_close','nominalization','reflective_pose','question_pivot','invented_experience'][::-1]
fig,axes=plt.subplots(1,3,figsize=(14,6.3),sharey=True)
for ax,ident in zip(axes,CLASSIFIERS):
 part=patterns.query("classifier==@ident and population=='raw' and model=='all' and zone=='whole' and threshold==0.5").set_index('style_id').loc[targets]
 y=np.arange(len(part));ax.barh(y-.18,100*part.baseline_fraction,.34,color=BLUE,label='Minimal request')
 ax.barh(y+.18,100*part.expanded_fraction,.34,color=ORANGE,label='Expanded constraints')
 ax.set_yticks(y,part.name);ax.set_xlim(0,105);ax.set_xlabel('Paired replies labelled present (%)')
 ax.set_title(JUDGES[ident]);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
axes[0].legend(loc='lower right',fontsize=8)
fig.suptitle('The measured frequency depends on the classifier and pattern',fontsize=15,fontweight='bold')
fig.tight_layout();fig.savefig(FIG/'paid_prose_patterns.png',bbox_inches='tight');plt.close(fig)

shared=pd.read_csv(OUT/'shared_classifier_counts.csv')
styles=['negative_contrast','additive_contrast','nominalization','invented_experience','formulaic_framing','single_sentence_paragraphs']
names=patterns.drop_duplicates('style_id').set_index('style_id').name
judges=[*CLASSIFIERS,'span_free'];changes=np.zeros((len(styles),4))
fig,ax=plt.subplots(figsize=(10,5))
for i,style in enumerate(styles):
 for j,ident in enumerate(judges):
  r=shared.query('classifier==@ident and style_id==@style').iloc[0]
  changes[i,j]=100*(r.expanded_present-r.baseline_present)/r.paired_posts
im=ax.imshow(changes,cmap='RdBu',vmin=-100,vmax=100,aspect='auto')
for i,style in enumerate(styles):
 for j,ident in enumerate(judges):
  r=shared.query('classifier==@ident and style_id==@style').iloc[0]
  ax.text(j,i,f'{int(r.baseline_present)} → {int(r.expanded_present)}',ha='center',va='center',color='white' if abs(changes[i,j])>45 else '#202020')
ax.set_xticks(np.arange(4),[JUDGES[x].replace(' ','\n',1) for x in judges]);ax.set_yticks(np.arange(len(styles)),[names[x] for x in styles])
ax.set_title('The same 399 pairs receive different labels from different classifiers')
fig.colorbar(im,ax=ax,label='Expanded minus minimal frequency (percentage points)',shrink=.8)
fig.tight_layout();fig.savefig(FIG/'paid_prose_shared_classifiers.png',bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(12,4.4),sharey=True);x=np.arange(4)
for ax,ident in zip(axes,CLASSIFIERS):
 part=patterns.query("classifier==@ident and population=='raw' and model!='all' and zone=='whole' and threshold==0.5 and style_id=='negative_contrast'").set_index('model').loc[WRITERS]
 ax.bar(x-.18,100*part.baseline_fraction,.34,color=BLUE,label='Minimal request');ax.bar(x+.18,100*part.expanded_fraction,.34,color=ORANGE,label='Expanded constraints')
 for i,(_,r) in enumerate(part.iterrows()):ax.text(i,max(100*r.baseline_fraction,100*r.expanded_fraction)+3,f'{int(r.baseline_present)}→{int(r.expanded_present)}',ha='center',fontsize=9)
 ax.set_xticks(x,[SHORT[m] for m in WRITERS]);ax.set_ylim(0,110);ax.set_title(JUDGES[ident]);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0].set_ylabel('Replies labelled negative contrast (%)');axes[0].legend(fontsize=8)
fig.suptitle('Writer comparisons change with the classifier',fontsize=15,fontweight='bold');fig.tight_layout()
fig.savefig(FIG/'paid_prose_by_writer.png',bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(11,4.7));x=np.arange(4)
part=usage.query("condition=='expanded'").set_index('model').loc[WRITERS]
axes[0].bar(x,part.strict_readable,color=BLUE,label='Valid tagged body')
axes[0].bar(x,part.invalid_tag_nonempty,bottom=part.strict_readable,color=ORANGE,label='Text, invalid tags')
for i,(_,r) in enumerate(part.iterrows()):
 for count,bottom in [(r.strict_readable,0),(r.invalid_tag_nonempty,r.strict_readable)]:
  if count:axes[0].text(i,bottom+count/2,str(int(count)),ha='center',va='center',color='white',fontweight='bold')
axes[0].set_xticks(x,[SHORT[m] for m in WRITERS]);axes[0].set_ylim(0,108);axes[0].set_ylabel('Effective new-condition replies (100 per writer)')
axes[0].set_title('Missing tags remain after the empty reply is recovered');axes[0].legend(fontsize=8,loc='lower left')
for condition,offset,color,label in [('baseline',-.18,BLUE,'Minimal request'),('expanded',.18,ORANGE,'Expanded constraints')]:
 part=usage.query('condition==@condition').set_index('model').loc[WRITERS]
 axes[1].bar(x+offset,100*part.warm_cache_fraction,.34,color=color,label=label)
 for i,value in enumerate(part.warm_cache_fraction):axes[1].text(i+offset,100*value+1,f'{100*value:.0f}%',ha='center',fontsize=9)
axes[1].set_xticks(x,[SHORT[m] for m in WRITERS]);axes[1].set_ylim(0,105);axes[1].set_ylabel('Cache reads / known warm-turn input tokens (%)')
axes[1].set_title('Most writer input on later turns came from cache');axes[1].grid(axis='y',alpha=.15);axes[1].set_axisbelow(True)
fig.tight_layout();fig.savefig(FIG/'paid_prose_format_cache.png',bbox_inches='tight');plt.close(fig)

phrases=pd.read_csv(OUT/'reference_phrases.csv').iloc[::-1];fig,ax=plt.subplots(figsize=(10,4.8));y=np.arange(len(phrases))
ax.barh(y-.17,phrases.baseline_posts,.32,color=BLUE,label='Minimal request');ax.barh(y+.17,phrases.expanded_posts,.32,color=ORANGE,label='Expanded constraints')
ax.set_yticks(y,[f'{SHORT[r.model]} · {r.zone.replace("_"," ")}\n“{r.phrase}”' for _,r in phrases.iterrows()])
ax.set_xlabel('Replies containing exact phrase absent from their source article');ax.set_xlim(0,20)
ax.set_title('Several recurring hooks and engagement phrases disappear');ax.legend(fontsize=9)
fig.tight_layout();fig.savefig(FIG/'paid_prose_phrases.png',bbox_inches='tight');plt.close(fig)

conflicts=pd.read_csv(OUT/'region_conflicts.csv');fig,ax=plt.subplots(figsize=(8.5,4.3));x=np.arange(3)
for condition,offset,color,label in [('baseline',-.18,BLUE,'Minimal request'),('expanded',.18,ORANGE,'Expanded constraints')]:
 values=[len(conflicts.query('classifier==@ident and condition==@condition')) for ident in CLASSIFIERS]
 ax.bar(x+offset,values,.34,color=color,label=label)
 for i,value in enumerate(values):ax.text(i+offset,value+10,str(value),ha='center',fontsize=9)
ax.set_xticks(x,[JUDGES[j] for j in CLASSIFIERS]);ax.set_ylabel('Region-positive / whole-negative judgments')
ax.set_title('Regional answers can conflict with whole-post answers');ax.legend(fontsize=9)
fig.tight_layout();fig.savefig(FIG/'paid_prose_conflicts.png',bbox_inches='tight');plt.close(fig)
'''


def build():
    result=s.load(OUT/'summary.json');assert result['complete'] and all(r['case_records']==800 for r in result['classifiers'])
    patterns=pd.read_csv(OUT/'paired_patterns.csv');metrics=pd.read_csv(OUT/'post_metrics.csv');usage=pd.read_csv(OUT/'writer_usage.csv')
    shared=pd.read_csv(OUT/'shared_classifier_counts.csv');agreement=pd.read_csv(OUT/'classifier_agreement.csv')
    examples=s.load(OUT/'examples.json');articles=s.load(ROOT/'data/main/articles.json')
    protocol=s.load(ROOT/'data/paid_decision_full/protocol.json');api={x['classifier']:x for x in result['classifiers']}
    styles=protocol['definitions'];strict_n=result['strict_pairs'];raw_n=result['raw_pairs']
    def pat(style,ident='gpt',pop='raw',writer='all',zone='whole',threshold=.5):
        return patterns.query('classifier==@ident and population==@pop and model==@writer and zone==@zone and style_id==@style and threshold==@threshold').iloc[0]
    def arrow(r,denominator=False):
        return f'{int(r.baseline_present)} → {int(r.expanded_present)}'+(f' / {int(r.paired_posts)}' if denominator else '')
    def ex(item,writer,turn):return next(r for r in examples if (r['item_id'],r['writer'],r['turn'])==(item,writer,turn))
    def prob(case,style,condition='expanded'):
        return ' · '.join(f"{JUDGES[ident]} {case['whole_probabilities'][ident][condition][style]:.3f}" for ident in ['gpt','jev','mercury'])
    def sentences(text):return s.sentences(text)
    def first(text):return sentences(text.split('\n\n')[0])[0]
    def last(text):
        paragraphs=[p for p in text.split('\n\n') if p.strip() and not all(w.startswith('#') for w in p.split())]
        return sentences(paragraphs[-1])[-1]
    contrast=', '.join(f"{JUDGES[i]} {arrow(pat('negative_contrast',i))}" for i in api)
    nominal=', '.join(f"{JUDGES[i]} {arrow(pat('nominalization',i))}" for i in api)
    intro='''# Changing LinkedIn prose and checking the classifier

A person wants to share news about an AI tool on LinkedIn. They give a writing model the announcement and ask for a post. A useful draft explains what changed and why a reader might care. The person still needs to check its facts and decide whether its voice fits.

Asking for another draft gives them a choice. Yet the alternatives can keep returning to a familiar opening, a succession of short paragraphs and an invitation to comment. The wording changes while the same editing work returns.

**Illustrative example, not measured data.** Suppose an announcement says a support tool can search old tickets. A draft might begin, “This isn't just search. It's a new way to work.” The opening delays the useful fact and denies an alternative the reader did not propose. A direct account could explain which tickets become searchable.

Now add a complication: the tool searches archived tickets but cannot open attachments. That distinction helps the reader. Removing every negative word would lose useful information. The editing question concerns what a phrase does in context.

One approach leaves the writing choices to the model. Another leaves angle and length open while discouraging stock framing, unnecessary contrasts, repetitive rhythm and generic endings. The second approach might save editing work, replace one habit with another or make its output harder to extract.

Some changes are easy to count. A hashtag is a visible string. Deciding whether a contrast is unnecessary requires reading it with the source. A separate classification model can help review many drafts, but its judgments are another measurement choice that needs checking.

For example, two classifiers might both recognize a hashtag ending and disagree about whether a factual comparison is rhetorical padding. Paying for a classifier does not establish that its labels match readers. Giving the same passages and definitions to several classifiers reveals which conclusions depend on that choice.

This study asks whether prose guidance changes recurring LinkedIn habits across four writers, and whether three paid classifiers agree about the changes. It keeps literal wording, output-format failures and model-assigned editorial labels separate. It does not add overlapping labels into a writing-quality score.'''
    summary=f'''## Study summary

Four writers produced five numbered drafts from each of 20 frozen AI news articles under a minimal request and an expanded prose prompt: **400 effective replies per condition**. One empty capacity failure in the new condition was recovered from its original first-turn context; all other replies stayed unchanged. The writers used high effort through their CLIs, with tools and search disabled.

Three dated paid decision models each classify all 800 replies for 40 patterns in six regions. A **pattern frequency** counts replies whose returned probability is at least 0.5. In the {raw_n} matched nonempty pairs, negative-contrast labels change as follows: **{contrast}**. In the {strict_n} valid-body pairs, the respective counts are {', '.join(arrow(pat('negative_contrast',i,'strict')) for i in api)}. These are classifier judgments, not verified faults.

The classifiers disagree sharply about some remaining prose. Noun-heavy wording is {nominal}. There are **108 nonempty tag failures**, which select the strict population. No human preference, factual accuracy or editing-time outcome was measured. The prompt and taxonomy were selected after baseline inspection, and writing conditions were collected at different times, so this is an exploratory comparison of the complete prompting package.'''
    workflow=f'''```mermaid
flowchart TD
 A["20 frozen AI articles<br/>21,219 words"] --> B["Minimal request<br/>4 writers × 5 drafts = 400 cached replies"]
 A --> C["Expanded prose prompt<br/>400 original slots + one authorized empty-failure retry"]
 C --> D["400 effective new replies<br/>{strict_n} valid tagged bodies; 108 exact raw replies"]
 B --> E["Source + one measured reply<br/>same 40 definitions and six regions"]
 D --> E
 E --> G["3 paid decision models<br/>800 cases each; two question batches per case"]
 G --> H["{result['total_valid_probabilities']:,} valid probabilities<br/>strict pairs and all nonempty pairs kept separate"]
 H --> I["Article-cluster comparisons<br/>classifier disagreements and worked examples"]
 B --> J["Literal phrase/layout audit<br/>source-overlap checks and native cache counters"]
 D --> J
 J --> I
```

For the Kimi case, the same saved article enters each writer conversation. Five replies are collected in order. Each classifier then sees one measured reply and its source, without the writer's identity or other drafts. Tag extraction controls entry to the strict analysis; exact raw text remains available for the secondary audit. Literal phrase counting is a separate path and never supplies contextual API labels.'''
    sections=[]
    source_table=table(['Example ID','Published','Article','Words'],[(a['item_id'],a['publication_date'],f"[{a['title']}]({a['url']})",a['words']) for a in articles if a['item_id'] in ['01-kimi','02-tb-screening','06-protostar','14-seti']])
    full_table=table(['ID','Published','Article','Words'],[(a['item_id'],a['publication_date'],f"[{a['title']}]({a['url']})",a['words']) for a in articles])
    (OUT/'ARTICLES.md').write_text('# The 20 frozen source articles\n\n'+full_table+'\n',encoding='utf-8',newline='\n')
    sections.append(('1. What the writers were given',f'''The 20 public sources, published October 23–30, cover models, research, AI products, security, publishing and infrastructure. They were fresh when collected and remain frozen. This is a varied convenience sample of English AI news, not a random LinkedIn sample.

{source_table}

[The complete index](data/paid_prose_comparison/ARTICLES.md) gives all 20 titles, dates, URLs and lengths. The sources total 21,219 words; the longest has 3,197 and Kimi has 296. Length is not equalized, so some sources offer more possible angles.

Both conditions receive exactly the same saved title, date and substantive article text. Extraction removes page furniture while retaining meaningful lists, captions and corrections. The [manifest](data/main/articles.json) records extraction methods and hashes. Publisher-containing inputs stay local and excluded from Git; the public data retain source URLs and fingerprints.

The [freshness record](data/main/freshness.json) checks the articles against documented writer cutoffs or release-date fallbacks. All three paid classifier releases also precede the articles. These checks do not prove that an opaque backend had never encountered the material. Phrase analysis separately excludes exact wording already present in the corresponding source.

**Measured input example: `01-kimi`.** The article reports a Kimi K3.1 Pro release, benchmark comparisons and prices. It attributes a pelican-drawing test to its author. The intended LinkedIn poster supplied no biography. A draft can attribute the test to the author; a claim that the poster personally ran it needs separate evidence. First-person analysis alone is allowed by the rubric. This role distinction becomes an informative classifier-disagreement case below.'''))
    model_rows=[]
    for name,ident,call,reason in [('GPT-6.1 Sol','gpt-6.1-sol','codex exec / resume','One tested GPT writer'),('GPT-6.1 Terra','gpt-6.1-terra','codex exec / resume','Second tested GPT writer'),
        ('Claude Opus 5.5','claude-opus-5-5','claude -p / resume','One tested Claude writer'),('Claude Sonnet 5.5','claude-sonnet-5-5','claude -p / resume','Second tested Claude writer')]:
        model_rows.append([name,f'`{ident}`; undated alias','OpenAI' if ident.startswith('gpt') else 'Anthropic',f'`{call}`','Not published','High; tools/search off',reason])
    catalogue=s.load(ROOT/'data/paid_decision_full/catalogue.json')
    reasons={'gpt':'Continuity with the original paid audit; exact baseline requests can be reused','jev':'Structured-decision model from a second vendor','mercury':'Third vendor to check whether conclusions depend on one classifier'}
    for ident,r in api.items():
        model_rows.append([JUDGES[ident],'`'+r['model']+'`',catalogue['models'][ident]['endpoint']['provider_name'],'OpenRouter Decisions API','Not published','Typed questions; no effort control exposed; no tools',reasons[ident]])
    model_rows.append(['Span-01 Lite','`respan/span-01-lite-20260925`','Respan','Earlier zero-price OpenRouter audit','Not published','No new calls; retained on the common sample','Historical free comparator, not a fourth current paid model'])
    models=table(['Model','Pinned ID / identity limit','Provider','How called','Size / precision','Output settings','Why included'],model_rows)
    initial=(ROOT/'data/prompt_conditions/simple_prose_v3.txt').read_text(encoding='utf-8').strip()
    followup=(ROOT/'data/prompt_conditions/simple_prose_v3_followup.txt').read_text(encoding='utf-8').strip()
    sections.append(('2. Prompts and model access',f'''The minimal condition asks only, “Write a LinkedIn post based on the following article,” followed by the complete article. Its later turns contain exactly “Generate another post.” The expanded condition keeps angle, voice, length, structure and ending open while adding 15 prose constraints and an output boundary.

The expanded task begins with this excerpt; [the complete exact template](data/prompt_conditions/simple_prose_v3.txt) retains all 15 constraints, the tag request and the article placeholder.

```text
Write a LinkedIn post based on the article below. Use your judgment about the angle, voice, length, structure and ending.

<constraints>
- Return plain prose without hashtags, emojis, decorative symbols, headings, bold text, bullet points or numbered lists.
```

The remaining constraints address paragraph rhythm, contrasts, stock framing and transitions, generic benefits, word choice, staged revelations, mechanical sentence shapes, trailing significance clauses, hedging, endings, invented experience and punctuation. Necessary factual distinctions remain allowed. The [writer registration](data/simple_prose_v3_full/preregistration.json) preserves the exact initial and continuation strings and their hashes.

The exact continuation is:

```text
{followup}
```

Each model/article block uses one native conversation. Turns two through five resume it, so previous drafts remain visible. “Independent” requests a standalone post; it does not make the observations statistically independent. The constraint list, continuation wording and tag contract change together, preventing an effect from being assigned to one component.

{models}

Writer aliases have no immutable dated revision exposed here. Codex was `0.160.1`; Claude Code was `2.1.296`. The retry uses the same Codex version and high-effort command. Isolation removes notebook/style files and disables tools, search and skills from the writer context; native logs show no tool use. This is a test through the specified CLIs, including their runtime behavior, rather than a claim about unwrapped model checkpoints.

The classifiers are pinned to the dated canonical IDs returned by the live catalogue. Each request names one provider and disables fallback; successful native responses are checked against that dated model and provider. The typed endpoint exposes no effort setting. No unsupported reasoning parameter is invented, and no tools or search are supplied.

### How the study got here

A smoke test checked output diversity and collection code. An earlier source-auditing prompt led some Claude replies to include commentary; the present prompt removes that procedure. Its full writing set and free classification audit were retained before the request for paid classifiers. The current comparison uses three paid models, imports only exact matching historical OpenAI baseline requests, and preserves the earlier free labels as a separately identified comparator. Registrations, transport amendments and earlier results remain in [protocol history](data/PROTOCOL.md).'''))
    retry=ex('14-seti','gpt-6.1-sol',2)
    call_graph='''```mermaid
flowchart TD
 A["Cached writer archive<br/>codex exec / claude -p; high; five-turn blocks"] --> P["Measured reply + source"]
 F["Native first-turn prefix<br/>Codex CLI thread/fork; no generation"] --> R["Sol · codex exec resume<br/>one authorized retry; unchanged continuation"]
 R --> P
 P --> G["OpenAI Decisions · OpenRouter<br/>up to 120 typed probabilities per batch"]
 P --> J["Jev · OpenRouter<br/>up to 120 typed probabilities per batch"]
 P --> M["Mercury Decide · OpenRouter<br/>up to 120 typed probabilities per batch"]
 G -->|"next batch until 240; exact cache reused"| G
 J -->|"next batch until 240"| J
 M -->|"next batch; transport-only retries with pacing"| M
 G --> C["Wait for all cases<br/>native responses retained; no cross-model handoff"]
 J --> C
 M --> C
 C --> T["Separate per-classifier tables<br/>article-cluster analysis; no combined score"]
```'''
    sections.append(('3. From a reply to a pattern label',f'''A strict new-condition post contains exactly one nonempty, non-nested `<linkedin_post>...</linkedin_post>` pair. Missing, malformed, repeated or empty tags do not trigger a rewrite or a guessed body. Text before and after valid tags is saved separately. The baseline keeps its older frozen wrapper/note parser because its prompt requested no tags.

The strict paired comparison contains **{strict_n} pairs** with readable post bodies in both conditions. The secondary audit contains **400 pairs** and measures every nonempty invalid-tag new reply as exact raw text, retaining even a lone closing tag. It is labelled `raw_unparsed_response`, not a repaired post body. The raw sensitivity was declared before the full free-run labels and retained for this paid comparison.

### Recovering the empty generation without later drafts

The original Sol SETI second turn returned an empty capacity error. Its conversation later continued, so resuming its latest state would expose the retry to posts three through five. The installed CLI's session-control operation instead forks through the first completed turn. The native history reference, byte boundary and first assistant reply are verified against the original prefix; the original session stays unchanged. Actual generation then uses `codex exec resume`, high effort, the original exact continuation and the original tool/search restrictions.

The replacement returns 176 words but omits valid tags. Its opening is:

{quote(first(retry['expanded']))}

The expected format wraps the complete post in one tag pair. Observed `post_body` remains null, so this reply enters only the raw-text analysis. The [complete retry](data/simple_prose_v3_retry/OUTPUT.md), [native provenance](data/simple_prose_v3_retry/fork.json) and [retry protocol](data/simple_prose_v3_retry/protocol.json) preserve this outcome. It is one of 108 current tag failures, not a second empty generation.

Only this failed slot is replaced for the current comparison. Original turns three through five remain on their original branch and did not see the replacement. A sensitivity excludes the entire Sol SETI block. The historical failure is retained; the new condition therefore has 401 actual generation attempts and 400 effective replies.

### What each region means

The API receives the whole measured text and five additional regions: first paragraph; transition starts (first 12 whitespace-delimited words of later sentences and paragraphs); point endings (last sentences of substantive paragraphs before the last); conclusion (last substantive paragraph); and closing (its last sentence). Hashtag-only final paragraphs are excluded from substantive endings. Sentence splitting is a fixed heuristic, not a linguistic gold standard.

Each region is supplied beside the complete source and reply. An instance must occur within that named region. Extracts can overlap, and assembling sentence windows changes visible layout. Whole-text labels are primary; regional formatting labels remain diagnostics. Opening-sentence and 30-word inventories supplement the phrase audit without changing classifier regions.

### Typed questions and the counting rule

Each nonempty reply has 240 predicates: 40 patterns in six regions. A **predicate** is one yes/no question such as whether an unnecessary negative contrast occurs in the whole reply. Separate probabilities allow multiple labels on a post; the values do not sum to one. The exact question form is:

```json
{{"whole__negative_contrast": {{
  "type": "noul",
  "instructions": "Under the RUBRIC definition and exceptions for negative_contrast, does an instance occur in region whole? Use the whole post and source for context.",
  "criteria": {{"true": "The defined pattern occurs in the specified region.", "false": "The defined pattern is absent from the specified region."}}
}}}}
```

The rubric defines this pattern as denying an alternative the reader may never have proposed and allows correction of an actual misunderstanding. The state contains the source, whole reply, regions and all definitions with useful exceptions. It treats article and reply as data, not instructions, and withholds writer identity, prompting condition and other drafts. Literal string counters never supply contextual labels.

At the main threshold, probability 0.70 becomes present and 0.30 absent. Counts at 0.2 and 0.8 show dependence on that operating choice; none is calibrated against human labels. **Illustrative counting example:** four of ten paired replies labelled before and one after means 40% versus 10%, a decrease of 30 percentage points. An unavailable probability is excluded for that predicate, never filled with zero.

Intervals resample the 20 articles 2,000 times, retaining all available paired drafts within a sampled article and averaging article-level changes. The central 95% of those changes is reported. Tables retain post-weighted changes too, since tag survival can alter article weights. These intervals cover variation across this topic set, conditional on classifier and aliases; they exclude classifier bias, prompt selection and backend drift. There is no multiple-comparison correction for the exploratory 40-pattern audit.

{call_graph}

Classifiers do not exchange answers. Two three-region batches normally supply 120 probabilities each, with identical state and disjoint question sets. Exact cached OpenAI baseline requests are reused. Mercury's rejected requests are recovered with slower pacing and transport-only retries; valid answers are never retried for their content or confidence. Provider failures stay in the request ledger, apart from labels about prose.'''))
    selected=['negative_contrast','additive_contrast','single_sentence_paragraphs','bold_density','formulaic_framing','nominalization','invented_experience']
    comparison_table=table(['Pattern','OpenAI strict / raw','Jev strict / raw','Mercury strict / raw'],[
        [styles[style]['name'],*[arrow(pat(style,ident,'strict'))+' / '+arrow(pat(style,ident)) for ident in api]] for style in selected])
    intervals=table(['Classifier','Negative contrast, raw pairs','Article-weighted change','95% article-cluster interval'],[
        [JUDGES[ident],arrow(pat('negative_contrast',ident),True),f"{pat('negative_contrast',ident).article_weighted_change_pp:+.1f} pp",
         f"[{pat('negative_contrast',ident).article_cluster_95_low_pp:+.1f}, {pat('negative_contrast',ident).article_cluster_95_high_pp:+.1f}] pp"] for ident in api])
    sections.append(('4. Which changes survive a different classifier',f'''All three paid classifiers label fewer negative contrasts under the expanded prompt. Compare the left panel's {strict_n} matched valid-body pairs with the right panel's 400 matched nonempty pairs. Blue is the minimal request and orange the expanded constraints; each annotation gives counts before and after. The vertical scale is a percentage, not a writing-quality score.

![Negative-contrast frequencies from three paid classifiers, with strict valid-body and all-nonempty populations shown separately.](figures/paid_prose_contrasts.png)

{intervals}

The intervals describe source-to-source variation in the paired change for each classifier. They cannot establish that one classifier is right, and the five drafts from an article are not treated as independent topics. The effect is a comparison of the complete prompt package: prose constraints, explicit standalone continuation and output tags.

Other patterns show both shared movements and large differences in level. The next figure uses all 400 nonempty pairs at 0.5. Its ten patterns were selected to cover contrasts, framing, layout, endings, noun-heavy wording and experience claims; all 40 remain in the linked tables.

![Ten selected pattern frequencies, with one panel per paid classifier and identical measured replies.](figures/paid_prose_patterns.png)

{comparison_table}

Each table cell shows the strict arrow first and raw-text arrow second. The corresponding denominators are {strict_n} and 400; [the full table](data/paid_prose_comparison/paired_patterns.csv) retains the denominator for each predicate, all thresholds and every writer. The strict population is selected by tag compliance, so it cannot stand in for all new writing.

Noun-heavy counts are {nominal}. The identical rubric allows necessary technical nouns. OpenAI's change has an article-cluster interval of [{pat('nominalization').article_cluster_95_low_pp:+.1f}, {pat('nominalization').article_cluster_95_high_pp:+.1f}] percentage points, including zero; Mercury's zero count is a floor. These are different decisions on identical passages, with no human-labelled set to choose between them.

The additive criterion concerns correction or escalation, rather than only the string “not just.” Jev labels 75 expanded replies while that literal string occurs in none; this gap needs contextual validation, not a claim of 75 verified wording-rule violations.

Literal formatting gives a firmer observation: all 400 new measured replies contain zero hashtag strings and zero Markdown bold spans. Classifier labels may describe generic hashtag tails or repeated emphasis, which are contextual definitions rather than exact string counts. A visible reduction does not establish reader preference for the result.

The threshold sensitivity repeats every comparison at 0.2 and 0.8. At 0.8, negative contrast is {', '.join(JUDGES[i]+' '+arrow(pat('negative_contrast',i,threshold=.8)) for i in api)}. Lower frequencies at a higher cutoff reflect the operating rule, not automatically greater accuracy. Categories at a floor cannot rank writers on that criterion.'''))
    common_styles=['negative_contrast','additive_contrast','nominalization','invented_experience','formulaic_framing','single_sentence_paragraphs']
    shared_table=table(['Pattern',*JUDGES.values()],[[styles[style]['name'],*[f"{int(shared.query('classifier==@ident and style_id==@style').iloc[0].baseline_present)} → {int(shared.query('classifier==@ident and style_id==@style').iloc[0].expanded_present)}" for ident in JUDGES]] for style in common_styles])
    disagreement_table=table(['Pair of classifiers','Baseline negative-contrast disagreements','New negative-contrast disagreements'],[
        [JUDGES[one]+' / '+JUDGES[two],*[int(agreement.query('classifier_1==@one and classifier_2==@two and condition==@condition and style_id=="negative_contrast"').iloc[0].disagreements) for condition in ['baseline','expanded']]]
        for one,two in [('gpt','jev'),('gpt','mercury'),('gpt','span_free')]])
    sections.append(('5. What changes when the classifier changes',f'''The earlier free audit used Span-01 Lite. A fair comparison removes the recovered slot from every classifier, leaving the same **399 matched pairs**. The figure and table below use that common sample. They do not compare 399 old replies with 400 new ones, and they do not substitute one model's labels for another's.

![Four classifiers evaluated on the identical 399-pair sample. Cells show baseline-to-expanded counts and colour shows the frequency change.](figures/paid_prose_shared_classifiers.png)

{shared_table}

Each cell contains the original count and expanded-prompt count. Colour shows expanded minus original frequency in percentage points; numbers make the direction readable without colour. Different levels, floors or directions on the same passages expose dependence on the classifier. The comparison does not establish that paid labels are more accurate.

{disagreement_table}

Disagreement counts concern particular replies, not just similar aggregate rates: two classifiers can flag the same number of posts while choosing different ones. The [agreement table](data/paid_prose_comparison/classifier_agreement.csv) includes individual positive counts, disagreement totals and chance-adjusted agreement, called Cohen's kappa. Kappa is undefined when both have no variation; agreement is not accuracy without a reference set.

At 0.5, the numbers of categories with zero labels in both current paid arms are {', '.join(JUDGES[i]+' '+str(api[i]['zero_both_patterns']) for i in api)} out of 40. A floor cannot establish absence of the prose behavior, and near-floor counts cannot support a writer ranking. The free audit's 17 zero-both categories on its original paired sample are retained as historical evidence, rather than presented as verified clean writing.

The [common-sample table](data/paid_prose_comparison/shared_classifier_counts.csv) holds all 40 patterns. Classifier labels remain separate; there is no majority vote, manual reconciliation or sum of different patterns into a defect score.'''))
    writer_table=table(['Writer',*['Negative contrast: '+JUDGES[i] for i in api]],[[SHORT[writer],*[arrow(pat('negative_contrast',ident,writer=writer)) for ident in api]] for writer in s.MODELS])
    sections.append(('6. Writers, openings, transitions and endings',f'''Every writer contributes 100 nonempty pairs to the current raw-text comparison. The following figure shows negative-contrast labels for each writer under each paid classifier. The axes and source posts are identical, so differences between panels arise from the classifier, not a different sample.

![Per-writer negative-contrast counts before and after constraints, shown separately for three paid classifiers.](figures/paid_prose_by_writer.png)

{writer_table}

Counts over 100 translate directly into percentages. The plot can identify a habit worth reviewing under a given rubric/model combination, but it is not a quality league table. Writer-family statements cover only the two tested GPT writers and two tested Claude writers through these CLIs and conversation design. They do not establish a property of every model in either family.

The phrase audit provides a separate view of exact wording. It normalizes case and apostrophes, builds two-to-eight-word sequences and excludes a phrase when that exact sequence occurs in its corresponding article. A recurring candidate requires at least five replies across at least three articles for the same writer and location. A sequence counts once per reply. Common connective phrases can pass this source-absence rule.

![Selected recurring baseline hooks and endings, compared with their exact expanded-prompt counts.](figures/paid_prose_phrases.png)

{table(['Writer','Location','Exact phrase','Original','Expanded'],[[SHORT[r.model],r.zone.replace('_',' '),'“'+r.phrase+'”',f'{int(r.baseline_posts)}/100',f'{int(r.expanded_posts)}/100'] for _,r in pd.read_csv(OUT/'reference_phrases.csv').iterrows()])}

These examples were selected from recurring baseline openings, transitions and endings. Expanded counts are computed directly, even when below the candidate threshold; a missing filtered row is never called zero. The changes describe these exact strings, not proof that every opening or ending became varied. [All recurring strings](data/paid_prose_comparison/common_phrases.csv) and [the original 111 fixed expressions](data/paid_prose_comparison/fixed_phrases.csv) remain available by location.

The [family phrase table](data/paid_prose_comparison/family_phrases.csv) requires the five-reply/three-article support rule separately in both tested members. It keeps both counts visible rather than assigning one model's phrase to a whole family. Repeated attribution or connective wording is not automatically an editorial fault.

The API also asks where a contextual pattern occurs. These selected questions address the opening, move into another point, point endings, conclusion and final sentence, using all 400 raw pairs:

{table(['Location / selected pattern',*[JUDGES[i] for i in api]],[[zone.replace('_',' ')+' / '+styles[style]['name'],*[arrow(pat(style,ident,zone=zone)) for ident in api]] for zone,style in [('opening_paragraph','generic_opener'),('transition_starts','question_pivot'),('point_endings','negative_contrast'),('conclusion','repeated_conclusion'),('closing','engagement_close')]])}

Regions overlap: a closing sentence is inside the conclusion. These rows are separate questions and cannot be summed or forced to agree with the whole-text answer. Sentence-window layout labels remain diagnostics because extracting windows changes the layout. Exact repetition and contextual prose labels answer different questions.'''))
    format_table=table(['Writer','Valid tagged bodies','Nonempty invalid tags','Mean words: original → new','Warm cached input: new'],[
        [SHORT[writer],f"{int(usage.query('condition=="expanded" and model==@writer').iloc[0].strict_readable)}/100",
         int(usage.query('condition=="expanded" and model==@writer').iloc[0].invalid_tag_nonempty),
         f"{usage.query('condition=="baseline" and model==@writer').iloc[0].mean_words:.1f} → {usage.query('condition=="expanded" and model==@writer').iloc[0].mean_words:.1f}",
         f"{100*usage.query('condition=="expanded" and model==@writer').iloc[0].warm_cache_fraction:.1f}%"] for writer in s.MODELS])
    sections.append(('7. Output boundaries and cache usage',f'''Recovering an empty request does not repair a missing output boundary. The new condition now has 400 nonempty replies, but only {strict_n} valid enclosed bodies: Sol 27/100, Terra 65/100 and both Claude writers 100/100. The 108 invalid-tag replies include the recovered Sol post. No prose is regenerated because of its wording, tags or classifier label.

![New-condition tag compliance and provider-reported warm-turn input-cache fractions for the writing models.](figures/paid_prose_format_cache.png)

{format_table}

The left panel counts effective replies, so its bars total 100 each. The original empty capacity attempt is retained in the attempt history, outside these 400 effective outputs. A missing tag is a format failure, not proof of wrong content. The raw audit preserves the entire reply, including any lone closing tag, and keeps it distinct from a readable enclosed post.

The right panel sums native cache-read tokens and divides by total known input tokens on turns two through five. Codex's cumulative counters are differenced into per-turn increments; Claude's categories are combined without counting cumulative session cost twice. Unknown counters are excluded from the ratio. The authorized retry had 0 cached input tokens out of 8,901 input tokens after its earlier context was restored later; its known counters are included.

Resuming conversations preserves a shared article/history prefix and permits cache reuse. The observed fractions do not prove that this strategy maximizes savings: no cache-policy experiment was run, and earlier drafts remain visible. Length stays model-chosen; the table's word counts are descriptive, not a quality preference.

For the paid classifiers, 800 exact historical OpenAI requests are reused locally. Their full request bodies and hashes match; no new provider request or live trace is emitted for a cache hit. Their historical reported cost of $2.2653584 is recorded separately from new spend.

Native Decisions response usage exposes no cache-read count. A read-only generation-metadata probe for each paid provider also returns null cached-token and cache-discount fields. [Those three samples](data/paid_decision_full/cache_metadata_probes.json) document the availability check. Null means unknown, not zero. The catalogue advertises implicit caching for Mercury, but that capability is not a measured hit rate in this study.'''))
    examples_text=[]
    for writer in s.MODELS:
        case=ex('01-kimi',writer,2)
        examples_text.append(f'''### {SHORT[writer]}: Kimi, numbered draft 2

Stable pair: `01-kimi/{writer}/02`. New reply's tag status: `{case['expanded_format_status']}`. Source and expected task are shared across these four examples.

**Original opening and closing sentences:**

{quote(first(case['baseline']))}

{quote(last(case['baseline']))}

**Expanded opening and closing sentences:**

{quote(first(case['expanded']))}

{quote(last(case['expanded']))}

Whole-post negative-contrast probabilities, original → new: {' · '.join(f"{JUDGES[i]} {case['whole_probabilities'][i]['baseline']['negative_contrast']:.3f} → {case['whole_probabilities'][i]['expanded']['negative_contrast']:.3f}" for i in api)}. Labels use the complete reply; this pair is one observation.''')
    sonnet=ex('01-kimi','claude-sonnet-5-5',2);model_spec=ex('08-model-spec','claude-sonnet-5-5',3);dartmouth=ex('12-dartmouth-writing','claude-sonnet-5-5',5);zest=ex('16-zest','claude-opus-5-5',5)
    sections.append(('8. Worked examples and remaining prose', '''These four pairs use the same 296-word Kimi article and numbered slot, rather than selecting the largest label changes. Expected: a standalone source-based post, with plain prose and tags under the expanded prompt. Openings and closings are exact excerpts; the [complete pairs and probabilities](data/paid_prose_comparison/examples.json) retain all paragraphs. Aggregate counts above establish how common the displayed behavior was.

'''+ '\n\n'.join(examples_text)+f'''

### Attribution is a separate review task

The Sonnet baseline above claims that the poster ran a pelican test. In the supplied article, the test belongs to its author; the intended poster supplied no biography. The baseline invented-experience probabilities are {prob(sonnet,'invented_experience','baseline')}. The earlier free model returned {sonnet['whole_probabilities']['span_free']['baseline']['invented_experience']:.3f}. This case illustrates why a low label count is not an attribution guarantee. The returned labels remain unchanged and no manual label is inserted into the tables.

### Two “not only” phrases remain

Literal scanning finds “not only” in two expanded Sonnet replies, and no “not just” or “more than just” occurrence in the expanded set. This is a string observation rather than an automatic contextual-fault assignment. In `08-model-spec/claude-sonnet-5-5/03`:

{quote(next(sentence for sentence in sentences(model_spec['expanded']) if 'not only' in sentence))}

Whole-text additive-contrast probabilities: {prob(model_spec,'additive_contrast')}. In `12-dartmouth-writing/claude-sonnet-5-5/05`:

{quote(next(sentence for sentence in sentences(dartmouth['expanded']) if 'not only' in sentence))}

Its probabilities are {prob(dartmouth,'additive_contrast')}. The phrases survive the instruction to state additional facts directly. The rubric's useful-exception rule is a separate contextual question, so literal prompt compliance and model-assigned prose labels can differ.

### A counterfactual product explanation

For `16-zest/claude-opus-5-5/05`, the source concerns a restaurant agent whose public launch waited for booking support. The expanded reply says:

{quote(next(sentence for sentence in sentences(zest['expanded']) if sentence.startswith('A version')))}

Whole-text negative-contrast probabilities are {prob(zest,'negative_contrast')}; the earlier free model returned {zest['whole_probabilities']['span_free']['expanded']['negative_contrast']:.3f}. The counterfactual explains a source-described product choice, exposing the boundary between useful distinction and rhetorical alternative. There is no independent gold label resolving it. The probabilities are preserved without calling the passage a proven defect or correcting them by hand.'''))
    controls=pd.read_csv(OUT/'controls.csv')
    control_table=[]
    for ident in api:
        pos=controls.query('classifier==@ident and expected_present');neg=controls.query('classifier==@ident and not expected_present')
        missed=pos.query('not matches_expectation')
        control_table.append([JUDGES[ident],f'{int(pos.matches_expectation.sum())}/{len(pos)}',f'{int(neg.matches_expectation.sum())}/{len(neg)}',
            ', '.join(f'{r.style_id} ({r.probability:.3f})' for _,r in missed.iterrows()) or 'None'])
    sections.append(('9. Checks, disagreements and limits',f'''The fixed controls contain three authored posts: an exaggerated rhetorical example, an obvious-formatting example and a plain factual example. They have ten intended positive instances and six intended negatives. The same fixtures were used for the earlier free check and are excluded from all study frequencies.

{table(['Paid classifier','Intended positives flagged','Intended negatives unflagged','Missed intended positives'],control_table)}

These 16 expectations are informal diagnostics, not a representative human-labelled accuracy set. The fixed main cutoff stays at 0.5 even when an intended control instance is missed. A formatting device can have a useful role, and these simple checks cannot calibrate probabilities on subtle prose.

There are **{result['regional_positive_whole_negative']:,} regional-positive / whole-negative judgments** across the paid classifiers. The following figure counts judgments, not unique replies; one reply can contribute several conflicts for a pattern.

![Counts of regional labels whose corresponding whole-text label is negative, separately by classifier and prompting condition.](figures/paid_prose_conflicts.png)

The [conflict table](data/paid_prose_comparison/region_conflicts.csv) retains every stable case ID and probability pair. Window extraction can create apparent one-sentence layouts, and separately returned answers are not logically constrained to agree. Whole-text labels remain the outcome for layout comparisons; no regional result is manually reconciled.

Provider transport is a different failure type. Mercury returned rate limits and intermittent gateway errors during the initial pass; the initial request allowance also left some cases unattempted. The recovery amendment preserves rejected attempts and partial indices, adds only missing requests, and serializes Mercury with slower pacing. Valid typed answers are not regenerated. [Transport history](data/paid_decision_full/transport_repair.json) records the change, rather than counting rejected requests as prose faults.

All current 2,400 cases supply 240 valid probabilities: 576,000 total, with zero final unreadable or missing predicates. The initial pass had 789 fully readable OpenAI cases, 794 Jev cases and 738 Mercury cases. Recovery filled 45 partial Mercury cases and 34 cases left uncached by the initial request allowance. Floor results therefore describe returned labels, not missing answers filled with zero.

The design has broader limits. Prompt and taxonomy were selected after inspecting baseline writing. The Kimi preview was reused, not held out. The initial prompt, continuation and tags change together. Writer aliases are undated; writing conditions and the retry were collected at different times. OpenAI baseline labels reuse earlier exact requests. News topics and paragraph extraction limit transfer, and previous drafts can influence later turns within a conversation.

No human preference, factual correctness, engagement or editing-time outcome was measured. Agreement among classifiers would not itself establish truth, and their disagreement does not identify the correct model. The evidence supports changes in several measured habits on these sources; a reader study is needed before turning those changes into a claim of better writing.'''))
    spend_table=table(['Classifier','Fresh HTTP attempts','Reused exact requests','Known new cost','Historical reused cost','New attempts missing a cost field'],[
        [JUDGES[i],api[i]['fresh_http_attempts'],api[i]['reused_exact_requests'],f"${api[i]['known_new_cost_usd']:.6f}",f"${api[i]['historical_reused_cost_usd']:.6f}",api[i]['new_missing_cost_fields']] for i in api])
    sections.append(('10. Reproduction and spend',f'''The notebook defines every helper inside itself and replays public cached outputs. Default execution needs no publisher text, private API cache or model credentials and makes no model calls. Source-overlap fingerprints and fixed source counts let the exact wording audit replay without redistributing publisher text.

{spend_table}

Known newly reported classifier cost is **${result['known_new_classifier_cost_usd']:.6f}**, including the nine authored-control requests. The reused OpenAI requests carried $2.2653584 of historical reported cost and were not charged again. Rejected requests without native cost counters remain unknown, not zero. The $20 guard covers new classification requests and reserves allowance for unpriced attempts; the [usage table](data/paid_prose_comparison/classifier_usage.csv) records native tokens, availability of cache fields and complete/unreadable case counts.

The expanded writing condition retains $4.9356308 in known Claude equivalents, including its Kimi preview. The one authorized retry is a Codex call whose dollar equivalent is unavailable; actual subscription charges and total Codex dollars remain unknown. No other successful writer generation was rerun.

Every fresh model call checks local Langfuse availability and retains a full request/response cache row. Exact cache reuse emits no new live trace. Publisher-bearing inputs and control transcripts stay under ignored `data/local_inputs/`; public rows retain settings, outputs, native usage and hashes. [Validation](data/paid_prose_comparison/validation.json) checks the restored native prefix, original continuation, request fingerprints, model/provider identity, every native answer and a portable replay with network and CLI access blocked.

Useful files:

- [Executed notebook](40_linkedin_writing_habits.ipynb), [all 400 effective new replies](data/paid_prose_comparison/outputs.md), [the recovered reply](data/simple_prose_v3_retry/OUTPUT.md) and [original baseline posts](data/main/posts.md).
- [All 40 definitions, explanations and illustrations](data/expanded_audit/STYLE_GUIDE.md), [paid registration](data/paid_decision_full/protocol.json), [retry registration](data/simple_prose_v3_retry/protocol.json) and [protocol history](data/PROTOCOL.md).
- All per-generation probabilities: [OpenAI](data/paid_prose_comparison/probabilities_gpt.csv), [Jev](data/paid_prose_comparison/probabilities_jev.csv), [Mercury](data/paid_prose_comparison/probabilities_mercury.csv). [Paired counts and intervals](data/paid_prose_comparison/paired_patterns.csv), [classifier agreement](data/paid_prose_comparison/classifier_agreement.csv), [complete examples](data/paid_prose_comparison/examples.json) and [file manifest](data/MANIFEST.json).

To reproduce the saved analysis:

```text
cd notebooks/40-linkedin-writing-habits
python -m nbconvert --to notebook --execute --inplace 40_linkedin_writing_habits.ipynb
```

Live collection is separate and opt-in. The collectors expose small default call limits, a pair-count knob, a model list and the $20 classification guard. Fresh requests need matching private sources and credentials; the native retry additionally needs the preserved original session. Changing the prompt, model or source requires a new registration, rather than silently reusing this completed protocol.'''))
    sections.append(('11. Future work and further reading','''### Future work

- Randomize and interleave writing conditions on new, held-out articles. Keep the same rubric and compare source-paired changes. Current prompt selection, temporal separation and reused baseline labels limit causal interpretation.
- Separate prose constraints, standalone continuation and output tags into distinct conditions. Measure format compliance and prose labels. The 108 tag failures and simultaneous instruction changes motivate this component test.
- Build a blinded human-labelled set of useful and unnecessary contrasts, noun-heavy passages and source-role transfers. Measure classifier precision, recall and threshold calibration. The disagreement tables and missed authored controls show why agreement alone is insufficient.
- Compare fresh conversations with five-turn blocks at a fixed request budget. Measure wording diversity, editing time and native cache reads. Shared history permits cache reuse but makes successive drafts correlated.
- Have readers edit and choose complete, source-checked posts. Measure preference, factual mistakes and minutes of editing. The present label reductions establish no human quality or engagement improvement.

### Further reading

Links checked November 3, 2026 (Toronto time).

- [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107) (Reinhart et al., 2025). Examines grammatical and rhetorical variation in other generations, motivating analysis beyond familiar vocabulary.
- [Why Does ChatGPT “Delve” So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models](https://aclanthology.org/2025.coling-main.426/) (Juzek and Ward, 2025). Provides historical lexical comparisons rather than a universal current blacklist.
- [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016) (Kobak et al., 2025). Studies corpus-level vocabulary shifts in a different writing domain, not a detector for individual posts.
- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) (Zheng et al., 2023). Discusses model-based evaluation and biases; it does not validate the decision-model rubric used here.
- [Submit a Decisions request](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) (OpenRouter, accessed 2026). Documents typed questions over shared state, the mechanism used for this audit.
'''))
    contents='## Contents\n\n'+'\n'.join(f'{n}. [{title.split(". ",1)[1]}](#{re.sub(r"[^a-z0-9 -]","",title.lower()).replace(" ","-")})' for n,(title,_) in enumerate(sections,1))
    readme='\n\n'.join([intro,summary,contents+'\n\n'+workflow,*['## '+title+'\n\n'+body for title,body in sections]]).rstrip()+'\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    output=['# Effective expanded-prompt replies\n\n400 nonempty replies after one authorized retry. Valid enclosed bodies are shown directly; invalid-tag replies are reproduced as exact raw text. The original empty attempt remains in its historical directory.\n']
    for writer in s.MODELS:
        for article in articles:
            for turn in range(1,6):
                value=analysis.paid.record_for('expanded',article['item_id'],writer,turn)
                text=value['text'];r=value['record']
                output.append(f"## {article['item_id']}/{writer}/{turn:02d}\n\nSource: [{article['title']}]({article['url']}). Format: `{r['format_status']}`.\n\n"+
                    (text if value['strict_readable'] else 'Exact raw reply, invalid tags:\n\n```text\n'+text+'\n```')+'\n')
    (OUT/'outputs.md').write_text('\n'.join(output),encoding='utf-8',newline='\n')
    setup=validation.embedded_setup(ROOT)+'''N_LIVE_PAIRS=2
MAX_NEW_PAID_CALLS=12
MAX_NEW_WRITER_CALLS=0
MAX_NEW_CLASSIFIER_USD=20
# Cached replay only. Optional live collection is a separate explicit CLI action.
comparison=MODULES['paid_prose_analysis'].analyse()
OUT=ROOT/'data/paid_prose_comparison'
CLASSIFIERS=['gpt','jev','mercury']
WRITERS=MODULES['smoke_study'].MODELS
SHORT={'gpt-6.1-sol':'Sol','gpt-6.1-terra':'Terra','claude-opus-5-5':'Opus','claude-sonnet-5-5':'Sonnet'}
JUDGES={'gpt':'OpenAI Decisions','jev':'Jev 1.14','mercury':'Mercury Decide','span_free':'Span-01 Lite (free)'}
assert comparison['complete']
'''
    nb=nbformat.v4.new_notebook(metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
    nb.cells=[nbformat.v4.new_markdown_cell(intro),nbformat.v4.new_markdown_cell(summary),nbformat.v4.new_markdown_cell(contents+'\n\n'+workflow)]
    for title,body in sections:
        nb.cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\n'+body))
        if title.startswith('3.'):
            nb.cells.append(nbformat.v4.new_markdown_cell('The next cell defines every helper within this notebook and analyzes only saved public responses. No collection or tracing function is called. The plotting cell uses one shared style block and writes the figures interpreted below.'))
            nb.cells.append(nbformat.v4.new_code_cell(setup));nb.cells.append(nbformat.v4.new_code_cell(PLOTS))
        if title.startswith('4.'):
            nb.cells.append(nbformat.v4.new_code_cell('display(patterns.query("population==\'raw\' and model==\'all\' and zone==\'whole\' and threshold==0.5 and style_id==\'negative_contrast\'")[["classifier","paired_posts","baseline_present","expanded_present","article_weighted_change_pp","article_cluster_95_low_pp","article_cluster_95_high_pp"]])'))
        if title.startswith('10.'):
            nb.cells.append(nbformat.v4.new_code_cell("display(api)\nprint('Known new reported classifier cost: $', comparison['known_new_classifier_cost_usd'])\nprint('Historical reused classifier cost, not charged again: $', comparison['imported_historical_cost_usd'])\nprint('Writer retry: one Codex call; dollars unavailable. Earlier expanded Claude equivalent: $4.9356308.')"))
    path=ROOT/'40_linkedin_writing_habits.ipynb'
    if path.exists():
        old=nbformat.read(path,as_version=4);previous=[c for c in old.cells if c.cell_type=='code'];current=[c for c in nb.cells if c.cell_type=='code']
        if [c.source for c in previous]==[c.source for c in current]:
            for before,after in zip(previous,current):after.outputs=before.outputs;after.execution_count=before.execution_count
    nbformat.write(nb,path)
    update_guide(patterns,styles)
    print('README bytes',len(readme.encode()),'notebook cells',len(nb.cells))


def update_guide(patterns,styles):
    path=ROOT/'data/expanded_audit/STYLE_GUIDE.md';text=path.read_text(encoding='utf-8')
    text=text.replace('the same free typed classifier applied to both arms','the same three paid typed classifiers applied to both arms, with each reported separately')
    assert list(styles)==[x['id'] for x in s.load(ROOT/'data/expanded_audit/criteria.json')['styles']]
    start=text.index('## How the multi-label classification works');end=text.index('## Contents',start)
    text=text[:start]+'''## How the multi-label classification works

The current comparison applies three paid classifiers to the same 800 effective replies: `openai/gpt-6-luna-decisions-20261006`, `typesafe/jev-1.14-20261014` and `inception/mercury-decide-20260930`. Each uses its named provider through OpenRouter Decisions, with fallback disabled, the same 40 definitions and six regions, and no tools or search. Whole-text labels are primary; probabilities and thresholds are not calibrated against human readers.

Tables below use the **secondary matched nonempty-reply comparison**, 100 pairs per writer. Invalid-tag replies are exact raw text, never inferred bodies. The report separately gives the strict 292-pair comparison, format failures, a recovery-block sensitivity and threshold sensitivity. Classifier labels are never combined into a badness score. Earlier free labels and paid intermediate-prompt results remain separate historical data. Literal surface examples below retain their original baseline scope and never supply contextual labels.

[Current report](../../README.md), [paired counts and denominators](../paid_prose_comparison/paired_patterns.csv), [OpenAI probabilities](../paid_prose_comparison/probabilities_gpt.csv), [Jev probabilities](../paid_prose_comparison/probabilities_jev.csv), [Mercury probabilities](../paid_prose_comparison/probabilities_mercury.csv), [protocol](../paid_decision_full/protocol.json).

'''+text[end:]
    blocks=list(re.finditer(r'\*\*Decisions API labels:.*?(?=\n\*\*(?:What is counted|Surface diagnostic))',text,re.S));assert len(blocks)==40
    for match,style in reversed(list(zip(blocks,styles))):
        rows=[]
        for ident in ['gpt','jev','mercury']:
            for threshold in [.5,.8]:
                values=[]
                for writer in s.MODELS:
                    row=patterns.query('classifier==@ident and population=="raw" and model==@writer and zone=="whole" and style_id==@style and threshold==@threshold').iloc[0]
                    values.append(f'{int(row.baseline_present)}/{int(row.paired_posts)} → {int(row.expanded_present)}/{int(row.paired_posts)}')
                rows.append([JUDGES[ident],f'p ≥ {threshold}',*values])
        label='**Decisions API labels: minimal request → expanded constraints.** Each cell is a matched count/denominator under the named paid classifier; estimates are not verified faults.\n\n'
        label+=table(['Classifier','Cutoff',*SHORT.values()],rows)+'\n'
        text=text[:match.start()]+label+text[match.end():]
    path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':build()
