from pathlib import Path

from api.models import DiagnosticRequest
from diagnostics.engine import CircuitSageEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = PROJECT_ROOT / "data" / "canonical"


REPRESENTATIVE_PROJECTS = [
    {
        "project_name": "HC-SR04 Ultrasonic",
        "project_id": "8",
        "query": "HC-SR04 ultrasonic distance sensor",
    },
    {
        "project_name": "DHT11 / DHT22",
        "project_id": "1",
        "query": "DHT11 temperature humidity sensor",
    },
    {
        "project_name": "MPU6050",
        "project_id": "50",
        "query": "MPU6050 I2C sensor",
    },
    {
        "project_name": "nRF24L01",
        "project_id": "15",
        "query": "nRF24L01 SPI wireless communication",
    },
    {
        "project_name": "GSM",
        "project_id": "22",
        "query": "SIM900 GSM communication",
    },
    {
        "project_name": "Stepper Motor",
        "project_id": "145",
        "query": "stepper motor control",
    },
]


def test_representative_projects_are_retrievable():
    engine = CircuitSageEngine()

    for project in REPRESENTATIVE_PROJECTS:
        result = engine.retrieve(project["query"])

        project_ids = {
            str(item["project_id"])
            for item in result["results"]
        }

        assert project["project_id"] in project_ids, (
            f"Project {project['project_id']} "
            f"({project['project_name']}) was not retrieved "
            f"for query: {project['query']}"
        )


def test_representative_queries_have_supported_scope():
    engine = CircuitSageEngine()

    for project in REPRESENTATIVE_PROJECTS:
        result = engine.retrieve(project["query"])

        retrieval_for_scope = {
            item["project_id"]: {
                "score": item["score"],
                "matches": item["matches"],
            }
            for item in result["results"]
        }

        from retrieval.scope_gate import evaluate_scope

        scope = evaluate_scope(
            project["query"],
            retrieval_for_scope,
            engine.coverage,
            evidence_context={
                "code": "// representative diagnostic code evidence",
                "serial_output": None,
            },
        )

        assert scope["status"] == "SUPPORTED", (
            f"{project['project_name']} unexpectedly returned "
            f"{scope['status']}: {scope.get('reason')}"
        )


def test_unknown_domain_remains_unsupported():
    engine = CircuitSageEngine()

    request = DiagnosticRequest(
        problem_description=(
            "Diagnose my quantum teleportation control system."
        )
    )

    response = engine.diagnose(request)

    assert response.status == "UNSUPPORTED"
    assert response.accepted is True
    assert response.diagnosis.startswith(
        "This component or diagnostic scenario isn't currently supported"
    )