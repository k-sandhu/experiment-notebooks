"""Notebook 40 collection and deterministic replay. No model APIs or SDKs."""
import argparse
from collections import Counter
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA = ROOT / 'data'
MODELS = ['gpt-6.1-sol', 'gpt-6.1-terra', 'claude-opus-5-5', 'claude-sonnet-5-5']
EFFORT = 'high'
N_ARTICLES = 1
N_REPEATS = 5
MAX_NEW_CALLS = 20
TIMEOUT_SECONDS = 240
PROTOCOL = 'smoke-v2-high-cache-blocked'
SOURCE_URL = 'https://huggingface.co/blog/mistral-large4'
PROMPT_TEMPLATE = 'Write a LinkedIn post based on the following article.\n\n<article>\n{article}\n</article>'
FOLLOWUP_PROMPT = 'Generate another post.'
NEUTRAL = 'You are a helpful assistant.\n'


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def normalise(text):
    text = unicodedata.normalize('NFKC', text).lower().replace('\u2019', "'")
    return ' '.join(text.split())


def words(text):
    return re.findall(r"\b\w+(?:['\u2019-]\w+)*\b", text.lower())


def freeze_source():
    """Whole article body, locally retained; URL/hash are the public provenance."""
    import requests
    from bs4 import BeautifulSoup
    target = DATA / 'local_inputs' / 'mistral-large4.txt'
    if target.exists():
        assert sha(target.read_text(encoding='utf-8')) == load(DATA / 'article.json')['text_sha256']
        return
    response = requests.get(SOURCE_URL, timeout=45)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    wrapper = soup.select_one('.blog-content')
    body = wrapper.select_one('div.relative.overflow-clip')
    assert wrapper and body, 'Article extraction selector changed'
    # Remove the duplicate interactive contents widget, retain the written contents.
    for widget in body.select('.SVELTE_HYDRATER'):
        widget.decompose()
    chunks = [wrapper.h1.get_text(' ', strip=True), 'Published October 29, 2026']
    for child in body.find_all(recursive=False):
        if child.name == 'pre':
            chunks.append(child.get_text('', strip=False).strip())
        else:
            chunks.append(child.get_text(' ', strip=True))
    article = '\n\n'.join(x for x in chunks if x).strip() + '\n'
    assert len(article) > 10000 and 'Mistral Large 4' in article
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(article, encoding='utf-8')
    save(DATA / 'article.json', {
        'item_id': 'smoke-mistral-large4', 'url': SOURCE_URL,
        'title': chunks[0], 'publication_date': '2026-10-29',
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'text_sha256': sha(article), 'characters': len(article), 'words': len(words(article)),
        'raw_html_sha256': hashlib.sha256(response.content).hexdigest(),
        'local_input': 'data/local_inputs/mistral-large4.txt',
        'redistribution': 'Full source text retained locally and git-ignored; no redistribution licence assumed.',
        'extraction': 'Title, publication date and complete article body; duplicate interactive contents widget removed. Code retained as text. No linked pages fetched into input.',
        'role': 'Smoke only; exclude this topic from a later confirmatory sample.'})


