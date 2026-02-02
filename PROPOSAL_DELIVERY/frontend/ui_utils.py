import streamlit as st
import os

def load_css(asset_path: str = "assets/style.css"):
    """Loads the custom CSS file if it exists."""
    if os.path.exists(asset_path):
        with open(asset_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def status_pill(status: str) -> str:
    """
    Renders a beautiful status pill using custom CSS classes.
    
    Args:
        status: The WorkflowState value (e.g., 'APPROVED', 'AWAITING_HUMAN').
    """
    color_map = {
        "APPROVED": "status-approved",
        "REJECTED": "status-rejected",
        "AWAITING_HUMAN": "status-awaiting"
    }
    # Default fallback
    cls = color_map.get(status, "status-awaiting")
    clean_text = status.replace("_", " ")
    return f"<span class='status-pill {cls}'>{clean_text}</span>"
