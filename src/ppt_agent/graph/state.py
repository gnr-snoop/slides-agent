"""LangGraph state definition for the PPT Agent.

This module defines the state that flows through the graph, including the document,
presentation plan, user feedback, and approval status.
"""

from enum import Enum
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

from ppt_agent.schemas.slides import PresentationPlan


class PlanStatus(str, Enum):
    """Status of the presentation plan."""

    PENDING = "pending"  # Initial state, no plan yet
    DRAFT = "draft"  # Plan generated, awaiting review
    REVISION_REQUESTED = "revision_requested"  # User requested changes
    APPROVED = "approved"  # User approved the plan
    REJECTED = "rejected"  # User rejected the plan entirely


class DocumentAnalysis(BaseModel):
    """Analysis of the input document."""

    main_topic: str = Field(default="", description="Main topic of the document")
    key_sections: list[str] = Field(
        default_factory=list,
        description="Key sections identified in the document",
    )
    technical_highlights: list[str] = Field(
        default_factory=list,
        description="Technical highlights to emphasize",
    )
    economic_highlights: list[str] = Field(
        default_factory=list,
        description="Economic/business highlights to emphasize",
    )
    target_audience: str = Field(
        default="",
        description="Inferred target audience",
    )
    suggested_tone: str = Field(
        default="professional",
        description="Suggested presentation tone",
    )


class AgentState(BaseModel):
    """State for the PPT Agent graph.

    This state flows through the graph and contains all information needed
    for generating and refining the presentation plan.
    """

    # Input
    document: str = Field(
        ...,
        description="The input document containing the proposal",
    )

    # Analysis
    document_analysis: DocumentAnalysis | None = Field(
        default=None,
        description="Analysis of the input document",
    )

    # Plan
    presentation_plan: PresentationPlan | None = Field(
        default=None,
        description="The generated presentation plan",
    )

    # Review cycle
    status: PlanStatus = Field(
        default=PlanStatus.PENDING,
        description="Current status of the plan",
    )
    user_feedback: str = Field(
        default="",
        description="User feedback for revision",
    )
    revision_count: int = Field(
        default=0,
        description="Number of revisions made",
    )
    max_revisions: int = Field(
        default=5,
        description="Maximum number of allowed revisions",
    )

    # Messages for conversation history
    messages: Annotated[list[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Conversation history",
    )

    # Metadata
    error: str | None = Field(
        default=None,
        description="Error message if something went wrong",
    )

    class Config:
        arbitrary_types_allowed = True
