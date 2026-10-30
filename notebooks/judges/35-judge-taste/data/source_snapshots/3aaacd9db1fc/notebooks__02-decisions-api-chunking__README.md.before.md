# 02 · Chunking long documents: Decisions API vs classic splitters

**Goal.** Test whether the Decisions API can decide *where* to split a long document better than fixed windows,
recursive splitting, heading heuristics or embedding-based "semantic chunking", with all structure-aware methods
sharing the same candidate split points and the same dynamic-programming segmenter.

**Result.** As a section-start detector the Decisions API scores mean **AP 0.60 / ROC-AUC 0.88**, against 0.43 / 0.82
for a heading heuristic and 0.32 / 0.73 for embedding distance. Its chunks place a boundary near **85%** of real
section starts and only **8%** of them mix two sections (fixed windows: 28% and 46%). It costs about **$0.37 per
million document tokens**. Retrieval recall@5 is 0.76-0.79 for every chunker: on this question set, cleaner
chunks did not change what retrieval finds.

**Workflow.** The whole experiment from data to results, with the counts from this run. Every model response is cached in `data/`, so a re-run replays it without API calls.

```mermaid
flowchart TD
    docs["6 public documents: 5 PDFs + the RFC 9110 text<br/>386,257 tokens"]
    qs["lumen-copilot benchmark questions.csv<br/>33 question and evidence-quote pairs"]
    ext["Extract text blocks (PyMuPDF)<br/>9,096 blocks, 716 gold section starts<br/>from PDF outlines and RFC numbering"]
    loc["Locate each evidence quote<br/>33 of 33 found"]
    units["Candidate units<br/>blocks merged to ≥ 40 tokens, split above 200<br/>4,534 units"]
    base["Fixed tokens, Recursive<br/>no model"]
    head["Headings scorer<br/>regex, no model"]
    sem["Semantic scorer<br/>free embedding model, 1 vector per unit"]
    dec["Decisions scorer<br/>144 Decisions calls, 1.44M input tokens, $0.14"]
    dp["Shared DP segmenter<br/>chunks ≤ 400 tokens"]
    chunks["5 chunkings<br/>1,104 to 1,487 chunks each"]
    ev1["Boundary detection<br/>AP and ROC-AUC on 4 outlined documents"]
    ev2["Section structure<br/>section-start recall, mixed-section chunks"]
    ev3["Retrieval over a pooled embedding index<br/>recall@1, 3, 5 and MRR on 33 quotes"]
    res["Decisions + DP: AP 0.60, 85% of section starts hit, 8% mixed chunks<br/>recall@5 0.76-0.79 for every chunker"]
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

![Boundary probabilities along a NIST standard](figures/boundary_scores_example.png)

| | |
|---|---|
| Data | six public documents (arXiv "Attention Is All You Need", NIST SP 800-63B, RFC 9110, Berkshire Hathaway 2023 letter, IPCC AR6 WG1 SPM, IRS 1040 instructions) and the human-written questions and evidence quotes from the public [lumen-copilot](https://github.com/k-sandhu/lumen-copilot) RAG benchmark |
| Methods | fixed tokens; recursive; headings + DP; semantic + DP; Decisions + DP (400-token budget for all) |
| Cost to re-run from scratch | $0.14 on OpenRouter (144 Decisions calls); $0 replaying the caches |

**Run it.** The PDFs are downloaded from their publishers on the first run into `data/docs/` (git-ignored). Model
calls replay from `data/`.
