# Interview AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10 | 3.11 | 3.12 | 3.13](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/Built%20with-LangGraph-orange)](https://langchain-ai.github.io/langgraph/)

AI-powered interview automation with LangGraph. Conduct, evaluate, and report on technical interviews with customizable rules and tools.

## Installation

```bash
pip install interview-ai
```

## Agent Setup (Required)

After installation, run the setup command to initialize the agent configuration:

```bash
init-agent
```

This creates an `interview_ai/` directory with:
- `config.json` - LLM and storage settings
- `interview_rules.json` - Interview formats and rules
- `tools.py` - Custom tools for the agent
- `.example-env` - Environment variables template

> ⚠️ **Important**: The package will fail without running `init-agent` first.

## Configuration

### Environment Variables

Copy `.example-env` to `.env` and configure:

```env
# Required: Choose one
OPENAI_API_KEY="your-openai-key"
GOOGLE_API_KEY="your-google-key"

# Optional: Database persistence
POSTGRES_CONNECTION_URI="postgresql://..."
MONGODB_CONNECTION_URI="mongodb://..."
```

### Config File (`interview_ai/config.json`)

```json
{
  "llm_model_name": "gpt-4.1-mini",
  "storage_mode": "memory",
  "internet_search": "duckduckgo"
}
```

## Quick Start

```python
from interview_ai import InterviewClient

# Initialize with interview format
client = InterviewClient(interview_format="short")

# Start interview
result = client.start()
interview_config = result["interview_config"]
print(result["message"])  # "Please enter your full name"

# Continue interview with user responses
response = client.next(interview_config, user_message="John Doe")
print(response["message"])  # Next question or prompt

# End interview and get evaluation
result = client.end(interview_config)
print(result["evaluation"])  # Final evaluation from LLM

# With operations_map for additional actions
result = client.end(interview_config, operations_map=[
    {"type": "email", "to": "hr@company.com"},
    {"type": "api", "endpoint": "https://..."}
])
# Returns: {"evaluation": "...", "email": "...", "api": "..."}
```

### Interview Formats

Pre-configured formats in `interview_rules.json`:

| Format | Questions | Time/Question | Type |
|--------|-----------|---------------|------|
| `short` | 5 | 1 min | Mixed |
| `long` | 5 | 10 min | Mixed |
| `coding` | 1 | 30 min | Coding |

## Custom Tools

Add your own tools in `interview_ai/tools.py`:

```python
from langchain_core.tools import StructuredTool

def company_lookup(company_name: str) -> str:
    """Look up company interview patterns."""
    return f"Interview patterns for {company_name}..."

company_tool = StructuredTool.from_function(
    company_lookup,
    description="Look up typical interview questions for a company"
)

# Register your tools here
user_tools = [company_tool]
```

The agent will automatically load and use your custom tools.

## Why Interview AI?

| Feature | Interview AI | DIY Agent |
|---------|-------------|-----------|
| **Setup Time** | 5 minutes | Hours/Days |
| **Interview Flow** | Built-in graph with phases | Manual state management |
| **Custom Rules** | JSON configuration | Hardcoded logic |
| **Custom Tools** | Drop-in `tools.py` | Complex integration |
| **Evaluation** | Structured output schema | Custom parsing |
| **Persistence** | SQLite/Postgres/MongoDB | Manual implementation |
| **Answer Timer** | Automatic expiry | Not included |

## Documentation

For detailed usage, API reference, and advanced configuration:

📖 **[Full Documentation](https://toonformatter.net/docs.html?package=interview-ai)**

## License

[MIT](LICENSE) © 2025 Ankit Pal
