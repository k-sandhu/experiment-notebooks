"""Build one current explanation, figures and self-contained notebook."""
import csv
from pathlib import Path
import re
import nbformat
import smoke_study as s
import expanded_full_analysis as a

ROOT=Path(__file__).resolve().parent
OUT=a.OUT
SHORT={'gpt-6.1-sol':'Sol','gpt-6.1-terra':'Terra','claude-opus-5-5':'Opus','claude-sonnet-5-5':'Sonnet'}


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',
        *['| '+' | '.join(str(x).replace('|','\\|').replace('\n',' ') for x in row)+' |' for row in rows]])


def quote(text):return '\n'.join('> '+line if line else '>' for line in text.strip().splitlines())


PLOTS=r'''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'figure.dpi':140,'savefig.dpi':170,'font.family':'DejaVu Sans','font.size':10,
 'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#303841',
 'axes.titlesize':13,'axes.grid':False,'figure.facecolor':'white','axes.facecolor':'white'})
BLUE='#396B9D';ORANGE='#C46B36';GRAY='#7A8794'
patterns=pd.read_csv(OUT/'paired_patterns.csv');usage=pd.read_csv(OUT/'usage.csv')
metrics=pd.read_csv(OUT/'post_metrics.csv')
raw=patterns.query("population == 'raw_sensitivity' and model == 'all' and zone == 'whole' and threshold == 0.5")
strict=patterns.query("population == 'strict' and model == 'all' and zone == 'whole' and threshold == 0.5")
top=raw.sort_values('baseline_present',ascending=False).head(14).iloc[::-1]
fig,axes=plt.subplots(1,2,figsize=(13,7),sharey=True)
for ax,frame,title in [(axes[0],strict,'Valid tagged bodies, matched pairs'),(axes[1],raw,'All nonempty replies, matched pairs')]:
 part=frame.set_index('style_id').loc[top.style_id];y=np.arange(len(part));n=part.paired_posts.iloc[0]
 ax.barh(y-.18,100*part.baseline_fraction,.34,color=BLUE,label='Minimal request')
 ax.barh(y+.18,100*part.expanded_fraction,.34,color=ORANGE,label='Expanded prose constraints')
 ax.set_yticks(y,part.name);ax.set_xlim(0,105);ax.set_xlabel('Replies labelled present (%)');ax.set_title(f'{title}\nn = {n} pairs')
 ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
axes[0].legend(loc='lower right',fontsize=9)
fig.suptitle('Layout labels fall; noun-heavy wording remains common',fontsize=16,fontweight='bold',y=.99)
fig.tight_layout();fig.savefig(FIG/'expanded_full_patterns.png',bbox_inches='tight');plt.close(fig)

part=usage.query("condition=='expanded'").set_index('model').loc[MODELS]
fig,ax=plt.subplots(figsize=(8.5,4.2));x=np.arange(4)
ax.bar(x,part.strict_readable,color=BLUE,label='Valid tagged body')
ax.bar(x,part.invalid_tag_nonempty,bottom=part.strict_readable,color=ORANGE,label='Text, invalid tags')
ax.bar(x,part.cli_failures,bottom=part.strict_readable+part.invalid_tag_nonempty,color=GRAY,label='CLI failure')
for i,(_,row) in enumerate(part.iterrows()):
 for value,bottom in [(row.strict_readable,0),(row.invalid_tag_nonempty,row.strict_readable)]:
  if value:ax.text(i,bottom+value/2,str(int(value)),ha='center',va='center',color='white',fontweight='bold')
ax.set_xticks(x,['Sol','Terra','Opus','Sonnet']);ax.set_ylim(0,112);ax.set_ylabel('Planned slots (100 per model)')
ax.set_title('Claude returned every tag pair; Sol and Terra often omitted them')
ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.12),fontsize=9)
fig.tight_layout();fig.savefig(FIG/'expanded_full_formats.png',bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(11,4.5));x=np.arange(4)
for condition,offset,color,label in [('baseline',-.18,BLUE,'Minimal request'),('expanded',.18,ORANGE,'Expanded constraints')]:
 part=usage.query('condition==@condition').set_index('model').loc[MODELS]
 axes[0].bar(x+offset,part.mean_words,.34,color=color,label=label)
 axes[1].bar(x+offset,100*part.warm_cache_fraction,.34,color=color,label=label)
 for i,value in enumerate(part.mean_words):axes[0].text(i+offset,value+5,f'{value:.0f}',ha='center',fontsize=9)
 for i,value in enumerate(part.warm_cache_fraction):axes[1].text(i+offset,100*value+1,f'{100*value:.0f}%',ha='center',fontsize=9)
for ax in axes:ax.set_xticks(x,['Sol','Terra','Opus','Sonnet']);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0].set_ylabel('Mean words per nonempty reply');axes[0].set_ylim(0,360);axes[0].set_title('Length changes differ by writer')
axes[1].set_ylabel('Provider cache reads / known input tokens (%)');axes[1].set_ylim(0,105);axes[1].set_title('Most warm-turn input came from cache')
axes[0].legend(fontsize=9);fig.tight_layout();fig.savefig(FIG/'expanded_full_length_cache.png',bbox_inches='tight');plt.close(fig)

features=['negative_contrast','additive_contrast','nominalization','single_sentence_paragraphs']
fig,axes=plt.subplots(2,2,figsize=(11,7));x=np.arange(4)
for ax,style in zip(axes.flat,features):
 part=patterns.query("population=='raw_sensitivity' and zone=='whole' and threshold==0.5 and style_id==@style and model!='all'").set_index('model').loc[MODELS]
 ax.bar(x-.18,100*part.baseline_fraction,.34,color=BLUE,label='Minimal request')
 ax.bar(x+.18,100*part.expanded_fraction,.34,color=ORANGE,label='Expanded constraints')
 for i,(_,row) in enumerate(part.iterrows()):ax.text(i, max(100*row.baseline_fraction,100*row.expanded_fraction)+3,f'{int(row.baseline_present)} → {int(row.expanded_present)}',ha='center',fontsize=9)
 ax.set_xticks(x,['Sol','Terra','Opus','Sonnet']);ax.set_ylim(0,112);ax.set_ylabel('Matched replies labelled present (%)')
 ax.set_title(part.name.iloc[0]);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0,0].legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/'expanded_full_by_model.png',bbox_inches='tight');plt.close(fig)

phrases=pd.read_csv(OUT/'reference_phrases.csv').iloc[::-1]
fig,ax=plt.subplots(figsize=(10,4.6));y=np.arange(len(phrases))
ax.barh(y-.17,phrases.baseline_posts,.32,color=BLUE,label='Minimal request')
ax.barh(y+.17,phrases.expanded_posts,.32,color=ORANGE,label='Expanded constraints')
labels=[f"{SHORT[row.model]} · {row.zone.replace('_',' ')}\n“{row.phrase}”" for _,row in phrases.iterrows()]
ax.set_yticks(y,labels);ax.set_xlabel('Nonempty replies containing source-absent exact phrase');ax.set_xlim(0,20)
ax.set_title('Several recurring hooks and engagement phrases disappeared')
ax.legend(fontsize=9);fig.tight_layout();fig.savefig(FIG/'expanded_full_phrases.png',bbox_inches='tight');plt.close(fig)

conflicts=pd.read_csv(OUT/'region_conflicts.csv')
part=conflicts.groupby(['condition','style_id']).size().sort_values(ascending=False).head(8).iloc[::-1]
fig,ax=plt.subplots(figsize=(9,4.6));y=np.arange(len(part))
ax.barh(y,part.values,color=[BLUE if key[0]=='baseline' else ORANGE for key in part.index])
ax.set_yticks(y,[f'{condition} · {style.replace("_"," ")}' for condition,style in part.index])
for i,value in enumerate(part.values):ax.text(value+1,i,str(value),va='center',fontsize=9)
ax.set_xlim(0,max(part.values)*1.15);ax.set_xlabel('Region-positive / whole-negative judgments (not unique replies)')
ax.set_title('Regional judgments can conflict with whole-text labels')
fig.tight_layout();fig.savefig(FIG/'expanded_full_conflicts.png',bbox_inches='tight');plt.close(fig)
'''


