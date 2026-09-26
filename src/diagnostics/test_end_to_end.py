from pathlib import Path

from api.models import DiagnosticRequest
from diagnostics.engine import CircuitSageEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]

HC_SR04_CODE = (
    PROJECT_ROOT
    / "data"
    / "Ultrasonic_Sensor_HC-SR04"
    / "Ultrasonic_Sensor_HC-SR04.ino"
)


def test_real_hcsr04_end_to_end():
    code = HC_SR04_CODE.read_text(encoding="utf-8")

    engine = CircuitSageEngine()

    request = DiagnosticRequest(
        problem_description=(
            "My HC-SR04 ultrasonic sensor is not giving "
            "the expected distance reading."
        ),
        code=code,
        project_name="Ultrasonic_Sensor_HC-SR04.ino",
    )

    response = engine.diagnose(request)

    print("\n=== CIRCUITSAGE END-TO-END RESULT ===")
    print("Status:", response.status)
    print("Accepted:", response.accepted)
    print("Component:", response.component)
    print("Validator:", response.validator)
    print("Limitations:", response.limitations)
    print("\nDiagnosis:")
    print(response.diagnosis)

    assert response.status == "SUPPORTED"
    assert response.component == "HC-SR04"

    assert response.validator
    assert response.validator["validator_id"] == "hcsr04_v1"
    assert response.validator["overall_status"] == "PASS"

    assert response.validator["summary"]["passed"] == 8
    assert response.validator["summary"]["failed"] == 0
    assert response.validator["summary"]["unknown"] == 0

    assert response.diagnosis

    assert len(response.evidence) > 0
    assert len(response.unknowns) > 0