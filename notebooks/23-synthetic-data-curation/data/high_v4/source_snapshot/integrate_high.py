"""Apply the reviewed v4 appendix and update the standalone reading paths."""
import hashlib
import json
from pathlib import Path
from build_high_extension import build

base = Path(__file__).parent
repo = base.parent / 'experiment_notebooks'
folder = repo / 'notebooks/23-synthetic-data-curation'
proposal = build(write=True)
path = folder / '23_synthetic_data_curation.ipynb'
notebook = json.loads(path.read_text(encoding='utf-8'))
headline = ('The newest attempt requests high reasoning on longer procurement histories. All 1,056 possible main packets and 32 pilot packets pass independent source checks. '
    'The live pilot stopped after repeated HTTP 429 service errors: 31 request records contain three correct answers, 24 service rejections and four interrupted records. '
    'No difficulty level was selected and no repair-versus-retry comparison was run. The larger cases are ready, but their model performance remains unmeasured.')
top_workflow = '''
### Higher-reasoning follow-up status

```mermaid
flowchart LR
    inputs["32 pilot + 1056 potential main packets"] --> checks["Independent source/key audits<br/>all packets agree"]
    checks --> trial["High-reasoning Sol pilot<br/>31 preserved request records"]
    trial --> stopped["Service interrupted<br/>3 answers,24 HTTP429,4 pending"]
    trial -. "not reached" .-> planned["160-240 originals +24 audit<br/>up to80 paired repair/retry cases"]
```

The source checks establish calculable targets. The incomplete pilot provides three individual answers, but cannot select a difficulty level or estimate whether feedback helps.
'''
for c in notebook['cells']:
    if c['cell_type'] != 'markdown':
        continue
    s = ''.join(c['source'])
    if s.startswith('# Making useful'):
        s = s.replace('The latest follow-up adds 48', 'The third follow-up adds 48') + '\n\n' + headline + '\n'
    if s.startswith('## Contents'):
        s += '\n' + top_workflow
    c['source'] = s.splitlines(keepends=True)

future = '''## 14. Future work and further reading

The linked sources were checked on October 26, 2026. The higher-reasoning comparison remains unmeasured because service errors stopped its pilot.

### Future work

- Resume a separately versioned high-reasoning run when CLI requests complete reliably, using the frozen 160-case collection, conditional 80-case expansion and 24-case audit. Measure genuine value failures and paired recovery. The 31 interrupted-run request records did not establish a difficulty level.
- Add an old-answer-only arm to the paired recovery test, alongside fresh retry and old answer plus failed-field feedback. Measure how much any repair advantage comes from the previous answer versus the diagnosis. V3 recovered the same three failures with retry and repair, and the current design combines both kinds of added information.
- Give Sol a calculator or ledger-reconciliation tool on matched source packets. Measure quantity and price error rates, tool use and total tokens against the tool-disabled setting. V3's four original wrong fields were numerical; the new source audit makes exact arithmetic independently inspectable.
- Add cancellation, missing-document and OCR conditions with explicit solvable or abstention targets, and have independent reviewers check each packet before calls. Measure valid abstention and error type. The 1,056 new main packets all describe active orders with clean tables, leaving those conditions untested.
- Replace oracle failed-field flags with a separate verifier that sees only the source and proposed answer. Measure verifier precision and paired recovery against exact-key feedback. The present planned repair arm benefits from a diagnosis that ordinary extraction workflows may not have.

### Further reading

- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (Huang et al., 2024). Studies correction without external feedback; our proposed repair package receives externally verified failed-field labels.
- [Learning to Build the Environment: Self-Evolving Reasoning RL via Verifiable Environment Synthesis](https://arxiv.org/abs/2605.14392) (Shi et al., 2026). Motivates executable task generation, verification and difficulty calibration; this notebook collects data without reproducing its training procedure.
- [Self-Evolve With a Reference: Anchored Training of Tool-Integrated Agents](https://arxiv.org/abs/2610.09856) (Liao et al., 2026). Motivates separating curriculum-selection signals from measured learning; our answer keys check extraction correctness.
- [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](https://arxiv.org/abs/2505.03335) (Zhao et al., 2025). Combines task proposal and executable verification in a training loop; this experiment stops before training.
- [Deduplicating Training Data Makes Language Models Better](https://aclanthology.org/2022.acl-long.577/) (Lee et al., 2022). Explains why repeated records and split overlap need explicit accounting when preparing data.
- [Self-Instruct: Aligning Language Models with Self-Generated Instructions](https://aclanthology.org/2023.acl-long.754/) (Wang et al., 2023). An earlier example of generating instruction examples and filtering invalid or similar items.
'''
notebook['cells'][-1]['source'] = future.splitlines(keepends=True)

