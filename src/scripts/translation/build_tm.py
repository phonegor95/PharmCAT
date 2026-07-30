#!/usr/bin/env python3
"""Build a translation memory from the current translated file.

Pairs the untranslated English reference against the translated file
positionally, giving an English-string -> Chinese-string map that later merges
reuse. This is why the English reference for the current version must be kept
in the repo: without it there is no way to tell which Chinese string corresponds
to which English source string.

    src/scripts/translation/build_tm.py -o tm.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402


def build(en_path, cn_path):
    en_data, cn_data = pgcore.load(en_path), pgcore.load(cn_path)
    tm = {'text': {}, 'impl': {}}
    conflicts = []
    for kind, en, cn in pgcore.pair(en_data, cn_data):
        bucket = tm[kind]
        if en in bucket and bucket[en] != cn:
            conflicts.append((en, bucket[en], cn))
            continue          # keep first occurrence, deterministic
        bucket.setdefault(en, cn)
    return tm, conflicts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--en', type=Path, help='untranslated English reference '
                                            '(default: auto-detect prescribing_guidance.v*.json)')
    ap.add_argument('--cn', type=Path, default=pgcore.GUIDANCE,
                    help='translated file (default: %(default)s)')
    ap.add_argument('-o', '--out', type=Path, required=True, help='output translation memory')
    args = ap.parse_args()

    en_path = args.en or pgcore.find_reference()
    tm, conflicts = build(en_path, args.cn)

    print(f'reference   : {en_path}')
    print(f'translation : {args.cn}')
    print(f'memory      : {len(tm["text"])} unique text.html, '
          f'{len(tm["impl"])} unique implications')
    if conflicts:
        print(f'\nNOTE: {len(conflicts)} English strings map to more than one Chinese '
              'string (first occurrence kept). Usually harmless duplicates; run '
              'make_review.py if you want to inspect them.')
        for en, first, other in conflicts[:3]:
            print(f'  EN : {en[:90]}')
            print(f'   -> {first[:70]}')
            print(f'   -> {other[:70]}')

    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(tm, fh, ensure_ascii=False, indent=1)
    print(f'\nwrote {args.out}')


if __name__ == '__main__':
    main()
