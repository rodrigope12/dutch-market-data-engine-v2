import streamlit as st
from backend.agent_brain import WorkflowEngine, WorkflowState

def render_review_queue(engine: WorkflowEngine):
    """
    Renders the Review Queue for blocked items.
    """
    st.title("Review Queue")
    st.markdown("Detailed inspection of exceptions blocked by the Agent.")
    
    to_review = [w for w in engine.active_workflows.values() if w.status == WorkflowState.AWAITING_HUMAN]
    
    if not to_review:
        st.success("All caught up! No exceptions pending.")
        # Minimalist placeholder
        st.caption("Enjoy the silence.")
    else:
        for ctx in to_review:
            with st.container():
                st.markdown(f"### {ctx.invoice.vendor_name}")
                st.markdown(f"**Amount:** €{ctx.invoice.amount:,.2f}")
                st.warning(f"**Blocker:** {ctx.human_action_needed}")
                
                c_act1, c_act2 = st.columns(2)
                if c_act1.button("Approve Release", key=f"q_app_{ctx.workflow_id}", type="primary"):
                    engine.signal_human_approval(ctx.workflow_id, True)
                    st.rerun()
                if c_act2.button("Reject & Archive", key=f"q_rej_{ctx.workflow_id}", type="secondary"):
                    engine.signal_human_approval(ctx.workflow_id, False)
                    st.rerun()
                st.divider()
