# Filing 200 research abstracts under 508 topics with a decision model

## Filing a paper under one topic

A research catalogue does more than store papers. It files each one under a subject, so that a reader can ask for every paper on stock market forecasting, an editor can find reviewers who work on blockchain security, and a funder can count how many papers on a subject appeared each year. OpenAlex, a free catalogue of research papers, does this with a list of 4,516 topics, arranged in a tree of 26 fields and 252 subfields ([OpenAlex help: Topics](https://help.openalex.org/data/topics/)). Every paper gets one primary topic.

Each filing is a small decision. A paper filed under the wrong topic does not disappear, but it goes missing from the searches and counts that rely on its topic. A reader looking for forecasting papers never sees it; a trend chart is off by one. Filing by hand is slow, so catalogues file automatically, and the useful question is which automatic filings a person still needs to check. Support desks routing tickets to hundreds of queues and shops placing products in category trees face the same problem.

### An illustrative example

This example is simplified. Its measured version is followed through the experiment in [section 2](#worked-example-one-abstract-from-start-to-finish).

A paper arrives titled "Stock market prediction using LSTM". Its abstract says it predicts Microsoft's share price from daily opening, highest and lowest prices with an LSTM, a type of neural network built for sequences. Suppose the catalogue had only four topics: stock market forecasting, neural networks, accounting standards and supply chains. A person would read the four, see that the paper is about predicting share prices, and file it under stock market forecasting in a few seconds.

Now give the person 508 topics, each with a paragraph of description. Nobody reads 508 descriptions for every paper. A person narrows the list first. The topics are grouped into 24 subfields, so the natural move is to pick the subfield and then read only the topics inside it.

Here the first step can go wrong. The paper is built around a neural network, so the obvious subfield is Artificial Intelligence, and inside it the obvious topic is "Neural Networks and Applications". But the catalogue keeps "Stock Market Forecasting Methods" in a different subfield, Management Science and Operations Research. A person who opened the Artificial Intelligence shelf will never see the right topic, however carefully they read that shelf. The mistake was made at the first step, and the second step cannot undo it.

A different way to narrow avoids that trap. Instead of choosing a shelf, write down the 25 topics whose descriptions sound most like the paper, from anywhere in the tree, and choose among those. For this paper the short list would hold stock market forecasting near the top, because its description mentions stock price prediction and neural networks in the same paragraph. The cost of this route is a different risk: if the right topic does not sound like the paper, it never makes the short list.

### Letting a model do the filing

A **decision model** is a language model that answers a fixed-choice question instead of writing text. It receives the evidence (here, a paper's title and abstract), a question ("Which research topic is the primary subject of this paper?") and a list of allowed answers, and it returns a probability for every answer. An illustrative reply for the paper above, with three answers on offer, might be 0.90 for stock market forecasting, 0.07 for neural networks and 0.03 for time series forecasting. Nothing has to be parsed out of a sentence, and the answer is always one of the listed topics.

The probability is the second reason to use such a model. A catalogue could file a paper automatically when the model gives its first choice 0.9 or more, and send the rest to a person. That rule only works if the probabilities mean what they say: of all the papers filed at 0.9, about 9 in 10 should be right. A model whose answers match their stated probabilities in this way is called **calibrated**. It is a property to measure, not to assume.

The model cannot simply be handed all 508 topics in one question. The notebook's author reported that the service rejected a question listing all of them, and even where a long list is accepted, sending 508 descriptions with every paper costs about 18 times as many tokens as sending 25 (section 2 explains both). So the list has to be narrowed before the model chooses, and the narrowing step is where the methods differ.

### Ways to narrow the list

This experiment compares three ways of narrowing, each followed by the decision model's choice, and one baseline without the model.

- Shortlist then choose. A text-similarity model, called an embedding model, turns any text into a list of numbers so that texts on similar subjects get similar lists. Comparing these lists ranks all 508 topics almost instantly, at no cost here. The 25 most similar topics go to the decision model, which picks one.
- Subfield first. The decision model picks the subfield, then the topic within it. A second version keeps the three most likely subfields, so a close call at the first step does not decide the answer.
- Tournament. The 508 topics are split into two halves of 254. The model ranks each half, the best 8 of each go to a final of 16, and the model picks the winner. One version lists only the topic names in the first round; the other lists the full descriptions.
- Similarity only. The embedding model's most similar topic is taken as the answer, with no decision model at all. It shows what the decision model adds.

A useful outcome is a method that files the most papers correctly for the money, together with a confidence rule that tells a person which filings to check.

## The question

When an abstract has to be filed under one of 508 research topics, and a decision model cannot be shown all 508 in one question, which way of narrowing the list files the most of 200 abstracts correctly for the money: a 25-topic shortlist by text similarity followed by one question, a subfield first and then a topic, or a two-round tournament? And are the model's probabilities reliable enough to file its confident answers without a person checking them?

A catalogue team, or anyone filing documents against a long label list, needs both answers: the first to choose a design, the second to decide how much of the work still goes to people.

## Study summary

Six methods filed the same 200 abstracts of journal articles, published 2020 to 2024 and drawn at random from OpenAlex, under OpenAlex's 508 topics in computer science, business and decision sciences. Five methods ask OpenAI Decisions, a decision model reached through the OpenRouter service; the sixth uses text similarity alone. The right answer for each abstract is the topic OpenAlex's own classifier gave it.

- Shortlist then choose filed 179 of 200 abstracts under OpenAlex's topic (89.5%, 95% interval 85% to 94%) for $0.29 per 1,000 abstracts, with one model call each. Its 25-topic shortlist held the right topic for 191 of the 200; similarity alone, taking the most similar topic, got 127 right (63.5%).
- The other model-based methods filed 153 to 172 correctly. Subfield first got 153 (76.5%), because its first step sent 39 abstracts to the wrong subfield. Keeping the top three subfields raised that to 171 (85.5%) at $1.56 per 1,000, and the tournament with descriptions reached 172 (86.0%) at $5.25. Shortlist then choose's lead over these two could be chance (it alone was right on 20 and 16 abstracts, they alone on 12 and 9), but it costs about a fifth and an eighteenth as much.
- 5 of the 1,000 model-based runs ended in a refusal, a reply that cannot be scored; they count as wrong. On readable replies the order of the methods does not change (shortlist then choose: 179 of 199).
- Accepting answers with a confidence of 0.9 or more would file 173 of 200 abstracts automatically, 162 of them under OpenAlex's topic (93.6%), and send 27 to a person. The probabilities run high: answers in that band averaged 0.99 but were right 93.6% of the time. Answers given probability 1 were right 122 of 123 times; those between 0.90 and 0.98 only 22 of 31.

In the original situation: a team filing papers could let shortlist then choose file about 86 in every 100 automatically and check the rest; about 1 in 16 of the automatic filings would differ from OpenAlex's topic, and several of those differences are readings a person could defend.

The main caveat is that the right answers are OpenAlex's automatic labels, not a person's, and that the papers and their labels were public before the model was released, so the model may have seen them. The accuracy is an upper bound for new papers, and with 200 abstracts, gaps of a few points between the better methods could be chance.

## Contents

1. [The topics and the abstracts](#1-the-topics-and-the-abstracts)
2. [How the experiment runs](#2-how-the-experiment-runs)
3. [The models and the measures](#3-the-models-and-the-measures)
4. [Results: accuracy and cost](#4-results-accuracy-and-cost)
5. [Results: can the confidence decide what to check](#5-results-can-the-confidence-decide-what-to-check)
6. [Error analysis](#6-error-analysis)
7. [What the evidence supports](#7-what-the-evidence-supports)
8. [Limitations](#8-limitations)
9. [Spend, data and how to run](#9-spend-data-and-how-to-run)
10. [Future work and further reading](#10-future-work-and-further-reading)

## 1. The topics and the abstracts

The labels are every OpenAlex topic in three fields: Computer Science (302 topics); Business, Management and Accounting (146); and Decision Sciences (60). That gives 508 topics in 24 subfields. The subfields are very uneven: Information Systems holds 78 topics and Artificial Intelligence 77, while Industrial relations holds one. Each topic has a name, a published description and keywords. The methods compare an abstract with a topic text built from the name, the description and the first six keywords; for stock market forecasting it begins "This cluster of papers focuses on predicting stock market trends" and runs to 538 characters.

The abstracts come from a random sample of 600 English journal articles published 2020 to 2024 whose OpenAlex primary topic lies in one of the three fields (`data/openalex_works.jsonl`, sampled with seed 42). Two filters left 332:

- OpenAlex gives each primary topic a score, its classifier's probability that the topic is right. Only works scored 0.9 or more were kept, which removes the most ambiguous cases.
- The abstract had to have at least 80 words.

From those 332, 200 were drawn at random. They cover 131 distinct topics, 91 of which appear only once. By field, 117 abstracts are in Computer Science, 63 in Business, Management and Accounting and 20 in Decision Sciences. By year: 22 from 2020, 38 from 2021, 46 from 2022, 49 from 2023 and 45 from 2024. Abstracts run from 84 to 661 words (median 192). Each model sees the title and abstract, cut at 3,000 characters, which shortened 3 of the 200.

The right answer is OpenAlex's primary topic, a silver label: assigned by a program and checked by no one for this experiment. OpenAlex's help page (checked 28 October 2026) says its classifier was replaced in October 2026; the old one read title, abstract, citations and journal, the new one title, abstract and source name. The download date of the works file is not recorded, so which one labelled these abstracts is not known. Subfield accuracy (section 3) is less sensitive to these labels than exact-topic accuracy, because neighbouring topics usually share a subfield.

OpenAlex releases its data under a CC0 public-domain licence ([OpenAlex help: Pricing](https://help.openalex.org/hc/en-us/articles/24397762024087-Pricing)), so the topics and works are saved in `data/`. This notebook was built before the repository's rule that test data must be newer than the models. Every paper was published by 2024, and OpenAlex's topics, descriptions and topic assignments were public before OpenAI Decisions was released, so the model may have seen these papers with their topics. Its accuracy here is therefore an upper bound for papers it has never seen.

## 2. How the experiment runs

### Why the list has to be narrowed

The notebook's author reported that a question listing all 508 topics was rejected and that one question accepts at most 255 options. The rejection was not saved (the cache keeps only answers and refusals), so the notebook cell that sends that question shows only a cache miss. Every question in the run has at most 254 options, but the repository holds no direct evidence for the limit, and neither OpenAI's guide nor OpenRouter's reference, checked on 28 October 2026, states one. OpenAI's guide allows 1 to 400 questions per request.

Cost is the second reason to narrow, and it is measured. Each request is billed by its input tokens at $0.10 per million, and output tokens are always 0 (fields `usage.cost`, `usage.input_tokens` and `usage.output_tokens` in `data/decisions_cache.jsonl`). The tournament's first round, which lists all 508 descriptions across two questions, used 50,985 input tokens per abstract on average. A 25-topic question used 2,890.

### The six methods

| Letter | Method | What it does | Decision model calls per abstract |
|---|---|---|---|
| A | Similarity only | Ranks the 508 topics by similarity to the abstract and takes the first | 0 |
| B1 | Tournament with names | Round 1: two questions in one call, each over 254 topic names; the top 8 of each go to a final over 16 full descriptions | 2 |
| B2 | Tournament with descriptions | As B1, but round 1 lists full descriptions (about 6.6 times the tokens) | 2 |
| C1 | Subfield first, top 1 | Picks one of 24 subfields, then a topic among that subfield's topics (up to 78) | 2 |
| C2 | Subfield first, top 3 | Keeps the three most likely subfields and picks among their pooled topics (up to 198) | 2 |
| D | Shortlist then choose | Keeps the 25 most similar topics and asks one question over them | 1 |

The letters and code names appear in the notebook's charts: "A. embedding nearest-label", "B1. tournament (names → final)", "B2. tournament (descriptions → final)", "C1. cascade (beam=1)", "C2. cascade (beam=3)" and "D. embed top-25 → decide". This README uses the plain names.

Every method asks the same question ("Which research topic is the primary subject of this paper? Choose the single best-matching topic."), and every final question shows full topic descriptions. In subfield first, each subfield is described by its field and the names of its topics. The two tournament halves are a fixed random split of the 508 topics. The confidence of a method is the probability it gives its first choice; subfield first multiplies the probability of the kept subfields by the probability of the topic. Similarity only has no real probability, so it is left out of the confidence analysis.

### Workflow

One abstract is embedded, run through each method and scored against OpenAlex's topic; the worked example below follows one.

```mermaid
flowchart TD
    topics["OpenAlex topics in 3 fields<br/>508 topics in 24 subfields<br/>name, description, keywords"]
    works["OpenAlex works<br/>600 random English journal articles, 2020-2024"]
    filt["Keep topic score ≥ 0.9 and abstract ≥ 80 words: 332<br/>random sample of 200 abstracts, 131 distinct topics"]
    emb["Embedding model (free, via OpenRouter)<br/>708 vectors: 508 topic texts + 200 abstracts"]
    A["A. Similarity only<br/>no model call"]
    D["D. Shortlist then choose<br/>200 Decisions calls, 1 refused"]
    B["B1, B2. Tournament<br/>797 distinct Decisions calls, 2 refused"]
    C["C1, C2. Subfield first<br/>598 distinct Decisions calls, 1 refused<br/>(first step shared by both)"]
    score["Score 6 methods x 200 abstracts against OpenAlex's topic<br/>1,000 model-based runs: 995 answered, 5 refused"]
    res["Accuracy, cost per 1,000 abstracts, seconds per abstract,<br/>confidence checks, error cases"]
    topics --> emb
    works --> filt --> emb
    emb --> A
    emb --> D
    topics --> B
    topics --> C
    filt --> B
    filt --> C
    A --> score
    B --> score
    C --> score
    D --> score
    score --> res
```

The run used 1,595 distinct Decisions calls. The two subfield-first versions share their identical first call (and one refusal), and the two tournaments happened to share one final, so 5 refused runs come from 4 refused calls.

### Model calls for each abstract

Each box is one call to OpenAI Decisions through OpenRouter, or one lookup in the embedding model. Arrows show what one call passes to the next. The calls for one abstract run in sequence, and 8 abstracts run in parallel.

```mermaid
flowchart LR
    doc["Abstract<br/>title + abstract, up to 3,000 characters"]
    subgraph B ["Tournament (B1: names in round 1, B2: descriptions)"]
        b1["Decisions call 1<br/>2 questions in one call, 254 topics each<br/>returns a probability per topic"]
        b2["Decisions call 2<br/>1 question over 16 finalists<br/>full descriptions"]
        b1 -->|"top 8 of each half"| b2
    end
    subgraph C ["Subfield first (C1: top 1, C2: top 3)"]
        c1["Decisions call 1<br/>1 question over 24 subfields"]
        c2["Decisions call 2<br/>topics of the kept subfields<br/>up to 78 (C1) or 198 (C2)"]
        c1 -->|"top 1 or top 3 subfields"| c2
    end
    subgraph D ["Shortlist then choose"]
        d1["Embedding model<br/>similarity to 508 topic texts"]
        d2["Decisions call<br/>1 question over the top 25 topics"]
        d1 -->|"top 25 topics"| d2
    end
    pred["First choice, ranked list, confidence"]
    doc --> b1
    doc --> c1
    doc --> d1
    b2 --> pred
    c2 --> pred
    d2 --> pred
```

### Worked example: one abstract from start to finish

This is the measured version of the opening example: OpenAlex work W4383504851, "STOCK MARKET PREDICTION USING LSTM" (2020, 137 words). OpenAlex files it under Stock Market Forecasting Methods, in the subfield Management Science and Operations Research, with a score of 1.0.

Shortlist then choose first ranks the 508 topic texts by similarity. Stock Market Forecasting Methods comes first, ahead of Sentiment Analysis and Opinion Mining and Financial Analysis and Corporate Governance. The 25 most similar topics include several that have nothing to do with the paper (Hand Gesture Recognition Systems is fifth, Seismology and Earthquake Studies twentieth); the shortlist only has to contain the right topic, not to be clean. Neural Networks and Applications is not among the 25.

The request to OpenAI Decisions has three parts: the title and abstract as the evidence; one question of type `choice` with the instruction quoted in section 2; and the 25 topic texts as the allowed answers. It used 2,758 input tokens. The reply, from the cache, abbreviated:

```json
{"answers": {"topic": {"type": "choice",
   "choice": "Stock Market Forecasting Methods",
   "probabilities": {"Stock Market Forecasting Methods": 1,
                     "Sentiment Analysis and Opinion Mining": 0,
                     "Financial Analysis and Corporate Governance": 0, "...": 0},
   "confidence": 1}},
 "usage": {"input_tokens": 2758, "output_tokens": 0, "cost": 0.0002758},
 "model": "openai/gpt-6-luna-decisions-20261006"}
```

The `confidence` field is the service's own figure; it matches the top probability here, and the notebook uses the top probability throughout. The first choice matches OpenAlex's topic, so the abstract counts as correct for top-1 accuracy. Its confidence of 1 is above 0.9, so under the auto-accept rule it would be filed without review. The call cost $0.00028 and took 0.82 seconds.

The other methods on the same abstract:

| Method | First choice | Confidence | Correct |
|---|---|---:|---|
| Similarity only | Stock Market Forecasting Methods | (no probability) | yes |
| Tournament with names | Stock Market Forecasting Methods | 1.00 | yes |
| Tournament with descriptions | Stock Market Forecasting Methods | 1.00 | yes |
| Subfield first, top 1 | Neural Networks and Applications | 0.495 | no |
| Subfield first, top 3 | Stock Market Forecasting Methods | 0.94 | yes |
| Shortlist then choose | Stock Market Forecasting Methods | 1.00 | yes |

Subfield first fell into the trap from the opening. Its first call gave Artificial Intelligence 0.50 and Management Science and Operations Research 0.48, a near tie. The top-1 version kept only Artificial Intelligence, and its second call, over that subfield's 77 topics, chose Neural Networks and Applications at 0.99. Multiplied together, the confidence is 0.50 × 0.99 = 0.495, so this wrong answer would have gone to a person rather than being filed. The top-3 version kept both subfields and Signal Processing, pooled their 121 topics, and chose correctly at 0.94.

## 3. The models and the measures

| Model | Pinned version | Provider and how called | Size and precision | Settings | Why included |
|---|---|---|---|---|---|
| OpenAI Decisions | `openai/gpt-6-luna-decisions-20261006`, returned in the `model` field of all 1,791 answered responses in `data/decisions_cache.jsonl`; requested as the undated `openai/gpt-6-luna-decisions` | OpenAI, through OpenRouter's Decisions endpoint (an HTTP request; the model has no command-line tool) | Not published | No sampling settings; each request carries only the evidence and the questions | The decision model under test: it returns a probability for every listed topic |
| Llama Nemotron Embed VL 1B v2 (the embedding model) | `nvidia/llama-nemotron-embed-vl-1b-v2:free`; no dated version recorded | NVIDIA, through OpenRouter's free embeddings endpoint | About 1B parameters (from the name); precision not recorded | 512-number vectors, scaled to length 1 | Free; builds the shortlist for shortlist then choose and is the similarity-only baseline |

`data/` records no training cutoff or release date for either model. The dated suffix shows the Decisions version is from 6 October 2026 or later.

The measures:

- A method's **top-1 accuracy** is the share of the 200 abstracts whose first choice is OpenAlex's topic. Higher is better. A refusal counts as wrong; the results also give the share on readable replies.
- Its **top-5 accuracy** counts an abstract as right if OpenAlex's topic is among the method's five highest-ranked topics. It shows near misses.
- Its **subfield accuracy** counts the first choice as right if it sits in the same subfield as OpenAlex's topic.
- The **shortlist recall** is the share of abstracts whose right topic is among the 25 shortlisted topics. It caps shortlist then choose, which can only pick from the list.
- The **cost** is the sum of `usage.cost` over a method's calls, per 1,000 abstracts; embeddings cost $0. The **seconds per abstract** add up the calls an abstract waits for in sequence.
- The **coverage** at a threshold is the share of abstracts whose confidence reaches it, the ones filed without review; the **accuracy on accepted** is top-1 accuracy among them.
- The **expected calibration error** (ECE) measures how far stated confidence is from observed accuracy. Answers are grouped into ten confidence bands (0 to 0.1, 0.1 to 0.2, and so on). In each band, take the gap between the average confidence and the share that were right, then average the gaps, weighting each band by its share of answers. Lower is better; 0 means confidence matches accuracy in every band.

A small example with real numbers. For shortlist then choose, 173 of the 200 answers had confidence of 0.9 or more. Their average confidence was 0.991, and 162 of the 173 were right, 0.936. The gap is 0.055. That band holds 86.5% of all answers, so it adds 0.055 × 0.865 = 0.048 to the method's ECE of 0.071. The other bands, holding the remaining 27 answers, add the other 0.023.

Intervals on top-1 accuracy are 95% bootstrap intervals: the 200 abstracts are resampled with replacement 2,000 times and the middle 95% of the resampled accuracies is reported. Comparisons between two methods use the abstracts where exactly one of them was right, because both methods saw the same 200 abstracts.

## 4. Results: accuracy and cost

| Method | Top-1 (correct of 200) | 95% interval | Top-5 | Subfield | Field | Refused | Top-1 on readable replies | Input tokens per abstract | $ per 1,000 abstracts | Seconds per abstract |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| Similarity only | 63.5% (127) | 56% to 70% | 85.0% | 77.0% | 91.0% | 0 | 127 of 200 | 0 | $0.00 | 0.00 |
| Tournament with names | 83.5% (167) | 78% to 89% | 89.5% | 91.0% | 98.5% | 0 | 167 of 200 | 9,755 | $0.98 | 2.20 |
| Tournament with descriptions | 86.0% (172) | 81% to 91% | 98.0% | 91.0% | 97.5% | 2 | 172 of 198 | 52,477 | $5.25 | 2.50 |
| Subfield first, top 1 | 76.5% (153) | 70% to 82% | 79.5% | 80.0% | 96.0% | 1 | 153 of 199 | 8,396 | $0.84 | 2.46 |
| Subfield first, top 3 | 85.5% (171) | 81% to 91% | 92.0% | 89.5% | 97.5% | 1 | 171 of 199 | 15,565 | $1.56 | 2.60 |
| Shortlist then choose | 89.5% (179) | 85% to 94% | 95.0% | 95.0% | 98.0% | 1 | 179 of 199 | 2,876 | $0.29 | 0.87 |

From the notebook's results table (section 5.1); the readable-reply column leaves out each method's refusals (`refused` entries in `data/decisions_cache.jsonl`).

![Left: horizontal bars of top-1 accuracy for the six methods with 95% intervals, red circles for top-5 accuracy and green squares for subfield accuracy; shortlist then choose is highest at 0.895. Right: top-1 accuracy against cost per 1,000 abstracts on a log scale for the five model-based methods; shortlist then choose sits at the top left](figures/accuracy_vs_cost.png)

How to read this figure. The left panel has one row per method, labelled with the code names from section 2. The blue bar is top-1 accuracy as a share of 200 abstracts, and the black line is its 95% interval. The red circle is top-5 accuracy and the green square subfield accuracy. Where the two coincide the square hides the circle: for shortlist then choose both are 0.95, and for similarity only the legend box partly covers the red circle at 0.85. The right panel leaves out similarity only, which costs nothing, and plots top-1 accuracy against dollars per 1,000 abstracts. The cost axis is logarithmic (each tick multiplies the cost), and the accuracy axis starts at 0.76, which makes vertical gaps look larger. The panel titles describe the axes rather than the finding, and "LLM methods" means the five methods that call the decision model.

Shortlist then choose files the most abstracts correctly, 179 of 200, at the lowest cost of any model-based method ($0.29 per 1,000) and in the least time (0.87 seconds per abstract, one call where the others make two in sequence). Its edge is clearest against similarity only and subfield first with one subfield. Shortlist then choose was right on 58 abstracts that similarity only missed, and similarity only on 6 that it missed. Against subfield first with one subfield the split is 40 to 14. A sign test on those abstracts gives p below 0.001 for both, so these gaps are not chance.

Against the three stronger alternatives the evidence is weaker. Shortlist then choose was right where the other was wrong on 22 abstracts against 10 for the tournament with names (p = 0.05), 20 against 12 for subfield first with three subfields (p = 0.22) and 16 against 9 for the tournament with descriptions (p = 0.23). Those three could be about as accurate. What separates them is cost: subfield first with three subfields costs 5.4 times as much, the tournament with names 3.4 times and the tournament with descriptions 18 times.

The decision model adds 26 points to the embedding model's own answer, from 127 to 179 correct. The embedding model is good at narrowing and poor at choosing: it ranked the right topic first for 127 abstracts but within its top 25 for 191.

### Where the wrong answers land

A neighbouring topic in the right subfield still puts a paper on the right shelf; a topic in another field does not. Each abstract is sorted by its first choice:

| Method | Correct | Wrong topic, right subfield | Wrong subfield, right field | Wrong field | Refused |
|---|---:|---:|---:|---:|---:|
| Similarity only | 127 | 27 | 28 | 18 | 0 |
| Tournament with names | 167 | 15 | 15 | 3 | 0 |
| Tournament with descriptions | 172 | 10 | 13 | 3 | 2 |
| Subfield first, top 1 | 153 | 7 | 32 | 7 | 1 |
| Subfield first, top 3 | 171 | 8 | 16 | 4 | 1 |
| Shortlist then choose | 179 | 11 | 6 | 3 | 1 |

Counts behind the notebook's error-landing chart (section 5.2), recounted from the cached responses.

Shortlist then choose has the fewest wrong-branch errors: 9 of its 20 readable mistakes left the subfield, against 39 of 46 for subfield first with one subfield. More than half of its mistakes are neighbouring topics, such as "Education, Technology, and Economics" for a paper OpenAlex files under "Economic Growth and Development".

### Why the shortlist works and where it fails

| Topics kept | 1 | 5 | 10 | 25 | 50 | 100 |
|---|---:|---:|---:|---:|---:|---:|
| Abstracts whose right topic is kept | 127 (63.5%) | 170 (85.0%) | 182 (91.0%) | 191 (95.5%) | 196 (98.0%) | 198 (99.0%) |

From the shortlist recall curve in the notebook (section 4, method A).

Keeping 25 topics holds the right one for 191 abstracts; doubling to 50 would add 5 more. Among the 191, the decision model chose the right topic for 179 (93.7%). The 9 abstracts whose topic missed the shortlist could not be filed correctly by this method, and they make up 9 of its 21 misses (one of them refused). The failure is plainest on a mathematical abstract. For "The Jordan Canonical Form of a Product of Elementary S-unitary Matrices" (W3098763576), the three most similar topics were Nonlinear Dynamics and Pattern Formation, Expert finding and Q&A systems, and activated carbon and charcoal; the right topic, Matrix Theory and Algorithms, ranked 31st.

### Why subfield first loses abstracts

Subfield first with one subfield sent 39 of the 200 abstracts to the wrong subfield at its first step and refused one more, so its second step could be right on at most 160. It was right on 153. Keeping three subfields cut the first-step misses to 15 and raised the score from 153 to 171; it was right on 22 abstracts that the one-subfield version missed and wrong on 4 it got right. The cost is the second question's length: an average of 113 topics instead of 42, and 15,565 input tokens per abstract instead of 8,396.

Of the 39 first-step misses, 14 went to Artificial Intelligence. They include the stock prediction paper from section 2, a course recommender built with language processing (W3185225192, OpenAlex topic Recommender Systems and Techniques) and a detector of Ponzi schemes on Ethereum (W4309857254, OpenAlex topic Blockchain Technology Applications and Security). In these three, the method is machine learning, while OpenAlex files the paper by what it is applied to. Shortlist then choose filed all three correctly.

### What the tournament pays for

The two tournaments differ only in their first round. With names alone, the right topic survived into the 16 finalists for 179 of 200 abstracts; with full descriptions, for 196 of the 198 that were answered. The final, which shows descriptions in both versions, then picked the right finalist for 167 of 179 and 172 of 196. Descriptions in round one keep the right topic in play more often, but the net gain is 5 abstracts (sign test p = 0.47) for 5.4 times the cost.

## 5. Results: can the confidence decide what to check

The notebook's two charts for this question (a reliability chart of stated confidence against observed accuracy, and a coverage chart) are not saved to `figures/`, so the tables below give the same information as counts.

| Accept if confidence is at least | Abstracts accepted | Correct among accepted | Sent to a person | Correct among those sent |
|---|---:|---|---:|---|
| 0 (accept all) | 200 | 179 (90%) | 0 | none |
| 0.3 | 198 | 178 (90%) | 2 | 1 |
| 0.5 | 197 | 177 (90%) | 3 | 2 |
| 0.7 | 186 | 170 (91%) | 14 | 9 |
| 0.9 | 173 | 162 (94%) | 27 | 17 |

For shortlist then choose. The notebook's threshold table gives the shares; this and the next two tables are recounted from `data/decisions_cache.jsonl` (field `answers.topic.probabilities`).

At 0.9, shortlist then choose files 173 abstracts automatically and gets 162 right (93.6%, Wilson 95% interval 89% to 96%). The 27 sent to a person include 17 that were right, 9 that were wrong and the refusal. Lower thresholds barely change accuracy, because almost all answers sit at the top of the scale.

| Method | ECE | Accepted at 0.9 or more | Correct among accepted | Wrong filings let through |
|---|---:|---:|---|---:|
| Tournament with names | 0.100 | 165 | 152 (92.1%) | 13 |
| Tournament with descriptions | 0.064 | 159 | 153 (96.2%) | 6 |
| Subfield first, top 1 | 0.127 | 141 | 126 (89.4%) | 15 |
| Subfield first, top 3 | 0.058 | 145 | 138 (95.2%) | 7 |
| Shortlist then choose | 0.071 | 173 | 162 (93.6%) | 11 |

ECE values are from the notebook's reliability chart.

At the same 0.9 rule, shortlist then choose files the most abstracts correctly without review, 162, against 153 for the tournament with descriptions and 138 for subfield first with three subfields. Those two let fewer wrong filings through (6 and 7 against 11), because they accept fewer abstracts. Which is better depends on what a wrong filing costs compared with a person's check.

The probabilities are usable for ranking but run high. In every method, answers above 0.8 were right less often than their average confidence: for shortlist then choose, 184 answers averaged 0.983 and 91.8% were right; for the tournament with names, 177 averaged 0.977 and 88.7%. The service reports probabilities in steps of 0.01, and shortlist then choose gave probability 1 to 123 of its 200 answers. Splitting its answers by confidence shows where the reliable part is:

| Confidence of first choice | Answers | Correct |
|---|---:|---:|
| Below 0.5 (including the refusal, scored 0) | 3 | 2 |
| 0.5 to 0.69 | 11 | 7 |
| 0.7 to 0.89 | 13 | 8 |
| 0.9 to 0.98 | 31 | 22 (71%) |
| 0.99 or 1 | 142 | 140 (98.6%) |


Answers at 0.99 or 1 were almost always right (140 of 142; at exactly 1, 122 of 123). Answers between 0.9 and 0.98 were right only 71% of the time (Wilson interval 53% to 84%), far below what they state. A threshold of 0.99 would have filed 142 abstracts at 98.6%. This split was found after looking at the results, on 200 abstracts, so it needs a fresh sample before anyone relies on it.

In the notebook's reliability chart, the middle bands (0.4 to 0.6 and 0.6 to 0.8) sit mostly below the diagonal for the tournaments and subfield first, and close to it for shortlist then choose. These bands hold 5 to 18 answers per method, so their points move a lot with a few abstracts.

## 6. Error analysis

Shortlist then choose missed 21 of 200 abstracts. They split into three kinds, counted from the cached shortlists and responses:

- 1 refusal. Its right topic was also outside the shortlist.
- 8 readable answers where the right topic was not on the 25-topic shortlist. The decision model chose the best topic on offer, and 5 of these 8 came with confidence of 0.9 or more.
- 12 answers where the right topic was on the shortlist and the model chose another. For 11 of them OpenAlex's topic was among the model's top 5, and 6 stayed in the right subfield.

Of the 11 wrong answers that would pass the 0.9 rule, 5 are shortlist misses and 6 are choices between listed topics. The probability describes the choice among the 25 topics shown; it cannot say that the right topic was missing from them.

### A shortlist miss that the other methods got right

The Jordan canonical form paper (W3098763576) defines S-unitary matrices and determines the Jordan form of a product of two of them. The embedding model ranked its topic, Matrix Theory and Algorithms, 31st, behind topics such as activated carbon and charcoal. The decision model chose Advanced Algebra and Logic, a neighbour in the same subfield, at 0.94. Both tournaments and both subfield-first versions, which never use the shortlist, filed it correctly. The pattern holds across the 9 shortlist misses: at least one other model-based method filed 8 of them correctly, and subfield first with three subfields filed 6.

### A confident choice the score counts as wrong

"Robust Optimization Model with Shared Uncertain Parameters in Multi-Stage Logistics Production and Inventory Process" (W3005017983) proposes a robust optimisation model and tests it on what the abstract calls "the multi-stage logistics production and inventory process problem". OpenAlex files it under Risk and Portfolio Optimization. Shortlist then choose had both topics on its list, in first and second place, and chose Supply Chain and Inventory Management with probability 1. It is the only wrong answer among the 123 given probability 1. Both tournaments made the same choice; subfield first with one subfield agreed with OpenAlex. The abstract supports either reading: its method is robust optimisation, its application is an inventory process.

"The Evolution of Luxury Consumption and Conceptualization: A Synthetic Review" (W4390615093) is similar. It reviews 307 papers on luxury and states that "Bibliometric analysis and content analysis were used". OpenAlex files it under Consumer Behavior in Brand Consumption and Identification; shortlist then choose chose scientometrics and bibliometrics research at 0.96. All four other model-based methods agreed with OpenAlex, and both tournaments gave its first choice only about 0.5. Here the paper's subject is luxury brands and its method is bibliometrics, and the methods split on which one defines the topic.

These cases show where top-1 accuracy against a silver label misleads. Each counts as one error, the same as a paper filed in the wrong field, although a person reading the abstract could accept the model's choice.

### Abstracts every model-based method got wrong

All five model-based methods missed 4 abstracts; all five were right on 119.

- "CE-PBFT: A high availability consensus algorithm for large-scale consortium blockchain" (W4404257738) proposes a Byzantine fault-tolerance protocol for blockchains. OpenAlex files it under Blockchain Technology Applications and Security. Every method chose Distributed systems and fault tolerance; shortlist then choose gave it 0.98, and the right topic was 27th by similarity, two places outside the shortlist. Both tournaments and subfield first with three subfields ranked OpenAlex's topic second. The paper is about both topics, and every method preferred the fault-tolerance reading.
- "SoK: Realistic adversarial attacks and defenses for intelligent network intrusion detection" (W4385973175) is the same kind of overlap. OpenAlex files it under Adversarial Robustness in Machine Learning; every model-based method chose Network Security and Intrusion Detection, and shortlist then choose gave OpenAlex's topic 0.11. Similarity only, which simply took the most similar topic, matched OpenAlex.
- "M.G. Mohanty vs. That State of Odisha" (W4386448110) discusses which Indian courts may hear commercial arbitration cases. OpenAlex files it under International Arbitration and Investment Law; every method chose Dispute Resolution and Class Actions, which shortlist then choose preferred 0.89 to 0.09.
- "Image Modification Using Deep Neural Cellular Automata" (W4309219744): OpenAlex files it under Generative Adversarial Networks and Image Synthesis; shortlist then choose chose Cellular Automata and Applications at 0.97.

In each case the model's choice names a real subject of the paper. They read as disagreements about which of two subjects is primary, which no method in this design can resolve without a person's label.

### Refusals

Five model-based runs ended in an HTTP 502 error whose message reads "OpenAI refused to answer question" and names the question. They came from 4 refused calls, because the two subfield-first versions share their first call.

| OpenAlex work | Title, shortened | Refused in | OpenAlex topic |
|---|---|---|---|
| W4281612646 | The Intermediate Guide to Jonathan Schwab | Tournament with descriptions, round 1 | Corporate Insolvency and Governance |
| W3098278328 | Challenges in the collection of convalescent plasma for COVID-19 patients | Tournament with descriptions, round 1 | Blood donation and transfusion practices |
| W3098314892 | Mechanism of "Scutellaria barbata-Hedyotis diffusa" against breast cancer | Both subfield-first versions, first step | Computational Drug Discovery Methods |
| W4226081738 | Cisco 352-001 Dumps [2022] | Shortlist then choose | Technology and Education Systems |

Two are medical papers. The other two are not research at all: the first is promotional web text about bankruptcy lawyers, the last an advertisement for exam answer files, both indexed by OpenAlex as journal articles. Every refused abstract was answered by the other methods, so a refusal depends on the question as well as the text: the bankruptcy text was refused when round one listed descriptions and answered when it listed names. The other methods filed the first three correctly; for the exam advertisement only subfield first with one subfield matched OpenAlex, at confidence 0.20. A refusal gives no label, so a filing system should send it to a person.

### A correct answer sent to review

"The Impact of Visual Stimuli on Online Shopper's Emotion: Applying S-O-R Theory in Online Fashion Retail" (W4403827652) shows the review queue doing its job. Shortlist then choose split 0.51 for Consumer Retail Behavior Studies, OpenAlex's topic, and 0.48 for Consumer Behavior and Marketing Influence. The answer is right, but at 0.51 it goes to a person, who would see two close topics. Subfield first with one subfield chose the other topic at 0.95. Of the 27 abstracts that shortlist then choose would send to review at 0.9, 17 are right answers like this one.

### What these examples cannot show

They show which topic each method returned and how sure it was, not why. The defensible-error cases are a reading of the abstract by the author of this page, not a second label from an independent person; how many of the 21 misses a person would accept has not been measured.

## 7. What the evidence supports

- To file documents against a long label list with this decision model, shortlist by text similarity and ask one question over the shortlist: 179 of 200 correct, $0.29 per 1,000 documents, under a second each. Subfield first with three subfields or a tournament with descriptions may be as accurate, but cost 5 and 18 times as much and take three times as long.
- Do not narrow with a single first step that cannot be revised. Choosing one subfield first lost 39 of 200 abstracts before the topic question was asked.
- Check the shortlist, not just the model. 9 abstracts were lost because the right topic was not among the 25, and the model gave 5 of them confidence of 0.9 or more. A better embedding model or a longer shortlist (98% at 50 topics) is the cheapest place to look for gains.
- Use the confidence to sort work, not as a literal probability. Accepting 0.9 or more filed 86.5% of abstracts at 93.6% accuracy. Answers at 0.99 or 1 were right 140 of 142 times; those between 0.90 and 0.98 behaved more like 70% than 95%.
- Treat a refusal as "send to a person". Refusals were rare (5 of 1,000 runs) and hit two medical papers and two advertisements.

The uncertainty that most needs another experiment is how accurate these methods are on papers the model cannot have seen, scored against labels a person has checked.

## 8. Limitations

- The data predates the repository's fresh-data rule. The papers were published 2020 to 2024 and their OpenAlex topics were public before the model was released, so the accuracy is an upper bound for new papers.
- The right answers are silver labels from OpenAlex's own classifier, kept only at a score of 0.9 or more. Which version of that classifier labelled them is not recorded. Several counted errors are defensible readings (section 6), and no person has labelled the 200 abstracts.
- 200 abstracts give 95% intervals about 5 points either side of each accuracy. The three best model-based methods are within that range of each other.
- One sample, one tournament split, one shortlist length (25) and one embedding model, the weakest part of the best method.
- The 255-option limit that shapes every design has no saved evidence (section 2), so a single question over all 508 topics was not compared.
- The cache also holds 200 responses from an earlier run of shortlist then choose with a paid embedding model (OpenAI's text-embedding-3-small, according to the notebook's earlier notes). Matched to the same abstracts by request hash, its shortlist held the right topic for 197 and it filed 182 correctly (91.0%). Its embeddings were not saved, so it cannot be replayed and is not in the results. Run history is in [`data/PROTOCOL.md`](data/PROTOCOL.md).
- The methods and measures were not fixed in a written plan before the results were seen. The confidence split at 0.99 in section 5 was found after looking at the results.
- Only one decision model was tested, at one version, through one provider.

## 9. Spend, data and how to run

The cache holds 1,795 Decisions responses with a recorded cost of $1.76. The results replay 1,595 of them ($1.70; the 4 refusals carry no cost); the other 200 ($0.058) are the earlier shortlist run in the limitations. The 708 embeddings were free. The median answered call took 1.16 seconds with 8 abstracts in flight.

| File in `data/` | What it holds |
|---|---|
| `openalex_topics.json` | The 508 OpenAlex topics with name, description, keywords, subfield and field |
| `openalex_works.jsonl` | The 600 sampled works: title, year, primary topic and score, abstract |
| `decisions_cache.jsonl` | Every Decisions response, keyed by a hash of the full request: probabilities, usage, cost, model version, latency, or a refusal |
| `embeddings_cache.npz` | The 708 embedding vectors, keyed by a hash of model name and text |
| `PROTOCOL.md` | Run history: dates, settings, the option-limit probe, refusals, the earlier shortlist run and spend |

From this folder, the notebook replays every call from the cache without an API key:

```bash
pip install -r ../../requirements.txt
jupyter nbconvert --to notebook --execute --inplace 01_decisions_api_500_label_classification.ipynb
```

A request missing from the cache needs `OPENROUTER_API_KEY` and is sent to OpenRouter. `N_DOCS` (200) at the top of the notebook sets the sample size. Re-running from an empty cache would make 1,595 Decisions calls, about $1.70. The free embedding endpoint may log its inputs, which is acceptable for these public abstracts but not for private documents. The full analysis is in [01_decisions_api_500_label_classification.ipynb](01_decisions_api_500_label_classification.ipynb).

## 10. Future work and further reading

### Future work

- Score against labels a person has checked. Have two people label the 200 abstracts and recount every method. Motivated by the defensible errors in section 6 and the 4 abstracts every method filed under the same non-OpenAlex topic.
- Separate shortlist misses from choice errors. Rerun shortlist then choose with 50 and 100 topics and with a larger open-weight embedding model, and report how many of its 21 misses each change fixes. Motivated by the 9 misses whose topic never reached the shortlist.
- Test a single question over all topics. Send one 508-option question, save the service's reply whether it answers or rejects, and compare accuracy and cost with the shortlist. Motivated by the unsaved rejection behind the 255-option limit.
- Test the confidence rule at scale and on new papers. Classify 2,000 abstracts published after the model's release, fit the threshold on half and check coverage and accuracy on the other half, including whether answers at 0.99 or 1 stay near 98.6% correct. Motivated by the 31 answers between 0.90 and 0.98 that were right 71% of the time.
- Scale to the full OpenAlex tree of 4,516 topics in 26 fields, where a shortlist keeps 25 of 4,516 and a cascade gains a level, so the two designs are tested where they differ most.

### Further reading

Links checked on 28 October 2026.

- [Decisions](https://developers.openai.com/api/docs/guides/decisions) (OpenAI API guide). The vendor's description of the model tested here: typed questions over fixed options, answered with probabilities instead of text.
- [Submit a Decisions request](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) (OpenRouter API reference). The endpoint and request body (evidence and questions) that the notebook sends.
- [Topics](https://help.openalex.org/data/topics/) (OpenAlex help). How OpenAlex builds its 4,516 topics and assigns them to works, and so what the silver labels here mean.
- [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599) (Guo et al., 2017). Defines expected calibration error and temperature scaling, the measure used in section 5 and the usual fix for over-confident probabilities.
- [Selective Classification for Deep Neural Networks](https://arxiv.org/abs/1705.08500) (Geifman and El-Yaniv, 2017). The trade-off between coverage and accuracy behind the auto-accept threshold.
- [In-Context Learning for Extreme Multi-Label Classification](https://arxiv.org/abs/2401.12178) (D'Oosterlinck et al., 2024). A pipeline that infers, retrieves and ranks over thousands of labels, close to shortlist then choose.
