"""Build one report and self-contained notebook for both prompt conditions."""
import csv
import json
from pathlib import Path
import re
import nbformat
import smoke_study as s

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/prompt_comparison'
MODELS=s.MODELS
NAMES=['GPT-6.1 Sol','GPT-6.1 Terra','Claude Opus 5.5','Claude Sonnet 5.5']
SHORT=['Sol','Terra','Opus','Sonnet']


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def table(headers,values):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(str(x).replace('|','/').replace('\n','<br>') for x in row)+' |' for row in values])


def quote(text):return '\n'.join('> '+line if line else '>' for line in text.strip().splitlines())


def excerpt(text,n):
    words=text.split()
    return ' '.join(words[:n])+(' …' if len(words)>n else '')


PLOT_CODE='''import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':160,'savefig.bbox':'tight',
    'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,
    'axes.axisbelow':True,'font.size':10,'figure.facecolor':'white'})
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
LABELS=['GPT-6.1 Sol','GPT-6.1 Terra','Claude Opus 5.5','Claude Sonnet 5.5']
SHORT=['Sol','Terra','Opus','Sonnet'];BASE='#b56c32';NEW='#245f91'
frame=pd.read_csv(OUT/'overall_patterns.csv')
primary=frame[(frame.zone=='whole')&frame.primary_target].copy()
primary=primary.set_index('style_id').reindex(TARGETS).reset_index()
pretty={'hashtag_tail':'Hashtag tail','single_sentence_paragraphs':'One-sentence paragraphs',
    'negative_contrast':'Negative contrast','clipped_rhythm':'Clipped rhythm','additive_contrast':'Not-just expansion',
    'emoji_layout':'Emoji layout','bold_density':'Repeated bold','formulaic_framing':'Formulaic framing',
    'invented_experience':'Unsupported experience','bold_leadins':'Bold list labels'}
y=np.arange(len(primary));fig,ax=plt.subplots(figsize=(10.4,6.2))
for i,r in enumerate(primary.itertuples()):ax.plot([r.baseline_present/4,r.new_present/4],[i,i],color='#b8b8b8',lw=2)
ax.scatter(primary.baseline_present/4,y,color=BASE,marker='o',label='Minimal request',s=55,zorder=3)
ax.scatter(primary.new_present/4,y,color=NEW,marker='s',label='Explicit prose prompt',s=48,zorder=3)
for i,r in enumerate(primary.itertuples()):ax.text(102,i,f'{r.baseline_present} → {r.new_present}',va='center',fontsize=9)
ax.set(yticks=y,yticklabels=[pretty[k] for k in primary.style_id],xlim=(-2,125),
       xticks=[0,25,50,75,100],xlabel='Posts labelled present at p ≥ 0.5 (%)',
       title='Classifier labels declined for all ten targets')
ax.invert_yaxis();ax.legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.14));ax.text(102,-.8,'Counts /400',fontsize=9)
fig.tight_layout();fig.savefig(FIG/'comparison_primary.png');plt.close(fig)

fig,ax=plt.subplots(figsize=(10.4,6.2));means=primary.change_percentage_points.to_numpy()
low=primary.paired_article_95_low.to_numpy();high=primary.paired_article_95_high.to_numpy()
ax.hlines(y,low,high,color=NEW,lw=1.5);ax.scatter(means,y,marker='s',color=NEW,zorder=3)
for pos,lo,hi in zip(y,low,high):ax.vlines([lo,hi],pos-.10,pos+.10,color=NEW,lw=1)
ax.axvline(0,color='#666',ls='--',lw=1)
ax.set(yticks=y,yticklabels=[pretty[k] for k in primary.style_id],
       xlabel='Explicit prompt minus minimal request (percentage points)',
       title=f'{int((means<0).sum())} of ten targeted patterns decreased in the classifier labels')
ax.invert_yaxis();fig.tight_layout();fig.savefig(FIG/'comparison_changes.png');plt.close(fig)

fmt=pd.read_csv(OUT/'formatting.csv');fig,axs=plt.subplots(1,3,figsize=(12,4.2))
for ax,key,title,unit in zip(axs,['words','bold_spans','hashtags'],['Post length','Literal bold markers','Literal hashtags'],['Mean words','Posts containing feature (%)','Posts containing feature (%)']):
    part=fmt[fmt.feature==key].set_index('writer_model').reindex(MODELS)
    for off,prefix,color,label in [(-.19,'baseline',BASE,'Minimal request'),(.19,'new',NEW,'Explicit prompt')]:
        vals=part[prefix+'_mean' if key=='words' else prefix+'_posts_containing'].to_numpy()
        bars=ax.bar(np.arange(4)+off,vals,.36,color=color,label=label)
        ax.bar_label(bars,labels=[f'{v:.0f}' for v in vals],padding=2,fontsize=8)
    ax.set(xticks=range(4),xticklabels=SHORT,title=title,ylabel=unit)
    ax.margins(y=.2)
axs[0].legend(frameon=False,fontsize=8);fig.suptitle('Word count and visible formatting are separate outcomes')
fig.tight_layout();fig.savefig(FIG/'comparison_formatting.png');plt.close(fig)

usage=pd.read_csv(OUT/'usage.csv');fig,ax=plt.subplots(figsize=(10.5,4.2))
for off,condition,color,label in [(-.19,'baseline',BASE,'Minimal request'),(.19,'plain_prose_v2',NEW,'Explicit prompt')]:
    part=usage[usage.condition==condition].set_index('model').reindex(MODELS)
    vals=100*part.cache_read_fraction_turns_2_to_5.to_numpy()
    bars=ax.bar(np.arange(4)+off,vals,.36,label=label,color=color)
    ax.bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=3)
ax.set(xticks=range(4),xticklabels=LABELS,ylim=(0,112),ylabel='Cached input / total input, turns 2–5 (%)',
       title='Both prompts reuse provider input during continued conversations')
ax.legend(frameon=False,ncol=2,loc='upper center');fig.tight_layout();fig.savefig(FIG/'comparison_cache.png');plt.close(fig)

turns=pd.read_csv(OUT/'turns.csv');fig,axs=plt.subplots(2,2,figsize=(10.5,6.3),sharex=True,sharey=True)
for ax,m,label in zip(axs.flat,MODELS,LABELS):
    part=turns[(turns.writer_model==m)&(turns.style_id=='negative_contrast')].sort_values('turn')
    ax.plot(part.turn,5*part.baseline_present,'o-',color=BASE,label='Minimal request')
    ax.plot(part.turn,5*part.new_present,'s-',color=NEW,label='Explicit prompt')
    ax.set(title=label,xticks=range(1,6),ylim=(-3,103))
for ax in axs[-1]:ax.set_xlabel('Conversation turn (20 posts per point)')
for ax in axs[:,0]:ax.set_ylabel('Negative contrast labelled present (%)')
axs[0,0].legend(frameon=False,fontsize=8);fig.suptitle('The same instruction remains in context through five drafts')
fig.tight_layout();fig.savefig(FIG/'comparison_turns.png');plt.close(fig)

location_pairs=[('opening_paragraph','formulaic_framing','Opening: stock framing'),
    ('transition_starts','negative_contrast','Transitions: negative contrast'),
    ('point_endings','payoff','Point endings: payoff'),('conclusion','repeated_conclusion','Conclusion: repeated point'),
    ('closing','engagement_close','Closing: generic engagement')]
fig,ax=plt.subplots(figsize=(10.5,4.6))
for i,(zone,style,label) in enumerate(location_pairs):
    r=frame[(frame.zone==zone)&(frame.style_id==style)].iloc[0]
    ax.plot([r.baseline_present/4,r.new_present/4],[i,i],color='#b8b8b8',lw=2)
    ax.scatter(r.baseline_present/4,i,color=BASE,marker='o',s=55,label='Minimal request' if i==0 else None)
    ax.scatter(r.new_present/4,i,color=NEW,marker='s',s=48,label='Explicit prompt' if i==0 else None)
    ax.text(102,i,f'{r.baseline_present} → {r.new_present}',va='center',fontsize=9)
ax.set(yticks=range(5),yticklabels=[x[2] for x in location_pairs],xlim=(-2,125),xticks=[0,25,50,75,100],
       xlabel='Posts labelled present in that location (%)',title='Locations distinguish hooks, transitions and endings')
ax.invert_yaxis();ax.legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.20));ax.text(102,-.6,'Counts /400',fontsize=9)
fig.tight_layout();fig.savefig(FIG/'comparison_locations.png');plt.close(fig)
'''


