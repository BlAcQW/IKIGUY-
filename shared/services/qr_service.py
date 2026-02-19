"""
Enhanced QR Code Generation Service for KasaAI

This module provides comprehensive QR code generation capabilities including:
- Custom name/text display on QR codes
- Brand color customization (background and foreground)
- Logo embedding in center of QR code
- High-resolution QR code generation (PNG)
- Data URL generation for web display
- Multiple logo support with positioning

Usage:
    from apps.shared.services.qr_service import QRCodeService, QRCodeConfig, LogoConfig

    # Basic usage
    service = QRCodeService()
    qr_bytes = await service.generate_qr_code(
        url="https://ailabsafrica.com",
        config=QRCodeConfig(
            name="My QR Code",
            fill_color="#000000",
            back_color="#FFFFFF"
        )
    )

    # With logo
    logo_config = LogoConfig(
        logo_data=logo_bytes,
        size_ratio=0.3,
        border_radius=10
    )
    qr_bytes = await service.generate_qr_code_with_logo(
        url="https://ailabsafrica.com",
        config=QRCodeConfig(name="Branded QR"),
        logo_config=logo_config
    )

Dependencies:
    pip install qrcode[pil] pillow

Author: KasaAI Team
Date: 2025-11-09
"""

import asyncio
import base64
import io
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import qrcode
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class ErrorCorrectionLevel(str, Enum):
    """QR code error correction levels."""

    LOW = "L"  # ~7% error correction
    MEDIUM = "M"  # ~15% error correction (default)
    QUARTILE = "Q"  # ~25% error correction
    HIGH = "H"  # ~30% error correction (best for logos)


