#!/bin/bash

# PharmCAT Chinese Translation Pipeline
# This script compiles PharmCAT with Chinese translation support and runs the pipeline
# Author: PharmCAT Chinese Translation Project
# Date: 2024-09-25

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists java; then
        print_error "Java is not installed. Please install Java 17 or later."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker."
        exit 1
    fi
    
    if ! command_exists ./gradlew; then
        print_error "Gradle wrapper not found. Make sure you're in the PharmCAT root directory."
        exit 1
    fi
    
    # Check Java version
    java_version=$(java -version 2>&1 | head -n1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$java_version" -lt 17 ]; then
        print_error "Java 17 or later is required. Current version: $java_version"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Clean previous build artifacts
clean_build() {
    print_status "Cleaning previous build artifacts..."
    ./gradlew clean
    rm -f build/pharmcat.jar
    print_success "Build artifacts cleaned"
}

# Compile PharmCAT with Chinese translation support
compile_pharmcat() {
    print_status "Compiling PharmCAT with Chinese translation support..."
    
    # Build the shadow JAR
    ./gradlew shadowJar
    
    # Copy to standard location
    cp build/libs/pharmcat-*-all.jar build/pharmcat.jar
    
    print_success "PharmCAT compiled successfully"
}

# Build Docker image
build_docker() {
    print_status "Building Docker image with Chinese translation support..."
    
    sudo docker build --network=host -t pcat .
    
    print_success "Docker image built successfully"
}

# Run PharmCAT pipeline
run_pipeline() {
    local input_file="$1"
    
    if [ -z "$input_file" ]; then
        print_error "No input file specified"
        exit 1
    fi
    
    if [ ! -f "$input_file" ]; then
        print_error "Input file not found: $input_file"
        exit 1
    fi
    
    print_status "Running PharmCAT pipeline with Chinese translation..."
    print_status "Input file: $input_file"
    
    # Run the pipeline
    sudo docker run --rm -v $(pwd):/pharmcat/data pcat pharmcat_pipeline "data/$input_file" --missing-to-ref -G -reporterHtml -reporterJson
    
    print_success "Pipeline completed successfully"
}

# Display results
show_results() {
    local base_name="$1"
    
    print_status "Generated files:"
    ls -lh "${base_name}".*.{html,json,vcf,txt} 2>/dev/null | while read line; do
        echo "  $line"
    done
    
    print_success "Chinese translation report generated: ${base_name}.report.html"
}

# Main function
main() {
    echo "=================================================="
    echo "PharmCAT Chinese Translation Pipeline"
    echo "=================================================="
    
    # Parse command line arguments
    INPUT_FILE=""
    SKIP_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                INPUT_FILE="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -i, --input FILE    Input VCF file (required)"
                echo "  --skip-build        Skip compilation and Docker build"
                echo "  -h, --help          Show this help message"
                echo ""
                echo "Example:"
                echo "  $0 -i PT_04.filtered.vcf.gz"
                echo "  $0 --skip-build -i PT_04.filtered.vcf.gz"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Use default input file if not specified
    if [ -z "$INPUT_FILE" ]; then
        INPUT_FILE="PT_04.filtered.vcf.gz"
        print_warning "No input file specified, using default: $INPUT_FILE"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Build steps (unless skipped)
    if [ "$SKIP_BUILD" = false ]; then
        clean_build
        compile_pharmcat
        build_docker
    else
        print_warning "Skipping build steps as requested"
    fi
    
    # Run pipeline
    run_pipeline "$INPUT_FILE"
    
    # Extract base name for results
    BASE_NAME=$(basename "$INPUT_FILE" .vcf.gz)
    BASE_NAME=$(basename "$BASE_NAME" .vcf)
    
    # Show results
    show_results "$BASE_NAME"
    
    echo "=================================================="
    print_success "PharmCAT Chinese Translation Pipeline completed!"
    echo "=================================================="
}

# Run main function with all arguments
main "$@"
