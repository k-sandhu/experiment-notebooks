"""Record opened canonical further-reading links and verified citation metadata."""
import json
from datetime import datetime, timezone
from pathlib import Path

destination = Path(__file__).parent.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation/data/high_v4/reference_checks.json'
rows = [
    ('https://arxiv.org/abs/2310.01798', 'Large Language Models Cannot Self-Correct Reasoning Yet', 'Huang et al.', 2024),
    ('https://arxiv.org/abs/2605.14392', 'Learning to Build the Environment: Self-Evolving Reasoning RL via Verifiable Environment Synthesis', 'Shi et al.', 2026),
    ('https://arxiv.org/abs/2610.09856', 'Self-Evolve With a Reference: Anchored Training of Tool-Integrated Agents', 'Liao et al.', 2026),
    ('https://arxiv.org/abs/2505.03335', 'Absolute Zero: Reinforced Self-play Reasoning with Zero Data', 'Zhao et al.', 2025),
    ('https://aclanthology.org/2022.acl-long.577/', 'Deduplicating Training Data Makes Language Models Better', 'Lee et al.', 2022),
    ('https://aclanthology.org/2023.acl-long.754/', 'Self-Instruct: Aligning Language Models with Self-Generated Instructions', 'Wang et al.', 2023),
]
payload = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
           'method': 'Opened each canonical abstract/Anthology page with the web tool; checked title, authors, year and relevance against its abstract.',
           'references': [dict(zip(('url', 'title', 'author_label', 'year'), row)) for row in rows]}
destination.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Saved canonical reference checks:', len(rows))
