from typing import List, Dict


REQUIRED_SECTIONS = [
    "1. CONFIRMED ISSUE",
    "2. CONFIRMED EVIDENCE",
    "3. UNKNOWN INFORMATION",
    "4. POSSIBLE EXPLANATIONS",
    "5. POTENTIAL CONSEQUENCES",
    "6. NEXT ENGINEERING VERIFICATION",
]


def find_sections(text: str) -> List[str]:
    """
    Find CircuitSage's numbered section headings.

    The six headings are part of the CircuitSage output contract,
    so we look for those exact headings rather than trying to parse
    arbitrary numbered headings.
    """

    found = []

    for section in REQUIRED_SECTIONS:
        if section in text:
            found.append(section)

    return found


def validate_section_structure(text: str) -> Dict:
    """
    Validate that Gemma returned exactly the six required sections.
    """

    sections = find_sections(text)

    missing = [
        section
        for section in REQUIRED_SECTIONS
        if section not in sections
    ]

    unexpected = []

    lines = text.splitlines()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if ". " not in stripped:
            continue

        number_part, title_part = stripped.split(". ", 1)

        if not number_part.isdigit():
            continue

        candidate = f"{number_part}. {title_part.strip()}"

        if candidate not in REQUIRED_SECTIONS:
            unexpected.append(candidate)

    unexpected = list(dict.fromkeys(unexpected))

    correct_order = sections == REQUIRED_SECTIONS

    return {
        "valid": (
            not missing
            and not unexpected
            and correct_order
        ),
        "sections_found": sections,
        "missing_sections": missing,
        "unexpected_sections": unexpected,
        "correct_order": correct_order,
    }


def validate_no_confirmed_malfunction(
    text: str,
    validator_overall_status: str,
) -> Dict:
    """
    Prevent Gemma from presenting a user-reported symptom
    as a confirmed engineering malfunction when deterministic
    validation did not establish one.
    """

    # If deterministic validation actually established a failure,
    # confirmed failure statements are allowed.
    if validator_overall_status == "FAIL":
        return {
            "valid": True,
            "reason": "Deterministic validator established a failure.",
        }

    confirmed_issue_start = "1. CONFIRMED ISSUE"
    confirmed_evidence_start = "2. CONFIRMED EVIDENCE"

    start = text.find(confirmed_issue_start)

    if start == -1:
        return {
            "valid": False,
            "reason": "Could not locate the CONFIRMED ISSUE section.",
        }

    end = text.find(
        confirmed_evidence_start,
        start + len(confirmed_issue_start),
    )

    if end == -1:
        return {
            "valid": False,
            "reason": "Could not locate the CONFIRMED EVIDENCE section.",
        }

    confirmed_issue = text[
        start + len(confirmed_issue_start):end
    ].strip().lower()

    # --------------------------------------------------
    # Explicit negative statements are safe.
    # --------------------------------------------------

    negative_prefixes = [
        "no confirmed malfunction",
        "no confirmed failure",
        "no malfunction has been established",
        "no failure has been established",
        "not confirmed",
        "cannot be confirmed",
        "cannot confirm",
        "there is no confirmed malfunction",
        "there is no confirmed failure",
    ]

    for prefix in negative_prefixes:
        confirmed_issue = confirmed_issue.replace(
            prefix,
            "",
        )

    # --------------------------------------------------
    # Unsupported malfunction claims.
    #
    # We intentionally use broader fragments rather than
    # requiring an exact sentence, because a model may write:
    #
    # "The HC-SR04 ultrasonic sensor is not giving..."
    #
    # rather than:
    #
    # "The sensor is not giving..."
    # --------------------------------------------------

    forbidden_fragments = [
        "sensor is not working",
        "sensor is malfunctioning",
        "sensor has failed",
        "sensor is faulty",
        "sensor is defective",
        "sensor is not functioning",
        "sensor is not operating",

        "not giving the expected",
        "not producing the expected",
        "not providing the expected",

        "circuit is not working",
        "circuit has failed",
        "circuit is malfunctioning",

        "confirmed malfunction",
        "confirmed failure",
    ]

    detected = [
        fragment
        for fragment in forbidden_fragments
        if fragment in confirmed_issue
    ]

    if detected:
        return {
            "valid": False,
            "reason": (
                "Gemma presented an unsupported malfunction or "
                f"user-reported symptom as confirmed despite "
                f"deterministic status {validator_overall_status}: "
                f"{detected}"
            ),
        }

    return {
        "valid": True,
        "reason": "No unsupported confirmed malfunction detected.",
    }


def validate_reasoning_output(
    text: str,
    validator_overall_status: str,
) -> Dict:
    """
    Run all deterministic checks on Gemma's output.
    """

    structure = validate_section_structure(text)

    malfunction = validate_no_confirmed_malfunction(
        text,
        validator_overall_status,
    )

    return {
        "valid": structure["valid"] and malfunction["valid"],
        "structure": structure,
        "malfunction_check": malfunction,
    }