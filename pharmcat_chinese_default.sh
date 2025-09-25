#!/bin/bash

# PharmCAT Chinese Translation Default Configuration
# This script sets up Chinese translation as the default configuration for PharmCAT

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================================="
echo "Setting PharmCAT Chinese Translation as Default"
echo -e "==================================================${NC}"

# 1. Set Chinese translation branch as default for new repos
echo -e "${BLUE}[STEP 1]${NC} Setting default branch to chinese-translation..."
git config --global init.defaultBranch chinese-translation
echo -e "${GREEN}✅ Default branch set to chinese-translation${NC}"

# 2. Switch to chinese-translation branch if not already on it
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "chinese-translation" ]; then
    echo -e "${BLUE}[STEP 2]${NC} Switching to chinese-translation branch..."
    git checkout chinese-translation
    echo -e "${GREEN}✅ Switched to chinese-translation branch${NC}"
else
    echo -e "${BLUE}[STEP 2]${NC} Already on chinese-translation branch"
    echo -e "${GREEN}✅ Current branch: $CURRENT_BRANCH${NC}"
fi

# 3. Set up Chinese translation environment variables
echo -e "${BLUE}[STEP 3]${NC} Setting up Chinese translation environment..."
export PHARMCAT_LANG=zh-CN
export PHARMCAT_TRANSLATION=chinese
export PHARMCAT_DEFAULT_CONFIG=example_chinese_config.json
echo -e "${GREEN}✅ Environment variables set${NC}"

# 4. Create default configuration symlink
echo -e "${BLUE}[STEP 4]${NC} Creating default configuration..."
if [ -f "example_chinese_config.json" ]; then
    ln -sf example_chinese_config.json pharmcat_default_config.json
    echo -e "${GREEN}✅ Default configuration linked to Chinese config${NC}"
else
    echo -e "${YELLOW}⚠️  Chinese config file not found${NC}"
fi

# 5. Set up aliases for Chinese translation commands
echo -e "${BLUE}[STEP 5]${NC} Setting up command aliases..."
cat >> ~/.bashrc << 'EOF'

# PharmCAT Chinese Translation Aliases
alias pharmcat-cn='./run_pharmcat_chinese.sh'
alias pharmcat-online='./run_pharmcat_online.sh'
alias pharmcat-test-cn='./test_chinese_translation.sh'
alias pharmcat-build-cn='./run_pharmcat_chinese.sh --build-local'
alias pharmcat-quick='./run_pharmcat_online.sh --skip-pull'
export PHARMCAT_LANG=zh-CN
export PHARMCAT_TRANSLATION=chinese
export PHARMCAT_DOCKER_IMAGE=phonegor95/pharmcat:chinese
EOF

echo -e "${GREEN}✅ Aliases added to ~/.bashrc${NC}"

# 6. Make scripts executable
echo -e "${BLUE}[STEP 6]${NC} Making Chinese translation scripts executable..."
chmod +x run_pharmcat_chinese.sh
chmod +x test_chinese_translation.sh
echo -e "${GREEN}✅ Scripts are now executable${NC}"

# 7. Display current configuration
echo -e "${BLUE}[STEP 7]${NC} Current configuration summary:"
echo "  Current branch: $(git branch --show-current)"
echo "  Default branch: $(git config --get init.defaultBranch)"
echo "  Chinese config: $(ls -la example_chinese_config.json 2>/dev/null || echo 'Not found')"
echo "  Translation scripts: $(ls -la *chinese*.sh 2>/dev/null | wc -l) files"

echo -e "\n${BLUE}=================================================="
echo -e "${GREEN}Chinese Translation Set as Default Successfully!${NC}"
echo -e "${BLUE}=================================================="

echo -e "\n${YELLOW}Usage:${NC}"
echo "  pharmcat-online -i file.vcf.gz     # Run with online Docker image (recommended)"
echo "  pharmcat-cn -i your_file.vcf.gz    # Run with Chinese translation"
echo "  pharmcat-test-cn                   # Test Chinese translation"
echo "  pharmcat-quick -i file.vcf.gz      # Quick run (skip image update)"
echo "  pharmcat-build-cn -i file.vcf.gz   # Build locally"

echo -e "\n${YELLOW}To apply aliases in current session:${NC}"
echo "  source ~/.bashrc"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Run: source ~/.bashrc"
echo "2. Test: pharmcat-test-cn"
echo "3. Use: pharmcat-cn -i your_file.vcf.gz"
