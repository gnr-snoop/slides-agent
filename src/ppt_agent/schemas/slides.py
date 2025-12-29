"""Slide template schemas using Pydantic models.

These schemas define the structure for different slide types that can be used
in a presentation. Each slide type has specific fields relevant to its purpose.
"""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class SlideType(str, Enum):
    """Enumeration of available slide types."""

    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    KEY_POINTS = "key_points"
    SECTION_HEADER = "section_header"
    CLOSING = "closing"


class SlideBase(BaseModel):
    """Base class for all slide types."""

    slide_type: SlideType
    speaker_notes: str = Field(
        default="",
        description="Speaker notes for the presenter",
    )


class TitleSlide(SlideBase):
    """Title slide - typically the first slide of the presentation."""

    slide_type: Literal[SlideType.TITLE] = SlideType.TITLE
    title: str = Field(..., description="Main title of the presentation")
    subtitle: str = Field(default="", description="Subtitle or tagline")
    author: str = Field(default="", description="Presenter or company name")
    date: str = Field(default="", description="Presentation date")


class AgendaSlide(SlideBase):
    """Agenda slide - outlines the presentation structure."""

    slide_type: Literal[SlideType.AGENDA] = SlideType.AGENDA
    title: str = Field(default="Agenda", description="Slide title")
    items: list[str] = Field(
        ...,
        description="List of agenda items",
    )


class ContentSlide(SlideBase):
    """Content slide - general purpose slide with title and body text."""

    slide_type: Literal[SlideType.CONTENT] = SlideType.CONTENT
    title: str = Field(..., description="Slide title")
    body: str = Field(..., description="Main content text (supports bullet points)")
    image_suggestion: str = Field(
        default="",
        description="Suggestion for an image or diagram to include",
    )


class KeyPointsSlide(SlideBase):
    """Key points slide - highlights important points with optional icons."""

    slide_type: Literal[SlideType.KEY_POINTS] = SlideType.KEY_POINTS
    title: str = Field(..., description="Slide title")
    points: list[dict[str, str]] = Field(
        ...,
        description="List of key points with 'title' and 'description' keys",
    )


class SectionHeaderSlide(SlideBase):
    """Section header slide - introduces a new section of the presentation."""

    slide_type: Literal[SlideType.SECTION_HEADER] = SlideType.SECTION_HEADER
    title: str = Field(..., description="Section title")
    subtitle: str = Field(default="", description="Optional section subtitle")


class ClosingSlide(SlideBase):
    """Closing slide - typically the last slide with call to action."""

    slide_type: Literal[SlideType.CLOSING] = SlideType.CLOSING
    title: str = Field(default="Thank You", description="Closing title")
    message: str = Field(default="", description="Closing message or call to action")


# Union type for any slide
Slide = Annotated[
    TitleSlide
    | AgendaSlide
    | ContentSlide
    | KeyPointsSlide
    | SectionHeaderSlide
    | ClosingSlide,
    Field(discriminator="slide_type"),
]


class PresentationPlan(BaseModel):
    """Complete presentation plan with all slides."""

    title: str = Field(..., description="Overall presentation title")
    description: str = Field(
        default="",
        description="Brief description of the presentation purpose",
    )
    target_audience: str = Field(
        default="",
        description="Intended audience for the presentation",
    )
    estimated_duration_minutes: int = Field(
        default=30,
        description="Estimated presentation duration in minutes",
    )
    slides: list[Slide] = Field(
        ...,
        description="Ordered list of slides in the presentation",
    )

    def get_slide_count(self) -> int:
        """Return the total number of slides."""
        return len(self.slides)

    def get_slide_summary(self) -> str:
        """Return a formatted summary of all slides."""
        lines = [
            f"Presentation: {self.title}",
            f"Slides: {self.get_slide_count()}",
            f"Duration: ~{self.estimated_duration_minutes} minutes",
            "",
            "Slide Structure:",
            "-" * 40,
        ]
        for i, slide in enumerate(self.slides, 1):
            slide_title = getattr(slide, "title", slide.slide_type.value)
            lines.append(f"{i:2}. [{slide.slide_type.value:15}] {slide_title}")

        return "\n".join(lines)
