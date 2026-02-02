import pytest
from decimal import Decimal
from backend.financial_body import FinancialCalculator

class TestFinancialIntegrity:
    """
    Verifies the "Body" of the AXIOM Agent.
    Constraint: MUST accept 100% deterministic accuracy.
    """
    
    def setup_method(self):
        self.calc = FinancialCalculator()

    def test_floating_point_avoidance(self):
        """
        Prove that 0.1 + 0.2 equals 0.3 exactly, unlike standard float math.
        """
        # Standard float failure case
        float_res = 0.1 + 0.2
        assert float_res != 0.3  # usually 0.30000000000000004
        
        # AXIOM Decimal Success check
        d1 = self.calc._to_decimal(0.1)
        d2 = self.calc._to_decimal(0.2)
        res = d1 + d2
        assert res == Decimal("0.3")

    def test_tax_rounding_rules(self):
        """
        Verify 'Round Half Up' rule common in EU finance.
        """
        # 10.125 * 0.21 = 2.12625 -> Should round to 2.13
        amount = Decimal("10.125")
        rate = Decimal("0.21")
        
        # Manual check
        expected = Decimal("2.13") 
        result = self.calc.calculate_tax(amount, rate)
        
        # Note: 10.125 * 0.21 is approx 2.126... so 2.13 is correct for 2 decimals
        assert result == expected

    def test_validate_invoice_math_success(self):
        """
        Golden Path: Invoice math adds up.
        """
        subtotal = 100.00
        tax = 21.00
        total = 121.00
        
        is_valid, reason, _ = self.calc.validate_invoice_math(subtotal, tax, total)
        assert is_valid is True
        assert reason == "Math Validated"

    def test_validate_invoice_math_failure(self):
        """
        Fraud detection: Total doesn't match components.
        """
        subtotal = 100.00
        tax = 21.00
        total = 125.00 # Obvious error
        
        is_valid, reason, debug = self.calc.validate_invoice_math(subtotal, tax, total)
        assert is_valid is False
        assert "Arithmetic Error" in reason
        assert debug['diff'] == 4.0

    def test_validate_tax_logic_failure(self):
        """
        Compliance check: Tax amount doesn't match the tax rate.
        """
        subtotal = 100.00
        tax = 10.00 # Should be 21
        total = 110.00 # Math adds up, but tax logic is wrong
        
        is_valid, reason, debug = self.calc.validate_invoice_math(subtotal, tax, total)
        assert is_valid is False
        assert "Tax Logic Error" in reason
