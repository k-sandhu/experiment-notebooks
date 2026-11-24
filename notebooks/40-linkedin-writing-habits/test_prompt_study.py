import unittest
from unittest.mock import patch
import numpy as np
import prompt_study as p
import prompt_comparison as c
import decision_audit as d
import smoke_study as s


class PromptStudyTests(unittest.TestCase):
    def test_exact_saved_template_and_short_followup(self):
        raw=(p.ROOT/'data/prompt_conditions/plain_prose_v2.txt').read_text(encoding='utf-8')
        template=raw.replace('{{complete_article_text}}','{article}')
        filled=template.format(article='A source fact with {literal braces}.')
        self.assertIn('A source fact with {literal braces}.',filled)
        self.assertNotIn('{{complete_article_text}}',filled)
        self.assertEqual(s.FOLLOWUP_PROMPT,'Generate another post.')

    def test_ten_targets_and_six_original_regions(self):
        self.assertEqual(p.PRIMARY_TARGETS,c.TARGETS)
        self.assertEqual(len(set(c.TARGETS)),10)
        self.assertEqual(d.DECISION_ZONES,['whole','opening_paragraph','transition_starts','point_endings','conclusion','closing'])

    def test_paired_bootstrap_uses_differences(self):
        lo,hi=c.paired_interval(np.zeros(20))
        self.assertEqual((lo,hi),(0.,0.))
        lo,hi=c.paired_interval(np.full(20,-20.))
        self.assertEqual((lo,hi),(-20.,-20.))


if __name__=='__main__':unittest.main()
