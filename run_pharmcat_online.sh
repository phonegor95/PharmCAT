#!/bin/bash

# PharmCAT Chinese Translation - Online Docker Image Runner
# This script uses the online Docker image from Docker Hub
# Author: PharmCAT Chinese Translation Project
# Date: 2024-09-25

set -e

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

# Function to check if Docker is available
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! sudo docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running or you don't have permission."
        exit 1
    fi
    
    print_success "Docker is available"
}

# Function to pull the latest image
pull_image() {
    print_status "Pulling latest PharmCAT Chinese translation image..."
    print_status "Image: $DOCKER_IMAGE"
    
    sudo docker pull "$DOCKER_IMAGE"
    
    print_success "Image pulled successfully"
}

# Function to run PharmCAT pipeline
run_pharmcat() {
    local input_file="$1"
    
    if [ -z "$input_file" ]; then
        input_file="$DEFAULT_INPUT"
        print_warning "No input file specified, using default: $input_file"
    fi
    
    if [ ! -f "$input_file" ]; then
        print_error "Input file not found: $input_file"
        exit 1
    fi
    
    print_status "Running PharmCAT with Chinese translation..."
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

# Function to show results
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

# Function to show image info
show_image_info() {
    print_status "Docker image information:"
    sudo docker images "$DOCKER_IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    print_status "Image details:"
    echo "  Repository: phonegor95/pharmcat"
    echo "  Tag: chinese"
    echo "  Features: Chinese drug names, phenotypes, and recommendations"
    echo "  Docker Hub: https://hub.docker.com/r/phonegor95/pharmcat"
}

# Main function
main() {
    echo "=================================================="
    echo "PharmCAT Chinese Translation - Online Runner"
    echo "=================================================="
    
    # Parse command line arguments
    INPUT_FILE=""
    SKIP_PULL=false
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
            --info)
                SHOW_INFO=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -i, --input FILE    Input VCF file"
                echo "  --skip-pull         Skip pulling latest image"
                echo "  --info              Show Docker image information"
                echo "  -h, --help          Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                                    # Run with default file"
                echo "  $0 -i your_file.vcf.gz              # Run with specific file"
                echo "  $0 --skip-pull -i file.vcf.gz       # Skip image update"
                echo "  $0 --info                           # Show image info"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Check Docker availability
    check_docker
    
    # Show image info if requested
    if [ "$SHOW_INFO" = true ]; then
        show_image_info
        exit 0
    fi
    
    # Pull latest image unless skipped
    if [ "$SKIP_PULL" = false ]; then
        pull_image
    else
        print_warning "Skipping image pull as requested"
    fi
    
    # Use provided input file or default
    if [ -z "$INPUT_FILE" ]; then
        INPUT_FILE="$DEFAULT_INPUT"
    fi
    
    # Run PharmCAT
    run_pharmcat "$INPUT_FILE"
    
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
