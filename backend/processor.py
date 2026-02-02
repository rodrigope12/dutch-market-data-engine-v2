import pdfplumber
import re
import logging
from datetime import datetime, date
from typing import Optional, List
from backend.models import Invoice

# Configure Module Logger
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Handles extraction of structured financial data from Unstructured PDF Invoices.
    
    Adheres to "Apple-Quality" standards:
    - Strict Typing
    - Robust Error Handling
    - Separation of Concerns
    """
    
    # Regex Patterns (Constants)
    VENDOR_PATTERN = r"(?:Vendor|FROM|Issuer):\s*(.+)"
    IBAN_PATTERN = r"(?:IBAN|Account|PAY TO)[:,]?\s*([A-Z]{2}[0-9A-Z\s]{13,32})"
    INVOICE_ID_PATTERNS = [
        r"(?:Invoice #|REF|Invoice Number|ID):\s*([A-Z0-9\-/]+)",
        r"INV-\d{4}-\d+"
    ]
    DATE_PATTERNS = [
        r"(?:Date|Issued):\s*(\d{4}-\d{2}-\d{2})",
        r"(\d{4}-\d{2}-\d{2})"
    ]
    AMOUNT_PATTERN = r"(?:Total Amount|BALANCE DUE|TOTAL|Grand Total)[:\s]*(?:EUR|€)?\s*([\d\.,]+)"
    DEPT_PATTERN = r"(?:Department|DEPT|Cost Center):\s*(\w+)"

    def parse(self, file_path: str) -> Invoice:
        """
        Orchestrates the parsing of a PDF file into a domain model.

        Args:
            file_path: Absolute path to the PDF file.

        Returns:
            Invoice: A validated domain object.
            
        Raises:
            ValueError: If text extraction yields empty results.
            RuntimeError: If critical parsing fails.
        """
        logger.info(f"Starting extraction for: {file_path}")
        
        try:
            raw_text = self._extract_text_from_pdf(file_path)
            if not raw_text:
                raise ValueError(f"No text content found in {file_path}")
            
            # Map extraction logic
            invoice_data = Invoice(
                invoice_id=self._extract_invoice_id(raw_text),
                vendor_name=self._extract_vendor(raw_text),
                iban=self._extract_iban(raw_text),
                date=self._extract_date(raw_text),
                amount=self._extract_amount(raw_text),
                currency="EUR",  # Defaulting for MVP
                department=self._extract_department(raw_text),
                file_path=file_path,
                items=[] # Line items scope for V2
            )
            
            logger.info(f"Successfully parsed Invoice #{invoice_data.invoice_id} from {invoice_data.vendor_name}")
            return invoice_data

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Invoice processing failed: {e}") from e

    def _extract_text_from_pdf(self, path: str) -> str:
        """Helper to safely extract text from all pages."""
        text_content: List[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
        return "\n".join(text_content).strip()

    def _extract_vendor(self, text: str) -> str:
        match = re.search(self.VENDOR_PATTERN, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: First non-generic line heuristic
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        ignore_list = {"INVOICE", "BILL", "RECEIPT", "CREDIT NOTE"}
        
        for line in lines:
            if line.upper() not in ignore_list:
                return line
        return "Unknown Vendor"

    def _extract_iban(self, text: str) -> str:
        match = re.search(self.IBAN_PATTERN, text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            # Remove spaces/newlines to standardize
            clean = re.sub(r'[\s\n]', '', raw)
            return clean
        return "UNKNOWN"

    def _extract_invoice_id(self, text: str) -> str:
        for pattern in self.INVOICE_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Handle cases like "INV-123 / 2023"
                return match.group(1).split('/')[0].strip()
        return "UNKNOWN"

    def _extract_date(self, text: str) -> Optional[date]:
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1).strip(), "%Y-%m-%d").date()
                except ValueError:
                    continue
        return None

    def _extract_amount(self, text: str) -> float:
        match = re.search(self.AMOUNT_PATTERN, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).strip()
            return self._normalize_currency_string(raw_val)
        return 0.0

    def _extract_department(self, text: str) -> str:
        match = re.search(self.DEPT_PATTERN, text, re.IGNORECASE)
        return match.group(1).strip() if match else "Unknown"

    def _normalize_currency_string(self, value_str: str) -> float:
        """
        Smartly handles EU (1.234,56) vs US (1,234.56) number formats.
        """
        try:
            # 1. Check for mixed delimiters to guess locale
            if ',' in value_str and '.' in value_str:
                last_comma = value_str.rfind(',')
                last_dot = value_str.rfind('.')
                
                if last_comma > last_dot: 
                    # EU Format: 1.234,56 -> 1234.56
                    value_str = value_str.replace('.', '').replace(',', '.')
                else:
                    # US Format: 1,234.56 -> 1234.56
                    value_str = value_str.replace(',', '')
            
            # 2. Check for simple comma (could be decimal or thousands)
            elif ',' in value_str:
                # If last part is 2 digits, assume decimal (e.g. ,50) -> EU
                # If 3 digits, assume thousands (e.g. 12,000) -> US
                # This is a heuristic; risky but necessary without locale hints.
                parts = value_str.split(',')
                if len(parts[-1]) == 2:
                    value_str = value_str.replace(',', '.')
                else:
                    value_str = value_str.replace(',', '')

            return float(value_str)
        except ValueError:
            logger.warning(f"Could not parse currency value: {value_str}")
            return 0.0
