"""
Image Receipt Service - Extract structured data from receipt images.

This service handles OCR and data extraction from receipt photos (JPEG, PNG, HEIC)
taken on mobile devices. It uses Tesseract OCR and optional AI (Gemini) for
accurate data extraction.

Usage:
    service = get_image_receipt_service(use_ocr=True)
    expense_data = await service.extract_from_image(image_file)

    # With AI extraction
    expense_data = await service.extract_from_image(
        image_file,
        use_ai=True,
        llm_provider="gemini"
    )

Author: AI Labs Africa Platform Team
Date: 2025-11-03
Version: 1.0.0
"""

import io
import logging
from typing import BinaryIO, Dict, Any, Optional
from PIL import Image
import pytesseract

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Image preprocessing will be limited.")

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False
    logging.warning("pillow-heif not available. HEIC images will not be supported.")

from apps.shared.services.pdf_extraction_service import (
    ExpenseData,
    PDFExtractionService,
    get_pdf_extraction_service
)

logger = logging.getLogger(__name__)


class ImageReceiptService:
    """
    Service for extracting structured data from receipt images.

    Features:
    - Extract text from JPEG, PNG, HEIC images
    - Image preprocessing (rotation, contrast, denoising)
    - OCR using Tesseract
    - Pattern matching or AI extraction (Gemini)
    - Reuses extraction logic from PDF service
    """

    def __init__(self, use_ocr: bool = True, tesseract_lang: str = "eng"):
        """
        Initialize image receipt service.

        Args:
            use_ocr: Whether to use OCR (always True for images)
            tesseract_lang: Language for OCR (default: English)
        """
        self.use_ocr = use_ocr
        self.tesseract_lang = tesseract_lang
        self.pdf_service = get_pdf_extraction_service(use_ocr=use_ocr)

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.

        Steps:
        1. Auto-rotate based on EXIF data
        2. Convert to grayscale
        3. Increase contrast
        4. Denoise
        5. Binarize (black & white)

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Auto-rotate based on EXIF orientation
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            except Exception as e:
                logger.warning(f"Failed to auto-rotate image: {e}")

            # If OpenCV available, use advanced preprocessing
            if CV2_AVAILABLE:
                # Convert PIL to OpenCV format
                img_array = np.array(image)

                # Convert to grayscale if needed
                if len(img_array.shape) == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array

                # Increase contrast using CLAHE
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

                # Denoise
                gray = cv2.fastNlMeansDenoising(gray, h=10)

                # Adaptive thresholding (binarization)
                binary = cv2.adaptiveThreshold(
                    gray,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )

                # Convert back to PIL
                image = Image.fromarray(binary)
            else:
                # Basic preprocessing without OpenCV
                from PIL import ImageEnhance, ImageFilter

                # Convert to grayscale
                if image.mode != 'L':
                    image = image.convert('L')

                # Increase contrast
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)

                # Sharpen
                image = image.filter(ImageFilter.SHARPEN)

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return image

    def extract_text_from_image(self, image_file: BinaryIO) -> str:
        """
        Extract raw text from image using OCR.

        Args:
            image_file: Binary image file (JPEG, PNG, HEIC)

        Returns:
            Extracted text as string

        Raises:
            ValueError: If image format is not supported
            RuntimeError: If OCR fails
        """
        try:
            # Load image
            image = Image.open(image_file)

            # Validate image
            if image.format not in ['JPEG', 'PNG', 'HEIF']:
                if not HEIF_AVAILABLE and image.format == 'HEIF':
                    raise ValueError(
                        "HEIC format not supported. Install pillow-heif: "
                        "pip install pillow-heif"
                    )
                # Try to process anyway
                logger.warning(f"Unexpected image format: {image.format}")

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Extract text using Tesseract
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.tesseract_lang,
                config='--psm 6'  # Assume uniform block of text
            )

            if not text or len(text.strip()) < 10:
                logger.warning("Very little text extracted from image. Image may be poor quality.")

            return text

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            raise RuntimeError(f"OCR extraction failed: {str(e)}")

    async def extract_from_image(
        self,
        image_file: BinaryIO,
        use_ai: bool = False,
        llm_provider: Optional[str] = None
    ) -> ExpenseData:
        """
        Extract structured expense data from receipt image.

        This method:
        1. Extracts text using OCR
        2. Extracts structured data using pattern matching or AI
        3. Returns ExpenseData object

        Args:
            image_file: Binary image file (JPEG, PNG, HEIC)
            use_ai: Whether to use AI (Gemini) for extraction
            llm_provider: LLM provider to use (default: gemini)

        Returns:
            ExpenseData object with extracted fields

        Example:
            ```python
            service = get_image_receipt_service()
            with open("receipt.jpg", "rb") as f:
                data = await service.extract_from_image(f, use_ai=True)
            print(f"Merchant: {data.merchant}, Amount: {data.amount}")
            ```
        """
        try:
            # Extract text from image
            raw_text = self.extract_text_from_image(image_file)

            if not raw_text or len(raw_text.strip()) < 10:
                logger.warning("Insufficient text extracted from image")
                return ExpenseData(
                    raw_text=raw_text,
                    confidence=0.1,
                    extraction_source="image_ocr"
                )

            # Use PDF service's extraction logic (reuse patterns and AI)
            if use_ai and llm_provider:
                expense_data = await self.pdf_service._extract_with_ai(
                    raw_text,
                    llm_provider
                )
            else:
                expense_data = self.pdf_service._extract_with_patterns(raw_text)

            # Add extraction source metadata
            expense_data.raw_text = raw_text
            if not hasattr(expense_data, 'extraction_source'):
                expense_data.extraction_source = "image_ocr_ai" if use_ai else "image_ocr_pattern"

            return expense_data

        except Exception as e:
            logger.error(f"Failed to extract data from image: {e}")
            # Return empty data with low confidence
            return ExpenseData(
                raw_text="",
                confidence=0.0,
                extraction_source="image_ocr_failed"
            )

    def validate_image(
        self,
        image_file: BinaryIO,
        max_size_mb: int = 10,
        min_size_kb: int = 10
    ) -> tuple[bool, Optional[str]]:
        """
        Validate image file for receipt processing.

        Args:
            image_file: Binary image file
            max_size_mb: Maximum file size in MB
            min_size_kb: Minimum file size in KB

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            image_file.seek(0, 2)  # Seek to end
            size_bytes = image_file.tell()
            image_file.seek(0)  # Reset to beginning

            size_mb = size_bytes / (1024 * 1024)
            size_kb = size_bytes / 1024

            if size_mb > max_size_mb:
                return False, f"Image too large ({size_mb:.1f}MB). Max: {max_size_mb}MB"

            if size_kb < min_size_kb:
                return False, f"Image too small ({size_kb:.1f}KB). Min: {min_size_kb}KB"

            # Try to open image
            try:
                image = Image.open(image_file)
                image_file.seek(0)  # Reset
            except Exception as e:
                return False, f"Invalid image file: {str(e)}"

            # Check dimensions
            width, height = image.size
            if width < 200 or height < 200:
                return False, f"Image resolution too low ({width}x{height}). Min: 200x200"

            if width > 6000 or height > 6000:
                return False, f"Image resolution too high ({width}x{height}). Max: 6000x6000"

            return True, None

        except Exception as e:
            return False, f"Image validation failed: {str(e)}"


def get_image_receipt_service(
    use_ocr: bool = True,
    tesseract_lang: str = "eng"
) -> ImageReceiptService:
    """
    Factory function to get image receipt service instance.

    Args:
        use_ocr: Whether to use OCR (always True for images)
        tesseract_lang: Language for OCR (default: English)

    Returns:
        ImageReceiptService instance

    Example:
        ```python
        service = get_image_receipt_service()
        with open("receipt.jpg", "rb") as f:
            data = await service.extract_from_image(f)
        ```
    """
    return ImageReceiptService(use_ocr=use_ocr, tesseract_lang=tesseract_lang)
