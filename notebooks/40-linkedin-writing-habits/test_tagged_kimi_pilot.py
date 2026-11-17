import unittest
from tagged_kimi_pilot import parse_post


class TaggedPostTests(unittest.TestCase):
    def test_preserves_outside_text_and_body(self):
        result=parse_post('Preface\n<linkedin_post>\nA post.\n\nSecond paragraph.\n</linkedin_post>\nA correction.')
        self.assertEqual(result['post_body'],'A post.\n\nSecond paragraph.')
        self.assertEqual(result['text_before'],'Preface\n')
        self.assertEqual(result['text_after'],'\nA correction.')
        self.assertEqual(result['format_status'],'extra_text')

    def test_whitespace_outside_is_not_commentary(self):
        result=parse_post('\n<linkedin_post>A post.</linkedin_post>\n')
        self.assertEqual(result['format_status'],'ok')
        self.assertFalse(result['extra_text_present'])

    def test_ambiguous_or_missing_tags_are_not_guessed(self):
        cases=['A post.', '<linkedin_post>A post.', '<linkedin_post> </linkedin_post>',
               '<linkedin_post>One</linkedin_post><linkedin_post>Two</linkedin_post>',
               '<linkedin_post>Outer<linkedin_post>Inner</linkedin_post></linkedin_post>',
               '<LinkedIn_Post>A post.</LinkedIn_Post>',
               '<linkedin_post extra="yes">A post.</linkedin_post>']
        for raw in cases:
            with self.subTest(raw=raw):
                result=parse_post(raw)
                self.assertIsNone(result['post_body'])
                self.assertEqual(result['format_status'],'invalid_tags')


if __name__=='__main__':unittest.main()
