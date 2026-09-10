#!/usr/bin/env python3
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "src" / "scripts" / "translation"
sys.path.insert(0, str(TOOLS))

import build_tm  # noqa: E402
import html_align  # noqa: E402
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
    def test_lookup_prefers_exact_then_normalized_markup(self):
        exact, normalized = pgcore.build_lookup({"Dose &gt; 5": "剂量&gt;5"})
        self.assertEqual(("剂量&gt;5", "exact"), pgcore.lookup(exact, normalized, "Dose &gt; 5"))
        self.assertEqual(("剂量&gt;5", "normalized"), pgcore.lookup(exact, normalized, "Dose > 5"))

    def test_translation_memory_reports_conflicting_source_strings(self):
        en = guidance("same", "same")
        cn = guidance("中文一", "中文二")
        memory, conflicts = build_tm.build_from_data(en, cn)
        self.assertEqual("中文一", memory["text"]["same"])
        self.assertEqual("中文二", memory["impl"]["same"])
        self.assertEqual([], conflicts)

        en["guidelines"][0]["recommendations"].append({
            "id": "r2", "text": {"html": "same"}, "implications": []})
        cn["guidelines"][0]["recommendations"].append({
            "id": "r2", "text": {"html": "不同翻译"}, "implications": []})
        _memory, conflicts = build_tm.build_from_data(en, cn)
        self.assertEqual(1, len(conflicts))

    def test_pair_rejects_structure_mismatch(self):
        en, cn = guidance("English"), guidance("中文")
        cn["guidelines"][0]["recommendations"][0]["implications"].append("extra")
        with self.assertRaises(SystemExit):
            list(pgcore.pair(en, cn))

    def test_atomic_dump_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "data.json"
            pgcore.dump({"中文": [1, 2]}, path)
            self.assertEqual({"中文": [1, 2]}, pgcore.load(path))
            self.assertFalse(path.read_bytes().endswith(b"\n"))

    def test_html_alignment_never_changes_text(self):
        source = "中文≤值<br />\n</li>"
        expected_markup = "English &le; value<br/>\n</li>"
        self.assertEqual("中文&le;值<br/>\n</li>", html_align.align(source, expected_markup))


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


