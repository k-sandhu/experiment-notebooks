"""Read-only request-key regression check for SPEC_PATCH_WORDING.md.

Run `python build/check_patch_wording.py snapshot` before editing nb38.py, then
`python build/check_patch_wording.py compare`. Only build/ artifacts are written.
Definitions are loaded through the AST; collection and notebook tests never run.
`python build/check_patch_wording.py prompts` regenerates the eight example prompts.
"""
import ast
from collections import Counter
import csv
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = Path.cwd()
BUILD = ROOT / 'build'
AUDIT = BUILD / '.patch_wording'
SOURCE = BUILD / 'nb38.py'
ORIGINAL_FORMATS = ['full', 'search_replace', 'json_replace', 'udiff', 'apply_patch', 'line_edits', 'sketch']
CONSTANTS = set('MODELS ALL_MODELS MERGE_MODEL EFFORT MERGE_EFFORT PROTOCOL SYSTEM FORMATS '
                'FORMAT_INSTRUCTIONS DOUBLE_QUOTES PLAIN_PAIRS RENAME_PAIRS FAILURE_REASONS '
                'PUNCT_TRANSLATION REFERENCE_TRANSLATION SKIP_MARKER APPLIERS STRICT EDIT_KINDS '
                'MAIN_PIPELINES FORMAT_LABELS METHOD_ORDER'.split())


def load_definitions(source):
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))
             or isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id in CONSTANTS for t in n.targets)]
    module = types.ModuleType('_nb38_key_check')
    sys.modules[module.__name__] = module
    ns = module.__dict__
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
    ns['ROOT'], ns['DATA'] = ROOT, ROOT / 'data'
    ns['CATALOG'] = json.loads((ns['DATA'] / 'model_catalog.json').read_text(encoding='utf-8'))['models']
    with (ns['DATA'] / 'documents.csv').open(encoding='utf-8', newline='') as f:
        docs = list(csv.DictReader(f))
    ns['DOCUMENTS'] = {d['document_number']: {**d, 'text': (ns['DATA'] / 'documents' /
                        (d['document_number'] + '.md')).read_bytes().decode('utf-8')} for d in docs}
    ns['TASKS'] = [json.loads(line) for line in (ns['DATA'] / 'tasks.jsonl').read_text(encoding='utf-8').splitlines()]
    ns['GIT_EXE'] = shutil.which('git')
    ns['PATCH_EXE'] = shutil.which('patch')
    if not ns['PATCH_EXE'] and os.name == 'nt' and ns['GIT_EXE']:
        candidate = Path(ns['GIT_EXE']).parent.parent.parent / 'usr/bin/patch.exe'
        ns['PATCH_EXE'] = str(candidate) if candidate.exists() else None
    ns['GIT_VERSION'] = subprocess.run([ns['GIT_EXE'], '--version'], capture_output=True, text=True).stdout.strip() if ns['GIT_EXE'] else None
    ns['PATCH_VERSION'] = subprocess.run([ns['PATCH_EXE'], '--version'], capture_output=True, text=True).stdout.splitlines()[0] if ns['PATCH_EXE'] else None
    return ns


def cache_rows():
    rows = {}
    for path in (ROOT / 'data').glob('cache_*.jsonl'):
        # A live append can leave an incomplete final record; take complete records only.
        raw = path.read_bytes()
        for line in raw[:raw.rfind(b'\n') + 1].splitlines():
            row = json.loads(line)
            rows[row['key']] = row
    return rows


def build_keys(ns, rows):
    keys, strict_results = {}, {}
    tasks = {t['task_id']: t for t in ns['TASKS']}
    assert len(tasks) == 36 and len(ns['ALL_MODELS']) == 5
    for task in tasks.values():
        for fmt in ORIGINAL_FORMATS:
            for label in ns['ALL_MODELS']:
                context = {'stage': 'generation', 'task_id': task['task_id'], 'format': fmt, 'source_model': label}
                request = ns['make_request'](label, ns['make_prompt'](task, fmt), context=context)
                keys['generation|' + '|'.join((label, fmt, task['task_id']))] = ns['digest'](request)
    for key, row in rows.items():
        request, response = row['request'], row['response']
        assert ns['digest'](request) == key
        rebuilt = ns['make_request'](request['label'], request['prompt'], request['effort'], request['context'])
        assert ns['digest'](rebuilt) == key, ('cached request reconstruction', key)
        context = request['context']
        if request['protocol'] != ns['PROTOCOL'] or context.get('stage') != 'generation':
            continue
        fmt, task_id, label = context['format'], context['task_id'], context['source_model']
        if fmt not in ORIGINAL_FORMATS:
            continue
        task = tasks[task_id]
        original = ns['DOCUMENTS'][task['document']]['text']
        identity = '|'.join((label, fmt, task_id))
        previous = {'task_id': task_id, 'format': fmt, 'source_model': label,
                    'previous_reply_sha256': ns['digest'](response)}
        if fmt in ns['STRICT']:
            result = ns['response_application'](original, response, ns['APPLIERS'][fmt][ns['STRICT'][fmt]])
            strict_results[identity] = ns['digest'](asdict(result))
            if ns['strict_failed'](result):
                retry = ns['make_request'](label, ns['retry_prompt'](task, fmt, response.get('text', ''), result),
                                           context={**previous, 'stage': 'retry'})
                keys['retry|' + identity] = ns['digest'](retry)
        if fmt in ns['EDIT_KINDS'] and not response.get('error') and (response.get('text') or '').strip():
            merge = ns['make_request'](ns['MERGE_MODEL'][0], ns['merge_prompt'](original, response['text'], fmt),
                                       ns['MERGE_EFFORT'], context={**previous, 'stage': 'merge'})
            keys['merge|' + identity] = ns['digest'](merge)
    # Every collected later-stage request must also match the newly built prompt and trigger.
    for key, row in rows.items():
        request = row['request']
        c = request['context']
        if request['protocol'] == ns['PROTOCOL'] and c.get('stage') in {'retry', 'merge'}:
            identity = '|'.join((c['stage'], c['source_model'], c['format'], c['task_id']))
            assert keys[identity] == key, ('cached later-stage request', identity)
    return {'keys': keys, 'strict_results': strict_results}


