"""Freeze and compare all Amendment 3 request keys without collecting or writing results.

Complete cache records are frozen by key before editing, independent of live appends.
Only build/.amendment3 and the comparison report are written by this checker.
"""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile
import sys

import check_patch_wording as checks

ROOT = Path.cwd()
BUILD = ROOT / 'build'
AUDIT = BUILD / '.amendment3'
SOURCE = BUILD / 'nb38.py'
TARGET = '2026-22093_rename'


def request_keys(ns, rows):
    checks.ORIGINAL_FORMATS = ns['FORMATS']
    assert len(checks.ORIGINAL_FORMATS) == 8
    return checks.build_keys(ns, rows)


def protected_nodes(source):
    # Only these existing functions are changed by this scoring amendment.
    changed = {'score_result', 'run_oracle_tests', 'run_instrument_unit_tests',
               'run_pipeline_table_tests', 'rename_rule_comparison', 'case'}
    result = {}
    collections = 0
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name not in changed:
            result[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result['assign:' + target.id] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'RUN_CALLS':
            result['collection:' + str(collections)] = ast.dump(node, include_attributes=False)
            collections += 1
    return result


def main():
    assert os.environ.get('NB_LIVE') != '1'
    AUDIT.mkdir(exist_ok=True)
    os.environ['TMP'] = os.environ['TEMP'] = str(AUDIT)
    os.environ['MPLCONFIGDIR'] = str(AUDIT / 'mplconfig')
    tempfile.tempdir = str(AUDIT)
    before_path = AUDIT / 'before.json'
    if sys.argv[1] == 'snapshot':
        assert not before_path.exists(), 'Never replace the before-edit snapshot.'
        source = SOURCE.read_bytes()
        (AUDIT / 'nb38_before.py.txt').write_bytes(source)
        rows = checks.cache_rows()
        result = request_keys(checks.load_definitions(source.decode('utf-8')), rows)
        paths = ['tasks.jsonl', 'frozen_manifest.json'] + [
            str(p.relative_to(ROOT / 'data')).replace('\\', '/')
            for p in (ROOT / 'data/expected').glob('*.md')]
        result.update(cache_keys=sorted(rows), source_sha256=hashlib.sha256(source).hexdigest(),
                      originals={p: (ROOT / 'data' / p).read_bytes().decode('utf-8') for p in paths})
        before_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Before-edit request hashes:', dict(Counter(k.split('|')[0] for k in result['keys'])))
        print(f'Frozen read-only cache snapshot: {len(rows)} complete records.')
        return
    assert sys.argv[1] == 'compare'
    before = json.loads(before_path.read_text(encoding='utf-8'))
    all_rows = checks.cache_rows()
    rows = {key: all_rows[key] for key in before['cache_keys']}
    old_source = (AUDIT / 'nb38_before.py.txt').read_text(encoding='utf-8')
    new_source = SOURCE.read_text(encoding='utf-8')
    old_ns, ns = checks.load_definitions(old_source), checks.load_definitions(new_source)
    old_ns['TASKS'] = [json.loads(s) for s in before['originals']['tasks.jsonl'].splitlines()]
    protected_old, protected_new = protected_nodes(old_source), protected_nodes(new_source)
    assert all(protected_new.get(k) == v for k, v in protected_old.items()), 'Protected settings/code changed.'
    new = request_keys(ns, rows)
    for field in ['keys', 'strict_results']:
        assert before[field] == new[field], field
    for relative, contents in before['originals'].items():
        if relative.startswith('expected/'):
            assert (ROOT / 'data' / relative).read_bytes() == contents.encode('utf-8'), relative
    old_lines = before['originals']['tasks.jsonl'].splitlines(keepends=True)
    new_lines = (ROOT / 'data/tasks.jsonl').read_bytes().decode('utf-8').splitlines(keepends=True)
    assert len(old_lines) == len(new_lines) == 36
    assert [json.loads(a)['task_id'] for a, b in zip(old_lines, new_lines) if a != b] == [TARGET]
    for task, previous in zip(ns['TASKS'], old_ns['TASKS']):
        assert {k: v for k, v in task.items() if k != 'accepted_alternatives'} == previous
        if task['task_id'] != TARGET:
            assert 'accepted_alternatives' not in task
    task = next(t for t in ns['TASKS'] if t['task_id'] == TARGET)
    filename = 'expected_alt/' + TARGET + '.md'
    primary = before['originals']['expected/' + TARGET + '.md']
    assert primary.count('%20FEVS%20') == 1
    alternative = (ROOT / 'data' / filename).read_bytes()
    assert alternative == primary.replace('%20FEVS%20', '%20FEVA%20').encode('utf-8')
    assert task['accepted_alternatives'] == [{'file': filename, 'sha256': hashlib.sha256(alternative).hexdigest()}]
    manifest = json.loads((ROOT / 'data/frozen_manifest.json').read_text(encoding='utf-8'))
    previous_manifest = json.loads(before['originals']['frozen_manifest.json'])
    assert {p for p in previous_manifest['sha256'] if previous_manifest['sha256'][p] != manifest['sha256'][p]} == {'tasks.jsonl'}
    assert set(manifest['sha256']) - set(previous_manifest['sha256']) == {filename}
    assert {k: v for k, v in manifest.items() if k != 'sha256'} == {
        k: v for k, v in previous_manifest.items() if k != 'sha256'}
    for relative, expected_hash in manifest['sha256'].items():
        assert hashlib.sha256((ROOT / 'data' / relative).read_bytes()).hexdigest() == expected_hash, relative
    report = (f'Request-key comparison: {dict(Counter(k.split("|")[0] for k in new["keys"]))}; all identical before/after.\n'
              f'Cached request reconstruction: {len(rows)} identical keys.\n'
              f'Existing strict results: {len(new["strict_results"])} identical before/after.\n'
              'Prompt builders, collection cells, model settings and all native appliers unchanged.\n'
              'Owner edits preserved: Claude concurrency 12, native patch final newline, Haiku $0.50 reservation.\n'
              'All 36 primary expected documents byte-identical; only FEVS task metadata gained an alternative.\n'
              'Task instructions, edits and checks unchanged; alternative and frozen manifest verified.\n')
    (BUILD / 'amendment3_key_comparison.txt').write_text(report, encoding='utf-8', newline='\n')
    print(report, end='')


if __name__ == '__main__':
    main()
