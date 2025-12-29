"""Prompt templates for the PPT Agent.

These prompts guide the LLM in analyzing documents and generating presentation plans.
"""

SLIDE_TYPES_DESCRIPTION = """
Available slide types:

1. **title** - Title slide (first slide)
   - title: Main presentation title
   - subtitle: Optional tagline
   - author: Presenter/company name
   - date: Presentation date

2. **agenda** - Agenda/outline slide
   - title: Usually "Agenda" or "Overview"
   - items: List of agenda items

3. **content** - General content slide
   - title: Slide title
   - body: Main content (can include bullet points)
   - image_suggestion: Optional image/diagram suggestion

4. **key_points** - Highlights important points
   - title: Slide title
   - points: List of points, each with 'title' and 'description'

5. **section_header** - Section divider
   - title: Section title
   - subtitle: Optional subtitle

6. **closing** - Final slide
   - title: Usually "Thank You" or "Next Steps"
   - message: Call to action or closing message
"""

DOCUMENT_ANALYSIS_PROMPT = """You are an expert business analyst and presentation consultant.

Analyze the following technical and economic proposal document and extract key information that will help create an effective presentation.

## Document to Analyze:
{document}

## Your Task:
Analyze the document and provide a structured analysis including:

1. **Main Topic**: What is the core subject/proposal about?
2. **Key Sections**: What are the main sections or themes in the document?
3. **Technical Highlights**: What technical aspects should be emphasized?
4. **Economic Highlights**: What business/economic benefits or costs should be highlighted?
5. **Target Audience**: Who is the intended audience for this presentation?
6. **Suggested Tone**: What tone would be most appropriate (formal, persuasive, technical, etc.)?

## Output Format:
Respond with a JSON object with this structure:
```json
{{
  "main_topic": "string",
  "key_sections": ["string", ...],
  "technical_highlights": ["string", ...],
  "economic_highlights": ["string", ...],
  "target_audience": "string",
  "suggested_tone": "string"
}}
```
"""

PLAN_GENERATION_PROMPT = """You are an expert presentation designer specializing in technical and business proposals.

Based on the document analysis below, create a comprehensive presentation plan.

## Document Analysis:
{analysis}

## Original Document:
{document}

## Available Slide Types:
{slide_types}

## Your Task:
Create a presentation plan that:
1. Starts with a compelling title slide
2. Includes an agenda/overview
3. Covers all key technical points
4. Highlights economic benefits
5. Ends with a clear call to action or next steps

## Guidelines:
- Target 10-15 slides for a 30-minute presentation
- Use appropriate slide types for different content
- Include speaker notes for each slide
- Make titles concise and impactful
- Ensure logical flow between slides
- Balance technical depth with business value

## Output Format:
Respond with a JSON object with this structure:
```json
{{
  "title": "Presentation title",
  "description": "Brief description",
  "target_audience": "Intended audience",
  "estimated_duration_minutes": 30,
  "slides": [
    {{
      "slide_type": "title",
      "title": "Main Title",
      "subtitle": "Subtitle",
      "author": "Author",
      "date": "Date",
      "speaker_notes": "Notes"
    }},
    {{
      "slide_type": "agenda",
      "title": "Agenda",
      "items": ["Item 1", "Item 2"],
      "speaker_notes": "Notes"
    }},
    {{
      "slide_type": "content",
      "title": "Slide Title",
      "body": "Content text",
      "image_suggestion": "",
      "speaker_notes": "Notes"
    }},
    ... more slides
  ]
}}
```

Slide types: title, agenda, content, key_points, section_header, closing

Generate the complete presentation plan with all slide details.
"""

PLAN_REVISION_PROMPT = """You are an expert presentation designer helping to revise a presentation plan based on user feedback.

## Current Presentation Plan:
{current_plan}

## User Feedback:
{feedback}

## Original Document:
{document}

## Available Slide Types:
{slide_types}

## Your Task:
Revise the presentation plan based on the user's feedback. Make sure to:
1. Address all points mentioned in the feedback
2. Maintain the overall coherence of the presentation
3. Keep the slide count reasonable (10-20 slides)
4. Preserve any aspects the user didn't mention (they're likely satisfied with those)

## Output Format:
Respond with the complete revised presentation plan as a JSON object with the same structure as the original plan:
```json
{{
  "title": "Presentation title",
  "description": "Brief description",
  "target_audience": "Intended audience",
  "estimated_duration_minutes": 30,
  "slides": [ ... slide objects ... ]
}}
```

Generate the complete revised presentation plan in JSON format.
"""
