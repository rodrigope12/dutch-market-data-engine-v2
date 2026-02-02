import streamlit as st
from backend.models import Invoice
from backend.agent_brain import WorkflowEngine
from frontend.ui_utils import load_css
from frontend.components.sidebar import render_sidebar
from frontend.components.activity_stream import render_activity_stream
from frontend.components.review_queue import render_review_queue
from frontend.components.memory_view import render_memory_view

# --- Config ---
st.set_page_config(
    page_title="AXIOM | Digital Worker",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialization ---
load_css()

if 'engine' not in st.session_state:
    st.session_state.engine = WorkflowEngine()

# Initialize Demo Data (Only once)
if not st.session_state.engine.active_workflows:
    demos = [
        Invoice(invoice_id="INV-2024-001", vendor_name="Amazon Web Services", iban="NL00RABO0123456789", amount=120.00, items=[]),
        Invoice(invoice_id="INV-2024-002", vendor_name="Dark Web Corp", iban="NL00RABO9876543210", amount=500.00, items=[]),
        Invoice(invoice_id="INV-2024-003", vendor_name="McKenzie Consulting", iban="NL00INGB0001112223", amount=15000.00, items=[])
    ]
    for inv in demos:
        st.session_state.engine.start_workflow(inv)

engine = st.session_state.engine

# --- Architecture ---
selected_view = render_sidebar()

if selected_view == "Activity Stream":
    render_activity_stream(engine)

elif selected_view == "Review Queue":
    render_review_queue(engine)

elif selected_view == "Agent Memory":
    render_memory_view(engine)
