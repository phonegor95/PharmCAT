#!/usr/bin/env python3
"""Rebuild the translated file on top of a new upstream release.

Takes upstream's untranslated file, substitutes Chinese into the two translated
fields from the translation memory plus the filled-in work list, and applies the
canonical terminology map. Everything outside those two fields is left exactly
as upstream wrote it.

    src/scripts/translation/apply.py --tm tm.json --new /tmp/new.json --todo todo.json

By default this refuses to write a partially translated file.
"""
import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tm', type=Path, required=True)
    ap.add_argument('--new', type=Path, required=True,
                    help='new upstream prescribing_guidance.json (untranslated)')
    ap.add_argument('--todo', type=Path,
                    help='work list from plan_merge.py with "cn" filled in')
    ap.add_argument('-o', '--out', type=Path, default=pgcore.GUIDANCE,
                    help='output (default: %(default)s, i.e. in place)')
    ap.add_argument('--reference-out', type=Path,
                    help='also write upstream\'s file here as the new English reference '
                         '(e.g. .../prescribing_guidance.v3.5.0.json)')
    ap.add_argument('--allow-partial', action='store_true',
                    help='write even if some strings are still untranslated')
    ap.add_argument('--no-terminology', action='store_true',
                    help='skip the canonical terminology pass')
    args = ap.parse_args()

    tm = pgcore.load(args.tm)
    lookup = {'text': dict(tm['text']), 'impl': dict(tm['impl'])}
    if args.todo:
        blank = 0
        for entry in pgcore.load(args.todo):
            if not entry.get('cn'):
                blank += 1
                continue
            lookup[entry['kind']][entry['en']] = entry['cn']
        if blank:
            print(f'work list: {blank} entries still have an empty "cn"')

    data = pgcore.load(args.new)
    idx = {k: pgcore.build_lookup(lookup[k]) for k in ('text', 'impl')}
    untranslated = []
    via_norm = 0
    for gi, ri, kind, si, value in list(pgcore.iter_fields(data)):
        cn, how = pgcore.lookup(*idx[kind], value)
        if cn is not None:
            pgcore.set_field(data, gi, ri, kind, si, cn)
            if how == 'normalized':
                via_norm += 1
        else:
            untranslated.append((kind, value))
    if via_norm:
        print(f'{via_norm} field values matched after normalizing markup differences')

    if untranslated:
        print(f'\n{len(untranslated)} field values have no translation:')
        for kind, value in untranslated[:5]:
            print(f'  [{kind}] {value[:110]}')
        if not args.allow_partial:
            raise SystemExit('\nrefusing to write a partial translation '
                             '(pass --allow-partial to override)')

    # Canonical terminology, applied to old and new translations alike.
    counts = collections.Counter()
    if not args.no_terminology:
        for gi, ri, kind, si, value in list(pgcore.iter_fields(data)):
            new_value = value
            for variant, canon in pgcore.CANONICAL.items():
                if variant in new_value:
                    counts[variant] += new_value.count(variant)
                    new_value = new_value.replace(variant, canon)
            if new_value != value:
                pgcore.set_field(data, gi, ri, kind, si, new_value)
        if counts:
            print('\nterminology normalized:')
            for variant, n in counts.most_common():
                print(f'  {n:>5}  {variant} -> {pgcore.CANONICAL[variant]}')

    pgcore.dump(data, args.out)
    print(f'\nwrote {args.out}')

    if args.reference_out:
        pgcore.dump(pgcore.load(args.new), args.reference_out)
        print(f'wrote {args.reference_out} (new English reference — delete the old one)')

    print('\nNow run verify.py before building an image.')


if __name__ == '__main__':
    main()
