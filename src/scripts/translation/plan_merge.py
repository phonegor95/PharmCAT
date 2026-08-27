#!/usr/bin/env python3
"""Report what a new upstream release leaves untranslated.

Applies the translation memory to a new upstream prescribing_guidance.json by
exact English-string match and reports coverage. Whatever the memory cannot
cover is written out as a work list, each entry carrying the closest existing
translation as a style reference.

    git show v3.5.0:src/main/resources/.../prescribing_guidance.json > /tmp/new.json
    src/scripts/translation/plan_merge.py --tm tm.json --new /tmp/new.json -o todo.json
"""
import argparse
import difflib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tm', type=Path, required=True, help='translation memory from build_tm.py')
    ap.add_argument('--new', type=Path, required=True,
                    help='new upstream prescribing_guidance.json (untranslated)')
    ap.add_argument('-o', '--out', type=Path, required=True, help='work list for the translator')
    ap.add_argument('--no-hints', action='store_true',
                    help='skip nearest-match hints (much faster on large gaps)')
    args = ap.parse_args()

    tm = pgcore.load(args.tm)
    new = pgcore.load(args.new)

    idx = {k: pgcore.build_lookup(tm[k]) for k in ('text', 'impl')}
    seen, missing = {'text': set(), 'impl': set()}, {'text': [], 'impl': []}
    covered = {'text': 0, 'impl': 0}
    total = {'text': 0, 'impl': 0}
    via_norm = 0
    for _gi, _ri, kind, _si, value in pgcore.iter_fields(new):
        total[kind] += 1
        cn, how = pgcore.lookup(*idx[kind], value)
        if cn is not None:
            covered[kind] += 1
            if how == 'normalized':
                via_norm += 1
        elif value not in seen[kind]:
            seen[kind].add(value)
            missing[kind].append(value)

    print(f'{"field":12} {"values":>8} {"covered":>8} {"gap":>6}   unique untranslated')
    for kind in ('text', 'impl'):
        gap = total[kind] - covered[kind]
        print(f'{kind:12} {total[kind]:>8} {covered[kind]:>8} {gap:>6}   {len(missing[kind])}')
    n_unique = len(missing['text']) + len(missing['impl'])
    n_values = sum(total.values())
    print(f'\nreuse: {sum(covered.values())}/{n_values} field values '
          f'({100 * sum(covered.values()) / max(n_values, 1):.1f}%) '
          f'covered by the existing translation')
    if via_norm:
        print(f'  ({via_norm} matched only after normalizing markup — see pgcore.match_key)')
    print(f'to translate: {n_unique} unique strings')

    items = []
    for kind in ('text', 'impl'):
        keys = list(tm[kind])
        for value in missing[kind]:
            entry = {'kind': kind, 'en': value, 'cn': ''}
            if not args.no_hints and keys:
                near = difflib.get_close_matches(value, keys, n=1, cutoff=0.0)
                if near:
                    ratio = difflib.SequenceMatcher(None, value, near[0]).ratio()
                    if ratio >= 0.5:
                        entry['hint_en'] = near[0]
                        entry['hint_cn'] = tm[kind][near[0]]
                        entry['hint_similarity'] = round(ratio, 3)
            items.append(entry)

    pgcore.dump(items, args.out)
    print(f'\nwrote {args.out} — fill in each "cn" field, then run apply.py')
    print('Keep HTML tags, id="..." anchors, entities (&quot; &gt; &le;), gene symbols,')
    print('star alleles, rsIDs, PMIDs, doses and units exactly as they appear in "en".')


if __name__ == '__main__':
    main()
