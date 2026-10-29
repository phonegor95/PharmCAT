import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'src/scripts/translation'))
from sync_populations import render, synchronize, translations


class PopulationSyncTest(unittest.TestCase):
    def guidance(self):
        return {'guidelines': [{'guideline': {'source': 'CPIC', 'id': 'G1', 'version': 1},
                'recommendations': [{'id': str(i), 'population': value, 'lookupKey': [],
                                     'relatedChemicals': [], 'text': {'html': 'Unchanged'}}
                                    for i, value in enumerate(('general', 'adults', None))]}]}

    def test_native_identity_and_null_preservation(self):
        en = self.guidance()
        cn = copy.deepcopy(en)
        cn['guidelines'][0]['recommendations'].reverse()
        pairs = {'general': '一般人群', 'adults': '成人', '-': '-'}
        updated, changed = synchronize(en, cn, pairs)
        self.assertEqual(changed, 2)
        self.assertEqual([r['population'] for r in updated['guidelines'][0]['recommendations']],
                         [None, '成人', '一般人群'])
        self.assertEqual(synchronize(en, updated, pairs)[1], 0)
        self.assertEqual(json.loads(render(json.dumps(cn, indent=2), updated)), updated)
        self.assertEqual(en, self.guidance())

    def test_missing_extra_and_identity_drift_fail(self):
        en = self.guidance()
        pairs = {'general': '一般人群', 'adults': '成人', '-': '-'}
        for bad in ({'general': '一般人群', '-': '-'}, {**pairs, 'unknown': '未知'}):
            with self.assertRaisesRegex(ValueError, 'coverage mismatch'):
                synchronize(en, en, bad)
        cn = copy.deepcopy(en)
        cn['guidelines'][0]['recommendations'][0]['id'] = 'different'
        with self.assertRaisesRegex(ValueError, 'IDs differ'):
            synchronize(en, cn, pairs)
        cn = copy.deepcopy(en)
        cn['guidelines'][0]['recommendations'][0]['lookupKey'] = ['different']
        with self.assertRaisesRegex(ValueError, 'lookupKey'):
            synchronize(en, cn, pairs)

    def test_all_locales_required_and_sentinel_is_implicit(self):
        data = {'source_locale': 'en', 'field': 'Population', 'locales': ['zh-cn', 'ja'],
                'populations': [{'en': 'general', 'zh-cn': '一般人群', 'ja': '一般集団'}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preset.json'
            path.write_text(json.dumps(data))
            self.assertEqual(translations(path), {'general': '一般人群', '-': '-'})
            data['populations'][0]['ja'] = ''
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'Missing ja'):
                translations(path)
            data['populations'][0]['ja'] = '一般集団'
            data['populations'].append({'en': '-', 'zh-cn': '-', 'ja': '-'})
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'Duplicate unspecified'):
                translations(path)


if __name__ == '__main__':
    unittest.main()