def cell(source, kind='markdown'):
    result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True),
              'id': 'high-parent-' + hashlib.sha256(source.encode()).hexdigest()[:12]}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result

knobs = '''# Default execution only reads caches and audits saved sources.
HIGH_V4_LIVE = False
N_HIGH_LIVE_PILOT_CASES = 2  # At most four levels: eight new calls at this setting.
HIGH_V4_MODELS = ["gpt-6.1-sol"]
'''
notebook['cells'].insert(4, cell(knobs, 'code'))
audit_code = '''# Recompute every potential main target from saved model-visible text.
import gzip
import hashlib
import json
HIGH_PREFLIGHT_DIR = Path.cwd() / "data" / "high_v4" / "preflight"
HIGH_PREFLIGHT_MANIFEST = json.loads((HIGH_PREFLIGHT_DIR / "manifest.json").read_text(encoding="utf-8"))
HIGH_AUDITED_CASES = 0
for block in HIGH_PREFLIGHT_MANIFEST["levels"]:
    packed = (HIGH_PREFLIGHT_DIR / block["file"]).read_bytes()
    assert hashlib.sha256(packed).hexdigest() == block["compressed_sha256"]
    raw = gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest() == block["uncompressed_sha256"]
    for line in raw.decode("utf-8").splitlines():
        source_case = json.loads(line)
        derived, trace = high_material_answer(source_case["document"])
        assert derived == source_case["gold"], source_case["case_id"]
        HIGH_AUDITED_CASES += 1
assert HIGH_AUDITED_CASES == 1056
print("Independent SQL/Decimal reconstruction matched", HIGH_AUDITED_CASES, "saved main targets.")
print("These are solvability checks, not predictions or model accuracy.")
'''
smoke = '''# Optional new, bounded pilot only. Never resume or overwrite the saved attempts.
if HIGH_V4_LIVE:
    import uuid
    assert HIGH_V4_MODELS == ["gpt-6.1-sol"]
    assert 1 <= N_HIGH_LIVE_PILOT_CASES <= 8
    HIGH_NEW_ROOT = Path.cwd() / "data" / "tmp" / ("high_smoke_" + uuid.uuid4().hex[:12])
    HIGH_SMALL_CONFIG = {**HIGH_PILOT_CONFIG, "n_cases": N_HIGH_LIVE_PILOT_CASES,
                         "min_value_failures": min(3, N_HIGH_LIVE_PILOT_CASES)}
    HIGH_NEW_PILOT = high_run_pilot(config=HIGH_SMALL_CONFIG, root=HIGH_NEW_ROOT, live=True)
else:
    print("No new CLI calls. HIGH_V4_LIVE is False.")
'''
extra = [cell('### Recompute all saved source targets\n\nThe independent SQL/Decimal reader works directly from the saved text. This cell checks every potential main packet again, including those never sent to Sol. It prints a count rather than treating correct answer keys as model successes.'),
         cell(audit_code, 'code'),
         cell('### Optional small live pilot\n\nThe size knob near the top defaults to two cases per level and live calls are disabled. Setting HIGH_V4_LIVE to True creates a fresh, isolated pilot under data/tmp/, with at most eight requests at the default size. It stops on a service failure. This smoke test changes the pilot size and is not a replay or replication of the full planned comparison. Main originals and paired interventions remain separate explicit phases.'),
         cell(smoke, 'code')]