def build():
    import pandas as pd
    summary=s.load(OUT/'summary.json');patterns=pd.read_csv(OUT/'paired_patterns.csv')
    usage=pd.read_csv(OUT/'usage.csv');metrics=pd.read_csv(OUT/'post_metrics.csv')
    counts=pd.read_csv(OUT/'counts.csv');phrases=pd.read_csv(OUT/'common_phrases.csv')
    articles=s.load(ROOT/'data/main/articles.json');by_article={x['item_id']:x for x in articles}
    protocol=s.load(ROOT/'data/simple_prose_v3_full_classifier/protocol.json')
    def pat(style,pop='raw_sensitivity',model='all',threshold=.5,zone='whole'):
        return patterns.query('population==@pop and model==@model and style_id==@style and threshold==@threshold and zone==@zone').iloc[0]
    def cell(row):return f"{int(row.baseline_present)}/{int(row.paired_posts)} → {int(row.expanded_present)}/{int(row.paired_posts)}"
    def current(style,pop='raw_sensitivity'):return cell(pat(style,pop))
    def model_usage(condition,model):return usage.query('condition==@condition and model==@model').iloc[0]
    def raw(condition,item,model,turn):
        folder='main' if condition=='baseline' else 'simple_prose_v3_full'
        return s.load(ROOT/'data'/folder/'responses'/item/model/f'{turn:02d}.json')
    def body(condition,item,model,turn):
        r=raw(condition,item,model,turn);return a.text_for(condition,r)[0] or '[No generated text]'
    def probability(condition,item,model,turn,style,zone='whole'):
        path=ROOT/'data/simple_prose_v3_full_classifier/cases'/condition/item/model/f'{turn:02d}.json'
        if not path.exists():return 'pending (not collected)'
        r=s.load(path)
        v=r['answers'].get(zone+'__'+style,{})
        return f"{v['probability']:.3f}" if v.get('valid') else 'unreadable'
    api=summary['classifier'];raw_n=summary['raw_pairs'];strict_n=summary['strict_pairs']
    assert api['cases']==800 and int(pat('negative_contrast').paired_posts)==raw_n,'Refuse to publish a partial audit as the full study'
    invalid=int(usage.query("condition=='expanded'").invalid_tag_nonempty.sum())
    nominal=pat('nominalization');negative=pat('negative_contrast');hashtag=pat('hashtag_tail')
    intro='''# Can prose constraints change recurring LinkedIn writing habits?

A person wants to share news about an AI tool on LinkedIn. They give a writing model the announcement and ask for a post. A useful draft explains what happened and why it matters to a reader. The person still needs to check the facts and decide whether the voice fits.

Another draft offers a choice. Yet five drafts can share a familiar opening, short-paragraph rhythm and invitation to comment. The words differ while the structure returns, leaving the editor to remove the same devices repeatedly.

**Illustrative example, not measured data.** Suppose an announcement says a support tool can now search old tickets. A draft might begin, “This isn't just search. It's a new way to work.” That opening delays the useful fact and introduces an alternative the reader did not ask about. A direct account could begin with the new ability and explain which tickets it can search.

Now add a complication: the tool searches archived tickets but cannot open attachments. A distinction between what it can and cannot do helps the reader. An instruction to remove every negative word would lose useful information. The editing problem concerns the role of the wording in context, rather than whether a particular word appears.

One approach leaves every writing choice to the model. Another leaves angle and length open while discouraging stock framing, unnecessary contrasts, repetitive rhythm and generic endings. That might save editing work, replace one habit with another or make extraction harder.

These possibilities need separate measurements. Counting hashtags can establish whether a visible format changed. Deciding whether a contrast is unnecessary requires reading the claim with its source. Neither measurement establishes that readers prefer the draft or that its facts are correct.

This study therefore keeps two kinds of evidence. It records literal wording and layout, and asks a separate classification model to return a probability for each of 40 editorial patterns. Several patterns can occur in one draft. Their counts are never added into a writing-quality score.

The question is: **on the same 20 AI news articles, how do four writers' drafts change when a minimal request is replaced by prose constraints, an explicit standalone-post continuation and a tagged output request?**'''
    study=f'''## Study summary

Each writer was asked for five successive posts per article in each condition: 400 baseline slots and 400 expanded-prompt slots. All writers used high effort, CLI access and no tools or web search. A **pattern frequency** is the number of replies the free classification model labels present, divided by the number with readable answers for that pattern. The main tag-valid comparison contains **{strict_n} matched pairs**; the secondary audit includes **{raw_n} matched pairs of nonempty replies**, preserving missing-tag replies as exact raw text.

In valid tagged pairs, negative-contrast labels change from {current('negative_contrast','strict')}. In the broader audit, generic hashtag-tail labels changed from **{int(hashtag.baseline_present)}/{raw_n} to {int(hashtag.expanded_present)}/{raw_n}**, and unnecessary-negative-contrast labels changed from **{int(negative.baseline_present)}/{raw_n} to {int(negative.expanded_present)}/{raw_n}**. Noun-heavy wording changed from **{int(nominal.baseline_present)}/{raw_n} to {int(nominal.expanded_present)}/{raw_n}**. These are classifier estimates; there is no human preference or factual-quality result.

The output contract was a substantial limitation: **{invalid} nonempty replies omitted valid post tags**, and one Sol request returned an empty capacity error. Claude returned all 200 tag pairs; Sol returned 27/100 and Terra 65/100. Many contextual categories sit near zero under this classifier, so the study cannot rank writers on those categories. The prompts were developed after examining baseline writing, the baseline was collected first and the writer IDs are undated aliases. The results are an exploratory comparison of the complete prompting package.'''
    workflow=f'''```mermaid
flowchart TD
 A["20 frozen AI news articles<br/>23–30 October 2026"] --> B["Minimal request<br/>4 CLI writers × 5 turns = 400 replies"]
 A --> C["Expanded prose constraints<br/>4 CLI writers × 5 slots = 400 attempts"]
 B --> D["Frozen baseline post parser<br/>400 readable post bodies"]
 C --> E["Strict tag parser<br/>{strict_n} enclosed bodies; {invalid} raw replies; 1 empty failure"]
 D --> F["Same dated free Decisions checkpoint<br/>40 patterns × 6 regions per nonempty reply"]
 E --> F
 F --> G["{api['valid_probabilities']:,} valid probabilities<br/>strict paired comparison + raw-text sensitivity"]
 D --> H["Exact phrases, source overlap<br/>literal layout, length and native cache counters"]
 E --> H
 G --> I["Article-cluster comparisons<br/>examples, tables and figures"]
 H --> I
```

For the Kimi example, the complete saved article enters each writer conversation. Five replies are collected in order, then each reply is split according to its condition's output contract. The classifier receives one reply and its source, while exact phrase counting compares the reply with that same source. A missing tag prevents a strict post-body result; it still leaves a clearly labelled raw reply for the secondary audit.'''
    sections=[]
    full_source_table=table(['ID','Date','Article / topic','Words'],[(x['item_id'],x['publication_date'],f"[{x['title']}]({x['url']})",x['words']) for x in articles])
    (OUT/'ARTICLES.md').write_text('# The 20 frozen source articles\n\n'+full_source_table+'\n',encoding='utf-8',newline='\n')
    sources_table=table(['Example ID','Date','Article / topic','Words'],[(x['item_id'],x['publication_date'],f"[{x['title']}]({x['url']})",x['words']) for x in articles if x['item_id'] in ['01-kimi','02-tb-screening','06-protostar','16-zest']])
    sections.append(('1. Articles and the writing task',f'''The inputs are 20 complete, frozen public articles, one per selected topic, published from October 23 through October 30, 2026. They total {sum(x['words'] for x in articles):,} words. The set covers releases, speech, healthcare, scientific applications, publishing, security, infrastructure and AI adoption. It is a deliberately varied convenience sample of AI news, rather than a random sample of LinkedIn subjects or industry events.

Both conditions receive identical frozen titles, dates and substantive article text. Extraction removes page furniture and retains meaningful lists, captions and corrections. The [manifest](data/main/articles.json) records extraction methods and hashes; publisher text stays local and excluded from Git.

{sources_table}

These four examples show the range; [the complete 20-article index](data/expanded_full_comparison/ARTICLES.md) gives every title, date, URL and length.

The longest source has {max(x['words'] for x in articles):,} words and Kimi has 296. Longer sources offer more material and larger classification requests. Source length is not equalized and draft length is left to the writer.

The [freshness record](data/main/freshness.json) checks the recent articles against documented writer cutoffs or release-date fallbacks. Opaque backend changes prevent proving no prior exposure. Phrase counts exclude exact wording present in the same source.

**Measured input example: `01-kimi`.** The saved source reports the release of Kimi K3.1 Pro, benchmark comparisons and token prices. It also attributes an image-generation observation to the article's author. The intended LinkedIn poster supplied no biography or test history. A useful draft can report the observation with attribution; a claim that the poster personally tested it needs separate evidence. That distinction is part of the contextual rubric, not a rule that every use of “I” is wrong.'''))
    models=table(['Model','Pinned version / identity limit','Provider and call','Size / precision','Output settings','Reason for inclusion'],[
        ['GPT-6.1 Sol','`gpt-6.1-sol`; undated alias','OpenAI, `codex exec` / explicit resume','Not published','High; tools/search off; neutral system','One GPT-6.1 writer; tests the previously observed Sol style'],
        ['GPT-6.1 Terra','`gpt-6.1-terra`; undated alias','OpenAI, `codex exec` / explicit resume','Not published','High; tools/search off; neutral system','Second writer from the same tested family'],
        ['Claude Opus 5.5','`claude-opus-5-5`; undated alias','Anthropic, `claude -p` / explicit resume','Not published','High; tools/search off; neutral system','One Claude writer; longer drafts in the baseline'],
        ['Claude Sonnet 5.5','`claude-sonnet-5-5`; undated alias','Anthropic, `claude -p` / explicit resume','Not published','High; tools/search off; neutral system','Second Claude writer; permits a within-family comparison'],
        ['Span-01 Lite','`respan/span-01-lite-20260925`; dated checkpoint and native returned ID','Respan via OpenRouter Decisions API, standard zero-price route','Not published','Typed boolean questions; no effort control exposed; no tools; Respan only; prices capped at zero','The live catalogue exposed one unique free decision checkpoint; applies the same rubric to both conditions']])
    initial=(ROOT/'data/prompt_conditions/simple_prose_v3.txt').read_text(encoding='utf-8')
    followup=(ROOT/'data/prompt_conditions/simple_prose_v3_followup.txt').read_text(encoding='utf-8')
    sections.append(('2. Prompts, models and conversation design',f'''The minimal condition asks, “Write a LinkedIn post based on the following article,” followed by the complete article. Turns two through five contain only “Generate another post.” The expanded condition keeps the task open while adding 15 constraints about prose and layout, an explicit standalone-post continuation and an output boundary. Length and angle stay open.

The expanded task begins:

```text
Write a LinkedIn post based on the article below. Use your judgment about the angle, voice, length, structure and ending.
```

Inside `<constraints>`, it asks for plain prose; direct claims and ordinary words; meaningful connections between ideas; varied rhythm; necessary uncertainty; and an ending that stops when the subject is covered. It discourages unnecessary negative contrasts, “not just” expansions, stock framing, significance tails, staged revelations, forced groups of three and invented personal experience. [The complete initial template](data/prompt_conditions/simple_prose_v3.txt) is the exact experimental prompt, including useful exceptions. Nothing is added from this report during generation.

The exact continuation is:

```text
{followup.strip()}
```

Each model/article block has its own new conversation ID. The first call supplies the article and initial task; the next four resume that conversation with the saved continuation. Earlier drafts remain visible. “Independent” describes the requested standalone post, so the five drafts are correlated observations rather than five independent statistical samples.

{models}

Writer IDs are undated aliases. Codex was `0.160.1`; Claude Code was `2.1.296`. Calls share a neutral system prompt and isolation settings, with no notebook, style file, search or tools available. Native logs show no tool activity.

```mermaid
flowchart LR
 A["Source + initial prompt"] --> S["Sol · codex exec<br/>returns one draft"]
 A --> T["Terra · codex exec<br/>returns one draft"]
 A --> O["Opus · claude -p<br/>returns one draft"]
 A --> N["Sonnet · claude -p<br/>returns one draft"]
 S -->|"resume turns 2–5; wait each turn"| S
 T -->|"resume turns 2–5; wait each turn"| T
 O -->|"resume turns 2–5; wait each turn"| O
 N -->|"resume turns 2–5; wait each turn"| N
 S --> R["Four separate native conversations<br/>wait for each turn; unchanged continuation<br/>repeat until five numbered slots"]
 T --> R
 O --> R
 N --> R
 R --> P["Strict body parser + exact raw sensitivity"]
 P --> D["Span-01 Lite · OpenRouter Decisions<br/>up to 40 probabilities per batch<br/>source + one reply; no draft history"]
 D -->|"next batch until 240; transport retry/split"| D
 D -->|"all batches finished"| C["Full request/response caches<br/>readable answers and failures kept separately"]
```

Writers can run concurrently; turns within a conversation wait. The classifier receives source and one reply, with no writer identity, condition or prior drafts. Classification order is interleaved across matched pairs; writing-condition order is not.

### How the study got here

A smoke test checked output diversity and collection code. An intermediate source-auditing prompt produced editorial commentary in some Claude replies. The current prompt removes that procedure. All 20 matching Kimi preview replies were imported, including the format failure; the remaining 380 slots use the unchanged prompt. Both current arms are reclassified with the same free model. Earlier paid labels and intermediate outputs remain in [protocol history](data/PROTOCOL.md), outside the current numerical comparison.'''))
    strict_table=table(['Population','What enters','Matched pairs','What it can establish'],[
        ['Strict post-body comparison','Baseline parsed body; expanded valid enclosed body',strict_n,'Change among cells with a readable post body in both conditions'],
        ['Raw-text sensitivity','Same baseline body; exact entire expanded reply if tags fail',raw_n,'Whether a reduction survives inclusion of missing-tag prose; not a repaired post parser'],
        ['Recovery-block sensitivity','Raw pairs excluding Sol on the SETI article',int(pat('negative_contrast','raw_without_recovery_block').paired_posts),'Whether that one capacity-interrupted conversation changes the observation']])
    sections.append(('3. How a reply becomes a measurement',f'''The workflow above separates generation from extraction. A **strict readable post** contains exactly one complete, nonempty, non-nested `<linkedin_post>...</linkedin_post>` pair. Text before and after is saved separately. Missing, repeated, malformed or empty tags do not cause an automatic rewrite or a guessed body. An empty CLI error has no prose to classify.

{strict_table}

The secondary raw audit was declared after early tag failures, before full-run classification. It keeps every nonempty invalid-tag reply as exact raw text; no post body is guessed. The older baseline parser stays frozen because its prompt requested no tags.

### Regions and literal measurements

The classifier sees six named regions. **Whole** is the entire measured text; **opening paragraph** is the first paragraph; **transition starts** are the first 12 whitespace-delimited words of later sentences and paragraphs; **point endings** are final sentences of substantive paragraphs other than the last; **conclusion** is the last substantive paragraph; and **closing** is its final sentence. A hashtag-only final paragraph is excluded from substantive endings. Sentence splitting is a fixed heuristic and is not a linguistic gold standard.

Regions are provided beside the whole text and source. An instance must occur within its named region. Assembled transition and point-ending windows can alter layout, so whole-text labels are primary and regional formatting labels are diagnostic. Separate opening-sentence and 30-word inventories do not change the classifier regions.

Literal counters measure words, paragraphs, hashtags, Markdown bold, list markers, specified emoji ranges, punctuation and exact “not just / not only / more than just” phrases. They never assign contextual prose faults and do not cover every emoji sequence.

### Typed multi-label questions

The free Decisions model answers one yes/no probability per pattern and region. Forty separate probabilities allow multiple labels on one reply; the 40 values do not have to sum to one. The state contains the source, whole text, six regions and frozen definitions with useful exceptions. The question shape is:

```json
{{"whole__negative_contrast": {{
  "type": "noul",
  "instructions": "Under the RUBRIC definition and exceptions for negative_contrast, does an instance occur in region whole? Use the whole post and source for context.",
  "criteria": {{"true": "The defined pattern occurs in the specified region.", "false": "The defined pattern is absent from the specified region."}}
}}}}
```

The rubric defines negative contrast as denying an alternative the reader may never have proposed, allowing correction of an actual misunderstanding. Source and reply are treated as data. Probability 0.70 is present at 0.5; 0.30 is absent. The 0.2/0.8 sensitivities are operating choices, not calibrated guarantees.

**Illustrative counting example.** If four of ten readable paired replies receive a label under the minimal request and one of the same ten under the expanded prompt, the frequencies are 40% and 10%, a decrease of 30 percentage points. A missing probability is removed from that predicate's paired denominator; it is never converted to “absent.” The actual [paired table](data/expanded_full_comparison/paired_patterns.csv) gives the denominator for every model, region, pattern and threshold.

Intervals resample the 20 articles 2,000 times, retaining available matched drafts within each sampled article and averaging article-level changes. The central 95% of those draws is shown. Post-weighted changes are also retained because unequal tag survival can alter weighting. Intervals cover variation across these articles, conditional on classifier and aliases; they exclude classifier bias, prompt selection and backend drift. The 40-pattern audit is exploratory with no multiple-comparison correction.

### Worked measured case: from raw reply to a label

For `01-kimi/claude-sonnet-5-5/01`, the original opening is:

{quote(a.regions(body('baseline','01-kimi','claude-sonnet-5-5',1))['opening_paragraph'])}

The expanded opening in the same numbered slot is:

{quote(a.regions(body('expanded','01-kimi','claude-sonnet-5-5',1))['opening_paragraph'])}

The original parser and tag parser each supply their measured body. The classifier's whole-text negative-contrast probabilities are {probability('baseline','01-kimi','claude-sonnet-5-5',1,'negative_contrast')} and {probability('expanded','01-kimi','claude-sonnet-5-5',1,'negative_contrast')}; each is independently compared with 0.5. Literal word counts are {len(s.words(body('baseline','01-kimi','claude-sonnet-5-5',1)))} and {len(s.words(body('expanded','01-kimi','claude-sonnet-5-5',1)))}. These steps link the saved input, raw output, extracted body and returned probabilities. There is no single correct LinkedIn post or human gold prose label for this item.'''))
    # Results are generated only from the current matched free-classifier tables.
    top=patterns.query("population=='raw_sensitivity' and model=='all' and zone=='whole' and threshold==0.5").sort_values('baseline_present',ascending=False).head(14)
    result_table=table(['Pattern','Strict valid-body pairs','All nonempty pairs (secondary)','Article-cluster change, secondary'],[
        [r['name'],current(r.style_id,'strict'),cell(r),f"{r.article_weighted_change_pp:+.1f} pp [{r.article_cluster_95_low_pp:+.1f}, {r.article_cluster_95_high_pp:+.1f}]"] for _,r in top.iterrows()])
    sections.append(('4. Which patterns changed, and which remained',f'''Compare each pattern across the two prompting packages. The left panel uses only matched valid post bodies; the right panel includes missing-tag text as exact raw replies. Blue bars show the minimal request and orange bars show expanded constraints. The horizontal axis is the percentage labelled present at probability at least 0.5. The two panels have different selected populations, so a change in their level can reflect which drafts survived the tag contract.

![Fourteen whole-text pattern frequencies, with strict and raw-text paired populations shown separately.](figures/expanded_full_patterns.png)

{result_table}

Each arrow uses the same article/model/turn cells. Intervals resample articles and measure percentage-point changes, not numbers of instances. These are the 14 largest baseline frequencies; [all 40 patterns, thresholds and regions](data/expanded_full_comparison/paired_patterns.csv) include increases and zeroes.

Hashtag-tail labels changed from {current('hashtag_tail')}, repeated one-sentence-paragraph labels from {current('single_sentence_paragraphs')}, and repeated bold-emphasis labels from {current('bold_density')}. Those movements agree with the direct observations of zero hashtag strings and zero bold spans across all 399 nonempty expanded replies. These visible changes do not establish reader preference.

The contrast result is narrower. Unnecessary-negative-contrast labels changed from {current('negative_contrast')}, while automatic not-just-expansion labels changed from {current('additive_contrast')}. The rubric allows useful factual distinctions, so these numbers differ from a literal count of “not” or “but.” They also differ from the earlier paid classifier's counts, which are not part of this comparison. The full examples below show why a returned flag still needs contextual interpretation.

Noun-heavy wording remains a substantial category: {current('nominalization')}. The change's article-cluster interval is {nominal.article_cluster_95_low_pp:+.1f} to {nominal.article_cluster_95_high_pp:+.1f} percentage points, including zero. Asking a writer to avoid familiar slogans does not ensure that it describes actions directly. That aggregate observation does not show that the instructions caused abstract nouns, or that every noun phrase should be removed. It identifies a remaining review task under this classifier's definition.

The [threshold table](data/expanded_full_comparison/paired_patterns.csv) repeats every comparison at 0.2 and 0.8. At the stricter 0.8 cutoff, negative contrast is {cell(pat('negative_contrast',threshold=.8))} and noun-heavy wording is {cell(pat('nominalization',threshold=.8))}. Some categories are at or near a floor even in the baseline. A zero does not establish that the prose is free of the behavior, and a category with only a few labelled cases cannot support a reliable writer ranking.

Excluding the capacity-interrupted Sol SETI block gives negative contrast {cell(pat('negative_contrast','raw_without_recovery_block'))} and noun-heavy wording {cell(pat('nominalization','raw_without_recovery_block'))}. This sensitivity retains the broader pattern while making the scope of that recovery explicit. It cannot remove the larger temporal or prompt-selection confounds.'''))
    permodel=table(['Writer','Negative contrast','Not-just expansion','Noun-heavy wording','Isolated sentence paragraphs'],[
        [SHORT[m],*[cell(pat(style,model=m)) for style in ['negative_contrast','additive_contrast','nominalization','single_sentence_paragraphs']]] for m in s.MODELS])
    sections.append(('5. Differences among the four writers',f'''The following comparison keeps model identity visible. Each percentage uses matched nonempty replies for that writer: 99 for Sol because of its capacity failure, and 100 for each other writer. These are the secondary raw-text comparisons; the [full table](data/expanded_full_comparison/paired_patterns.csv) also supplies the smaller strict valid-body populations, including their article counts.

![Four per-model comparisons of contrast, additive contrast, noun-heavy wording and one-sentence-paragraph patterns.](figures/expanded_full_by_model.png)

{permodel}

The labels above the bars give counts before and after. The plots use percentages to keep Sol's 99 pairs visible beside the other writers' 100. The two Claude models both returned every tag pair, so their strict and raw-text populations coincide. Sol and Terra's valid-tag subsets are selected by format compliance; treating those subsets alone as all of their writing would overstate what the strict comparison covers.

Family names cover only the two tested members under this design. A family phrase must meet the support rule separately in both; one writer’s habit is not assigned to its whole family.

Source text, nominal model ID, effort and tool access are fixed. Writing conditions were collected at different times, so backend changes remain a possible contributor. Randomized interleaving is needed for a stronger causal claim.'''))
    refs=pd.read_csv(OUT/'reference_phrases.csv')
    wording_table=table(['Writer','Location','Exact source-absent phrase','Minimal request','Expanded prompt'],[
        [SHORT[r.model],r.zone.replace('_',' '),'“'+r.phrase+'”',f'{r.baseline_posts}/{r.baseline_denominator}',f'{r.expanded_posts}/{r.expanded_denominator}'] for _,r in refs.iterrows()])
    new_examples=[]
    for model in s.MODELS:
        for zone in ['transition_starts']:
            part=phrases.query("condition=='expanded' and model==@model and zone==@zone and words>=3")
            if len(part):
                r=part.iloc[0];new_examples.append([SHORT[model],zone.replace('_',' '),'“'+r.phrase+'”',int(r.posts_containing),int(r.distinct_topics)])
    newphrase_table=table(['Writer','Location','Example recurring string','Replies','Articles'],new_examples)
    location_table=table(['Location','Selected contextual pattern','Minimal → expanded, matched replies'],[
        [zone.replace('_',' '),pat(style,zone=zone)['name'],cell(pat(style,zone=zone))] for zone,style in [
            ('opening_paragraph','generic_opener'),('transition_starts','question_pivot'),('point_endings','negative_contrast'),
            ('conclusion','repeated_conclusion'),('closing','engagement_close')]])
    sections.append(('6. Repeated openings, transitions and endings',f'''A phrase can recur without violating any editorial rule. To find wording habits, the analysis lowercases and normalizes apostrophes, builds exact sequences of two through eight words, and checks each sequence against that reply's own source article. It counts a phrase once per reply and retains candidates seen in at least five replies across at least three articles for a particular model and region.

This **source-absent** rule removes exact wording already present in that article. It does not remove paraphrased source language or prove that the phrase came from a model-specific habit. Common connective phrases can pass it. These inventories are descriptive, chosen after viewing the outputs, and do not use the earlier baseline discovery/confirmation split as if the expanded prompt were a new preregistered validation sample.

![Selected repeated baseline phrases by writer and region, compared with their expanded-prompt counts.](figures/expanded_full_phrases.png)

{wording_table}

These examples were selected from recurring baseline hooks, transitions and endings. Both counts are computed directly with per-article source exclusion; a missing filtered-inventory row is never treated as zero. Several familiar phrases disappear, which does not establish that every opening or ending became varied.

The expanded drafts still share connective and attribution phrases. One transition example per writer meeting the support rule is:

{newphrase_table}

Ordinary attribution and connective wording can recur: “says it will” can attribute company plans across several articles. These string counts never assign an editorial fault.

No expanded opening-paragraph string of at least three words meets the five-reply/three-article rule. This does not prove unique openings: structures can repeat with different words. The [common inventory](data/expanded_full_comparison/common_phrases.csv) includes two-word strings; [fixed counts](data/expanded_full_comparison/fixed_phrases.csv) track the original 111 entries across regions.

### Contextual labels by location
+
+The API also asks whether a defined instance occurs in a specific region, using the whole text and source for context. The following selected questions address the opening, the move into another point, paragraph endings, the concluding paragraph and the final sentence. Counts use the same secondary matched nonempty population and threshold of 0.5.
+
+{location_table}
+
+Regions overlap and their answers are separate judgments. Counts must not be added or forced to match whole-text labels. Closing engagement labels change from {cell(pat('engagement_close',zone='closing'))}; point-ending negative contrast changes from {cell(pat('negative_contrast',zone='point_endings'))}. All regional probabilities remain in the paired table.
+
+The [family table](data/expanded_full_comparison/family_phrases.csv) requires separate support in both tested members. Overlapping strings such as “what do you” and “what do you think” must not be added together.'''))
    fmt_table=table(['Writer','Valid tagged body','Nonempty, invalid tags','CLI failure','Outside text'],[
        [SHORT[m],f"{int(model_usage('expanded',m).strict_readable)}/100",int(model_usage('expanded',m).invalid_tag_nonempty),int(model_usage('expanded',m).cli_failures),int(model_usage('expanded',m).outside_text)] for m in s.MODELS])
    sections.append(('7. Format failures, length and provider caching',f'''A response can do useful writing and still fail the program's output contract. The following figure keeps those outcomes separate. Blue is an extractable tagged body, orange is a nonempty raw reply with invalid tags and grey is the empty CLI error. Every writer has 100 planned slots.

![Counts of valid tags, missing-tag text and the single capacity failure for each writer.](figures/expanded_full_formats.png)

{fmt_table}

There were {invalid} nonempty tag failures: 72 from Sol and 35 from Terra. Of these replies, 86 contained neither tag and 21 contained only a closing tag. The raw-text audit retains that closing tag rather than silently repairing the response. The remaining Sol failure was a capacity error before any prose appeared. No writer added commentary outside a valid tag pair. A missing boundary is a format failure; it is not evidence that the wording is wrong. All raw outputs remain saved, and the secondary audit measures their exact text without claiming to have extracted a valid post.

**Measured format case: `06-protostar/gpt-6.1-sol/01`.** The raw reply begins:

{quote(body('expanded','06-protostar','gpt-6.1-sol',1).split('\n\n')[0])}

The expected output has the same post inside one tag pair. This reply has no valid boundary, so `post_body` is null and the strict comparison excludes it. Its raw words are still classified with input type `raw_unparsed_response`. This example was chosen to show an ordinary missing-tag reply, not a refusal or an invented parsing repair. It represents one of the 107 nonempty format failures.

One Sol SETI request returned “Selected model is at capacity” with exit code 1 and no text. The failed second slot was kept. The same conversation then received the unchanged continuation for numbered slots three through five, without a retry of slot two or a fabricated assistant message. The unanswered user request remains in its native history. All 400 slots were attempted, producing 399 nonempty replies; the recovery-block sensitivity removes the entire Sol SETI block.

![Mean reply lengths and native cache-read fractions for warm turns, comparing the two prompts.](figures/expanded_full_length_cache.png)

The left panel counts words in all nonempty measured replies. Its four expanded means, in Sol/Terra/Opus/Sonnet order, are {', '.join(f"{model_usage('expanded',m).mean_words:.1f}" for m in s.MODELS)} words; the baseline means are {', '.join(f"{model_usage('baseline',m).mean_words:.1f}" for m in s.MODELS)}. The prompt prescribes no length. Terra became shorter in this collection, Sol longer, and Claude remained around 300 words. No brevity or quality preference is inferred from those lengths.

The right panel sums provider-reported cache reads and divides by total known input tokens on turns two through five. The expanded fractions are {', '.join(f"{SHORT[m]} {100*model_usage('expanded',m).warm_cache_fraction:.1f}%" for m in s.MODELS)}. The failed Sol turn has no usable token counters and is excluded from that ratio, rather than counted as a zero-token cache miss. Codex cumulative counters are differenced into per-turn increments; Claude's native cache categories are combined without double-counting session totals.

Resuming preserves the article and growing history as a cacheable prefix. The observed reuse does not prove this strategy maximizes savings: no cache-policy comparison was run, and prior drafts remain visible. The classifier exposes no cache-read counter, so its cache rate is unknown.'''))
    # Four matched writer examples are deliberately anchored to the same Kimi slot.
    examples=[]
    for model in s.MODELS:
        old=body('baseline','01-kimi',model,2);new=body('expanded','01-kimi',model,2)
        oldzone=a.regions(old);newzone=a.regions(new)
        examples.append(dict(item_id='01-kimi',model=model,turn=2,baseline=old,expanded=new))
    s.save(OUT/'examples.json',examples)
    measured=[]
    for ex in examples:
        model=ex['model'];old=a.regions(ex['baseline']);new=a.regions(ex['expanded'])
        measured.append(f'''### {SHORT[model]}: Kimi, numbered post 2

Stable pair: `01-kimi/{model}/02`, using the same 296-word release article. Expected: a standalone source-based post, with plain prose and tags under the expanded prompt. Observed tag status: `{raw('expanded','01-kimi',model,2)['format_status']}`.

**Original opening sentence and closing:**

{quote(old['opening_sentence'])}

{quote(old['closing'])}

**Expanded opening sentence and closing:**

{quote(new['opening_sentence'])}

{quote(new['closing'])}

The free classifier's whole-text negative-contrast probabilities are {probability('baseline','01-kimi',model,2,'negative_contrast')} → {probability('expanded','01-kimi',model,2,'negative_contrast')}; noun-heavy wording is {probability('baseline','01-kimi',model,2,'nominalization')} → {probability('expanded','01-kimi',model,2,'nominalization')}. Labels use the complete text; one pair is not a representative sample. [Complete responses](data/expanded_full_comparison/examples.json).{(" In this Sonnet baseline, the draft says that the poster ran a pelican test; the source attributes that work to its own author, and the poster supplied no biography. The classifier's invented-experience probability is "+probability('baseline','01-kimi',model,2,'invented_experience')+". That output is a source-role check the classifier may miss, not evidence that a low label count guarantees sound attribution. No manual label is added to the results.") if model=='claude-sonnet-5-5' else ''}''')
    sections.append(('8. Before-and-after examples and remaining contrasts','''These four examples use the same source and numbered slot for comparability, rather than selecting the largest label changes. Opening and closing sentences are exact excerpts; linked paired responses retain every paragraph.

'''+ '\n\n'.join(measured)+f'''

### Sonnet still uses “not only”

Two expanded Sonnet replies contain the literal phrase “not only”; no expanded writer uses the literal “not just” or “more than just” variants in this collection. This is a string observation, not an automatic contextual fault assignment. In `08-model-spec/claude-sonnet-5-5/03`, the passage says:

{quote(next(sentence for sentence in s.sentences(body('expanded','08-model-spec','claude-sonnet-5-5',3)) if 'not only' in sentence))}

The whole-text automatic-not-just-expansion probability is {probability('expanded','08-model-spec','claude-sonnet-5-5',3,'additive_contrast')}. The other occurrence is `12-dartmouth-writing/claude-sonnet-5-5/05`:

{quote(next(sentence for sentence in s.sentences(body('expanded','12-dartmouth-writing','claude-sonnet-5-5',5)) if 'not only' in sentence))}

That reply's probability is {probability('expanded','12-dartmouth-writing','claude-sonnet-5-5',5,'additive_contrast')}. Both phrases survive the explicit instruction to state additional facts directly. Whether the rubric's contextual escalation occurs is the API's separate judgment. Literal compliance with a wording instruction and contextual prose classification should not be conflated.

### A returned negative-contrast label can be debatable

For `16-zest/claude-opus-5-5/05`, the source concerns a restaurant agent that delayed its public launch until it could book tables. The expanded reply includes:

{quote(next(sentence for sentence in s.sentences(body('expanded','16-zest','claude-opus-5-5',5)) if sentence.startswith('A version')))}

The classifier returns negative-contrast probability {probability('expanded','16-zest','claude-opus-5-5',5,'negative_contrast')}. The counterfactual explains a source-described product choice, exposing the boundary between useful distinction and rhetorical alternative. With no independent gold label, the probability is preserved without manual correction or calling it a proven defect.'''))
    conflicts=pd.read_csv(OUT/'region_conflicts.csv')
    conflict_table=conflicts.groupby(['condition','style_id']).size().sort_values(ascending=False).head(8)
    zeroes=sum(int(pat(style).baseline_present)==0 and int(pat(style).expanded_present)==0 for style in protocol['definitions'])
    sections.append(('9. Classifier checks, disagreements and limits',f'''A free API is useful only if its output can be interpreted. The pilot checked three authored fixtures: a rhetorical example, a formatted example and a neutral example. It recognized nine of ten intended positive instances and all six intended negative instances. Those 16 checks are an informal smoke test, not a representative accuracy estimate or a calibrated validation set. One intended question-and-answer pivot was missed even though the fixture said “The takeaway? The future is here.” Its returned probability was 0.064.

A separate long-source control returned 0.922 for an obvious authored contrast, 0.946 for a hashtag tail and 0.002 for absent bold. This checks transport on the largest source, not subtle classification accuracy or attention to every source detail. The usable context limit was not independently established.

Across the full data there are **{api['regional_positive_whole_negative']} region-positive / whole-negative judgments** at the 0.5 threshold. These are separate returned answers, not mutually constrained outputs. The most frequent conflict groups are:

![The eight largest groups of regional positive labels whose corresponding whole-text label is negative. Counts are judgments rather than unique replies.](figures/expanded_full_conflicts.png)

{table(['Condition','Pattern','Regional conflicts'],[(condition,style,int(n)) for (condition,style),n in conflict_table.items()])}

The horizontal axis counts judgments, with blue for baseline and orange for expanded replies. One reply can contribute several region conflicts for the same pattern. The [conflict table](data/expanded_full_comparison/region_conflicts.csv) retains every probability pair and stable ID. Assembling transition starts or paragraph endings on separate lines can create an apparent one-sentence layout. That is why whole-text layout labels are the comparison outcome and regional layout labels are diagnostics. Contextual region-versus-whole contradictions are retained too; none is manually reconciled.

At the main threshold, {zeroes} of the 40 whole-text categories have zero labelled cases in both arms of the broader paired audit. Other categories have only a handful. These floors prevent a meaningful ranking on those criteria. A classifier can miss a real device, apply a useful-exception rule inconsistently or flag an ordinary factual contrast. Returned probabilities quantify its outputs, not the frequency of human-verified writing faults.

The prompt/taxonomy were selected after baseline inspection, Kimi is not held out, and writing conditions were collected sequentially using undated aliases. Constraints, continuation and tags change together. English AI news limits transfer; missing tags select the strict population; conversation drafts can influence one another.

No factual, preference, engagement or editing-time outcome was measured. The evidence supports a change in visible habits within this sample, while tags and contextual prose still need review. It cannot identify AI authorship or establish that people prefer the new drafts.'''))
    spend_table=table(['Condition','Writer','Completed / attempted','Mean words, nonempty','Warm cache reads','Reported dollar equivalent'],[
        [r.condition,SHORT[r.model],f'{r.completed}/{r.attempted}',f'{r.mean_words:.1f}',f'{100*r.warm_cache_fraction:.1f}%',
         'Unknown' if pd.isna(r.reported_cost_usd) else f'${r.reported_cost_usd:.6f}'] for _,r in usage.iterrows()])
    sections.append(('10. Reproduction, cached data and spend',f'''The notebook replays saved responses and classification probabilities. Its default execution makes no model calls, does not need publisher text and imports no module from this repository. All helpers are defined inside it. Source-overlap evidence is stored as candidate hashes and fixed-phrase source counts; replay verifies that the observed outputs still match that evidence before using it.

{spend_table}

Known Claude equivalents for the expanded condition total **$4.9356308**, including the $0.2131714 preview; the other 380 attempts add $4.7224594. Codex dollars and actual total subscription charges are unknown. Earlier runs retain separate ledgers, and cache replay makes no new model call.

The full classification ledger contains **{api['attempts']:,} HTTP attempts**, with statuses {api['statuses']}. Successful attempts report **${api['known_reported_cost_usd']:.6f}** in total. There are {api['successful_missing_cost']} successful attempts and {api['failed_missing_cost']} failed attempts without native cost fields. A missing field remains unknown. The separate long-source control and zero-price route probe each reported zero; earlier pilot diagnostics are recorded in their own [report](data/free_decision_pilot/REPORT.md).

The dated standard route advertises zero input/output prices, confirmed by a tiny control. Respan-only routing, zero price ceilings and disabled fallback prevent a paid substitution. Both current arms use that route. Its `:free` alias is the same checkpoint, not an independent classifier; earlier paid labels remain separate.

The full audit returned {api['valid_probabilities']:,} valid probabilities, {api['invalid_probabilities']} invalid and {api['missing_probabilities']} missing answers among nonempty cases. The empty generation has no probabilities. Native token totals and transport details are in the [summary](data/expanded_full_comparison/summary.json); classifier cache reads are not exposed.

Public records retain outputs, settings, native usage and hashes. Full publisher-containing requests remain in ignored private caches. [Validation](data/expanded_full_comparison/validation.json) reconstructs answers and checks prompt histories, raw logs, counters, pilot bytes and provider guards, then replays tables with sources, network and CLIs unavailable. Local Langfuse was unavailable; full caches and backfill records are retained.

Useful files: [executed notebook](40_linkedin_writing_habits.ipynb), [all expanded responses](data/simple_prose_v3_full/outputs.md), [baseline posts](data/main/posts.md), [all definitions and illustrations](data/expanded_audit/STYLE_GUIDE.md), [full probabilities](data/expanded_full_comparison/probabilities.csv), [protocol history](data/PROTOCOL.md), [writer registration](data/simple_prose_v3_full/preregistration.json), [classification registration](data/simple_prose_v3_full_classifier/protocol.json) and [file manifest](data/MANIFEST.json). Tables and complete examples are linked beside their interpretation above.

To replay locally, install the notebook's ordinary Python dependencies and run:

```text
cd notebooks/40-linkedin-writing-habits
python -m nbconvert --to notebook --execute --inplace 40_linkedin_writing_habits.ipynb
```

Fresh collection requires matching private sources, authenticated writer CLIs and an OpenRouter credential. The collectors have small default call limits and explicit maximum-new-call knobs. Changed prompts or models require a new registration; successful exact requests replay from cache.'''))
    sections.append(('11. Future work and further reading','''### Future work

- Randomize and interleave the two writing conditions on a fresh, held-out article sample. Keep article pairing and the same free classifier, and measure pattern changes alongside model/version evidence. The present temporal separation and prompt selection limit causal interpretation.
- Test constraints, standalone continuation and tag instructions as separate components. Measure format compliance and the same prose labels. The 107 missing-tag replies and simultaneous prompt changes motivate this test.
- Build a blinded human-labelled set with useful factual contrasts, unnecessary rhetorical contrasts and noun-heavy passages. Measure classifier precision, recall and threshold calibration. The missed authored pivot, near-floor categories and regional contradictions show why smoke controls are insufficient.
- Compare fresh independent conversations with the five-turn conversation design at a fixed topic and request budget. Measure wording diversity, cache reads and editing time. The observed cache reuse comes with prior drafts remaining visible.
- Ask readers to edit or choose complete posts after checking sources. Measure preference, factual errors and minutes of editing alongside pattern frequencies. The current study establishes no human quality or engagement improvement.

### Further reading

Links checked November 2, 2026 (Toronto time).

- [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107) (Reinhart et al., 2025). Examines grammatical and rhetorical variation in other models, motivating analysis beyond familiar vocabulary.
- [Why Does ChatGPT “Delve” So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models](https://aclanthology.org/2025.coling-main.426/) (Juzek and Ward, 2025). Provides historical lexical comparisons and cautions against assuming a universal current blacklist.
- [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016) (Kobak et al., 2025). Studies excess vocabulary at corpus scale in a different domain; it does not validate a detector for individual LinkedIn posts.
- [Submit a Decisions request](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) (OpenRouter, accessed 2026). Documents typed questions over shared state, the API mechanism used for the multi-label audit.
'''))
    contents='## Contents\n\n'+'\n'.join(f'{i}. [{title.split(". ",1)[1]}](#{re.sub(r"[^a-z0-9 -]","",title.lower()).replace(" ","-")})' for i,(title,_) in enumerate(sections,1))
    readme='\n\n'.join([intro,study,contents+'\n\n'+workflow,*['## '+title+'\n\n'+body for title,body in sections]]).rstrip()+'\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    # Embed every dependency; normal notebook execution only analyzes cached public files.
    names=['smoke_study','full_study','tagged_kimi_pilot','expanded_full_study','decision_audit','full_free_classification','expanded_full_analysis']
    aliases={'smoke_study':'s','full_study':'f','tagged_kimi_pilot':'p','expanded_full_study':'w','decision_audit':'d','full_free_classification':'c'}
    sources={}
    for name in names:
        code=(ROOT/(name+'.py')).read_text(encoding='utf-8')
        for dependency,alias in aliases.items():code=code.replace('import '+dependency+' as '+alias+'\n','')
        sources[name]=code
    setup='from pathlib import Path\nimport types\nROOT=Path.cwd()\nMODULES={}\n'+f'EMBEDDED_SOURCES={sources!r}\nALIASES={aliases!r}\n'+'''for name,code in EMBEDDED_SOURCES.items():
    module=types.ModuleType('embedded_'+name)
    module.__file__=str(ROOT/(name+'.py'))
    for dependency,alias in ALIASES.items():
        if dependency in MODULES:module.__dict__[alias]=MODULES[dependency]
    exec(compile(code,module.__file__,'exec'),module.__dict__)
    MODULES[name]=module
s=MODULES['smoke_study'];MODELS=s.MODELS
comparison=MODULES['expanded_full_analysis'].analyse()
OUT=ROOT/'data/expanded_full_comparison'
SHORT={'gpt-6.1-sol':'Sol','gpt-6.1-terra':'Terra','claude-opus-5-5':'Opus','claude-sonnet-5-5':'Sonnet'}
assert comparison['writer_records']==800 and comparison['classifier']['cases']==800
'''
    nb=nbformat.v4.new_notebook(metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
    nb.cells=[nbformat.v4.new_markdown_cell(intro),nbformat.v4.new_markdown_cell(study),nbformat.v4.new_markdown_cell(contents+'\n\n'+workflow)]
    for title,bodytext in sections:
        nb.cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\n'+bodytext))
        if title.startswith('3.'):
            nb.cells.append(nbformat.v4.new_markdown_cell('The next cell defines the collection and analysis helpers inside this notebook, but calls only deterministic cached analysis. No API, CLI or tracing call occurs on replay. The plotting cell uses one shared style block; later sections explain each saved figure.'))
            nb.cells.append(nbformat.v4.new_code_cell(setup));nb.cells.append(nbformat.v4.new_code_cell(PLOTS))
        if title.startswith('4.'):
            nb.cells.append(nbformat.v4.new_code_cell('display(patterns.query("population==\'raw_sensitivity\' and model==\'all\' and zone==\'whole\' and threshold==0.5")[["name","paired_posts","baseline_present","expanded_present","article_weighted_change_pp","article_cluster_95_low_pp","article_cluster_95_high_pp"]])'))
        if title.startswith('10.'):
            nb.cells.append(nbformat.v4.new_code_cell("display(usage)\nprint('Expanded known Claude equivalent: $4.9356308; Codex dollars and actual total unknown.')\nprint('Full classifier known reported cost:', comparison['classifier']['known_reported_cost_usd'])\nprint('Classifier attempts lacking cost:', comparison['classifier']['failed_missing_cost'] + comparison['classifier']['successful_missing_cost'])"))
    path=ROOT/'40_linkedin_writing_habits.ipynb'
    if path.exists():
        previous=nbformat.read(path,as_version=4)
        old=[cell for cell in previous.cells if cell.cell_type=='code']
        new=[cell for cell in nb.cells if cell.cell_type=='code']
        if [cell.source for cell in old]==[cell.source for cell in new]:
            for before,after in zip(old,new):after.outputs=before.outputs;after.execution_count=before.execution_count
    nbformat.write(nb,path)
    # Keep the definitions and measured surface examples, replace every obsolete paid comparison.
    guide=ROOT/'data/expanded_audit/STYLE_GUIDE.md';text=guide.read_text(encoding='utf-8')
    start=text.index('The definitions and illustrative examples') if 'The definitions and illustrative examples' in text else text.index('The 400 ')
    end=text.index('## How to use the examples')
    text=text[:start]+'''The definitions and illustrative examples were developed after the original writing collection. The current study compares a minimal request with expanded prose constraints on the same 20 articles. Contextual labels come only from the same free typed classifier applied to both arms. The categories overlap and must never be added into a score of bad writing. This guide is not an authorship detector.\n\n'''+text[end:]
    start=text.index('## How the multi-label classification works');end=text.index('## Contents',start)
    text=text[:start]+'''## How the multi-label classification works

The current classifier is `respan/span-01-lite-20260925` through OpenRouter's zero-price standard route, restricted to Respan with fallback disabled and maximum prices zero. It returns a separate yes/no probability for each of 40 patterns in six regions. Whole-text labels are primary. Thresholds of 0.5 and 0.8 are uncalibrated operating choices; no human gold labels establish their accuracy.

The per-pattern comparisons below use the **secondary matched nonempty-reply audit**: 99 pairs for Sol and 100 for each other writer. Missing-tag expanded replies are measured as exact raw text, never inferred post bodies. The report separately gives the strict tag-valid comparison (292 pairs), format failures, threshold sensitivity and regional inconsistencies. Earlier paid classifications remain saved as history and are not mixed with these counts. Literal surface examples below retain their original baseline scope and never assign contextual labels.

[Current report](../../README.md), [all current probabilities](../expanded_full_comparison/probabilities.csv), [paired comparisons and denominators](../expanded_full_comparison/paired_patterns.csv), [classification protocol](../simple_prose_v3_full_classifier/protocol.json).

'''+text[end:]
    # The guide follows the original catalogue order; ids are stable across all rubric versions.
    identifiers=list(protocol['definitions'])
    assert identifiers==[x['id'] for x in s.load(ROOT/'data/expanded_audit/criteria.json')['styles']]
    blocks=list(re.finditer(r'\*\*Decisions API labels:.*?(?=\n\*\*(?:What is counted|Surface diagnostic))',text,re.S))
    assert len(blocks)==40
    for match,style in reversed(list(zip(blocks,identifiers))):
        label='**Decisions API labels: minimal request → expanded constraints.** Each cell is a matched count/denominator. These are free-model estimates, not verified faults.\n\n'
        label+=table(['Cutoff',*SHORT.values()],[[f'p ≥ {t}',*[cell(pat(style,model=m,threshold=t)) for m in s.MODELS]] for t in [.5,.8]])+'\n'
        text=text[:match.start()]+label+text[match.end():]
    text=text.replace('../../../17-writing-validation-extension/README.md','../../../judges/17-writing-validation-extension/README.md')
    for folder in ['15-analytical-writing-style','17-writing-validation-extension']:
        text=text.replace('/tree/main/notebooks/'+folder,'/tree/main/notebooks/judges/'+folder)
    guide.write_text(text,encoding='utf-8',newline='\n')
    print('README bytes',len(readme.encode()),'cells',len(nb.cells))


if __name__=='__main__':build()
