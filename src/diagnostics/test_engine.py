from api.models import DiagnosticRequest

from diagnostics.engine import (
    CircuitSageEngine,
)


def test_engine_retrieves_hcsr04():
    engine = CircuitSageEngine()

    retrieval = engine.retrieve(
        "HC-SR04 ultrasonic sensor"
    )

    assert retrieval["results"]

    project_ids = [
        result["project_id"]
        for result in retrieval["results"]
    ]

    assert "8" in project_ids


def test_engine_identifies_hcsr04():
    engine = CircuitSageEngine()

    retrieval = engine.retrieve(
        "HC-SR04 ultrasonic sensor"
    )

    component = engine.identify_component(
        "HC-SR04 ultrasonic sensor",
        retrieval["results"],
    )

    assert component == "HC-SR04"


def test_engine_runs_hcsr04_validator():
    engine = CircuitSageEngine()

    code = """
int trigPin = 11;
int echoPin = 12;

void setup() {
    Serial.begin(9600);
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);
}

void loop() {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(5);

    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);

    digitalWrite(trigPin, LOW);

    long duration = pulseIn(echoPin, HIGH);

    int cm = (duration / 2) / 29.1;

    Serial.println(cm);

    delay(250);
}
"""

    result = engine.run_deterministic_validation(
        component="HC-SR04",
        code=code,
        project_name="test_hcsr04.ino",
    )

    assert result is not None
    assert result["validator_id"] == "hcsr04_v1"
    assert result["overall_status"] == "PASS"
    assert result["summary"]["passed"] == 8


def test_engine_handles_supported_validator_with_insufficient_evidence():
    engine = CircuitSageEngine()

    result = engine.run_deterministic_validation(
        component="DHT11",
        code="Serial.println(temperature);",
    )

    assert result is not None
    assert result["validator_id"] == "dht_v1"
    assert result["overall_status"] == "UNKNOWN"
    assert result["summary"]["failed"] == 0
    assert result["summary"]["unknown"] > 0


def test_engine_rejects_empty_problem():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="",
        )
    )

    assert response.status == "INVALID_REQUEST"
    assert response.accepted is True