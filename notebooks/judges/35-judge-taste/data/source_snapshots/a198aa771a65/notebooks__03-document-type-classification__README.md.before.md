# 03 · Document-type classification on real regulatory and industry PDFs

**Goal.** Notebook 01 classified clean research abstracts by topic. This one classifies messy real-world PDFs
(permits, enforcement settlements, inspection forms, recall notices, accident reports, rate-case filings) by
*document type*, over 101 types, and asks how much of each document the classifier needs to read.

**Result.** One flat `choice` question over all 101 types is the best design: **90.9% top-1**, 96% top-3,
**$0.48 per 1,000 documents**. Retrieve-then-decide, the winner in notebook 01, drops to 88%: embeddings capture
topic, not document form. Reading 8,000 characters instead of 2,000 adds 4 points, mostly on documents whose first
page is a cover letter. Environmental documents are no harder than other industries (91-92% vs 90%).

**Workflow.** The whole experiment from data to results, with the counts from this run. Every model response is cached in `data/`, so a re-run replays it without API calls.

```mermaid
flowchart TD
    tax["Taxonomy written for this notebook<br/>101 document types in 13 groups<br/>20 of them distractors never in the corpus"]
    cat["data/catalog: public PDFs pinned by URL and sha256<br/>22 datasets, files up to 3 MB"]
    gold["Gold labels<br/>publisher-metadata rules for 21 datasets,<br/>first-page review for the facility bundles"]
    dl["Download, check sha256, extract text (PyMuPDF)<br/>first 6 pages, up to 8,000 characters<br/>289 selected, 276 kept, 13 dropped"]
    emb["Free embedding model (OpenRouter)<br/>101 type vectors + 276 document vectors"]
    A["A. Nearest type by cosine similarity<br/>no LLM call"]
    B["B1, B2. Flat: 1 Decisions call over 101 types<br/>first 2,000 or 8,000 characters"]
    C["C. Group → type cascade, beam 2<br/>2 Decisions calls per document"]
    D["D. Embedding top 15 → Decisions<br/>1 Decisions call per document"]
    score["Score 5 methods × 276 documents<br/>acc@1, acc@3, macro-F1, group accuracy,<br/>$ per 1,000 documents, calibration"]
    res["Best: flat over 101 types on 8,000 characters, 90.9% acc@1 (the cascade ties)<br/>1,634 Decisions calls in the cache, $0.47 in total"]
    tax --> gold
    cat --> gold --> dl
    tax --> emb
    dl --> emb
    emb --> A
    emb --> D
    dl --> B
    dl --> C
    tax --> B
    tax --> C
    A --> score
    B --> score
    C --> score
    D --> score
    score --> res
```

![Accuracy by method](figures/accuracy_by_method.png)

| | |
|---|---|
| Data | about 300 public PDFs from US and UK regulators and agencies (EPA, state water boards, NHTSA, FDA, CMS, UK AAIB/MAIB/RAIB, Environment Agency, USGS, NY PSC, Federal Register), each pinned by URL and sha256 in `data/catalog/` |
| Labels | 101 document types in 13 groups, gold labels from publisher metadata and a manual first-page review |
| Methods | embedding nearest-label; flat Decisions question; group→type cascade; embedding shortlist + Decisions; 2,000 vs 8,000 characters of context |
| Cost to re-run from scratch | $0.47 on OpenRouter (1,634 Decisions calls); $0 replaying the caches |

**Run it.** The first run downloads about 300 MB of PDFs into `data/docs/` (git-ignored) and checks each file's
sha256 against the catalog. Model calls replay from `data/`.
