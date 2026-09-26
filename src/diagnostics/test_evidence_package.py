from evidence_package import EvidencePackage


def test_evidence_package_contains_core_fields():
    package = EvidencePackage(
        user_query="HC-SR04 is not detecting distance",
        scope_status="SUPPORTED",
        component="HC-SR04",
    )

    data = package.to_json_ready()

    assert data["user_query"] == "HC-SR04 is not detecting distance"
    assert data["scope_status"] == "SUPPORTED"
    assert data["component"] == "HC-SR04"

    assert data["retrieved_projects"] == []
    assert data["schematic_evidence"] == []
    assert data["engineering_parameters"] == {}
    assert data["known_unknowns"] == []


def test_validator_result_can_be_attached():
    validator = {
        "validator_id": "hcsr04_v1",
        "component": "HC-SR04",
        "overall_status": "PASS",
        "summary": {
            "total": 8,
            "passed": 8,
            "failed": 0,
            "unknown": 0,
        },
    }

    package = EvidencePackage(
        user_query="HC-SR04 is not detecting distance",
        scope_status="SUPPORTED",
        component="HC-SR04",
        validator_result=validator,
    )

    data = package.to_json_ready()

    assert data["validator_result"]["validator_id"] == "hcsr04_v1"
    assert data["validator_result"]["overall_status"] == "PASS"
    assert data["validator_result"]["summary"]["passed"] == 8


def test_unknown_information_is_preserved():
    package = EvidencePackage(
        user_query="HC-SR04 is not detecting distance",
        scope_status="SUPPORTED",
        component="HC-SR04",
        known_unknowns=[
            "Physical wiring has not been inspected.",
            "Actual sensor response is unknown.",
        ],
    )

    data = package.to_json_ready()

    assert len(data["known_unknowns"]) == 2
    assert "Physical wiring has not been inspected." in data["known_unknowns"]
