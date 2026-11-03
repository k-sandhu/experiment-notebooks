import unittest
import paid_decision_study as paid
import smoke_study as s


class PaidDecisionTests(unittest.TestCase):
    def test_exact_old_gpt_request_can_be_reused(self):
        protocol=s.load(paid.ROOT/'data/decision_audit/protocol.json')
        post=s.load(paid.ROOT/'data/main/responses/01-kimi/gpt-6.1-sol/01.json')
        article=next(a for a in s.load(paid.ROOT/'data/main/articles.json') if a['item_id']=='01-kimi')
        source=(paid.ROOT/article['local_input']).read_text(encoding='utf-8')
        payloads=paid.payloads(s.split_response(post['text'])['body'],source,protocol,'gpt')
        self.assertEqual(sum(len(p['questions']) for p in payloads),240)
        for payload in payloads:
            key=s.sha(s.canonical(payload))
            self.assertTrue((paid.ROOT/'data/decision_audit/responses'/f'{key}.json').exists())

    def test_retry_is_overlay_and_raw_is_not_silently_repaired(self):
        old=s.load(paid.ROOT/'data/simple_prose_v3_full/responses/14-seti/gpt-6.1-sol/02.json')
        value=paid.record_for('expanded','14-seti','gpt-6.1-sol',2)
        self.assertFalse(old['text'])
        self.assertEqual(value['record']['retry_of'],old['request_sha256'])
        self.assertEqual(value['text'],value['record']['text'])
        self.assertFalse(value['strict_readable'])

    def test_model_routing_does_not_pass_writer_or_condition_metadata(self):
        protocol=s.load(paid.ROOT/'data/decision_audit/protocol.json')
        for ident,profile in paid.MODELS.items():
            payloads=paid.payloads('A post.','An article.',protocol,ident)
            self.assertEqual(len({v['state'] for v in payloads}),1)
            names=[name for payload in payloads for name in payload['questions']]
            self.assertEqual(len(names),len(set(names)))
            for payload in payloads:
                self.assertEqual(set(payload),{'model','state','questions','provider'})
                self.assertFalse(payload['provider']['allow_fallbacks'])
                self.assertEqual(payload['model'],profile['model'])


if __name__=='__main__':unittest.main()
