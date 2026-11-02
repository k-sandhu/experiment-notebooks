"""Small regression tests for the failure-prone accounting and extraction logic."""
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import smoke_study as study


class SmokeHarnessTests(unittest.TestCase):
    def test_claude_cache_counts_are_disjoint(self):
        raw = '\n'.join(json.dumps(x) for x in [
            {'type': 'system', 'subtype': 'init', 'tools': [], 'mcp_servers': [], 'session_id': 'fixture'},
            {'type': 'result', 'subtype': 'success', 'result': 'A post.',
             'usage': {'input_tokens': 10, 'cache_read_input_tokens': 900,
                       'cache_creation_input_tokens': 90, 'output_tokens': 30}}])
        parsed = study.parse_result('claude-opus-5-5', raw)
        self.assertEqual(parsed['input_total'], 1000)
        self.assertEqual(parsed['cache_read_fraction'], .9)
        self.assertEqual(parsed['text'], 'A post.')

    def test_codex_missing_writes_are_unknown_not_zero(self):
        raw = '\n'.join(json.dumps(x) for x in [
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'A post.'}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 1000,
                                                'cached_input_tokens': 800, 'output_tokens': 30}}])
        parsed = study.parse_result('gpt-6.1-sol', raw)
        self.assertEqual(parsed['input_total'], 1000)
        self.assertEqual(parsed['cache_read_fraction'], .8)
        self.assertIsNone(parsed['cache_write_tokens'])

    def test_tool_activity_is_detected(self):
        raw = json.dumps({'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'WebSearch', 'input': {}}]}})
        self.assertEqual(len(study.parse_result('claude-opus-5-5', raw)['tool_events']), 1)

    def test_codex_cli_warning_is_not_a_tool_call(self):
        raw = json.dumps({'type': 'item.completed', 'item': {'type': 'error', 'message': 'Fixture warning'}})
        result = study.parse_result('gpt-6.1-terra', raw)
        self.assertEqual(result['tool_events'], [])
        self.assertEqual(len(result['cli_warnings']), 1)

    def test_hashtags_do_not_replace_substantive_closing(self):
        text = 'A finding.\n\nWhat do you think?\n\n#AI #Science'
        self.assertEqual(study.zones(text)['closing'], 'What do you think?')
        self.assertTrue(study.formatting(text)['closing_question'])

    def test_editorial_note_and_wrapper_are_not_post_boundaries(self):
        text = '**LinkedIn post:**\n\n---\n\nA finding.\n\nWhat would you build?\n\n#AI\n\n---\n\n**Note:** The article has an inconsistency.'
        parts = study.split_response(text)
        self.assertEqual(study.zones(text)['opening_sentence'], 'A finding.')
        self.assertEqual(study.zones(text)['closing'], 'What would you build?')
        self.assertIn('inconsistency', parts['annotation'])
        self.assertTrue(study.formatting(text)['response_preface'])

    def test_emoji_after_question_is_not_a_new_sentence(self):
        self.assertEqual(study.zones('What would you build? \U0001f447')['closing'], 'What would you build? \U0001f447')
        self.assertTrue(study.formatting('What would you build? \U0001f447')['closing_question'])

    def test_identical_prompt_but_distinct_replicate_slots(self):
        request_hash = study.sha(study.PROMPT_TEMPLATE.format(article='Fixture source'))
        slots = {f'{repeat:02d}-{request_hash[:12]}' for repeat in range(1, 6)}
        self.assertEqual(len(slots), 5)
        self.assertEqual(study.normalise('Same\n post.'), study.normalise('same post.'))

    def test_resumed_codex_counters_are_differenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for repeat, inp, cached, out in [(1,1000,0,100),(2,2200,1100,180)]:
                p = data/'conversation'/'gpt-6.1-sol'/f'{repeat:02d}.json'
                study.save(p, {'requested_model':'gpt-6.1-sol','replicate':repeat})
                events = [{'type':'thread.started','thread_id':'fixture'},
                          {'type':'turn.completed','usage':{'input_tokens':inp,
                           'cached_input_tokens':cached,'cache_write_input_tokens':0,'output_tokens':out}}]
                p.with_suffix('.jsonl').write_text('\n'.join(json.dumps(e) for e in events),encoding='utf-8')
            with patch.object(study,'DATA',data), patch.object(study,'MODELS',['gpt-6.1-sol']):
                study.refresh_accounting('conversation')
            r=study.load(data/'conversation'/'gpt-6.1-sol'/'02.json')
            self.assertEqual(r['input_total'],1200)
            self.assertEqual(r['cache_read_tokens'],1100)
            self.assertEqual(r['output_tokens'],80)
            self.assertEqual(r['raw_session_usage']['input_tokens'],2200)


if __name__ == '__main__':
    unittest.main()
