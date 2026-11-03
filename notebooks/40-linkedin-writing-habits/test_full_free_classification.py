import unittest
import full_free_classification as f
import smoke_study as s


class FullFreeClassificationTests(unittest.TestCase):
    def test_exact_body_is_not_reparsed_as_a_legacy_wrapper(self):
        text='LinkedIn post:\n\nActual content.\n\n---\nNote: this is inside the requested body.'
        self.assertEqual(f.body_zones(text)['whole'],text)
        self.assertEqual(f.body_zones(text)['opening_paragraph'],'LinkedIn post:')

    def test_all_predicates_are_partitioned_once_with_zero_price_guard(self):
        protocol=s.load(f.ROOT/'data/decision_audit/protocol.json')
        payloads=f.payloads('Post body.','Source article.',protocol)
        questions=[name for payload in payloads for name in payload['questions']]
        self.assertEqual(len(questions),240)
        self.assertEqual(len(set(questions)),240)
        self.assertEqual(len({payload['state'] for payload in payloads}),1)
        for payload in payloads:
            self.assertLessEqual(len(payload['questions']),40)
            self.assertEqual(payload['model'],f.MODEL)
            self.assertEqual(payload['provider']['max_price'],{'prompt':0,'completion':0})
            self.assertFalse(payload['provider']['allow_fallbacks'])


if __name__=='__main__':unittest.main()
