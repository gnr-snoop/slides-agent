"""Google Slides service for generating presentations from PresentationPlan.

This module provides functionality to create Google Slides presentations
from the structured PresentationPlan schema.
"""

import os
from typing import Any

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

from ppt_agent.schemas.slides import (
    AgendaSlide,
    ClosingSlide,
    ContentSlide,
    KeyPointsSlide,
    PresentationPlan,
    SectionHeaderSlide,
    TitleSlide,
)

# Google Slides API scopes
SCOPES = ["https://www.googleapis.com/auth/presentations"]


class GoogleSlidesService:
    """Service for creating Google Slides presentations from PresentationPlan."""

    def __init__(
        self,
        credentials_path: str | None = None,
        service_account_path: str | None = None,
        token_path: str = "token.json",
    ):
        """Initialize the Google Slides service.

        Args:
            credentials_path: Path to OAuth2 client credentials JSON file.
            service_account_path: Path to service account credentials JSON file.
                                  Use this for server-to-server authentication.
            token_path: Path to store/load OAuth2 tokens.
        """
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.service_account_path = service_account_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
        self.token_path = token_path
        self._service: Resource | None = None

    def _get_credentials(self) -> Credentials | ServiceAccountCredentials:
        """Get Google API credentials.

        Returns:
            Valid credentials for the Google Slides API.
        """
        # Try service account first (for server deployments)
        if self.service_account_path and os.path.exists(self.service_account_path):
            return ServiceAccountCredentials.from_service_account_file(
                self.service_account_path,
                scopes=SCOPES,
            )

        # Fall back to OAuth2 flow (for local development)
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path or not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        "No credentials found. Please provide either:\n"
                        "- GOOGLE_CREDENTIALS_PATH env var (OAuth2 client credentials)\n"
                        "- GOOGLE_SERVICE_ACCOUNT_PATH env var (service account)"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for future use
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    def _get_service(self) -> Resource:
        """Get or create the Google Slides API service.

        Returns:
            Google Slides API service resource.
        """
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("slides", "v1", credentials=creds)
        return self._service

    def create_presentation(self, plan: PresentationPlan) -> dict[str, Any]:
        """Create a Google Slides presentation from a PresentationPlan.

        Args:
            plan: The presentation plan to convert to slides.

        Returns:
            Dictionary with presentation ID and URL.
        """
        service = self._get_service()

        # Create a new presentation
        presentation = service.presentations().create(
            body={"title": plan.title}
        ).execute()

        presentation_id = presentation["presentationId"]

        # Get the default slide to delete it later
        default_slide_id = presentation["slides"][0]["objectId"]

        # Build all slide requests (without speaker notes)
        requests = []
        slide_ids = []  # Track slide IDs for speaker notes

        # Add slides based on the plan
        for i, slide in enumerate(plan.slides):
            slide_id = f"slide_{i}"
            slide_ids.append((slide_id, slide.speaker_notes))
            slide_requests = self._create_slide_requests(slide, i)
            requests.extend(slide_requests)

        # Delete the default blank slide
        requests.append({"deleteObject": {"objectId": default_slide_id}})

        # Execute all requests in batch
        if requests:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()

        # Add speaker notes in a separate batch (requires getting notes page IDs)
        #self._add_speaker_notes(service, presentation_id, slide_ids)

        presentation_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"

        return {
            "presentation_id": presentation_id,
            "url": presentation_url,
            "title": plan.title,
            "slide_count": len(plan.slides),
        }

    def _create_slide_requests(self, slide: Any, index: int) -> list[dict[str, Any]]:
        """Create API requests for a single slide.

        Args:
            slide: The slide schema object.
            index: The slide index for generating unique IDs.

        Returns:
            List of API request dictionaries.
        """
        slide_id = f"slide_{index}"
        requests = []

        # Determine layout based on slide type
        if isinstance(slide, TitleSlide):
            requests.extend(self._create_title_slide(slide, slide_id))
        elif isinstance(slide, AgendaSlide):
            requests.extend(self._create_agenda_slide(slide, slide_id))
        elif isinstance(slide, ContentSlide):
            requests.extend(self._create_content_slide(slide, slide_id))
        elif isinstance(slide, KeyPointsSlide):
            requests.extend(self._create_key_points_slide(slide, slide_id))
        elif isinstance(slide, SectionHeaderSlide):
            requests.extend(self._create_section_header_slide(slide, slide_id))
        elif isinstance(slide, ClosingSlide):
            requests.extend(self._create_closing_slide(slide, slide_id))

        # Speaker notes are added separately after all slides are created
        return requests

    def _create_title_slide(self, slide: TitleSlide, slide_id: str) -> list[dict[str, Any]]:
        """Create requests for a title slide."""
        title_id = f"{slide_id}_title"
        subtitle_id = f"{slide_id}_subtitle"

        requests = [
            # Create the slide with TITLE layout
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "CENTERED_TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "SUBTITLE"}, "objectId": subtitle_id},
                    ],
                }
            },
            # Insert title text
            {
                "insertText": {
                    "objectId": title_id,
                    "text": slide.title,
                }
            },
        ]

        # Add subtitle if present
        subtitle_parts = []
        if slide.subtitle:
            subtitle_parts.append(slide.subtitle)
        if slide.author:
            subtitle_parts.append(slide.author)
        if slide.date:
            subtitle_parts.append(slide.date)

        if subtitle_parts:
            requests.append({
                "insertText": {
                    "objectId": subtitle_id,
                    "text": "\n".join(subtitle_parts),
                }
            })

        return requests

    def _create_agenda_slide(self, slide: AgendaSlide, slide_id: str) -> list[dict[str, Any]]:
        """Create requests for an agenda slide."""
        title_id = f"{slide_id}_title"
        body_id = f"{slide_id}_body"

        # Format agenda items as bullet points
        body_text = "\n".join(f"• {item}" for item in slide.items)

        return [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "BODY"}, "objectId": body_id},
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": slide.title,
                }
            },
            {
                "insertText": {
                    "objectId": body_id,
                    "text": body_text,
                }
            },
        ]

    def _create_content_slide(self, slide: ContentSlide, slide_id: str) -> list[dict[str, Any]]:
        """Create requests for a content slide."""
        title_id = f"{slide_id}_title"
        body_id = f"{slide_id}_body"

        return [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "BODY"}, "objectId": body_id},
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": slide.title,
                }
            },
            {
                "insertText": {
                    "objectId": body_id,
                    "text": slide.body,
                }
            },
        ]

    def _create_key_points_slide(self, slide: KeyPointsSlide, slide_id: str) -> list[dict[str, Any]]:
        """Create requests for a key points slide."""
        title_id = f"{slide_id}_title"
        body_id = f"{slide_id}_body"

        # Format key points with title and description
        body_lines = []
        for point in slide.points:
            point_title = point.get("title", "")
            point_desc = point.get("description", "")
            if point_title:
                body_lines.append(f"• {point_title}")
                if point_desc:
                    body_lines.append(f"  {point_desc}")

        body_text = "\n".join(body_lines)

        return [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "BODY"}, "objectId": body_id},
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": slide.title,
                }
            },
            {
                "insertText": {
                    "objectId": body_id,
                    "text": body_text,
                }
            },
        ]

    def _create_section_header_slide(
        self, slide: SectionHeaderSlide, slide_id: str
    ) -> list[dict[str, Any]]:
        """Create requests for a section header slide."""
        title_id = f"{slide_id}_title"

        # SECTION_HEADER layout only has a TITLE placeholder
        # We'll add subtitle as part of the title if present
        title_text = slide.title
        if slide.subtitle:
            title_text = f"{slide.title}\n\n{slide.subtitle}"

        return [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "SECTION_HEADER"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": title_text,
                }
            },
        ]

    def _create_closing_slide(self, slide: ClosingSlide, slide_id: str) -> list[dict[str, Any]]:
        """Create requests for a closing slide."""
        title_id = f"{slide_id}_title"
        subtitle_id = f"{slide_id}_subtitle"

        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "CENTERED_TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "SUBTITLE"}, "objectId": subtitle_id},
                    ],
                }
            },
            {
                "insertText": {
                    "objectId": title_id,
                    "text": slide.title,
                }
            },
        ]

        if slide.message:
            requests.append({
                "insertText": {
                    "objectId": subtitle_id,
                    "text": slide.message,
                }
            })

        return requests

    def _add_speaker_notes(
        self,
        service: Resource,
        presentation_id: str,
        slide_notes: list[tuple[str, str]],
    ) -> None:
        """Add speaker notes to slides after they are created.

        Args:
            service: Google Slides API service.
            presentation_id: The presentation ID.
            slide_notes: List of (slide_id, notes_text) tuples.
        """
        # Get the presentation to find notes page shape IDs
        presentation = service.presentations().get(
            presentationId=presentation_id
        ).execute()

        notes_requests = []

        for slide in presentation.get("slides", []):
            slide_id = slide["objectId"]

            # Find matching notes from our list
            notes_text = None
            for sid, notes in slide_notes:
                if sid == slide_id:
                    notes_text = notes
                    break

            if not notes_text:
                continue

            # Get the notes page and find the body shape
            notes_page = slide.get("slideProperties", {}).get("notesPage", {})
            for element in notes_page.get("pageElements", []):
                shape = element.get("shape", {})
                if shape.get("shapeType") == "TEXT_BOX":
                    # This is the notes text box
                    notes_shape_id = element["objectId"]
                    notes_requests.append({
                        "insertText": {
                            "objectId": notes_shape_id,
                            "text": notes_text,
                        }
                    })
                    break

        # Execute notes update if we have any
        if notes_requests:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": notes_requests},
            ).execute()
