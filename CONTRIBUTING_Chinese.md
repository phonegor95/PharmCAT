# Contributing Chinese Translation to PharmCAT

This guide explains how to contribute the Chinese translation feature to the main PharmCAT repository.

## 🚀 Quick Start

### Step 1: Fork the Repository

1. **Go to the main PharmCAT repository**: https://github.com/PharmGKB/PharmCAT
2. **Click "Fork"** in the top right corner
3. **Select your account** to create the fork
4. **Wait for the fork to be created** at `https://github.com/YOUR_USERNAME/PharmCAT`

### Step 2: Update Remote URLs

After forking, update your local repository to push to your fork:

```bash
# Add your fork as a remote (replace YOUR_USERNAME with your GitHub username)
git remote add fork https://github.com/YOUR_USERNAME/PharmCAT.git

# Verify remotes
git remote -v
```

### Step 3: Push Your Branch

```bash
# Push the chinese-translation branch to your fork
git push fork chinese-translation
```

### Step 4: Create Pull Request

1. **Go to your fork**: `https://github.com/YOUR_USERNAME/PharmCAT`
2. **Click "Compare & pull request"** (GitHub will show this automatically)
3. **Fill out the pull request template**:

## 📝 Pull Request Template

```markdown
## Chinese Translation Support for PharmCAT

### Summary
This PR adds comprehensive Chinese translation support to PharmCAT, enabling the generation of pharmacogenomic reports with Chinese drug names, phenotype descriptions, and prescribing guidance.

### Features Implemented
- ✅ Chinese drug names in prescribing recommendation section headers
- ✅ Chinese phenotype translation system (慢代谢型, 正常代谢型, etc.)
- ✅ Chinese prescribing guidance content support
- ✅ Backward compatibility maintained
- ✅ Automated build and deployment script
- ✅ Comprehensive documentation and examples

### Technical Changes

#### Core Implementation
- **ReportHelpers.java**: Added `getChineseDrugName()` and `printRecMapWithChinese()` methods
- **AccessionObject.java**: Added `name_cn` field support for Chinese drug names
- **RecommendationAnnotation.java**: Added `lookupKey_cn` support for Chinese phenotypes
- **AnnotationReport.java**: Added missing `getLookupKey()` method
- **report.hbs**: Updated HTML template to use Chinese translation methods

#### New Files
- **README_Chinese.md**: Comprehensive documentation (174 lines)
- **run_pharmcat_chinese.sh**: Automated build and run script
- **example_chinese_config.json**: Example configuration
- **test_chinese_translation.sh**: Validation script

### Translation Examples

| English | Chinese |
|---------|---------|
| Poor Metabolizer | 慢代谢型 |
| Normal Metabolizer | 正常代谢型 |
| Intermediate Metabolizer | 中等代谢型 |
| Decreased Function | 功能降低 |
| Normal Function | 正常功能 |

### Usage

```bash
# Compile and run with Chinese translation
./run_pharmcat_chinese.sh -i your_file.vcf.gz

# Skip build if already compiled
./run_pharmcat_chinese.sh --skip-build -i your_file.vcf.gz
```

### Testing
- ✅ All existing tests pass
- ✅ Chinese translation validation script included
- ✅ Example configuration provided
- ✅ Backward compatibility verified

### Configuration
Users can add Chinese translations to their prescribing guidance JSON:

```json
{
  "relatedChemicals": [
    {
      "name": "warfarin",
      "name_cn": "华法林"
    }
  ],
  "lookupKey": {
    "CYP2C9": "Poor Metabolizer"
  },
  "lookupKey_cn": {
    "CYP2C9": "慢代谢型"
  }
}
```

### Impact
- Enables PharmCAT usage in Chinese-speaking healthcare environments
- Maintains full backward compatibility
- Provides foundation for other language translations
- Includes comprehensive documentation and automation

### Checklist
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Documentation updated
- [x] Tests added/updated
- [x] Backward compatibility maintained
- [x] Example usage provided
```

## 🔧 Alternative: Create Patch Files

If you prefer not to use GitHub's web interface, you can create patch files:

```bash
# Create patch files for your commits
git format-patch origin/development..chinese-translation

# This will create .patch files that can be emailed or shared
```

## 📧 Contact Information

If you need help with the contribution process:

1. **GitHub Issues**: Create an issue in the main PharmCAT repository
2. **Email**: Contact the PharmCAT maintainers
3. **Documentation**: Refer to PharmCAT's CONTRIBUTING.md file

## 🎯 Next Steps

1. **Fork the repository** on GitHub
2. **Update your remote** to point to your fork
3. **Push your branch** to your fork
4. **Create a pull request** using the template above
5. **Respond to feedback** from maintainers

Your Chinese translation feature is well-implemented and ready for contribution! 🎉
