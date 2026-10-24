---
name: pharmcat-report-zh-cn
description: Translate an existing PharmCAT HTML report into a separate Simplified Chinese .zh-cn.html report using the PharmCAT Chinese guidance and companion GenDecoder dictionaries. Use for English or partly translated reports; preserve genotype results, doses, markup, and citations.
---

Generate a Chinese copy of an existing report without rerunning genotyping or changing clinical conclusions.

## Translation sources

Locate the PharmCAT checkout containing `README_Chinese.md`. When this skill is installed in `PharmCAT/.agents/skills/pharmcat-report-zh-cn/`, the script detects the repository automatically. Otherwise pass `--pharmcat`.

Read `README_Chinese.md` before changing terminology. Clinical translations come from these files under `src/main/resources/org/pharmgkb/pharmcat/reporter/`:

- `prescribing_guidance.json`: Chinese recommendation prose, implications, and population labels.
- `prescribing_guidance.v*.json`: the matching English reference. Pair records by guideline/recommendation ID, never by unrelated array positions.

Structured labels come from `GenDecoder/assets/pharmcat/data/zh-cn/`: `drugs.json`, `phenotypes.json`, `source.json`, `recommendation.json`, `genotype_translation.json`, and `implications.json`. GenDecoder is usually a sibling checkout; `--dictionaries` overrides this location. These dictionaries are required and are read in place. Do not copy or alter the canonical clinical data to translate one report.

The bundled [report-ui.zh-cn.json](references/report-ui.zh-cn.json) supplies report headings, explanatory notes, and disclaimers. It supplements the clinical resources. Sample names, dates, and genotype counts are handled dynamically, without patient-specific mappings.

## Generate the report

Run the bundled Python 3 standard-library script. Resolve `SKILL_DIR` to the directory containing this `SKILL.md`:

```bash
python3 "$SKILL_DIR/scripts/translate_report.py" /path/to/sample.report.html \
  --pharmcat /path/to/PharmCAT \
  --dictionaries /path/to/GenDecoder/assets/pharmcat/data/zh-cn
```

The default output is `sample.report.zh-cn.html`, with a sibling `sample.report.zh-cn.translation-review.json`. `--output` selects another filename. Existing outputs are never overwritten; use a new destination during revisions. The original input must remain unchanged.

The script sets `lang="zh-CN"` and translates human-facing text with exact mappings and limited templates. It preserves existing Chinese, bibliography titles/journal names, gene and variant identifiers, hyperlinks, IDs, classes, tables, scripts, CSS, and embedded images. It checks HTML events, functional attributes, text-node boundaries, existing Chinese, and numbers before writing output. English month names may become their numeric Chinese equivalent.

For clinical HTML with multiple text leaves, the script uses positional translations only when tag structure and text-leaf counts align and numbers stay within the same leaf. Ambiguous or differently structured fragments are left for review. Do not strip links or formatting to force a clinical mapping.

## Resolve gaps and verify

Inspect `remaining_english` in the review JSON. It deliberately includes technical values and proper names. Keep gene symbols, rsIDs, variants, allele names, version strings, URLs, abbreviations, and original bibliographic entries. Translate remaining explanatory English, drug names, and phenotype/action labels. Inspect partially translated text as well as entirely English nodes.

For missing plain-text translations, create an exact English-to-Chinese JSON mapping and rerun to a fresh output with `--extra /path/to/extra.json`. Prefer existing PharmCAT and GenDecoder terminology. Preserve every dose, unit, threshold, percentage, negation, qualifier, and repeated identifier. A validation failure must be resolved; do not suppress the checks to accept changed clinical data. If markup differs between paired clinical fragments, inspect the source and target HTML and translate with the original markup intact, then verify the same invariants.

Check the rendered report when browser tooling is available: title/metadata, genotype summary, recommendation tables, matching details, disclaimers, anchors, and images. State any remaining substantive English or unavailable clinical mapping. Do not equate a passing structural check with clinical validation.

Return the output file link and a brief verification result. Creating this skill or translating a report does not authorize commits, pushes, changing the PharmCAT guidance, rebuilding containers, or changing the reporting application.
