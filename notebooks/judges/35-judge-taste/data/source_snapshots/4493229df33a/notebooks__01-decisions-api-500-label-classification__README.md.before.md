# 01 · Classifying documents into 508 labels with the OpenAI Decisions API

**Goal.** Find out how to use OpenAI's Decisions API (`openai/gpt-6-luna-decisions` on OpenRouter) when the label
set is far larger than one question allows (a `choice` question takes at most 255 options), and whether its
probabilities are good enough to auto-accept confident labels.

**Result.** Retrieve-then-decide wins on accuracy, cost and calls: a free embedding model shortlists 25 labels,
then one Decisions call chooses. **89.5% top-1** (95% CI 85-94%) over 508 labels, **$0.29 per 1,000 documents**.
Auto-accepting at confidence ≥ 0.9 covers 86.5% of documents at 93.6% accuracy. A greedy subfield→topic
cascade reaches only 76.5% because first-step errors cannot be recovered; a beam of 3 recovers most of that.

**Workflow.** The whole experiment from data to results, with the counts from this run. Every model response is cached in `data/`, so a re-run replays it without API calls.

```mermaid
flowchart TD
    topics["OpenAlex topics API<br/>3 fields → 508 topic labels in 24 subfields<br/>name, description, keywords"]
    works["OpenAlex works API<br/>600 random English articles, 2020-2024"]
    filt["Keep topic score ≥ 0.9 and abstract ≥ 80 words: 332<br/>sample 200 documents, 131 distinct gold topics"]
    emb["Free embedding model (OpenRouter)<br/>508 label vectors + 200 document vectors"]
    A["A. Nearest label by cosine similarity<br/>no LLM call"]
    B["B1, B2. Tournament<br/>2 Decisions calls per document"]
    C["C1, C2. Subfield → topic cascade, beam 1 and 3<br/>2 Decisions calls per document"]
    D["D. Embedding top 25 → Decisions<br/>1 Decisions call per document"]
    score["Score 6 methods × 200 documents<br/>acc@1, acc@5, subfield and field accuracy,<br/>$ per 1,000 documents, latency, calibration"]
    res["Best: D, 89.5% acc@1, $0.29 per 1,000 documents<br/>1,795 Decisions calls in the cache, $1.76 in total"]
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

![Accuracy and cost per method](figures/accuracy_vs_cost.png)

| | |
|---|---|
| Data | 508 OpenAlex research topics (Computer Science, Business, Decision Sciences); 200 English abstracts from OpenAlex with their primary topic as the (silver) gold label |
| Methods | embedding nearest-label; two-round tournament; hierarchical cascade (beam 1 and 3); embedding shortlist + one Decisions call |
| Cost to re-run from scratch | $1.76 on OpenRouter (1,795 Decisions calls); $0 replaying the caches in `data/` |

**Run it.** `pip install -r ../../requirements.txt`, open the notebook, run all cells. Without `OPENROUTER_API_KEY`
the notebook replays every call from `data/`.
