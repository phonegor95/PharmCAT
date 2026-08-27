#!/usr/bin/env python3
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
