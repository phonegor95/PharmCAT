#!/usr/bin/env python3
"""Align the Chinese markup with the English, mechanically.

Translators reliably drift on markup that carries no meaning, so this fixes the
part that can be fixed without judgment:

  * <br> spelling — upstream mixes <br/> and <br />; match it per string
  * CN-only trailing <br/> immediately before </li>, which upstream never has
  * &le; / &ge; vs literal ≤ / ≥ — match whichever the English string uses

It deliberately does NOT touch:

  * &quot; placement. Those mark quoted drug-label text and choosing the span is
    a judgment call. verify.py reports missing ones as a fatal error, so they
    surface for review rather than being guessed at here.
  * anything inside a tag, or any Chinese text.

    src/scripts/translation/html_align.py            # report only
    src/scripts/translation/html_align.py --write
"""
import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402


def align(cn, en):
    """Return cn with markup aligned to en. Never changes text content."""
    out = cn

    # <br> spelling: follow whichever form this English string uses.
    if '<br/>' in en and '<br />' not in en:
        out = out.replace('<br />', '<br/>')
    elif '<br />' in en and '<br/>' not in en:
        out = out.replace('<br/>', '<br />')

    # A <br> right before </li> adds nothing and upstream does not do it.
    if '<br/>\n</li>' not in en:
        out = out.replace('<br/>\n</li>', '\n</li>')
    if '<br />\n</li>' not in en:
        out = out.replace('<br />\n</li>', '\n</li>')

    # ≤ / ≥ : entity or literal, whichever the English uses.
    for entity, literal in (('&le;', '≤'), ('&ge;', '≥')):
        if literal in en and entity not in en:
            out = out.replace(entity, literal)
        elif entity in en and literal not in en:
            out = out.replace(literal, entity)

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cn', type=Path, default=pgcore.GUIDANCE)
    ap.add_argument('--en', type=Path, help='English reference (default: auto-detect)')
    ap.add_argument('--write', action='store_true', help='apply the changes (default: report only)')
    args = ap.parse_args()

    en_path = args.en or pgcore.find_reference()
    cn_data, en_data = pgcore.load(args.cn), pgcore.load(en_path)

    en_values = [v for *_x, v in pgcore.iter_fields(en_data)]
    fields = list(pgcore.iter_fields(cn_data))
    if len(en_values) != len(fields):
        raise SystemExit('reference does not match the translated file (field count differs)')

    changed = collections.Counter()
    for (gi, ri, kind, si, cn), en in zip(fields, en_values):
        new = align(cn, en)
        if new == cn:
            continue
        if ('<br/>' in cn) != ('<br/>' in new) or ('<br />' in cn) != ('<br />' in new):
            changed['<br> spelling'] += 1
        if cn.count('<br') != new.count('<br'):
            changed['trailing <br> before </li>'] += 1
        if ('&le;' in cn) != ('&le;' in new) or ('&ge;' in cn) != ('&ge;' in new):
            changed['&le;/&ge; alignment'] += 1
        if args.write:
            pgcore.set_field(cn_data, gi, ri, kind, si, new)

    if not changed:
        print('markup already aligned with the English — nothing to do')
        return 0
    print('markup differences that can be fixed mechanically:')
    for what, n in changed.most_common():
        print(f'  {n:>5}  {what}')
    if args.write:
        pgcore.dump(cn_data, args.cn)
        print(f'\nwrote {args.cn} — now run verify.py')
    else:
        print('\n(report only; pass --write to apply)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
