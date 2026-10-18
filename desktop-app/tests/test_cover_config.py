"""User preference values must remain portable and safe, including future clients."""
import copy
import json
import unittest
from pathlib import Path
from cover_config import normalize_config

VECTORS = json.loads((Path(__file__).parent / 'fixtures/cover-config.json').read_text())

class CoverConfigTests(unittest.TestCase):
    def test_shared_values_defaults_and_future_roundtrip_without_mutation(self):
        for case in VECTORS['valid']:
            with self.subTest(case=case['name']):
                before = copy.deepcopy(case['input'])
                actual = normalize_config(case['input'])
                self.assertEqual(case['input'], before)
                if 'want' in case:
                    self.assertEqual(actual, case['want'])
                else:
                    for key, value in case['subset'].items():
                        self.assertEqual(actual[key], value)
                if actual is not None:
                    self.assertEqual(normalize_config(actual), actual)
                    actual['new'] = True
                    self.assertEqual(case['input'], before)

    def test_rejects_invalid_types_unsafe_values_and_unbounded_json(self):
        for value in VECTORS['invalid'] + [
            {'customTitle': '中' * 201}, {'customSubtitle': 's' * 241},
            {'extra': '中' * 3000}, {'imageX': float('nan')},
            {'extra': float('inf')}, {'version': 2, 'extra': float('nan')},
            {'extra': object()}, {'primary': None}, {'extra': '\ud800'},
        ]:
            with self.subTest(value=repr(value)[:120]):
                with self.assertRaises(ValueError):
                    normalize_config(value)

if __name__ == '__main__':
    unittest.main()
