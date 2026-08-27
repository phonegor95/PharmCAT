# Deprecated Docker image workflow

The historical `phonegor95/pharmcat:chinese` floating Docker image workflow is no longer supported. That tag held an older PharmCAT release while appearing current, so it is not a reproducible source for clinical reports.

Chinese PharmCAT is now a data-only translation maintained in:

```text
src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json
```

Follow `docs/translation-workflow.md` to update and verify the translation. GenDecoder builds its pinned bilingual Singularity image with `bin/build_pharmcat_image.sh` from the GenDecoder repository; the build combines the official upstream JAR with a verified Chinese JAR from this fork.
