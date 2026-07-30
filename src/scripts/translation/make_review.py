#!/usr/bin/env python3
"""Emit a side-by-side English/Chinese review page.

Intended for a human reviewer — ideally a pharmacist — not for a diff tool. By
default it shows only what changed against a baseline revision, so each merge
produces a review of just that merge's work rather than all 1100+ strings.

    # review what this branch changed against the last release
    src/scripts/translation/make_review.py --base-rev v3.1.1 -o review.html

    # review everything
    src/scripts/translation/make_review.py --all -o review.html

Open the file in a browser. Nothing is uploaded.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pgcore  # noqa: E402

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>PharmCAT 中文翻译审校 — {n} entries</title>
<style>
 :root {{ color-scheme: light dark; }}
 body {{ font: 15px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
         margin: 0 auto; max-width: 1500px; padding: 1.5rem; }}
 h1 {{ font-size: 1.3rem; margin: 0 0 .25rem; }}
 .meta {{ opacity: .7; font-size: .85rem; margin-bottom: 1rem; }}
 .bar {{ position: sticky; top: 0; background: Canvas; padding: .6rem 0;
         border-bottom: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
         display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; z-index: 2; }}
 input[type=search] {{ padding: .4rem .6rem; min-width: 22rem; font: inherit; }}
 table {{ border-collapse: collapse; width: 100%; }}
 th, td {{ text-align: left; vertical-align: top; padding: .55rem .7rem;
           border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }}
 th {{ position: sticky; top: 3.2rem; background: Canvas; font-size: .8rem;
       text-transform: uppercase; letter-spacing: .04em; opacity: .75; }}
 td.en {{ width: 40%; }} td.cn {{ width: 40%; }}
 td.k {{ white-space: nowrap; font-size: .75rem; opacity: .6; }}
 .old {{ display: block; margin-top: .4rem; padding-left: .6rem;
         border-left: 3px solid color-mix(in srgb, CanvasText 25%, transparent);
         opacity: .6; font-size: .9em; }}
 .old::before {{ content: "was: "; font-variant: small-caps; opacity: .8; }}
 code {{ background: color-mix(in srgb, CanvasText 8%, transparent);
         padding: .05em .3em; border-radius: 3px; font-size: .88em; }}
 tr.hide {{ display: none; }}
 .tag {{ font-size: .7rem; padding: .1em .45em; border-radius: 3px;
         background: color-mix(in srgb, CanvasText 12%, transparent); }}
</style>
<h1>PharmCAT 中文处方指导 — 翻译审校</h1>
<div class="meta">{subtitle}</div>
<div class="bar">
  <input type="search" id="q" placeholder="filter (drug, gene, Chinese or English text)…">
  <label><input type="checkbox" id="onlynew"> only entries with no previous translation</label>
  <span id="count"></span>
</div>
<table>
  <thead><tr><th>#</th><th>field</th><th>English (upstream)</th><th>中文</th></tr></thead>
  <tbody id="rows">
{rows}
  </tbody>
</table>
<script>
const q = document.getElementById('q'), only = document.getElementById('onlynew');
const rows = [...document.querySelectorAll('#rows tr')], count = document.getElementById('count');
function apply() {{
  const needle = q.value.toLowerCase(), fresh = only.checked;
  let shown = 0;
  for (const tr of rows) {{
    const ok = (!needle || tr.textContent.toLowerCase().includes(needle))
            && (!fresh || tr.dataset.fresh === '1');
    tr.classList.toggle('hide', !ok);
    if (ok) shown++;
  }}
  count.textContent = shown + ' / ' + rows.length + ' shown';
}}
q.addEventListener('input', apply); only.addEventListener('change', apply); apply();
</script>
"""


def git_show(rev, path):
    proc = subprocess.run(['git', 'show', f'{rev}:{path}'], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f'cannot read {rev}:{path}\n{proc.stderr.strip()}')
    return json.loads(proc.stdout)


def baseline_map(rev):
    """English-keyed translation map as of `rev`.

    Keyed by English string, not by position: an older release has a different
    number of recommendations, so positional pairing would silently misalign.
    """
    listing = subprocess.run(
        ['git', 'ls-tree', '--name-only', rev, f'{pgcore.REPORTER_DIR}/'],
        capture_output=True, text=True)
    if listing.returncode != 0:
        raise SystemExit(f'cannot list {rev}:{pgcore.REPORTER_DIR}')
    refs = [Path(line) for line in listing.stdout.split('\n')
            if re.search(r'prescribing_guidance\.v.*\.json$', line)]
    if len(refs) != 1:
        raise SystemExit(f'{rev} has {len(refs)} English reference files; expected exactly one '
                         '(cannot diff translations without knowing their English source)')
    old_en = git_show(rev, str(refs[0]))
    old_cn = git_show(rev, f'{pgcore.REPORTER_DIR}/prescribing_guidance.json')
    out = {}
    for kind, en, cn in pgcore.pair(old_en, old_cn):
        out.setdefault((kind, pgcore.match_key(en)), cn)
    return out, refs[0].name


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cn', type=Path, default=pgcore.GUIDANCE)
    ap.add_argument('--en', type=Path, help='English reference (default: auto-detect)')
    ap.add_argument('--base-rev', help='git revision whose translation to diff against '
                                       '(e.g. v3.1.1, or a commit)')
    ap.add_argument('--all', action='store_true', help='show every entry, not just changes')
    ap.add_argument('-o', '--out', type=Path, required=True)
    args = ap.parse_args()

    en_path = args.en or pgcore.find_reference()
    cn_data, en_data = pgcore.load(args.cn), pgcore.load(en_path)
    pairs = list(pgcore.pair(en_data, cn_data))

    base, base_ref = {}, None
    if args.base_rev and not args.all:
        base, base_ref = baseline_map(args.base_rev)
        print(f'baseline {args.base_rev} ({base_ref}): {len(base)} known translations')

    rows, shown = [], 0
    seen = set()
    for kind, en, cn in pairs:
        if (kind, en) in seen:
            continue
        seen.add((kind, en))
        old = base.get((kind, pgcore.match_key(en)))
        changed = args.all or not base or old is None or old != cn
        if not changed:
            continue
        shown += 1
        fresh = '1' if (old is None or not pgcore.HAN.search(old or '')) else '0'
        old_html = (f'<span class="old">{html.escape(old)}</span>'
                    if old and old != cn and not args.all else '')
        rows.append(
            f'    <tr data-fresh="{fresh}">'
            f'<td class="k">{shown}</td>'
            f'<td class="k"><span class="tag">{kind}</span></td>'
            f'<td class="en">{html.escape(en)}</td>'
            f'<td class="cn">{html.escape(cn)}{old_html}</td></tr>')

    scope = ('every entry' if args.all or not args.base_rev
             else f'entries whose translation differs from <code>{html.escape(args.base_rev)}</code>')
    subtitle = (f'{shown} of {len(seen)} unique strings — showing {scope}. '
                f'Reference: <code>{html.escape(en_path.name)}</code>. '
                'HTML tags, entities, gene symbols, doses and PMIDs must match the English exactly.')
    args.out.write_text(PAGE.format(n=shown, subtitle=subtitle, rows='\n'.join(rows)),
                        encoding='utf-8')
    print(f'wrote {args.out} — {shown} entries')
    print('Open it in a browser; use the filter box to review by drug or gene.')


if __name__ == '__main__':
    main()
