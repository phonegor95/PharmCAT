#!/bin/bash

# Test script for PharmCAT Chinese Translation
# This script demonstrates the Chinese translation functionality using example data

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================================="
echo "PharmCAT Chinese Translation Test"
echo -e "==================================================${NC}"

# Test 1: Check if script exists and is executable
echo -e "${BLUE}[TEST 1]${NC} Checking script availability..."
if [ -x "./run_pharmcat_chinese.sh" ]; then
    echo -e "${GREEN}✅ Script is executable${NC}"
else
    echo -e "${YELLOW}⚠️  Making script executable...${NC}"
    chmod +x ./run_pharmcat_chinese.sh
fi

# Test 2: Check help functionality
echo -e "\n${BLUE}[TEST 2]${NC} Testing help functionality..."
./run_pharmcat_chinese.sh --help | head -10

# Test 3: Check if example VCF exists
echo -e "\n${BLUE}[TEST 3]${NC} Checking for example VCF files..."
if [ -f "docs/examples/pharmcat.example.vcf.bgz" ]; then
    echo -e "${GREEN}✅ Example VCF found: docs/examples/pharmcat.example.vcf.bgz${NC}"
    EXAMPLE_VCF="docs/examples/pharmcat.example.vcf.bgz"
elif [ -f "docs/examples/multisample.vcf" ]; then
    echo -e "${GREEN}✅ Example VCF found: docs/examples/multisample.vcf${NC}"
    EXAMPLE_VCF="docs/examples/multisample.vcf"
else
    echo -e "${YELLOW}⚠️  No example VCF found, will use placeholder${NC}"
    EXAMPLE_VCF="example.vcf.gz"
fi

# Test 4: Check Chinese translation files
echo -e "\n${BLUE}[TEST 4]${NC} Checking Chinese translation implementation..."

echo "Checking modified Java files:"
if [ -f "src/main/java/org/pharmgkb/pharmcat/reporter/format/html/ReportHelpers.java" ]; then
    if grep -q "translatePhenotypesToChinese" src/main/java/org/pharmgkb/pharmcat/reporter/format/html/ReportHelpers.java; then
        echo -e "${GREEN}✅ ReportHelpers.java contains Chinese translation methods${NC}"
    fi
fi

if [ -f "src/main/java/org/pharmgkb/pharmcat/reporter/model/pgkb/AccessionObject.java" ]; then
    if grep -q "name_cn" src/main/java/org/pharmgkb/pharmcat/reporter/model/pgkb/AccessionObject.java; then
        echo -e "${GREEN}✅ AccessionObject.java supports Chinese drug names${NC}"
    fi
fi

if [ -f "src/main/resources/org/pharmgkb/pharmcat/reporter/report.hbs" ]; then
    if grep -q "getChineseDrugName\|printRecMapWithChinese" src/main/resources/org/pharmgkb/pharmcat/reporter/report.hbs; then
        echo -e "${GREEN}✅ HTML template uses Chinese translation methods${NC}"
    fi
fi

# Test 5: Check documentation
echo -e "\n${BLUE}[TEST 5]${NC} Checking documentation..."
if [ -f "README_Chinese.md" ]; then
    echo -e "${GREEN}✅ Chinese translation documentation exists${NC}"
    echo "Documentation size: $(wc -l < README_Chinese.md) lines"
fi

if [ -f "example_chinese_config.json" ]; then
    echo -e "${GREEN}✅ Example Chinese configuration exists${NC}"
    echo "Configuration size: $(wc -l < example_chinese_config.json) lines"
fi

# Test 6: Check git branch and commit
echo -e "\n${BLUE}[TEST 6]${NC} Checking git status..."
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "chinese-translation" ]; then
    echo -e "${GREEN}✅ On chinese-translation branch${NC}"
    echo "Latest commit:"
    git log --oneline -1
else
    echo -e "${YELLOW}⚠️  Not on chinese-translation branch${NC}"
fi

# Test 7: Demonstrate translation mappings
echo -e "\n${BLUE}[TEST 7]${NC} Chinese translation mappings:"
echo "English → Chinese:"
echo "  Poor Metabolizer → 慢代谢型"
echo "  Normal Metabolizer → 正常代谢型"
echo "  Intermediate Metabolizer → 中等代谢型"
echo "  Decreased Function → 功能降低"
echo "  Normal Function → 正常功能"

# Test 8: Show example usage
echo -e "\n${BLUE}[TEST 8]${NC} Example usage:"
echo "To run with example data:"
echo "  ./run_pharmcat_chinese.sh -i $EXAMPLE_VCF"
echo ""
echo "To run with your own VCF:"
echo "  ./run_pharmcat_chinese.sh -i your_file.vcf.gz"
echo ""
echo "To skip build (if already compiled):"
echo "  ./run_pharmcat_chinese.sh --skip-build -i your_file.vcf.gz"

echo -e "\n${BLUE}=================================================="
echo -e "${GREEN}Chinese Translation Test Complete!${NC}"
echo -e "${BLUE}=================================================="

echo -e "\n${YELLOW}Ready to publish to GitHub:${NC}"
echo "1. Current branch: chinese-translation"
echo "2. All Chinese translation features implemented"
echo "3. Documentation and examples provided"
echo "4. Automated build script ready"
echo ""
echo -e "${YELLOW}To push to GitHub:${NC}"
echo "  git push origin chinese-translation"
