"""V5 sampling/storage/independent-source checks, never model failures."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import scale_fixtures as s


class ScaleFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = s.scale_make_cases(6, 255128, tier=128)
        cls.long = s.scale_make_cases(1, 255192, tier=192, split="audit")[0]

    def test_independent_full_source_checks_both_tiers(self):
        result = s.scale_audit_fixtures(iter(self.cases + [self.long]))
        self.assertEqual(result["n_cases"], 7)
        self.assertTrue(result["passed"])
        self.assertEqual(set(result["family_counts"]), set(s.SCALE_FAMILIES))
        full = s.scale_audit_case(self.long, include_traces=True)
        self.assertEqual(full["answer"], self.long["gold"])
        self.assertEqual(full["ordered_units"] - full["net_dispatch_units"], full["open_units"])
        self.assertIn("independent_text_fraction_trace", full)
        self.assertEqual(self.long["created_at"], "2026-10-26")

    def test_chunking_and_family_balance(self):
        chunks = s.scale_make_cases(2, 255128, tier=128) + s.scale_make_cases(4, 255128, tier=128, start_index=2)
        self.assertEqual(chunks, self.cases)
        self.assertEqual(len({c["family"] for c in chunks}), 6)
        self.assertEqual(len({c["case_id"] for c in chunks}), 6)

    def test_seed_split_tier_domain_separation(self):
        variants = [s.scale_make_cases(1, seed, tier=tier, split=split)[0]
                    for seed, tier, split in [(255128,128,"pilot"),(255129,128,"pilot"),
                                              (255128,192,"pilot"),(255128,128,"audit"),
                                              (255128,128,"collection")]]
        self.assertEqual(len({c["case_id"] for c in variants}), 5)
        self.assertEqual(len({c["semantic_hash"] for c in variants}), 5)

    def test_no_label_or_gold_enters_solver_input(self):
        visible = s.scale_model_input(self.cases[0])
        self.assertEqual(set(visible), {"case_id","task_instructions","documents"})
        self.assertEqual(visible["documents"], self.cases[0]["document"])
        self.assertEqual(visible["task_instructions"], s.SCALE_TASK_INSTRUCTIONS)

    def test_checker_value_schema_and_evidence_are_distinct(self):
        c = self.cases[0]
        good = s.scale_correct_response(c)
        self.assertTrue(s.scale_validate_answer(c,good)["accepted"])
        value = copy.deepcopy(good);value["answer"]["quantity_units"] += 1
        checked = s.scale_validate_answer(c,value)
        self.assertTrue(checked["valid_schema"]);self.assertFalse(checked["exact_fields"])
        typed = copy.deepcopy(good);typed["answer"]["quantity_units"] = True
        self.assertFalse(s.scale_validate_answer(c,typed)["valid_schema"])
        cites = copy.deepcopy(good);cites["evidence"]["quantity_units"] = ["P06"]
        checked = s.scale_validate_answer(c,cites)
        self.assertTrue(checked["exact_fields"]);self.assertFalse(checked["accepted"])
        extra = copy.deepcopy(good);extra["answer"]["extra"] = "forbidden"
        self.assertFalse(s.scale_validate_answer(c,extra)["valid_schema"])

    def test_source_and_reference_mutations_fail(self):
        c = copy.deepcopy(self.cases[0])
        c["gold"]["quantity_units"] += 1
        with self.assertRaises(ValueError):s.scale_audit_case(c)
        c = copy.deepcopy(self.cases[0]);c["document"] = c["document"].replace("SH-04", "MISSING-SHIPMENT", 1)
        with self.assertRaises(ValueError):s.scale_audit_case(c)

    def test_embedded_sources_are_isolated_and_hash_locked(self):
        base = Path(s.__file__).parent
        sources = {name:(base/name).read_text(encoding="utf-8-sig") for name in s.SCALE_CORE_SHA256}
        namespace={"__name__":"scale_embedded_test", "HIGH_FIELDS":["untouched"]}
        exec(compile(Path(s.__file__).read_text(),"embedded_scale", "exec"), namespace)
        namespace["scale_load_cores"](core_sources=sources)
        self.assertEqual(namespace["HIGH_FIELDS"], ["untouched"])
        self.assertEqual(namespace["scale_make_cases"](1,255128,128)[0],self.cases[0])
        sources["high_fixtures.py"] += "\n# unauthorized source drift\n"
        with self.assertRaises(ValueError):namespace["scale_load_cores"](core_sources=sources)

    def test_zero_and_invalid_generation(self):
        self.assertEqual(s.scale_make_cases(0,1), [])
        self.assertEqual(s.scale_audit_fixtures([])["n_cases"], 0)
        for kwargs in [{"n":True,"seed":1},{"n":1,"seed":True},{"n":1,"seed":1,"tier":64},
                       {"n":1,"seed":1,"start_index":-1},{"n":1,"seed":1,"split":"unknown"}]:
            with self.assertRaises(ValueError):s.scale_make_cases(**kwargs)

    def test_deterministic_compressed_roundtrip_and_full_reaudit(self):
        with tempfile.TemporaryDirectory(prefix="scale_fixture_test_") as directory:
            root=Path(directory)
            a=root/"a.jsonl.gz";b=root/"b.jsonl.gz"
            first=s.scale_write_corpus(a, iter(self.cases[:2]))
            second=s.scale_write_corpus(b, iter(self.cases[:2]))
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(list(s.scale_iter_corpus(a,first)), self.cases[:2])
            raw=gzip.decompress(a.read_bytes())
            self.assertNotIn(b"\r\n",raw);self.assertTrue(raw.endswith(b"\n"))
            self.assertEqual(hashlib.sha256(raw).hexdigest(),first["uncompressed_sha256"])
            self.assertTrue(s.scale_verify_corpus(a)["passed"])
            self.assertEqual(len(first["case_index"]),2)
            self.assertEqual(first["case_index"][0]["content_hash"],self.cases[0]["content_hash"])
            with self.assertRaises(ValueError):s.scale_write_corpus(a, [])
            self.assertEqual(a.read_bytes(),b.read_bytes())
            changed=copy.deepcopy(first);changed["case_index"][0]["semantic_hash"]="wrong"
            manifest=root/(a.name+".manifest.json")
            manifest.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):s.scale_verify_corpus(a,full_audit=False)

    def test_incomplete_or_duplicate_corpus_is_not_left_as_complete(self):
        with tempfile.TemporaryDirectory(prefix="scale_fixture_failure_test_") as directory:
            root=Path(directory);path=root/"bad.jsonl.gz"
            with self.assertRaises(ValueError):s.scale_write_corpus(path,[self.cases[0],self.cases[0]])
            self.assertEqual(list(root.iterdir()),[])
            m=s.scale_write_corpus(path,[self.cases[0]])
            with self.assertRaises(ValueError):s.scale_check_cohort_overlap([m,m])
            self.assertTrue(s.scale_check_cohort_overlap([m])["passed"])
            path.write_bytes(path.read_bytes()+b"tampered")
            with self.assertRaises(ValueError):list(s.scale_iter_corpus(path,m))

    def test_preflight_generic_blocks_and_cross_cohort_check(self):
        with tempfile.TemporaryDirectory(prefix="scale_preflight_test_") as directory:
            result=s.scale_preflight_cohorts(directory,[
                {"name":"pilot128","n":1,"seed":81,"tier":128,"split":"pilot"},
                {"name":"audit192","n":1,"seed":82,"tier":192,"split":"audit"}])
            self.assertEqual(result["cross_cohort_audit"]["n_cases"],2)
            self.assertEqual(result["live_calls"],0)
            self.assertFalse(list(Path(directory).glob("*.jsonl")))
            with self.assertRaises(ValueError):s.scale_preflight_cohorts(directory,[{"name":"../bad"}])

    def test_previous_corpus_inventory_and_overlap(self):
        with tempfile.TemporaryDirectory(prefix="scale_prior_inventory_test_") as directory:
            root=Path(directory)
            plain=root/"old.jsonl"
            plain.write_text("\n".join(json.dumps(c) for c in self.cases[:2])+"\n",encoding="utf-8")
            packed=root/"snapshot.jsonl.gz"
            with gzip.open(packed,"wt",encoding="utf-8") as stream:
                stream.write(json.dumps(self.cases[0])+"\n")
            inventory=s.scale_previous_corpus_keys([plain,packed])
            self.assertEqual(inventory["n_rows"],3)
            self.assertEqual(inventory["n_unique_ids"],2)
            self.assertEqual(len(inventory["source_files"]),2)
            self.assertTrue(s.scale_check_previous_overlap(self.cases[2:],inventory)["passed"])
            with self.assertRaises(ValueError):s.scale_check_previous_overlap(self.cases,inventory)
            broken=root/"not_sources.jsonl";broken.write_text('{"result":"not a source case"}\n')
            with self.assertRaises(ValueError):s.scale_previous_corpus_keys([broken])


if __name__ == "__main__":unittest.main()
