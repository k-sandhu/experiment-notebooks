# 04 · Chunking long environmental and industry documents

**Goal.** Repeat the chunking comparison of notebook 02 on long, table-heavy public filings: NPDES and Title V
permits, a RCRA permit, an enforcement settlement, a 387-page utility rate case, a nursing-home inspection, a
pesticide label and a recall notice, each with its own question bank and verbatim evidence quotes.

**Result.** The Decisions API is again the best boundary detector (mean **AP 0.35** vs 0.21 for headings and 0.20 for
embedding distance) and only **6%** of its chunks mix two sections. Retrieval recall@5 is 0.50-0.55 for every
method. A new failure mode appears: 22% of short evidence quotes are split by a Decisions boundary at a real topic
change, against 6-8% for the other methods. Structure-aware chunks need a small overlap or neighbour expansion at
retrieval time.

**Workflow.** The whole experiment from data to results, with the counts from this run. Every model response is cached in `data/`, so a re-run replays it without API calls.

```mermaid
flowchart TD
    docs["12 long public PDFs, sha256-pinned in data/catalog<br/>permits, a settlement, rate cases, an inspection, a label, a recall<br/>694,127 tokens"]
    qs["Curated question banks<br/>284 question and evidence-quote pairs, 144 questions"]
    ext["Extract text blocks (PyMuPDF)<br/>20,800 blocks, 522 gold section starts<br/>from PDF outlines"]
    loc["Locate each evidence quote<br/>276 of 284 found"]
    units["Candidate units<br/>blocks merged to ≥ 40 tokens, split above 200<br/>8,725 units"]
    base["Fixed tokens, Recursive<br/>no model"]
    head["Headings scorer<br/>regex, no model"]
    sem["Semantic scorer<br/>free embedding model, 1 vector per unit"]
    dec["Decisions scorer<br/>278 Decisions calls, 2.70M input tokens, $0.27"]
    dp["Shared DP segmenter<br/>chunks ≤ 400 tokens"]
    chunks["5 chunkings<br/>1,987 to 2,659 chunks each"]
    ev1["Boundary detection<br/>AP and ROC-AUC on 4 outlined documents"]
    ev2["Section structure<br/>section-start recall, mixed-section chunks"]
    ev3["Retrieval over a pooled embedding index<br/>recall@1, 3, 5 and MRR on 276 quotes"]
    res["Decisions + DP: AP 0.35, 77% of section starts hit, 6% mixed chunks<br/>recall@5 0.50-0.55 for every chunker"]
    docs --> ext
    ext --> units
    ext --> base --> chunks
    qs --> loc
    ext --> loc
    units --> head --> dp
    units --> sem --> dp
    units --> dec --> dp
    dp --> chunks
    head --> ev1
    sem --> ev1
    dec --> ev1
    chunks --> ev2
    chunks --> ev3
    loc --> ev3
    ev1 --> res
    ev2 --> res
    ev3 --> res
```

![Boundary probabilities along a California permit](figures/boundary_scores_example.png)

| | |
|---|---|
| Data | 12 long public PDFs pinned by URL and sha256 in `data/catalog/`, with 276 evidence quotes from curated question banks |
| Methods | fixed tokens; recursive; headings + DP; semantic + DP; Decisions + DP (400-token budget) |
| Cost to re-run from scratch | $0.27 on OpenRouter (278 Decisions calls); $0 replaying the caches |

**Run it.** The first run downloads the PDFs into `data/docs/` (git-ignored) and verifies their sha256. Model calls
replay from `data/`.
