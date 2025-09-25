# PharmCAT Chinese Translation - Default Configuration

This document explains how to set up and use Chinese translation as the default configuration for PharmCAT.

## 🎯 Quick Start

The Chinese translation has been set as the default configuration. You can now use these simplified commands:

```bash
# Test Chinese translation
pharmcat-test-cn

# Run with online Docker image (recommended)
pharmcat-online -i your_file.vcf.gz

# Run with Chinese translation (pulls/builds as needed)
pharmcat-cn -i your_file.vcf.gz

# Quick run (skip image update)
pharmcat-quick -i your_file.vcf.gz

# Build locally instead of using online image
pharmcat-build-cn -i your_file.vcf.gz
```

## 📋 What's Been Configured

### 1. Default Branch
- **Current branch**: `chinese-translation`
- **Global default**: Set to `chinese-translation` for new repositories
- **All Chinese translation features**: Fully implemented and tested

### 2. Environment Variables
```bash
PHARMCAT_LANG=zh-CN
PHARMCAT_TRANSLATION=chinese
PHARMCAT_DEFAULT_CONFIG=example_chinese_config.json
```

### 3. Command Aliases
- `pharmcat-online` → `./run_pharmcat_online.sh` (uses online Docker image)
- `pharmcat-cn` → `./run_pharmcat_chinese.sh` (pulls/builds as needed)
- `pharmcat-test-cn` → `./test_chinese_translation.sh`
- `pharmcat-build-cn` → `./run_pharmcat_chinese.sh --build-local`
- `pharmcat-quick` → `./run_pharmcat_online.sh --skip-pull`

### 4. Default Configuration Files
- **Main config**: `example_chinese_config.json`
- **Default settings**: `.pharmcat_defaults`
- **Docker image**: `phonegor95/pharmcat:chinese` (online)
- **Symlink**: `pharmcat_default_config.json` → `example_chinese_config.json`

## 🚀 Usage Examples

### Basic Usage (Online Docker Image - Recommended)
```bash
# Run with online Docker image (fastest)
pharmcat-online -i your_file.vcf.gz

# Quick run without updating image
pharmcat-quick -i your_file.vcf.gz

# Show Docker image information
pharmcat-online --info
```

### Traditional Usage (Local Build)
```bash
# Run with automatic pull/build
pharmcat-cn -i your_file.vcf.gz

# Build locally instead of pulling
pharmcat-build-cn -i your_file.vcf.gz

# Skip image operations
pharmcat-cn --skip-pull -i your_file.vcf.gz
```

### Advanced Usage
```bash
# Test all Chinese translation features
pharmcat-test-cn

# Direct Docker command with online image
sudo docker run --rm -v $(pwd):/pharmcat/data phonegor95/pharmcat:chinese pharmcat_pipeline "data/your_file.vcf.gz" --missing-to-ref -G -reporterHtml -reporterJson

# Pull the latest image manually
sudo docker pull phonegor95/pharmcat:chinese
```

## 📁 File Structure

```
PharmCAT/
├── run_pharmcat_chinese.sh          # Main Chinese translation script
├── test_chinese_translation.sh      # Test script
├── pharmcat_chinese_default.sh      # Setup script
├── example_chinese_config.json      # Chinese configuration
├── pharmcat_default_config.json     # Symlink to Chinese config
├── .pharmcat_defaults               # Default settings
├── README_Chinese.md                # Chinese documentation
└── README_Chinese_Default.md        # This file
```

## 🔧 Chinese Translation Features

### 1. Drug Names (药物名称)
- warfarin → 华法林
- allopurinol → 别嘌醇

### 2. Phenotype Translations (表型翻译)
- Poor Metabolizer → 慢代谢型
- Normal Metabolizer → 正常代谢型
- Intermediate Metabolizer → 中等代谢型
- Decreased Function → 功能降低
- Normal Function → 正常功能

### 3. Recommendation Translations (建议翻译)
- Complete Chinese translations for all clinical recommendations
- Localized dosing guidelines
- Chinese-specific clinical context

## 🛠️ Troubleshooting

### If aliases don't work:
```bash
source ~/.bashrc
```

### If scripts aren't executable:
```bash
chmod +x *.sh
```

### If Docker isn't available:
```bash
# Install Docker first, then run:
sudo docker build --network=host -t pcat .
```

### To reset to default configuration:
```bash
./pharmcat_chinese_default.sh
```

## 📊 Verification

Run the test script to verify everything is working:
```bash
pharmcat-test-cn
```

Expected output should show:
- ✅ All scripts executable
- ✅ Chinese translation methods implemented
- ✅ Documentation and examples available
- ✅ On chinese-translation branch

## 🌐 Repository Information

- **Current branch**: chinese-translation
- **Remote**: fork (https://github.com/phonegor95/PharmCAT.git)
- **Status**: Ready for production use
- **Last updated**: 2024-09-25

## 📝 Next Steps

1. **Test the setup**: `pharmcat-test-cn`
2. **Run with example data**: `pharmcat-cn -i docs/examples/pharmcat.example.vcf.bgz`
3. **Use with your data**: `pharmcat-cn -i your_file.vcf.gz`
4. **Share with team**: Push to GitHub with `git push fork chinese-translation`

---

**Note**: This configuration makes Chinese translation the default for all PharmCAT operations. The original English functionality remains available by switching branches if needed.
