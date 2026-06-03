"""Jinja2-free string templates for FastAPI application skeleton.

These are provided as reference scaffolds and starting points.
The agent may use them directly or adapt them as needed.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# models.py template
# ---------------------------------------------------------------------------

MODELS_TEMPLATE = '''\
"""Pydantic models for {project_name}."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class {entity}Base(BaseModel):
    """Shared fields for {entity}."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255, examples=["{entity_lower} example"])


class {entity}Create({entity}Base):
    """Request body for creating a {entity}."""


class {entity}Update(BaseModel):
    """Request body for updating a {entity} (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)


class {entity}Response({entity}Base):
    """Response schema for a {entity}."""

    id: int = Field(..., examples=[1])
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Generic paginated list wrapper."""

    items: list[{entity}Response]
    total: int
    page: int
    page_size: int
'''

# ---------------------------------------------------------------------------
# routes.py template
# ---------------------------------------------------------------------------

ROUTES_TEMPLATE = '''\
"""API routes for {project_name}."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from .models import (
    {entity}Create,
    {entity}Response,
    {entity}Update,
    PaginatedResponse,
)

router = APIRouter(prefix="/{entity_lower}s", tags=["{entity}s"])

# In-memory store for demonstration purposes.
_store: dict[int, dict] = {{}}
_next_id: int = 1


@router.post(
    "/",
    response_model={entity}Response,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new {entity}",
)
def create_{entity_lower}(body: {entity}Create) -> {entity}Response:
    """Create a new {entity} and return the created resource."""
    global _next_id
    item = {entity}Response(id=_next_id, name=body.name)
    _store[_next_id] = item.model_dump()
    _next_id += 1
    return item


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List all {entity}s",
)
def list_{entity_lower}s(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse:
    """Return a paginated list of {entity}s."""
    items = [_store[k] for k in sorted(_store)]
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse(
        items=[{entity}Response(**i) for i in items[start:end]],
        total=len(items),
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{{item_id}}",
    response_model={entity}Response,
    summary="Get a {entity} by ID",
)
def get_{entity_lower}(item_id: int) -> {entity}Response:
    """Retrieve a single {entity} by its ID."""
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    return {entity}Response(**_store[item_id])


@router.put(
    "/{{item_id}}",
    response_model={entity}Response,
    summary="Replace a {entity}",
)
def update_{entity_lower}(item_id: int, body: {entity}Update) -> {entity}Response:
    """Update an existing {entity} by ID."""
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    if body.name is not None:
        _store[item_id]["name"] = body.name
    return {entity}Response(**_store[item_id])


@router.delete(
    "/{{item_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a {entity}",
)
def delete_{entity_lower}(item_id: int) -> None:
    """Delete a {entity} by ID."""
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    del _store[item_id]
'''

# ---------------------------------------------------------------------------
# main.py template
# ---------------------------------------------------------------------------

MAIN_TEMPLATE = '''\
"""Entry point for {project_name} API."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="{project_name} API",
    description="{description}",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Return service health status."""
    return {{"status": "ok"}}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''

# ---------------------------------------------------------------------------
# openapi.yaml template
# ---------------------------------------------------------------------------

OPENAPI_TEMPLATE = '''\
openapi: "3.1.0"
info:
  title: "{project_name} API"
  description: "{description}"
  version: "0.1.0"
servers:
  - url: http://localhost:8000/api/v1
    description: Local development server
paths:
  /{entity_lower}s:
    get:
      summary: List all {entity}s
      operationId: list_{entity_lower}s
      tags:
        - {entity}s
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          description: Paginated list of {entity}s
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PaginatedResponse"
    post:
      summary: Create a new {entity}
      operationId: create_{entity_lower}
      tags:
        - {entity}s
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/{entity}Create"
      responses:
        "201":
          description: Created {entity}
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{entity}Response"
  /{entity_lower}s/{{item_id}}:
    get:
      summary: Get a {entity} by ID
      operationId: get_{entity_lower}
      tags:
        - {entity}s
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: The requested {entity}
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{entity}Response"
        "404":
          description: {entity} not found
    put:
      summary: Update a {entity}
      operationId: update_{entity_lower}
      tags:
        - {entity}s
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/{entity}Update"
      responses:
        "200":
          description: Updated {entity}
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/{entity}Response"
        "404":
          description: {entity} not found
    delete:
      summary: Delete a {entity}
      operationId: delete_{entity_lower}
      tags:
        - {entity}s
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "204":
          description: Deleted successfully
        "404":
          description: {entity} not found
components:
  schemas:
    {entity}Base:
      type: object
      required:
        - name
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
          example: "{entity_lower} example"
    {entity}Create:
      allOf:
        - $ref: "#/components/schemas/{entity}Base"
    {entity}Update:
      type: object
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
    {entity}Response:
      allOf:
        - $ref: "#/components/schemas/{entity}Base"
        - type: object
          required:
            - id
            - created_at
          properties:
            id:
              type: integer
              example: 1
            created_at:
              type: string
              format: date-time
    PaginatedResponse:
      type: object
      required:
        - items
        - total
        - page
        - page_size
      properties:
        items:
          type: array
          items:
            $ref: "#/components/schemas/{entity}Response"
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
'''


def render_models(project_name: str, entity: str) -> str:
    """Render the models.py template for the given project and entity name."""
    return MODELS_TEMPLATE.format(
        project_name=project_name,
        entity=entity,
        entity_lower=entity.lower(),
    )


def render_routes(project_name: str, entity: str) -> str:
    """Render the routes.py template for the given project and entity name."""
    return ROUTES_TEMPLATE.format(
        project_name=project_name,
        entity=entity,
        entity_lower=entity.lower(),
    )


def render_main(project_name: str, description: str = "") -> str:
    """Render the main.py template."""
    return MAIN_TEMPLATE.format(
        project_name=project_name,
        description=description or f"API for {project_name}",
    )


def render_openapi(project_name: str, entity: str, description: str = "") -> str:
    """Render the openapi.yaml template."""
    return OPENAPI_TEMPLATE.format(
        project_name=project_name,
        entity=entity,
        entity_lower=entity.lower(),
        description=description or f"API for {project_name}",
    )
