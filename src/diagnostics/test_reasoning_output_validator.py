from reasoning_output_validator import validate_reasoning_output


VALID_RESPONSE = """
1. CONFIRMED ISSUE
No confirmed malfunction has been established from the available evidence.

2. CONFIRMED EVIDENCE
The deterministic validator passed all eight HC-SR04 code checks.

3. UNKNOWN INFORMATION
Physical wiring and physical sensor response are unknown.

4. POSSIBLE EXPLANATIONS
The available evidence is insufficient to identify a specific physical cause.

5. POTENTIAL CONSEQUENCES
The system may continue to produce unexpected readings if the physical issue remains unresolved.

6. NEXT ENGINEERING VERIFICATION
Verify physical wiring and observe the Serial Monitor output.
"""


INVALID_SECTION_RESPONSE = """
1. CONFIRMED ISSUE
No confirmed malfunction has been established.

2. CONFIRMED EVIDENCE
All deterministic checks passed.

3. UNKNOWN INFORMATION
Physical behavior is unknown.

4. POSSIBLE EXPLANATIONS
Insufficient evidence.

5. POTENTIAL CONSEQUENCES
Unknown.

6. NEXT ENGINEERING VERIFICATION
Verify the hardware.

7. EXTRA SECTION
This should not exist.
"""


INVALID_MALFUNCTION_RESPONSE = """
1. CONFIRMED ISSUE
The sensor is not working and has a confirmed malfunction.

2. CONFIRMED EVIDENCE
All deterministic checks passed.

3. UNKNOWN INFORMATION
Physical behavior is unknown.

4. POSSIBLE EXPLANATIONS
Unknown.

5. POTENTIAL CONSEQUENCES
Unexpected readings.

6. NEXT ENGINEERING VERIFICATION
Check the hardware.
"""


INVALID_USER_COMPLAINT_RESPONSE = """
1. CONFIRMED ISSUE
The HC-SR04 ultrasonic sensor is not giving the expected distance reading.

2. CONFIRMED EVIDENCE
All deterministic checks passed.

3. UNKNOWN INFORMATION
Physical wiring and physical sensor response are unknown.

4. POSSIBLE EXPLANATIONS
Insufficient evidence to identify a specific physical cause.

5. POTENTIAL CONSEQUENCES
Unexpected readings may continue.

6. NEXT ENGINEERING VERIFICATION
Verify the physical wiring.
"""


def test_valid_response():
    result = validate_reasoning_output(
        VALID_RESPONSE,
        "PASS",
    )

    assert result["valid"] is True


def test_extra_section_is_rejected():
    result = validate_reasoning_output(
        INVALID_SECTION_RESPONSE,
        "PASS",
    )

    assert result["valid"] is False
    assert result["structure"]["unexpected_sections"]


def test_unsupported_confirmed_malfunction_is_rejected():
    result = validate_reasoning_output(
        INVALID_MALFUNCTION_RESPONSE,
        "PASS",
    )

    assert result["valid"] is False
    assert result["malfunction_check"]["valid"] is False


def test_user_complaint_must_not_be_presented_as_confirmed_issue():
    result = validate_reasoning_output(
        INVALID_USER_COMPLAINT_RESPONSE,
        "PASS",
    )

    assert result["valid"] is False
    assert result["malfunction_check"]["valid"] is False