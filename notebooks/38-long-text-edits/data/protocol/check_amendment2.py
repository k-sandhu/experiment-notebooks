"""Offline Amendment 2 regression check. Snapshot before editing; compare after.

Only snapshot/compare artifacts under build/.amendment2 are written. Live caches
are read as complete JSONL records and frozen by key, so later appends are harmless.
No applier or model is called when reconstructing generation and merge requests.
"""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from check_patch_wording import cache_rows, load_definitions

ROOT = Path.cwd()
BUILD = ROOT / 'build'
AUDIT = BUILD / '.amendment2'
SOURCE = BUILD / 'nb38.py'


def request_keys(ns, rows):
    keys = {}
    tasks = {t['task_id']: t for t in ns['TASKS']}
    assert len(tasks) == 36 and len(ns['FORMATS']) == 8 and len(ns['ALL_MODELS']) == 5
    for task in tasks.values():
        for fmt in ns['FORMATS']:
            for label in ns['ALL_MODELS']:
                context = {'stage': 'generation', 'task_id': task['task_id'], 'format': fmt, 'source_model': label}
                request = ns['make_request'](label, ns['make_prompt'](task, fmt), context=context)
                keys['generation|' + '|'.join((label, fmt, task['task_id']))] = ns['digest'](request)
    for key, row in rows.items():
        q, response = row['request'], row['response']
        assert ns['digest'](q) == key
        assert ns['digest'](ns['make_request'](q['label'], q['prompt'], q['effort'], q['context'])) == key
        c = q['context']
        if q['protocol'] != ns['PROTOCOL'] or c.get('stage') != 'generation':
            continue
        fmt, task_id, label = c['format'], c['task_id'], c['source_model']
        assert keys['generation|' + '|'.join((label, fmt, task_id))] == key
        if fmt in ns['EDIT_KINDS'] and not response.get('error') and (response.get('text') or '').strip():
            context = {'task_id': task_id, 'format': fmt, 'source_model': label,
                       'previous_reply_sha256': ns['digest'](response), 'stage': 'merge'}
            original = ns['DOCUMENTS'][tasks[task_id]['document']]['text']
            request = ns['make_request'](ns['MERGE_MODEL'][0], ns['merge_prompt'](original, response['text'], fmt),
                                         ns['MERGE_EFFORT'], context=context)
            keys['merge|' + '|'.join((label, fmt, task_id))] = ns['digest'](request)
    for key, row in rows.items():
        q, c = row['request'], row['request']['context']
        if q['protocol'] == ns['PROTOCOL'] and c.get('stage') == 'merge':
            assert keys['merge|' + '|'.join((c['source_model'], c['format'], c['task_id']))] == key
    return keys


