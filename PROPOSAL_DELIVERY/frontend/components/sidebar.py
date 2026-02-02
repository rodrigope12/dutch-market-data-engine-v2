import streamlit as st

def render_sidebar() -> str:
    """
    Renders the AXIOM OS Sidebar.
    
    Returns:
        The selected menu option (str).
    """
    with st.sidebar:
        st.markdown("### AXIOM **OS**")
        st.caption("Finance Transformation Agent")
        st.markdown("---")
        
        menu_options = ["Activity Stream", "Review Queue", "Agent Memory"]
        
        # Use a more styled radio interface in the future, for now standard streamlt is fine
        selected = st.radio(
            "Navigation", 
            menu_options,
            index=0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Bottom Status Area
        st.caption("System Status")
        st.info("System Online\n\nv2.0.0")
        
        return selected
