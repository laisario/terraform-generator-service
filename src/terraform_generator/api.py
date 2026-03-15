"""HTTP API for Terraform Generator Service (Railway, etc.)."""

import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from terraform_generator.config import Settings
from terraform_generator.events.orchestrator import Orchestrator
from terraform_generator.events.payloads import (
    ProcessingCompletedPayload,
    ProcessingFailedPayload,
)

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
from fastapi import Body, HTTPException
import requests

def process(
    event_id: str = Body(..., embed=True),
    project_id: str = Body(..., embed=True),
    json_url_r2: str = Body(..., alias="json_url_r2", embed=True),
    sent_at: str = Body(..., embed=True),
) -> JSONResponse:
    """
    Process JSON input and generate Terraform files.
    The input parameters are:
      - event_id: The event identifier.
      - project_id: The project identifier.
      - json_url_r2: The R2 (S3-compatible) URL to fetch the JSON definition.
      - sent_at: Timestamp when the event was sent.
    The function will retrieve the JSON from the provided R2 URL and then process it.
    """
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

    # Attach event/project metadata if needed (optional, e.g., inside payload_json)
    payload_json["_event_id"] = event_id
    payload_json["_project_id"] = project_id
    payload_json["_sent_at"] = sent_at

    # Pass as JSON string
    content = json.dumps(payload_json)
    result = orchestrator.process(content=content)

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
