"""Build the current full-run README and independent offline notebook."""
import csv
import json
from pathlib import Path
import re
import nbformat
import smoke_study as s
from build_style_guide import audit_report_section

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/main'
MODELS=s.MODELS
NAMES=['GPT-6.1 Sol','GPT-6.1 Terra','Claude Opus 5.5','Claude Sonnet 5.5']


def rows(name):
    with (DATA/name).open(encoding='utf-8',newline='') as handle:return list(csv.DictReader(handle))


def table(headers,data):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
        ['| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in data])


PLOT_CODE='''import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':160,'savefig.bbox':'tight',
    'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,
    'axes.axisbelow':True,'font.size':10,'figure.facecolor':'white'})
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
LABELS=['GPT-6.1 Sol','GPT-6.1 Terra','Claude Opus 5.5','Claude Sonnet 5.5']
COLORS=['#245f91','#bf6d30','#39846c','#8265a5']
format_frame=pd.read_csv(DATA/'formatting_summary.csv')
features=[('bold_spans','Bold markers'),('emoji_codepoints','Emoji'),('hashtags','Hashtags'),
    ('em_dashes','Em dash'),('response_preface','Post wrapper'),
    ('editorial_note','Editorial note'),('closing_question','Closing question')]
matrix=[]
for model in MODELS:
    matrix.append([float(format_frame[(format_frame.model==model)&(format_frame.feature==key)].iloc[0].post_fraction)*100 for key,_ in features])
fig,ax=plt.subplots(figsize=(11.2,4.0));im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
for i,row in enumerate(matrix):
    for j,value in enumerate(row):ax.text(j,i,f'{value:.0f}/100',ha='center',va='center',color='white' if value>=60 else '#222')
ax.set(xticks=range(len(features)),xticklabels=[label for _,label in features],yticks=range(4),yticklabels=LABELS,
    title='Formatting recurs across 20 topics, even as the posts change')
ax.tick_params(axis='x',rotation=28);ax.grid(False);fig.colorbar(im,ax=ax,label='Posts containing feature (%)',shrink=.8)
fig.tight_layout();fig.savefig(FIG/'main_formatting.png');plt.close(fig)

fixed=pd.read_csv(DATA/'fixed_prose_counts.csv');whole=fixed[fixed.zone=='whole']
focus=['isnt_x_its_y','my_takeaway','not_just_x','why_this_matters','the_opportunity','teaser_question']
fig,axs=plt.subplots(2,3,figsize=(12,6.2),sharey=True)
for ax,phrase in zip(axs.flat,focus):
    part=whole[whole.phrase_id==phrase].set_index('model').reindex(MODELS)
    vals=100*part.post_fraction.to_numpy();low=100*part.article_bootstrap_95_low.to_numpy();high=100*part.article_bootstrap_95_high.to_numpy()
    bars=ax.bar(range(4),vals,color=COLORS,yerr=np.vstack([vals-low,high-vals]),capsize=3)
    ax.bar_label(bars,labels=[f'{v:.0f}' for v in vals],padding=3,fontsize=9)
    pretty={'isnt_x_its_y':"isn't X / it's Y",'not_just_x':'not just / not only X'}
    ax.set(xticks=range(4),xticklabels=['Sol','Terra','Opus','Sonnet'],ylim=(0,105),title=pretty.get(phrase,phrase.replace('_',' ')))
for ax in axs[:,0]:ax.set_ylabel('Posts containing candidate (%)')
fig.suptitle('Fixed prose candidates have different frequencies across the tested models',fontsize=13)
fig.tight_layout();fig.savefig(FIG/'main_prose.png');plt.close(fig)

cache=pd.read_csv(DATA/'provider_cache_usage.csv');fig,ax=plt.subplots(figsize=(10,4));x=np.arange(4)
for offset,condition,color,hatch in [(-.19,'Initial turn','#245f91',''),(.19,'Follow-ups 2-5','#bf6d30','//')]:
    vals=[]
    for model in MODELS:
        part=cache[(cache.requested_model==model)&((cache.turn==1) if condition=='Initial turn' else (cache.turn>1))]
        vals.append(100*part.cache_read_tokens.sum()/part.input_total.sum())
    bars=ax.bar(x+offset,vals,.36,label=condition,color=color,hatch=hatch)
    ax.bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=3)
ax.set(xticks=x,xticklabels=LABELS,ylim=(0,112),ylabel='Reported cached input / total input (%)',
       title='Short follow-ups reuse cached input, including earlier conversation turns')
ax.legend(frameon=False,ncol=2,loc='upper center');fig.tight_layout();fig.savefig(FIG/'main_cache.png');plt.close(fig)

turns=pd.read_csv(DATA/'turn_summary.csv');fig,ax=plt.subplots(figsize=(9,4))
for model,label,color,marker in zip(MODELS,LABELS,COLORS,['o','s','^','D']):
    part=turns[turns.model==model].sort_values('turn');ax.plot(part.turn,part.mean_words,marker=marker,label=label,color=color)
ax.set(xticks=range(1,6),xlabel='Turn in the same conversation (20 articles per point)',ylabel='Mean proposed-post words',
       title='Post length varies by model and conversation turn')
ax.legend(frameon=False,bbox_to_anchor=(1,1),loc='upper left');fig.tight_layout();fig.savefig(FIG/'main_turns.png');plt.close(fig)

extra=pd.read_csv(ROOT/'data/decision_audit/counts.csv')
chosen=[('negative_contrast','Negative\\ncontrast'),('engagement_close','Generic\\nengagement close'),
        ('clipped_rhythm','Clipped\\nrhythm'),('single_sentence_paragraphs','One-sentence\\nparagraphs'),
        ('bold_leadins','Bold list\\nlabels'),('hashtag_tail','Generic\\nhashtag tail')]
matrix=[[int(extra[(extra.writer_model==m)&(extra.zone=='whole')&(extra.style_id==k)].iloc[0].posts_labelled_present)
         for k,_ in chosen] for m in MODELS]
fig,ax=plt.subplots(figsize=(11.2,4.1));im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
for i,row in enumerate(matrix):
    for j,value in enumerate(row):ax.text(j,i,f'{value}/100',ha='center',va='center',color='white' if value>=60 else '#222')
ax.set(xticks=range(len(chosen)),xticklabels=[v for _,v in chosen],yticks=range(4),yticklabels=LABELS,
       title='The decision model assigns different pattern frequencies across writers')
ax.grid(False);fig.colorbar(im,ax=ax,label='Posts labelled present at p ≥ 0.5 (%)',shrink=.8)
fig.text(.5,.01,'Exploratory classifier estimates, without human validation; 100 posts per writer.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.04,1,1));fig.savefig(FIG/'main_expanded_styles.png');plt.close(fig)
'''


def main():
    summary=s.load(DATA/'summary.json');assert all(summary['gates'].values()),summary['gates']
    models=summary['models'];articles=s.load(DATA/'articles.json');fixed=rows('fixed_prose_counts.csv')
    decision_summary=s.load(ROOT/'data/decision_audit/summary.json');assert decision_summary['complete']
    fmt=rows('formatting_summary.csv');candidates=rows('phrase_candidates.csv')
    valid=[s.load(p) for p in sorted((DATA/'responses').glob('*/*/*.json')) if '.started.' not in p.name]
    posts=rows('posts.csv');by_id={a['item_id']:a for a in articles}
    def feature(model,key):return next(r for r in fmt if r['model']==model and r['feature']==key)
    def phrase(model,key,zone='whole'):return next(r for r in fixed if r['model']==model and r['phrase_id']==key and r['zone']==zone)
    def rec(model,item,turn):return next(r for r in valid if r['requested_model']==model and r['item_id']==item and r['turn']==turn)
    def quoted(text):return '\n'.join('> '+line for line in text.strip().splitlines())
    def pct(value):return f'{float(value):.1%}'
    word_total=sum(a['words'] for a in articles)
    intro='''# How four models write LinkedIn posts from recent AI news

A person sharing an AI news article on LinkedIn needs to decide what to say first, why the news matters to a professional reader, and how to finish. A useful post keeps the facts straight while giving the reader a reason to spend time on them. Asking an assistant for a draft leaves many of those choices to the assistant.

The first sentence can lead with the announcement, raise a question or set up a contrast. Later paragraphs can connect the news to a practical decision. The ending might offer a lesson, ask readers for their views or simply stop after the last useful point. These choices give a post much of its voice.

Consider an illustrative example. A lab announces a model that can work with longer documents. One possible post explains which documents a team could now process. Another explains the cost of running it. These are different angles on the same news, and neither needs an instruction about tone or length to be possible. This is a teaching example, not one of the measured model responses.

Now imagine asking for another post in the same conversation. The assistant can see the earlier draft. It may choose another angle, reuse a familiar opening or keep the same closing structure. Changing the facts it highlights does not necessarily change its writing habits.

A repeated expression is not automatically a problem. A closing question can invite a useful discussion, and a technical term may be necessary to describe the news accurately. The question here is how often the same phrases and structures recur, and whether that happens across unrelated subjects rather than only within one article.

That distinction matters to someone choosing or editing a writing assistant. If an opening recurs across many drafts, the person may spend time replacing it. If the draft's closing question is nearly automatic, it may make posts on different subjects feel alike. Counting only whether complete documents differ would miss both patterns.

To measure recurrence, this study counts how many posts contain a phrase or formatting feature. If 12 of a model's 100 posts use an expression, its post incidence is 12%. It also counts how many of the 20 article topics contain it. A phrase found in 12 posts across eight subjects is different evidence from a phrase found in all five attempts about one subject.

The comparison keeps the source article and the short request the same for all four models. Each model gets one conversation per article and writes five posts in that conversation. This lets us ask which openings, transitions, point endings, post closings and layouts recur when a person requests several drafts from recent AI news.
'''
    headline_counts=[int(feature(m,'closing_question')['posts_containing']) for m in MODELS]
    study_summary=f'''All four models returned 100 readable responses: **400 posts across 20 recent news topics**, with five posts in each model/article conversation. Every model ran at high effort through its CLI. The first request included the full article; the next four messages were exactly `Generate another post.` No tool calls were observed.

Closing questions appeared in {headline_counts[0]}/100 Sol posts, {headline_counts[1]}/100 Terra posts, {headline_counts[2]}/100 Opus posts and {headline_counts[3]}/100 Sonnet posts. The fixed phrase inventory and cross-topic search below show which parts of the prose recur alongside those layouts. These are observed writing habits, not scores of which model writes better.

The main caveat is the conversation setup: later posts can draw on earlier drafts. These results describe the requested workflow on this 20-topic AI-news sample, not five independent answers to an empty conversation or every kind of LinkedIn writing. The source text and unavoidable CLI/runtime scaffolding can also affect the output.
'''
    contents='''## Contents

1. [The source articles](#1-the-source-articles)
2. [Models and controlled requests](#2-models-and-controlled-requests)
3. [What counts as repeated prose](#3-what-counts-as-repeated-prose)
4. [Formatting across the posts](#4-formatting-across-the-posts)
5. [Fixed prose candidates and discovered phrases](#5-fixed-prose-candidates-and-discovered-phrases)
6. [Conversation turns and concrete cases](#6-conversation-turns-and-concrete-cases)
7. [Provider cache reuse](#7-provider-cache-reuse)
8. [Limits and practical interpretation](#8-limits-and-practical-interpretation)
9. [Spend, saved data and reproduction](#9-spend-saved-data-and-reproduction)
10. [Future work and further reading](#10-future-work-and-further-reading)

```mermaid
flowchart TD
    A["20 distinct AI news topics<br/>October 23-30, 2026"] --> B["Freeze full article text locally<br/>URLs, dates and hashes in manifest"]
    B --> C["4 models, high effort<br/>80 separate conversations"]
    C --> D["Initial full-article prompt<br/>then 4 short follow-ups per conversation"]
    D --> E["400 raw responses and usage records<br/>all responses retained"]
    E --> F["Post boundaries, 111 fixed prose candidates<br/>formatting and source-overlap checks"]
    F --> G["10 discovery topics / 10 confirmation topics<br/>cross-topic phrases and article-level intervals"]
    G --> H["Tables, figures and worked cases<br/>offline replay from saved data"]
```

One article takes the same path through each model. Its full text appears only on the first turn, and the CLI carries the conversation forward for the next four requests. Each new post is saved with its source ID, model, turn and provider usage. The analysis uses the saved responses, not another model's opinion about their style.
'''
    sections=[]
    source_table=table(['ID / source article','Published','Area','Words','Analysis split'],[
        [f"[{a['item_id']}: {a['title']}]({a['url']})",a['publication_date'],a['category'],a['words'],a['split']] for a in articles])
    sections.append(('1. The source articles',f'''The input set contains {word_total:,} words across 20 articles published October 23-30, 2026, inside the requested ten-day window relative to November 1 in Toronto. Each article covers a different announcement, incident, commercial development or research update. The topics include model releases, healthcare, scientific data, security, publishing, copyright, infrastructure and consumer applications.

{source_table}

Each row is one source shared by all four models, not an additional prompt variation. The articles vary in length and in publisher voice. Keeping that variation is part of testing habits across subjects; matching the same article within every four-model comparison prevents one model receiving easier or more promotional source material than another. It does not make the selected news a random sample of the industry.

The complete article body was used, including substantive lists, code, captions and correction notices. Extraction removed navigation, sharing widgets, related-story cards and accessibility-only labels. The title and publication date accompanied the body. No model received a summary, length instruction or editorial explanation of the article. The full inputs are local and git-ignored because public access does not itself grant redistribution rights. [The article manifest](data/main/articles.json) retains URLs, dates, extraction selectors, retrieval times and hashes; [source-overlap records](data/main/source_overlap.json) support offline analysis without republishing each article.

The date rule is recorded in [the model freshness record](data/main/freshness.json). Sol's documented cutoff is April 30, 2026 and Terra's is June 1. The Claude release-date fallbacks are September 22 for Opus 5.5 and September 28 for Sonnet 5.5. Every selected article was published later. Recent publication reduces ordinary training-data overlap, but undated model IDs and undocumented later updates mean it cannot prove that a provider never saw a page.

The manifest distinguishes publication and event dates; both remain inside the window. The previously inspected Mistral smoke article is excluded.'''))
    model_table=table(['Model','Requested version / immutable pin','Provider and call','Size / precision','Settings','Why included'],[
        [label,f'`{m}`; no immutable dated revision exposed','OpenAI, `codex exec`' if m.startswith('gpt') else 'Anthropic, `claude -p`',
         'Not published','High effort; default supported sampling; neutral optional base instruction',
         'Requested GPT-6.1 family member' if m.startswith('gpt') else 'Requested Claude 5.5 family member'] for m,label in zip(MODELS,NAMES)]+[
        ['Decisions classifier','`openai/gpt-6-luna-decisions-20261006`','OpenAI via OpenRouter Decisions API','Not published',
         '40 independent predicates × 6 regions; effort not exposed; no tools or fallback','Requested multi-label classification of writing patterns']])
    sections.append(('2. Models and controlled requests',f'''{model_table}

The four writers' CLI IDs have no immutable dated revision; returned IDs are retained. The classifier has a dated pin. Matching high effort across writers does not establish identical hidden computation. No fallback is allowed.

Every new model/article conversation begins with:

```text
Write a LinkedIn post based on the following article.

<article>
{{{{complete_article_text}}}}
</article>
```

Each of the next four turns contains only:

```text
Generate another post.
```

The follow-up adds no article, stylistic direction or request for a different angle. Models cannot see the audit inventory. The optional base instruction is `You are a helpful assistant.` Each of the 80 model/article conversations stays separate.

```mermaid
flowchart LR
    A["Article and minimal request"] --> S["GPT-6.1 Sol<br/>codex exec<br/>5 posts + usage"]
    A --> T["GPT-6.1 Terra<br/>codex exec<br/>5 posts + usage"]
    A --> O["Claude Opus 5.5<br/>claude -p<br/>5 posts + usage"]
    A --> N["Claude Sonnet 5.5<br/>claude -p<br/>5 posts + usage"]
    S --> C["Saved response caches"]
    T --> C
    O --> C
    N --> C
```

```mermaid
sequenceDiagram
    participant H as Harness
    participant M as Selected model CLI
    H->>M: New conversation, full article prompt
    M-->>H: Post 1, usage, explicit conversation ID
    loop Turns 2 to 5
        H->>M: Resume same ID: Generate another post.
        Note over H: Wait for this response before next turn
        M-->>H: New post, usage, same conversation ID
    end
```

The four model workers run independently. Each conversation's five calls are sequential, and article order uses a saved shuffle seed. The local response cache records the full request and turn; all 400 posts required new generation requests.

The four writers use only CLIs. Search, shell, browser/computer/image tools, MCP, optional skills, plugins, hooks, memories and multi-agent operation were disabled with smoke-tested controls. Init catalogues and raw events were checked; observed tool calls: zero. The classifier uses the API separately, with supplied evidence and no tools.

Each writer returned 100 distinct normalised post bodies, with no exact duplicate pair within a conversation. Distinct posts can still share phrases and structure.

Some runtime instructions cannot be removed. Claude still lists three built-in plugin inventory labels, and Codex debug output retains mandatory runtime catalogue/team/environment scaffolding despite feature disables. No repository writing rules enter the generation working directory. Thus zero observed tool use and the supported disable switches are verified, while an identical pure provider system prompt is not. [The protocol](data/PROTOCOL.md) and saved command records document that distinction.

### How the study got here

The smoke test verified new outputs and session resumes, exposed cumulative usage counters and identified assistant notes outside post bodies. Those repairs preceded the full run. Its 40 outputs remain separate from all main results; details are in [the protocol](data/PROTOCOL.md).'''))
    sections.append(('3. What counts as repeated prose','''The first analysis uses a fixed inventory of 111 vocabulary items, phrases and structure candidates, saved before the smoke generations and retained unchanged for the full run. It includes expressions such as `my takeaway`, `why this matters` and `the opportunity`, vocabulary candidates such as `delve` and `underscore`, and sentence patterns such as a negative contrast followed by a positive claim. [The inventory](data/prose_lexicon.json) gives every exact matching rule and its provenance.

The research papers in Further reading motivate counting lexical overrepresentation; they do not establish that every item is overused by these four models on LinkedIn. The repository's editorial watchlist supplies candidates, and the LinkedIn-specific expressions are stated investigator hypotheses. A match is descriptive, not automatically a defect or an AI-authorship signal. Literal technical use and useful signposting remain possible.

For each phrase the report counts posts containing it, total occurrences, occurrences per 1,000 words and distinct source topics. Counts are also separated by location: the opening sentence, opening paragraph, first 30 words, transition-start windows, non-final paragraph endings, final substantive paragraph and closing sentence. Raw responses and editorial notes have their own views. These zones overlap, so adding their counts would double-count text.

The closing is the final substantive sentence before a hashtag-only block. A literal response wrapper, such as a label announcing a LinkedIn post, is counted separately from the opening. A clearly delimited editorial note is preserved separately from the post ending. Sentence and boundary rules are deterministic heuristics. Raw responses remain available so a reader can inspect ambiguous cases rather than take the parser as a judgment of quality.

The second analysis searches all two-to-eight-word sequences. A sequence contributes to the model-signature search only on posts whose own source article does not contain it under the same tokenisation. This conservative filter prevents a product name or copied source wording from becoming a signature merely because the model repeats the news. It cannot prove the origin of a phrase or make every remaining expression distinctive.

Ten article topics were assigned to discovery and ten to confirmation before main generation. A discovered phrase needs at least five discovery posts across at least three discovery topics. It is labelled confirmed only if it also occurs in at least five confirmation posts across at least three confirmation topics. Each half contains 50 posts per model. Other observations remain exploratory. The threshold was fixed in [the preregistration](data/main/preregistration.json), not chosen to make a particular model look distinctive.

The 95% intervals use 2,000 article-bootstrap draws, keeping each article's five posts together. They describe topic variation in this sample. An all-zero bootstrap does not prove future impossibility. Held-out support is a replication threshold, not a multiple-testing-adjusted significance claim.'''))
    fmt_table=table(['Model','Bold','Emoji','Hashtags','Em dash','Closing question','Wrapper / note'],[
        [label,*[f"{feature(m,k)['posts_containing']}/100" for k in ['bold_spans','emoji_codepoints','hashtags','em_dashes','closing_question']],
         f"{feature(m,'response_preface')['posts_containing']} / {feature(m,'editorial_note')['posts_containing']}"] for m,label in zip(MODELS,NAMES)])
    sections.append(('4. Formatting across the posts',f'''The chart asks which visible choices recur across the source topics. Compare rows within each column: a high count means the feature appears in many of that model's 100 proposed posts. Numeric labels make the comparison readable without relying on colour. Wrappers and editorial notes describe the assistant response around the post, rather than formatting inside the proposed post.

![Formatting feature incidence out of 100 posts per model across 20 topics.](figures/main_formatting.png)

{fmt_table}

Closing questions appear in {', '.join(f'{label}: {feature(m,"closing_question")["posts_containing"]}/100' for m,label in zip(MODELS,NAMES))}. A question at the end is therefore a recurring choice in this workflow, rather than something the prompt required. These frequencies do not show whether readers would find the questions useful or repetitive; the study did not publish the posts or measure engagement.

The other columns separate choices that can easily get conflated. Bold markers are Markdown syntax in the returned text, not proof LinkedIn will render them as bold. Emoji counts test presence; the detailed table also retains emoji-range codepoint counts. Hashtags are separate from headings and links. An em dash is a punctuation observation, not an error. A post wrapper or source-checking note may create editing work even when the proposed post itself is usable.

The complete [per-post formatting table](data/main/formatting.csv) includes words, paragraphs, short lines, blank lines, Markdown bullets, numbered items, emoji-prefixed lines, headings, links and punctuation. Emoji-prefixed lines are recorded separately rather than automatically called list items. [The summary table](data/main/formatting_summary.csv) includes article-bootstrap intervals. These quantities let a reader distinguish repeated layout from repeated wording, and inspect whether a high average is spread across topics or concentrated in a few conversations.'''))
    fixed_focus=['my_takeaway','the_opportunity','isnt_x_its_y','not_just_x','why_this_matters','teaser_question']
    fixed_table=table(['Fixed candidate','Sol','Terra','Opus','Sonnet'],[
        [key.replace('_',' '),*[f"{phrase(m,key)['posts_containing']}/100" for m in MODELS]] for key in fixed_focus])
    chosen=[]
    for model in MODELS:
        pool=[r for r in candidates if r['model']==model and r['status']=='confirmed' and r['zone'] in ['opening_sentence','transition_starts','closing','whole'] and int(r['words'])>=3]
        pool.sort(key=lambda r:(-int(r['posts_containing']),-int(r['words']),r['phrase']))
        selection=[]
        for row in pool:
            if any(row['phrase'] in p['phrase'] or p['phrase'] in row['phrase'] for p in selection):continue
            selection.append(row)
            if len(selection)==2:break
        chosen.extend(selection)
    candidate_table=table(['Model','Location','Source-absent phrase','Posts','Topics','Discovery / confirmation posts'],[
        [NAMES[MODELS.index(r['model'])],r['zone'],f"`{r['phrase']}`",r['posts_containing'],r['distinct_topics'],f"{r['discovery_posts']} / {r['confirmation_posts']}"] for r in chosen]) if chosen else 'No three-word-or-longer phrase passed the frozen confirmation threshold in the displayed locations.'
    sections.append(('5. Fixed prose candidates and discovered phrases',f'''The fixed-candidate chart compares the same six matching rules across models. Each bar is the percentage of 100 proposed posts containing that candidate. The black whiskers are the article-bootstrap 95% intervals defined above. The raw source-overlap counts remain in the full table; the displayed fixed counts include all occurrences and do not by themselves establish that wording originated with a model.

![Six fixed prose candidates, with post incidence and article-bootstrap intervals.](figures/main_prose.png)

{fixed_table}

For the literal phrase `my takeaway`, the observed counts are {', '.join(f'{label}: {phrase(m,"my_takeaway")["posts_containing"]}/100 across {phrase(m,"my_takeaway")["distinct_topics"]} topics' for m,label in zip(MODELS,NAMES))}. The topic counts matter because five similar endings in one conversation are weaker evidence of a general habit than the same ending recurring across unrelated articles. The matching phrase may still be useful prose; the experiment measures frequency, not an automatic quality penalty.

The negative-contrast rule is broader than an exact phrase. It flags a nearby pattern such as a statement that something is not one thing followed by a positive reframing. It is a candidate span requiring contextual review, not a grammar parser or a claim that all such contrasts are artificial. The [fixed count table](data/main/fixed_prose_counts.csv) includes zeroes, locations, word-normalised occurrence rates, source-absent denominators and the number of topics represented. [Traceable match examples](data/main/fixed_phrase_examples.csv) connect positive counts to saved post IDs.

The teaser-question candidate is near the floor: one Sol post, one Terra post and no Opus or Sonnet posts match it. This sample cannot rank the models reliably on such a rare candidate. A zero count means it was not observed under this matching rule, not that the model never writes it.

The table selects up to two prevalent confirmed phrases per model, each at least three words long, skipping nested phrases. The full search remains linked below.

{candidate_table}

Every displayed phrase meets the frozen discovery and confirmation thresholds. Totals cover all 20 topics; the final column separates the two halves. Paired source-derived occurrences are excluded. Ordinary English can pass this threshold, so recurrence does not establish an exclusive model fingerprint.

The complete search is in [phrase_candidates.csv](data/main/phrase_candidates.csv), including phrases that did not confirm. Openings, transitions, point endings and closings can be inspected separately. [Family fixed counts](data/main/family_fixed_counts.csv) show both member models alongside the two-family totals. [Shared confirmed phrases](data/main/family_shared_phrases.csv) require confirmation for each of the family's two tested models separately. A phrase common to one family member alone is not presented as shared by the family.

Family totals pool 200 posts but still represent only two tested models and the same 20 topics. They do not isolate an effect of a vendor's training choices, and CLI scaffolding remains a possible contributor. The per-model columns are retained so that a pooled family count cannot conceal a large difference between its members.'''))
    # Five ordinary, traceable examples are chosen without inventing a failure.
    examples=[]
    selections=[('An ordinary first draft','gpt-6.1-sol','14-seti',1),
                ('The same conversation asks for another angle','gpt-6.1-sol','14-seti',2),
                ('A different model sees the same science article','claude-opus-5-5','14-seti',1),
                ('A security incident changes the subject','gpt-6.1-terra','13-cursor-extension',1),
                ('A public-data announcement reaches its fifth draft','claude-sonnet-5-5','06-protostar',5),
                ('First-person writing needs an attribution check','claude-sonnet-5-5','01-kimi',2)]
    for title,model,item,turn in selections:
        r=rec(model,item,turn);z=s.zones(r['text']);features=s.formatting(r['text'])
        pid=f'{item}/{model}/{turn:02d}'
        opening=z['opening_paragraph'];closing=z['closing']
        examples.append(f'''### {title}

Case `{pid}` uses [{by_id[item]['title']}]({by_id[item]['url']}). The expected output is a new article-based draft. Its observed opening is:

{quoted(opening[:650])}

The proposed post closes with:

{quoted(closing[:450])}

Measured: {features['words']} words, {features['paragraphs']} paragraphs, {features['hashtags']} hashtags; closing question: {str(features['closing_question']).lower()}; editorial note: {str(features['editorial_note']).lower()}. [Full response](data/main/posts.md).''')
        if item=='01-kimi':
            examples[-1]+='''

This case also shows a concrete editing risk. The source is Simon Willison's report of trying the model. The prompt gives no personal history for the LinkedIn account, but the draft adopts first-person experience, including a claim about skipping benchmark tables and trying the model. Publishing that as the account owner's own experience would require verification or revision. This is an inspected attribution risk in one saved case, not an estimate of the rate of unsupported claims across all 400 posts.'''
    turn_table=rows('turn_summary.csv')
    turn_interpretation=' Mean words from turn 1 to turn 5: '+ '; '.join(
        label+' '+f"{float(next(r['mean_words'] for r in turn_table if r['model']==model and r['turn']=='1')):.1f}"+' to '+
        f"{float(next(r['mean_words'] for r in turn_table if r['model']==model and r['turn']=='5')):.1f}"
        for model,label in zip(MODELS,NAMES))+'. Each endpoint averages 20 posts.'
    sections.append(('6. Conversation turns and concrete cases','''Five posts from a conversation share an article and earlier context, but their lengths and openings can change as the person asks for another draft. The figure compares mean proposed-post length across turns. Each point averages the same 20 articles for one model; the lines connect observed means and do not imply a causal learning curve.

![Mean post word count by conversation turn for each model, with 20 posts per point.](figures/main_turns.png)

The horizontal axis is turn number, with the full article supplied only at turn 1. The vertical axis is words in the extracted proposed post, excluding a recognised wrapper or editorial note.'''+turn_interpretation+''' The plot describes which drafts a person received at each step. It does not show that asking again causes a particular length, because the model also sees its previous answers and there is no independently randomised history-control arm in the main study. [The turn table](data/main/turn_summary.csv) retains counts and formatting alongside length.

The following cases were selected to make the workflow inspectable: two consecutive Sol drafts about one science article, an Opus first draft of that same article, a different subject through Terra, and Sonnet's fifth draft of a public-data article. They illustrate the measurement boundaries and comparisons rather than being a sample of the highest or lowest quality posts. They do not replace the aggregate tables.

'''+'\n\n'.join(examples)+'''

### Errors, disagreements and boundaries

All 400 planned responses were readable, so there is no unreadable model response to invent as an error example. Readability is at the ceiling and does not rank the models' skill. A response can still contain a factual mistake, an unsuitable claim or awkward writing; no gold-post or factual adjudication was performed. The saved text is the evidence for a later quality review.

The same-article examples show different emphasis and wording; there is no adjudicated best post.

Wrappers and editorial notes are separated from proposed posts. The raw responses preserve ambiguous boundaries; [protocol history](data/PROTOCOL.md) records the parser rules and earlier amendments.'''))
    cache_table=table(['Model','All input tokens','Cache reads','New cache writes','Cached share, turns 2-5','Reported CLI dollar equivalent'],[
        [NAMES[i],f"{r['input_tokens']:,}",f"{r['cache_read_tokens']:,}",f"{r['cache_write_tokens']:,}",pct(r['cache_read_fraction_turns_2_to_5']),
         f"${r['reported_cost_usd']:.4f}" if r['reported_cost_usd'] is not None else 'Unavailable'] for i,r in enumerate(models)])
    sections.append(('7. Provider cache reuse',f'''A provider can reuse calculations for an unchanged conversation prefix while generating a new answer. That is different from this notebook's local response cache, which only replays a completed request during analysis. Every main-study response required a generation request; cached input tokens are provider-reported usage for that request.

The chart compares the first turn of each conversation with turns 2-5. It aggregates tokens before dividing, so longer requests have their actual weight. The denominator includes the full model-visible input, including prior conversation turns and CLI scaffolding, not only the three words in the follow-up message.

![Provider-reported cached-input fractions for initial turns and short follow-ups.](figures/main_cache.png)

{cache_table}

On turns 2-5, the weighted cache-read shares are {', '.join(f'{NAMES[i]}: {pct(r["cache_read_fraction_turns_2_to_5"])}' for i,r in enumerate(models))}. These are observations from this run, not guaranteed backend behaviour. An initial turn may already read a shared runtime prefix from cache, and a later turn may need to write newly added conversation history even if much of the old context is reused.

For Claude, ordinary input, cache-read input and cache-write input are disjoint and must be added to obtain total input. For Codex the input counter is already inclusive. Resumed Codex counters accumulate across the saved conversation, and Claude's reported dollar cost also accumulates. The collector retains native counters and differences them within the same conversation before aggregating. The smoke verification against native last-turn counters is retained in [counter scope checks](data/counter_scope_checks.json); main per-turn values and scopes are in [the cache ledger](data/main/provider_cache_usage.csv).

To encourage reuse, all five turns of an article/model block remain sequential, with unchanged source, optional system line, working directory, effort and tool configuration. Conversation IDs are explicitly resumed; there is no global last-conversation lookup. Article text is not resent on follow-ups, and no padding is added to reach a provider cache threshold. Different model workers run independently so an output from another model never enters the conversation.

A high read fraction is not the same as a small bill. Later turns contain earlier posts, and cache writes and generated output have their own costs. Dollar equivalents are only stated where the CLI exposes them. Runtime/provider prefix caching can also reuse material shared across articles; the counters do not isolate the article's own contribution. No causal cache-strategy comparison or routing guarantee is claimed.'''))
    sections.append(('8. Limits and practical interpretation','''The evidence supports a specific editing workflow: inspect recurring openings, transitions, point endings, closing questions and layout choices for these four models when requesting five drafts from one article-specific conversation. The saved counts identify concrete habits worth reviewing. They do not establish that a model is a better LinkedIn writer, that a recurring phrase is always undesirable, or that a reader could identify AI authorship from it.

There is no human-written LinkedIn comparison corpus, blinded editorial score, engagement outcome or independent factual answer key. A model can vary its wording while adding an unsupported claim, or reuse a phrase while accurately explaining the news. Distinct response hashes and readable-output counts address collection integrity rather than writing quality. With every model returning readable text, that success measure is at a ceiling.

The 20 topics were selected from a short AI-news window, not randomly sampled from all professional writing. They include related industry themes and several company-authored announcements. Publisher tone and source length may influence posts. Source-overlap filtering removes an important confound for exact phrases, but it cannot remove every effect of the source's framing or meaning.

The five sequential posts are conditional on earlier drafts. The phrase counts and intervals therefore keep article clusters intact. The discovery/confirmation split reduces the chance of presenting a one-topic coincidence as a broad habit, but it remains a small held-out sample and does not turn descriptive phrase mining into a validated authorship detector. Nested phrases and common function-word sequences also mean the number of confirmed candidates is not a count of independent habits.

Provider families are represented by two models each. Model versions are requested undated IDs rather than immutable weight snapshots, and mandatory CLI/runtime instructions are not identical across providers. No observed tool use was allowed, but the retained platform scaffolding limits claims about a bare model's intrinsic style. These are results for the named CLI workflows and settings.

The original source set, 111-item inventory, follow-up wording and confirmation thresholds were fixed before main generation. The 40-pattern taxonomy and 70 surface rules were added after collection. Classifier questions and thresholds were frozen before its API run, but the overall audit remains exploratory. A single decision model may favor particular voices or misapply a criterion; 996 region/whole label conflicts illustrate that limit. [The protocol](data/PROTOCOL.md) preserves the amendments. Human validation is needed before interpreting labels as reader annoyances.'''))
    known=sum(r['reported_cost_usd'] or 0 for r in models)
    sections.append(('9. Spend, saved data and reproduction',f'''The collection contains 400 generation requests and 800 classifier requests. All posts and 96,000 classifier answers were readable, with no observed writer tool calls or fallback models. Two smoke-classified posts are reused in the main classification cache, not billed twice.

The 200 Claude responses report ${known:.6f}; the classifier reports ${decision_summary['reported_cost_usd']:.6f}. Codex dollar equivalents and the actual subscription charge remain unavailable. Earlier generation smoke costs are separate, including one interrupted diagnostic with unknown final usage. [Writer finances](data/main/financial_summary.json) and [classifier usage](data/decision_audit/usage.csv) retain the native records.

The `data/main/` cache retains raw CLI streams, parsed posts, request fingerprints, IDs, settings, timing and usage. Article bodies stay local and git-ignored; committed metadata and overlap checks support replay. The added definitions and counts are in `data/expanded_audit/`.

- [Executed notebook](40_linkedin_writing_habits.ipynb), with collection and analysis helpers embedded for self-contained replay.
- [All main generated responses](data/main/posts.md), with stable article/model/turn IDs.
- [Article manifest](data/main/articles.json) and [preregistration](data/main/preregistration.json).
- [Per-post ledger](data/main/posts.csv), [cache usage](data/main/provider_cache_usage.csv) and [model summary](data/main/model_summary.csv).
- [Fixed prose counts](data/main/fixed_prose_counts.csv), [match examples](data/main/fixed_phrase_examples.csv), [phrase search](data/main/phrase_candidates.csv) and [shared family phrases](data/main/family_shared_phrases.csv).
- [Formatting](data/main/formatting.csv), [formatting summaries](data/main/formatting_summary.csv) and [turn summaries](data/main/turn_summary.csv).
- [Collector](full_study.py), [analysis](main_analysis.py), [validation](data/main/validation.json), [protocol](data/PROTOCOL.md) and [file manifest](data/MANIFEST.json).

From this folder, the ordinary reproduction path is offline:

```powershell
python -m unittest -v test_smoke_study.py test_full_study.py test_expanded_audit.py test_decision_audit.py
python main_analysis.py
python expanded_audit.py
python decision_audit.py analyse
python -m nbconvert --to notebook --execute --inplace 40_linkedin_writing_habits.ipynb
```

The notebook imports no helper from another repository folder. It embeds its own CLI wrappers and analysis functions, reads the committed response caches and derived source-overlap records, and makes no model or network call during default execution. Python, NumPy, pandas, matplotlib, nbformat and nbconvert are needed for replay; the collector also uses requests and Beautiful Soup for source acquisition. Article source hashes prevent a changed web page from silently becoming the original input.

Live collection is explicit and defaults stay small. The surface audit makes no model calls; the classifier replays its saved responses by default. Complete classifier wire bodies remain local because they contain publisher articles. Public response records retain request hashes, source/post hashes and typed answers. The classifier's transport exposed no cache counters or effort control; neither is invented as zero or high.

Default replay needs no full source files: saved overlap fingerprints are checked against the unchanged outputs and criteria. Smoke evidence stays separate.'''))
    sections.append(('10. Future work and further reading','''Links checked November 1, 2026 (Toronto local date).

### Future work

- Compare fresh sessions and continued conversations on a new, matched 20-topic sample with randomised condition order. Measure phrase recurrence and cache use separately; the current five-turn results are conditional on prior drafts.
- Add a preselected, blinded human review of factual faithfulness, clarity, specificity and readiness to publish. Measure whether the observed recurring prose and formatting change reader preferences; the current study has no quality or engagement outcome.
- Repeat on non-AI subjects and independent reporting with a larger topic sample. Measure which patterns persist outside the narrow AI-news window, since source vocabulary and company announcement tone can influence the counts.
- Test a minimal user preference such as a request to omit a recurring closing structure, while holding the source and model fixed. Measure how much the confirmed patterns change and whether factual support is preserved; the current prompt intentionally gave no stylistic guidance.

### Further reading

- [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016) (Kobak et al., 2025). Motivates frequency-based comparison while showing why a word alone is not an authorship judgment.
- [Why Does ChatGPT "Delve" So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models](https://arxiv.org/abs/2412.11385) (Juzek and Ward, 2024). Studies lexical overrepresentation in another writing setting; its results do not by themselves establish LinkedIn habits.
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) (OpenAI, accessed 2026). Explains prefix caching and usage fields, with API controls that must not be assumed to exist in Codex.
- [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (Anthropic, accessed 2026). Explains read/write counters and growing conversation prefixes, which determine the cache denominator used here.
'''))
    for i,(title,body) in enumerate(sections):
        if title.startswith('3.'):
            body+='\n\nThe [guide](data/expanded_audit/STYLE_GUIDE.md) defines 40 editorial patterns with illustrations, rewrites and exceptions, drawing on notebooks 15 and 17 and online sources. Their labels come from the Decisions API. Seventy separate surface rules are diagnostics, not the classifier. These additions are exploratory; their labels are model estimates rather than human-verified faults.'
        elif title.startswith('5.'):body+='\n\n'+audit_report_section()
        sections[i]=(title,body)
    study_summary+='\n\nThe Decisions API independently labels all 40 editorial patterns in each post and five smaller regions: 96,000 probabilities. At p ≥ 0.5, it labels unnecessary negative contrast in 85 Sol, 59 Terra, 89 Opus and 56 Sonnet posts. These are classifier estimates, with 996 region/whole disagreements and no human validation. [Definitions and examples for every pattern](data/expanded_audit/STYLE_GUIDE.md) explain the exploratory taxonomy; the original 111-item inventory remains unchanged.\n'
    readme=(intro+'\n'+study_summary+'\n'+contents+'\n'+'\n\n'.join('## '+title+'\n\n'+body for title,body in sections)).rstrip()+'\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    saved=['# Main generated responses\n\n400 responses from 80 article-specific conversations; no quality score is implied.\n']
    for r in valid:
        pid=f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}"
        saved.append(f"## {pid}\n\nSource: [{by_id[r['item_id']]['title']}]({by_id[r['item_id']]['url']}). Session: `{r['session_id']}`. Input: {r['input_total']}; cache reads: {r['cache_read_tokens']}; writes: {r['cache_write_tokens']}.\n\n"+r['text']+'\n')
    (DATA/'posts.md').write_text('\n'.join(saved),encoding='utf-8')
    notebook=nbformat.v4.new_notebook(metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
    notebook.cells=[nbformat.v4.new_markdown_cell(intro),nbformat.v4.new_markdown_cell(study_summary),nbformat.v4.new_markdown_cell(contents)]
    smoke_code=(ROOT/'smoke_study.py').read_text(encoding='utf-8').split("\nif __name__ == '__main__':")[0]
    full_code=(ROOT/'full_study.py').read_text(encoding='utf-8').split("\nif __name__=='__main__':")[0].replace('import smoke_study as s\n','')
    analysis_code=(ROOT/'main_analysis.py').read_text(encoding='utf-8').split("\nif __name__=='__main__':")[0].replace('import smoke_study as s\n','')
    expanded_code=(ROOT/'expanded_audit.py').read_text(encoding='utf-8').split("\nif __name__=='__main__':")[0].replace('import smoke_study as s\n','')
    decision_code=(ROOT/'decision_audit.py').read_text(encoding='utf-8').split("\nif __name__=='__main__':")[0].replace('import smoke_study as s\n','')
    setup=smoke_code+'''\nimport types
s=types.SimpleNamespace(**{key:value for key,value in globals().copy().items() if not key.startswith('_')})
'''+full_code+'\n'+analysis_code+'\n'+expanded_code+'\n'+decision_code
    setup+='''\n# Default replay only. Live collection is a separate, explicit CLI command.
MAX_NEW_CALLS=5
main_rows=analyse()
expanded_rows=analyse_expanded()
decision_rows=analyse_decisions()
assert all(s.load(DATA/'summary.json')['gates'].values())
'''
    for title,body in sections:
        notebook.cells.append(nbformat.v4.new_markdown_cell('## '+title+'\n\n'+body))
        if title.startswith('2.'):
            notebook.cells.append(nbformat.v4.new_markdown_cell('The next cell defines all helpers inside this notebook and replays the committed responses. It does not call a model or download an article. The small new-call setting is retained for any separately requested live collection.'))
            notebook.cells.append(nbformat.v4.new_code_cell(setup))
            notebook.cells.append(nbformat.v4.new_markdown_cell('One plotting style block below creates all five main figures from saved tables. The later numbered results sections explain what to compare in each image.'))
            notebook.cells.append(nbformat.v4.new_code_cell(PLOT_CODE))
        elif title.startswith('5.'):
            notebook.cells.append(nbformat.v4.new_code_cell("display(pd.read_csv(DATA/'fixed_prose_counts.csv').query(\"zone == 'whole' and phrase_id in ['my_takeaway','the_opportunity','isnt_x_its_y']\")[[\"model\",\"phrase_id\",\"posts_containing\",\"distinct_topics\",\"posts_containing_when_source_absent\"]])"))
            notebook.cells.append(nbformat.v4.new_markdown_cell('The displayed counts separate all observed posts from the posts whose own source lacks the expression. Different denominators answer different questions; neither is a score of writing quality.'))
        elif title.startswith('7.'):
            notebook.cells.append(nbformat.v4.new_code_cell("display(pd.DataFrame(main_rows)[['model','input_tokens','cache_read_tokens','cache_write_tokens','cache_read_fraction_turns_2_to_5','reported_cost_usd']])"))
            notebook.cells.append(nbformat.v4.new_markdown_cell('These are per-turn-corrected aggregates. Missing Codex dollar totals remain missing rather than being changed to zero. Cache shares include the input history supplied by the CLI.'))
        elif title.startswith('9.'):
            notebook.cells.append(nbformat.v4.new_code_cell("known=sum(r['reported_cost_usd'] or 0 for r in main_rows)\nprint(f'Main Claude CLI list-price equivalent: ${known:.6f}')\nprint('Decisions classifier reported cost:',s.load(DECISIONS/'summary.json')['reported_cost_usd'])\nprint('Main Codex dollar equivalent and actual total spend: unavailable.')"))
    nbformat.write(notebook,ROOT/'40_linkedin_writing_habits.ipynb')
    print('Full README bytes',len(readme.encode()),'notebook cells',len(notebook.cells))


if __name__=='__main__':main()
