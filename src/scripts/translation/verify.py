#!/usr/bin/env python3
"""Gate the translated file. Run this before building any image.

Checks, in order of how much damage each failure does:

  structure    nothing outside text.html / implications differs from upstream
  coverage     every field value that should be Chinese is Chinese
  entities     no HTML entity present in English is missing in Chinese
  tags         same tag multiset, same <br> count and spelling, balanced nesting
  unescaped    no raw < > & left in text content, in either language
  numbers      digits in the English also appear in the Chinese (reported, not fatal)
  terminology  one canonical rendering per term across the whole file

    src/scripts/translation/verify.py
    src/scripts/translation/verify.py --upstream-tag v3.4.0

Exit status is non-zero if any fatal check fails, so it can gate a build.
"""
import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402

FATAL = []
WARN = []


def fail(check, message):
    FATAL.append((check, message))


def warn(check, message):
    WARN.append((check, message))


def structural_diff(a, b, path=''):
    """Paths where two JSON trees differ, ignoring values (compared separately)."""
    out = []
    if type(a) is not type(b):
        return [f'{path}: type {type(a).__name__} vs {type(b).__name__}']
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [f'{path}: keys differ ({sorted(set(a) ^ set(b))})']
        for k in a:
            out += structural_diff(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b):
            return [f'{path}: length {len(a)} vs {len(b)}']
        for i, (x, y) in enumerate(zip(a, b)):
            out += structural_diff(x, y, f'{path}[{i}]')
    elif a != b:
        out.append(f'{path}: value differs')
    return out


TRANSLATED_PATH = re.compile(r'\.recommendations\[\d+\]\.(text\.html|implications\[\d+\])$')


def check_structure(cn, upstream):
    diffs = structural_diff(upstream, cn)
    stray = [d for d in diffs if not (d.endswith(': value differs')
                                      and TRANSLATED_PATH.search(d[:-len(': value differs')]))]
    if stray:
        fail('structure', f'{len(stray)} difference(s) outside the two translated fields; '
                          f'first: {stray[0]}')
    else:
        print(f'  structure   OK  ({len(diffs)} value diffs, all in text.html / implications)')


def check_pairs(cn_data, en_data):
    pairs = list(pgcore.pair(en_data, cn_data))
    uniq = sorted(set(pairs))
    print(f'  (checking {len(pairs)} field values, {len(uniq)} unique EN/CN pairs)')

    missing = [(k, e) for k, e, c in pairs
               if pgcore.needs_translation(e) and not pgcore.HAN.search(c)]
    if missing:
        fail('coverage', f'{len(missing)} field values are not translated; '
                         f'first: {missing[0][1][:90]}')
    else:
        print('  coverage    OK  (every substantive field value contains Chinese)')

    ent_lost = tags = brs = nesting = 0
    for _k, e, c in uniq:
        # Compare against the English minus known upstream junk, which the
        # translation is expected to drop along with any entities inside it.
        e_clean = pgcore.strip_artifacts(e)
        if (collections.Counter(pgcore.ENTITY.findall(e_clean))
                - collections.Counter(pgcore.ENTITY.findall(c))):
            ent_lost += 1
        if (collections.Counter(m.group(0) for m in pgcore.TAG_NAME.finditer(e))
                != collections.Counter(m.group(0) for m in pgcore.TAG_NAME.finditer(c))):
            tags += 1
        if (len(pgcore.BR.findall(e)) != len(pgcore.BR.findall(c))
                or any(('<br/>' in e) != ('<br/>' in c) for _ in (0,))
                or ('<br />' in e) != ('<br />' in c)):
            brs += 1
        if pgcore.tag_balance(c) and not pgcore.tag_balance(e):
            nesting += 1

    for label, n, msg in (('entities', ent_lost, 'pair(s) drop an HTML entity present in the English'),
                          ('tags', tags, 'pair(s) have a different tag multiset'),
                          ('tags <br>', brs, 'pair(s) differ in <br> count or spelling'),
                          ('nesting', nesting, 'Chinese value(s) have broken tag nesting')):
        if n:
            fail(label, f'{n} {msg}')
        else:
            print(f'  {label:11} OK')

    raw = 0
    for _k, e, c in uniq:
        if pgcore.unescaped(c):
            raw += 1
    if raw:
        fail('unescaped', f'{raw} Chinese value(s) contain a raw < > or &')
    else:
        print('  unescaped   OK  (no raw < > & in Chinese text content)')

    num = re.compile(r'\d+(?:\.\d+)?')
    odd = [e for _k, e, c in uniq
           if collections.Counter(num.findall(pgcore.strip_artifacts(e)))
           - collections.Counter(num.findall(c))]
    if odd:
        warn('numbers', f'{len(odd)} pair(s) have digits in the English missing from the '
                        f'Chinese. Often benign (5-fluorouracil -> 氟尿嘧啶, CYP2D6, 6-TGN) '
                        f'but dosing numbers must match — review these.')
    else:
        print('  numbers     OK')


def check_terminology(cn_data):
    blob = '\n'.join(v for *_x, v in pgcore.iter_fields(cn_data))
    offenders = {variant: blob.count(variant)
                 for variant in pgcore.CANONICAL if blob.count(variant)}
    if offenders:
        detail = ', '.join(f'{v} x{n} (should be {pgcore.CANONICAL[v]})'
                           for v, n in offenders.items())
        fail('terminology', f'non-canonical term(s): {detail}')
    else:
        print(f'  terminology OK  ({len(pgcore.CANONICAL)} canonical terms enforced)')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cn', type=Path, default=pgcore.GUIDANCE)
    ap.add_argument('--en', type=Path, help='English reference (default: auto-detect)')
    ap.add_argument('--upstream-tag',
                    help='git tag holding the pristine upstream file to compare structure '
                         'against (default: inferred from the reference filename)')
    args = ap.parse_args()

    en_path = args.en or pgcore.find_reference()
    cn_data, en_data = pgcore.load(args.cn), pgcore.load(en_path)

    print(f'translated : {args.cn}')
    print(f'reference  : {en_path}\n')

    tag = args.upstream_tag
    if not tag:
        m = re.search(r'\.v(\d+\.\d+\.\d+)\.json$', en_path.name)
        tag = f'v{m.group(1)}' if m else None
    upstream = None
    if tag:
        rel = f'{pgcore.REPORTER_DIR}/prescribing_guidance.json'
        proc = subprocess.run(['git', 'show', f'{tag}:{rel}'],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            import json as _json
            upstream = _json.loads(proc.stdout)
        else:
            warn('structure', f'could not read {tag}:{rel} — skipped the structural check')
    if upstream is not None:
        check_structure(cn_data, upstream)
    elif not tag:
        warn('structure', 'no upstream tag inferred — skipped the structural check')

    check_pairs(cn_data, en_data)
    check_terminology(cn_data)

    if WARN:
        print('\nWARNINGS (review, not blocking):')
        for check, msg in WARN:
            print(f'  [{check}] {msg}')
    if FATAL:
        print('\nFAILED:')
        for check, msg in FATAL:
            print(f'  [{check}] {msg}')
        print(f'\n{len(FATAL)} fatal check(s) failed.')
        return 1
    print('\nAll fatal checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
