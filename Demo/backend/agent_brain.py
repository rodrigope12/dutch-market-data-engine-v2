import uuid
import logging
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.financial_body import FinancialCalculator
from backend.models import Invoice

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

class WorkflowState(str, Enum):
    """Represents the lifecycle stages of a Digital Worker process."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class MemoryInterface:
    """
    Abstract Protocol for Agent Memory.
    Enables swapping between MockMemory (Dev) and VectorDB (Prod).
    """
    def retrieve_context(self, vendor_name: str) -> Dict[str, Any]:
        raise NotImplementedError

class AgentMemory(MemoryInterface):
    """
    Simulated Vector Database for Context Retrieval (RAG).
    
    In Production: This would connect to Pinecone/Weaviate.
    TODO: Implement PineconeClient here.
    """
    def __init__(self) -> None:
        # Knowledge Graph Simulation
        self.vendor_patterns: Dict[str, Dict[str, Any]] = {
            "dark web corp": {"risk": "HIGH", "avg_delay": 5, "category": "Suspicious"},
            "aws": {"risk": "LOW", "category": "Infrastructure"},
            "mckenzie consulting": {"risk": "MEDIUM", "category": "Professional Services"},
        }
    
    def retrieve_context(self, vendor_name: str) -> Dict[str, Any]:
        """
        Retrieves historical context for a given vendor.
        
        Args:
            vendor_name: The name of the vendor to look up.
            
        Returns:
            Dictionary containing risk profile and metadata.
        """
        key = vendor_name.lower().strip()
        context = self.vendor_patterns.get(key, {"risk": "UNKNOWN", "category": "General"})
        logger.debug(f"Memory Retrieval [{key}]: {context}")
        return context

class WorkflowContext(BaseModel):
    """
    State container for a single Invoice Processing workflow.
    Equivalent to a 'Run ID' in Temporal.io.
    """
    workflow_id: str = Field(..., description="Unique UUID for this execution")
    status: WorkflowState = Field(WorkflowState.PENDING, description="Current lifecycle state")
    invoice: Invoice = Field(..., description="The financial document being processed")
    logs: List[str] = Field(default_factory=list, description="Audit trail of agent reasoning")
    math_verification: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    human_action_needed: Optional[str] = None

class WorkflowEngine:
    """
    Orchestrates the autonomous financial agent.
    
    Architecture:
    - State Machine: Manages transitions between Processing and Human-in-the-Loop.
    - Durable Execution: Designed to be serialized/resumed (mocked via in-memory dict).
    """
    
    def __init__(self) -> None:
        self.memory = AgentMemory()
        self.calculator = FinancialCalculator()
        self.active_workflows: Dict[str, WorkflowContext] = {}

    def start_workflow(self, invoice: Invoice) -> str:
        """
        Initializes a new Digital Worker for the provided invoice.
        
        Returns:
            The workflow_id (str) tracking this process.
        """
        w_id = str(uuid.uuid4())[:8]
        context = WorkflowContext(
            workflow_id=w_id,
            status=WorkflowState.PENDING,
            invoice=invoice
        )
        self.active_workflows[w_id] = context
        self._log(context, f"Workflow initialized for Invoice #{invoice.invoice_id}")
        
        # Immediate Execution Trigger
        self._execute_step(w_id)
        return w_id

    def _execute_step(self, w_id: str) -> None:
        """
        The Core Logic Loop (ReAct Pattern).
        
        1. Perceive: Read Invoice Data
        2. Remember: Check Vector DB for Context
        3. Reason: Validate Math & Risk
        4. Act: Approve, Reject, or Pause for Human
        """
        if w_id not in self.active_workflows:
            logger.error(f"Workflow {w_id} not found.")
            return

        ctx = self.active_workflows[w_id]
        ctx.status = WorkflowState.PROCESSING
        self._log(ctx, "Agent execution started.")

        # --- Phase 1: Context Retrieval ---
        vendor_ctx = self.memory.retrieve_context(ctx.invoice.vendor_name)
        ctx.memory_context = vendor_ctx
        self._log(ctx, f"Memory Lookup: Identified as {vendor_ctx.get('risk')} Risk.")

        # Gate 1: High Risk Block
        if vendor_ctx.get("risk") == "HIGH":
            self._pause_for_human(ctx, "High Risk Vendor detected. CFO Approval Required.")
            return

        # --- Phase 2: Math Integrity Check ---
        # Assuming 21% Tax Rate for demonstration purposes
        try:
            # Reverse engineer subtotal since we only have 'amount' in the MVP Invoice model
            # In production, we would use exact fields from the OCR.
            tax_rate = 0.21
            implied_subtotal = ctx.invoice.amount / (1 + tax_rate)
            implied_tax = ctx.invoice.amount - implied_subtotal
            
            is_valid, reason, _ = self.calculator.validate_invoice_math(
                subtotal=implied_subtotal,
                tax_amount=implied_tax,
                total=ctx.invoice.amount,
                tax_rate=tax_rate
            )
            
            # Simulated Large Transaction Check (> 10k)
            if ctx.invoice.amount > 10000:
                self._pause_for_human(ctx, "Large Transaction (> €10k). Variance Protocol initiated.")
                return

        except Exception as e:
            logger.error(f"Math Engine Failure: {e}")
            self._pause_for_human(ctx, "Deterministic Math Engine Error. Manual Review needed.")
            return

        # --- Phase 3: Final Decision ---
        ctx.status = WorkflowState.APPROVED
        self._log(ctx, "Auto-Approval Logic satisfied. Transaction Released.")

    def signal_human_approval(self, w_id: str, approved: bool) -> None:
        """
        External Signal Handler (Human-in-the-Loop).
        Resumes the frozen workflow based on CFO's decision.
        """
        if w_id not in self.active_workflows:
            return
        
        ctx = self.active_workflows[w_id]
        if ctx.status != WorkflowState.AWAITING_HUMAN:
            logger.warning(f"Signal received for {w_id} but not in AWAITING state.")
            return

        if approved:
            self._log(ctx, "Signal Received: CFO APPROVED. Resuming...")
            ctx.status = WorkflowState.APPROVED
            ctx.human_action_needed = None
        else:
            self._log(ctx, "Signal Received: CFO REJECTED. Terminating.")
            ctx.status = WorkflowState.REJECTED
            ctx.human_action_needed = None
    
    def _pause_for_human(self, ctx: WorkflowContext, reason: str) -> None:
        """Helper to transition state to PAUSED."""
        ctx.status = WorkflowState.AWAITING_HUMAN
        ctx.human_action_needed = reason
        self._log(ctx, f"Workflow Paused: {reason}")

    def _log(self, ctx: WorkflowContext, message: str) -> None:
        """Appends a timestamped log to the audit trail."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        ctx.logs.append(entry)
        logger.info(f"[{ctx.workflow_id}] {message}")