def freeze_lexicon():
    target = DATA / 'prose_lexicon.json'
    if target.exists():
        return
    groups = {
        'vocabulary': 'delve|tapestry|testament|intricate|meticulous|pivotal|crucial|vital|robust|seamless|leverage|harness|unlock|elevate|empower|foster|underscore|showcase|realm|landscape|navigate|journey|embark|game-changer|cutting-edge|groundbreaking|transformative|holistic|multifaceted|nuanced|comprehensive|invaluable|vibrant|boasts|notably|additionally|furthermore|moreover',
        'stock_phrases': "plays a key role|a wide range of|a myriad of|valuable insights|it's worth noting|it's important to note|let's dive in|sets the stage|marks a pivotal moment|in an evolving landscape|in today's fast-paced world|when it comes to|studies show|experts agree|it is widely known|serves as|stands as|functions as|may potentially|could possibly|it seems that|state-of-the-art",
        'linkedin_candidates': "this changes everything|the future is|the future of|here's why|here's the thing|here's what|here's the catch|let that sink in|read that again|think about that|a reminder that|what this means|why this matters|the real question|the bigger picture|the bottom line|my takeaway|my take|key takeaway|key takeaways|in conclusion|in summary|at the end of the day|the takeaway|the result|the lesson|the shift|the opportunity|food for thought|what do you think|what's your take|agree or disagree|curious to hear|would love to hear|let me know|drop a comment|share your thoughts|thoughts|certainly|great question|i hope this helps",
    }
    entries = []
    for category, phrases in groups.items():
        for phrase in phrases.split('|'):
            escaped = re.escape(phrase).replace(r'\ ', r'\s+')
            # Stem selected vocabulary words, while keeping ordinary boundary matching.
            tails = {'harness': r'(?:es|ed|ing)?', 'unlock': r'(?:s|ed|ing)?'}
            regex = r'\b' + escaped + tails.get(phrase, '') + r'\b'
            if phrase in ['delve', 'leverage', 'underscore', 'showcase']:
                regex = r'\b' + escaped[:-1] + r'(?:e|es|ed|ing)\b'
            entries.append({'id': phrase.replace(' ', '_'), 'label': phrase, 'category': category,
                            'regex': regex, 'status': 'fixed_before_smoke'})
    patterns = {
        'not_x_but_y': r"\bnot\b[^.!?\n]{1,140}\bbut\b",
        'isnt_x_its_y': r"\b(?:isn't|is not)\b[^.!?\n]{1,140}(?:[.!?]\s+|[,;:]\s*)?(?:it's|it is)\b",
        'not_just_x': r'\bnot (?:just|only)\b',
        'trailing_significance': r',\s*(?:highlighting|underscoring|showcasing|demonstrating|reinforcing|signaling)\b',
        'teaser_question': r"\b(?:the (?:result|lesson|takeaway|catch|question)|what changed|why it matters)\?",
        'colon_reveal': r"\b(?:here's (?:the|what|why)|the (?:result|lesson|takeaway|catch|question))[^\n.!?]{0,60}:",
        'recap_signal': r'\b(?:in conclusion|in summary|overall|key takeaways?)\b',
        'vague_authority': r'\b(?:studies show|experts agree|research suggests|it is widely known)\b',
        'stacked_hedge': r'\b(?:may potentially|could possibly|might perhaps)\b',
        'significance_claim': r'\b(?:significantly|dramatically|substantially|remarkably)\b',
    }
    for label, regex in patterns.items():
        entries.append({'id': label, 'label': label, 'category': 'structure_candidate',
                        'regex': regex, 'status': 'fixed_before_smoke',
                        'caution': 'Candidate span requiring contextual review, not an automatic defect.'})
    save(target, {'version': 1, 'frozen_at': datetime.now(timezone.utc).isoformat(),
                  'sources': ['Repository AGENTS.md editorial watchlist',
                              'https://arxiv.org/abs/2406.07016', 'https://arxiv.org/abs/2412.11385'],
                  'scope': 'Papers motivate vocabulary analysis; the repository supplies editorial candidates. LinkedIn-specific phrases and regexes are investigator hypotheses. No entry is an AI authorship detector.',
                  'entries': entries})


def clean_env():
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('CODEX_', 'CLAUDE_')) and k not in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']}


def isolation_dir():
    # Same path for all repetitions: changing cwd can invalidate the prompt prefix.
    directory = Path(tempfile.gettempdir()) / 'linkedin-40-isolation'
    directory.mkdir(exist_ok=True)
    (directory / 'neutral.txt').write_text(NEUTRAL, encoding='utf-8')
    (directory / 'empty-mcp.json').write_text('{"mcpServers":{}}\n', encoding='utf-8')
    return directory


def codex_options():
    directory = isolation_dir()
    flags = ['--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--ephemeral', '--strict-config']
    for feature in ['shell_tool', 'unified_exec', 'apps', 'plugins', 'multi_agent', 'browser_use',
                    'computer_use', 'image_generation', 'code_mode', 'code_mode_host', 'shell_snapshot',
                    'hooks', 'memories', 'skill_search', 'tool_suggest', 'sleep_tool', 'goals', 'view_image']:
        flags += ['--disable', feature]
    flags += ['--enable', 'skip_host_skill_discovery']
    for key, value in {'web_search': '"disabled"', 'model_reasoning_effort': '"high"',
                       'project_doc_max_bytes': '0', 'personality': '"none"',
                       'developer_instructions': '""',
                       'model_instructions_file': json.dumps((directory / 'neutral.txt').as_posix())}.items():
        flags += ['-c', f'{key}={value}']
    return flags


