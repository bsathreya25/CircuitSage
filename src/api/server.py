from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from api.models import DiagnosticRequest
from diagnostics.engine import CircuitSageEngine


app = FastAPI(
    title="CircuitSage API",
    description="Agentic AI backend for embedded-systems diagnostics.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://circuitsagev1.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseRequest(BaseModel):
    problem_description: str = Field(
        ...,
        min_length=1,
        description="Description of the embedded-system problem.",
    )
    code: Optional[str] = Field(
        default=None,
        description="Arduino/C/C++ source code.",
    )
    schematic_path: Optional[str] = Field(
        default=None,
        description="Path or identifier for a schematic artifact.",
    )
    serial_output: Optional[str] = Field(
        default=None,
        description="Observed Serial Monitor output.",
    )
    project_name: Optional[str] = Field(
        default=None,
        description="Optional project or source-file name.",
    )


engine = CircuitSageEngine()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CircuitSage API",
        "version": "1.0.0",
    }


@app.post("/diagnose")
def diagnose(request: DiagnoseRequest):
    try:
        diagnostic_request = DiagnosticRequest(
            problem_description=request.problem_description,
            code=request.code,
            schematic_path=request.schematic_path,
            serial_output=request.serial_output,
            project_name=request.project_name,
        )

        response = engine.diagnose(diagnostic_request)

        return response.to_dict()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "ERROR",
                "message": "CircuitSage encountered an internal diagnostic error.",
                "detail": str(exc),
            },
        )