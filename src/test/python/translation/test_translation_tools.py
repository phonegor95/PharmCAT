#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "src" / "scripts" / "translation"
sys.path.insert(0, str(TOOLS))

import pgcore  # noqa: E402
import verify  # noqa: E402


def guidance(text, implication="GENE: 中文含义"):
    return {
        "guidelines": [{
            "guideline": {"id": "g"},
            "recommendations": [{
                "id": "r",
                "text": {"html": text},
                "implications": [implication],
            }],
        }],
    }


class PgcoreTest(unittest.TestCase):
    def test_pair_rejects_structure_mismatch(self):
        en, cn = guidance("English"), guidance("中文")
        cn["guidelines"][0]["recommendations"][0]["implications"].append("extra")
        with self.assertRaises(SystemExit):
            list(pgcore.pair(en, cn))



class VerifyTest(unittest.TestCase):
    def setUp(self):
        verify.FATAL.clear()
        verify.WARN.clear()

    def test_structure_allows_only_translated_fields(self):
        upstream = guidance("English")
        translated = guidance("中文")
        verify.check_structure(translated, upstream)
        self.assertEqual([], verify.FATAL)
        translated["guidelines"][0]["guideline"]["id"] = "changed"
        verify.check_structure(translated, upstream)
        self.assertTrue(any(check == "structure" for check, _ in verify.FATAL))

    def test_missing_translation_fails(self):
        verify.check_pairs(guidance("This is still a long English recommendation"),
                           guidance("This is still a long English recommendation"))
        self.assertTrue(any(check == "coverage" for check, _ in verify.FATAL))

    def test_dropped_dose_fails(self):
        en = guidance("Use 25 mg daily for treatment")
        cn = guidance("治疗期间每日使用")
        verify.check_pairs(cn, en)
        self.assertTrue(any(check in {"numbers", "clinical tokens"}
                            for check, _ in verify.FATAL))

    def test_canonical_alias_fails(self):
        verify.check_terminology(guidance("使用布美匹唑治疗"))
        self.assertTrue(any(check == "terminology" for check, _ in verify.FATAL))



class PopulationTranslationTest(unittest.TestCase):
    def setUp(self):
        verify.FATAL.clear()
        verify.WARN.clear()

    def test_all_population_labels_in_guidance_are_translated(self):
        reporter = ROOT / pgcore.REPORTER_DIR
        en = pgcore.load(reporter / 'prescribing_guidance.v3.4.0.json')
        cn = pgcore.load(reporter / 'prescribing_guidance.json')
        verify.check_populations(cn, en)
        self.assertEqual([], verify.FATAL)

    def test_null_population_is_preserved(self):
        en, cn = guidance('English'), guidance('中文')
        for data in (en, cn):
            data['guidelines'][0]['recommendations'][0]['population'] = None
        verify.check_populations(cn, en)
        self.assertEqual([], verify.FATAL)
        cn['guidelines'][0]['recommendations'][0]['population'] = '一般人群'
        verify.check_populations(cn, en)
        self.assertTrue(any(kind == 'population' for kind, _ in verify.FATAL))

    def test_population_threshold_is_preserved(self):
        en, cn = guidance('English'), guidance('中文')
        en['guidelines'][0]['recommendations'][0]['population'] = 'child >40kg_adult'
        rec = cn['guidelines'][0]['recommendations'][0]
        rec['population'] = '体重 >40 kg 的儿童及成人'
        verify.check_populations(cn, en)
        self.assertEqual([], verify.FATAL)
        rec['population'] = '体重 >50 kg 的儿童及成人'
        verify.check_populations(cn, en)
        self.assertTrue(any(kind == 'population' for kind, _ in verify.FATAL))

    def test_untranslated_population_is_rejected(self):
        en, cn = guidance('English'), guidance('中文')
        for data in (en, cn):
            data['guidelines'][0]['recommendations'][0]['population'] = 'adults'
        verify.check_populations(cn, en)
        self.assertTrue(any(kind == 'population' for kind, _ in verify.FATAL))

    def test_inconsistent_translation_is_rejected(self):
        import copy
        en, cn = guidance('English'), guidance('中文')
        en['guidelines'][0]['recommendations'][0]['population'] = 'adults'
        cn['guidelines'][0]['recommendations'][0]['population'] = '成人'
        for data in (en, cn):
            rows = data['guidelines'][0]['recommendations']
            rows.append(copy.deepcopy(rows[0]))
        cn['guidelines'][0]['recommendations'][1]['population'] = '儿童'
        verify.check_populations(cn, en)
        self.assertTrue(any(kind == 'population' for kind, _ in verify.FATAL))


if __name__ == "__main__":
    unittest.main()
