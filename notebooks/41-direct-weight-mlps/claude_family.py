"""Owner-requested Claude family submissions (2026-11-05): Opus 5.5, Sonnet 5.5 and Haiku 5.5.

Each model receives the unchanged frozen prompt through `claude -p`, with the same isolation as the
original Opus request (no tools, empty MCP catalogue, neutral system prompt). Settings follow the earlier
Opus continuation: high effort, 128,000-token output allowance and a US$20 budget flag per call. No test
feedback, other models' answers or tester-chosen values are supplied. One call per model.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import experiment as e

FAMILY = {
    'opus': {'backend': 'claude', 'model': 'claude-opus-5-5', 'effort': 'high'},
    'sonnet': {'backend': 'claude', 'model': 'claude-sonnet-5-5', 'effort': 'high'},
    'haiku': {'backend': 'claude', 'model': 'claude-haiku-5-5', 'effort': 'high'},
    'fable': {'backend': 'claude', 'model': 'claude-fable-5-1', 'effort': 'high'},  # added on owner request after the first three
}
OUTPUT_TOKEN_CAP = 128000
BUDGET_USD = '20.0'
RUN = 'claude-family-2026-11-05'


def collect(key):
    e.MODELS.setdefault(key, FAMILY[key])
    saved = dict(e.MODELS[key])
    e.MODELS[key] = FAMILY[key]
    try:
        out = e.DATA / 'claude_family' / key
        out.mkdir(parents=True, exist_ok=True)
        prompt = (e.DATA / 'prompt.txt').read_text(encoding='utf-8')
        assert e.sha(prompt) == json.loads((e.DATA / 'manifest.json').read_text(encoding='utf-8'))['prompt_sha256']
        cmd = e.cli_command(key, out)
        cmd[cmd.index('--max-budget-usd') + 1] = BUDGET_USD
        request = {'config': FAMILY[key], 'prompt': prompt, 'schema': e.SCHEMA, 'tools_enabled': [],
                   'protocol': 'digits-v1', 'command': cmd, 'output_token_cap': OUTPUT_TOKEN_CAP, 'run': RUN,
                   'run_reason': 'Owner-requested Claude family comparison. Same prompt and isolation as the original '
                                 'Opus request; high effort and 128000 output allowance as in the Opus continuation.'}
        keyhash = e.sha(json.dumps(request, sort_keys=True))
        cache = out / 'response.json'
        if cache.exists():
            record = json.loads(cache.read_text(encoding='utf-8'))
            assert record['cache_key'] == keyhash
        else:
            assert not (out / 'started.json').exists(), 'Unresolved request; inspect logs instead of regenerating'
            e.dump(out / 'request.json', request)
            e.dump(out / 'started.json', {'started_utc': e.utc(), 'cache_key': keyhash})
            print('START ' + key, flush=True)
            record = e.run_cli(key, out, request)
            record.update(cache_key=keyhash, request=request)
            e.dump(cache, record)
            (out / 'weights_output.json').write_text(record.get('answer', ''), encoding='utf-8')
            (out / 'reasoning.txt').write_text(record.get('reasoning', ''), encoding='utf-8')
            e.trace_call(keyhash, FAMILY[key], request, record)
        result = e.validate_and_score(key, record, out_override=out)
        print(json.dumps({'model': key, 'format_failure': result['format_failure'],
                          'category': result['failure_category'],
                          'test': result.get('test', {}).get('accuracy'),
                          'wall_seconds': record.get('wall_seconds'), 'cost_usd': record.get('cost_usd')}), flush=True)
    finally:
        e.MODELS[key] = saved


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', default=list(FAMILY), choices=list(FAMILY))
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=len(args.models)) as pool:
        for future in [pool.submit(collect, key) for key in args.models]:
            try:
                future.result()
            except Exception as exc:
                print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}), flush=True)
