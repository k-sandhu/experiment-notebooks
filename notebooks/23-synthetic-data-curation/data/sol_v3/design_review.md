# Sol-focused round: decisions before calls

The second round had 128 value-correct Sol collection answers out of 128. Its
Luna-to-Sol repairs did not add a source that Sol could not already solve. The
third round asks whether a repair can recover an actual Sol first-pass miss.

Fresh fictional purchase-order packs are rendered by code. Models help write
the generator, but no live generation call writes a test document or answer key.
The new operations include corrected ledger events, reversals, dated pack sizes,
allocation across lines, field-specific amendments and layered price calculations.
Two implementations calculate the labels. Agent reviewers also check rendered
source packs, because agreement between two reducers cannot prove the rendering
contains every fact needed for the answer.

The pilot is a bounded difficulty screen. Eight new cases at each of at most
three predefined levels go to both models once. Stop at the first level with at
least two Sol value or schema failures; otherwise use level three and disclose
that the screen did not find the target difficulty. Keep every pilot attempt and
its stop decision. Do not include pilot items in main accuracy or export counts.

Freeze the chosen level before generating 48 collection cases and 12 audit cases.
Both models get one original answer per case. Select at most 24 collection cases
where Sol's original answer has a value or schema error, using the frozen ordering.
The audit is not used for selection or repair. Evidence-only failures are reported
separately and cannot qualify a case for the main repair comparison.

Each selected source gets three paired interventions: a fresh Sol attempt blind
to its old answer, a Sol repair with its old answer and failed-field categories,
and a Luna repair with the same old Sol answer and the same feedback. The feedback
contains no expected values. It does contain privileged information from the
synthetic answer key about which fields are wrong. This is externally verified
repair, not intrinsic self-correction.

All three interventions get one answer attempt per selected item, the same
source documents, the same batch composition and the same low reasoning setting.
Repair prompts are longer than retry prompts, and completion lengths can differ.
Equal call counts do not mean equal tokens or computation. Record those costs.
All calls use the Codex CLI with tools disabled. This measures that configuration,
not maximum possible model performance.

The primary outcome is the number of original Sol misses that become fully
value-correct, followed by the stricter count also accepted by the evidence check.
Compare paired successes and disagreements with the blind retry. Also count
distinct sources newly solved beyond both original models. Selection conditional
on a Sol failure changes the population; report its denominator alongside full
collection and untouched audit results. No model is trained in this experiment.
Corrected data is a candidate teaching signal, not evidence of a better model.

All earlier data and figures remain byte-identical. Normal notebook execution
replays caches without model calls. This design and the final machine-readable
protocol accompany the saved responses.
