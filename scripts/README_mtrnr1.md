# MT-RNR1 Variant Extraction for PharmCAT

## Overview

This script extracts MT-RNR1 (mitochondrial 12S rRNA) variants from mtdna-server-2 output files and formats them for use with PharmCAT's outside call feature (`-po` flag).

MT-RNR1 variants are associated with aminoglycoside-induced hearing loss, and this tool helps integrate mitochondrial variant data into PharmCAT's pharmacogenomic analysis pipeline.

## Background

- **MT-RNR1** is a mitochondrial gene encoding the 12S ribosomal RNA
- **Clinical significance**: Certain MT-RNR1 variants (most notably m.1555A>G) increase risk of aminoglycoside-induced hearing loss
- **Gene characteristics**: Monoploid (mitochondrial), uses variant notation instead of star alleles
- **PharmCAT support**: PharmCAT recognizes 24 known MT-RNR1 variants

## Installation

No installation required. The script is a standalone Python 3 script.

**Requirements:**
- Python 3.6 or higher (standard library only, no external dependencies)
- Input file from [genepi/mtdna-server-2](https://github.com/genepi/mtdna-server)

## Quick Start

```bash
# Extract MT-RNR1 variants from mtdna-server-2 output
python3 scripts/extract_mtrnr1_variants.py \
  -i path/to/variants.annotated.txt

# Output will be created in the same directory as input:
# path/to/<sample_id>.mtrnr1.tsv
```

## Usage

### Command-Line Options

```
-i, --input INPUT          Input variants.annotated.txt file (required)
-o, --output OUTPUT        Output TSV file path (optional)
--include-unknown          Include variants not in PharmCAT's known list
--verbose                  Enable detailed logging
--version                  Show version and exit
-h, --help                 Show help message
```

### Examples

#### Example 1: Process single sample
```bash
python3 extract_mtrnr1_variants.py \
  -i /path/to/sample/variants.annotated.txt
```

**Output:** `/path/to/sample/A251114.mtrnr1.tsv`

#### Example 2: Specify output location
```bash
python3 extract_mtrnr1_variants.py \
  -i /path/to/sample/variants.annotated.txt \
  -o /output/dir/sample.pharmcat.tsv
```

#### Example 3: Include unknown variants with verbose logging
```bash
python3 extract_mtrnr1_variants.py \
  -i variants.annotated.txt \
  --include-unknown \
  --verbose
```

#### Example 4: Use with PharmCAT pipeline
```bash
# Step 1: Extract MT-RNR1 variants
python3 extract_mtrnr1_variants.py -i mtdna/variants.annotated.txt

# Step 2: Run PharmCAT with outside call
pharmcat -vcf sample.vcf -po sample.mtrnr1.tsv
```

## Output Format

The script generates a tab-separated values (TSV) file in PharmCAT's outside call format using the exact keys from [MT_RNR1.json](../src/main/resources/org/pharmgkb/pharmcat/phenotype/MT_RNR1.json):

### With Variants Detected
```tsv
#gene	diplotype	phenotype	activityScore
MT-RNR1	m.663A>G
MT-RNR1	m.1555A>G
```

### No Variants (Reference)
```tsv
#gene	diplotype	phenotype	activityScore
MT-RNR1	Reference
```

**Key points:**
- MT-RNR1 is a monoploid gene (single allele, no `/` separator)
- Variant notation uses format: `m.{Position}{Ref}>{Alt}` (e.g., `m.1555A>G`)
- The `m.` prefix is **required** to match PharmCAT's MT_RNR1.json keys
- If no known variants are found, outputs `Reference`
- `phenotype` and `activityScore` columns are empty (PharmCAT fills these)

## Example Directory Structure

```
20251202_A251281_A259999/
└── results/
    └── mtdna/
        └── A259999/
            ├── variants.annotated.txt   # Input from mtdna-server-2
            └── A259999.mtrnr1.tsv       # Output (auto-generated)
```

## PharmCAT-Supported MT-RNR1 Variants

All 24 variants match the keys in [MT_RNR1.json](../src/main/resources/org/pharmgkb/pharmcat/phenotype/MT_RNR1.json):

### Increased Risk Variants (3)
These variants confer **increased risk** of aminoglycoside-induced hearing loss:
- **m.1555A>G** - Most well-known and clinically significant
- m.1494C>T
- m.1095T>C

### Normal Risk Variants (1)
- m.827A>G - Normal risk despite being a variant

### Uncertain Risk Variants (20)
Variants with uncertain or unclear clinical significance:
- m.663A>G, m.669T>C, m.747A>G, m.786G>A
- m.807A>C, m.807A>G, m.839A>G, m.896A>G
- m.930G>A, m.951G>A, m.960C>del, m.961T>G
- m.961T>del, m.961T>del+Cn, m.988G>A
- m.1189T>C, m.1243T>C, m.1520T>C, m.1537C>T, m.1556C>T

## Behavior and Filtering

### Default Behavior (Recommended)
✓ Only outputs variants in PharmCAT's known list (24 variants)
✓ Skips unknown/novel variants
✓ Outputs `Reference` if no known variants found
✓ Only accepts PASS-filtered variants from mtdna-server-2

### With `--include-unknown` Flag
- Outputs all MT-RNR1 variants found
- Issues warnings for unknown variants
- Useful for research or comprehensive reporting

## Input File Format

The script expects mtdna-server-2's `variants.annotated.txt` output format. The script **automatically detects** the Maplocus column position, so it works with different mtdna-server-2 versions.

Example (38-column format):
```
ID	Filter	Pos	Ref	Variant	VariantLevel	MeanBaseQuality	Coverage	GT	Type	Mutation	Substitution	Maplocus	...
A259999	PASS	663	A	G	1	.	5489	0/1	2	663G	transition	MT-RNR1	...
```

Example (14-column format):
```
ID	Filter	Pos	Ref	Variant	VariantLevel	Coverage	VariantLevelTop	VariantLevelMinor	MajorBase	MinorBase	MajorLevel	MinorLevel	Maplocus
A259999	PASS	663	A	G	0.98	100	0.98	0.02	G	A	98	2	MT-RNR1
```

**Required columns:**
- Column 0: ID (sample identifier)
- Column 1: Filter (PASS/other)
- Column 2: Pos (genomic position)
- Column 3: Ref (reference allele)
- Column 4: Variant (variant allele)
- Maplocus: Gene/region (e.g., "MT-RNR1") - position auto-detected from header

## Sample ID Extraction

The script automatically extracts the sample ID from:
1. **Parent directory name (preferred)**
   - `/path/to/mtdna/A259999/variants.annotated.txt` → Sample ID: `A259999`
2. **Filename if directory parsing fails**
   - Falls back to extracting from filename

## Logging and Diagnostics

### Normal Output
```
INFO: Processing file: variants.annotated.txt
INFO: Sample ID: A259999
INFO: Found known MT-RNR1 variant: m.663A>G
INFO: Found known MT-RNR1 variant: m.1555A>G
INFO: Found 2 known MT-RNR1 variant(s)
INFO: Writing output to: /tmp/A259999.mtrnr1.tsv
INFO: Output: MT-RNR1	m.663A>G
INFO: Output: MT-RNR1	m.1555A>G
Success! Created PharmCAT outside call file: A259999.mtrnr1.tsv
```

### Verbose Output (`--verbose`)
```
INFO: Processing file: variants.annotated.txt
INFO: Sample ID: A251114
DEBUG: Found unknown MT-RNR1 variant: m.750A>G
DEBUG: Found unknown MT-RNR1 variant: m.1438A>G
INFO: Found known MT-RNR1 variant: m.1555A>G
INFO: Found 1 known MT-RNR1 variant(s)
INFO: Found 2 unknown MT-RNR1 variant(s) not in PharmCAT's known list
INFO: These variants will not be included in output
```

### With Unknown Variants
```
WARNING: Found 2 unknown MT-RNR1 variant(s): m.750A>G, m.1438A>G
WARNING: Including unknown variants in output (--include-unknown flag set)
```

## Integration with PharmCAT

### Standard Workflow

```bash
# 1. Run mtdna-server-2 on your BAM file
# (produces variants.annotated.txt)

# 2. Extract MT-RNR1 variants for PharmCAT
python3 extract_mtrnr1_variants.py \
  -i mtdna_results/sample/variants.annotated.txt \
  -o pharmcat_input/sample.mtrnr1.tsv

# 3. Run PharmCAT with both VCF and MT-RNR1 outside call
pharmcat \
  -vcf sample.vcf \
  -po pharmcat_input/sample.mtrnr1.tsv \
  -reporterHtml \
  -reporterJson
```

### Chinese Translation Support

If using the PharmCAT chinese-translation branch, the MT-RNR1 phenotypes will be automatically translated to Chinese in the final report.

## Troubleshooting

### Error: Input file not found
**Cause:** Specified file path doesn't exist
**Solution:** Check file path, ensure mtdna-server-2 completed successfully

### Error: No MT-RNR1 rows found
**Cause:** Input file has no MT-RNR1 variants or incorrect format
**Solution:** Verify input is from mtdna-server-2, check that file has Maplocus column in header

### Warning: No known variants found
**Cause:** Sample has MT-RNR1 variants but none match PharmCAT's known list
**Result:** Script outputs `Reference` (normal behavior)
**Action:** This is expected for most samples. Use `--verbose` to see which variants were found.

### Delimiter/encoding issues
**Solution:** Ensure input file uses tab delimiters and UTF-8 encoding

## Technical Notes

### Mitochondrial Heteroplasmy
- mtdna-server-2 reports heteroplasmy levels
- This script accepts both homoplasmic (1/1) and heteroplasmic (0/1) variants
- Only PASS-filtered variants are included by default

### Monoploid Gene Handling
- MT-RNR1 exists in mitochondrial DNA (single copy, not diploid)
- PharmCAT expects single allele format (no slash separator)
- Format: `MT-RNR1\tm.1555A>G` (NOT `MT-RNR1\tm.1555A>G/m.1555A>G`)

### Variant Notation
- PharmCAT's MT_RNR1.json uses the `m.` prefix format (e.g., `m.1555A>G`)
- This script outputs with the `m.` prefix to match PharmCAT's expected keys
- Deletions are formatted as: `m.{Pos}{Ref}>del` (e.g., `m.960C>del`)

## Validation

The script has been validated to produce output that **exactly matches** the keys in PharmCAT's [MT_RNR1.json](../src/main/resources/org/pharmgkb/pharmcat/phenotype/MT_RNR1.json):

```bash
✓ All 24 JSON variants are supported by the script
✓ No extra variants in the script
✅ PERFECT MATCH: Script variants exactly match MT_RNR1.json
```

## References

- [PharmCAT Outside Call Format Documentation](../../docs/using/Outside-Call-Format.md)
- [PharmCAT MT-RNR1 Phenotype Definitions](../src/main/resources/org/pharmgkb/pharmcat/phenotype/MT_RNR1.json)
- [mtdna-server-2 GitHub Repository](https://github.com/genepi/mtdna-server)
- [CPIC Guideline on Aminoglycosides](https://cpicpgx.org/)

## Version History

- **1.0.2** (2025-12-17): Auto-detect Maplocus column
  - **CRITICAL FIX**: Auto-detect Maplocus column position from header
  - Now works with both 14-column and 38-column mtdna-server-2 formats
  - Tested with real data from mtdna-server-2

- **1.0.1** (2025-12-17): Updated to match MT_RNR1.json format
  - **CRITICAL FIX**: Added "m." prefix to variant notation (e.g., `m.1555A>G`)
  - Validated against PharmCAT's MT_RNR1.json (perfect match)
  - All 24 known variants now use correct format

- **1.0.0** (2025-12-17): Initial release
  - Support for 24 PharmCAT-known MT-RNR1 variants
  - Automatic sample ID extraction
  - Configurable unknown variant handling
  - Verbose logging support

## Author

Generated with Claude Code (https://claude.com/claude-code)

## License

This script is part of the PharmCAT project. Refer to the main PharmCAT license for usage terms.
