import streamlit as st
import pandas as pd
from backend.agent_brain import WorkflowEngine

def render_memory_view(engine: WorkflowEngine):
    """
    Renders the internal state of the Agent's memory.
    """
    st.title("Business Context Memory")
    st.markdown("Contextual data used for vendor risk assessment.")
    
    data = []
    # Data visualization for demo purposes
    if hasattr(engine.memory, 'vendor_patterns'):
        params = engine.memory.vendor_patterns
        for vendor, context in params.items():
            row = {"Vendor": vendor.title(), **context}
            data.append(row)
    
    if data:
        st.dataframe(
            pd.DataFrame(data), 
            use_container_width=True,
            column_config={
                "risk": st.column_config.TextColumn("Risk Profile"),
                "category": st.column_config.TextColumn("Category"),
                "avg_delay": st.column_config.NumberColumn("Avg Delay (Days)"),
            }
        )
    else:
        st.info("Memory is empty.")
