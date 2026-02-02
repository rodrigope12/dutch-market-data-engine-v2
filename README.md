# AXIOM Digital Worker - Technical MVP

**For AXIOM Review Team**

This is the technical proof-of-concept for the "Single Technical Partner" role. It demonstrates the **Brain (Logic)**, **Body (Math)**, and **Face (Dashboard)** architecture.

## 🚀 Quick Start

### Option 1: Local Python
```bash
# 1. Create venv
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Internal Audit (Run Tests)
# This verifies the Financial Body's deterministic math
python3 -m pytest tests/

# 4. Run the Digital Worker
streamlit run app.py
```

### Option 2: Docker (The Vault)
```bash
# Build the isolated container
docker build -t axiom-worker .

# Run the localized instance
docker run -p 8501:8501 axiom-worker
```

## 🧠 What to Look For (The "Brain")
Go to the **"Agent Memory"** tab in the sidebar.
- You will see the Agent's "Brain Activity".
- Notice how it retrieves **Risk Profiles** for specific vendors ("Dark Web Corp" vs "AWS").
- This demonstrates the **RAG / Vector Memory** requirement.

## 🧮 What to Verify (The "Body")
In `backend/financial_body.py`, I use `decimal.Decimal` for all math.
- The system automatically rejects invoices where `Subtotal + Tax != Total` (down to the cent).
- See `tests/test_math_engine.py` (if included) for the validation logic.

## 👨‍💻 Human-in-the-Loop (The "Face")
1. Launch the app.
2. Go to **"Review Queue"**.
3. You will see an invoice flagged as **"High Risk Vendor"** (simulated).
4. As the "CFO", you can **Approve** or **Reject** it.
5. This resumes the Agent's state machine.

---
*Built by [Your Name] for AXIOM.*