def main():
    result=s.load(OUT/'summary.json');assert result['new_writer_readable']==400
    articles=s.load(ROOT/'data/main/articles.json');by_article={a['item_id']:a for a in articles}
    patterns=rows('patterns.csv');overall=rows('overall_patterns.csv');formats=rows('formatting.csv');usage=rows('usage.csv')
    reliability=s.load(ROOT/'data/plain_prose_v2/decisions/summary.json')
    base_reliability=s.load(ROOT/'data/decision_audit/summary.json')
    targets=result['primary_targets'];examples=s.load(OUT/'examples.json')
    def pat(model,style):return next(r for r in patterns if r['writer_model']==model and r['zone']=='whole' and r['style_id']==style)
    def overall_row(style):return next(r for r in overall if r['zone']=='whole' and r['style_id']==style)
    def fmt(model,key):return next(r for r in formats if r['writer_model']==model and r['feature']==key)
    neg=overall_row('negative_contrast');paragraph=overall_row('single_sentence_paragraphs')
    decreased=sum(float(r['change_percentage_points'])<0 for r in targets)
    headline=table(['Pattern','Minimal request /400','Explicit prompt /400','Change, percentage points'],[
        [r['name'],r['baseline_present'],r['new_present'],f"{r['change_percentage_points']:+.2f}"] for r in targets])
    per_model=table(['Writer','Negative contrast','One-sentence paragraphs','Formulaic framing','Unsupported experience'],[
        [label,*[pat(m,k)['baseline_present']+' → '+pat(m,k)['new_present'] for k in ['negative_contrast','single_sentence_paragraphs','formulaic_framing','invented_experience']]] for m,label in zip(MODELS,NAMES)])
    intro='''# Can explicit instructions change recurring LinkedIn writing habits?

A person sharing a news article on LinkedIn needs to decide what happened, what readers need to know and where to stop. An assistant can produce a draft quickly. The useful outcome is a post that communicates the news accurately in a voice the person would be willing to publish under their own name.

Producing several drafts does not guarantee several different writing habits. One draft may open with a dramatic contrast, another with a short question, and a third with an apparent lesson. Their facts can differ while their rhythm, paragraph breaks and closing requests remain familiar. An editor who sees the same devices repeatedly may spend time removing them from each draft.

Consider an **illustrative example**, separate from the measured posts: an article says a transcription service can now run without an internet connection. A simple request for a LinkedIn post leaves the assistant to choose a hook, presentation and ending. It might write an account of the feature, or it might add a slogan about the future of work and a request for comments.

Suppose the person prefers connected paragraphs and a concrete explanation of who can use the feature. They can ask for that directly. They can also ask the assistant to leave out hashtags, decorative formatting and invented personal experience. This changes the instructions the writer receives while leaving the source article the same.

There is a complication: a style instruction can be followed without improving the substance. Removing a hashtag is easy to observe. Deciding whether a contrast was unnecessary, or whether a paragraph feels mechanical, depends on context and on the reader. A shorter draft can omit a needed qualification. A plain draft can still make an unsupported claim.

This comparison therefore keeps two measurements separate. Literal checks count visible items such as bold markers, words and hashtags. A separate decision model estimates whether a defined writing pattern occurs. The model can assign several patterns to one post, but its labels are judgments rather than a record of what human readers dislike.

The two approaches are ordinary writing requests. One gives the assistant an article and asks for a LinkedIn post. The other gives it the same article with an explicit description of the desired prose and the recurring habits to avoid. Both ask for five drafts in a continued conversation, so later responses can draw on earlier drafts as well as the original instruction.

The question is whether that explicit prompt reduces the targeted patterns across different articles and writers, which habits remain, and what else changes in the returned posts. A useful answer identifies the size of the observed changes and the limits of using an automated critic to judge them. It does not require a claim that one style is right for every author.
'''
    summary=f'''## Study summary

Four writers each produced five posts from each of 20 frozen AI news articles under two prompts: 400 posts with a minimal request and 400 with the explicit prose prompt. GPT-6.1 Sol, GPT-6.1 Terra, Claude Opus 5.5 and Claude Sonnet 5.5 all used high effort through their CLIs, with search and optional tools disabled. Each condition has 80 separate article-specific conversations.

A pinned Decisions classifier evaluated 40 overlapping patterns in six locations in every post, returning 192,000 probabilities. A whole-post label is counted at probability at least 0.5. It labelled negative contrast in **{neg['baseline_present']}/400 minimal-request posts and {neg['new_present']}/400 explicit-prompt posts**. One-sentence paragraph labels changed from {paragraph['baseline_present']}/400 to {paragraph['new_present']}/400. {decreased} of the ten targeted frequencies decreased. Noun-heavy wording increased from 72 to 108 posts; Opus mean length rose from 315.5 to 408.1 words.

All 800 posts are readable; the new condition uses fresh conversation IDs and unchanged articles. For an editor, these results show which recurring habits the instruction changed under this setup. The main caveat is that the classifier has no human gold labels: fewer flags do not establish more accurate, more engaging or preferable prose. The prompt was designed after observing baseline habits, and baseline collection happened earlier in time.
'''
    titles=['1. Articles and inputs','2. Writers and prompt conditions','3. How patterns are classified and compared',
        '4. Changes in targeted patterns','5. Formatting and other patterns','6. Worked cases and conversation turns',
        '7. Provider cache use and reported cost','8. Limits and practical interpretation','9. Saved data and reproduction',
        '10. Future work and further reading']
    contents='## Contents\n\n'+'\n'.join(f"{i}. [{t[3:] if i<10 else t[4:]}](#{re.sub('[^a-z0-9 -]','',t.lower()).replace(' ','-')})" for i,t in enumerate(titles,1))+'''

```mermaid
flowchart LR
    A["20 frozen full articles"] --> B["Minimal request<br/>4 writers × 5 drafts<br/>400 cached posts"]
    A --> P["Explicit prose prompt<br/>same 4 writers × 5 drafts<br/>400 new posts"]
    B --> D["Pinned Decisions API<br/>2 requests per post<br/>40 patterns × 6 locations"]
    P --> D
    D --> R["192,000 probabilities<br/>paired article comparisons"]
    B --> F["Literal formatting, length<br/>usage and protocol checks"]
    P --> F
    F --> R
```

One example follows both branches: the same science article goes to the same writer in two separate conversations. Each branch returns five posts. The classifier sees each post and article without the prompt or condition name; the analysis then compares the two five-post groups within that article. Grouping by article prevents the five related drafts from being treated as five independent news topics.
'''
    sections=[]
    article_table=table(['ID','Published','Subject and source','Words'],[
        [a['item_id'],a['publication_date'],'['+a['title']+']('+a['url']+')',a['words']] for a in articles])
    preview_path=OUT/'input_preview.json'
    if preview_path.exists():preview=s.load(preview_path)
    else:
        input_excerpt='Radio telescopes generate enormous volumes of data'
        actual=(ROOT/by_article['14-seti']['local_input']).read_text(encoding='utf-8')
        assert input_excerpt in actual
        preview={'item_id':'14-seti','source_sha256':by_article['14-seti']['text_sha256'],'verbatim_excerpt':input_excerpt,
            'scope':'Short reading excerpt only; both models receive the complete frozen article, never this excerpt as a substitute.'}
        s.save(preview_path,preview)
    sections.append((titles[0],f'''The source set is the same 20 articles used to identify the original writing habits. They were published October 23–30, 2026, within the requested news window when the sources were frozen. They cover different AI announcements, incidents and applications, including health screening, model releases, scientific data, publishing, security, consumer agents and copyright. The new prompt study reuses those inputs rather than mixing a new news sample into the comparison.

{article_table}

Both conditions and all four writers receive every article. Pairing controls source vocabulary, length and publisher tone; it does not make this a random sample. Several inputs are company announcements.

### A look at one input

The SETI source (`14-seti`) includes the words:

> {preview['verbatim_excerpt']}…

In the article, agents can control the Allen Telescope Array and work with incoming measurements. NVIDIA Holoscan processes the sensor stream, and models can be applied to the data. This is a description of a search system, with the scale of radio data motivating the application. That reading aid is a paraphrase for this report; every writer and classifier receives the full frozen article. Cases in section 6 follow this same source through both prompts and into the counting procedure.

The full body, title and date are supplied. Extraction keeps substantive lists, captions, code and corrections and removes page furniture. The [manifest](data/main/articles.json) records dates, extraction and hashes; both conditions must match it.

Sources postdate the documented writer cutoffs or release fallbacks in [the freshness record](data/main/freshness.json), and the classifier's October 6 release. Opaque later backend changes still prevent a guarantee of no prior exposure.

Full publisher text stays local and git-ignored. Hashes freeze the input; saved overlap checks support offline replay. A changed web page cannot silently replace the source.
'''))
    model_table=table(['Model','Version and pin','Provider and call','Size / precision','Output settings','Role in the comparison'],[
        [label,'`'+model+'`; immutable weight revision not exposed','OpenAI, codex exec' if model.startswith('gpt') else 'Anthropic, claude -p',
         'Not published','High effort; supported default sampling; neutral optional base instruction','Requested writer; same model ID in both conditions'] for model,label in zip(MODELS,NAMES)]+[
        ['Decisions classifier','openai/gpt-6-luna-decisions-20261006','OpenAI through OpenRouter Decisions endpoint','Not published',
         'Independent Bernoulli probabilities; no exposed effort setting; no fallback','Assigns all 40 patterns under the same rubric, with condition metadata withheld']])
    prompt=(ROOT/'data/prompt_conditions/plain_prose_v2.txt').read_text(encoding='utf-8')
    sections.append((titles[1],f'''{model_table}

Writer IDs, high effort, neutral optional base instruction, supported sampling and CLI controls stay fixed. CLI versions match; no fallback is allowed. Undated IDs cannot pin the underlying weights.

The minimal request is exactly:

```text
Write a LinkedIn post based on the following article.

<article>
{{{{complete_article_text}}}}
</article>
```

The explicit prompt specifies a goal, source rules, connected prose, exclusions and a final check. It leaves length and paragraph count open and allows necessary factual negation. Format compliance alone does not establish better writing.

<details>
<summary>Exact explicit prose prompt</summary>

```text
{prompt.rstrip()}
```

</details>

Both conditions then use exactly the same four follow-ups:

```text
Generate another post.
```

The article appears only at turn 1. Follow-ups resume the same ID and retain prior drafts. Conditions use disjoint IDs: 160 conversations in total. Later drafts are related outputs rather than independent first attempts.

```mermaid
sequenceDiagram
    participant H as Harness
    participant W as Selected writer CLI
    H->>W: New condition-specific conversation; full article and initial prompt
    W-->>H: Post 1, explicit session ID and usage
    loop Turns 2 through 5
        H->>W: Resume the same ID: Generate another post.
        Note over H: Wait for the response before the next turn
        W-->>H: Next post, same session ID and native usage
    end
```

One worker per writer runs independently; turns within a conversation are sequential. Search, tools, MCP, optional skills, hooks, plugins and memories are disabled. No writer sees another's output or a classifier result. Raw events verify tool isolation, although mandatory provider scaffolding differs.

The prompt and plan precede new generation, but target selection follows baseline results. The comparison is exploratory. Forty writer-smoke outputs and four classifier-smoke requests count toward the full run. There is no content-based retry, tuning or exclusion. [Protocol history](data/PROTOCOL.md) retains the details.
'''))
    sections.append((titles[2],'''The outcome is the fraction of posts assigned each writing pattern by the pinned decision model. A label is a model judgment, not a proven defect. The [40-pattern guide](data/expanded_audit/STYLE_GUIDE.md) explains every definition, its rationale, an authored illustration, a clearer alternative and a useful exception. The eight original contextual criteria come from the earlier writing studies; additional candidates come from empirical linguistic research and editorial observations. Evidence types remain distinguished in the source ledger.

The classifier sees the post, source, definitions, exceptions and region extracts. Writer identity, condition, prompt and previous drafts are withheld, although style can reveal clues. The rubric is identical across conditions; regex hits do not assign labels.

Forty independent yes/no questions cover each of six locations: whole post, opening paragraph, transition starts, point endings, conclusion and closing sentence. A post can carry several labels. Their probabilities need not sum to one. Each post uses two requests of 120 questions, with unchanged shared evidence; the second request does not receive the first request's answers. That gives 1,600 classifier requests and 192,000 probability answers across both conditions.

```mermaid
flowchart LR
    A["One post + its source article<br/>no condition or writer label"] --> B["Decisions API, request 1<br/>whole / opening / transitions<br/>120 independent probabilities"]
    A --> C["Decisions API, request 2<br/>point endings / conclusion / closing<br/>120 independent probabilities"]
    B -. "wait; preserve shared input" .-> C
    B --> D["240 cached probabilities per post"]
    C --> D
```

Readable answers have the expected name and a finite probability in [0,1]. Missing, refused or invalid answers remain unreadable, not absent. Presence uses p ≥ 0.5, with p ≥ 0.8 sensitivity and an ambiguous 0.2 < p < 0.8 band. These fixed thresholds are not calibrated accuracy guarantees.

Regions overlap: a closing sentence also belongs to its paragraph and whole post. Counts cannot be added. Deterministic boundary heuristics separate clear assistant notes; raw responses preserve ambiguity. Region/whole label conflicts remain unresolved.

The main comparison is paired by article. In an **illustrative counting example**, if a writer has a pattern in three of five baseline drafts and one of five prompted drafts about the same article, the article's difference is 1/5 − 3/5 = −40 percentage points. We average the 20 matched article differences for that writer. A pooled comparison keeps all four writers and all five turns together within each resampled article.

The 95% intervals use 2,000 resamples of 20 paired articles, preserving their related drafts. They quantify topic variation under this procedure, not uncertainty over readers or model weights. A zero-width interval at zero does not prove future impossibility.

Ten targets precede new generation; all 40 patterns remain visible to check substitutions. Overlapping labels are not a composite quality score. Formatting and the original 111-item inventory are separate diagnostics. The earlier phrase split does not make this intervention confirmatory.
'''))
    strict=table(['Pattern','Minimal p ≥ .8 /400','Explicit p ≥ .8 /400'],[
        [r['name'],r['baseline_high_confidence_present'],r['new_high_confidence_present']] for r in targets])
    location_pairs=[('opening_paragraph','formulaic_framing','Opening: stock framing'),
        ('transition_starts','negative_contrast','Transitions: negative contrast'),
        ('point_endings','payoff','Point endings: payoff'),('conclusion','repeated_conclusion','Conclusion: repeated point'),
        ('closing','engagement_close','Closing: generic engagement')]
    location_values=[(label,next(r for r in overall if r['zone']==zone and r['style_id']==style)) for zone,style,label in location_pairs]
    location_table=table(['Location and pattern','Minimal /400','Explicit /400'],[[label,r['baseline_present'],r['new_present']] for label,r in location_values])
    sections.append((titles[3],f'''Compare the two markers on each row of the first figure. The horizontal axis is the percentage of 400 posts the classifier labels present at p ≥ 0.5. Circles show the minimal request; squares show the explicit prose prompt. The right-hand annotation gives the two counts so a reader can distinguish a large change from a visually small one. These are overlapping pattern frequencies, not independent error rates.

![Classifier-labelled frequencies for ten preselected targets in two prompt conditions, with counts out of 400.](figures/comparison_primary.png)

{headline}

The negative-contrast label changes from {neg['baseline_present']}/400 to {neg['new_present']}/400, a difference of {float(neg['change_percentage_points']):+.2f} percentage points. This is a contextual classifier label, broader than matching one literal phrase. It can misclassify a useful factual comparison.

One-sentence paragraph labels change from {paragraph['baseline_present']}/400 to {paragraph['new_present']}/400. The prompt allows occasional short sentences, so a remaining label is not automatically a violation. A reader may prefer the layout or disagree with the classifier.

The change figure uses percentage points: negative means fewer labels with the explicit prompt. Whiskers are the paired article-bootstrap intervals; drafts remain grouped within source topics.

![Paired article-level changes for the ten targeted patterns, with 95 percent bootstrap intervals.](figures/comparison_changes.png)

{decreased} of the ten pooled target frequencies decreased. The detailed [paired tables](data/prompt_comparison/patterns.csv) show each writer separately, including topic support and stricter thresholds. Intervals concern topic variation, not reader preference or label correctness. No multiple-testing-adjusted claim is made.

{per_model}

Cells show minimal → explicit counts out of 100 per writer. Effects differ between writers. Unsupported-experience labels are estimates of attribution risk, not verified fabrications; inspect source and post before accepting that judgment.

The next table applies p ≥ 0.8 to the same cached probabilities. It tests threshold sensitivity without another model call; both cutoffs remain reported.

{strict}

The location chart selects one editorial pattern per region: opening framing, transition contrast, point-ending payoff, conclusion repetition and closing engagement. Each denominator is 400 posts. Regions overlap and do not decompose a whole-post label.

![Selected patterns in openings, transition starts, point endings, conclusions and closings, compared by prompt.](figures/comparison_locations.png)

{location_table}

{'; '.join(label+' changes from '+r['baseline_present']+'/400 to '+r['new_present']+'/400' for label,r in location_values)}. This makes the observed changes more specific than a single count for an entire post. Region extracts overlap and transition starts are short windows, so these counts cannot establish that a whole paragraph lacks the pattern or be summed into a post total. Classifier inconsistencies are retained in the error analysis.

These observations concern two instruction bundles and continued conversations. They cannot isolate the contribution of one clause.
'''))
    format_table=table(['Writer','Mean words','Bold-marker posts','Hashtag posts','Closing-question posts'],[
        [label,f"{float(fmt(m,'words')['baseline_mean']):.1f} → {float(fmt(m,'words')['new_mean']):.1f}",
         *[fmt(m,k)['baseline_posts_containing']+' → '+fmt(m,k)['new_posts_containing'] for k in ['bold_spans','hashtags','closing_question']]] for m,label in zip(MODELS,NAMES)])
    extra=[r for r in overall if r['zone']=='whole' and r['primary_target']=='False']
    extra.sort(key=lambda r:(-float(r['change_percentage_points']),r['style_id']))
    extra_table=table(['Non-primary pattern','Minimal /400','Explicit /400','Change, percentage points'],[
        [r['name'],r['baseline_present'],r['new_present'],f"{float(r['change_percentage_points']):+.2f}"] for r in extra[:5]])
    closing=overall_row('engagement_close')
    sections.append((titles[4],f'''The formatting figure asks two distinct questions: does the prompt change how much text is returned, and does it change literal formatting? The left panel uses mean words. The other panels use the share of posts containing actual Markdown bold markers or hashtags. Each panel has its own labelled axis and the same two condition colors. There is no second scale superimposed on an axis.

![Mean post length and literal bold/hashtag incidence by writer and prompt condition.](figures/comparison_formatting.png)

{format_table}

Mean words by writer are { '; '.join(label+': '+f"{float(fmt(m,'words')['baseline_mean']):.1f} → {float(fmt(m,'words')['new_mean']):.1f}" for m,label in zip(MODELS,NAMES))}. The instruction does not set a word target, so these are changes in returned content under the two prompts, rather than compliance with a fixed length. The counts above expose how much visible format changed alongside the model-assigned prose labels.

These are direct text measurements. Removing hashtags establishes format compliance, while a length change can add or remove useful context. Neither establishes clearer reasoning. The complete [formatting comparison](data/prompt_comparison/formatting.csv) includes paragraphs, emoji, em dashes, lists, headings and closing questions.

Length remains an outcome: longer posts offer more chances for a construction, while short ones can avoid it by omitting explanation. The saved [per-post ledgers](data/plain_prose_v2/posts.csv) retain words and boundaries for further checks without generating new text.

The next five non-primary rows have the largest signed increases, with alphabetical ties. This deterministic diagnostic exposes possible substitutions; it is not confirmatory.

{extra_table}

Generic engagement closing was an additional requested restriction. Its label changes from {closing['baseline_present']}/400 to {closing['new_present']}/400. A substantive closing question can be useful. Its literal punctuation is measured separately from the model-defined generic engagement request.

Rare patterns cannot be ranked reliably. Zero after an explicit format ban is a compliance floor, not proof of better writing. Full zeroes, ambiguity and topic counts remain in [all-pattern results](data/prompt_comparison/overall_patterns.csv).

Family totals expose both tested member counts. They represent two models per provider, not all of its models or an isolated training effect.

The unchanged 111-item inventory measures exact wording, with source-absence denominators and locations. Its negative-reframing regex is narrower than a contextual judgment that a contrast is unnecessary. [Baseline phrase counts](data/main/fixed_prose_counts.csv) and [explicit-prompt phrase counts](data/plain_prose_v2/fixed_prose_counts.csv) allow that distinction to be checked without conflating the two methods.
'''))
    cases=[]
    for i,ex in enumerate(examples):
        base,new=ex['baseline'],ex['plain_prose_v2'];bp=base['probabilities']['negative_contrast'];np_=new['probabilities']['negative_contrast']
        cases.append(f'''### Case {i+1}: {ex['source_title']}

Slot `{ex['post_id']}` uses [this source]({ex['source_url']}). Both drafts should reflect its facts; the explicit draft also receives the prose requirements. There is no single gold post.

Minimal-request opening:

{quote(excerpt(base['zones']['opening_paragraph'],40))}

Explicit-prompt opening:

{quote(excerpt(new['zones']['opening_paragraph'],40))}

Minimal closing:

{quote(excerpt(base['zones']['closing'],25))}

Explicit closing:

{quote(excerpt(new['zones']['closing'],25))}

Measured words: {base['formatting']['words']} → {new['formatting']['words']}; hashtags: {base['formatting']['hashtags']} → {new['formatting']['hashtags']}. Negative-contrast probability: {bp:.2f} → {np_:.2f}, hence labels {str(bp>=.5).lower()} → {str(np_>=.5).lower()} at p ≥ 0.5. These are literal counts and model judgments, not a quality verdict.''')
    conflicts=table(['Condition','Region-positive / whole-negative labels','Region questions','Readable classifier answers'],[
        ['Minimal request',base_reliability['whole_region_conflicting_labels'],'80,000',base_reliability['valid_answers']],
        ['Explicit prose prompt',reliability['whole_region_conflicting_labels'],'80,000',reliability['valid_answers']]])
    turn_rows=rows('turns.csv')
    turn_first=[r for r in turn_rows if r['style_id']=='negative_contrast' and r['turn']=='1']
    turn_last=[r for r in turn_rows if r['style_id']=='negative_contrast' and r['turn']=='5']
    turn_numbers=f"In the explicit condition, the label appears in {sum(int(r['new_present']) for r in turn_first)}/80 first drafts and {sum(int(r['new_present']) for r in turn_last)}/80 fifth drafts. The corresponding minimal-request counts are {sum(int(r['baseline_present']) for r in turn_first)}/80 and {sum(int(r['baseline_present']) for r in turn_last)}/80. Each pooled count contains the same 20 articles and four writers. These are observed positions in continued conversations, not a randomized test of repetition itself."
    sections.append((titles[5],'''The turn figure follows one preselected prose target through the five drafts. Each point is a percentage of 20 posts, one per article at that turn for that writer. Lines connect observed conversation positions. They do not imply that asking again causes a trend independently of the previous answers already in context.

![Negative-contrast classifier labels by conversation turn, writer and prompt condition.](figures/comparison_turns.png)

'''+turn_numbers+'''

The [turn table](data/prompt_comparison/turns.csv) includes all 40 patterns so this one chart does not substitute for the full record. Twenty observations per point still represent the same 20 source topics, not new independent topic samples at each turn.

The six cases retain the earlier report's slots, chosen before intervention results: consecutive Sol science drafts, an Opus draft of the same source, a Terra security case, a Sonnet fifth draft and its earlier attribution case. They cover ordinary comparisons, not selected extremes. Excerpts are shortened; [complete paired posts](data/prompt_comparison/examples.json) preserve context. Each case connects input, expected behavior, raw wording and parsed measurements. Its effect on a label count is not evidence of factual correctness.

'''+ '\n\n'.join(cases)+f'''

### What failed, and what remains uncertain

All 800 posts are readable, a collection ceiling that cannot rank quality. There is no unreadable response to show and no factual or human-quality gold score. Readable posts can still be wrong or violate instructions.

The classifier sometimes labels a region positive and its whole post negative, a logical conflict under the threshold. The following counts are region-label conflicts, not unique faulty posts or proven false answers.

{conflicts}

Conflicts remain in the [baseline](data/decision_audit/region_consistency.csv) and [explicit](data/plain_prose_v2/decisions/region_consistency.csv) records. Whole-post answers are used directly, without manual overrides. Without gold labels we cannot settle which answer is correct; consistent answers can also be wrong.

These examples teach the measurement and identify passages to review. Earlier writing validation found weak agreement on alleged prose faults, reinforcing the need to treat these labels as estimates.
'''))
    cache_table=table(['Writer','Minimal cached share, turns 2–5','Explicit cached share, turns 2–5','Explicit input tokens','Explicit reported writer dollars'],[
        [label,*[f"{float(next(r['cache_read_fraction_turns_2_to_5'] for r in usage if r['condition']==cond and r['model']==m)):.2%}" for cond in ['baseline','plain_prose_v2']],
         next(r['input_tokens'] for r in usage if r['condition']=='plain_prose_v2' and r['model']==m),
         next(r['reported_cost_usd'] or 'Unavailable' for r in usage if r['condition']=='plain_prose_v2' and r['model']==m)] for m,label in zip(MODELS,NAMES)])
    known_writer=sum(float(r['reported_cost_usd']) for r in usage if r['condition']=='plain_prose_v2' and r['reported_cost_usd'])
    sections.append((titles[6],f'''Provider caching reuses an input prefix. Local caching replays a saved response without generation. Each new post required a generation; reused smoke slots and offline replays add no calls.

The chart divides cached by total input tokens on turns 2–5. Its denominator includes prior posts and runtime context. Both conditions use short follow-ups in explicitly resumed conversations.

![Weighted provider cache-read shares on conversation follow-ups for each prompt and writer.](figures/comparison_cache.png)

{cache_table}

Cache shares are observed, not a routing experiment. Prompt length, history, timing and backend routing differ. A high cached share can still accompany a larger bill.

Claude reports ordinary input, cache-read input and cache-write input separately, so they are added for inclusive input. Codex's input counter is already inclusive. Its resumed-session counters accumulate, and Claude's reported cost accumulates, so the harness differences those fields within each conversation. Native counters and per-turn values are retained; missing dollars remain missing. No padding is added to trigger caching.

The new 400 writer requests report ${known_writer:.6f} for Claude. New classifier requests report ${reliability['reported_cost_usd']:.6f}, for a known additional equivalent of ${known_writer+reliability['reported_cost_usd']:.6f}. Codex dollar equivalents and actual subscription charges remain unavailable, so that known sum is not a complete invoice. Earlier baseline and generation-smoke usage remain separately recorded; intervention smoke is included in the new 400 rather than billed twice.

The classifier transport exposes no effort control or cache-read/write counters. The original four writers use high effort; an unsupported effort parameter is not invented for the decision endpoint. Shared evidence is unchanged across the two classifier requests for a post, but missing counters prevent measuring its backend cache use. Native usage and cost records are saved for every request.
'''))
    sections.append((titles[7],'''The comparison shows how text and classifier labels differ between two writing requests on matched sources. It does not rank writers for LinkedIn or establish reader preference.

The prompt bundles format bans, prose guidance, attribution and a final check. Reductions cannot be assigned to individual clauses. Format compliance is easy to observe; contextual labels can respond to length or tone. Component tests are needed to separate those mechanisms.

There is no human-written control, reader study, engagement result or factual gold answer. An unsupported-experience label is a warning, not a verified fabrication. Contextual judgments have not been validated for the intended audience.

Targets come from baseline results on these same topics. The comparison is exploratory, with possible topic-specific adaptation. The earlier phrase split does not make this a confirmatory prompt test.

Baseline preceded intervention. CLI versions and controls match, but undated writer IDs leave backend changes uncontrolled. Randomized interleaving would give stronger evidence about prompt effects.

Twenty AI-news topics, including company announcements, do not cover all writing. Results may change across subjects, languages and author identities. Five continued drafts differ from independent first attempts.

One uncalibrated classifier can favor a style, confuse presence with excess or disagree across regions. Threshold sensitivity and conflicts expose part of that uncertainty. Validate candidate prompts with intended readers and source checks before treating fewer labels as better prose.
'''))
    sections.append((titles[8],'''There are 800 writer generations, 160 conversations and 1,600 classifier requests. Separate condition caches retain native responses, hashes, settings, sessions, turns, timing and usage. Complete article-containing wire bodies remain local and git-ignored.

- [Executed notebook](40_linkedin_writing_habits.ipynb), with all analysis and collection helpers embedded for self-contained replay.
- [Exact new prompt](data/prompt_conditions/plain_prose_v2.txt), [prompt rationale](data/prompt_conditions/plain_prose_v2.json), [intervention registration](data/plain_prose_v2/preregistration.json) and [protocol history](data/PROTOCOL.md).
- [Baseline writer data](data/main/), [baseline classifier data](data/decision_audit/), [new writer data](data/plain_prose_v2/) and [new classifier data](data/plain_prose_v2/decisions/).
- [All 400 explicit-prompt posts](data/plain_prose_v2/posts.md), with source links and stable article/writer/turn IDs.
- [All pattern changes](data/prompt_comparison/patterns.csv), [pooled patterns](data/prompt_comparison/overall_patterns.csv), [article pairs](data/prompt_comparison/paired_articles.csv), [turns](data/prompt_comparison/turns.csv) and [family members](data/prompt_comparison/families.csv).
- [Literal formatting](data/prompt_comparison/formatting.csv), [writer usage](data/prompt_comparison/usage.csv), [classifier reliability](data/prompt_comparison/classifier_reliability.csv), [worked cases](data/prompt_comparison/examples.json) and [definitions for every pattern](data/expanded_audit/STYLE_GUIDE.md).
- [Comparison validation](data/prompt_comparison/validation.json), including source/prompt hashes, fresh sessions, native counter checks and article-free offline replay.
- [Original fixed phrase counts](data/main/fixed_prose_counts.csv), [new fixed phrase counts](data/plain_prose_v2/fixed_prose_counts.csv), [original lexical inventory](data/prose_lexicon.json) and [file manifest](data/MANIFEST.json).

From this experiment folder, default analysis is offline:

```powershell
python -m unittest test_smoke_study.py test_full_study.py test_expanded_audit.py test_decision_audit.py test_prompt_study.py
python prompt_study.py analyse
python prompt_comparison.py
python -m nbconvert --to notebook --execute --inplace 40_linkedin_writing_habits.ipynb
```

The notebook embeds all helpers and replays caches without API, CLI or network calls. It needs Python, NumPy, pandas, matplotlib, nbformat and nbconvert; requests is for explicit live collection. Saved overlap checks reject changed output or rule fingerprints.

Live collection is explicit, with small ordinary call limits. Completed slots are verified and reused. Missing middle turns or interrupted starts require reconciliation because later drafts depend on them. The 40 writer-smoke slots and four classifier-smoke requests are included in the full counts.

Validation checks provenance and replay integrity, not current provider behavior or writing quality. Run history and amendments stay in [the protocol](data/PROTOCOL.md).
'''))
    sections.append((titles[9],'''Sources checked November 1–2, 2026. The following sources motivate methods or further tests; none validates the present classifier as a measure of human annoyance.

### Future work

- Randomize and interleave prompt conditions on a fresh matched topic sample, retaining article pairing. Measure the same pattern frequencies and post lengths; the current sequential collection leaves time and backend changes as a confound.
- Compare components of the instruction: format restrictions alone, connected-prose guidance alone, attribution guidance alone and the full specification. Measure which target changes persist; this study changes several instructions together.
- Add a blinded reader study and a source-grounded factual review, with criteria fixed in advance. Measure clarity, preference and unsupported claims alongside classifier labels; current reductions have no human quality validation.
- Test other subjects, languages and author-provided experiences. Measure whether patterns and attribution warnings transfer; the present set is limited to AI news and supplies no personal biography.

### Further reading

- [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107v2) (Reinhart et al., 2025). Studies grammatical variation in other model generations and motivates looking beyond a few familiar words.
- [Why Does ChatGPT “Delve” So Much?](https://aclanthology.org/2025.coling-main.426/) (Juzek and Ward, 2025). Provides a reproducible historical vocabulary analysis, which should not be treated as a universal current blacklist.
- [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016v5) (Kobak et al., 2025). Explains corpus-level excess-word analysis in a different writing domain.
- [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) (OpenAI, accessed 2026). Describes explicit instructions and evaluation of prompt behavior; guidance is a starting point rather than proof of improvement.
- [Decisions API](https://developers.openai.com/api/docs/guides/decisions) (OpenAI, accessed 2026). Explains independent typed probability questions and the need to validate thresholds in an application.
'''))
    readme='\n\n'.join([intro,summary,contents,*['## '+title+'\n\n'+body for title,body in sections]]).rstrip()+'\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    saved=['# Explicit-prompt generated posts\n\n400 new posts in 80 article-specific conversations. These are raw responses, not editorially approved posts.\n']
    for path in sorted((ROOT/'data/plain_prose_v2/responses').glob('*/*/*.json')):
        if '.started.' in path.name:continue
        r=s.load(path);item=by_article[r['item_id']]
        slot=f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}"
        saved.append(f"## {slot}\n\nSource: [{item['title']}]({item['url']}). Session: `{r['session_id']}`.\n\n"+r['text']+'\n')
    (ROOT/'data/plain_prose_v2/posts.md').write_text('\n'.join(saved),encoding='utf-8')
    # Each module is defined from embedded source. No repository module is imported on replay.
    sources={}
    names=['smoke_study','full_study','main_analysis','expanded_audit','decision_audit','prompt_study','prompt_comparison']
    imports={'smoke_study':'s','full_study':'f','main_analysis':'a','decision_audit':'d'}
    for name in names:
        code=(ROOT/(name+'.py')).read_text(encoding='utf-8')
        for module,alias in imports.items():code=code.replace('import '+module+' as '+alias+'\n','')
        sources[name]=code
    setup='''from pathlib import Path
import types
ROOT=Path.cwd()
MODULES={}
'''+ 'EMBEDDED_SOURCES='+repr(sources)+'''\nALIASES={'smoke_study':'s','full_study':'f','main_analysis':'a','decision_audit':'d'}
for name,code in EMBEDDED_SOURCES.items():
    module=types.ModuleType('embedded_'+name)
    module.__file__=str(ROOT/(name+'.py'))
    for dependency,alias in ALIASES.items():
        if dependency in MODULES:module.__dict__[alias]=MODULES[dependency]
    exec(compile(code,module.__file__,'exec'),module.__dict__)
    MODULES[name]=module
s=MODULES['smoke_study'];MODELS=s.MODELS
MODULES['main_analysis'].analyse()
MODULES['expanded_audit'].analyse_expanded()
MODULES['decision_audit'].analyse_decisions()
MODULES['prompt_study'].analyse_prompt_study()
comparison=MODULES['prompt_comparison'].compare_prompts()
TARGETS=MODULES['prompt_comparison'].TARGETS
OUT=ROOT/'data/prompt_comparison'
assert comparison['fresh_conversation_ids'] and comparison['classifier_definitions_identical']
'''
    nb=nbformat.v4.new_notebook(metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
    nb.cells=[nbformat.v4.new_markdown_cell(intro),nbformat.v4.new_markdown_cell(summary),nbformat.v4.new_markdown_cell(contents)]
    for title,body in sections:
        nb.cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\n'+body))
        if title.startswith('3.'):
            nb.cells.append(nbformat.v4.new_markdown_cell('The next cell defines every helper within the notebook and replays saved responses. It contains no live collection call. All uncertainty calculations resample article groups. The plotting cell uses one shared style block for the five figures interpreted in the later results sections.'))
            nb.cells.append(nbformat.v4.new_code_cell(setup));nb.cells.append(nbformat.v4.new_code_cell(PLOT_CODE))
        elif title.startswith('4.'):
            nb.cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'overall_patterns.csv').query(\"zone == 'whole' and primary_target\")[[\"name\",\"baseline_present\",\"new_present\",\"change_percentage_points\",\"paired_article_95_low\",\"paired_article_95_high\"]])"))
        elif title.startswith('7.'):
            nb.cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(OUT/'usage.csv')[[\"condition\",\"model\",\"mean_words\",\"cache_read_fraction_turns_2_to_5\",\"reported_cost_usd\"]])"))
        elif title.startswith('9.'):
            nb.cells.append(nbformat.v4.new_code_cell("writer=pd.read_csv(OUT/'usage.csv').query(\"condition == 'plain_prose_v2'\").reported_cost_usd.sum()\nclassifier=s.load(ROOT/'data/plain_prose_v2/decisions/summary.json')['reported_cost_usd']\nprint(f'Known additional reported equivalent: ${writer+classifier:.6f}')\nprint('Codex dollar equivalent and actual total subscription charges: unavailable.')"))
    notebook_path=ROOT/'40_linkedin_writing_habits.ipynb'
    if notebook_path.exists():
        previous=nbformat.read(notebook_path,as_version=4)
        old_code=[cell for cell in previous.cells if cell.cell_type=='code']
        new_code=[cell for cell in nb.cells if cell.cell_type=='code']
        if [cell.source for cell in old_code]==[cell.source for cell in new_code]:
            for old,new in zip(old_code,new_code):
                new.outputs=old.outputs;new.execution_count=old.execution_count
            print('Unchanged code: preserved',len(new_code),'executed cells during narrative-only rebuild.')
    nbformat.write(nb,notebook_path)
    print('Current comparison README bytes:',len(readme.encode()),'; notebook cells:',len(nb.cells))


if __name__=='__main__':main()
