"""Checks for new matching rules and separation of candidates from judgments."""
import unittest
import expanded_audit as a
from build_style_catalog import make_catalog


class ExpandedAuditTests(unittest.TestCase):
    def test_all_regex_examples_match_their_rule(self):
        for entry in make_catalog()['entries']:
            if entry['kind']=='regex':
                with self.subTest(entry=entry['id']):
                    self.assertTrue(a.audit_matches(entry,entry['illustrative_example']))

    def test_all_layout_examples_have_a_positive_value(self):
        for entry in make_catalog()['entries']:
            if entry['kind']=='layout':
                with self.subTest(entry=entry['id']):
                    self.assertGreater(a.audit_layout(entry['illustrative_example'])[entry['id']],0)

    def test_patterns_cannot_bridge_disjoint_windows(self):
        e=next(x for x in make_catalog()['entries'] if x['id']=='less_more')
        self.assertFalse(a.audit_matches(e,'less about cost\nmore about speed'))
        self.assertTrue(a.audit_matches(e,'less about cost and more about speed'))

    def test_curly_apostrophe_and_word_boundaries(self):
        e=next(x for x in make_catalog()['entries'] if x['id']=='honesty_cue')
        self.assertTrue(a.audit_matches(e,'Let’s be honest: it costs more.'))
        self.assertFalse(a.audit_matches(e,'dishonestly'))

    def test_list_blocks_break_paragraph_runs(self):
        layout=a.audit_layout('First fact.\n\nSecond fact.\n\n- A list item\n\nThird fact.')
        self.assertEqual(layout['single_sentence_run3'],0)
        self.assertEqual(a.audit_layout('One fact.\n\nAnother fact.\n\nA third fact.')['single_sentence_run3'],1)

    def test_hashtags_and_headings_are_separate(self):
        layout=a.audit_layout('## A New Release\n\nA fact.\n\n#AI #Research')
        self.assertEqual(layout['headings'],1)
        self.assertEqual(layout['hashtags'],2)
        self.assertEqual(layout['title_case_headings'],1)

    def test_human_judgments_are_not_automated_by_criteria(self):
        catalog=make_catalog()
        self.assertEqual(len(catalog['styles']),40)
        self.assertTrue(all('useful_when' in x for x in catalog['styles']))
        self.assertIn('post',catalog['status'].lower())
        # Core prior criteria remain contextual, rather than acquiring a fake regex score.
        self.assertFalse(any(e['style_id']=='unclear_reference' for e in catalog['entries']))


if __name__=='__main__':unittest.main()
