"""
Setup script for KasaAI Shared Libraries
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kasaai-shared",
    version="1.0.0",
    author="KasaAI Team",
    author_email="team@kasaai.com",
    description="Shared libraries and interfaces for KasaAI components",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kasaai/shared",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "asyncio-mqtt>=0.11.0",
        "redis>=4.0.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.28.0",
        "psycopg2-binary>=2.9.0",
        "aiofiles>=23.0.0",
        "httpx>=0.24.0",
        "cryptography>=41.0.0",
        "dataclasses-json>=0.6.0",
        "aiohttp>=3.8.0",
        "numpy>=1.21.0",
        "websockets>=11.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
        "voice": [
            "fastrtc[vad,tts]>=0.1.0",  # WebRTC for voice conversations
        ],
    },
    entry_points={
        "console_scripts": [
            "kasaai-shared=kasaai_shared.cli:main",
        ],
    },
)
