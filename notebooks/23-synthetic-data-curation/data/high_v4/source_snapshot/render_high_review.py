"""Render code-hidden notebook and standalone README for a local visual review."""
import json
import re
from pathlib import Path
import mistune
import nbformat
from nbconvert import HTMLExporter
from bs4 import BeautifulSoup

base = Path(__file__).resolve().parent
folder = base.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
output = folder / 'data/tmp/high_review'
output.mkdir(parents=True, exist_ok=True)
notebook = nbformat.read(folder / '23_synthetic_data_curation.ipynb', as_version=4)
exporter = HTMLExporter(exclude_input=True, embed_images=True)
notebook_html, _ = exporter.from_notebook_node(notebook, resources={'metadata': {'path': str(folder)}})
markdown = mistune.create_markdown(escape=False, plugins=['table', 'url', 'strikethrough'])
body = markdown((folder / 'README.md').read_text(encoding='utf-8'))
style = '''body{font-family:system-ui,sans-serif;line-height:1.6;max-width:1000px;margin:40px auto;padding:0 24px;color:#17232d} img{max-width:100%;height:auto} table{border-collapse:collapse;width:100%;font-size:14px} th,td{border:1px solid #ccd4db;padding:7px;text-align:left} th{background:#f0f4f7} pre{background:#f4f6f8;padding:14px;overflow:auto} h2{margin-top:46px} details{margin:18px 0} code{overflow-wrap:anywhere} a{color:#2266a0}'''
readme_html = '<!doctype html><html><head><meta charset="utf-8"><title>Notebook 23 README review</title><style>'+style+'</style></head><body>'+body+'</body></html>'


def prepare_html(text, add_ids=False):
    soup = BeautifulSoup(text, 'html.parser')
    if add_ids:
        for heading in soup.select('h1,h2,h3,h4,h5,h6'):
            slug = re.sub(r'[^\w\- ]', '', heading.get_text().strip().lower())
            heading['id'] = re.sub(r' +', '-', slug)
    for image in soup.select('img[src]'):
        if image['src'].startswith('figures/'):
            image['src'] = '/' + image['src']
    return str(soup)


notebook_html = prepare_html(notebook_html)
readme_html = prepare_html(readme_html, add_ids=True)
(output / 'notebook.html').write_text(notebook_html, encoding='utf-8', newline='\n')
(output / 'README.html').write_text(readme_html, encoding='utf-8', newline='\n')
checks = {}
for label, text in [('notebook', notebook_html), ('readme', readme_html)]:
    soup = BeautifulSoup(text, 'html.parser')
    anchors = {tag['id'] for tag in soup.select('[id]')}
    local_links = [tag['href'] for tag in soup.select('a[href]') if tag['href'].startswith('#')]
    checks[label] = {'headings': [tag.get_text().strip() for tag in soup.select('h2')],
                     'broken_in_page_links': sorted(set(link for link in local_links if link[1:] not in anchors)),
                     'images': len(soup.select('img')), 'details_blocks': len(soup.select('details'))}
(base / 'high_rendered_review_checks.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(checks, indent=2))