def main():
    assert os.environ.get('NB_LIVE') != '1'
    mode = sys.argv[1]
    AUDIT.mkdir(exist_ok=True)
    os.environ['TMP'] = os.environ['TEMP'] = str(AUDIT)
    os.environ['MPLCONFIGDIR'] = str(AUDIT / 'mplconfig')
    tempfile.tempdir = str(AUDIT)
    before_path = AUDIT / 'before.json'
    if mode == 'snapshot':
        assert not before_path.exists(), 'Never replace the before-edit snapshot.'
        source = SOURCE.read_bytes()
        (AUDIT / 'nb38_before.py.txt').write_bytes(source)
        rows = cache_rows()
        ns = load_definitions(source.decode('utf-8'))
        keys = request_keys(ns, rows)
        paths = ['tasks.jsonl', 'frozen_manifest.json'] + [
            str(p.relative_to(ROOT / 'data')).replace('\\', '/') for p in (ROOT / 'data/expected').glob('*.md')]
        originals = {p: (ROOT / 'data' / p).read_bytes().decode('utf-8') for p in paths}
        before = {'keys': keys, 'cache_keys': sorted(rows), 'originals': originals,
                  'source_sha256': hashlib.sha256(source).hexdigest()}
        before_path.write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Before-edit request hashes:', dict(Counter(k.split('|')[0] for k in keys)))
        print(f'Frozen read-only cache snapshot: {len(rows)} complete records.')
    elif mode == 'compare':
        before = json.loads(before_path.read_text(encoding='utf-8'))
        current_rows = cache_rows()
        rows = {k: current_rows[k] for k in before['cache_keys']}
        old_ns = load_definitions((AUDIT / 'nb38_before.py.txt').read_text(encoding='utf-8'))
        old_ns['TASKS'] = [json.loads(s) for s in before['originals']['tasks.jsonl'].splitlines()]
        ns = load_definitions(SOURCE.read_text(encoding='utf-8'))
        # The merge prompt/request builders are identical for any reply, including
        # replies appended after this fixed cache snapshot was taken.
        protected = {'make_prompt', 'make_request', 'cli_options', 'merge_prompt',
                     'FORMAT_INSTRUCTIONS', 'SYSTEM', 'PROTOCOL', 'EFFORT', 'MERGE_EFFORT',
                     'MODELS', 'ALL_MODELS', 'MERGE_MODEL', 'EDIT_KINDS', 'FORMATS'}
        def definitions(source):
            result = {}
            for node in ast.parse(source).body:
                names = ([node.name] if isinstance(node, ast.FunctionDef) else
                         [t.id for t in node.targets if isinstance(t, ast.Name)] if isinstance(node, ast.Assign) else [])
                for name in set(names) & protected:
                    result[name] = ast.dump(node, include_attributes=False)
            return result
        assert definitions((AUDIT / 'nb38_before.py.txt').read_text(encoding='utf-8')) == definitions(
            SOURCE.read_text(encoding='utf-8')), 'A prompt builder or request setting changed.'
        def collection_cells(source):
            return [ast.dump(node, include_attributes=False) for node in ast.parse(source).body
                    if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'RUN_CALLS']
        assert collection_cells((AUDIT / 'nb38_before.py.txt').read_text(encoding='utf-8')) == collection_cells(
            SOURCE.read_text(encoding='utf-8')), 'A collection cell changed.'
        old_keys, new_keys = request_keys(old_ns, rows), request_keys(ns, rows)
        assert before['keys'] == old_keys == new_keys, 'A generation or merge request key changed.'
        target = '2026-21300_rename'
        changed = []
        for relative, text in before['originals'].items():
            if relative.startswith('expected/'):
                if (ROOT / 'data' / relative).read_bytes() != text.encode('utf-8'):
                    changed.append(relative)
        assert changed == [f'expected/{target}.md'], changed
        assert (ROOT / 'data/expected_v1' / (target + '.md')).read_bytes() == before['originals'][changed[0]].encode('utf-8')
        old_tasks = {t['task_id']: t for t in old_ns['TASKS']}
        old_lines = before['originals']['tasks.jsonl'].splitlines(keepends=True)
        new_lines = (ROOT / 'data/tasks.jsonl').read_bytes().decode('utf-8').splitlines(keepends=True)
        assert len(old_lines) == len(new_lines) == 36
        assert [json.loads(old)['task_id'] for old, new in zip(old_lines, new_lines) if old != new] == [target]
        for task in ns['TASKS']:
            old = old_tasks[task['task_id']]
            if task['task_id'] != target:
                assert old == task
            else:
                assert task['instructions'] == old['instructions']
                for field in old:
                    if field not in {'edits', 'expected_sha256'}:
                        assert task[field] == old[field], field
                assert [{k: v for k, v in e.items() if k not in {'check', 'count'}} for e in task['edits']] == [
                    {k: v for k, v in e.items() if k not in {'check', 'count'}} for e in old['edits']]
                original = ns['DOCUMENTS'][task['document']]['text']
                expected = ns['expected_document'](original, task['edits'])
                assert expected == (ROOT / 'data/expected' / (target + '.md')).read_bytes().decode('utf-8')
                assert ns['sha'](expected) == task['expected_sha256']
                assert ns['check_edit'](expected, task['edits'][0]['check'])
                assert task['edits'][0]['count'] == old['edits'][0]['count'] + 23
        manifest = json.loads((ROOT / 'data/frozen_manifest.json').read_text(encoding='utf-8'))
        for relative, expected_hash in manifest['sha256'].items():
            assert hashlib.sha256((ROOT / 'data' / relative).read_bytes()).hexdigest() == expected_hash, relative
        old_manifest = json.loads(before['originals']['frozen_manifest.json'])
        assert {p for p in old_manifest['sha256'] if old_manifest['sha256'][p] != manifest['sha256'][p]} == {
            'tasks.jsonl', f'expected/{target}.md'}
        assert set(manifest['sha256']) - set(old_manifest['sha256']) == {f'expected_v1/{target}.md'}
        report = (f'Request-key comparison: {dict(Counter(k.split("|")[0] for k in new_keys))}; all identical before/after.\n'
                  f'Cached request reconstruction: {len(rows)} identical keys.\n'
                  'Prompt builders/settings unchanged, including merges for later collection appends.\n'
                  'Expected documents: 35 byte-identical; only 2026-21300_rename changed; old version preserved.\n'
                  'Task instructions unchanged; rename check includes 23 plural occurrences; frozen manifest verified.\n')
        (BUILD / 'amendment2_key_comparison.txt').write_text(report, encoding='utf-8', newline='\n')
        print(report, end='')
    else:
        raise ValueError('Expected snapshot or compare.')


if __name__ == '__main__':
    main()
