import unittest
import free_decision_pilot as f
import smoke_study as s


class FreeDecisionPilotTests(unittest.TestCase):
    def test_wire_contains_only_body_and_zero_price_route(self):
        protocol=s.load(f.ROOT/'data/decision_audit/protocol.json')
        record=dict(text='SECRET PREFACE <linkedin_post>Post body.</linkedin_post> SECRET NOTE',
                    post_body='Post body.',requested_model='SECRET WRITER',turn=1)
        a=f.payload_for(record,0,protocol,'Source article.')
        batches=[f.payload_for(record,i,protocol,'Source article.') for i in range(6)]
        self.assertEqual(a['model'],f.MODEL)
        self.assertEqual(a['provider']['max_price'],{'prompt':0,'completion':0})
        self.assertFalse(a['provider']['allow_fallbacks'])
        self.assertEqual(a['provider']['only'],['respan'])
        self.assertNotIn('SECRET',a['state'])
        self.assertNotIn('<linkedin_post>',a['state'])
        self.assertIn('Post body.',a['state'])
        self.assertEqual(len(a['questions']),40)
        self.assertEqual(len(set().union(*(set(b['questions']) for b in batches))),240)

    def test_invalid_generation_tags_are_not_classified_as_prose(self):
        with self.assertRaises(AssertionError):
            f.payload_for(dict(text='Untagged prose.',post_body=None),0,{},'Source.')


if __name__=='__main__':unittest.main()