def command(model, conversation=False, session_id=None):
    if model.startswith('gpt'):
        options = codex_options()
        if conversation:
            options.remove('--ephemeral')
        return [shutil.which('codex.cmd') or shutil.which('codex'), 'exec', *options,
                '-m', model, '--json', *(['resume', session_id] if session_id else []), '-']
    cmd = [shutil.which('claude'), '-p', '--model', model, '--effort', EFFORT,
            '--tools', '', '--safe-mode', '--disable-slash-commands', '--strict-mcp-config', '--mcp-config',
            str(isolation_dir() / 'empty-mcp.json'), '--disallowedTools', 'mcp__*',
            '--no-session-persistence', '--system-prompt', NEUTRAL.strip(),
            '--output-format', 'stream-json', '--verbose', '--max-budget-usd', '1.00']
    if conversation:
        cmd.remove('--no-session-persistence')
    if session_id:
        cmd += ['--resume', session_id]
    return cmd


def json_events(stdout):
    events = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except json.JSONDecodeError:
            pass
    return events


def parse_result(model, stdout):
    events = json_events(stdout)
    text_parts, tool_events, catalogues, cli_warnings = [], [], [], []
    usage, session, resolved, reported_cost, completed = {}, None, None, None, False
    for e in events:
        if model.startswith('gpt'):
            session = e.get('thread_id', session)
            if e.get('type') == 'item.completed':
                item = e.get('item', {})
                if item.get('type') == 'agent_message':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'error':
                    cli_warnings.append(item)
                elif item.get('type') not in ['reasoning']:
                    tool_events.append(item)
            if e.get('type') == 'turn.completed':
                usage, completed = e.get('usage', {}), True
        else:
            session = e.get('session_id', session)
            if e.get('type') == 'system' and e.get('subtype') == 'init':
                catalogues.append({'tools': e.get('tools'), 'mcp_servers': e.get('mcp_servers'),
                                   'skills': e.get('skills'), 'plugins': e.get('plugins')})
                resolved = e.get('model', resolved)
            if e.get('type') == 'assistant':
                for block in e.get('message', {}).get('content', []):
                    if block.get('type') == 'tool_use':
                        tool_events.append(block)
            if e.get('type') == 'result':
                usage = e.get('usage', {})
                text_parts = [e.get('result', '')]
                reported_cost = e.get('total_cost_usd')
                completed = e.get('subtype') == 'success' and not e.get('is_error', False)
    text = '\n\n'.join(text_parts).strip()
    if model.startswith('gpt'):
        total = usage.get('input_tokens')
        details = usage.get('input_tokens_details', {})
        reads = usage.get('cached_input_tokens', details.get('cached_tokens'))
        writes = usage.get('cache_write_input_tokens', details.get('cache_write_tokens'))
        uncached = total - reads - writes if all(isinstance(x, int) for x in [total, reads, writes]) else None
    else:
        uncached = usage.get('input_tokens')
        reads, writes = usage.get('cache_read_input_tokens'), usage.get('cache_creation_input_tokens')
        total = sum([uncached, reads, writes]) if all(isinstance(x, int) for x in [uncached, reads, writes]) else None
    return {'text': text, 'completed': completed, 'session_id': session,
            'reported_model': resolved, 'raw_usage': usage, 'input_total': total,
            'cache_read_tokens': reads, 'cache_write_tokens': writes, 'uncached_input_tokens': uncached,
            'output_tokens': usage.get('output_tokens'), 'reported_cost_usd': reported_cost,
            'reported_session_cost_usd': reported_cost,
            'cache_read_fraction': reads / total if isinstance(reads, int) and total else None,
            'tool_events': tool_events, 'catalogues': catalogues, 'cli_warnings': cli_warnings,
            'raw_sha256': sha(stdout), 'text_sha256': sha(text), 'normalised_sha256': sha(normalise(text))}


