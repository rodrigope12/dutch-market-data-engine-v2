from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, Tuple
import logging

logger = logging.getLogger("FinancialBody")

class FinancialCalculator:
    """
    Guarantees deterministic accuracy for all financial calculations.
    Uses Python's decimal.Decimal instead of floats.
    """
    
    @staticmethod
    def _to_decimal(value: any) -> Decimal:
        """Safe conversion to Decimal."""
        try:
            if isinstance(value, float):
                # Convert float to string first to avoid precision artifacts
                return Decimal(str(value))
            return Decimal(value)
        except (InvalidOperation, ValueError):
            logger.error(f"Math Error: Could not convert {value} to Decimal")
            raise ValueError(f"Invalid financial input: {value}")

    @staticmethod
    def calculate_tax(amount: Decimal, rate: Decimal) -> Decimal:
        """
        Calculates tax with standard financial rounding (Half Up).
        Example: 100.00 * 0.21 = 21.00
        """
        tax = amount * rate
        # Quantize to 2 decimal places
        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_invoice_math(
        subtotal: float, 
        tax_amount: float, 
        total: float, 
        tax_rate: float = 0.21
    ) -> Tuple[bool, str, dict]:
        """
        Validates if Subtotal + Tax == Total.
        Also checks if Tax Amount matches the expected Tax Rate.
        Returns: (IsValid, Reason, DebugDetails)
        """
        try:
            d_sub = FinancialCalculator._to_decimal(subtotal)
            d_tax = FinancialCalculator._to_decimal(tax_amount)
            d_total = FinancialCalculator._to_decimal(total)
            d_rate = FinancialCalculator._to_decimal(tax_rate)
            
            # 1. Check Arithmetic (Sub + Tax = Total)
            calculated_total = d_sub + d_tax
            if calculated_total != d_total:
                diff = d_total - calculated_total
                return False, f"Arithmetic Error: Subtotal + Tax != Total. Diff: {diff}", {
                    "expected_total": float(calculated_total),
                    "claimed_total": float(d_total),
                    "diff": float(diff)
                }

            # 2. Check Tax Logic (Sub * Rate ~ Tax)
            expected_tax = FinancialCalculator.calculate_tax(d_sub, d_rate)
            # Allow small variance for rounding differences (e.g. +/- 0.05)
            # Some invoices round per line item, some on total.
            tax_diff = abs(expected_tax - d_tax)
            if tax_diff > Decimal("0.05"):
                return False, f"Tax Logic Error: Tax amount doesn't match rate {tax_rate}. Diff: {tax_diff}", {
                    "expected_tax": float(expected_tax),
                    "claimed_tax": float(d_tax),
                    "diff": float(tax_diff)
                }

            return True, "Math Validated", {}
            
        except ValueError as e:
            return False, str(e), {}
