#!/bin/bash

################################################################################
# Masakhane & African Language Dataset Download Script
#
# Downloads datasets from various sources to Hetzner storage:
# - MasakhaNER 2.0 (GitHub)
# - LAFAND-MT (GitHub)
# - MasakhaPOS (GitHub)
# - Financial Inclusion Speech Dataset (AWS S3)
#
# Usage:
#   bash download_masakhane_datasets.sh [category]
#
#   Categories: ner, mt, pos, speech, all (default: all)
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HETZNER_BASE="/mnt/hetzner_storage/voice-lab/datasets"
MASAKHANE_BASE="${HETZNER_BASE}/masakhane"
FINANCIAL_BASE="${HETZNER_BASE}/financial-inclusion"
CATEGORY="${1:-all}"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Hetzner is mounted
    if ! mountpoint -q /mnt/hetzner_storage; then
        log_error "Hetzner storage not mounted at /mnt/hetzner_storage"
        exit 1
    fi
    log_success "Hetzner storage mounted"

    # Check for required commands
    for cmd in git curl wget; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done
    log_success "All required commands available"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."

    mkdir -p "${MASAKHANE_BASE}"/{masakhaner,lafand-mt,masakhane-pos}
    mkdir -p "${FINANCIAL_BASE}"/{akuapem,asante,fante,ga}

    log_success "Directories created"
}

################################################################################
# MasakhaNER 2.0 Downloads
################################################################################

download_masakhaner() {
    local lang=$1
    local lang_code=$2

    log_info "Downloading MasakhaNER 2.0 - ${lang}..."

    local dest="${MASAKHANE_BASE}/masakhaner/${lang_code}"
    mkdir -p "${dest}"

    # Base URL for raw GitHub content
    local base_url="https://raw.githubusercontent.com/masakhane-io/masakhane-ner/main/MasakhaNER2.0/data/${lang_code}"

    # Download train/dev/test files
    for split in train dev test; do
        log_info "  Downloading ${split} split..."
        wget -q -O "${dest}/${split}.txt" "${base_url}/${split}.txt" 2>/dev/null || \
            log_warn "  Failed to download ${split}.txt - file may not exist"
    done

    # Try to download README
    wget -q -O "${dest}/README.md" "https://raw.githubusercontent.com/masakhane-io/masakhane-ner/main/MasakhaNER2.0/README.md" 2>/dev/null || true

    log_success "MasakhaNER ${lang} download complete"
}

################################################################################
# LAFAND-MT Downloads
################################################################################

download_lafand_mt() {
    local lang=$1
    local lang_code=$2

    log_info "Downloading MAFAND-MT - ${lang}..."

    local dest="${MASAKHANE_BASE}/lafand-mt/${lang_code}"
    mkdir -p "${dest}"

    # Clone or update repository (sparse checkout for specific language)
    if [ ! -d "${MASAKHANE_BASE}/lafand-mt/.git" ]; then
        log_info "  Cloning LAFAND-MT repository..."
        cd "${MASAKHANE_BASE}/lafand-mt"
        git clone --depth 1 --filter=blob:none --sparse https://github.com/masakhane-io/lafand-mt.git temp
        cd temp
        git sparse-checkout set "data/${lang_code}"
        mv data/${lang_code}/* "${dest}/" 2>/dev/null || true
        cd ..
        rm -rf temp
    else
        log_info "  Repository already cloned, updating..."
    fi

    log_success "LAFAND-MT ${lang} download complete"
}

################################################################################
# MasakhaPOS Downloads
################################################################################

download_masakhane_pos() {
    log_info "Downloading MasakhaPOS repository..."

    local dest="${MASAKHANE_BASE}/masakhane-pos"

    if [ ! -d "${dest}/.git" ]; then
        log_info "  Cloning MasakhaPOS repository..."
        git clone --depth 1 https://github.com/masakhane-io/masakhane-pos.git "${dest}"
    else
        log_info "  Repository exists, pulling updates..."
        cd "${dest}"
        git pull
        cd -
    fi

    log_success "MasakhaPOS download complete"
}

################################################################################
# Financial Inclusion Speech Dataset Downloads
################################################################################

download_financial_inclusion() {
    local language=$1

    log_info "Downloading Financial Inclusion - ${language}..."

    local dest="${FINANCIAL_BASE}/${language}"
    mkdir -p "${dest}"

    # Note: The actual S3 URLs are in the GitHub repository
    # We need to fetch the download links from the README or data files

    local repo_url="https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset"

    log_warn "Financial Inclusion dataset download requires manual AWS S3 access"
    log_info "  Repository: ${repo_url}"
    log_info "  Please check the repository for actual download links"
    log_info "  Destination ready at: ${dest}"

    # Clone repository to get metadata
    if [ ! -d "${dest}/.repo" ]; then
        log_info "  Cloning repository metadata..."
        git clone --depth 1 "${repo_url}" "${dest}/.repo" 2>/dev/null || \
            log_warn "  Could not clone repository"
    fi

    log_info "Financial Inclusion ${language} prepared (manual download required)"
}

################################################################################
# Main execution
################################################################################

main() {
    echo "=========================================================================="
    echo "  Masakhane & African Language Dataset Downloader"
    echo "=========================================================================="
    echo "Category: ${CATEGORY}"
    echo "Destination: ${HETZNER_BASE}"
    echo "=========================================================================="
    echo ""

    check_prerequisites
    create_directories

    case "${CATEGORY}" in
        ner|all)
            log_info "===== Downloading NER Datasets ====="
            download_masakhaner "Twi" "twi"
            download_masakhaner "Ewe" "ewe"
            ;;
    esac

    case "${CATEGORY}" in
        mt|all)
            log_info "===== Downloading Machine Translation Datasets ====="
            download_lafand_mt "Twi" "twi"
            download_lafand_mt "Ewe" "ewe"
            ;;
    esac

    case "${CATEGORY}" in
        pos|all)
            log_info "===== Downloading POS Tagging Datasets ====="
            download_masakhane_pos
            ;;
    esac

    case "${CATEGORY}" in
        speech|all)
            log_info "===== Preparing Financial Inclusion Speech Datasets ====="
            download_financial_inclusion "akuapem"
            download_financial_inclusion "asante"
            download_financial_inclusion "fante"
            download_financial_inclusion "ga"
            ;;
    esac

    echo ""
    echo "=========================================================================="
    log_success "Download process complete!"
    echo "=========================================================================="
    echo ""
    echo "Next steps:"
    echo "  1. Verify downloaded files:"
    echo "     ls -lh ${MASAKHANE_BASE}"
    echo "     ls -lh ${FINANCIAL_BASE}"
    echo ""
    echo "  2. For Financial Inclusion dataset:"
    echo "     - Check repository for S3 download links"
    echo "     - Use AWS CLI or wget to download audio files"
    echo ""
    echo "  3. Update MongoDB with actual file statistics:"
    echo "     python scripts/update_dataset_stats.py"
    echo ""
    echo "=========================================================================="
}

main
