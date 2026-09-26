from evidence_package import EvidencePackage
from reasoning_pipeline import run_reasoning_pipeline


def test_pipeline_uses_deterministic_diagnosis(monkeypatch):
    gemma_response = """
This is deliberately irrelevant and should not control the diagnosis.
"""

    monkeypatch.setattr(
        "reasoning_pipeline.reason_from_evidence",
        lambda package: gemma_response,
    )

    package = EvidencePackage(
        user_query="HC-SR04 problem",
        scope_status="SUPPORTED",
        component="HC-SR04",
        validator_result={
            "overall_status": "PASS",
            "summary": {
                "total": 8,
                "passed": 8,
                "failed": 0,
                "unknown": 0,
            },
            "checks": [
                {
                    "check_id": "HC001",
                    "name": "TRIG pin defined",
                    "status": "PASS",
                    "evidence": "trigPin = 11",
                },
                {
                    "check_id": "HC002",
                    "name": "ECHO pin defined",
                    "status": "PASS",
                    "evidence": "echoPin = 12",
                },
            ],
        },
        known_unknowns=[
            "Physical wiring has not been verified.",
        ],
    )

    result = run_reasoning_pipeline(package)

    assert result["accepted"] is True
    assert result["reasoning_source"] == "deterministic"

    assert (
        "No confirmed malfunction has been established"
        in result["diagnosis"]
    )

    assert "TRIG pin defined" in result["diagnosis"]
    assert "ECHO pin defined" in result["diagnosis"]

    # Gemma output must not replace deterministic diagnosis.
    assert result["diagnosis"] != gemma_response


def test_pipeline_survives_invalid_gemma_output(monkeypatch):
    invalid_response = """
{
    "projects": [
        {
            "project_id": 292,
            "project_name": "L293D Motor Shield Examples"
        }
    ]
}
"""

    monkeypatch.setattr(
        "reasoning_pipeline.reason_from_evidence",
        lambda package: (_ for _ in ()).throw(
            ValueError("Gemma returned an invalid schema")
        ),
    )

    package = EvidencePackage(
        user_query="HC-SR04 problem",
        scope_status="SUPPORTED",
        component="HC-SR04",
        validator_result={
            "overall_status": "PASS",
            "summary": {
                "total": 8,
                "passed": 8,
                "failed": 0,
                "unknown": 0,
            },
            "checks": [],
        },
        known_unknowns=[
            "Physical wiring has not been verified.",
        ],
    )

    result = run_reasoning_pipeline(package)

    assert result["accepted"] is True
    assert result["reasoning_source"] == "deterministic"

    assert result["gemma_reasoning"] is None
    assert result["gemma_error"] == "Gemma returned an invalid schema"

    assert (
        "No confirmed malfunction has been established"
        in result["diagnosis"]
    )


def test_pipeline_preserves_deterministic_fail(monkeypatch):
    monkeypatch.setattr(
        "reasoning_pipeline.reason_from_evidence",
        lambda package: (_ for _ in ()).throw(
            ValueError("Gemma failure")
        ),
    )

    package = EvidencePackage(
        user_query="HC-SR04 problem",
        scope_status="SUPPORTED",
        component="HC-SR04",
        validator_result={
            "overall_status": "FAIL",
            "summary": {
                "total": 8,
                "passed": 7,
                "failed": 1,
                "unknown": 0,
            },
            "checks": [
                {
                    "check_id": "HC003",
                    "name": "TRIG configured OUTPUT",
                    "status": "FAIL",
                    "evidence": "pinMode(trigPin, OUTPUT) not detected",
                }
            ],
        },
        known_unknowns=[
            "Physical hardware operation has not been verified.",
        ],
    )

    result = run_reasoning_pipeline(package)

    assert result["accepted"] is True
    assert result["reasoning_source"] == "deterministic"

    assert "code-level issue was detected" in result["diagnosis"]
    assert "TRIG configured OUTPUT" in result["diagnosis"]

    assert result["gemma_reasoning"] is None
    assert result["gemma_error"] == "Gemma failure"


def test_pipeline_handles_unknown_validator(monkeypatch):
    monkeypatch.setattr(
        "reasoning_pipeline.reason_from_evidence",
        lambda package: (_ for _ in ()).throw(
            ValueError("Gemma failure")
        ),
    )

    package = EvidencePackage(
        user_query="HC-SR04 problem",
        scope_status="SUPPORTED",
        component="HC-SR04",
        validator_result={
            "overall_status": "UNKNOWN",
            "summary": {
                "total": 8,
                "passed": 7,
                "failed": 0,
                "unknown": 1,
            },
            "checks": [],
        },
        known_unknowns=[
            "Physical wiring has not been verified.",
        ],
    )

    result = run_reasoning_pipeline(package)

    assert result["accepted"] is True
    assert result["reasoning_source"] == "deterministic"

    assert (
        "No confirmed malfunction has been established"
        in result["diagnosis"]
    )

    assert result["gemma_reasoning"] is None
    assert (
    result["gemma_error"]
    == "Gemma reasoning skipped because deterministic validation status is UNKNOWN."
)