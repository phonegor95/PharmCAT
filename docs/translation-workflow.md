# Chinese translation workflow

Written for whoever — human or AI agent — merges the next upstream PharmCAT
release into this fork. Follow it in order. Every claim below was verified
during the v3.4.0 merge; the "Traps" section is the list of things that actually
went wrong, so read it before starting.

## The invariant

Exactly two fields are translated, in
`src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json`:

```
guidelines[].recommendations[].text.html
guidelines[].recommendations[].implications[]
```

**Everything else must stay byte-identical to upstream** — ids, lookup keys,
genotypes, drug names, structure, key order, formatting (2-space indent, real
UTF-8, no trailing newline). `verify.py` enforces this by diffing against the
pristine upstream file read straight from the git tag. If that check fails, the
merge is wrong; do not "fix" the check.

The fork has no functional Java changes. `ReportHelpers.getChineseDrugName()`,
`printRecMapWithChinese()`, `AccessionObject.nameCn` and
`AnnotationReport.getLookupKey()` are dead code left from an approach rolled
back in 59a8d86a; nothing references them and `report.hbs` matches upstream.
The translation is data, not code.

## Files

| File | Role |
|---|---|
| `prescribing_guidance.json` | the translated file, loaded by `PgkbGuidelineCollection` |
| `prescribing_guidance.v<VER>.json` | untranslated English at the **current** version |
| `src/scripts/translation/` | the tooling below |

The English reference is not decoration. It is the only way to know which
English string a given Chinese string came from, which is what makes reuse
across releases possible. Keep exactly one, named for the version it came from,
and replace it whenever you merge.

## Merging a new release

Say the new tag is `v3.5.0`.

```bash
# 1. merge. prescribing_guidance.json will conflict; that is expected and you do
#    not resolve it by hand — step 4 regenerates the whole file.
git fetch upstream --tags
git merge v3.5.0

# 2. translation memory from the CURRENT (pre-merge) state
git stash                       # get the pre-merge files back if the merge left them conflicted
src/scripts/translation/build_tm.py -o /tmp/tm.json
git stash pop

# 3. what does the new release leave untranslated?
git show v3.5.0:src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json \
  > /tmp/new.json
src/scripts/translation/plan_merge.py --tm /tmp/tm.json --new /tmp/new.json -o /tmp/todo.json

# 4. translate: fill in every "cn" in /tmp/todo.json (see "Translating" below)

# 5. rebuild the file, and install the new English reference
src/scripts/translation/apply.py \
    --tm /tmp/tm.json --new /tmp/new.json --todo /tmp/todo.json \
    --reference-out src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.v3.5.0.json
git rm src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.v3.4.0.json

# 6. mechanical markup alignment, then the gate
src/scripts/translation/html_align.py --write
src/scripts/translation/verify.py          # must exit 0

# 7. review
src/scripts/translation/make_review.py --base-rev v3.4.0 -o /tmp/review.html

# 8. build the image (in the GenDecoder repo)
bin/build_pharmcat_image.sh 3.5.0
```

For scale: the v3.4.0 merge reused **81%** of field values from the existing
translation by exact string match, leaving 234 unique strings to translate out
of 1138. Expect similar unless upstream rewrites the data wholesale, as it did
in v3.2.0.

## Translating

Reuse is automatic. Only the `plan_merge.py` work list needs attention. Each
entry carries `hint_en` / `hint_cn` — the closest existing translation — so
match its wording rather than inventing new phrasing.

Preserve exactly, from the `en` field:

- HTML tags and `id="..."` anchors (translate the visible heading text only)
- entities: `&quot;` `&gt;` `&lt;` `&le;` `&ge;` `&nbsp;` — both fields render
  through `{{{ }}}` in `report.hbs`, i.e. raw HTML, so entities matter
- gene symbols, star alleles (`*1/*4`), rsIDs, `c.`/`m.` variant notation
- PMIDs, URLs, doses, units, percentages
- the `GENE: ` prefix on implications, which stays English

An LLM can draft this, but do not treat it as authoritative. During the v3.4.0
merge a model returned 13 review findings of which one was a confident false
CRITICAL — it claimed `CYP2D6` had been mistranslated as `CYP2C19` in a string
that never contained `CYP2C19`, and its "corrected" version was byte-identical
to the original. Verify every finding against the actual text.

Terminology is enforced, not suggested. `pgcore.CANONICAL` holds one canonical
rendering per term and `verify.py` fails on any other. `pgcore.ALLOWED_VARIANTS`
documents the two splits that are deliberate because the English makes the same
distinction — do not collapse them.

## Reviewing

