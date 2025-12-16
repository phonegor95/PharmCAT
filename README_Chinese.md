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

## 🎯 Quick Start

### Prerequisites

- Java 17 or later
- Docker
- Gradle (included via wrapper)

### Recommended: Using Online Docker Image

The fastest way to use PharmCAT with Chinese translation:

```bash
# Run with online Docker image (recommended - always up to date)
./run_pharmcat_chinese.sh -i your_file.vcf.gz

# Quick run without updating image
./run_pharmcat_chinese.sh --skip-pull -i your_file.vcf.gz

# Show Docker image information
./run_pharmcat_chinese.sh --info
```

### Alternative: Local Build

```bash
# Build locally instead of pulling from Docker Hub
./run_pharmcat_chinese.sh --build-local -i your_file.vcf.gz

# Show help
./run_pharmcat_chinese.sh --help
```

### Command Aliases (Optional)

For convenience, you can set up aliases:

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias pharmcat-cn='./run_pharmcat_chinese.sh'
alias pharmcat-test-cn='./test_chinese_translation.sh'

# Then use:
pharmcat-cn -i your_file.vcf.gz
```

## 📋 Usage Examples

### Basic Usage

```bash
# Run with default file
./run_pharmcat_chinese.sh

# Run with specific VCF file
./run_pharmcat_chinese.sh -i your_file.vcf.gz

# Skip image pull/update (faster for repeated runs)
./run_pharmcat_chinese.sh --skip-pull -i your_file.vcf.gz
```

### Advanced Usage

```bash
# Build Docker image locally
./run_pharmcat_chinese.sh --build-local -i your_file.vcf.gz

# Show Docker image details
./run_pharmcat_chinese.sh --info

# Test Chinese translation features
./test_chinese_translation.sh
```

### Manual Docker Commands

If you prefer to run steps manually:

```bash
# 1. Pull the online Docker image
sudo docker pull phonegor95/pharmcat:chinese

# 2. Run pipeline directly
sudo docker run --rm \
  -v $(pwd):/pharmcat/data \
  phonegor95/pharmcat:chinese \
  pharmcat_pipeline "data/your_file.vcf.gz" \
  --missing-to-ref -G -reporterHtml -reporterJson

# 3. Build locally (optional)
./gradlew clean shadowJar
cp build/libs/pharmcat-*-all.jar build/pharmcat.jar
sudo docker build --network=host -t phonegor95/pharmcat:chinese .
sudo docker push phonegor95/pharmcat:chinese
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

## 🔧 Chinese Translation Setup (Optional)

### Default Configuration

To make Chinese translation the default for all operations:

```bash
# Set environment variables in your shell profile (~/.bashrc or ~/.zshrc)
export PHARMCAT_LANG=zh-CN
export PHARMCAT_TRANSLATION=chinese
export PHARMCAT_DOCKER_IMAGE=phonegor95/pharmcat:chinese

# Create convenient aliases
alias pharmcat-cn='./run_pharmcat_chinese.sh'
alias pharmcat-test-cn='./test_chinese_translation.sh'
alias pharmcat-quick='./run_pharmcat_chinese.sh --skip-pull'

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

### File Structure

```
PharmCAT/
├── run_pharmcat_chinese.sh          # Unified Chinese translation script
├── test_chinese_translation.sh      # Test script
├── setup_contribution.sh            # Git setup for contributing
├── README_Chinese.md                # This documentation
└── CONTRIBUTING_Chinese.md          # Contribution guide
```

## 🛠️ Troubleshooting

### Common Issues

1. **Java Version**: Ensure Java 17+ is installed and set as default
   ```bash
   java -version  # Should show 17 or higher
   ```

2. **Docker Permissions**: The script uses `sudo docker` - ensure your user has Docker access
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **File Permissions**: Make sure scripts are executable
   ```bash
   chmod +x run_pharmcat_chinese.sh test_chinese_translation.sh
   ```

4. **Docker Not Available**: Install Docker first
   ```bash
   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io
   ```

### Verification

To verify Chinese translations are working:

```bash
# Run the test script
./test_chinese_translation.sh

# Check for Chinese drug names in section headers
grep -o '<h3 id="[^"]*">[^<]*</h3>' *.report.html

# Check for Chinese phenotypes in prescribing recommendations
grep -A 5 -B 5 "rx-phenotype" *.report.html | grep -E "(慢代谢型|正常代谢型|中等代谢型)"
```

### Reset to Defaults

If you need to reset or reconfigure:

```bash
# Pull fresh Docker image
sudo docker pull phonegor95/pharmcat:chinese

# Rebuild locally if needed
./run_pharmcat_chinese.sh --build-local -i your_file.vcf.gz
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
