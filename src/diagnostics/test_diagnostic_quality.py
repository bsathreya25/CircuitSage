from diagnostics.engine import CircuitSageEngine
from diagnostics.validators import run_hcsr04_validator
from api.models import DiagnosticRequest


HEALTHY_HCSR04 = """
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


BROKEN_HCSR04 = """
int trigPin = 11;
int echoPin = 12;

void setup() {
    Serial.begin(9600);
    pinMode(trigPin, INPUT);
    pinMode(echoPin, OUTPUT);
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


INCOMPLETE_HCSR04 = """
int trigPin = 11;
int echoPin = 12;

void setup() {
    pinMode(trigPin, OUTPUT);
}

void loop() {
}
"""


def test_healthy_hcsr04_produces_pass():
    result = run_hcsr04_validator(
        HEALTHY_HCSR04,
        source_file="healthy_hcsr04.ino",
    )

    assert result.overall_status() == "PASS"
    assert result.passed == 8
    assert result.failed == 0
    assert result.unknown == 0


def test_broken_hcsr04_produces_explicit_failures():
    result = run_hcsr04_validator(
        BROKEN_HCSR04,
        source_file="broken_hcsr04.ino",
    )

    assert result.overall_status() == "FAIL"
    assert result.failed == 2

    failed_checks = {
        check.name
        for check in result.checks
        if check.status == "FAIL"
    }

    assert "TRIG configured OUTPUT" in failed_checks
    assert "ECHO configured INPUT" in failed_checks


def test_incomplete_hcsr04_remains_unknown():
    result = run_hcsr04_validator(
        INCOMPLETE_HCSR04,
        source_file="incomplete_hcsr04.ino",
    )

    assert result.overall_status() == "UNKNOWN"
    assert result.failed == 0
    assert result.unknown > 0


def test_broken_hcsr04_engine_reports_code_level_issue():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="My HC-SR04 distance readings are incorrect.",
            code=BROKEN_HCSR04,
        )
    )

    assert response.status == "SUPPORTED"
    assert response.accepted is True
    assert response.validator["overall_status"] == "FAIL"

    assert "incorrectly configured" in response.diagnosis.lower()
    assert "input" in response.diagnosis.lower()
    assert "output" in response.diagnosis.lower()


def test_incomplete_hcsr04_does_not_confirm_malfunction():
    engine = CircuitSageEngine()

    response = engine.diagnose(
        DiagnosticRequest(
            problem_description="My HC-SR04 distance readings are incorrect.",
            code=INCOMPLETE_HCSR04,
        )
    )

    assert response.status == "SUPPORTED"
    assert response.accepted is True
    assert response.validator["overall_status"] == "UNKNOWN"

    assert (
        "No confirmed malfunction has been established"
        in response.diagnosis
    )