from api.models import DiagnosticRequest

from diagnostics.engine import CircuitSageEngine


def test_empty_problem_returns_invalid_request():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="",
        )
    )

    assert response.status == "INVALID_REQUEST"
    assert response.accepted is True
    assert response.error is None


def test_unknown_component_returns_safe_response():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description=(
                "XYZ_SUPER_UNKNOWN_SENSOR_123 "
                "is behaving strangely"
            )
        )
    )

    assert response.status == "UNSUPPORTED"
    assert response.accepted is True
    assert response.diagnosis
    assert response.limitations


def test_no_retrieval_evidence_returns_unsupported():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="GSM system",
        )
    )

    assert response.status == "UNSUPPORTED"
    assert response.accepted is True
    assert response.diagnosis
    assert response.limitations


def test_supported_validator_with_insufficient_evidence_does_not_create_fake_failure():
    engine = CircuitSageEngine()

    result = engine.run_deterministic_validation(
        component="DHT11",
        code=(
            "void setup() {}"
            "\n"
            "void loop() {}"
        ),
    )

    assert result is not None
    assert result["validator_id"] == "dht_v1"
    assert result["component"] == "DHT11/DHT22"
    assert result["overall_status"] == "UNKNOWN"
    assert result["summary"]["failed"] == 0
    assert result["summary"]["unknown"] > 0


def test_response_serialization():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="",
        )
    )

    data = response.to_dict()

    assert isinstance(data, dict)

    assert "status" in data
    assert "accepted" in data
    assert "diagnosis" in data
    assert "evidence" in data
    assert "unknowns" in data
    assert "verification_steps" in data
    assert "retrieved_projects" in data
    assert "validator" in data
    assert "limitations" in data