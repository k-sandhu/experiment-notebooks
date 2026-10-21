# Human validation materials

No human responses have been collected. Model adjudication is reported separately in the notebook.

## Reader study

Distribute only [participant/reader.html](participant/reader.html), which runs locally in a modern desktop browser without a server or an account. Keep the administrator directory separate. It contains source identities and correct answers.

Use readers who have not already seen the source packets or study examples. Assign one unused P code to each person. Do not assign someone both a reader role and an editor role for the same case. Each of the 64 schedules has eight documents: one fresh case from each of six decision families and one document from each of the two older cases. No reader sees two versions of one case. Together the schedules cover all 396 documents, with some documents assigned to two readers. The comparison is a pilot, not a sample sized to detect a specified effect. Start with a small number of schedules to check timing and question difficulty before filling the whole plan.

The reader starts a timed document, finishes early or reaches the limit, then answers after the text is hidden. Limits are 90 seconds for an email, 120 for slide text, 300 for an article and 420 for an academic report. Older short documents have a 90-second limit. Some generated documents exceed their requested lengths; the time limit still applies. The test measures comprehension and short-term recall under a time budget, not prose style alone.

Ask readers to work without assistance, complete one session without reloading, and download their response JSON at the end. The page sends no responses to a service. Return each file to the study administrator. Browser timer and visibility events are recorded; background-tab events are reported rather than silently excluded. Reading time is secondary to accuracy.

## Independent editor review

Distribute only [participant/editor.html](participant/editor.html). Assign the A and B versions of each E booklet to different people. A person must not review the same passage twice or discuss it before both independent reviews are submitted. Each booklet has up to 12 passages, with the full document and task available for context.

The selection contains both previously flagged and previously unflagged passages. Do not tell editors which group a passage belongs to, its author or the old judge's assessment. A marked passage can be appropriate.

Use one primary type per problem:

- A prose problem makes the meaning harder to recover from the wording or structure.
- A factual problem conflicts with or adds unsupported claims to the evidence.
- A reasoning problem concerns the inference from the evidence to the conclusion.
- A format problem concerns the requested deliverable, including process notes left in an email or article.
- No problem is a valid assessment. Required terminology, politeness, headings and justified uncertainty are not faults by themselves.

Severity 0 means no justified problem; 1 is a minor nuisance; 2 is likely rereading; 3 is likely misunderstanding. These labels are editor assessments, not measured reader effects. Explain the local reason even when accepting a passage. Download the completed JSON and return it to the administrator.

## Import and analysis

Place completed human JSON files in `data/human/submissions/`, then execute the notebook offline. Raw exports in that folder are git-ignored. It validates the assigned codes, complete assignments, protocol version, data types and duplicate person-item entries. Rejected files appear in `data/human_status.json`. Only complete valid files enter the results.

The notebook scores reader answers against the separate administrator key. Monetary answers allow a USD 0.50 rounding tolerance; quantity answers allow 0.01. Only complete booklets enter this pilot analysis; report incomplete or abandoned sessions separately when administering the study. For fresh cases it uses four varying questions; the older cases exclude their constant randomization question from aggregate accuracy. It averages readers within documents and samples within case and writer. Its interval routine resamples both cases and readers. Editor results retain disagreements and require at least two independent submissions per passage for the paired summary.

Reader accuracy, time, confidence and effort have separate columns. Editor agreement does not make a label objective truth. To assess prose edits causally, first obtain independently verified edits that preserve facts and reasoning, then randomize readers to versions in a new protocol. No verified edited versions are included here.

Run bookkeeping and limitations are in the notebook and its README. The participant pages contain no answer keys, author fields, source-flag labels or model judgments. Their rendered headings and tables preserve the original document's formatting; the underlying text remains unchanged. Slide text is shown as a document, so this study does not evaluate presentation layout.
