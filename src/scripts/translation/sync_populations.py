#!/usr/bin/env python3
"""Synchronize only population labels from an approved multilingual preset.

Defaults to a read-only check. Match native guidance IDs, never report row order.
"""
import argparse
import copy
import json
from pathlib import Path
import re


REPORTER = Path(__file__).resolve().parents[2] / 'main/resources/org/pharmgkb/pharmcat/reporter'


def translations(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('source_locale') != 'en' or data.get('field') != 'Population':
        raise ValueError('Invalid population preset')
    pairs = {}
    for row in data['populations']:
        label = row.get('en')
        if not isinstance(label, str) or not label or label in pairs:
            raise ValueError('Missing or duplicate English population')
        for locale in data['locales']:
            if not isinstance(row.get(locale), str) or not row[locale].strip():
                raise ValueError(f'Missing {locale} translation for {label}')
        pairs[label] = row['zh-cn']
    if '-' in pairs:
        raise ValueError('Duplicate unspecified sentinel')
    pairs['-'] = '-'
    return pairs


def indexed(data):
    result = {}
    for group in data['guidelines']:
        guideline = group['guideline']
        for rec in group['recommendations']:
            key = (guideline['source'], guideline['id'], rec['id'])
            if key in result:
                raise ValueError('Duplicate native guidance identity')
            result[key] = (guideline, rec)
    return result


def synchronize(english, chinese, pairs):
    result = copy.deepcopy(chinese)
    en, zh = indexed(english), indexed(result)
    if not en or en.keys() != zh.keys():
        raise ValueError('Guidance recommendation IDs differ')
    expected = {rec.get('population') for _, rec in en.values()} - {None}
    expected.add('-')
    if expected != pairs.keys():
        raise ValueError(f'Population coverage mismatch: missing={sorted(expected - pairs.keys())}, '
                         f'extra={sorted(pairs.keys() - expected)}')
    changed = 0
    for key, (guideline, rec) in en.items():
        target_guideline, target = zh[key]
        if guideline['version'] != target_guideline['version']:
            raise ValueError('Guidance versions differ')
        for field in ('lookupKey', 'relatedChemicals'):
            if rec[field] != target[field]:
                raise ValueError(f'Guidance mismatch: {field}')
        label = rec.get('population')
        value = None if label is None else pairs[label]
        changed += target.get('population') != value
        if 'population' in rec:
            target['population'] = value
        elif 'population' in target:
            raise ValueError('Unexpected population field')
    return result, changed


def render(original, updated):
    values = iter(rec['population'] for group in updated['guidelines']
                  for rec in group['recommendations'] if 'population' in rec)
    pattern = re.compile(r'("population"\s*:\s*)(?:null|"(?:[^"\\]|\\.)*")')
    text = pattern.sub(lambda m: m[1] + json.dumps(next(values), ensure_ascii=False), original)
    if json.loads(text) != updated:
        raise ValueError('Population-only rendering did not preserve guidance')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset', type=Path, required=True)
    parser.add_argument('--english', type=Path, default=REPORTER / 'prescribing_guidance.v3.4.0.json')
    parser.add_argument('--chinese', type=Path, default=REPORTER / 'prescribing_guidance.json')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    original = args.chinese.read_text(encoding='utf-8')
    pairs = translations(args.preset)
    updated, changed = synchronize(json.loads(args.english.read_text(encoding='utf-8')),
                                   json.loads(original), pairs)
    if args.apply and changed:
        args.chinese.write_text(render(original, updated), encoding='utf-8')
    print(f'{len(pairs)} exact labels; {len(indexed(updated))} recommendations; '
          f'{changed} population values {"updated" if args.apply else "differ"}')
    if changed and not args.apply:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
