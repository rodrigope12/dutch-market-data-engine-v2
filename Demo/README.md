# AXIOM Digital Worker - Technical MVP

**Prepared for:** AXIOM Finance Transformation Consultancy
**Role:** Single Technical Partner (Brain, Body, Face)

This repository contains the **Proof of Concept (MVP)** for the Autonomous Financial Agent. It demonstrates the required architecture:
*   **The Brain**: ReAct Logic Loop (Python/n8n style)
*   **The Body**: Deterministic Math Engine (100% Precision)
*   **The Face**: Human-in-the-Loop Dashboard (Streamlit)

---

## 🚀 Quick Start (Professional Setup)

For a clean and isolated execution, we recommend using a Python Virtual Environment.

### 1. Environment Setup
Open your terminal in this directory and run:

```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

### 2. Install Dependencies
Install the required libraries into your isolated environment:

```bash
pip install -r requirements.txt
```

### 3. Run the Digital Worker
Launch the Agent's Control Panel:

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser (usually at `http://localhost:8501`).

---

## 🏗️ Architecture Overview

### 1. Agent Logic (`backend/agent_brain.py`)
*   **WorkflowEngine**: Orchestrates the lifecycle of every invoice (Pendng -> Processing -> Approved/Rejected).
*   **MemoryInterface**: Simulates a Vector Database connection to retrieve vendor risk profiles (e.g., "Dark Web Corp" = High Risk).

### 2. Math Integrity (`backend/financial_body.py`)
*   **FinancialCalculator**: Uses Python's `decimal` library to prevent floating-point errors.
*   **Validation**: Automatically cross-references `Subtotal + Tax` against `Total`. If there is a variance > €0.05, the Agent pauses for human review.

### 3. Deployment (`Dockerfile`)
*   Included is a production-ready `Dockerfile` that creates a non-root user (`axiom`) for security.
*   Ready to be deployed to Hetzner/DigitalOcean for multi-tenant isolation.
