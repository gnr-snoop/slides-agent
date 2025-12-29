"""LangGraph workflow definition for the PPT Agent.

This module defines the complete graph workflow with human-in-the-loop
review cycles for presentation plan generation.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ppt_agent.graph.nodes import (
    analyze_document,
    check_for_errors,
    finalize_plan,
    generate_plan,
    handle_rejection,
    present_for_review,
    revise_plan,
    should_continue_review,
)
from ppt_agent.graph.state import AgentState, PlanStatus


def create_graph() -> StateGraph:
    """Create the PPT Agent workflow graph.

    The workflow follows this structure:
    1. Analyze Document -> Extract key information
    2. Generate Plan -> Create initial presentation plan
    3. Present for Review -> Show plan to user (INTERRUPT)
    4. Based on user response:
       - "approve" -> Finalize and output
       - "reject" -> End with rejection
       - feedback -> Revise plan -> Back to review
    """
    # Create the graph with our state schema
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_document", analyze_document)
    workflow.add_node("generate_plan", generate_plan)
    workflow.add_node("present_for_review", present_for_review)
    workflow.add_node("revise_plan", revise_plan)
    workflow.add_node("finalize_plan", finalize_plan)
    workflow.add_node("handle_rejection", handle_rejection)

    workflow.set_entry_point("analyze_document")

    workflow.add_conditional_edges(
        "analyze_document",
        check_for_errors,
        {
            "error": END,
            "continue": "generate_plan",
        },
    )

    workflow.add_conditional_edges(
        "generate_plan",
        check_for_errors,
        {
            "error": END,
            "continue": "present_for_review",
        },
    )


    workflow.add_conditional_edges(
        "present_for_review",
        should_continue_review,
        {
            "finalize": "finalize_plan",
            "reject": "handle_rejection",
            "revise": "revise_plan",
            "max_revisions": "finalize_plan",  
        },
    )

    workflow.add_conditional_edges(
        "revise_plan",
        check_for_errors,
        {
            "error": END,
            "continue": "present_for_review",
        },
    )

    workflow.add_edge("finalize_plan", END)
    workflow.add_edge("handle_rejection", END)

    return workflow


def compile_graph():
    """Compile the graph with memory checkpointing for human-in-the-loop.

    Returns a compiled graph that can be used with the LangGraph Server API.
    """
    workflow = create_graph()

    # Use MemorySaver for checkpointing (enables interrupt/resume)
    #memory = MemorySaver()

    # Compile with interrupt_before on present_for_review
    # This allows the user to provide feedback before continuing
    compiled = workflow.compile(
        #checkpointer=memory,
        interrupt_after=["present_for_review"],  # Interrupt after showing the plan
    )

    return compiled


# Export the compiled graph for LangGraph Server
graph = compile_graph()
