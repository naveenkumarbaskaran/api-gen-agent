# api-gen-agent

An AI agent that takes a plain-English description of an API and generates a
complete, working FastAPI project including:

- `models.py` — Pydantic v2 request/response models
- `routes.py` — FastAPI router with full CRUD endpoints
- `main.py` — Application entry point with CORS and health check
- `openapi.yaml` — OpenAPI 3.1 specification

Powered by [Anthropic Claude](https://anthropic.com) (`claude-sonnet-4-6`) via
the official `anthropic` Python SDK with tool use.

---

## Installation

```bash
pip install api-gen-agent
```

Or install from source:

```bash
git clone https://github.com/example/api-gen-agent
cd api-gen-agent
pip install -e .
```

### Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Quick Start

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

api-gen-agent create "A REST API for a bookstore that manages books, authors,
and customer orders." --output ./bookstore_api
```

This writes four files into `./bookstore_api/`:

```
bookstore_api/
  models.py
  routes.py
  main.py
  openapi.yaml
```

You can run the generated app immediately:

```bash
pip install fastapi uvicorn
cd bookstore_api
uvicorn main:app --reload
# Open http://localhost:8000/docs
```

---

## CLI Reference

```
Usage: api-gen-agent create [OPTIONS] DESCRIPTION

  Generate a FastAPI project from a plain-English API DESCRIPTION.

Arguments:
  DESCRIPTION  One or more sentences describing the API.  [required]

Options:
  --framework TEXT   Target framework (currently only fastapi).  [default: fastapi]
  --output PATH      Output directory for generated files.  [default: ./generated]
  --model TEXT       Anthropic model to use.  [default: claude-sonnet-4-6]
  --api-key TEXT     Anthropic API key (defaults to ANTHROPIC_API_KEY env var).
  --verbose          Print agent reasoning and tool calls.
  --help             Show this message and exit.
```

### Examples

```bash
# Simple CRUD API
api-gen-agent create "A task management API with projects and tasks"

# Specify output directory
api-gen-agent create "An e-commerce API for products and orders" --output ./shop_api

# Verbose mode to see agent reasoning
api-gen-agent create "A blog platform API" --verbose

# Use a different Claude model
api-gen-agent create "A pet clinic API" --model claude-opus-4-8
```

---

## Python API

You can also use the agent programmatically:

```python
from api_gen_agent import ApiGenAgent

agent = ApiGenAgent(
    output_dir="./generated",
    verbose=True,
)

result = agent.generate(
    "A REST API for a library that manages books, members, and loan records."
)

print("Files written:")
for path in result["files_written"]:
    print(f"  {path}")

print("Summary:", result["summary"])
print("Output dir:", result["output_dir"])
```

### `ApiGenAgent` constructor parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | Anthropic API key; falls back to `ANTHROPIC_API_KEY` env var |
| `model` | `str` | `"claude-sonnet-4-6"` | Anthropic model ID |
| `output_dir` | `str \| Path` | `"./generated"` | Where to write generated files |
| `framework` | `str` | `"fastapi"` | Target framework (currently only `"fastapi"`) |
| `verbose` | `bool` | `False` | Print tool calls and agent messages |

### `ApiGenAgent.generate(description)` return value

```python
{
    "files_written": ["/abs/path/models.py", ...],  # absolute paths
    "summary": "Generated a bookstore API with ...",  # agent's summary
    "output_dir": "/abs/path/to/output_dir",
}
```

---

## Templates

The `api_gen_agent.templates` module provides Jinja2-free string templates that
can be rendered independently of the agent:

```python
from api_gen_agent.templates import render_models, render_routes, render_main, render_openapi

models_src = render_models(project_name="Bookstore", entity="Book")
routes_src = render_routes(project_name="Bookstore", entity="Book")
main_src   = render_main(project_name="Bookstore", description="A bookstore API")
spec_yaml  = render_openapi(project_name="Bookstore", entity="Book", description="A bookstore API")
```

These are reference scaffolds. When the agent runs, it generates code tailored
to the specific API description rather than filling in the templates directly.

---

## How It Works

1. The CLI passes your description to `ApiGenAgent.generate()`.
2. The agent sends the description to Claude with two tools:
   - `write_file(path, content)` — write a file to disk
   - `create_directory(path)` — create a directory
3. Claude calls these tools to produce `models.py`, `routes.py`, `main.py`, and `openapi.yaml`.
4. The agent loops until Claude stops calling tools (`stop_reason == "end_turn"`).
5. A summary of what was generated is printed to the terminal.

---

## Development

```bash
# Install with dev dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Lint
ruff check api_gen_agent

# Type check
mypy api_gen_agent
```

---

## License

MIT
