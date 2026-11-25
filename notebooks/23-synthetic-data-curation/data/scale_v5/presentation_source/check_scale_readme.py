"""Check the finished reader-facing files without changing experiment data."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

BASE = Path(__file__).resolve().parent
_PORTABLE_ROOT = BASE.parents[2]
ROOT = (_PORTABLE_ROOT if (_PORTABLE_ROOT / 'data/scale_v5/main/protocol.json').is_file()
        else BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation')


def prose(text):
    return re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)


def headings(text):
    return re.findall(r'^## (\d+)\. ([^\n]+)', prose(text), re.M)


def anchor(text):
    return re.sub(r'[^\w-]', '', text.lower().replace(' ', '-'))


def main():
    # Operator metadata and the reporting marker precede any artifact read.
    status = json.loads((ROOT / 'data/scale_v5/main/continuation_006_receipts/manifest_metadata.json').read_bytes())
    assert status['completion_gate']['complete'] and status['finished_receipt_return_code'] == 0
    assert status['scheduled_arm_slots'] == 1200 and status['terminal_arm_records'] == 1191
    assert status['pending_arm_slots'] == 9 and status['unrecorded_arm_slots'] == 0
    marker = BASE / 'scale_presentation_finalization_complete.json'
    if not marker.is_file():
        marker = ROOT / 'data/scale_v5/presentation_results/finalization.json'
    assert marker.is_file()
    readme_path = ROOT / 'README.md'
    raw = readme_path.read_bytes()
    assert 25000 <= len(raw) <= 50000, len(raw)
    text = raw.decode('utf-8')
    reader = prose(text)
    numbered = headings(text)
    assert [int(number) for number, _ in numbered] == list(range(1, 11)), numbered
    assert numbered[-1][1] == 'Future work and further reading'
    assert text.count('## The study in brief') == 1
    intro = text.split('## The study in brief', 1)[0]
    assert not re.search(r'\b(?:GPT|Sol|Luna|Codex)\b', intro)
    paragraphs = [part for part in re.split(r'\n\s*\n', intro) if part.strip() and not part.lstrip().startswith('#')]
    assert 6 <= len(paragraphs) <= 10, len(paragraphs)
    assert len(set(re.findall(r'^#### Case (\d+):', text, re.M))) >= 5
    figure_links = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
    assert len(figure_links) == 8, figure_links
    anchors = {anchor(match) for match in re.findall(r'^#{1,6} (.+)', reader, re.M)}
    broken = []
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        target = target.strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue
        if not parsed.path:
            if parsed.fragment and unquote(parsed.fragment) not in anchors:
                broken.append(target)
        elif not (ROOT / unquote(parsed.path)).is_file():
            broken.append(target)
    assert not broken, broken
    notebook = json.loads((ROOT / '23_synthetic_data_curation.ipynb').read_bytes())
    markdown = '\n\n'.join(''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'markdown')
    assert headings(markdown) == numbered
    assert markdown.startswith(intro.rstrip())
    style = re.findall(r"\b(?:delve|tapestry|testament|intricate|meticulous(?:ly)?|pivotal|crucial|robust|seamless(?:ly)?|leverage|unlock|underscore|showcase|realm|landscape|game-changer|cutting-edge|groundbreaking|transformative|holistic|multifaceted|comprehensive|furthermore|moreover|additionally|notably)\b|—", reader, re.I)
    report = dict(passed=True, readme_bytes=len(raw), introductory_paragraphs=len(paragraphs),
                  numbered_sections=10, measured_examples=len(set(re.findall(r'^#### Case (\d+):', text, re.M))),
                  figures=8, broken_local_links=broken, style_hits_for_manual_review=style,
                  readme_sha256=hashlib.sha256(raw).hexdigest(),
                  notebook_markdown_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
                  checker_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  model_calls=0, note='Structure and local links checked automatically; interpretation and figures require reader review.')
    (BASE / 'scale_readme_final_review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
