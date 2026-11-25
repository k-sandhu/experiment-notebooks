"""Regression fixtures for full-run extraction, accounting and phrase boundaries."""
import unittest
import full_study as f
import main_analysis as a
import smoke_study as s


class FullStudyTests(unittest.TestCase):
    def test_inline_link_stays_in_its_paragraph(self):
        html='<div class="entry-content"><p>The <a href="/">new model</a> is available.</p><p>Second paragraph.</p></div><h1>A release</h1>'
        title,text,selector=f.extract_article(html,'https://techcrunch.com/fixture')
        self.assertEqual(text,'The new model is available.\n\nSecond paragraph.')

    def test_news_widget_is_excluded(self):
        html='<h1>A news story</h1><div class="FITT_Article_main__body"><p>First fact.</p><section class="MobileContentPromo"><p>Unrelated news.</p></section><p>Last fact.</p></div>'
        _,text,_=f.extract_article(html,'https://abcnews.com/fixture')
        self.assertNotIn('Unrelated',text)
        self.assertIn('Last fact.',text)

    def test_cumulative_codex_fields_are_differenced(self):
        parsed={'raw_usage':{'input_tokens':2200,'cached_input_tokens':1100,'cache_write_input_tokens':0,'output_tokens':180}}
        result=f.corrected(parsed,'gpt-6.1-sol',{'input_tokens':1000,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':100},0)
        self.assertEqual(result['input_total'],1200)
        self.assertEqual(result['cache_read_tokens'],1100)
        self.assertEqual(result['output_tokens'],80)

    def test_claude_session_cost_is_differenced(self):
        parsed={'raw_usage':{},'reported_session_cost_usd':.07}
        result=f.corrected(parsed,'claude-opus-5-5',{},.03)
        self.assertAlmostEqual(result['reported_cost_usd'],.04)

    def test_disjoint_windows_do_not_invent_phrases(self):
        self.assertNotIn('ending unrelated',a.grams('ending\nunrelated',disjoint=True))
        self.assertIn('ending unrelated',a.grams('ending unrelated'))

    def test_short_followup_is_exact(self):
        self.assertEqual(s.FOLLOWUP_PROMPT,'Generate another post.')
        self.assertEqual(len(f.SOURCES),20)
        self.assertNotIn('https://huggingface.co/blog/mistral-large4',[source[3] for source in f.SOURCES])


if __name__=='__main__':unittest.main()
