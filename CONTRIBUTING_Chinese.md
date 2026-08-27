# Contributing Chinese prescribing-guidance translations

This fork keeps PharmCAT behavior aligned with upstream and translates data only. Contributions must not add Chinese-specific Java, template, matching, phenotyping, or serialization logic.

## Allowed translation surface

Only these values may differ from the matching upstream release:

```text
guidelines[].recommendations[].text.html
guidelines[].recommendations[].implications[]
```

They live in:

```text
src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json
```

The adjacent `prescribing_guidance.v<version>.json` is the immutable English reference used by the translation tools.

## Before editing

Read [`docs/translation-workflow.md`](docs/translation-workflow.md). Preserve HTML tags and entities, gene symbols, alleles, variants, PMIDs, doses, units, percentages, and the `GENE: ` implication prefix. Use terminology already established in `src/scripts/translation/pgcore.py`.

For an upstream-version merge, build translation memory and generate a work list rather than text-merging the large JSON file.

## Required checks

```bash
python3 src/scripts/translation/verify.py
python3 -m unittest discover \
  -s src/test/python/translation -p 'test_*.py' -v
./gradlew test
./gradlew shadowJar
```

Generate a local review page:

```bash
python3 src/scripts/translation/make_review.py --all \
  -o /tmp/pharmcat-zh-cn-review.html
```

A clinician or pharmacist should review new or materially changed clinical text. Mechanical HTML alignment does not substitute for clinical review.

## GenDecoder coordination

The JAR intentionally leaves structured names and classifications in English. GenDecoder translates those CSV fields using `assets/pharmcat/data/zh-cn/*.json`. When adding or changing a canonical drug, phenotype, genotype, source, or recommendation-level term:

1. update the relevant GenDecoder dictionary;
2. update `pgcore.CANONICAL` for any deprecated internal aliases;
3. run GenDecoder's cross-layer PharmCAT validator against this source/JAR;
4. rebuild a newly named bilingual SIF—never overwrite the existing production image.

Do not commit generated JARs, SIFs, review HTML, translation-memory work files, or floating Docker-image references.
