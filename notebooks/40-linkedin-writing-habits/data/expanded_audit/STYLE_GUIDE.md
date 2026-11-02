# A guide to recurring AI writing patterns

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

1. [Vague abstraction](#vague-abstraction)
2. [Unnecessary jargon](#unnecessary-jargon)
3. [Empty emphasis](#empty-emphasis)
4. [Repeated conclusion](#repeated-conclusion)
5. [Padded construction](#padded-construction)
6. [Formulaic framing](#formulaic-framing)
7. [Stacked hedges](#stacked-hedges)
8. [Unclear reference](#unclear-reference)
9. [Repeated prestige vocabulary](#stock-vocabulary)
10. [Unnecessary negative contrast](#negative-contrast)
11. [Automatic not-just expansion](#additive-contrast)
12. [Mechanical groups of three](#triad)
13. [Trailing significance clause](#significance-tail)
14. [Inflated forms of is or has](#inflated-copula)
15. [Question-and-answer pivot](#question-pivot)
16. [Throat clearing and signposting](#throat-clearing)
17. [Vague attribution](#vague-attribution)
18. [Generic scene-setting opener](#generic-opener)
19. [Generic engagement close](#engagement-close)
20. [Formulaic challenges and future ending](#formulaic-future)
21. [Announcing honesty](#honesty-label)
22. [Demonstrative payoff sentence](#payoff)
23. [Presupposed objection](#fake-objection)
24. [Unexplained analyst metaphor](#analyst-metaphor)
25. [Staged reflection or discovery](#reflective-pose)
26. [Decorative or false range](#false-range)
27. [Noun-heavy wording](#nominalization)
28. [Repeated participial clauses](#participial-clause)
29. [Repeated clipped rhythm](#clipped-rhythm)
30. [Repeated bold emphasis](#bold-density)
31. [Bold labels on every list item](#bold-leadins)
32. [Emoji as repeated layout markers](#emoji-layout)
33. [Title case and heading templates](#title-case)
34. [Mechanical one-sentence paragraphs](#single-sentence-paragraphs)
35. [Chatbot or markup residue](#markup-residue)
36. [Unsupported first-person experience](#invented-experience)
37. [Generic benefit language](#generic-benefit)
38. [Uniform sentence and paragraph rhythm](#uniform-rhythm)
39. [Repeated punctuation for emphasis](#punctuation-tics)
40. [Automatic hashtag tail](#hashtag-tail)

[All 70 counting rules](#all-70-counting-rules) · [Sources and evidence strength](#sources-and-evidence-strength) · [Reproduce](#reproduce)


<a id="vague-abstraction"></a>

## 1. Vague abstraction

**Definition.** An abstract claim omits the actor, action or comparison a reader needs.

**Why review it?** The sentence sounds purposeful while leaving the practical change unclear.

**Illustration.** This creates a new paradigm for enterprise value.

**Clearer alternative.** The tool checks invoices against purchase orders before payment.

**When it can help.** An abstract summary can help after the concrete mechanism is explained.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 3 (0) | 2 (0) | 18 (0) | 9 (0) |

**What is counted.** `vague_connection`: An association is described as close, deep or strong; specificity must be checked in context.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Vague-connection cue | 0/100 | 0/100 | 1/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `17-orbital-compute/claude-opus-5-5/05`, first saved positive example in deterministic order:

> arlier rockets. alphabet also holds a significant stake in spacex, so the two visions are closely linked.
>
> **bet #3: alphabet keeps funding the long game.**
> suncatcher is designed to be economical in the 2030s. meanwhile, alphabet's s

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="unnecessary-jargon"></a>

## 2. Unnecessary jargon

**Definition.** Specialist or corporate wording adds decoding work without needed precision.

**Why review it?** Readers must translate the terminology before they can judge the claim.

**Illustration.** Operationalize a synergistic inference enablement layer.

**Clearer alternative.** Let the support team run the model inside its ticketing system.

**When it can help.** A technical term is useful when the audience needs its exact meaning.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 1 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="empty-emphasis"></a>

## 3. Empty emphasis

**Definition.** Importance, novelty or certainty is asserted without supporting evidence.

**Why review it?** The adjective supplies enthusiasm in place of a checkable comparison.

**Illustration.** An incredibly revolutionary breakthrough for every business.

**Clearer alternative.** In the reported test, median response time fell from four seconds to two.

**When it can help.** A strong claim can be justified by a named comparison and evidence.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension), [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 8 (1) | 3 (0) |

**What is counted.** `importance_copula`: An is/are statement calls its subject key, crucial or essential.; `broader_trend`: A cue places an event in a broader movement or calls it a significant shift or turning point.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Is key / crucial / essential | 1/100 | 0/100 | 0/100 | 0/100 |
| Broader trend cue | 1/100 | 1/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `06-protostar/gpt-6.1-terra/05`, first saved positive example in deterministic order:

> ber 2–13, the challenge also asks teams to propose a climate adaptation policy idea. it's part of a broader effort to make publicly funded scientific data, models, and code easier to discover and reuse.
>
> better access creates opportuniti

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="repeated-conclusion"></a>

## 4. Repeated conclusion

**Definition.** A point is restated without new evidence or a useful role in the format.

**Why review it?** The reader spends time rereading a proposition instead of learning its implication.

**Illustration.** The service costs less. In short, it is cheaper. The takeaway is lower cost.

**Clearer alternative.** The service costs less, but the quoted price excludes storage.

**When it can help.** A summary can help in a long report, a slide deck or an accessibility context.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 3 (1) | 0 (0) | 16 (1) | 4 (1) |

**What is counted.** `ultimately`: A conventional summary transition appears; whether it repeats a conclusion is not judged.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Ultimately / all in all | 1/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `04-nemotron-speech/gpt-6.1-sol/05`, first saved positive example in deterministic order:

> accuracy requirements
> → hardware footprint and cost per audio hour
>
> the best benchmark is ultimately the workload you need to run.
>
> #speechai #aiinfrastructure #enterpriseai

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="padded-construction"></a>

## 5. Padded construction

**Definition.** Extra scaffolding delays a proposition that could be stated directly.

**Why review it?** The sentence spends words announcing its job before doing it.

**Illustration.** It is important to note that there is a need for an evaluation of the results.

**Clearer alternative.** Evaluate the results.

**When it can help.** Framing may be needed to distinguish a recommendation from an observed fact.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 1 (0) | 1 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="formulaic-framing"></a>

## 6. Formulaic framing

**Definition.** A stock opener, contrast or slogan contributes little to this particular point.

**Why review it?** The same frame can surround unrelated news without changing its wording.

**Illustration.** The future is here, and the possibilities are endless.

**Clearer alternative.** The release adds offline transcription in six languages.

**When it can help.** A familiar structure can orient readers if the content makes it specific.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 14 (1) | 13 (3) | 64 (25) | 46 (13) |

**What is counted.** `canned_insight`: An introductory cue claims to reveal a truth, reality, essence or bigger point.; `good_news`: A familiar transition reassures the reader or announces good news.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Canned insight cue | 0/100 | 0/100 | 0/100 | 0/100 |
| Canned reassurance cue | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="stacked-hedges"></a>

## 7. Stacked hedges

**Definition.** Several uncertainty markers qualify the same claim redundantly.

**Why review it?** The reader cannot tell whether the doubt comes from weak evidence or verbal caution.

**Illustration.** This may potentially perhaps reduce errors.

**Clearer alternative.** It may reduce errors; the company has not published a controlled test.

**When it can help.** Different qualifiers can express different uncertainties, so inspect their scope.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="unclear-reference"></a>

## 8. Unclear reference

**Definition.** The reader cannot recover an actor, pronoun, comparison or logical link.

**Why review it?** A grammatical sentence can still leave the reader unsure what caused what.

**Illustration.** The vendor told the customer its model failed, which changed their plan.

**Clearer alternative.** The vendor said its own model failed. The customer then delayed deployment.

**When it can help.** A pronoun is concise when its referent is clear from the surrounding text.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="stock-vocabulary"></a>

## 9. Repeated prestige vocabulary

**Definition.** A small vocabulary of impressive-sounding words recurs across unrelated subjects.

**Why review it?** Repeated diction can make separate posts sound interchangeable. Frequency alone is not a fault.

**Illustration.** Delve into this intricate tapestry of transformative innovation.

**Clearer alternative.** The article explains how the new search index handles updates.

**When it can help.** Literal or precise use is fine. A model habit requires counts across several topics.

**Basis.** [JW: Why Does ChatGPT "Delve" So Much?](https://aclanthology.org/2025.coling-main.426/), [K: Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016v5), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**What is counted.** `jw_delves`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_delved`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_delving`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_showcasing`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_delve`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_boasts`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_underscores`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_comprehending`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_intricacies`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_surpassing`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_intricate`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_underscoring`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_garnered`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_showcases`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_emphasizing`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_underscore`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_realm`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_surpasses`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_groundbreaking`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_advancements`: Exact word form from Appendix A; no stemming or semantic judgment.; `jw_aligns`: Exact word form from Appendix A; no stemming or semantic judgment.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| delves | 0/100 | 0/100 | 0/100 | 0/100 |
| delved | 0/100 | 0/100 | 0/100 | 0/100 |
| delving | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. Only the first three rules are displayed here; the complete table below includes the others. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `02-tb-screening/claude-sonnet-5-5/03`, first saved positive example in deterministic order:

> 's what makes this possible:
>
> 🔹 **medsiglip** is a lightweight vision-language model that aligns medical images with clinical language. you can classify or search images with plain-language labels, or fine-tune it on a small s

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="negative-contrast"></a>

## 10. Unnecessary negative contrast

**Definition.** A claim is framed by denying an alternative that the reader may never have proposed.

**Why review it?** The denial adds a dramatic turn and may set up a false choice.

**Illustration.** This isn't a product launch. It's a revolution.

**Clearer alternative.** The launch adds a model marketplace to the existing product.

**When it can help.** A contrast is useful when correcting an actual misunderstanding.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 85 (49) | 59 (29) | 89 (56) | 56 (35) |

**What is counted.** `less_more`: A sentence contrasts less about one thing with more about another within a bounded span.; `appositive_not`: A comma is followed by not and a short phrase; the negation may be useful or factually necessary.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Less about / more about | 0/100 | 4/100 | 0/100 | 1/100 |
| Comma followed by not | 16/100 | 9/100 | 36/100 | 40/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/claude-sonnet-5-5/03`, first saved positive example in deterministic order:

> h your current vendors
>
> **3. but don't skip the homework**
> benchmarks are a starting point, not a verdict. before you switch anything, i'd do the following:
> - run the model on your own prompts and your own evals
> - compare cost at your

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="additive-contrast"></a>

## 11. Automatic not-just expansion

**Definition.** A simple additional fact is presented as a correction or escalation.

**Why review it?** Repeated expansion makes ordinary additions sound like revelations.

**Illustration.** It doesn't just summarize meetings; it transforms collaboration.

**Clearer alternative.** It summarizes meetings and assigns action items to attendees.

**When it can help.** The form can clarify a real limitation in what readers already expect.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 47 (17) | 30 (14) | 53 (25) | 43 (15) |

**What is counted.** `more_than_just`: The exact expansion phrase more than just.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| More than just | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="triad"></a>

## 12. Mechanical groups of three

**Definition.** Lists or parallel phrases repeatedly use three items regardless of the evidence.

**Why review it?** A pleasing rhythm can encourage generic additions that do not add information.

**Illustration.** Smarter. Faster. Better.

**Clearer alternative.** The reported test completed in two seconds and used half as much memory.

**When it can help.** Three real findings deserve three items. A triad count cannot decide usefulness.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 4 (0) | 3 (0) | 22 (8) | 9 (3) |

**What is counted.** `triad_candidate`: Matches three short lexical spans; does not establish three parallel grammatical items.; `three_item_lists`: Contiguous marked list runs containing exactly three lines.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Three short comma-separated spans | 74/100 | 73/100 | 78/100 | 81/100 |
| Exactly three-item list blocks | 18/100 | 7/100 | 32/100 | 32/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/claude-opus-5-5/01`, first saved positive example in deterministic order:

> *benchmarks:** artificial analysis scored it **55**. that puts it ahead of claude fable 5.1, gpt-6 astra, and gemini 4 argon (all 53) and behind only claude opus 5.5 (58). moonshot's own benchmarks put it roughly level with opus 5.5 and gpt-6 astra, winn

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="significance-tail"></a>

## 13. Trailing significance clause

**Definition.** A sentence ends with a participle that announces the importance of the preceding fact.

**Why review it?** The tail can substitute an interpretation for evidence supporting that interpretation.

**Illustration.** The company added a dashboard, underscoring its commitment to innovation.

**Clearer alternative.** The company added a dashboard showing request costs by team.

**When it can help.** A trailing clause is useful when it states a specific, supported consequence.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="inflated-copula"></a>

## 14. Inflated forms of is or has

**Definition.** A plain relation is replaced by a ceremonial verb phrase.

**Why review it?** The additional wording can imply significance that the relation itself does not carry.

**Illustration.** The release stands as a testament to the team's vision.

**Clearer alternative.** The release includes the first version of the team's speech model.

**When it can help.** Serves as is accurate when something has a particular function or role.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="question-pivot"></a>

## 15. Question-and-answer pivot

**Definition.** The writer asks a short question and immediately supplies the answer.

**Why review it?** Used repeatedly, the device manufactures suspense and interrupts the argument.

**Illustration.** The catch? You still need to check the output.

**Clearer alternative.** You still need to check the output.

**When it can help.** A question can help when it is the reader's real question and needs explanation.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 17 (12) | 8 (6) | 17 (9) | 5 (3) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="throat-clearing"></a>

## 16. Throat clearing and signposting

**Definition.** Text announces the next statement instead of stating it.

**Why review it?** The opening or transition becomes longer without adding the promised content.

**Illustration.** It's worth noting that the model runs locally.

**Clearer alternative.** The model runs locally.

**When it can help.** Signposts help in a long document when they identify a meaningful change of topic.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 1 (0) | 0 (0) | 10 (2) | 11 (0) |

**What is counted.** `rhetorical_label`: A colon-ended label announces the kind of statement about to follow.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Rhetorical label | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="vague-attribution"></a>

## 17. Vague attribution

**Definition.** An opinion or finding is assigned to unnamed authorities.

**Why review it?** The reader cannot check the evidence or distinguish consensus from one opinion.

**Illustration.** Experts agree that AI agents will replace most software.

**Clearer alternative.** The article quotes one analyst who expects agents to change software purchasing.

**When it can help.** A collective attribution is useful when its membership and evidence are supplied.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**What is counted.** `named_authority_absent`: A fixed expression invokes unnamed experts, observers or shared belief; a name elsewhere may resolve it.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Unnamed authority cue | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="generic-opener"></a>

## 18. Generic scene-setting opener

**Definition.** The first sentence describes a broad era or trend rather than this event.

**Why review it?** Many unrelated posts could begin with the same line, delaying the news.

**Illustration.** In today's rapidly evolving digital world, innovation never stops.

**Clearer alternative.** The lab released its speech model on Tuesday.

**When it can help.** Background can be needed when the intended reader does not know the subject.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 1 (1) | 5 (2) | 0 (0) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="engagement-close"></a>

## 19. Generic engagement close

**Definition.** A post ends by soliciting reactions without a specific question grounded in its argument.

**Why review it?** The request can feel attached to the post solely to collect comments.

**Illustration.** Thoughts? Agree or disagree? Let me know below.

**Clearer alternative.** Which of these checks would your team require before giving an agent payment access?

**When it can help.** A focused question can invite useful knowledge that the article does not answer.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [H: Fixing AI LinkedIn Posts That Scream ChatGPT, Iris Vandermeer](https://humanizedcopy.com/posts/fixing-ai-linkedin-posts-that-scream-chatgpt). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 3 (2) | 41 (31) | 41 (33) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="formulaic-future"></a>

## 20. Formulaic challenges and future ending

**Definition.** An ending acknowledges obstacles, then predicts a promising future without specifying either.

**Why review it?** The apparent balance can leave the reader without a decision or unresolved question.

**Illustration.** Despite the challenges, the future looks bright as innovation continues.

**Clearer alternative.** The service still lacks an audit log; the vendor has not announced a release date.

**When it can help.** Concrete limitations and dated plans are useful, even when placed at the end.

**Basis.** [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 3 (2) | 0 (0) |

**What is counted.** `challenges_close`: A bounded despite-these/the/its-challenges formula; a concrete obstacle can still be useful.; `future_outlook`: A future-outlook/prospects label or a claim that the future looks bright or promising.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Despite-challenges phrase | 0/100 | 0/100 | 0/100 | 0/100 |
| Future-outlook label | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="honesty-label"></a>

## 21. Announcing honesty

**Definition.** The writer labels a statement as honest, candid or real rather than supporting it.

**Why review it?** A sincerity cue can become a repeated substitute for explaining the evidence.

**Illustration.** Let's be honest: this changes everything.

**Clearer alternative.** The price change would cut this example workload's bill from $40 to $25.

**When it can help.** A candid statement can be appropriate in a personal account; the cue is not proof of insincerity.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 6 (5) | 5 (3) |

**What is counted.** `honesty_cue`: The writer explicitly labels the statement as honest or candid.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Honesty cue | 1/100 | 0/100 | 3/100 | 1/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `07-apple-local-models/claude-opus-5-5/04`, first saved positive example in deterministic order:

> said it, so you get a transcript organized by speaker turn.
>
> the benchmarks are reported honestly, with caveats:
> • parakeet unified scored 1.43% word error rate on librispeech test-clean, vs. 2.12% for apple's transcriber.
> • an

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="payoff"></a>

## 22. Demonstrative payoff sentence

**Definition.** A paragraph ends with a short this or that sentence that labels its significance.

**Why review it?** Repeated payoffs can make the conclusion sound prewritten.

**Illustration.** That's the unlock.

**Clearer alternative.** The change lets customers export their logs without a support request.

**When it can help.** A short reference can tie together a genuinely complex preceding explanation.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 4 (2) | 1 (1) | 2 (0) | 0 (0) |

**What is counted.** `demonstrative_payoff`: A this/that cue introduces a why/where explanation or labels an unlock, shift, point or lesson.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| That's why / where / the | 7/100 | 6/100 | 8/100 | 6/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `02-tb-screening/gpt-6.1-terra/05`, first saved positive example in deterministic order:

> list review. but that speed only helps if the technology reaches the people who need it.
>
> that's why the collaboration between google research and nexus ai stands out. their work has moved from research into clinics and even four

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="fake-objection"></a>

## 23. Presupposed objection

**Definition.** The writer introduces an imagined reader objection and immediately defeats it.

**Why review it?** It can make an unsupported assumption about what the reader believes.

**Illustration.** You might think this is just another chatbot, but hear me out.

**Clearer alternative.** Unlike the previous version, this system can schedule a meeting after confirmation.

**When it can help.** Address an objection when readers have actually raised it or the evidence warrants it.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 1 (0) | 0 (0) | 1 (0) | 0 (0) |

**What is counted.** `fake_objection`: A cue imagines what the reader thinks or asks them to hear the writer out; it may address a real objection.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Imagined objection cue | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="analyst-metaphor"></a>

## 24. Unexplained analyst metaphor

**Definition.** A figurative word makes a point sound structural, hidden or profound without clarifying it.

**Why review it?** The metaphor can replace the mechanism the reader needs to understand.

**Illustration.** This is the load-bearing shift quietly rewriting the physics of work.

**Clearer alternative.** The update lets the agent approve refunds up to a preset limit.

**When it can help.** Literal uses and metaphors with a precise, explained mapping can help.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide), [C: Claudisms](https://claudisms.ai/). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 1 (0) | 1 (0) | 12 (6) | 3 (1) |

**What is counted.** `quietly`: The adverbs quietly and silently; literal and figurative uses are both counted.; `load_bearing`: The literal expression load-bearing, with a space or hyphen; metaphor requires inspection.; `does_real_work`: A claim that a distinction or other subject does real work, without judging whether the work is explained.; `physics_metaphor`: A fixed physics phrase; the rule cannot distinguish literal science from a grand metaphor.; `lives_in`: The expression lives in or lives at; physical residence and abstract placement are both matched.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Quietly or silently | 5/100 | 4/100 | 12/100 | 5/100 |
| Load-bearing | 0/100 | 0/100 | 0/100 | 0/100 |
| Does real work | 0/100 | 0/100 | 1/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. Only the first three rules are displayed here; the complete table below includes the others. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `03-gemini-carbon/claude-opus-5-5/04`, first saved positive example in deterministic order:

> l cheating on terminal-bench 4.0 went to 0.0%. no more "all tests pass" because the agent quietly rewrote the tests.
>
> **it respects scope.**
> overreach dropped 26%. under-delivery dropped 29%. it does what you asked, all of what

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="reflective-pose"></a>

## 25. Staged reflection or discovery

**Definition.** The writer narrates an insight as a thought that keeps returning or an unexpected discovery.

**Why review it?** The autobiographical frame can add drama without adding evidence.

**Illustration.** The question I keep coming back to changed how I see everything.

**Clearer alternative.** The unresolved question is who is liable when the agent issues a refund.

**When it can help.** A true account of reflection is appropriate when the author supplies it.

**Basis.** [C: Claudisms](https://claudisms.ai/). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 12 (9) | 6 (6) |

**What is counted.** `reflective_pose`: A fixed phrase frames a thought as worth contemplation or an idea the writer has arrived at.; `coming_back`: The writer describes returning to a thought; literal movement is also matched.; `recurring_question`: A question is framed as repeatedly arising or occupying the writer.; `discovery_arc`: A first-person setup says the writer did not plan, intend or expect the discovery.; `false_singularity`: A personal-superlative cue selects the most surprising or memorable item; a justified ranking is also matched.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Reflective pose phrase | 0/100 | 0/100 | 1/100 | 1/100 |
| Coming back to | 0/100 | 0/100 | 4/100 | 1/100 |
| Recurring-question frame | 0/100 | 0/100 | 0/100 | 1/100 |

These are descriptions of the saved posts, not counts of justified faults. Only the first three rules are displayed here; the complete table below includes the others. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `03-gemini-carbon/claude-opus-5-5/04`, first saved positive example in deterministic order:

> last point might be the most underrated. anyone who has handed a task to an ai agent and come back to find it refactored three unrelated files knows the pain.
>
> **availability:** carbon is going to cyber defenders first, then to tru

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="false-range"></a>

## 26. Decorative or false range

**Definition.** A from-to construction implies a useful spectrum whose endpoints may not share one scale.

**Why review it?** The wording suggests breadth while obscuring which cases are actually covered.

**Illustration.** From productivity to possibility, the platform does it all.

**Clearer alternative.** The platform transcribes calls and drafts follow-up emails.

**When it can help.** A real range, such as prices from $5 to $20, is informative.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**What is counted.** `from_to`: Finds a range-shaped span; real numeric and temporal ranges are also matched.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| From-to span | 11/100 | 17/100 | 19/100 | 19/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/gpt-6.1-sol/01`, first saved positive example in deterministic order:

> e shortlist. real workloads determine whether it stays there.
>
> what would make you switch from a hosted proprietary model to an open-weight alternative: performance, cost, or control?
>
> #ai #openweights #llm

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="nominalization"></a>

## 27. Noun-heavy wording

**Definition.** Actions are packaged as abstract nouns, sometimes hiding who acts.

**Why review it?** A dense string of process nouns makes the reader reconstruct the actors and verbs.

**Illustration.** The implementation of the evaluation of deployment readiness is required.

**Clearer alternative.** The team must check whether the model is ready to deploy.

**When it can help.** Terms such as calibration name useful concepts. A noun suffix does not establish a noun or a defect.

**Basis.** [R: Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107v2), [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 17 (3) | 7 (0) | 29 (5) | 19 (2) |

**What is counted.** `nominal_suffix`: Counts suffix-bearing tokens, including false positives; no part-of-speech tagging.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Tokens ending in -tion/-sion/-ment/-ness/-ity | 100/100 | 99/100 | 99/100 | 100/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/claude-opus-5-5/01`, first saved positive example in deterministic order:

> -host, fine-tune, and audit a model that competes with the best proprietary systems, at a fraction of the cost.
>
> would a near-frontier open model change how your team chooses between building on apis and self-hosting? 👇
>
> #ai #ll

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="participial-clause"></a>

## 28. Repeated participial clauses

**Definition.** Sentences repeatedly add -ing clauses to compress actions or descriptions.

**Why review it?** Compression can blur timing, actors or causation. This is broader than a significance tail.

**Illustration.** The agent reads the ticket, generating a reply, routing the case, reducing effort.

**Clearer alternative.** The agent reads the ticket and drafts a reply. A person decides where to route it.

**When it can help.** A participial clause is useful when the actor and relationship are clear.

**Basis.** [R: Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107v2). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 1 (0) | 1 (1) | 35 (10) | 28 (4) |

**What is counted.** `comma_ing`: Counts an immediately post-comma -ing word, not all participial clauses.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Comma followed by an -ing word | 39/100 | 41/100 | 43/100 | 40/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/claude-opus-5-5/01`, first saved positive example in deterministic order:

> pus 5.5 (58). moonshot's own benchmarks put it roughly level with opus 5.5 and gpt-6 astra, winning some tests and coming close on others.
>
> 💰 **pricing:** $2 per million input tokens and $10 per million output. that matches gpt-6

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="clipped-rhythm"></a>

## 29. Repeated clipped rhythm

**Definition.** Several short sentences or fragments appear consecutively for emphasis.

**Why review it?** A constant staccato rhythm can make ordinary details sound artificially dramatic.

**Illustration.** No forms. No friction. Just results.

**Clearer alternative.** The tool fills in the form using the customer record.

**When it can help.** One short sentence can emphasize an important fact; fragments can suit some voices.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 49 (31) | 14 (9) | 67 (45) | 46 (26) |

**What is counted.** `short_sentence_run3`: Maximal runs of at least three consecutive sentences, each one to six words.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Runs of at least three short sentences | 7/100 | 1/100 | 19/100 | 4/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="bold-density"></a>

## 30. Repeated bold emphasis

**Definition.** A post repeatedly applies bold markers to selected phrases.

**Why review it?** When many phrases compete for emphasis, it becomes harder to see the main point.

**Illustration.** **This launch** changes **everything** about **how we work**.

**Clearer alternative.** This launch adds two features: local search and a shared audit log.

**When it can help.** A heading or one key figure can benefit from emphasis. LinkedIn may display literal Markdown markers.

**Basis.** [WS: Wikipedia: Signs of AI writing/Style](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing/Style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 4 (3) | 3 (2) | 74 (67) | 69 (60) |

**What is counted.** `bold_spans`: Number of **...** or __...__ spans.; `bold_word_share`: Bold-span words divided by all post words.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Bold spans | 73/100 | 60/100 | 91/100 | 98/100 |
| Share of words inside bold spans (mean share) | 6.3% | 4.1% | 9.2% | 10.4% |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="bold-leadins"></a>

## 31. Bold labels on every list item

**Definition.** List entries repeatedly begin with a bold label and a colon.

**Why review it?** A template can impose categories that do not help explain the substance.

**Illustration.** - **Impact:** A big change. / - **Future:** More innovation.

**Clearer alternative.** The price falls by 20%. The free tier still excludes private data.

**When it can help.** Consistent labels are useful when comparing genuinely parallel attributes.

**Basis.** [WS: Wikipedia: Signs of AI writing/Style](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing/Style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 4 (3) | 6 (6) | 42 (38) | 46 (41) |

**What is counted.** `bold_leadins`: Lines with a list marker or emoji, then a bold label and a colon.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Bold list labels | 1/100 | 4/100 | 16/100 | 12/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="emoji-layout"></a>

## 32. Emoji as repeated layout markers

**Definition.** Emoji introduce many lines, headings or bullet-like statements.

**Why review it?** Decoration can become the organizing device even when ordinary structure would be clearer.

**Illustration.** 🚀 Big launch / 💡 Huge insight / 🔥 Massive opportunity

**Clearer alternative.** The release adds shared workspaces and a usage dashboard.

**When it can help.** Emoji may fit an author's voice or aid scanning. Their presence is not inherently poor writing.

**Basis.** [WS: Wikipedia: Signs of AI writing/Style](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing/Style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 2 (2) | 11 (9) | 89 (87) | 64 (63) |

**What is counted.** `emoji_prefixed_lines`: Lines beginning with a code point in the documented emoji ranges.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Emoji-prefixed lines | 2/100 | 12/100 | 74/100 | 57/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="title-case"></a>

## 33. Title case and heading templates

**Definition.** Short posts use formal, capitalized section headings or repeat the same heading scheme.

**Why review it?** The post can read like an outline rather than a developed point.

**Illustration.** ## The Future Of Intelligent Enterprise Transformation

**Clearer alternative.** What changes for support teams

**When it can help.** Headings help in long or complex posts and may follow a publication's house style.

**Basis.** [WS: Wikipedia: Signs of AI writing/Style](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing/Style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 2 (1) | 6 (4) |

**What is counted.** `headings`: Lines beginning with one to six # signs and a space.; `title_case_headings`: Headings with at least three alphabetic words, all non-stopwords beginning uppercase.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Markdown headings | 0/100 | 0/100 | 0/100 | 0/100 |
| Title-case Markdown headings | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="single-sentence-paragraphs"></a>

## 34. Mechanical one-sentence paragraphs

**Definition.** Most paragraphs contain one sentence, repeatedly separated by blank lines.

**Why review it?** Every sentence gets similar visual weight, which can interrupt connected reasoning.

**Illustration.** The model is faster. /  / The price is lower. /  / The stakes are high.

**Clearer alternative.** The model is faster and costs less, but the article does not test its error rate.

**When it can help.** Short paragraphs can improve mobile reading. Density and runs are descriptive, not quality thresholds.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [H: Fixing AI LinkedIn Posts That Scream ChatGPT, Iris Vandermeer](https://humanizedcopy.com/posts/fixing-ai-linkedin-posts-that-scream-chatgpt). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 97 (88) | 82 (52) | 96 (80) | 96 (78) |

**What is counted.** `single_sentence_paragraph_share`: Share of substantive, non-list paragraphs split into one sentence.; `single_sentence_run3`: Maximal runs of at least three one-sentence substantive non-list paragraphs.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| One-sentence paragraph share (mean share) | 68.2% | 52.9% | 49.5% | 47.4% |
| Runs of at least three one-sentence paragraphs | 70/100 | 20/100 | 39/100 | 24/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="markup-residue"></a>

## 35. Chatbot or markup residue

**Definition.** The response includes assistant-facing commentary, placeholders or formatting artifacts instead of only the finished post.

**Why review it?** The draft can require cleanup or accidentally publish process instructions.

**Illustration.** Certainly! Here is your post: [Insert personal story here].

**Clearer alternative.** Start with the supported news; add a personal story only when the author provides one.

**When it can help.** An explicit placeholder may be useful in a requested template, and an editorial note can prevent an error.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [W: Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 8 (8) | 6 (6) |

**What is counted.** `assistant_residue`: A fixed assistant-facing introduction, helpfulness closing or AI/cutoff self-reference appears.; `horizontal_rules`: Lines containing at least three identical -, * or _ characters.; `code_fences`: Lines beginning with three backticks.; `placeholder`: Bracketed insert/add/your-text placeholders.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Assistant residue cue | 0/100 | 0/100 | 0/100 | 0/100 |
| Horizontal rules | 0/100 | 0/100 | 10/100 | 6/100 |
| Code fences | 0/100 | 0/100 | 1/100 | 4/100 |
| Placeholders | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="invented-experience"></a>

## 36. Unsupported first-person experience

**Definition.** The draft gives the poster a personal experience, observation or emotion that the supplied material does not establish.

**Why review it?** A ready-to-publish draft may put an invented claim in the author's voice.

**Illustration.** I spent last week testing this system with my team.

**Clearer alternative.** The article reports a week-long test by the vendor's team.

**When it can help.** First-person judgment is different from biography. An author-supplied experience is valid.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style), [N17: Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 20 (17) | 3 (3) | 51 (45) | 51 (42) |

**What is counted.** `experience_cue`: Finds a small set of first-person verbs; unsupported experience requires comparison with the article.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| First-person experience cue | 1/100 | 0/100 | 5/100 | 4/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

**Measured excerpt, not the teaching example.** `01-kimi/claude-sonnet-5-5/01`, first saved positive example in deterministic order:

> 's 2-3x faster at twice the price, with cache hits priced the same.
>
> **the pelican test**
> i tried it through moonshot's api with the `llm openai endpoint` command, asking it for an svg of a pelican riding a bicycle. i ran it at

Case and punctuation are normalized for matching; the full raw response is in [the saved posts](../main/posts.md). This match has not been judged a defect.


<a id="generic-benefit"></a>

## 37. Generic benefit language

**Definition.** A product benefit is described without saying what task changes or for whom.

**Why review it?** Readers cannot connect the promise to a concrete use or limitation.

**Illustration.** It does the heavy lifting so you can focus on what matters.

**Clearer alternative.** It matches receipts to card transactions; you review unmatched items.

**When it can help.** A short slogan can accompany a specific explanation, especially in advertising.

**Basis.** [T: Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 1 (0) | 1 (0) |

**What is counted.** `generic_benefit_phrase`: A benefit is expressed through a fixed effort, clarity, friction, momentum or alignment slogan.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Generic benefit phrase | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="uniform-rhythm"></a>

## 38. Uniform sentence and paragraph rhythm

**Definition.** Successive sentences or paragraphs repeatedly have the same length or internal template.

**Why review it?** A predictable cadence can make distinct points feel interchangeable. There is no universal ideal length.

**Illustration.** A post gives every point one claim, one example and one recap, even when the example adds nothing.

**Clearer alternative.** Give a complex point the explanation it needs; let a simple fact occupy one sentence.

**When it can help.** Parallel structure can help readers compare genuinely similar cases.

**Basis.** [G: How To Write Without Sounding Like AI, George Kao](https://georgekao.substack.com/p/how-to-write-without-sounding-like). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 11 (0) | 4 (1) |

**Surface diagnostic.** No regex rule is assigned to this contextual criterion. Its labels above come only from the Decisions API.


<a id="punctuation-tics"></a>

## 39. Repeated punctuation for emphasis

**Definition.** One punctuation device repeatedly supplies pauses, suspense or excitement.

**Why review it?** Habitual dashes, ellipses or exclamation marks can give every sentence the same emotional weight.

**Illustration.** A new model! A new era! An entirely new way to work!

**Clearer alternative.** The model adds image input. The article does not report a comparison with the earlier version.

**When it can help.** Punctuation can convey a real relationship or fit an author's voice. Count it without treating it as proof of AI authorship.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 0 (0) | 0 (0) | 1 (1) | 0 (0) |

**What is counted.** `em_dashes`: Literal em dash characters in the proposed post.; `exclamations`: Literal exclamation marks in the proposed post.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Em dashes | 92/100 | 74/100 | 2/100 | 0/100 |
| Exclamation marks | 0/100 | 0/100 | 0/100 | 0/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


<a id="hashtag-tail"></a>

## 40. Automatic hashtag tail

**Definition.** Every post ends with a block of generic topic labels.

**Why review it?** The ending may look templated, especially when tags repeat across unrelated articles.

**Illustration.** #AI #Innovation #FutureOfWork #Leadership

**Clearer alternative.** Use only tags that serve the intended audience, or end after the last useful sentence.

**When it can help.** A relevant tag can help organize a series or address a particular community.

**Basis.** [N15: Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style). The definition and editing explanation here are the study author's operational interpretation.

**Decisions API classification of saved posts.** Each cell is model-labelled present at p ≥ 0.5, followed by the count at p ≥ 0.8 in parentheses. Denominator: 100 readable whole-post judgments per writer.

| Sol | Terra | Opus | Sonnet |
|---|---|---|---|
| 84 (81) | 100 (100) | 100 (99) | 100 (99) |

**What is counted.** `hashtags`: Hash-prefixed word tokens; headings with # plus a space are excluded.

| Observed surface measure | Sol | Terra | Opus | Sonnet |
|---|---|---|---|---|
| Hashtags | 85/100 | 100/100 | 100/100 | 100/100 |

These are descriptions of the saved posts, not counts of justified faults. All wording rules also retain source-matching checks in [counts.csv](counts.csv).

No measured text excerpt is asserted for this category. Layout measures are in the per-post table; zero wording matches do not establish that the broader style never occurs.


## All 70 counting rules

Every added rule is defined below and has its own illustration. These illustrations demonstrate positive matches. Exact regular expressions are saved in [criteria.json](criteria.json); all zeroes, model counts, locations and source-absence denominators are in [counts.csv](counts.csv). The 21 `jw_` rules are exact forms from Juzek and Ward's Appendix A. Several overlap with the original inventory; they are included for a faithful, separate check of that historical list, not as 21 new independent habits.

The noun-suffix, comma-plus-ing, three-span coordination, range and first-person rules are deliberately labelled **proxies**: they find text worth inspecting, not a linguistic parse, a false claim or a bad sentence. Broad proxy presence can saturate. For example, a nominal-suffix token appears in 398/400 posts. Many ordinary technical nouns meet that suffix rule, so this does not show that 398 posts are badly written. Layout fractions report their average value, rather than claiming that any nonzero share is excessive.

| ID | Definition / exact scope | Illustration | Evidence source IDs |
|---|---|---|---|
| `jw_delves` | Exact word form from Appendix A; no stemming or semantic judgment. | `delves` | JW |
| `jw_delved` | Exact word form from Appendix A; no stemming or semantic judgment. | `delved` | JW |
| `jw_delving` | Exact word form from Appendix A; no stemming or semantic judgment. | `delving` | JW |
| `jw_showcasing` | Exact word form from Appendix A; no stemming or semantic judgment. | `showcasing` | JW |
| `jw_delve` | Exact word form from Appendix A; no stemming or semantic judgment. | `delve` | JW |
| `jw_boasts` | Exact word form from Appendix A; no stemming or semantic judgment. | `boasts` | JW |
| `jw_underscores` | Exact word form from Appendix A; no stemming or semantic judgment. | `underscores` | JW |
| `jw_comprehending` | Exact word form from Appendix A; no stemming or semantic judgment. | `comprehending` | JW |
| `jw_intricacies` | Exact word form from Appendix A; no stemming or semantic judgment. | `intricacies` | JW |
| `jw_surpassing` | Exact word form from Appendix A; no stemming or semantic judgment. | `surpassing` | JW |
| `jw_intricate` | Exact word form from Appendix A; no stemming or semantic judgment. | `intricate` | JW |
| `jw_underscoring` | Exact word form from Appendix A; no stemming or semantic judgment. | `underscoring` | JW |
| `jw_garnered` | Exact word form from Appendix A; no stemming or semantic judgment. | `garnered` | JW |
| `jw_showcases` | Exact word form from Appendix A; no stemming or semantic judgment. | `showcases` | JW |
| `jw_emphasizing` | Exact word form from Appendix A; no stemming or semantic judgment. | `emphasizing` | JW |
| `jw_underscore` | Exact word form from Appendix A; no stemming or semantic judgment. | `underscore` | JW |
| `jw_realm` | Exact word form from Appendix A; no stemming or semantic judgment. | `realm` | JW |
| `jw_surpasses` | Exact word form from Appendix A; no stemming or semantic judgment. | `surpasses` | JW |
| `jw_groundbreaking` | Exact word form from Appendix A; no stemming or semantic judgment. | `groundbreaking` | JW |
| `jw_advancements` | Exact word form from Appendix A; no stemming or semantic judgment. | `advancements` | JW |
| `jw_aligns` | Exact word form from Appendix A; no stemming or semantic judgment. | `aligns` | JW |
| `canned_insight` | An introductory cue claims to reveal a truth, reality, essence or bigger point. | `The reality is that the tool still needs approval.` | T |
| `honesty_cue` | The writer explicitly labels the statement as honest or candid. | `Let's be honest: the service is expensive.` | T |
| `rhetorical_label` | A colon-ended label announces the kind of statement about to follow. | `Reality check: the test used only ten cases.` | T |
| `quietly` | The adverbs quietly and silently; literal and figurative uses are both counted. | `The update is quietly changing the industry.` | T |
| `load_bearing` | The literal expression load-bearing, with a space or hyphen; metaphor requires inspection. | `That assumption is load-bearing.` | T |
| `does_real_work` | A claim that a distinction or other subject does real work, without judging whether the work is explained. | `This distinction does real work.` | T |
| `demonstrative_payoff` | A this/that cue introduces a why/where explanation or labels an unlock, shift, point or lesson. | `That's the unlock.` | T |
| `fake_objection` | A cue imagines what the reader thinks or asks them to hear the writer out; it may address a real objection. | `You might think the test is complete.` | T |
| `less_more` | A sentence contrasts less about one thing with more about another within a bounded span. | `It is less about speed and more about cost.` | T |
| `more_than_just` | The exact expansion phrase more than just. | `It is more than just a chatbot.` | T |
| `appositive_not` | A comma is followed by not and a short phrase; the negation may be useful or factually necessary. | `It is a workflow, not a chatbot.` | T |
| `good_news` | A familiar transition reassures the reader or announces good news. | `The good news is that access is free.` | T |
| `importance_copula` | An is/are statement calls its subject key, crucial or essential. | `The audit log is crucial.` | T |
| `generic_benefit_phrase` | A benefit is expressed through a fixed effort, clarity, friction, momentum or alignment slogan. | `It does the heavy lifting.` | T |
| `reflective_pose` | A fixed phrase frames a thought as worth contemplation or an idea the writer has arrived at. | `This is worth talking about.` | C |
| `coming_back` | The writer describes returning to a thought; literal movement is also matched. | `I keep coming back to this question.` | C |
| `recurring_question` | A question is framed as repeatedly arising or occupying the writer. | `The question I keep coming back to is cost.` | C |
| `discovery_arc` | A first-person setup says the writer did not plan, intend or expect the discovery. | `I didn't set out to find this pattern.` | C |
| `false_singularity` | A personal-superlative cue selects the most surprising or memorable item; a justified ranking is also matched. | `The one that surprised me most was speed.` | C |
| `physics_metaphor` | A fixed physics phrase; the rule cannot distinguish literal science from a grand metaphor. | `It changes the physics of work.` | C |
| `lives_in` | The expression lives in or lives at; physical residence and abstract placement are both matched. | `The risk lives in the workflow.` | C |
| `challenges_close` | A bounded despite-these/the/its-challenges formula; a concrete obstacle can still be useful. | `Despite these challenges, the future is bright.` | W |
| `future_outlook` | A future-outlook/prospects label or a claim that the future looks bright or promising. | `The future looks promising.` | W |
| `broader_trend` | A cue places an event in a broader movement or calls it a significant shift or turning point. | `This is part of a broader movement.` | W |
| `vague_connection` | An association is described as close, deep or strong; specificity must be checked in context. | `The tool is closely linked to progress.` | W |
| `named_authority_absent` | A fixed expression invokes unnamed experts, observers or shared belief; a name elsewhere may resolve it. | `Industry experts expect rapid growth.` | W |
| `nominal_suffix` | Counts suffix-bearing tokens, including false positives; no part-of-speech tagging. | `Implementation requires evaluation.` | R |
| `comma_ing` | Counts an immediately post-comma -ing word, not all participial clauses. | `The model reads the ticket, generating a reply.` | R |
| `triad_candidate` | Matches three short lexical spans; does not establish three parallel grammatical items. | `It is fast, reliable, and secure.` | W, R |
| `from_to` | Finds a range-shaped span; real numeric and temporal ranges are also matched. | `From productivity to possibility, it does it all.` | N15 |
| `experience_cue` | Finds a small set of first-person verbs; unsupported experience requires comparison with the article. | `I spent last week testing the service.` | N15, N17 |
| `ultimately` | A conventional summary transition appears; whether it repeats a conclusion is not judged. | `Ultimately, the decision is yours.` | T |
| `assistant_residue` | A fixed assistant-facing introduction, helpfulness closing or AI/cutoff self-reference appears. | `Here is your LinkedIn post.` | N15 |
| `bold_spans` | Number of **...** or __...__ spans. | `**A change** in **price**.` | WS |
| `bold_leadins` | Lines with a list marker or emoji, then a bold label and a colon. | `- **Cost:** The price fell.` | WS |
| `bold_word_share` | Bold-span words divided by all post words. | `**Price fell** from $10 to $8.` | WS |
| `emoji_prefixed_lines` | Lines beginning with a code point in the documented emoji ranges. | `💡 One point` | WS |
| `headings` | Lines beginning with one to six # signs and a space. | `## What changes` | WS |
| `title_case_headings` | Headings with at least three alphabetic words, all non-stopwords beginning uppercase. | `## A New Model Release` | WS |
| `three_item_lists` | Contiguous marked list runs containing exactly three lines. | `- Price<br>- Speed<br>- Memory` | W |
| `single_sentence_paragraph_share` | Share of substantive, non-list paragraphs split into one sentence. | `A fact.<br><br>Another fact.` | N15, H |
| `single_sentence_run3` | Maximal runs of at least three one-sentence substantive non-list paragraphs. | `A fact.<br><br>Another fact.<br><br>A third fact.` | N15, H |
| `short_sentence_run3` | Maximal runs of at least three consecutive sentences, each one to six words. | `It is here. It is fast. It costs less.` | T |
| `horizontal_rules` | Lines containing at least three identical -, * or _ characters. | `---` | N15, W |
| `code_fences` | Lines beginning with three backticks. | `\`\`\`text` | N15, W |
| `placeholder` | Bracketed insert/add/your-text placeholders. | `[Insert personal story here]` | N15, W |
| `em_dashes` | Literal em dash characters in the proposed post. | `One change—many claims.` | N15 |
| `exclamations` | Literal exclamation marks in the proposed post. | `A launch!` | N15 |
| `hashtags` | Hash-prefixed word tokens; headings with # plus a space are excluded. | `#AI #Research` | N15 |

## Sources and evidence strength

Links and relevant source passages were checked November 1, 2026 in Toronto (November 2 UTC). Bibliographic dates are distinct from this access date. The source ledger classifies empirical research separately from editorial preferences. Research on scientific abstracts and older model generations does not validate a current LinkedIn claim. Practitioner sites and Wikipedia advice pages supply candidates only. Their authorship-detection, training-data and engagement claims are not adopted. Short paraphrases and original teaching examples are used; full source pages are not redistributed.

| ID | Source | Type | Relevant passage / use |
|---|---|---|---|
| N15 | [Notebook 15: What changes an AI judge's writing score?](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/15-analytical-writing-style) | earlier experiment | README, section 4; notebook habit_definitions. Supplies eight context-sensitive prose criteria. A correctly quoted flag is not proof that its criticism is justified. |
| N17 | [Notebook 17: Writing validation](https://github.com/k-sandhu/experiment-notebooks/tree/main/notebooks/17-writing-validation-extension) | validation experiment | README, sections 7 and 10; neutral prose criteria. Fresh judges gave prose concerns on only 1.6% of opinions on previously flagged passages. Preserve the distinction between a surface match and a justified criticism. |
| JW | [Why Does ChatGPT "Delve" So Much?](https://aclanthology.org/2025.coling-main.426/) | empirical, other models and genre | Appendix A, Table 2. Identifies 21 exact word forms in scientific abstracts. These are historical vocabulary candidates, not a LinkedIn blacklist. |
| K | [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016v5) | empirical, other genre | Abstract and excess-vocabulary method. Motivates corpus frequency comparison. An individual word does not establish authorship or poor quality. |
| R | [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107v2) | empirical, other models and genres | Results on participial clauses, nominalization and coordination. Finds grammatical differences in GPT-4o and Llama 3 writing. Our small surface rules do not reproduce its linguistic parser. |
| W | [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | editorial observations, unvalidated for LinkedIn | Content; language and grammar. Suggests reviewing grand claims, forced contrasts, unnamed authorities and formulaic endings. Wikipedia genre conventions do not automatically transfer to LinkedIn. |
| WS | [Wikipedia: Signs of AI writing/Style](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing/Style) | editorial observations, unvalidated for LinkedIn | Boldface; inline-header lists; title case; emoji. Suggests layout candidates. Presence alone does not measure excessive formatting. |
| T | [Anti-AI Writing Guide, Tundra AI Labs](https://tundraailabs.com/writing-guide) | practitioner preferences, unvalidated | Rhythm; contrasts; word choice; openers and closers. Offers editing preferences about clipped rhythm, rhetorical staging and generic benefits. Use as candidate generation, not measured prevalence. |
| C | [Claudisms](https://claudisms.ai/) | living editorial catalogue, unvalidated | Reflective framing; discovery arcs; metaphors. Provides additional candidate phrases. The site name does not establish that a phrase is specific to Claude. |
| G | [How To Write Without Sounding Like AI, George Kao](https://georgekao.substack.com/p/how-to-write-without-sounding-like) | author editing preferences, unvalidated | April 10, 2026; structure, rhythm and specificity. Recommends reviewing repeated sentence lengths and paragraph templates. These are preferences, not evidence about the four tested models. |
| H | [Fixing AI LinkedIn Posts That Scream ChatGPT, Iris Vandermeer](https://humanizedcopy.com/posts/fixing-ai-linkedin-posts-that-scream-chatgpt) | commercial editorial advice, unvalidated | June 25, 2026, updated July 18; one-line paragraphs and closing questions. Suggests inspecting post shape and generic engagement requests. Its claims about training data and reader penalties are not adopted here. |

## Reproduce

From the experiment folder, run `python expanded_audit.py` and `python build_style_guide.py`. These commands read saved responses and make no model calls. The embedded notebook replays the same calculations without importing repository helpers. When full article files are absent, the frozen [source checks](source_overlap.json) verify the criteria and response fingerprints before replaying paired source-presence counts.

The surface audit adds no model calls. The Decisions classifier uses 800 requests and returns 96,000 independent probabilities, with no new post generation. [Classifier usage](../decision_audit/usage.csv) retains native token/cost records; unavailable cache counters remain missing. [Per-post surface measures](per_post.csv), [per-turn diagnostics](by_turn.csv), [family diagnostics](by_family.csv), [summary](summary.json) and [protocol history](../PROTOCOL.md) preserve the distinct methods. Family rows expose both tested member models; two models do not represent every member of a provider's family. The original [111-entry inventory](../prose_lexicon.json) and [fixed counts](../main/fixed_prose_counts.csv) remain separately available.


Classifier reported cost: $2.265358. This is separate from the original writers' usage. The endpoint exposes no effort control, and returned cache counters for 0/800 requests. Missing counters do not mean zero reuse. Region/whole label conflicts: 996; these are not manually repaired.
