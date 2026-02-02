import streamlit as st
from backend.agent_brain import WorkflowEngine, WorkflowState
from frontend.ui_utils import status_pill

def render_activity_stream(engine: WorkflowEngine):
    """
    Renders the main Activity Stream view.
    """
    st.title("Activity Stream")
    st.markdown("Real-time oversight of your Digital Worker fleet.")
    
    # 3-Column Key Metrics
    col1, col2, col3 = st.columns(3)
    
    pending_count = len([w for w in engine.active_workflows.values() if w.status == WorkflowState.AWAITING_HUMAN])
    processed_count = len([w for w in engine.active_workflows.values() if w.status in [WorkflowState.APPROVED, WorkflowState.REJECTED]])
    
    col1.metric("Active Workflows", len(engine.active_workflows))
    col2.metric("Attention Needed", pending_count, delta_color="inverse" if pending_count > 0 else "off")
    col3.metric("Processed Today", processed_count)
    
    st.divider()
    
    # List of Items
    st.markdown("#### Recent Transactions")
    
    # Sort: Pending first, then by ID
    sorted_workflows = sorted(
        engine.active_workflows.items(), 
        key=lambda x: 0 if x[1].status == WorkflowState.AWAITING_HUMAN else 1
    )
    
    for w_id, ctx in sorted_workflows:
        # Card Layout
        expanded_state = (ctx.status == WorkflowState.AWAITING_HUMAN)
        with st.expander(f"{ctx.invoice.vendor_name} — €{ctx.invoice.amount:,.2f}", expanded=expanded_state):
            
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.markdown(status_pill(ctx.status.value), unsafe_allow_html=True)
                st.caption(f"Invoice: {ctx.invoice.invoice_id} | ID: {w_id}")
                
                if ctx.human_action_needed:
                    st.error(f"Reason: {ctx.human_action_needed}")
                
                st.markdown("**Agent Thought Process:**")
                for log in ctx.logs:
                    st.text(f"• {log}")

            with c2:
                # Action Buttons (Only if pending)
                if ctx.status == WorkflowState.AWAITING_HUMAN:
                    st.markdown("##### &nbsp; Decision Required")
                    if st.button("Approve", key=f"app_{w_id}", type="primary"):
                        engine.signal_human_approval(w_id, True)
                        st.rerun()
                    
                    if st.button("Reject", key=f"rej_{w_id}", type="secondary"):
                        engine.signal_human_approval(w_id, False)
                        st.rerun()
