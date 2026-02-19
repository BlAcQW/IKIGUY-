#!/bin/bash

###############################################################################
# Docker Cleanup Script
# Removes dangling images and unused containers to free up disk space
#
# Usage: ./cleanup-docker.sh [--aggressive]
# Options:
#   --aggressive: Also removes unused volumes and networks
###############################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

AGGRESSIVE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --aggressive)
            AGGRESSIVE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--aggressive]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Docker Cleanup Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check disk space before
echo -e "\n${BLUE}Disk space before cleanup:${NC}"
df -h /var/lib/docker 2>/dev/null || df -h /

# Remove dangling images
echo -e "\n${YELLOW}Removing dangling Docker images...${NC}"
docker image prune -f

# Remove stopped containers
echo -e "\n${YELLOW}Removing stopped containers...${NC}"
docker container prune -f

if [ "$AGGRESSIVE" = true ]; then
    echo -e "\n${YELLOW}Running aggressive cleanup...${NC}"

    # Remove unused volumes
    echo -e "\n${YELLOW}Removing unused volumes...${NC}"
    docker volume prune -f

    # Remove unused networks
    echo -e "\n${YELLOW}Removing unused networks...${NC}"
    docker network prune -f

    # Remove all unused images (not just dangling)
    echo -e "\n${YELLOW}Removing all unused images...${NC}"
    docker image prune -a -f
fi

# Check disk space after
echo -e "\n${BLUE}Disk space after cleanup:${NC}"
df -h /var/lib/docker 2>/dev/null || df -h /

echo -e "\n${GREEN}✓ Docker cleanup completed!${NC}"
