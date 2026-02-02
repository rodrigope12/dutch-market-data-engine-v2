import pandas as pd
import time
import logging
from datetime import datetime
from typing import List, Optional, Any
from backend.models import Invoice, CheckResult, CheckStatus, ProcessingResult

# Configure Logger with a clean namespace
logger = logging.getLogger("AXIOM.Services")

class ComplianceService:
    """
    Core Logic Engine for Invoice Verification.
    
    Responsibilities:
    - Business Rule Validation (Budget, Contract, Risk)
    - Vendor screening against Watchlists (Sanctions, Internal Blocklists)
    - Integration with ERP Systems (Odoo/SAP)
    """
    
    def __init__(self, data_sources: str = "data"):
        self.data_sources = data_sources
        self._initialize_resources()

    def _initialize_resources(self) -> None:
        """
        Loads and normalizes reference data (Vendors, Budgets, Contracts).
        Gracefully handles missing data by initializing empty DataFrames.
        """
        try:
            self.vendors = pd.read_csv(f"{self.data_sources}/vendors.csv")
            self.budgets = pd.read_csv(f"{self.data_sources}/budgets.csv")
            self.contracts = pd.read_csv(f"{self.data_sources}/contracts.csv")
            
            # Normalize Critical Columns for Case-Insensitive Matching
            if 'risk_level' in self.vendors.columns:
                self.vendors['risk_level'] = self.vendors['risk_level'].fillna('Medium')
            
            logger.info("Compliance Resources loaded successfully.")
            
        except FileNotFoundError as e:
            logger.warning(f"Compliance data missing ({e.filename}). Operating in reduced capacity.")
            self._set_empty_state()
        except Exception as e:
            logger.error(f"Critical error loading resources: {e}", exc_info=True)
            self._set_empty_state()

    def _set_empty_state(self) -> None:
        """Fallback initialization to prevent crash on missing data."""
        self.vendors = pd.DataFrame(columns=['vendor_name', 'iban', 'risk_level'])
        self.budgets = pd.DataFrame(columns=['department', 'total_budget', 'remaining_budget'])
        self.contracts = pd.DataFrame(columns=['vendor_name', 'start_date', 'end_date', 'is_active'])

    def process_invoice(self, invoice: Invoice) -> ProcessingResult:
        """
        Orchestrates the full compliance checklist for a single invoice.
        
        Args:
            invoice: The domain model to validate.
            
        Returns:
            ProcessingResult: The final decision package including all sub-check details.
        """
        logger.info(f"Starting compliance scan for Invoice: {invoice.invoice_id}")
        
        # Execute Checks (Pattern: Policy-based Design)
        checks: List[CheckResult] = [
            self._verify_financial_routing(invoice),
            self._assess_vendor_risk(invoice),
            self._validate_budgetary_alignment(invoice),
            self._verify_contractual_standing(invoice)
        ]
        
        # Aggregate Results
        critical_failures = [c for c in checks if c.status == CheckStatus.FAIL]
        warnings = [c for c in checks if c.status == CheckStatus.WARNING]
        
        final_status = "APPROVED"
        risk_score = 0
        
        if critical_failures:
            final_status = "REJECTED"
            risk_score = 100
            logger.info(f"REJECTED: {len(critical_failures)} critical failure(s).")
        elif warnings:
            final_status = "DRAFT" # Needs Human Review
            risk_score = 50
            logger.info(f"REVIEW NEEDED: {len(warnings)} warning(s).")
        else:
            # Action: Sync to System of Record
            self._post_to_odoo_mock(invoice)
            logger.info("APPROVED: Invoice validated and synced.")
            
        return ProcessingResult(
            invoice=invoice,
            checks=checks,
            final_status=final_status,
            risk_score=risk_score
        )

    def _post_to_odoo_mock(self, invoice: Invoice) -> bool:
        """
        Simulates an API Transaction to Odoo ERP (account.move).
        """
        logger.info(f"[ERP SYNC] Posting Invoice {invoice.invoice_id} to Odoo...")
        # Simulate network latency for realism if needed
        return True

    def _verify_financial_routing(self, invoice: Invoice) -> CheckResult:
        """Ensures the IBAN on the invoice matches the authorized vendor record."""
        # Normalize IBANs
        if 'iban' in self.vendors.columns:
            authorized_ibans = set(str(i).replace(" ", "") for i in self.vendors['iban'].unique())
        else:
            authorized_ibans = set()

        status = CheckStatus.PASS
        msg = "IBAN verified."
        
        if invoice.iban == "UNKNOWN":
            status = CheckStatus.FAIL
            msg = "Missing IBAN on document."
        elif invoice.iban not in authorized_ibans:
            # In production, we might fuzzy match or check generic bank account formats
            status = CheckStatus.FAIL
            msg = f"Unauthorized IBAN detected: {invoice.iban}"
            
        return CheckResult(check_name="Financial Routing", status=status, message=msg, timestamp=time.time())

    def _assess_vendor_risk(self, invoice: Invoice) -> CheckResult:
        """Checks the Vendor against the internal Risk Matrix."""
        inv_vendor = invoice.vendor_name.strip().lower()
        
        # Vectorized Lookup (mocked)
        match_mask = self.vendors['vendor_name'].str.strip().str.lower() == inv_vendor
        vendor_data = self.vendors[match_mask]
        
        if vendor_data.empty:
            return CheckResult(
                check_name="Vendor Risk", 
                status=CheckStatus.WARNING, 
                message="Vendor unknown (First-time supplier).", 
                timestamp=time.time()
            )
        
        risk_level = vendor_data.iloc[0].get('risk_level', 'Medium')
        if risk_level == "High":
            return CheckResult(
                check_name="Vendor Risk", 
                status=CheckStatus.FAIL, 
                message="Vendor is flagged as HIGH RISK.", 
                timestamp=time.time()
            )
        
        return CheckResult(check_name="Vendor Risk", status=CheckStatus.PASS, message="Vendor cleared.", timestamp=time.time())

    def _validate_budgetary_alignment(self, invoice: Invoice) -> CheckResult:
        """Ensures the department has sufficient Remaining Budget."""
        inv_dept = invoice.department.strip().lower()
        match_mask = self.budgets['department'].str.strip().str.lower() == inv_dept
        allocation = self.budgets[match_mask]

        if invoice.department == "Unknown":
            return CheckResult(check_name="Budget Check", status=CheckStatus.WARNING, message="Unclassified Department.", timestamp=time.time())
        
        if allocation.empty:
            return CheckResult(check_name="Budget Check", status=CheckStatus.FAIL, message=f"No budget allocated for '{invoice.department}'.", timestamp=time.time())

        remaining = float(allocation.iloc[0].get('remaining_budget', 0.0))
        if invoice.amount > remaining:
            return CheckResult(
                check_name="Budget Check", 
                status=CheckStatus.FAIL, 
                message=f"Budget Exceeded. Req: €{invoice.amount} > Rem: €{remaining}", 
                timestamp=time.time()
            )
            
        return CheckResult(
            check_name="Budget Check", 
            status=CheckStatus.PASS, 
            message=f"Approved. (Remaining: €{remaining - invoice.amount:.2f})", 
            timestamp=time.time()
        )

    def _verify_contractual_standing(self, invoice: Invoice) -> CheckResult:
        """Verifies that an active contract exists offering coverage for this date."""
        inv_vendor = invoice.vendor_name.strip().lower()
        match_mask = self.contracts['vendor_name'].str.strip().str.lower() == inv_vendor
        agreements = self.contracts[match_mask]
        
        if not invoice.date:
             return CheckResult(check_name="Contract Check", status=CheckStatus.FAIL, message="Invoice missing date info.", timestamp=time.time())

        inv_date_iso = invoice.date.strftime("%Y-%m-%d")
        
        # Iterate through agreements to find ONE valid coverage period
        # O(N) but N is usually small (<5 contracts per vendor)
        for _, agreement in agreements.iterrows():
            if agreement.get('is_active', False):
                start = agreement.get('start_date', '1900-01-01')
                end = agreement.get('end_date', '2099-12-31')
                
                if start <= inv_date_iso <= end:
                    return CheckResult(
                        check_name="Contract Check", 
                        status=CheckStatus.PASS, 
                        message=f"Active Master Agreement found.", 
                        timestamp=time.time()
                    )
        
        return CheckResult(check_name="Contract Check", status=CheckStatus.FAIL, message="No active contract covers this date.", timestamp=time.time())