`make_review.py --base-rev <previous tag>` writes a self-contained HTML page:
English and Chinese side by side, previous translation shown inline where it
changed, filter box, and a toggle for entries that had no previous translation.
Open it in a browser; nothing is uploaded.

Review surface is larger than "the new strings" whenever a pass edits old
translations — the v3.4.0 merge produced 482 review entries from 234 new
translations, the rest being terminology and markup normalization. A clinician
should look at new translations, model-suggested fixes, and anything
`verify.py` warns about under `numbers`. Mechanical markup changes do not need
clinical review.

## What the tools will and will not do

| Task | Tool | Automated? |
|---|---|---|
| reuse existing translations | `apply.py` | yes, exact match then markup-insensitive |
| terminology consistency | `apply.py` / `verify.py` | yes, enforced |
| `<br>` spelling and count, `&le;`/`&ge;` style | `html_align.py` | yes |
| `&quot;` placement around quoted label text | — | **no**, needs judgment; `verify.py` fails so it surfaces |
| broken tag nesting | `verify.py` | detected, fixed by hand |
| new clinical text | — | **no** |

`&quot;` deserves a note. Those quote marks delimit verbatim FDA/EMA drug-label
text. Without them a quoted label statement reads as PharmCAT's own
recommendation, which is a clinical misrepresentation, not a formatting nit. The
v3.4.0 merge had to restore 385 of them across 200 translations. Choosing the
span is judgment, so it is deliberately not automated — but if you use a model
for it, constrain it to insertion only and verify that the output with `&quot;`
stripped is byte-identical to the input. That reduces the model to placing
markers and makes a text rewrite impossible.

## Traps

Each of these cost time during the v3.4.0 merge.

**Upstream deleted content in v3.2.0.** The `<h4>"Other Considerations"` sections
vanished from `text.html`: 1364 heading tags in v3.1.1, zero from v3.2.0 onward.
1299 of 3677 shared recommendations lost >25% of their text; median `text.html`
went 375 → 204 characters. This is upstream's decision, it is not recoverable
from elsewhere in the file (`otherPrescribingGuidance` is a boolean), and the
fork tracks it deliberately. Do not reintroduce the old text.

**Do not text-merge `prescribing_guidance.json`.** Upstream rewrote ~45k lines
between v3.1.1 and v3.4.0. Regenerate with `apply.py` instead.

**The English reference is not byte-identical to upstream.** A few unescaped
characters were corrected in it (`(INR > 4)` → `(INR &gt; 4)`, `Grade >=2` →
`Grade ≥2`, a bare `&`). So a translation-memory key built from the reference
will not exactly equal upstream's string. `pgcore.match_key()` handles this with
a markup-insensitive fallback; `plan_merge.py` reports how many matched that
way. Without it, already-translated strings look like new work.

**Upstream ships scraped junk.** Two DPWG implications have website footer
navigation appended ("About ClinPGx Acknowledgements FAQ …"). The translations
correctly omit it, which makes the `&amp;` inside it look like entity loss.
`pgcore.UPSTREAM_ARTIFACTS` allowlists it. Add to that list, with a reason,
rather than weakening a check.

**`/mnt/SA127` is mounted `nodev`.** Singularity sandbox extraction fails there
with `failed to stat rootPath`. Build on local disk and publish the finished
`.sif` to the share; `bin/build_pharmcat_image.sh` already does.

**Version labels drift.** Two images labelled `pgkb/pharmcat:latest` and
`phonegor95/pharmcat:chinese` in fact held PharmCAT 3.1.1 for eight months
unnoticed. Image filenames and `PHARMCAT_IMG` are now pinned to the version they
actually contain. Keep it that way.

**Keep the guidance inside the jar.** `PgkbGuidelineCollection` resolves the file
through the classpath, so a directory ahead of the jar shadows it — verified,
5793 Han characters in a real report from an unmodified upstream image with no
custom jar. It is tempting, and it was rejected: it lets a stale translation load
silently against a newer PharmCAT. The bilingual image ships two jars, each with
its own guidance welded in, so a mismatch is impossible.

## Tooling reference

All scripts live in `src/scripts/translation/` and take `--help`.

| Script | Purpose |
|---|---|
| `pgcore.py` | shared helpers, canonical terminology, upstream-artifact allowlist |
| `build_tm.py` | English reference + translated file → translation memory |
| `plan_merge.py` | memory + new upstream → coverage report and work list |
| `apply.py` | memory + work list + new upstream → rebuilt translated file |
| `html_align.py` | mechanical markup alignment against the English |
| `verify.py` | the gate: structure, coverage, entities, tags, terminology |
| `make_review.py` | side-by-side HTML review page |

`verify.py` exits non-zero on failure, so it can gate a build. Run it before
`build_pharmcat_image.sh`, always.
