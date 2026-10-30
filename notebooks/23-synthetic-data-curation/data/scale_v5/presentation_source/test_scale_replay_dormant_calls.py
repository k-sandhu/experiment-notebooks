"""Offline instrumentation must retain an intentionally dormant live example."""
import unittest
from replay_scale_notebook import scale_qa_force_offline


class Tests(unittest.TestCase):
    def test_guarded_pilot_preserved_but_cannot_execute(self):
        source = 'SCALE_LIVE = True\nif SCALE_LIVE:\n    run(live=True)\nelse:\n    run(live=True)\n'
        rewritten, changes = scale_qa_force_offline(source)
        self.assertIn('if SCALE_LIVE:\n    run(live=True)', rewritten)
        self.assertIn('else:\n    run(live=False)', rewritten)
        calls = []
        exec(rewritten, {'run': lambda *, live: calls.append(live)})
        self.assertEqual(calls, [False])
        self.assertEqual(len(changes), 2)

    def test_ordinary_reachable_call_is_still_forced_offline(self):
        rewritten, _ = scale_qa_force_offline('if ordinary_condition:\n    run(live=True)\n')
        calls = []
        exec(rewritten, {'ordinary_condition': True, 'run': lambda *, live: calls.append(live)})
        self.assertEqual(calls, [False])


if __name__ == '__main__':
    unittest.main()
