## 1. Cover Letter
**Subject: AGENTIC: I built your "Digital Worker" already. Code + Demo attached.**

Hi there,

I don't sell scripts; I build autonomous systems. **I have already built the "AXIOM Digital Worker" MVP** to demonstrate that I am the Single Technical Partner you are looking for.

I analyzed your architecture requirements (Brain, Body, Face) and built a proof-of-concept that runs locally. Please see the attached `app.py` and backend logic.

### Why this stack wins:
1.  **The Brain (n8n + Python)**: My MVP uses a `WorkflowEngine` (see `backend/agent_brain.py`) that implements a ReAct loop. It perceives the invoice, queries "Memory" (simulated Vector DB), and makes risk decisions *before* asking for human help.
2.  **The Body (Deterministic Math)**: I do NOT use LLMs for math. I use Python's `decimal` library (see `backend/financial_body.py`) to guarantee 100.00% precision.
3.  **The Face (Streamlit Control Panel)**: A premium "Human-in-the-loop" dashboard where the CFO only steps in when the Agent pauses for "High Risk" variance.

I am ready to deploy this containerized Agent (`Dockerfile` included) to your Hetzner VPS today.

Best,
[Your Name]

---

## 2. Mandatory Questions

### The Agent: Describe the most complex "Autonomous Agent" you have built. Did it have memory? How did it handle errors?
**Answer:**
I built the **AXIOM Financial Agent** (included in this zip).
*   **Architecture**: It uses a custom **State Machine** (`WorkflowState` in `agent_brain.py`) to manage the lifecycle of a transaction.
*   **Memory**: It implements a `MemoryInterface` (RAG pattern) to look up historical vendor behavior. For example, if "Dark Web Corp" submits an invoice, the Agent retrieves its risk profile from the vector store and auto-flags it as HIGH RISK, pausing for human review without crashing.
*   **Error Handling**: It wraps the Math Engine in a try/catch block. If the OCR data is malformed, it doesn't crash; it transitions the workflow state to `AWAITING_HUMAN` with a specific error reason ("Deterministic Math Engine Error"), allowing the CFO to fix it manually in the dashboard.

### The Architecture: We want to sell the same Agent to 10 clients. How do you structure the Docker/n8n setup to make deployment easy and scalable?
**Answer:**
I use a **Multi-Tenant Containerized Architecture**.
1.  **Code-Base Separation**: One core codebase, but configuration is injected at runtime.
2.  **Docker Composition**: I have included a `Dockerfile` that creates a non-root user (`axiom`) for security ("The Vault").
3.  **Deployment**: For 10 clients, we deploy 10 isolated containers. Each container pulls the specific client's config (API Keys, Risk Thresholds) from environment variables.
    *   `docker run -e CLIENT_ID=client_A -e RISK_THRESHOLD=5000 axiom-image`
    *   `docker run -e CLIENT_ID=client_B -e RISK_THRESHOLD=10000 axiom-image`
This ensures Client A's data never leaks to Client B, satisfying your security requirement perfectly.

### The Math: How do you ensure the Agent doesn't hallucinate a tax amount? (Explain your validation logic).
**Answer:**
**I never allow the LLM to do arithmetic.**
In `backend/financial_body.py`, I implemented a `FinancialCalculator` class that uses Python's `decimal.Decimal` type.
1.  **Extraction**: The LLM extracts the text strings ("100.00", "21.00").
2.  **Validation Loop**: My Python engine calculates `Subtotal * TaxRate`. If the result differs from the `Total` by more than €0.05, the Agent rejects the invoice automatically.
3.  **Determinism**: `100.00 * 0.21` is *always* `21.00` in my code. In an LLM, it might be `21.01`. My strict separation ensures the Agent only "Reasons" about the tax, but the "Body" calculates it.
