"""Main entry point for the PPT Agent.

This module provides functions to run the agent both as a standalone script
and through the LangGraph Server API.
"""

import asyncio
from typing import Any

from ppt_agent.graph.state import AgentState, PlanStatus
from ppt_agent.graph.workflow import graph


async def run_agent(document: str, thread_id: str = "default") -> dict[str, Any]:
    """Run the PPT Agent with a document.

    This function starts the agent workflow and handles the interactive
    review loop with the user.

    Args:
        document: The proposal document text to create a presentation for.
        thread_id: Unique identifier for this conversation thread.

    Returns:
        The final state of the agent including the approved/rejected plan.
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    initial_state = AgentState(document=document)

    # Run until first interrupt (present_for_review)
    print("\n🚀 Starting PPT Agent...")
    print("📄 Analyzing document and generating presentation plan...\n")

    result = await graph.ainvoke(initial_state.model_dump(), config)

    # Print the review message
    if result.get("messages"):
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            print(last_message.content)

    # Interactive review loop
    while result.get("status") == PlanStatus.DRAFT.value:
        # Get user feedback
        print("\n" + "-" * 50)
        user_input = input("Your response: ").strip()

        if not user_input:
            print("Please provide feedback or type 'approve'/'reject'.")
            continue

        # Update state with user feedback and resume
        result = await graph.ainvoke(
            {"user_feedback": user_input},
            config,
        )

        # Print the response
        if result.get("messages"):
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print("\n" + last_message.content)

    return result


async def submit_feedback(thread_id: str, feedback: str) -> dict[str, Any]:
    """Submit feedback for an existing thread (for API usage).

    This is useful when running through the LangGraph Server API
    where the interaction is stateless.

    Args:
        thread_id: The thread ID to resume.
        feedback: User feedback or approval/rejection.

    Returns:
        The updated state after processing the feedback.
    """
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"user_feedback": feedback},
        config,
    )

    return result


def run_sync(document: str, thread_id: str = "default") -> dict[str, Any]:
    """Synchronous wrapper for running the agent.

    Args:
        document: The proposal document text.
        thread_id: Unique identifier for this conversation thread.

    Returns:
        The final state of the agent.
    """
    return asyncio.run(run_agent(document, thread_id))


# Example usage
EXAMPLE_DOCUMENT = """
# Cloud Migration Proposal for Acme Corporation

## Executive Summary
We propose migrating Acme Corporation's on-premise infrastructure to AWS cloud, 
reducing operational costs by 40% while improving system reliability and scalability.

## Technical Approach

### Phase 1: Assessment (2 weeks)
- Inventory existing infrastructure
- Identify application dependencies
- Create migration roadmap

### Phase 2: Foundation (4 weeks)
- Set up AWS landing zone
- Configure networking and security
- Establish CI/CD pipelines

### Phase 3: Migration (8 weeks)
- Migrate non-critical workloads first
- Implement data replication
- Perform staged cutover of production systems

### Phase 4: Optimization (4 weeks)
- Right-size resources
- Implement auto-scaling
- Set up monitoring and alerting

## Technical Stack
- AWS EC2, ECS, and Lambda for compute
- RDS and DynamoDB for databases
- S3 for storage
- CloudFront for CDN
- Terraform for infrastructure as code

## Economic Analysis

### Current Costs (Annual)
- Hardware maintenance: $200,000
- Data center lease: $150,000
- IT operations staff: $300,000
- Total: $650,000

### Projected Cloud Costs (Annual)
- AWS services: $250,000
- Managed services: $100,000
- Reduced IT staff needs: $150,000
- Total: $500,000

### ROI
- Annual savings: $150,000
- Migration cost: $200,000
- Break-even: 16 months
- 5-year savings: $550,000

## Timeline
- Total duration: 18 weeks
- Start date: January 2026
- Go-live: May 2026

## Team
- Project Manager: 1
- Cloud Architects: 2
- DevOps Engineers: 3
- Database Specialists: 1

## Contact
John Smith, Cloud Solutions Lead
john.smith@cloudpartners.com
+1 (555) 123-4567
"""


if __name__ == "__main__":
    print("=" * 60)
    print("PPT Agent - Presentation Plan Generator")
    print("=" * 60)

    result = run_sync(EXAMPLE_DOCUMENT)

    print("\n" + "=" * 60)
    print("Final Status:", result.get("status", "Unknown"))
    print("=" * 60)
