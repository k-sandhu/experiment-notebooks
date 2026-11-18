# Public-data deal sourcing in the United States and Canada

## 2026-11-17 · Plan before model outputs

Claim: [#122](https://github.com/k-sandhu/experiment-notebooks/issues/122). Branch: `add-46-us-canada-deal-sourcing`. Fix the search and scoring rules here before starting model runs. Freeze evidence and keep all raw model answers. A pilot is enough to see where search or verification fails. Six briefs give three matched U.S.–Canada comparisons and support descriptive comparisons within these regions.

### Briefs and candidates

| Brief suffix | Required services |
| --- | --- |
| PT | Industrial pressure **and** temperature calibration for external paying customers |
| DE | Industrial dimensional **and** electrical calibration for external paying customers |
| FA | Inspection/testing **and** maintenance/repair of commercial building fire alarm systems |

Run each brief for Michigan/Ohio and for Ontario/Québec. A firm needs an operating site in either listed region. A registered agent, mailing address or service radius alone does not establish a site. Suppliers of instruments, in-house labs and monitoring-only firms are useful near misses. Report a maximum of ten leads, one slot per distinct operating business. Brands, facilities and acquired service divisions collapse into their operating group for duplicate handling. Keep missing slots in the denominator. Score profile claims about the operating company or division named in the input, with the entity scope and date recorded for financials when available.

Country-specific records include Michigan and Ohio registry searches and Ontario, Québec and Canada federal records where appropriate. Accreditation and certification documents establish scope and address at a site. Website claims about family or independent ownership are coded as public statements. Group status needs positive evidence of control or combination. The absence of an announcement, a list of officers, or an active registry entry is insufficient for independent ownership. Reviewers tag qualification as `verified fit` (site, all required services and affirmative independence evidence), `ruled out` (evidence of a hard mismatch) or `unresolved` (a real candidate with incomplete evidence), with unverified names tracked apart. Exclude current operating businesses publicly shown under a larger group. Note any asset-only transaction and treat the transferred operation and the surviving legal entity separately.

### Comparison

1. Deterministic directory/evidence-list baseline. Freeze the rows before seeing model output. Rank businesses in the correct sector by count of required services evidenced in those entries; ties sort by case ID. These rows form a bounded public-source sample, not a full accreditation directory census.
2. Open-web search. Each model gets each brief and a live public search tool through the same Codex CLI. Each receives the same brief and search-operation target. Record actual visible usage where available.
3. Directory-first. Both models start with the exact same sector candidate list and same query access and can identify aliases and verify the listed candidates. They may return only businesses on the supplied list. Code checks any departures.
4. Matched company research. The target is 12 U.S. and 12 Canadian companies, supplied in batches of three. Both models do web-enabled research from names and regions, then resolve the same fields with search disabled and identical source packets. Field labels cover city and regional abbreviation, both calibration service pairs or both fire service fields, and control status. Negative evidence for a particular service must be explicit; otherwise report `unknown`. For open research, a positive may be issued on new evidence, and flagged for independent checking. For the packet condition, only the supplied frozen evidence is in scope. On every call collect URLs, short grounds for the label, and any supported revenue or EBITDA figures with separate date, unit and scope. Unknown financial fields are acceptable.

Open-web and directory-first search are budget-matched by instructions to aim for up to 12 search/open operations per task. The CLI does not enforce a per-call search quota; where available, use its event logs to report actual activity. Search access and aggregate wall time are observed. A time-boxed *human* sourcing and timed review condition requires a human analyst. Keep that condition pending unless one participates, and do not equate model or adjudicator runtime with analyst minutes. No outreach, broker data, gated registry reports or estimates of undisclosed financial data.

### Models, spend and freshness

Use `gpt-6.2-sol` and `gpt-6-luna` through `codex exec`, both at medium reasoning effort. Sol offers a stronger general research comparison and Luna offers a compact model suitable for high-volume screens. The CLI catalog exposes undated IDs; record the requested IDs, CLI version and run date, and record a dated backend revision only if returned. [OpenAI model comparison](https://developers.openai.com/api/docs/models/compare) lists knowledge cutoffs of 2026-06-01 and 2026-05-18, respectively. The current sourcing snapshots and new combinations of criteria are collected in November 2026. Some real businesses, past disclosures and website facts predate those cutoffs. This unavoidable overlap makes recall and accuracy potentially optimistic for unfamiliar businesses. Preserve publication dates where given, distinguish undated pages from pages published after the cutoff, and keep a source access date. Short paraphrases are collected in data rather than copyrighted pages in full.

Projected measured calls: 24 discovery and 32 research calls (three companies per research call), plus setup or evidence review if needed. Default execution replays cached requests. No paid API calls are planned. Tabulate observed tokens, elapsed time, failures and any separately identified spend. Use fresh-call Langfuse traces where available.

### Scoring and interpretation

Pool lead claims by normalized company and location, keep ranks and methods hidden during evidence adjudication, and then join statuses back to methods. Match business aliases and acquisitions to the operating company. Treat licensed site and scope evidence as distinct from ownership evidence. Allow genuinely new candidates to count after independent checks. Report verified fits per ten slots, reference-list coverage where the denominator is known, independently verified additions beyond the bounded baseline, ruled out, unresolved, duplicate or unmatched names, and empty slots. The reference list is open-ended and its coverage is never market-wide recall.

For research, tabulate exact label matches on the frozen fields, including known and unknown labels separately. A service lacking affirmative evidence in a packet is unknown in the packet. For web research compare against the frozen public evidence, account for any independently verified new facts separately, and do not treat an outside claim as true without checking it. Check that material citations directly support their claims. Use the same criteria for both models. Report schema or reply failures apart from readable errors and include a readable-only denominator. Present observed call time and search events, without an analyst productivity estimate. Review real successes, exclusions, missing disclosures, and disagreements under the same rubric.

## 2026-11-17 · CLI change before successful study calls

The Windows launcher and the current account rejected the original requests. Keep the startup error rows. Use the installed npm Codex CLI entry point so settings are passed as separate arguments, and use `gpt-6.1-sol` in place of `gpt-6.2-sol` because the account rejected the latter ID. GPT-6.1 Sol's published cutoff is 2026-04-30. The fresh-data limitation still applies. Smoke prompts for CLI and live web availability are excluded from scoring.

## 2026-11-17 · Evidence adjudication and format sensitivity

After the 24 shortlist calls returned, source researchers received a pooled, sorted list of novel names, cities and brief codes. They did not receive ranks, arm, model name or model verdict. Company URLs, registrations and transaction disclosures established which names referred to operating businesses. One Canadian in-frame firm, Control Fire, was treated as unresolved for discovery after conflicting ownership accounts surfaced. Its pre-run packet remains unchanged in the profile agreement comparison. Parent deduplication combines Transcat's acquired Ohio assets where both appear on the same list. The novel sources and alias revisions were added independently of changing the research prompts or resending model calls.

The original parser accepts a JSON object or a fenced JSON object. Two Luna evidence-packet replies contain otherwise complete JSON followed by a closing final tag, one with a missing angle bracket. A sensitivity replay removes only that terminal tag before parsing. It preserves the original scores and saves a second research summary without fetching data or calling models.

For both parsers, score the documented municipal equivalents of North York and Scarborough (Toronto), Lachine and Saint-Laurent (Montréal), and Saint-Hubert (Longueuil), including the returned compound city and borough spellings. Keep distinct incorporated cities distinct. Candidate adjudication examined public source excerpts with assistance from independent Terra research agents. Research-field agreement uses the frozen packets, even when a cited outside source yields a genuine new fact.

After scoring, a separate, search-disabled Luna call checked that shortlist row counts, readable-field mismatches and the README's research totals reconcile. Its cached task ID is `qa/tables/arithmetic`. It was excluded from the 56 study calls and supplied no evidence or grades.
