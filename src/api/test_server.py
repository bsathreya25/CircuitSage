from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "CircuitSage API"
    assert data["version"] == "1.0.0"


def test_empty_problem_is_rejected():
    response = client.post(
        "/diagnose",
        json={
            "problem_description": "",
        },
    )

    assert response.status_code == 422


def test_missing_problem_is_rejected():
    response = client.post(
        "/diagnose",
        json={
            "code": "void setup() {}",
        },
    )

    assert response.status_code == 422


def test_unsupported_request_is_safe():
    response = client.post(
        "/diagnose",
        json={
            "problem_description": "My XYZ12345 quantum flux component is broken.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in {
        "UNSUPPORTED",
        "INSUFFICIENT_EVIDENCE",
    }

    assert "diagnosis" in data
    assert "limitations" in data


def test_diagnose_response_contract():
    response = client.post(
        "/diagnose",
        json={
            "problem_description": (
                "My HC-SR04 ultrasonic sensor is not giving "
                "the expected distance reading."
            ),
            "code": """
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
    long cm = (duration / 2) / 29.1;

    Serial.println(cm);
    delay(250);
}
""",
            "project_name": "test_hcsr04.ino",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUPPORTED"
    assert data["accepted"] is True
    assert data["component"] == "HC-SR04"

    assert data["validator"]["validator_id"] == "hcsr04_v1"
    assert data["validator"]["overall_status"] == "PASS"

    assert data["validator"]["summary"]["passed"] == 8
    assert data["validator"]["summary"]["failed"] == 0
    assert data["validator"]["summary"]["unknown"] == 0

    assert isinstance(data["diagnosis"], str)
    assert data["diagnosis"]

    assert isinstance(data["evidence"], list)
    assert isinstance(data["unknowns"], list)
    assert isinstance(data["limitations"], list)


def test_invalid_json_shape_is_rejected():
    response = client.post(
        "/diagnose",
        json={
            "problem_description": 12345,
        },
    )

    assert response.status_code == 422