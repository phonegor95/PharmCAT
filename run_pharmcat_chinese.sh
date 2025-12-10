#!/bin/bash

# PharmCAT Chinese Translation Pipeline
# Unified script for running PharmCAT with Chinese translation support
# Supports both online Docker image (recommended) and local build
# Author: PharmCAT Chinese Translation Project
# Date: 2024-09-25

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker image configuration
DOCKER_IMAGE="phonegor95/pharmcat:chinese"
DEFAULT_INPUT="PT_04.filtered.vcf.gz"

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

# Pull Docker image from Docker Hub
pull_docker() {
    print_status "Pulling PharmCAT Chinese translation image from Docker Hub..."
    print_status "Image: $DOCKER_IMAGE"

    sudo docker pull "$DOCKER_IMAGE"

    print_success "Docker image pulled successfully"
}

# Build Docker image (fallback option)
build_docker() {
    print_status "Building Docker image with Chinese translation support..."

    sudo docker build --network=host -t "$DOCKER_IMAGE" .

    print_success "Docker image built successfully"
}

# Show Docker image info
show_image_info() {
    print_status "Docker image information:"
    sudo docker images "$DOCKER_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

    print_status "Image details:"
    echo "  Repository: phonegor95/pharmcat"
    echo "  Tag: chinese"
    echo "  Features: Chinese drug names, phenotypes, and recommendations"
    echo "  Docker Hub: https://hub.docker.com/r/phonegor95/pharmcat"
}

# Run PharmCAT pipeline
run_pipeline() {
    local input_file="$1"

    if [ -z "$input_file" ]; then
        input_file="$DEFAULT_INPUT"
        print_warning "No input file specified, using default: $input_file"
    fi

    if [ ! -f "$input_file" ]; then
        print_error "Input file not found: $input_file"
        exit 1
    fi

    print_status "Running PharmCAT pipeline with Chinese translation..."
    print_status "Input file: $input_file"
    print_status "Docker image: $DOCKER_IMAGE"

    # Run the pipeline
    sudo docker run --rm \
        -v "$(pwd):/pharmcat/data" \
        "$DOCKER_IMAGE" \
        pharmcat_pipeline "data/$input_file" \
        --missing-to-ref -G -reporterHtml -reporterJson

    print_success "Pipeline completed successfully"
}

# Display results
show_results() {
    local base_name="$1"

    print_status "Generated files:"
    ls -lh "${base_name}".*.{html,json,vcf,txt} 2>/dev/null | while read line; do
        echo "  $line"
    done

    if [ -f "${base_name}.report.html" ]; then
        print_success "Chinese translation report: ${base_name}.report.html"
        print_status "Open this file in your browser to view the Chinese translation"
    fi
}

# Main function
main() {
    echo "=================================================="
    echo "PharmCAT Chinese Translation Pipeline"
    echo "=================================================="
    
    # Parse command line arguments
    INPUT_FILE=""
    SKIP_PULL=false
    BUILD_LOCAL=false
    SHOW_INFO=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                INPUT_FILE="$2"
                shift 2
                ;;
            --skip-pull)
                SKIP_PULL=true
                shift
                ;;
            --build-local)
                BUILD_LOCAL=true
                shift
                ;;
            --skip-build)
                # Legacy option for backward compatibility
                SKIP_PULL=true
                shift
                ;;
            --info)
                SHOW_INFO=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "This unified script supports both online Docker image (recommended) and local build."
                echo ""
                echo "Options:"
                echo "  -i, --input FILE    Input VCF file (default: $DEFAULT_INPUT)"
                echo "  --skip-pull         Skip pulling Docker image (use existing)"
                echo "  --build-local       Build Docker image locally instead of pulling"
                echo "  --skip-build        Legacy option (same as --skip-pull)"
                echo "  --info              Show Docker image information"
                echo "  -h, --help          Show this help message"
                echo ""
                echo "Recommended Usage (Online Docker Image):"
                echo "  $0 -i file.vcf.gz                    # Pull latest and run"
                echo "  $0 --skip-pull -i file.vcf.gz        # Use existing image"
                echo "  $0 --info                            # Show image info"
                echo ""
                echo "Alternative Usage (Local Build):"
                echo "  $0 --build-local -i file.vcf.gz      # Build locally and run"
                echo ""
                echo "Docker Image: $DOCKER_IMAGE"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Show image info if requested
    if [ "$SHOW_INFO" = true ]; then
        check_prerequisites
        show_image_info
        exit 0
    fi

    # Check prerequisites
    check_prerequisites

    # Docker image steps
    if [ "$BUILD_LOCAL" = true ]; then
        print_status "Mode: Local build"
        clean_build
        compile_pharmcat
        build_docker
    elif [ "$SKIP_PULL" = false ]; then
        print_status "Mode: Online Docker image (recommended)"
        pull_docker
    else
        print_warning "Mode: Using existing image"
        print_status "Skipping Docker image pull/build as requested"
    fi

    # Use provided input file or default
    if [ -z "$INPUT_FILE" ]; then
        INPUT_FILE="$DEFAULT_INPUT"
    fi
    
    # Run pipeline
    run_pipeline "$INPUT_FILE"
    
    # Extract base name for results
    BASE_NAME=$(basename "$INPUT_FILE" .vcf.gz)
    BASE_NAME=$(basename "$BASE_NAME" .vcf)
    
    # Show results
    show_results "$BASE_NAME"
    
    echo "=================================================="
    print_success "PharmCAT Chinese Translation completed!"
    echo "=================================================="

    print_status "Next steps:"
    echo "1. Open ${BASE_NAME}.report.html in your browser"
    echo "2. Review the Chinese translation results"
    echo "3. Share the Docker image: docker pull $DOCKER_IMAGE"
}

# Run main function with all arguments
main "$@"
