"""Graph nodes for the PPT Agent.

This module contains the node functions that perform the actual work
in the LangGraph workflow.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ppt_agent.graph.state import AgentState, DocumentAnalysis, PlanStatus
from ppt_agent.prompts.templates_esp import (
    DOCUMENT_ANALYSIS_PROMPT,
    PLAN_GENERATION_PROMPT,
    PLAN_REVISION_PROMPT,
    REVIEW_PLAN_TEMPLATE,
    SLIDE_TYPES_DESCRIPTION,
)
from ppt_agent.schemas.slides import PresentationPlan

# Load environment variables
load_dotenv()


def get_llm():
    """Initialize the LLM using init_chat_model for flexibility.

    Uses the MODEL_NAME environment variable to determine which model to use.
    Format: "provider/model_name" (e.g., "azure_openai/gpt-4o", "openai/gpt-4o")
    
    For Azure OpenAI, also requires:
    - AZURE_OPENAI_API_KEY
    - AZURE_OPENAI_ENDPOINT
    - OPENAI_API_VERSION
    """
    model_name = os.getenv("MODEL_NAME", "azure_openai:gpt-4o")
    
    # Check if using Azure OpenAI
    if model_name.startswith("azure_openai"):
        return init_chat_model(
            model_name,
            temperature=0.7,
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("OPENAI_API_VERSION", "2024-08-01-preview"),
        )
    
    return init_chat_model(model_name, temperature=0.7)


def get_structured_llm(schema: type):
    """Get an LLM with structured output for a specific schema.
    
    Uses 'json_mode' method for Azure OpenAI compatibility since Azure's
    structured output requires all fields to be required (no optional fields).
    """
    llm = get_llm()
    model_name = os.getenv("MODEL_NAME", "azure_openai:gpt-4o")
    
    # Azure OpenAI has stricter schema requirements - use json_mode instead
    if model_name.startswith("azure_openai"):
        return llm.with_structured_output(schema, method="json_mode")
    
    return llm.with_structured_output(schema)


async def analyze_document(state: AgentState) -> dict[str, Any]:
    """Analyze the input document to extract key information.

    This node takes the raw document and produces a structured analysis
    that guides the presentation plan generation.
    """
    llm = get_structured_llm(DocumentAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        #SystemMessage(content="You are an expert business analyst."),
        SystemMessage(content="Sos un experto analista de negocios."),
        HumanMessage(content=DOCUMENT_ANALYSIS_PROMPT.format(document=state.document)),
    ])

    try:
        chain = prompt | llm
        analysis = await chain.ainvoke({})

        return {
            "document_analysis": analysis,
            "messages": [
                #AIMessage(content=f"I've analyzed the document. Main topic: {analysis.main_topic}")
                AIMessage(content=f"He analizado el documento. Tema principal: {analysis.main_topic}")
            ],
        }
    except Exception as e:
        return {
            "error": f"Failed to analyze document: {str(e)}",
            "messages": [AIMessage(content=f"Error analyzing document: {str(e)}")],
        }


async def generate_plan(state: AgentState) -> dict[str, Any]:
    llm = get_structured_llm(PresentationPlan)

    analysis_text = state.document_analysis.model_dump_json(indent=2) if state.document_analysis else "No analysis available"

    prompt = ChatPromptTemplate.from_messages([
        #SystemMessage(content="You are an expert presentation designer."),
        SystemMessage(content="Eres un experto diseñador de presentaciones."),
        HumanMessage(content=PLAN_GENERATION_PROMPT.format(
            analysis=analysis_text,
            document=state.document,
            slide_types=SLIDE_TYPES_DESCRIPTION,
        )),
    ])

    try:
        chain = prompt | llm
        plan = await chain.ainvoke({})

        return {
            "presentation_plan": plan,
            "status": PlanStatus.DRAFT,
            "messages": [
                AIMessage(content=f"He creado un plan de presentación con {plan.get_slide_count()} diapositivas.\n\n{plan.get_slide_summary()}")
            ],
        }
    except Exception as e:
        return {
            "error": f"Failed to generate plan: {str(e)}",
            "status": PlanStatus.PENDING,
            "messages": [AIMessage(content=f"Error generating plan: {str(e)}")],
        }


async def revise_plan(state: AgentState) -> dict[str, Any]:

    llm = get_structured_llm(PresentationPlan)

    current_plan_text = state.presentation_plan.model_dump_json(indent=2) if state.presentation_plan else "No plan available"

    print("User feedback for revision:", state.user_feedback)
    print("------"*10)
    prompt = ChatPromptTemplate.from_messages([
        #SystemMessage(content="You are an expert presentation designer helping to refine a presentation."),
        SystemMessage(content="Eres un experto diseñador de presentaciones que ayuda a revisar un plan de presentación basándose en los comentarios del usuario."),
        HumanMessage(content=PLAN_REVISION_PROMPT.format(
            current_plan=current_plan_text,
            feedback=state.user_feedback,
            document=state.document,
            slide_types=SLIDE_TYPES_DESCRIPTION,
        )),
    ])

    try:
        chain = prompt | llm
        revised_plan = await chain.ainvoke({})

        return {
            "presentation_plan": revised_plan,
            "status": PlanStatus.DRAFT,
            "revision_count": state.revision_count + 1,
            "user_feedback": "",  # Clear feedback after processing
            "messages": [
                #AIMessage(content=f"I've revised the presentation plan based on your feedback.\n\n{revised_plan.get_slide_summary()}")
                AIMessage(content=f"He revisado el plan de presentación basándome en tus comentarios.\n\n{revised_plan.get_slide_summary()}")
            ],
        }
    except Exception as e:
        return {
            "error": f"Failed to revise plan: {str(e)}",
            "messages": [AIMessage(content=f"Error revising plan: {str(e)}")],
        }


async def present_for_review(state: AgentState) -> dict[str, Any]:
    """Present the current plan to the user for review.

    This is an interrupt node that pauses execution for human review.
    The plan is formatted and presented to the user.
    """
    if state.presentation_plan is None:
        return {
            #"messages": [AIMessage(content="No plan available for review.")],
            "messages": [AIMessage(content="No hay un plan disponible para revisión.")],
        }

    plan = state.presentation_plan
    summary = plan.get_slide_summary()

    # Create detailed slide breakdown
    detailed_slides = []
    for i, slide in enumerate(plan.slides, 1):
        slide_dict = slide.model_dump()
        detailed_slides.append(f"\n### Slide {i}: {slide.slide_type.value.upper()}")
        for key, value in slide_dict.items():
            if key != "slide_type" and value:
                if isinstance(value, list):
                    detailed_slides.append(f"  - {key}:")
                    for item in value:
                        if isinstance(item, dict):
                            detailed_slides.append(f"    • {json.dumps(item)}")
                        else:
                            detailed_slides.append(f"    • {item}")
                else:
                    detailed_slides.append(f"  - {key}: {value}")

    detailed_view = "\n".join(detailed_slides)

    review_message = REVIEW_PLAN_TEMPLATE.format(
        summary=summary,
        detailed_view=detailed_view,
        remaining_revisions=state.max_revisions - state.revision_count,
    )

    return {
        "messages": [AIMessage(content=review_message)],
    }


async def finalize_plan(state: AgentState) -> dict[str, Any]:
    """Finalize the approved presentation plan.

    This node is called when the user approves the plan.
    It outputs the final structure and generates Google Slides if configured.
    """
    if state.presentation_plan is None:
        return {
            "error": "No plan to finalize",
            "messages": [AIMessage(content="Error: No plan available to finalize.")],
        }

    plan = state.presentation_plan

    # Print the final structure
    print("\n" + "=" * 60)
    print("APPROVED PRESENTATION PLAN")
    print("=" * 60)
    print(plan.get_slide_summary())
    print("\n" + "=" * 60)
    print("FULL PLAN JSON:")
    print("=" * 60)
    print(plan.model_dump_json(indent=2))
    print("=" * 60 + "\n")

    # Try to generate Google Slides if credentials are configured
    slides_message = ""
    google_credentials = os.getenv("GOOGLE_CREDENTIALS_PATH") or os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
    
    if google_credentials:
        try:
            from ppt_agent.services.google_slides import GoogleSlidesService
            
            service = GoogleSlidesService()
            result = service.create_presentation(plan)
            slides_message = f"\n\n🔗 **Google Slides Created:**\n{result['url']}"
        except Exception as e:
            slides_message = f"\n\n⚠️ Could not create Google Slides: {str(e)}"
    else:
        slides_message = "\n\n💡 Configure GOOGLE_CREDENTIALS_PATH to auto-generate Google Slides."

    return {
        "status": PlanStatus.APPROVED,
        "messages": [
            AIMessage(content=f"✅ Plan approved and finalized!\n\n{plan.get_slide_summary()}{slides_message}")
        ],
    }


async def handle_rejection(state: AgentState) -> dict[str, Any]:
    """Handle plan rejection.

    This node is called when the user completely rejects the plan.
    """
    return {
        "status": PlanStatus.REJECTED,
        "messages": [
            #AIMessage(content="❌ The presentation plan has been rejected. You can start over with a new document or provide different requirements.")
            AIMessage(content="El plan de presentación ha sido rechazado. Puedes comenzar de nuevo con un nuevo documento o proporcionar diferentes requisitos.")
        ],
    }


def should_continue_review(state: AgentState) -> str:
    """Determine the next step based on user response.

    Returns the name of the next node to execute.
    """
    feedback = state.user_feedback.lower().strip()
    
    if feedback == "aprobar":
        return "finalize"
    elif feedback == "rechazar":
        return "reject"
    elif state.revision_count >= state.max_revisions:
        return "max_revisions"
    else:
        return "revise"


def check_for_errors(state: AgentState) -> str:
    """Check if there were any errors in the previous step."""
    if state.error:
        return "error"
    return "continue"
