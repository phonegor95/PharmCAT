# PharmCAT Chinese Translation Support

This branch adds comprehensive Chinese translation support to PharmCAT, enabling the generation of pharmacogenomic reports with Chinese drug names, phenotype descriptions, and prescribing guidance.

## Features

### ✅ Implemented Features

1. **Chinese Drug Names**: Drug section headers in prescribing recommendations display Chinese names
   - Example: `华法林` (warfarin), `别嘌醇` (allopurinol), `阿米替林` (amitriptyline)

2. **Chinese Phenotype Translation**: All phenotype values in prescribing recommendations are displayed in Chinese
   - `慢代谢型` (Poor Metabolizer)
   - `正常代谢型` (Normal Metabolizer)
   - `中等代谢型` (Intermediate Metabolizer)
   - `功能降低` (Decreased Function)
   - `正常功能` (Normal Function)

3. **Chinese Prescribing Guidance**: Full support for Chinese prescribing guidance content

## Quick Start

### Prerequisites

- Java 17 or later
- Docker
- Gradle (included via wrapper)

### Running the Pipeline

Use the provided script to compile and run PharmCAT with Chinese translation:

```bash
# Full build and run
./run_pharmcat_chinese.sh -i PT_04.filtered.vcf.gz

# Skip build if already compiled
./run_pharmcat_chinese.sh --skip-build -i PT_04.filtered.vcf.gz

# Show help
./run_pharmcat_chinese.sh --help
```

### Manual Steps

If you prefer to run steps manually:

```bash
# 1. Compile PharmCAT
./gradlew clean shadowJar
cp build/libs/pharmcat-*-all.jar build/pharmcat.jar

# 2. Build Docker image
sudo docker build --network=host -t pcat .

# 3. Run pipeline
sudo docker run --rm -v $(pwd):/pharmcat/data pcat pharmcat_pipeline data/PT_04.filtered.vcf.gz --missing-to-ref -G -reporterHtml -reporterJson
```

## Configuration

### Chinese Drug Names

Add Chinese drug names to your prescribing guidance JSON file:

```json
{
  "relatedChemicals": [
    {
      "name": "warfarin",
      "name_cn": "华法林"
    }
  ]
}
```

### Chinese Phenotypes

Add Chinese phenotype translations using `lookupKey_cn`:

```json
{
  "lookupKey": {
    "CYP2C9": "Poor Metabolizer"
  },
  "lookupKey_cn": {
    "CYP2C9": "慢代谢型"
  }
}
```

## Technical Implementation

### Modified Files

1. **Core Translation Logic**:
   - `src/main/java/org/pharmgkb/pharmcat/reporter/format/html/ReportHelpers.java`
   - Added `getChineseDrugName()` and `printRecMapWithChinese()` methods

2. **Data Model Support**:
   - `src/main/java/org/pharmgkb/pharmcat/reporter/model/pgkb/AccessionObject.java`
   - `src/main/java/org/pharmgkb/pharmcat/reporter/model/pgkb/RecommendationAnnotation.java`
   - `src/main/java/org/pharmgkb/pharmcat/reporter/model/result/AnnotationReport.java`

3. **HTML Template**:
   - `src/main/resources/org/pharmgkb/pharmcat/reporter/report.hbs`

### Translation Mapping

The system supports automatic translation of common phenotype terms:

| English | Chinese |
|---------|---------|
| Poor Metabolizer | 慢代谢型 |
| Normal Metabolizer | 正常代谢型 |
| Intermediate Metabolizer | 中等代谢型 |
| Rapid Metabolizer | 快代谢型 |
| Ultrarapid Metabolizer | 超快代谢型 |
| Decreased Function | 功能降低 |
| Normal Function | 正常功能 |
| No Function | 无功能 |
| Increased Function | 功能增强 |

## Example Output

The generated HTML report will display:

- **Section Headers**: Chinese drug names (e.g., `华法林` instead of `warfarin`)
- **Phenotype Values**: Chinese phenotype descriptions (e.g., `慢代谢型` instead of `Poor Metabolizer`)
- **Prescribing Guidance**: Chinese recommendation text as configured in your guidance file

## Files Generated

After running the pipeline, you'll find:

- `*.report.html` - HTML report with Chinese translations
- `*.report.json` - JSON report data
- `*.match.json` - Allele matching results
- `*.phenotype.json` - Phenotype calling results
- `*.match_warnings.txt` - Any matching warnings

## Troubleshooting

### Common Issues

1. **Java Version**: Ensure Java 17+ is installed and set as default
2. **Docker Permissions**: The script uses `sudo docker` - ensure your user has Docker access
3. **File Permissions**: Make sure the script is executable: `chmod +x run_pharmcat_chinese.sh`

### Verification

To verify Chinese translations are working:

```bash
# Check for Chinese drug names in section headers
grep -o '<h3 id="[^"]*">[^<]*</h3>' *.report.html

# Check for Chinese phenotypes in prescribing recommendations
grep -A 5 -B 5 "rx-phenotype" *.report.html | grep -E "(慢代谢型|正常代谢型|中等代谢型)"
```

## Contributing

This Chinese translation feature is ready for integration into the main PharmCAT repository. The implementation:

- ✅ Maintains backward compatibility
- ✅ Uses clean, maintainable code
- ✅ Follows existing PharmCAT patterns
- ✅ Includes comprehensive error handling
- ✅ Provides automated build and test scripts

## License

This work extends PharmCAT under the same license terms as the original project.
