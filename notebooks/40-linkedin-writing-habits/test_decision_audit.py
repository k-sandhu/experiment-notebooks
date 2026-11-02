import unittest
import decision_audit as d
from build_style_catalog import make_catalog


class DecisionAuditTests(unittest.TestCase):
    def test_independent_labels_need_not_sum_to_one(self):
        raw={'answers':{'a':{'type':'noul','noul':.9},'b':{'type':'noul','noul':.8}}}
        parsed=d.parse_decision(raw,['a','b'])
        self.assertTrue(all(x['valid'] for x in parsed.values()))
        self.assertEqual(parsed['a']['probability'],.9)
        self.assertEqual(parsed['b']['probability'],.8)

    def test_missing_refusal_and_out_of_range_are_unreadable(self):
        raw={'answers':{'refused':{'type':'refusal','refusal':'No answer'},'bad':{'type':'noul','noul':1.01}}}
        parsed=d.parse_decision(raw,['missing','refused','bad'])
        self.assertTrue(all(not x['valid'] and x['probability'] is None for x in parsed.values()))

    def test_batches_cover_all_six_regions_and_forty_labels(self):
        protocol={'definitions':{x['id']:{'definition':x['definition']} for x in make_catalog()['styles']}}
        record={'text':'A supported fact.\n\nA specific question?','requested_model':'hidden_writer'}
        first=d.decision_payload(record,0,protocol,'Source evidence.')
        second=d.decision_payload(record,1,protocol,'Source evidence.')
        self.assertEqual(len(first['questions']),120)
        self.assertEqual(len(second['questions']),120)
        self.assertFalse(set(first['questions'])&set(second['questions']))
        self.assertEqual(len(set(first['questions'])|set(second['questions'])),240)
        self.assertEqual(first['state'],second['state'])
        self.assertNotIn('hidden_writer',first['state'])
        self.assertFalse(first['provider']['allow_fallbacks'])
        self.assertNotIn('tools',first)


if __name__=='__main__':unittest.main()
