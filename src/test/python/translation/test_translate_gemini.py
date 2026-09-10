#!/usr/bin/env python3
"""Offline contracts only: no google SDK, credentials, network or real guidance."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / 'src/scripts/translation'
sys.path.insert(0, str(TOOLS))
import translate_gemini as driver


class TranslateGeminiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.todo = self.base / 'todo.json'
        self.glossary = self.base / 'glossary.json'
        self.output = self.base / 'draft.json'
        self.cache = self.base / 'cache.json'
        self.items = [
            {'kind': 'text', 'en': '<p id="dose">Use 25 mg.</p>', 'cn': '',
             'hint_en': 'Use a dose.', 'hint_cn': '使用剂量。', 'hint_similarity': 0.5},
            {'kind': 'impl', 'en': 'CYP2D6: Effect unknown.', 'cn': ''},
        ]
        self.write(self.todo, self.items)
        self.write(self.glossary, {'effect': '影响'})

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def args(self, **options):
        values = {'todo': self.todo, 'glossary': self.glossary, 'model': 'explicit-test-model',
                  'output': self.output, 'cache': self.cache}
        values.update(options)
        return [str(part) for key, value in values.items() if value is not None
                for part in ('--' + key.replace('_', '-'), value)]

    @staticmethod
    def response(**kwargs):
        items = json.loads(kwargs['contents'])['todo']
        for item in items:
            item['cn'] = ('<p id="dose">使用25 mg。</p>' if item['kind'] == 'text'
                          else 'CYP2D6: 影响不明。')
        return json.dumps(items, ensure_ascii=False)

    def run_cli(self, fake=None, **options):
        with patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO) as err:
            result = driver.main(self.args(**options), generate=fake)
        return result, err.getvalue()

    def test_default_prompt_sent_in_batch_and_every_fallback(self):
        calls = []

        def generate(**kwargs):
            calls.append(kwargs)
            return 'not JSON' if len(calls) == 1 else self.response(**kwargs)

        self.assertEqual(0, self.run_cli(generate)[0])
        self.assertEqual([2, 1, 1], [len(json.loads(c['contents'])['todo']) for c in calls])
        for call in calls:
            self.assertEqual(driver.DEFAULT_PROMPT.read_text(), call['config']['system_instruction'])
            self.assertEqual('explicit-test-model', call['model'])
            self.assertEqual(driver.pgcore.CANONICAL, json.loads(call['contents'])['glossary']['canonical'])
        draft = json.loads(self.output.read_text())
        for before, after in zip(self.items, draft):
            self.assertEqual({k: v for k, v in before.items() if k != 'cn'},
                             {k: v for k, v in after.items() if k != 'cn'})
        provenance = json.loads(Path(str(self.output) + '.provenance.json').read_text())
        self.assertEqual('unreviewed_draft', provenance['review_status'])
        self.assertEqual([], provenance['unresolved_indices'])

    def test_batch_success_is_one_call_and_never_changes_inputs(self):
        before = {p: p.read_bytes() for p in (self.todo, self.glossary, driver.DEFAULT_PROMPT)}
        fake = Mock(side_effect=self.response)
        self.assertEqual(0, self.run_cli(fake)[0])
        self.assertEqual(1, fake.call_count)
        for path, contents in before.items():
            self.assertEqual(contents, path.read_bytes())

    def test_schema_rejects_count_order_keys_source_kind_hints_and_types(self):
        valid = copy.deepcopy(self.items)
        for item in valid:
            item['cn'] = ''
        invalid = [valid[:1], list(reversed(valid)), {'items': valid}]
        changes = {'en': 'changed', 'kind': 'impl', 'cn': None, 'hint_en': 'changed',
                   'hint_cn': 1, 'hint_similarity': True, 'extra': 'not allowed'}
        for key, value in changes.items():
            case = copy.deepcopy(valid)
            case[0][key] = value
            invalid.append(case)
        case = copy.deepcopy(valid)
        del case[0]['hint_en']
        invalid.append(case)
        for response in invalid:
            with self.subTest(response=response), self.assertRaises(driver.InvalidDraft):
                driver.validate_response(self.items, response)
        with self.assertRaises(driver.InvalidDraft):
            driver.parse_json('[{"kind":"text","kind":"impl","en":"a","cn":""}]')
        # Numeric equality alone must not permit changes to hint types.
        source = [{'kind': 'text', 'en': 'a', 'cn': '', 'hint_similarity': 1}]
        with self.assertRaises(driver.InvalidDraft):
            driver.validate_response(source, [{**source[0], 'hint_similarity': 1.0}])

    def test_invalid_response_is_not_accepted_or_cached(self):
        fake = Mock(return_value='[{"kind":"text","en":"wrong","cn":"错误"}]')
        self.assertEqual(2, self.run_cli(fake)[0])
        self.assertEqual(3, fake.call_count)
        self.assertEqual(self.items, json.loads(self.output.read_text()))
        self.assertEqual({}, json.loads(self.cache.read_text())['entries'])

    def test_blank_response_is_unresolved_not_retried_or_cached(self):
        fake = Mock(return_value=json.dumps(self.items))
        self.assertEqual(2, self.run_cli(fake)[0])
        self.assertEqual(1, fake.call_count)
        self.assertEqual({}, json.loads(self.cache.read_text())['entries'])
        self.assertEqual([0, 1], json.loads(Path(str(self.output) + '.provenance.json').read_text())['unresolved_indices'])

    def test_whitespace_blank_is_retained_not_cached(self):
        items = [{**item, 'cn': '  '} for item in self.items]
        self.assertEqual(2, self.run_cli(Mock(return_value=json.dumps(items)))[0])
        self.assertEqual(items, json.loads(self.output.read_text()))
        self.assertEqual({}, json.loads(self.cache.read_text())['entries'])

    def test_network_failure_aborts_without_fallback_or_secret_logging(self):
        fake = Mock(side_effect=RuntimeError('SECRET_KEY private request payload'))
        status, error = self.run_cli(fake)
        self.assertEqual(1, status)
        self.assertIn('credentials, model access, quota and network', error)
        self.assertNotIn('SECRET_KEY', error)
        self.assertEqual(1, fake.call_count)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.cache.exists())

    def test_prefilled_items_are_untouched_and_not_cached(self):
        items = [{**item, 'cn': '人工待审译文'} for item in self.items]
        self.write(self.todo, items)
        with patch.object(driver, 'make_generate', side_effect=AssertionError('must not initialize SDK')):
            self.assertEqual(0, self.run_cli()[0])
        self.assertEqual(items, json.loads(self.output.read_text()))
        self.assertEqual({}, json.loads(self.cache.read_text())['entries'])

    def test_cache_reuse_and_context_separation(self):
        self.assertEqual(0, self.run_cli(Mock(side_effect=self.response))[0])
        original_cache = self.cache.read_bytes()
        self.assertEqual(0, self.run_cli(Mock(side_effect=AssertionError('cache miss')),
                                       output=self.base / 'cached.json', cache=None,
                                       cache_input=self.cache)[0])
        alternate_prompt = self.base / 'prompt.md'
        alternate_prompt.write_text(driver.DEFAULT_PROMPT.read_text() + '\nAdditional instruction.\n')
        alternate_glossary = self.base / 'glossary2.json'
        self.write(alternate_glossary, {'effect': '作用'})
        for i, change in enumerate(({'model': 'other-model'}, {'prompt': alternate_prompt},
                                    {'glossary': alternate_glossary}, {'batch_size': 1})):
            fake = Mock(side_effect=self.response)
            self.assertEqual(0, self.run_cli(fake, output=self.base / f'other{i}.json',
                                           cache=None, cache_input=self.cache, **change)[0])
            self.assertGreater(fake.call_count, 0)
        self.assertEqual(original_cache, self.cache.read_bytes())
        item = self.items[0]
        key = driver.cache_key(item)
        for change in ({'kind': 'impl'}, {'en': item['en'] + ' '}, {'hint_cn': '新提示'}):
            self.assertNotEqual(key, driver.cache_key({**item, **change}))

    def test_legacy_and_wrong_version_caches_are_rejected(self):
        for cache in ({'English': '中文'}, {'context': {'version': 0},
                                            'review_status': 'unreviewed_draft', 'entries': {}}):
            self.write(self.cache, cache)
            fake = Mock(side_effect=self.response)
            self.assertEqual(1, self.run_cli(fake, cache=None, cache_input=self.cache)[0])
            fake.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_existing_draft_cache_or_sidecar_never_overwritten(self):
        for path in (self.output, self.cache, Path(str(self.output) + '.provenance.json')):
            path.write_text('KEEP')
            fake = Mock(side_effect=self.response)
            self.assertEqual(1, self.run_cli(fake)[0])
            fake.assert_not_called()
            self.assertEqual('KEEP', path.read_text())
            path.unlink()

    def test_paths_cannot_alias_inputs_each_other_or_resources(self):
        for change in ({'output': self.todo}, {'output': self.glossary},
                       {'cache': self.todo}, {'cache': self.output},
                       {'cache': Path(str(self.output) + '.provenance.json')},
                       {'output': ROOT / 'src/main/resources/never-write-draft.json'},
                       {'output': driver.DEFAULT_PROMPT}):
            with self.subTest(change=change):
                fake = Mock(side_effect=self.response)
                self.assertEqual(1, self.run_cli(fake, **change)[0])
                fake.assert_not_called()
        self.output.symlink_to(self.todo)
        self.assertEqual(1, self.run_cli(Mock(side_effect=self.response))[0])
        self.assertEqual(self.items, json.loads(self.todo.read_text()))

    def test_no_overwrite_if_output_created_during_request(self):
        def racing_response(**kwargs):
            self.output.write_text('OTHER PROCESS')
            return self.response(**kwargs)
        self.assertEqual(1, self.run_cli(racing_response)[0])
        self.assertEqual('OTHER PROCESS', self.output.read_text())
        self.assertFalse(self.cache.exists())

    def test_literal_changes_rejected(self):
        for en, cn in (('<p id="x">Use 25 mg.</p>', '<p id="y">使用25 mg。</p>'),
                       ('Use 25 mg.', '使用26 mg。'), ('CYP2D6: Unknown.', 'CYP2C9: 不明。'),
                       ('Risk &gt; 5%', '风险大于5%')):
            with self.subTest(en=en), self.assertRaises(driver.InvalidDraft):
                driver.validate_literals({'kind': 'impl', 'en': en, 'cn': cn})

    def test_inline_gene_identifiers_allow_adjacent_chinese(self):
        driver.validate_literals({'kind': 'text',
                                  'en': 'A NAT2 normal metabolizer AND a TPMT normal metabolizer.',
                                  'cn': 'NAT2正常代谢者和TPMT正常代谢者。'})
        driver.validate_literals({'kind': 'impl',
                                  'en': 'HLA-B: rs123 OR *15:02.',
                                  'cn': 'HLA-B: rs123或*15:02。'})
        with self.assertRaises(driver.InvalidDraft):
            driver.validate_literals({'kind': 'text', 'en': 'NAT2 normal metabolizer.',
                                      'cn': 'CYP2D6正常代谢者。'})

    def test_import_help_and_tests_need_no_sdk_or_keys(self):
        # -S disables site-packages, so this tests real execution without google-genai.
        proc = subprocess.run([sys.executable, '-S', str(TOOLS / 'translate_gemini.py'), '--help'],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn('--model MODEL', proc.stdout)
        self.assertIn('UNREVIEWED', proc.stdout)
        with patch.dict(sys.modules, {'google': None}):
            spec = importlib.util.spec_from_file_location('driver_import_test', TOOLS / 'translate_gemini.py')
            spec.loader.exec_module(importlib.util.module_from_spec(spec))
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(driver.RequestFailed):
            driver.make_generate()


if __name__ == '__main__':
    unittest.main()