notebook['cells'][-1:-1] = extra
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')

readme_path = folder / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
prefix = readme.split('## 13. Future work and further reading')[0]
prefix = prefix.replace('The latest follow-up adds 48', 'The third follow-up adds 48')
prefix = prefix.replace('## Contents', headline + '\n\n## Contents', 1)
prefix = prefix.replace('- [13. Future work and further reading](#13-future-work-and-further-reading)',
    '- [13. Larger source packs and higher reasoning](#13-larger-source-packs-and-higher-reasoning)\n- [14. Future work and further reading](#14-future-work-and-further-reading)')
reproduction = '''
### Replaying the saved evidence

Normal execution of [the notebook](23_synthetic_data_curation.ipynb) replays the three completed historical protocols, reads the incomplete high-reasoning requests, recreates the figures and recomputes all 1,056 main targets from saved source text. It makes no model calls. The optional HIGH_V4_LIVE knob defaults to False; its small fresh pilot has a separate output folder and does not resume these failed requests.

```powershell
python -m nbconvert --to notebook --execute --inplace 23_synthetic_data_curation.ipynb
python -m unittest discover -s data/high_v4/source_snapshot -p "test_high*.py"
```

The 29 tests check source solvability, hand calculations, request isolation, field-only feedback, paired analysis and stopping on service failures. [Provenance](data/high_v4/provenance.json), [the artifact audit](data/high_v4/artifact_audit.json) and [the source index](data/high_v4/preflight/manifest.json) connect these claims to the saved materials. Failed or pending requests are retained; their unavailable token usage is not treated as zero.
'''
readme_path.write_text(prefix.rstrip() + '\n\n' + proposal['readme_appendix'] + '\n' + reproduction + '\n' + future,
                       encoding='utf-8', newline='\n')
root_path = repo / 'README.md'
root_text = root_path.read_text(encoding='utf-8')
lines = root_text.splitlines()
for i, line in enumerate(lines):
    if line.startswith('| 23 |'):
        lines[i] = ('| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | '
            'Generated extraction examples need correct values and inspectable evidence. Three completed protocols compare selection and repairs; the latest plan uses high-reasoning Sol on longer procurement histories, with 32 pilot and 1,056 possible main packets independently checked before calls. Can feedback repair beat a fresh retry on genuine misses? | '
            'V3 Sol answered 45/48 collection and 12/12 audit cases correctly; fresh Sol retry and feedback repair each fixed its 3 misses, while Luna repair fixed 0/3. The larger high-reasoning pilot was interrupted: 31 request records contain 3 correct answers, 24 HTTP429 service failures and 4 pending records. All 1,088 source packets pass independent audits, but no higher-reasoning difficulty level or paired comparison was measured. No model was trained. |')
    if line.startswith('* Notebook 23 replays'):
        lines[i] = ('* Notebook 23 replays 262 completed historical CLI requests and inspects 31 higher-reasoning request records offline, including service errors and interrupted attempts. It also recomputes all 1,056 potential main targets from saved text. Live knobs default off; small fresh runs use isolated ignored data/tmp/ folders.')
    if line.startswith('Notebook 23 uses fictional order threads'):
        lines[i] = ('Notebook 23 uses fictional order threads generated in code on 2026-10-24 and procurement packets generated on 2026-10-26. Source text, exact answer keys and available model responses are saved for inspection. It demonstrates data curation without training. Its [latest provenance record](notebooks/23-synthetic-data-curation/data/high_v4/provenance.json) records source audits and service interruptions; generated outputs do not carry a claim of unrestricted downstream training permission.')
root_path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'notebook_cells': len(notebook['cells']), 'state': proposal['state'], 'figures_created': True}))