class GuidanceFidelityTest(unittest.TestCase):
    """Exercise the shipped data against aligned English, not synthetic prose."""

    @classmethod
    def setUpClass(cls):
        cls.cn = pgcore.load(ROOT / pgcore.GUIDANCE)
        cls.en = pgcore.load(pgcore.find_reference(ROOT / pgcore.REPORTER_DIR))
        cls.pairs = list(pgcore.pair(cls.en, cls.cn))

    def test_only_translation_fields_differ_from_english(self):
        for diff in verify.structural_diff(self.en, self.cn):
            with self.subTest(diff=diff):
                self.assertTrue(diff.endswith(": value differs"))
                self.assertRegex(diff.removesuffix(": value differs"),
                                 verify.TRANSLATED_PATH)

    def test_absent_impact_is_not_absent_recommendation(self):
        matched = 0
        phenotypes = {
            "a normal metabolizer": "正常代谢者表型",
            "a rapid metabolizer": "快代谢者表型",
            "a ultrarapid metabolizer": "超快代谢者表型",
            "the increased function": "功能增强表型",
            "the normal function": "正常功能表型",
            "a non-expressor": "非表达者表型",
        }
        for kind, en, cn in self.pairs:
            if kind != "impl" or not en.startswith(
                    "The guideline does not provide a description of the impact of "):
                continue
            matched += 1
            with self.subTest(en=en):
                self.assertIn("影响", cn)
                self.assertNotIn("建议", cn)
                self.assertRegex(cn, r"未(?:提供|描述|说明)")
                for phenotype, translation in phenotypes.items():
                    if f"of {phenotype} phenotype on " in en:
                        self.assertIn(translation, cn)
        self.assertGreater(matched, 0)

    def test_actual_absent_recommendations_remain_recommendations(self):
        matched = 0
        for kind, en, cn in self.pairs:
            if (kind == "text" and en.startswith(
                    "<p>The guideline does not provide a recommendation for ")
                    and " in normal metabolizers." in en):
                matched += 1
                with self.subTest(en=en):
                    self.assertIn("建议", cn)
                    self.assertNotIn("影响的描述", cn)
        self.assertGreater(matched, 0)

    def test_quetiapine_and_clomipramine_impact_names(self):
        expected = {
            "The guideline does not provide a description of the impact of a normal metabolizer phenotype on quetiapine.":
                "该指南未提供正常代谢者表型对喹硫平影响的描述。",
            "The guideline does not provide a description of the impact of a rapid metabolizer phenotype on clomipramine.":
                "该指南未提供快代谢者表型对氯米帕明影响的描述。",
        }
        matched = set()
        for kind, en, cn in self.pairs:
            if kind == "impl" and en in expected:
                with self.subTest(en=en):
                    self.assertEqual(expected[en], cn)
                matched.add(en)
        self.assertEqual(set(expected), matched)

    def test_brexpiprazole_uses_canonical_glossary(self):
        matched = 0
        for _kind, en, cn in self.pairs:
            if re.search(r"\bbrexpiprazole\b", en, re.I):
                matched += 1
                with self.subTest(en=en):
                    self.assertIn("布瑞哌唑", cn)
                    for alias, canonical in pgcore.CANONICAL.items():
                        if canonical == "布瑞哌唑":
                            self.assertNotIn(alias, cn)
        self.assertGreater(matched, 0)

    def test_hydralazine_inclusive_boundary_and_lamotrigine_absent_recommendation(self):
        expected = {
            "PA166419602": (
                "<p>Initiate therapy at a total daily dose of 40 to 75 mg. "
                "Carefully titrate dose upward to clinical effect or guideline-recommended dose; "
                "use caution with total daily hydralazine doses of 200 mg or more.</p>\n",
                "<p>起始总日剂量为40-75 mg。仔细调整剂量至临床疗效或指南推荐剂量；"
                "对肼屈嗪总日剂量为200 mg或以上时需谨慎。</p>\n",
            ),
            "PA166299277": (
                "<p>The guideline does not provide a recommendation for lamotrigine in patients "
                "with no HLA-B*15:02 alleles or negative for the HLA-B*15:02 test.</p>\n",
                "<p>该指南未对没有 HLA-B*15:02 等位基因或 HLA-B*15:02 检测结果为阴性的患者"
                "使用拉莫三嗪提供建议。</p>\n",
            ),
        }
        matched = set()
        for eg, cg in zip(self.en["guidelines"], self.cn["guidelines"]):
            for er, cr in zip(eg["recommendations"], cg["recommendations"]):
                if er["id"] in expected:
                    with self.subTest(recommendation=er["id"]):
                        self.assertEqual(expected[er["id"]],
                                         (er["text"]["html"], cr["text"]["html"]))
                    matched.add(er["id"])
        self.assertEqual(set(expected), matched)

    def test_hydralazine_consider_dose_keeps_modality(self):
        expected = {
            "PA166419461": ("rapid", "快"),
            "PA166419601": ("intermediate", "中间"),
        }
        matched = set()
        for eg, cg in zip(self.en["guidelines"], self.cn["guidelines"]):
            for er, cr in zip(eg["recommendations"], cg["recommendations"]):
                if er["id"] not in expected:
                    continue
                metabolizer_en, metabolizer_cn = expected[er["id"]]
                with self.subTest(recommendation=er["id"]):
                    self.assertEqual(
                        "<p>Consider a starting total daily dose of at least 75 mg. "
                        "Titrate up to 300 mg total daily hydralazine dose as tolerated. "
                        f"NAT2 {metabolizer_en} metabolizers typically require a 50-100% "
                        "higher maintenance dose compared to poor metabolizers.</p>\n",
                        er["text"]["html"])
                    self.assertEqual(
                        "<p>可考虑以至少75 mg的总日剂量开始治疗，可据耐受性增至肼屈嗪总日剂量300 mg。"
                        f"NAT2{metabolizer_cn}代谢者的维持剂量通常比慢代谢者高50-100%。</p>\n",
                        cr["text"]["html"])
                matched.add(er["id"])
        self.assertEqual(set(expected), matched)


if __name__ == "__main__":
    unittest.main()
