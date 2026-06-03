"""Core ApiGenAgent using Anthropic SDK with tool use to generate FastAPI projects."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import anthropic

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
You are an expert FastAPI developer and code generator.

Given a plain-English description of an API, you generate a complete, working FastAPI project.

You MUST produce all four of these files by calling the write_file tool:
  1. models.py       - Pydantic models (request/response bodies, enums, etc.)
  2. routes.py       - FastAPI router with all endpoints
  3. main.py         - Application entry point that mounts the router
  4. openapi.yaml    - OpenAPI 3.1 specification

Guidelines:
- Use Pydantic v2 syntax (model_config, field validators)
- Add docstrings to every endpoint
- Include realistic example values in Pydantic Field() declarations
- The openapi.yaml must be valid YAML and match the routes exactly
- Create output directories with create_directory before writing files
- After all files are written, provide a short summary of what was generated
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "write_file",
        "description": (
            "Write content to a file at the given path. "
            "Creates parent directories automatically."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute file path to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Full text content to write to the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a directory (and all intermediate parents) at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to create.",
                },
            },
            "required": ["path"],
        },
    },
]


def _write_file(path: str, content: str, base_dir: Path) -> str:
    """Execute the write_file tool."""
    target = base_dir / path if not Path(path).is_absolute() else Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written: {target}"


def _create_directory(path: str, base_dir: Path) -> str:
    """Execute the create_directory tool."""
    target = base_dir / path if not Path(path).is_absolute() else Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return f"Created directory: {target}"


def _dispatch_tool(
    name: str, tool_input: dict[str, Any], base_dir: Path
) -> str:
    """Route a tool call to the correct implementation."""
    if name == "write_file":
        return _write_file(tool_input["path"], tool_input["content"], base_dir)
    if name == "create_directory":
        return _create_directory(tool_input["path"], base_dir)
    return f"Unknown tool: {name}"


class ApiGenAgent:
    """Agent that turns a plain-English API description into FastAPI boilerplate.

    Uses the Anthropic tool-use API to call write_file and create_directory
    tools, producing models.py, routes.py, main.py, and openapi.yaml.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = MODEL,
        output_dir: str | Path = "./generated",
        framework: str = "fastapi",
        verbose: bool = False,
    ) -> None:
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = model
        self.output_dir = Path(output_dir)
        self.framework = framework
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, description: str) -> dict[str, Any]:
        """Generate a FastAPI project from a plain-English API description.

        Args:
            description: Human-readable description of the API to generate.

        Returns:
            A dict with keys:
              - "files_written": list of absolute paths that were created
              - "summary": the agent's final text summary
              - "output_dir": the resolved output directory path
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        user_message = (
            f"Generate a complete {self.framework} project for the following API.\n\n"
            f"All files should be written into the directory: {self.output_dir}\n\n"
            f"API Description:\n{description}"
        )

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]

        files_written: list[str] = []
        summary = ""

        # Agentic tool-use loop
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if self.verbose:
                print(f"[agent] stop_reason={response.stop_reason}")

            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            # Collect text for summary (from any text blocks)
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    summary = block.text.strip()
                    if self.verbose:
                        print(f"[agent] {summary}")

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason != "tool_use":
                # Unexpected stop — break to avoid infinite loop
                break

            # Execute tool calls and collect results
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_input: dict[str, Any] = block.input  # type: ignore[assignment]
                result = _dispatch_tool(block.name, tool_input, self.output_dir)

                if self.verbose:
                    print(f"[tool] {block.name}({json.dumps(tool_input, ensure_ascii=False)[:120]}) -> {result}")

                if block.name == "write_file" and result.startswith("Written:"):
                    files_written.append(result[len("Written: "):])

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

            # Feed results back to the model
            messages.append({"role": "user", "content": tool_results})

        return {
            "files_written": files_written,
            "summary": summary,
            "output_dir": str(self.output_dir.resolve()),
        }