def preflight():
    """No generation: inspect prompt context and validate supported flags locally."""
    cmd = [shutil.which('codex.cmd') or shutil.which('codex'), 'debug', 'prompt-input']
    flags = codex_options()
    # These options belong to exec rather than debug.
    flags = [x for x in flags if x not in ['--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--ephemeral', '--strict-config']]
    result = subprocess.run(cmd + flags + ['PROBE_ONLY_NO_GENERATION'], cwd=isolation_dir(), env=clean_env(),
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    assert result.returncode == 0, result.stderr
    messages = json.loads(result.stdout)
    strings = [b.get('text', '') for m in messages for b in m.get('content', []) if isinstance(b, dict)]
    forbidden = ['# Instructions for AI agents', 'No em dashes.', 'Write a LinkedIn post', 'Use plain verbs.']
    assert not any(f in '\n'.join(strings) for f in forbidden), 'Writing/repository context contamination'
    save(DATA / 'preflight.json', {'protocol': PROTOCOL, 'checked_at': datetime.now(timezone.utc).isoformat(),
          'prompt_context_sha256': sha(result.stdout),
          'context_blocks': [{'role': m.get('role'), 'characters': len(canonical(m.get('content', [])))} for m in messages],
          'residual_context': 'Codex debug exposes runtime-injected skills catalogue, team directives and environment context despite feature disables. No repository writing rules observed. These platform-level instructions cannot be claimed removed.',
          'cli_versions': {name: subprocess.run([shutil.which(name + '.cmd') or shutil.which(name), '--version'], capture_output=True, text=True).stdout.strip() for name in ['codex', 'claude']},
          'commands': {model: command(model) for model in MODELS},
          'tool_catalogue_validation': 'Claude init catalogue checked per call; Codex disabled features plus event trace checked. Codex exec does not expose a complete advertised tool catalogue in JSONL.'})


def collect(repeats=N_REPEATS, max_new=MAX_NEW_CALLS, conversation=False):
    assert 1 <= repeats <= 5 and 0 <= max_new <= MAX_NEW_CALLS
    freeze_source()
    freeze_lexicon()
    preflight()
    article = (DATA / 'local_inputs' / 'mistral-large4.txt').read_text(encoding='utf-8')
    prompt = PROMPT_TEMPLATE.format(article=article)
    lexicon_hash = sha((DATA / 'prose_lexicon.json').read_text(encoding='utf-8'))
    model_order = MODELS.copy()
    random.Random(20261101).shuffle(model_order)
    n_new = 0
    for model in model_order:
        previous_session = None
        previous_session_cost = 0.0
        request = {'protocol': PROTOCOL, 'model': model, 'effort': EFFORT, 'prompt_sha256': sha(prompt),
                   'source_sha256': sha(article), 'system_sha256': sha(NEUTRAL),
                   'lexicon_sha256': lexicon_hash, 'command': command(model)}
        for replicate in range(1, repeats + 1):
            cmd = command(model, conversation, previous_session)
            request['command'] = cmd
            turn_prompt = FOLLOWUP_PROMPT if conversation and replicate > 1 else prompt
            request['prompt_sha256'] = sha(turn_prompt)
            if conversation:
                request['history_condition'] = 'same_conversation_initial_article_then_generate_another_post_only'
                request['turn_prompt_kind'] = 'followup_only' if replicate > 1 else 'initial_article'
            request_hash = sha(canonical(request))
            slot = DATA / ('conversation' if conversation else 'smoke') / model / f'{replicate:02d}-{request_hash[:12]}'
            if slot.with_suffix('.json').exists():
                saved = load(slot.with_suffix('.json'))
                assert saved['status'] == 'ok', 'Saved failed slot requires diagnosis, not silent replay'
                previous_session = saved['session_id'] if conversation else None
                if conversation and not model.startswith('gpt'):
                    previous_session_cost = saved.get('reported_session_cost_usd', saved.get('reported_cost_usd'))
                continue
            if slot.with_suffix('.started.json').exists():
                raise RuntimeError('Unresolved started request: reconcile its provider result before generating again')
            if conversation and any(int(p.name[:2]) > replicate for p in slot.parent.glob('*.json') if p.name[:2].isdigit()):
                raise RuntimeError('Conversation has later saved turns: do not fill a gap by appending to changed history')
            if n_new >= max_new:
                raise RuntimeError('New-call budget exhausted')
            start = time.monotonic()
            started_at = datetime.now(timezone.utc).isoformat()
            print(f'START {model} repeat {replicate}', flush=True)
            slot.parent.mkdir(parents=True, exist_ok=True)
            save(slot.with_suffix('.started.json'), {'requested_model': model, 'replicate': replicate,
                 'request': request.copy(), 'started_at': started_at, 'status': 'started_usage_not_yet_available'})
            try:
                result = subprocess.run(cmd, input=turn_prompt, cwd=isolation_dir(), env=clean_env(),
                                        capture_output=True, text=True, encoding='utf-8', errors='replace',
                                        timeout=TIMEOUT_SECONDS)
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
            except subprocess.TimeoutExpired as exc:
                stdout = (exc.stdout or b'').decode('utf-8', errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
                stderr, code = 'CLI timeout; no automatic content retry', -1
            parsed = parse_result(model, stdout)
            if conversation and not model.startswith('gpt') and parsed['reported_session_cost_usd'] is not None:
                parsed['reported_cost_usd'] = parsed['reported_session_cost_usd'] - previous_session_cost
                previous_session_cost = parsed['reported_session_cost_usd']
            parsed.update({'requested_model': model, 'replicate': replicate, 'request': request,
                           'request_sha256': request_hash, 'started_at': started_at,
                           'seconds': time.monotonic() - start, 'exit_code': code,
                           'local_replay': False})
            parsed['status'] = ('ok' if code == 0 and parsed['completed'] and parsed['text'] else 'unreadable_or_failed')
            if parsed['tool_events']:
                parsed['status'] = 'tool_protocol_violation'
            for cat in parsed['catalogues']:
                if any(cat.get(k) for k in ['tools', 'mcp_servers']):
                    parsed['status'] = 'catalogue_protocol_violation'
            slot.with_suffix('.jsonl').write_text(stdout, encoding='utf-8')
            slot.with_suffix('.stderr.txt').write_text(stderr, encoding='utf-8')
            save(slot.with_suffix('.json'), parsed)
            slot.with_suffix('.started.json').unlink()
            n_new += 1
            print(f"DONE {model} repeat {replicate}: {parsed['status']}; input={parsed['input_total']}; cache_read={parsed['cache_read_tokens']}; cache_write={parsed['cache_write_tokens']}; seconds={parsed['seconds']:.1f}", flush=True)
            if parsed['status'] != 'ok':
                raise RuntimeError('Smoke gate failed; inspect saved evidence before any more calls')
            if conversation:
                if previous_session is not None and previous_session != parsed['session_id']:
                    raise RuntimeError('Conversation changed session ID on resume')
                previous_session = parsed['session_id']


def split_response(text):
    """Conservative literal wrapper/note extraction; keep all raw text separately."""
    body, annotation, preface = text.strip(), '', ''
    parts = re.split(r'\n\s*---\s*\n', body)
    if len(parts) > 1:
        tail = parts[-1].strip()
        plain = tail.lstrip('*_ ').lower()
        if re.match(r'(?:note\b|one note\b|the article\b|i left out\b|before posting\b)', plain):
            annotation = tail
            body = '\n\n---\n\n'.join(parts[:-1]).strip()
    lines = body.splitlines()
    if lines and re.fullmatch(r'\*{0,2}linkedin post:\*{0,2}', lines[0].strip(), re.I):
        preface = lines.pop(0)
        while lines and (not lines[0].strip() or lines[0].strip() == '---'):
            lines.pop(0)
        body = '\n'.join(lines).strip()
    return {'body': body, 'preface': preface, 'annotation': annotation}


def sentences(text):
    # An emoji after a final question belongs to that sentence, not a new one.
    return re.split(r'''(?<=[.!?])\s+(?=["\u201c'\u2018*]*[A-Za-z0-9])''', text.strip()) if text.strip() else []


def zones(text):
    raw = text
    segments = split_response(text)
    text = segments['body']
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    substantive = [p for p in paragraphs if not all(w.startswith('#') for w in p.split())]
    ss_all = sentences(text)
    starts, endings = [], []
    for p in substantive:
        ss = sentences(p)
        starts.extend(ss[1:])
    for p in substantive[1:]:
        starts.append(p)
    for p in substantive[:-1]:
        endings.append(sentences(p)[-1])
    return {'whole_response': raw, 'editorial_note': segments['annotation'],
            'whole': text, 'opening_sentence': ss_all[0] if ss_all else '',
            'opening_paragraph': paragraphs[0] if paragraphs else '',
            'opening_30_words': ' '.join(text.split()[:30]),
            'transition_starts': '\n'.join(' '.join(x.split()[:12]) for x in starts),
            'point_endings': '\n'.join(endings),
            'conclusion': substantive[-1] if substantive else '',
            'closing': sentences(substantive[-1])[-1] if substantive else ''}


def formatting(text):
    segments = split_response(text)
    text = segments['body']
    paragraphs = [p for p in re.split(r'\n\s*\n', text.strip()) if p]
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return {'words': len(words(text)), 'characters': len(text), 'paragraphs': len(paragraphs),
            'response_preface': bool(segments['preface']), 'editorial_note': bool(segments['annotation']),
            'editorial_note_words': len(words(segments['annotation'])),
            'nonempty_lines': len(lines), 'blank_lines': sum(not l.strip() for l in text.splitlines()),
            'short_lines_le_8_words': sum(len(words(l)) <= 8 for l in lines),
            'bullets': len(re.findall(r'^\s*[-*\u2022]\s+', text, re.M)),
            'numbered_items': len(re.findall(r'^\s*\d+[.)]\s+', text, re.M)),
            'hashtags': len(re.findall(r'(?<!\w)#[\w]+', text)),
            'headings': len(re.findall(r'^\s*#{1,6}\s+', text, re.M)),
            'bold_spans': len(re.findall(r'\*\*.+?\*\*|__.+?__', text)),
            'links': len(re.findall(r'https?://\S+', text)),
            'em_dashes': text.count('\u2014'), 'colons': text.count(':'),
            'questions': text.count('?'), 'exclamations': text.count('!'),
            'ellipses': text.count('...') + text.count('\u2026'),
            'emoji_codepoints': sum(0x1F300 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF for c in text),
            'emoji_prefixed_lines': len(re.findall(r'^\s*[\U0001F300-\U0001FAFF\u2600-\u27BF]', text, re.M)),
            'opening_question': '?' in zones(text)['opening_sentence'],
            'closing_question': bool(re.search(r'\?[\s\W]*$', zones(text)['closing']))}


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def refresh_accounting(arm):
    """Convert cumulative resumed-session counters to per-invocation increments."""
    for model in MODELS:
        previous_usage, previous_cost = {}, 0.0
        for path in sorted((DATA / arm / model).glob('*.json')):
            if '.started.' in path.name:
                continue
            record = load(path)
            parsed = parse_result(model, path.with_suffix('.jsonl').read_text(encoding='utf-8'))
            native = parsed['raw_usage'].copy()
            if arm == 'conversation' and model.startswith('gpt'):
                delta = {k: v - previous_usage.get(k, 0) for k, v in native.items() if isinstance(v, int)}
                assert all(v >= 0 for v in delta.values()), 'Cumulative usage decreased'
                parsed['raw_session_usage'] = native
                parsed['per_turn_usage'] = delta
                parsed['input_total'] = delta.get('input_tokens')
                parsed['cache_read_tokens'] = delta.get('cached_input_tokens')
                parsed['cache_write_tokens'] = delta.get('cache_write_input_tokens')
                parsed['output_tokens'] = delta.get('output_tokens')
                parsed['uncached_input_tokens'] = parsed['input_total'] - parsed['cache_read_tokens'] - parsed['cache_write_tokens']
                parsed['cache_read_fraction'] = parsed['cache_read_tokens'] / parsed['input_total']
                parsed['usage_scope'] = 'Codex cumulative session counters differenced by turn; raw counters retained'
                previous_usage = native
            else:
                parsed['usage_scope'] = 'Per-invocation usage'
            if arm == 'conversation' and not model.startswith('gpt'):
                total = parsed['reported_session_cost_usd']
                parsed['reported_cost_usd'] = total - previous_cost if total is not None else None
                previous_cost = total
                parsed['usage_scope'] += '; Claude cumulative reported session cost differenced by turn'
            record.update(parsed)
            save(path, record)


def analyse(arm='smoke'):
    assert arm in ['smoke', 'conversation']
    records = [load(p) for p in sorted((DATA / arm).glob('*/*.json'))]
    prefix = '' if arm == 'smoke' else 'conversation_'
    lexicon = load(DATA / 'prose_lexicon.json')['entries']
    source_path = DATA / 'local_inputs' / 'mistral-large4.txt'
    source = normalise(source_path.read_text(encoding='utf-8')) if source_path.exists() else None
    overlap_path = DATA / 'source_overlap.json'
    overlaps = load(overlap_path) if overlap_path.exists() else {'lexicon': {}, 'candidate_sha256': {}}
    rows, pairs, phrase_rows, format_rows, candidates = [], [], [], [], []
    for model in MODELS:
        rs = sorted([r for r in records if r['requested_model'] == model], key=lambda r: r['replicate'])
        valid = [r for r in rs if r['status'] == 'ok']
        for a, b in itertools.combinations(valid, 2):
            wa, wb = words(a['text']), words(b['text'])
            na = set(zip(*(wa[i:] for i in range(3))))
            nb = set(zip(*(wb[i:] for i in range(3))))
            pairs.append({'model': model, 'repeat_a': a['replicate'], 'repeat_b': b['replicate'],
                          'exact_duplicate': a['text_sha256'] == b['text_sha256'],
                          'normalised_duplicate': a['normalised_sha256'] == b['normalised_sha256'],
                          'word_sequence_similarity': SequenceMatcher(None, wa, wb, autojunk=False).ratio(),
                          'trigram_jaccard': len(na & nb) / len(na | nb) if na | nb else 1.0})
        reads = [r['cache_read_tokens'] for r in valid]
        totals = [r['input_total'] for r in valid]
        warm = valid[1:]
        all_known = bool(valid) and all(isinstance(x, int) for x in reads + totals)
        warm_known = bool(warm) and all(isinstance(r[k], int) for r in warm for k in ['cache_read_tokens', 'input_total'])
        rows.append({'model': model, 'effort': EFFORT, 'attempted': len(rs), 'readable': len(valid),
                     'unique_exact': len({r['text_sha256'] for r in valid}),
                     'unique_normalised': len({r['normalised_sha256'] for r in valid}),
                     'unique_post_normalised': len({normalise(split_response(r['text'])['body']) for r in valid}),
                     'cache_read_tokens': sum(reads) if all_known else None,
                     'input_total_tokens': sum(totals) if all_known else None,
                     'cache_read_fraction_all': sum(reads) / sum(totals) if all_known and sum(totals) else None,
                     'cache_read_fraction_repeats_2_to_5': sum(r['cache_read_tokens'] for r in warm) / sum(r['input_total'] for r in warm) if warm_known else None,
                     'cache_write_tokens': sum(r['cache_write_tokens'] for r in valid) if valid and all(isinstance(r['cache_write_tokens'], int) for r in valid) else None,
                     'reported_cost_usd': sum(r['reported_cost_usd'] for r in valid) if valid and all(isinstance(r['reported_cost_usd'], (int,float)) for r in valid) else None,
                     'seconds': sum(r['seconds'] for r in rs),
                     'tool_events': sum(len(r['tool_events']) for r in rs)})
        for r in valid:
            format_rows.append({'model': model, 'replicate': r['replicate'], **formatting(r['text'])})
        for zone in zones(''):
            document_counts = Counter()
            for record in valid:
                tokens = words(normalise(zones(record['text'])[zone]))
                seen = set()
                for n in range(2, 9):
                    seen.update(' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1))
                document_counts.update(seen)
            source_tokens = ' ' + ' '.join(words(source)) + ' ' if source is not None else None
            for phrase, count in document_counts.items():
                if count >= 2:
                    if source_tokens is not None:
                        overlaps['candidate_sha256'][sha(phrase)] = (' ' + phrase + ' ') in source_tokens
                    candidates.append({'model': model, 'zone': zone, 'phrase': phrase,
                        'words': len(phrase.split()), 'posts_containing': count,
                        'readable_posts': len(valid), 'distinct_topics': 1,
                        'present_in_source': overlaps['candidate_sha256'].get(sha(phrase)),
                        'status': 'exploratory_one_topic_smoke'})
            for entry in lexicon:
                regex = re.compile(entry['regex'], re.I)
                texts = [normalise(zones(r['text'])[zone]) for r in valid]
                counts = [len(regex.findall(text)) for text in texts]
                denominator = sum(len(words(text)) for text in texts)
                if source is not None:
                    overlaps['lexicon'][entry['id']] = len(regex.findall(source))
                phrase_rows.append({'model': model, 'zone': zone, 'phrase_id': entry['id'],
                    'category': entry['category'], 'occurrences': sum(counts),
                    'posts_containing': sum(c > 0 for c in counts), 'readable_posts': len(valid),
                    'post_fraction': sum(c > 0 for c in counts) / len(valid) if valid else None,
                    'occurrences_per_1000_words': 1000 * sum(counts) / denominator if denominator else None,
                    'source_occurrences': overlaps['lexicon'].get(entry['id'])})
    write_csv(DATA / f'{arm}_summary.csv', rows)
    write_csv(DATA / f'{prefix}pairwise_similarity.csv', pairs)
    write_csv(DATA / f'{prefix}prose_counts.csv', phrase_rows)
    write_csv(DATA / f'{prefix}formatting.csv', format_rows)
    save(overlap_path, overlaps)
    write_csv(DATA / f'{prefix}phrase_candidates.csv', sorted(candidates, key=lambda r:(r['model'],r['zone'],-r['posts_containing'],-r['words'],r['phrase'])))
    write_csv(DATA / f'{prefix}provider_cache_usage.csv', [{k:r.get(k) for k in [
        'requested_model','replicate','status','input_total','uncached_input_tokens','cache_read_tokens',
        'cache_write_tokens','cache_read_fraction','output_tokens','reported_cost_usd','seconds','session_id']} for r in records])
    save(DATA / f'{arm}_summary.json', {'protocol': PROTOCOL, 'condition': arm, 'models': rows,
        'gates': {'twenty_successful': sum(r['status'] == 'ok' for r in records) == 20,
                  'five_unique_per_model': all(r['unique_normalised'] == 5 for r in rows),
                  'five_unique_post_bodies_per_model': all(r['unique_post_normalised'] == 5 for r in rows),
                  'no_observed_tool_events': not any(r['tool_events'] for r in records),
                  'prompts_match_condition': (len({r['request']['prompt_sha256'] for r in records}) == 1 if arm == 'smoke' else
                      all(r['request']['prompt_sha256'] == (sha(FOLLOWUP_PROMPT) if r['replicate'] > 1 else records[0]['request']['prompt_sha256']) for r in records)),
                  'sessions_match_condition': (len({r['session_id'] for r in records}) == len(records) if arm == 'smoke' else
                      all(len({r['session_id'] for r in records if r['requested_model'] == model}) == 1 for model in MODELS))},
        'interpretation': 'Smoke is an engineering check on one topic, not a model ranking or evidence of general family habits. Provider caching reuses input computation, not output text. Unknown usage fields remain null.'})
    print(json.dumps(rows, indent=2))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'collect', 'conversation', 'analyse', 'analyse-conversation'])
    parser.add_argument('--repeats', type=int, default=N_REPEATS)
    parser.add_argument('--max-new', type=int, default=MAX_NEW_CALLS)
    args = parser.parse_args()
    if args.mode == 'prepare':
        freeze_source(); freeze_lexicon(); preflight()
    elif args.mode in ['collect', 'conversation']:
        collect(args.repeats, args.max_new, conversation=args.mode == 'conversation')
    else:
        analyse('conversation' if args.mode == 'analyse-conversation' else 'smoke')
