"""
PDF Extraction Service.

Extract structured data from expense receipts and invoices using multiple extraction methods:
- Text-based extraction (PDFPlumber)
- OCR for scanned documents (Tesseract/pytesseract)
- Pattern matching for common receipt formats
- AI-powered extraction (optional, using LLMs)

This service is designed to extract common expense fields:
- Merchant/Vendor name
- Date
- Total amount
- Tax amount
- Items/Line items
- Payment method
- Receipt number
"""

import logging
import re
from typing import Optional, Dict, Any, List, BinaryIO, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import io

# PDF extraction libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logging.warning("pdfplumber not installed. Install with: pip install pdfplumber")

# OCR library
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract/PIL not installed. Install with: pip install pytesseract Pillow pdf2image")


logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Base exception for PDF extraction errors."""
    pass


class ExpenseData:
    """
    Structured expense data extracted from receipts/invoices.

    Attributes:
        merchant: Merchant/vendor name
        date: Transaction date
        amount: Total amount
        tax_amount: Tax amount (if found)
        currency: Currency code (e.g., USD, GHS)
        category: Inferred category (e.g., "restaurant", "office_supplies")
        items: List of line items (if found)
        payment_method: Payment method (if found)
        receipt_number: Receipt/invoice number
        raw_text: Raw extracted text
        confidence: Extraction confidence score (0.0-1.0)
    """

    def __init__(
        self,
        merchant: Optional[str] = None,
        date: Optional[date] = None,
        amount: Optional[Decimal] = None,
        tax_amount: Optional[Decimal] = None,
        currency: str = "USD",
        category: Optional[str] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        payment_method: Optional[str] = None,
        receipt_number: Optional[str] = None,
        raw_text: Optional[str] = None,
        confidence: float = 0.0
    ):
        """Initialize expense data."""
        self.merchant = merchant
        self.date = date
        self.amount = amount
        self.tax_amount = tax_amount
        self.currency = currency
        self.category = category
        self.items = items or []
        self.payment_method = payment_method
        self.receipt_number = receipt_number
        self.raw_text = raw_text
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "merchant": self.merchant,
            "date": self.date.isoformat() if self.date else None,
            "amount": float(self.amount) if self.amount else None,
            "tax_amount": float(self.tax_amount) if self.tax_amount else None,
            "currency": self.currency,
            "category": self.category,
            "items": self.items,
            "payment_method": self.payment_method,
            "receipt_number": self.receipt_number,
            "raw_text": self.raw_text,
            "confidence": self.confidence
        }


class PDFExtractionService:
    """
    Service for extracting structured data from expense receipts and invoices.

    Supports multiple extraction methods:
    1. Text-based extraction (for digital PDFs)
    2. OCR extraction (for scanned receipts)
    3. Pattern matching for common formats
    4. AI-powered extraction (optional)
    """

    # Common date patterns in receipts
    DATE_PATTERNS = [
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",  # MM/DD/YYYY or DD/MM/YYYY
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",    # YYYY-MM-DD
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2}),? (\d{4})\b",  # Month DD, YYYY
        r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b"   # DD Month YYYY
    ]

    # Common amount patterns (note: these match against lowercase text)
    AMOUNT_PATTERNS = [
        # Match "grand total" first (most specific)
        r"grand total[:\s]*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        # Match "balance due" / "amount due"
        r"balance due[:\s]*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        r"amount due[:\s]*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        # Match "total" with word boundary (avoid matching "subtotal")
        r"\btotal\b[:\s]*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        # Match "amount"
        r"\bamount\b[:\s]*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        # Last dollar amount on a line (lowest priority)
        r"\$([0-9,]+\.\d{2})\s*$",
    ]

    # Tax patterns (note: these match against lowercase text)
    TAX_PATTERNS = [
        # Match "vat at 19.00% usd 5.05", "tax: $10.50", etc.
        r"tax[:\s]*(?:at\s+[\d.]+%)?\s*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        r"vat[:\s]*(?:at\s+[\d.]+%)?\s*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        r"gst[:\s]*(?:at\s+[\d.]+%)?\s*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
        r"sales tax[:\s]*(?:at\s+[\d.]+%)?\s*(?:usd|eur|gbp|ghs|ngn|zar|kes|cad|aud)?\s*\$?([0-9,]+\.?\d{0,2})",
    ]

    # Currency symbols to codes
    CURRENCY_MAP = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "₵": "GHS",
        "¢": "GHS",
        "₦": "NGN",
        "R": "ZAR",
    }

    # Category keywords
    CATEGORY_KEYWORDS = {
        "restaurant": ["restaurant", "cafe", "coffee", "food", "dining", "pizza", "burger"],
        "travel": ["uber", "lyft", "taxi", "airline", "hotel", "airbnb", "flight"],
        "office_supplies": ["office", "staples", "pen", "paper", "printer"],
        "utilities": ["electric", "water", "gas", "internet", "phone"],
        "software": ["software", "saas", "subscription", "cloud", "hosting"],
        "rent": ["rent", "lease"],
        "marketing": ["advertising", "ads", "marketing", "facebook", "google ads"],
    }

    def __init__(self, use_ocr: bool = True, ocr_language: str = "eng"):
        """
        Initialize PDF extraction service.

        Args:
            use_ocr: Enable OCR for scanned documents
            ocr_language: Tesseract language code (e.g., 'eng', 'fra')
        """
        self.use_ocr = use_ocr and TESSERACT_AVAILABLE
        self.ocr_language = ocr_language

        if not PDFPLUMBER_AVAILABLE:
            raise PDFExtractionError(
                "pdfplumber is required. Install with: pip install pdfplumber"
            )

    async def extract_from_pdf(
        self,
        pdf_file: BinaryIO,
        use_ai: bool = False,
        llm_provider: Optional[str] = None
    ) -> ExpenseData:
        """
        Extract expense data from PDF file.

        Args:
            pdf_file: PDF file object or bytes
            use_ai: Use AI/LLM for extraction (more accurate but slower and costs money)
            llm_provider: LLM provider ID for AI extraction

        Returns:
            ExpenseData object with extracted fields

        Raises:
            PDFExtractionError: If extraction fails
        """
        try:
            # Extract text from PDF
            raw_text = self._extract_text_from_pdf(pdf_file)

            # If text extraction failed or yielded very little text, try OCR
            if not raw_text or len(raw_text.strip()) < 50:
                if self.use_ocr:
                    logger.info("Text extraction yielded little data, trying OCR...")
                    raw_text = self._extract_text_with_ocr(pdf_file)
                else:
                    raise PDFExtractionError(
                        "Failed to extract text from PDF. Try enabling OCR."
                    )

            # Use AI extraction if requested
            if use_ai and llm_provider:
                return await self._extract_with_ai(raw_text, llm_provider)

            # Use pattern matching extraction
            return self._extract_with_patterns(raw_text)

        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise PDFExtractionError(f"Failed to extract data from PDF: {str(e)}")

    def _extract_text_from_pdf(self, pdf_file: BinaryIO) -> str:
        """
        Extract text from PDF using pdfplumber.

        Args:
            pdf_file: PDF file object

        Returns:
            Extracted text
        """
        try:
            # Reset file pointer
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            text_parts = []
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""

    def _extract_text_with_ocr(self, pdf_file: BinaryIO) -> str:
        """
        Extract text from PDF using OCR (for scanned documents).

        Args:
            pdf_file: PDF file object

        Returns:
            Extracted text
        """
        if not TESSERACT_AVAILABLE:
            raise PDFExtractionError(
                "Tesseract OCR not available. Install with: pip install pytesseract Pillow pdf2image"
            )

        try:
            # Reset file pointer
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)

            # Convert PDF pages to images
            images = pdf2image.convert_from_bytes(pdf_file.read())

            # OCR each page
            text_parts = []
            for image in images:
                text = pytesseract.image_to_string(image, lang=self.ocr_language)
                text_parts.append(text)

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return ""

    def _extract_with_patterns(self, text: str) -> ExpenseData:
        """
        Extract expense data using pattern matching.

        Args:
            text: Raw text from PDF

        Returns:
            ExpenseData object
        """
        # Initialize expense data
        expense_data = ExpenseData(raw_text=text)

        # Extract fields
        expense_data.merchant = self._extract_merchant(text)
        expense_data.date = self._extract_date(text)
        expense_data.amount = self._extract_amount(text)
        expense_data.tax_amount = self._extract_tax(text)
        expense_data.currency = self._extract_currency(text)
        expense_data.category = self._infer_category(text)
        expense_data.payment_method = self._extract_payment_method(text)
        expense_data.receipt_number = self._extract_receipt_number(text)

        # Calculate confidence score
        expense_data.confidence = self._calculate_confidence(expense_data)

        return expense_data

    def _extract_merchant(self, text: str) -> Optional[str]:
        """Extract merchant name from text (usually first line or after 'from')."""
        lines = text.split('\n')

        # Skip words that indicate this line is not a merchant name
        skip_words = [
            'receipt', 'invoice', 'tax', 'total', 'date', 'from:',
            'to:', 'attention', 'payment', 'amount', 'description', 'qty',
            'quantity', 'price', 'subtotal', 'number', 'issued'
        ]

        # Separator words/phrases that might appear on same line as merchant
        separators = ['bill to', 'ship to', 'sold to', 'email:', 'phone:', 'fax:']

        # Try to find merchant name in first few lines
        for line in lines[:10]:  # Extended to check more lines
            line = line.strip()
            if line and len(line) > 2 and len(line) < 150:
                line_lower = line.lower()

                # Check if line contains separators - extract merchant part before separator
                for separator in separators:
                    if separator in line_lower:
                        # Find separator position in lowercase, then extract from original line
                        sep_pos = line_lower.find(separator)
                        parts = line[:sep_pos].strip()
                        if parts and len(parts) > 2 and any(c.isalpha() for c in parts):
                            # Make sure this part doesn't contain skip words
                            if not any(word in parts.lower() for word in skip_words):
                                return parts
                        # Continue to next line if extracted part isn't valid
                        break
                else:
                    # No separator found, check if line should be skipped entirely
                    if not any(word in line_lower for word in skip_words):
                        # Prefer lines that look like company names (not just numbers/special chars)
                        if any(c.isalpha() for c in line):
                            return line

        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract transaction date using pattern matching."""
        text_lower = text.lower()

        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return self._parse_date(match.group(0))
                except:
                    continue

        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        # Common date formats
        formats = [
            "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d",
            "%m-%d-%Y", "%d-%m-%Y",
            "%B %d, %Y", "%b %d, %Y",
            "%d %B %Y", "%d %b %Y"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue

        return None

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extract total amount using pattern matching."""
        text_lower = text.lower()

        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return Decimal(amount_str)
                except (InvalidOperation, IndexError):
                    continue

        return None

    def _extract_tax(self, text: str) -> Optional[Decimal]:
        """Extract tax amount using pattern matching."""
        text_lower = text.lower()

        for pattern in self.TAX_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    tax_str = match.group(1).replace(',', '')
                    return Decimal(tax_str)
                except (InvalidOperation, IndexError):
                    continue

        # Return 0.0 if no tax found (common for invoices without tax)
        return Decimal("0.0")

    def _extract_currency(self, text: str) -> str:
        """Extract currency from text."""
        # Look for currency symbols
        for symbol, code in self.CURRENCY_MAP.items():
            if symbol in text:
                return code

        # Look for currency codes
        currency_codes = ["USD", "EUR", "GBP", "GHS", "NGN", "ZAR", "KES"]
        for code in currency_codes:
            if code in text.upper():
                return code

        return "USD"  # Default

    def _infer_category(self, text: str) -> Optional[str]:
        """Infer expense category based on keywords."""
        text_lower = text.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category

        return None

    def _extract_payment_method(self, text: str) -> Optional[str]:
        """Extract payment method from text."""
        text_lower = text.lower()

        payment_methods = {
            "credit_card": ["credit", "visa", "mastercard", "amex", "discover"],
            "debit_card": ["debit"],
            "cash": ["cash"],
            "mobile_money": ["mobile money", "momo", "m-pesa", "airtel money"],
            "bank_transfer": ["bank transfer", "wire", "ach"],
        }

        for method, keywords in payment_methods.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return method

        return None

    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt/invoice number."""
        patterns = [
            r"(?:invoice|receipt)\s+(?:number|no\.?|#)[:\s]*([A-Z0-9-]+)",  # "Invoice Number INV123"
            r"(?:invoice|receipt)[# :]+([A-Z0-9-]+)",  # "Invoice: INV123"
            r"#([A-Z0-9-]{5,})",  # "#INV12345"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1).strip()
                # Skip common words that are not invoice numbers
                if number.lower() not in ['number', 'no', 'date', 'total']:
                    return number

        return None

    def _calculate_confidence(self, data: ExpenseData) -> float:
        """
        Calculate extraction confidence score.

        Score is based on how many fields were successfully extracted.
        """
        total_fields = 6  # merchant, date, amount, tax, category, payment_method
        extracted_fields = 0

        if data.merchant:
            extracted_fields += 1
        if data.date:
            extracted_fields += 1
        if data.amount:
            extracted_fields += 1.5  # Amount is most important
        if data.tax_amount:
            extracted_fields += 0.5
        if data.category:
            extracted_fields += 0.5
        if data.payment_method:
            extracted_fields += 0.5

        confidence = extracted_fields / total_fields
        return min(1.0, confidence)

    async def _extract_with_ai(
        self,
        text: str,
        llm_provider: str = "gemini"
    ) -> ExpenseData:
        """
        Extract expense data using AI/LLM (more accurate but costs money).

        Args:
            text: Raw text from PDF
            llm_provider: LLM provider ID (default: gemini)

        Returns:
            ExpenseData object

        Note:
            This uses Gemini to extract structured data from receipts.
            It's more accurate than pattern matching but costs money.
        """
        try:
            from apps.shared.integration.gemini_service import get_gemini_service
            import json
        except ImportError:
            raise PDFExtractionError("Gemini service not available")

        gemini = get_gemini_service()
        if not gemini.is_available():
            raise PDFExtractionError("Gemini API key not configured")

        # Create structured prompt for extraction
        prompt = f"""Extract expense information from this receipt text. Return ONLY a valid JSON object with these exact fields (use null for missing data):

{{
  "merchant": "merchant or vendor name (string or null)",
  "date": "transaction date in YYYY-MM-DD format (string or null)",
  "amount": "total amount as number (number or null)",
  "tax_amount": "tax amount as number (number or null)",
  "currency": "currency code like USD, GHS, EUR (string, default to USD if not found)",
  "category": "one of: restaurant, travel, office_supplies, utilities, software, rent, marketing, other (string or null)",
  "payment_method": "one of: cash, credit_card, debit_card, mobile_money, bank_transfer (string or null)",
  "receipt_number": "receipt or invoice number (string or null)"
}}

Receipt text:
{text[:15000]}

Return ONLY the JSON object, no explanations."""

        try:
            # Extract using Gemini with low temperature for consistency
            result = await gemini.extract_structured_data(
                prompt=prompt,
                max_output_tokens=1000,
                temperature=0.1
            )

            # Parse JSON response
            # Remove markdown code blocks if present
            json_str = result.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            extracted = json.loads(json_str)

            # Parse date if present
            expense_date = None
            if extracted.get("date"):
                try:
                    from datetime import datetime
                    expense_date = datetime.strptime(extracted["date"], "%Y-%m-%d").date()
                except:
                    # Try to parse with pattern matching as fallback
                    expense_date = self._extract_date(text)

            # Parse amounts
            amount = None
            tax_amount = None
            try:
                if extracted.get("amount") is not None:
                    amount = Decimal(str(extracted["amount"]))
            except:
                amount = self._extract_amount(text)

            try:
                if extracted.get("tax_amount") is not None:
                    tax_amount = Decimal(str(extracted["tax_amount"]))
            except:
                tax_amount = self._extract_tax(text)

            # Create expense data object
            expense_data = ExpenseData(
                merchant=extracted.get("merchant"),
                date=expense_date,
                amount=amount,
                tax_amount=tax_amount,
                currency=extracted.get("currency", "USD"),
                category=extracted.get("category"),
                payment_method=extracted.get("payment_method"),
                receipt_number=extracted.get("receipt_number"),
                raw_text=text,
                confidence=0.9  # AI extraction is high confidence
            )

            # Adjust confidence based on how many fields were extracted
            expense_data.confidence = self._calculate_confidence(expense_data)

            logger.info(
                f"AI extraction successful: merchant={expense_data.merchant}, "
                f"amount={expense_data.amount}, confidence={expense_data.confidence}"
            )

            return expense_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
            # Fallback to pattern matching
            return self._extract_with_patterns(text)
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            # Fallback to pattern matching
            return self._extract_with_patterns(text)

    async def map_fields_to_schema(
        self,
        extracted_data: Dict[str, Any],
        target_schema: Dict[str, str],
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Map extracted fields to target database schema.

        This is useful when extracted field names don't match your database schema.
        For example, mapping "vendor" → "merchant" or "total" → "amount".

        Args:
            extracted_data: Data extracted from PDF
            target_schema: Target schema mapping
                Example: {
                    "merchant": "vendor_name",
                    "expense_date": "transaction_date",
                    "amount": "total_amount"
                }
            use_ai: Use Gemini for intelligent field mapping (more accurate)

        Returns:
            Dict with fields mapped to target schema

        Example:
            extracted = {"vendor": "Starbucks", "total": 15.50}
            target = {"merchant": "vendor", "amount": "total"}
            result = await service.map_fields_to_schema(extracted, target)
            # Returns: {"merchant": "Starbucks", "amount": 15.50}
        """
        if not use_ai:
            # Simple direct mapping
            mapped = {}
            for target_field, source_field in target_schema.items():
                if source_field in extracted_data:
                    mapped[target_field] = extracted_data[source_field]
            return mapped

        # Use Gemini for intelligent mapping
        try:
            from apps.shared.integration.gemini_service import get_gemini_service
            import json
        except ImportError:
            # Fallback to simple mapping
            return {
                target: extracted_data.get(source)
                for target, source in target_schema.items()
                if source in extracted_data
            }

        gemini = get_gemini_service()
        if not gemini.is_available():
            # Fallback to simple mapping
            return {
                target: extracted_data.get(source)
                for target, source in target_schema.items()
                if source in extracted_data
            }

        prompt = f"""Map the following extracted receipt data to match the target database schema.

Extracted Data:
{json.dumps(extracted_data, indent=2, default=str)}

Target Schema (target_field: description):
{json.dumps(target_schema, indent=2)}

Return ONLY a JSON object with the data mapped to target field names. Preserve data types and values.
If a target field has no matching source data, use null.

Example:
If extracted has {{"vendor": "Starbucks"}} and target wants {{"merchant": "vendor name"}},
return {{"merchant": "Starbucks"}}

Return ONLY the JSON object:"""

        try:
            result = await gemini.extract_structured_data(
                prompt=prompt,
                max_output_tokens=1000,
                temperature=0.1
            )

            # Parse JSON
            json_str = result.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            mapped_data = json.loads(json_str.strip())

            logger.info(f"AI field mapping successful: {len(mapped_data)} fields mapped")
            return mapped_data

        except Exception as e:
            logger.error(f"AI field mapping failed: {str(e)}")
            # Fallback to simple mapping
            return {
                target: extracted_data.get(source)
                for target, source in target_schema.items()
                if source in extracted_data
            }

    async def extract_from_file(
        self,
        file: BinaryIO,
        filename: str,
        use_ai: bool = False,
        llm_provider: Optional[str] = None
    ) -> ExpenseData:
        """
        Extract expense data from either PDF or image file (unified interface).

        This method automatically detects the file type and routes to the
        appropriate extraction method:
        - PDF files → extract_from_pdf()
        - Image files (JPEG, PNG, HEIC) → image_receipt_service.extract_from_image()

        Args:
            file: Binary file object
            filename: Name of the file (used for type detection)
            use_ai: Whether to use AI extraction (Gemini)
            llm_provider: LLM provider (default: gemini)

        Returns:
            ExpenseData object with extracted fields

        Raises:
            PDFExtractionError: If file type is not supported or extraction fails

        Example:
            ```python
            service = get_pdf_extraction_service()

            # PDF file
            with open("receipt.pdf", "rb") as f:
                data = await service.extract_from_file(f, "receipt.pdf")

            # Image file
            with open("receipt.jpg", "rb") as f:
                data = await service.extract_from_file(f, "receipt.jpg", use_ai=True)
            ```
        """
        # Determine file type from extension
        file_ext = filename.lower().split(".")[-1]

        # PDF files
        if file_ext == "pdf":
            return await self.extract_from_pdf(file, use_ai=use_ai, llm_provider=llm_provider)

        # Image files (JPEG, PNG, HEIC)
        elif file_ext in ["jpg", "jpeg", "png", "heic", "heif"]:
            # Import image service (avoid circular import)
            try:
                from apps.shared.services.image_receipt_service import get_image_receipt_service
                image_service = get_image_receipt_service(
                    use_ocr=True,
                    tesseract_lang=self.ocr_language
                )
                return await image_service.extract_from_image(
                    file,
                    use_ai=use_ai,
                    llm_provider=llm_provider
                )
            except ImportError as e:
                logger.error(f"Image receipt service not available: {e}")
                raise PDFExtractionError(
                    "Image receipt processing not available. "
                    "Ensure image_receipt_service.py is installed."
                )

        else:
            raise PDFExtractionError(
                f"Unsupported file type: {file_ext}. "
                "Supported types: PDF, JPEG, PNG, HEIC"
            )


# Singleton instance
_pdf_extraction_service: Optional[PDFExtractionService] = None


def get_pdf_extraction_service(
    use_ocr: bool = True,
    ocr_language: str = "eng"
) -> PDFExtractionService:
    """
    Get or create PDF extraction service singleton.

    Args:
        use_ocr: Enable OCR for scanned documents
        ocr_language: Tesseract language code

    Returns:
        PDFExtractionService instance
    """
    global _pdf_extraction_service
    if _pdf_extraction_service is None:
        _pdf_extraction_service = PDFExtractionService(
            use_ocr=use_ocr,
            ocr_language=ocr_language
        )
    return _pdf_extraction_service
