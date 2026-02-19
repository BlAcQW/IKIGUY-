# Use official Crawl4AI image
FROM unclecode/crawl4ai:latest

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:11235/health || exit 1

# Use the default command from base image (don't override)
