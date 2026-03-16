"""HTTP API for Terraform Generator Service (Railway, etc.)."""

import json

import requests
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import (
    ProcessingCompletedPayload,
    ProcessingFailedPayload,
)
from terraform_generator.input.vibe_selector import ALLOWED_DECISIONS

app = FastAPI(
    title="Terraform Generator Service",
    description="Process JSON infrastructure definitions and generate Terraform files",
    version="0.1.0",
)


@app.get("/")
def health() -> dict:
    """Health check for Railway and load balancers."""
    return {"status": "ok", "service": "terraform-generator"}


@app.post("/api/process")
def process(
    event_id: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True),
    json_url_r2: str = Body(..., alias="json_url_r2", embed=True),
    sent_at: str = Body(..., embed=True),
    decision: str = Body(..., embed=True),
) -> JSONResponse:
    """
    Process JSON input and generate Terraform files.
    The input parameters are:
      - event_id: The event identifier.
      - project_id: The project identifier.
      - json_url_r2: The R2 (S3-compatible) URL to fetch the JSON definition.
      - sent_at: Timestamp when the event was sent.
      - decision: Which vibe to generate (vibe_economica or vibe_performance).
    Only the chosen vibe is used for Terraform generation.
    """
    if decision not in ALLOWED_DECISIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid decision '{decision}'. Allowed values: {sorted(ALLOWED_DECISIONS)}",
        )
    settings = Settings()
    orchestrator = Orchestrator(settings=settings)

    # Fetch the JSON definition from the given R2 URL
    try:
        response = requests.get(json_url_r2, timeout=15)
        response.raise_for_status()
        payload_json = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch or parse JSON from R2 url: {json_url_r2}. Error: {str(e)}"
        )

    # Attach event/project metadata to first item (input is array of items with 'output')
    if isinstance(payload_json, list) and payload_json:
        payload_json[0]["_event_id"] = event_id
        payload_json[0]["_project_id"] = project_id
        payload_json[0]["_sent_at"] = sent_at

    # Pass as JSON string (root must be array) with decision for vibe selection
    content = json.dumps(payload_json)
    result = orchestrator.process(content=content, decision=decision)

    if isinstance(result, ProcessingCompletedPayload):
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "correlation_id": result.correlation_id,
                "output_path": result.output_path,
                "summary": result.summary,
            },
        )

    assert isinstance(result, ProcessingFailedPayload)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "correlation_id": result.correlation_id,
            "stage": result.stage,
            "error": result.error,
            "partial_uploads": result.partial_uploads,
        },
    )
