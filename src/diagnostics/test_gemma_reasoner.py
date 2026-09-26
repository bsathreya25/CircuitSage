from evidence_package import EvidencePackage
from gemma_reasoner import build_reasoning_prompt


def test_prompt_contains_evidence_package():
    package = EvidencePackage(
        user_query="HC-SR04 gives no distance",
        scope_status="SUPPORTED",
        component="HC-SR04",
        retrieved_projects=[{"project_id": 8, "score": 20}],
    )

    prompt = build_reasoning_prompt(package)

    assert "HC-SR04 gives no distance" in prompt
    assert "SUPPORTED" in prompt
    assert "HC-SR04" in prompt


def test_prompt_contains_reasoning_rules():
    package = EvidencePackage(
        user_query="Test query",
        scope_status="SUPPORTED",
    )

    prompt = build_reasoning_prompt(package)

    assert "UNKNOWN is not FAILURE" in prompt
    assert "Never invent physical measurements" in prompt
    assert "Never treat the user problem report as proof of a malfunction" in prompt


def test_prompt_requires_structured_reasoning_fields():
    package = EvidencePackage(
        user_query="Test query",
        scope_status="SUPPORTED",
    )

    prompt = build_reasoning_prompt(package)

    required_fields = [
        '"confirmed_issue"',
        '"confirmed_evidence"',
        '"unknown_information"',
        '"possible_explanations"',
        '"potential_consequences"',
        '"next_engineering_verification"',
    ]

    for field in required_fields:
        assert field in prompt

    assert "Return ONLY a JSON object." in prompt
    assert "Do NOT add any other keys." in prompt