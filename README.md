# PPT Agent

AI Agent for generating presentation plans from technical and economic proposals using LangGraph.

## Features

- 📄 **Document Analysis**: Automatically extracts key information from proposal documents
- 🎨 **Slide Templates**: Structured schemas for various slide types (Title, Agenda, Key Points, etc.)
- 🔄 **Iterative Review**: Human-in-the-loop workflow for plan approval and revision
- 🔌 **Flexible LLM**: Uses `init_chat_model` to support multiple LLM providers
- 🚀 **LangGraph Server**: Ready for deployment with LangGraph Server API

## Project Structure

```
ppt-agent/
├── pyproject.toml          # Project configuration
├── langgraph.json          # LangGraph Server config
├── .env.example            # Environment variables template
└── src/
    └── ppt_agent/
        ├── __init__.py
        ├── agent.py            # Main entry point
        ├── schemas/
        │   ├── __init__.py
        │   └── slides.py       # Slide template schemas
        ├── graph/
        │   ├── __init__.py
        │   ├── state.py        # Agent state definition
        │   ├── nodes.py        # Graph node functions
        │   └── workflow.py     # LangGraph workflow
        └── prompts/
            ├── __init__.py
            └── templates.py    # Prompt templates
```

## Installation

### Prerequisites
- Python 3.12+
- OpenAI API key (or other supported LLM provider)

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd ppt-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Usage

### Running as a Script

```python
from ppt_agent.agent import run_sync

document = """
Your proposal document text here...
"""

result = run_sync(document)
```

Or run the example:
```bash
python -m ppt_agent.agent
```

### Running with LangGraph Server

1. **Start the server:**
   ```bash
   langgraph dev
   ```

2. **Access the API at** `http://localhost:8123`

3. **Create a new thread and send your document:**
   ```python
   import httpx

   # Create a thread
   response = httpx.post("http://localhost:8123/threads", json={})
   thread_id = response.json()["thread_id"]

   # Send document
   response = httpx.post(
       f"http://localhost:8123/threads/{thread_id}/runs",
       json={
           "assistant_id": "ppt_agent",
           "input": {"document": "Your document..."}
       }
   )
   ```

## Workflow

```
┌─────────────────┐
│ Analyze Document│
└────────┬────────┘
         ▼
┌─────────────────┐
│  Generate Plan  │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│Present for Review│◄────│   Revise Plan   │
└────────┬────────┘     └────────▲────────┘
         │                       │
    ┌────┴────┐                  │
    ▼         ▼                  │
┌───────┐ ┌────────┐    ┌────────┴────────┐
│Approve│ │ Reject │    │ Provide Feedback │
└───┬───┘ └────────┘    └─────────────────┘
    ▼
┌─────────────────┐
│  Finalize Plan  │
└─────────────────┘
```

## Slide Types

| Type | Description |
|------|-------------|
| `title` | Title slide with presentation title, subtitle, author |
| `agenda` | Agenda/overview with list of items |
| `content` | General content with title and body text |
| `key_points` | Highlights with title/description pairs |
| `section_header` | Section divider |
| `closing` | Final slide with call to action |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `MODEL_NAME` | LLM model identifier | `openai/gpt-4o` |

### Switching LLM Providers

Change `MODEL_NAME` in `.env`:
- OpenAI: `openai/gpt-4o`, `openai/gpt-4o-mini`
- Anthropic: `anthropic/claude-3-5-sonnet-20241022`
- Azure: `azure_openai/gpt-4o`

## Next Steps

- [ ] Google Slides generation from approved plans
- [ ] Support for image/chart suggestions
- [ ] Template customization per client
- [ ] Batch processing for multiple documents

## License

MIT