def main():
    assert os.environ.get('NB_LIVE') != '1', 'Run this check with NB_LIVE disabled.'
    AUDIT.mkdir(exist_ok=True)
    os.environ['TMP'] = os.environ['TEMP'] = str(AUDIT)
    os.environ['MPLCONFIGDIR'] = str(AUDIT / 'mplconfig')
    tempfile.tempdir = str(AUDIT)
    mode = sys.argv[1]
    baseline_path = AUDIT / 'before.json'
    if mode == 'snapshot':
        assert not baseline_path.exists(), 'The before-edit snapshot already exists.'
        source = SOURCE.read_bytes()
        (AUDIT / 'nb38_before.py.txt').write_bytes(source)
        rows = cache_rows()
        result = build_keys(load_definitions(source.decode('utf-8')), rows)
        result['cache_keys'] = sorted(rows)
        result['source_sha256'] = hashlib.sha256(source).hexdigest()
        baseline_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Before-edit request hashes:', dict(Counter(k.split('|')[0] for k in result['keys'])))
        print(f'Frozen read-only cache snapshot: {len(rows)} records; {len(result["strict_results"])} strict results.')
    elif mode == 'compare':
        before = json.loads(baseline_path.read_text(encoding='utf-8'))
        all_rows = cache_rows()
        rows = {key: all_rows[key] for key in before['cache_keys']}
        ns = load_definitions(SOURCE.read_text(encoding='utf-8'))
        instructions = (BUILD / 'SPEC_PATCH_WORDING.md').read_text(encoding='utf-8').split('```\n', 1)[1].split('\n```', 1)[0]
        assert ns['FORMAT_INSTRUCTIONS']['apply_patch_openai'] == instructions, 'New instructions must match the spec verbatim.'
        assert ns['FORMATS'] == ORIGINAL_FORMATS + ['apply_patch_openai']
        after = build_keys(ns, rows)
        for kind in ('keys', 'strict_results'):
            assert before[kind] == after[kind], (kind, [key for key in before[kind]
                if before[kind][key] != after[kind].get(key)][:10])
        counts = dict(Counter(k.split('|')[0] for k in after['keys']))
        assert counts['generation'] == 36 * 7 * 5
        report = (f'Request-key comparison: {counts}; all identical before/after.\n'
                  f'Cached request reconstruction: {len(rows)} identical keys.\n'
                  f'Existing strict results: {len(after["strict_results"])} identical before/after.\n')
        (BUILD / 'patch_wording_key_comparison.txt').write_text(report, encoding='utf-8', newline='\n')
        print(report, end='')
    elif mode == 'prompts':
        ns = load_definitions(SOURCE.read_text(encoding='utf-8'))
        shortest = min(ns['DOCUMENTS'].values(), key=lambda d: int(d['words']))
        task = next(t for t in ns['TASKS'] if t['document'] == shortest['document_number'] and t['bundle'] == 'mixed6')
        header = ('# Rendered prompts for the shortest document\n\n'
                  'These are the exact generation prompts, with the complete frozen document.\n\n'
                  f'Task: `{task["task_id"]}`. Document: {int(shortest["words"]):,} words. '
                  'System text is identical for every format:\n\n' + ns['SYSTEM'] + '\n\n')
        prompts = ''.join(f'## {fmt}\n\n````text\n{ns["make_prompt"](task, fmt)}\n````\n\n' for fmt in ns['FORMATS'])
        (BUILD / 'example_prompts.md').write_text(header + prompts, encoding='utf-8', newline='\n')
        print(f'Example prompts: {len(ns["FORMATS"])} rendered for {task["task_id"]}.')
    else:
        raise ValueError('Expected snapshot, compare or prompts.')


if __name__ == '__main__':
    main()
