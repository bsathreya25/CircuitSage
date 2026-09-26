from gemma_reasoner import (
    parse_reasoning_json,
    render_reasoning_sections,
)


def valid_payload():
    return {
        "confirmed_issue": (
            "No confirmed malfunction has been established "
            "from the available evidence."
        ),
        "confirmed_evidence": [
            "TRIG pin is configured as OUTPUT.",
            "ECHO pin is configured as INPUT.",
        ],
        "unknown_information": [
            "Physical wiring has not been verified.",
        ],
        "possible_explanations": [
            "Insufficient evidence to identify a specific technical cause."
        ],
        "potential_consequences": [
            "If the reported symptom persists, further verification is required."
        ],
        "next_engineering_verification": [
            "Verify the physical wiring.",
            "Check the actual Serial Monitor output.",
        ],
    }


def test_valid_structured_output_is_accepted():
    data = valid_payload()

    parsed = parse_reasoning_json(
        __import__("json").dumps(data)
    )

    assert parsed == data


def test_missing_field_is_rejected():
    data = valid_payload()
    del data["unknown_information"]

    try:
        parse_reasoning_json(__import__("json").dumps(data))
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "missing required keys" in str(error)


def test_extra_field_is_rejected():
    data = valid_payload()
    data["unexpected_field"] = "not allowed"

    try:
        parse_reasoning_json(__import__("json").dumps(data))
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "unexpected keys" in str(error)


def test_wrong_field_type_is_rejected():
    data = valid_payload()
    data["confirmed_evidence"] = "this must be a list"

    try:
        parse_reasoning_json(__import__("json").dumps(data))
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "must be a list" in str(error)


def test_renderer_always_produces_six_sections():
    rendered = render_reasoning_sections(valid_payload())

    required_sections = [
        "1. CONFIRMED ISSUE",
        "2. CONFIRMED EVIDENCE",
        "3. UNKNOWN INFORMATION",
        "4. POSSIBLE EXPLANATIONS",
        "5. POTENTIAL CONSEQUENCES",
        "6. NEXT ENGINEERING VERIFICATION",
    ]

    for section in required_sections:
        assert section in rendered

    assert rendered.index("1. CONFIRMED ISSUE") < \
        rendered.index("2. CONFIRMED EVIDENCE")

    assert rendered.index("2. CONFIRMED EVIDENCE") < \
        rendered.index("3. UNKNOWN INFORMATION")

    assert rendered.index("3. UNKNOWN INFORMATION") < \
        rendered.index("4. POSSIBLE EXPLANATIONS")

    assert rendered.index("4. POSSIBLE EXPLANATIONS") < \
        rendered.index("5. POTENTIAL CONSEQUENCES")

    assert rendered.index("5. POTENTIAL CONSEQUENCES") < \
        rendered.index("6. NEXT ENGINEERING VERIFICATION")