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
def process(body: dict) -> JSONResponse:
    """
    Process JSON input and generate Terraform files.
    Persistence depends on ENVIRONMENT (dev=local, production=S3).
    """
    settings = Settings()
    orchestrator = Orchestrator(settings=settings)

    # Pass as JSON string (orchestrator expects content for API flow)
    content = json.dumps(body)
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