class QRCodeFormat(str, Enum):
    """Output format for QR code."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    SVG = "svg"


class LogoConfig(BaseModel):
    """Configuration for logo embedding in QR code."""

    logo_data: Optional[bytes] = None  # Logo image bytes
    logo_path: Optional[str] = None  # Path to logo file
    size_ratio: float = Field(default=0.3, ge=0.1, le=0.5)  # Logo size relative to QR code
    border_width: int = Field(default=10, ge=0)  # White border around logo
    border_radius: int = Field(default=0, ge=0)  # Rounded corners for logo

    @validator('size_ratio')
    def validate_size_ratio(cls, v):
        """Ensure size ratio is reasonable."""
        if v < 0.1 or v > 0.5:
            raise ValueError("Logo size ratio must be between 0.1 and 0.5")
        return v


class QRCodeConfig(BaseModel):
    """Configuration for QR code generation."""

    name: str = Field(default="QR Code", description="Display name for the QR code")
    fill_color: str = Field(default="#000000", description="Foreground color (hex)")
    back_color: str = Field(default="#FFFFFF", description="Background color (hex)")
    box_size: int = Field(default=10, ge=1, le=50, description="Size of each box in pixels")
    border: int = Field(default=4, ge=0, le=10, description="Border size in boxes")
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.HIGH
    image_format: QRCodeFormat = QRCodeFormat.PNG
    size: int = Field(default=500, ge=100, le=2000, description="Output image size in pixels")

    @validator('fill_color', 'back_color')
    def validate_hex_color(cls, v):
        """Validate hex color format."""
        if not v.startswith('#'):
            raise ValueError("Color must be in hex format (e.g., #000000)")
        if len(v) not in [4, 7]:  # #RGB or #RRGGBB
            raise ValueError("Invalid hex color format")
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError("Invalid hex color value")
        return v.upper()


class QRCodeMetadata(BaseModel):
    """Metadata for generated QR code."""

    name: str
    url: str
    fill_color: str
    back_color: str
    has_logo: bool = False
    size: int
    format: QRCodeFormat
    file_size: int  # bytes
    created_at: str


class QRCodeResult(BaseModel):
    """Result of QR code generation."""

    image_data: bytes
    data_url: str  # Base64 data URL for web display
    metadata: QRCodeMetadata

    @property
    def size_kb(self) -> float:
        """Get file size in KB."""
        return self.metadata.file_size / 1024


class QRCodeService:
    """
    Comprehensive QR code generation service.

    Supports custom branding, logo embedding, and various output formats.
    """

    def __init__(
        self,
        default_config: Optional[QRCodeConfig] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize QR code service.

        Args:
            default_config: Default configuration for QR code generation
            cache_enabled: Whether to cache generated QR codes
        """
        self.default_config = default_config or QRCodeConfig()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, bytes] = {}

    def _get_cache_key(
        self,
        url: str,
        config: QRCodeConfig,
        logo_config: Optional[LogoConfig] = None
    ) -> str:
        """
        Generate cache key for QR code.

        Args:
            url: URL to encode
            config: QR code configuration
            logo_config: Optional logo configuration

        Returns:
            Cache key string
        """
        # Reason: Create unique cache key based on all configuration parameters
        key_parts = [
            url,
            config.fill_color,
            config.back_color,
            str(config.box_size),
            str(config.border),
            config.error_correction.value,
            str(config.size)
        ]

        if logo_config:
            key_parts.extend([
                str(logo_config.size_ratio),
                str(logo_config.border_width),
                str(logo_config.border_radius)
            ])

        return "|".join(key_parts)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., #FFFFFF)

        Returns:
            RGB tuple
        """
        hex_color = hex_color.lstrip('#')

        # Handle short format #RGB
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    async def _load_logo(self, logo_config: LogoConfig) -> Image.Image:
        """
        Load logo image from config.

        Args:
            logo_config: Logo configuration

        Returns:
            PIL Image object

        Raises:
            ValueError: If neither logo_data nor logo_path is provided
        """
        def load_image():
            if logo_config.logo_data:
                return Image.open(io.BytesIO(logo_config.logo_data))
            elif logo_config.logo_path:
                return Image.open(logo_config.logo_path)
            else:
                raise ValueError("Either logo_data or logo_path must be provided")

        return await asyncio.to_thread(load_image)

    def _add_rounded_corners(
        self,
        image: Image.Image,
        radius: int
    ) -> Image.Image:
        """
        Add rounded corners to image.

        Args:
            image: Input image
            radius: Corner radius in pixels

        Returns:
            Image with rounded corners
        """
        # Create circular mask
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            [(0, 0), image.size],
            radius=radius,
            fill=255
        )

        # Apply mask to image
        rounded = Image.new('RGBA', image.size, (255, 255, 255, 0))
        rounded.paste(image, (0, 0))
        rounded.putalpha(mask)

        return rounded

    async def _embed_logo(
        self,
        qr_image: Image.Image,
        logo_config: LogoConfig
    ) -> Image.Image:
        """
        Embed logo in center of QR code.

        Args:
            qr_image: Generated QR code image
            logo_config: Logo configuration

        Returns:
            QR code with embedded logo
        """
        # Load logo
        logo = await self._load_logo(logo_config)

        # Convert to RGBA if needed
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')

        # Calculate logo size
        qr_width, qr_height = qr_image.size
        logo_max_size = int(min(qr_width, qr_height) * logo_config.size_ratio)

        # Resize logo maintaining aspect ratio
        logo.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)

        # Add white border around logo
        if logo_config.border_width > 0:
            border_size = logo_config.border_width
            new_size = (
                logo.width + border_size * 2,
                logo.height + border_size * 2
            )
            bordered_logo = Image.new('RGBA', new_size, (255, 255, 255, 255))
            bordered_logo.paste(
                logo,
                (border_size, border_size),
                logo
            )
            logo = bordered_logo

        # Add rounded corners if requested
        if logo_config.border_radius > 0:
            logo = self._add_rounded_corners(logo, logo_config.border_radius)

        # Calculate position to center logo
        logo_x = (qr_width - logo.width) // 2
        logo_y = (qr_height - logo.height) // 2

        # Convert QR code to RGBA for transparency support
        if qr_image.mode != 'RGBA':
            qr_image = qr_image.convert('RGBA')

        # Paste logo onto QR code
        qr_image.paste(logo, (logo_x, logo_y), logo)

        return qr_image

    async def generate_qr_code(
        self,
        url: str,
        config: Optional[QRCodeConfig] = None
    ) -> QRCodeResult:
        """
        Generate QR code without logo.

        Args:
            url: URL to encode in QR code
            config: Optional configuration (uses default if not provided)

        Returns:
            QRCodeResult with generated image and metadata
        """
        config = config or self.default_config

        # Check cache
        cache_key = self._get_cache_key(url, config)
        if self.cache_enabled and cache_key in self._cache:
            logger.info(f"Returning cached QR code for: {url[:50]}...")
            image_data = self._cache[cache_key]
        else:
            # Generate QR code
            def generate():
                qr = qrcode.QRCode(
                    version=None,  # Auto-detect version
                    error_correction=getattr(
                        qrcode.constants,
                        f'ERROR_CORRECT_{config.error_correction.value}'
                    ),
                    box_size=config.box_size,
                    border=config.border,
                )

                qr.add_data(url)
                qr.make(fit=True)

                # Create image
                img = qr.make_image(
                    fill_color=self._hex_to_rgb(config.fill_color),
                    back_color=self._hex_to_rgb(config.back_color)
                )

                # Resize to target size
                img = img.resize((config.size, config.size), Image.Resampling.LANCZOS)

                return img

            img = await asyncio.to_thread(generate)

            # Convert to bytes
            output = io.BytesIO()
            img.save(output, format=config.image_format.value.upper())
            image_data = output.getvalue()

            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = image_data

        # Create data URL
        mime_type = f"image/{config.image_format.value}"
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_data).decode()}"

        # Create metadata
        from datetime import datetime, timezone
        metadata = QRCodeMetadata(
            name=config.name,
            url=url,
            fill_color=config.fill_color,
            back_color=config.back_color,
            has_logo=False,
            size=config.size,
            format=config.image_format,
            file_size=len(image_data),
            created_at=datetime.now(timezone.utc).isoformat()
        )

        return QRCodeResult(
            image_data=image_data,
            data_url=data_url,
            metadata=metadata
        )

    async def generate_qr_code_with_logo(
        self,
        url: str,
        config: Optional[QRCodeConfig] = None,
        logo_config: Optional[LogoConfig] = None
    ) -> QRCodeResult:
        """
        Generate QR code with embedded logo.

        Args:
            url: URL to encode in QR code
            config: Optional QR code configuration
            logo_config: Logo configuration

        Returns:
            QRCodeResult with generated image and metadata

        Raises:
            ValueError: If logo_config is not provided
        """
        if not logo_config:
            raise ValueError("logo_config is required for logo embedding")

        config = config or self.default_config

        # Check cache
        cache_key = self._get_cache_key(url, config, logo_config)
        if self.cache_enabled and cache_key in self._cache:
            logger.info(f"Returning cached QR code with logo for: {url[:50]}...")
            image_data = self._cache[cache_key]
        else:
            # Generate base QR code
            result = await self.generate_qr_code(url, config)

            # Load QR image
            qr_image = Image.open(io.BytesIO(result.image_data))

            # Embed logo
            qr_image = await self._embed_logo(qr_image, logo_config)

            # Convert to bytes
            output = io.BytesIO()
            qr_image.save(output, format=config.image_format.value.upper())
            image_data = output.getvalue()

            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = image_data

        # Create data URL
        mime_type = f"image/{config.image_format.value}"
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_data).decode()}"

        # Create metadata
        from datetime import datetime, timezone
        metadata = QRCodeMetadata(
            name=config.name,
            url=url,
            fill_color=config.fill_color,
            back_color=config.back_color,
            has_logo=True,
            size=config.size,
            format=config.image_format,
            file_size=len(image_data),
            created_at=datetime.now(timezone.utc).isoformat()
        )

        return QRCodeResult(
            image_data=image_data,
            data_url=data_url,
            metadata=metadata
        )

    def clear_cache(self):
        """Clear the QR code cache."""
        self._cache.clear()
        logger.info("QR code cache cleared")

    async def save_qr_code(
        self,
        result: QRCodeResult,
        file_path: Union[str, Path]
    ):
        """
        Save QR code to file.

        Args:
            result: QR code generation result
            file_path: Path to save file
        """
        def save():
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(result.image_data)

        await asyncio.to_thread(save)
        logger.info(f"QR code saved to: {file_path}")
