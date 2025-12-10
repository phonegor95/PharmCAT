#!/bin/bash

# Setup script for contributing Chinese translation to PharmCAT
# This script helps set up the proper git remotes and provides instructions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=================================================="
echo "PharmCAT Chinese Translation Contribution Setup"
echo "=================================================="

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "chinese-translation" ]; then
    print_error "You're not on the chinese-translation branch!"
    echo "Current branch: $CURRENT_BRANCH"
    echo "Please switch to chinese-translation branch:"
    echo "  git checkout chinese-translation"
    exit 1
fi

print_success "On chinese-translation branch"

# Check current remotes
print_status "Current git remotes:"
git remote -v

# Get GitHub username
echo ""
read -p "Enter your GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    print_error "GitHub username is required"
    exit 1
fi

# Check if fork remote already exists
if git remote | grep -q "^fork$"; then
    print_warning "Fork remote already exists, updating URL..."
    git remote set-url fork "https://github.com/$GITHUB_USERNAME/PharmCAT.git"
else
    print_status "Adding fork remote..."
    git remote add fork "https://github.com/$GITHUB_USERNAME/PharmCAT.git"
fi

print_success "Fork remote configured: https://github.com/$GITHUB_USERNAME/PharmCAT.git"

# Show current status
echo ""
print_status "Current git status:"
git status --short

echo ""
print_status "Recent commits on chinese-translation branch:"
git log --oneline -3

echo ""
echo "=================================================="
print_success "Setup Complete!"
echo "=================================================="

echo ""
print_warning "NEXT STEPS:"
echo ""
echo "1. 🍴 FORK THE REPOSITORY:"
echo "   - Go to: https://github.com/PharmGKB/PharmCAT"
echo "   - Click 'Fork' button"
echo "   - Wait for fork to be created at: https://github.com/$GITHUB_USERNAME/PharmCAT"
echo ""
echo "2. 🚀 PUSH YOUR BRANCH:"
echo "   git push fork chinese-translation"
echo ""
echo "3. 📝 CREATE PULL REQUEST:"
echo "   - Go to: https://github.com/$GITHUB_USERNAME/PharmCAT"
echo "   - Click 'Compare & pull request'"
echo "   - Use the template in CONTRIBUTING_Chinese.md"
echo ""
echo "4. 📋 PULL REQUEST TITLE:"
echo "   feat: Add comprehensive Chinese translation support for PharmCAT"
echo ""
echo "5. 📄 REFERENCE FILES:"
echo "   - CONTRIBUTING_Chinese.md (contribution guide)"
echo "   - README_Chinese.md (comprehensive documentation)"
echo "   - run_pharmcat_chinese.sh (unified build/run script)"
echo "   - test_chinese_translation.sh (validation script)"
echo ""

print_success "Your Chinese translation feature is ready for contribution!"

echo ""
print_status "Summary of changes:"
echo "  - Core translation implementation (5 Java files, 1 template)"
echo "  - Comprehensive documentation (README_Chinese.md)"
echo "  - Unified build/run script with online Docker support"
echo "  - Test validation script"
echo "  - Contribution setup helper"

echo ""
print_warning "Remember to:"
echo "  ✅ Fork the repository first"
echo "  ✅ Push to your fork (not the main repo)"
echo "  ✅ Create pull request from your fork"
echo "  ✅ Use the provided PR template"
