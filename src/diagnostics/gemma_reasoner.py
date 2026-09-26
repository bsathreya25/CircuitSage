"""
Gemma reasoning layer for CircuitSage.

Responsibilities:
1. Build an evidence-constrained prompt.
2. Call the local Ollama/Gemma model.
3. Parse and validate structured JSON.
4. Render structured reasoning into CircuitSage's six-section format.
"""

import json
from typing import Any, Dict

from ollama_client import ask_local_model


REQUIRED_KEYS = {
    "confirmed_issue",
    "confirmed_evidence",
    "unknown_information",
    "possible_explanations",
    "potential_consequences",
    "next_engineering_verification",
}

LIST_FIELDS = {
    "confirmed_evidence",
    "unknown_information",
    "possible_explanations",
    "potential_consequences",
    "next_engineering_verification",
}


SECTION_1 = "1. CONFIRMED ISSUE"
SECTION_2 = "2. CONFIRMED EVIDENCE"
SECTION_3 = "3. UNKNOWN INFORMATION"
SECTION_4 = "4. POSSIBLE EXPLANATIONS"
SECTION_5 = "5. POTENTIAL CONSEQUENCES"
SECTION_6 = "6. NEXT ENGINEERING VERIFICATION"

NO_CONFIRMED_MALFUNCTION = (
    "No confirmed malfunction has been established from the available evidence."
)

INSUFFICIENT_EVIDENCE = (
    "Insufficient evidence to identify a specific technical cause."
)


def build_reasoning_prompt(package) -> str:
    """
    Build the evidence-constrained Gemma reasoning prompt.
    """

    retrieved_projects = package.retrieved_projects or []
    validator_result = package.validator_result or {}
    schematic_evidence = package.schematic_evidence or []
    engineering_parameters = package.engineering_parameters or {}
    known_unknowns = package.known_unknowns or []

    prompt = f"""
CIRCUITSAGE ENGINEERING REASONING TASK
==========================================

You are the reasoning layer of CircuitSage, an engineering diagnostic
system for embedded systems.

Reason ONLY from the evidence supplied below.

Do not invent measurements, observations, wiring, hardware failures,
sensor behavior, or experimental results.

EVIDENCE PACKAGE
----------------

USER PROBLEM REPORT:
{package.user_query}

SCOPE STATUS:
{package.scope_status}

COMPONENT:
{package.component or "UNKNOWN"}

RETRIEVED PROJECTS:
{json.dumps(retrieved_projects, indent=2, default=str)}

DETERMINISTIC VALIDATOR RESULT:
{json.dumps(validator_result, indent=2, default=str)}

SCHEMATIC EVIDENCE:
{json.dumps(schematic_evidence, indent=2, default=str)}

ENGINEERING PARAMETERS:
{json.dumps(engineering_parameters, indent=2, default=str)}

KNOWN / UNKNOWN INFORMATION:
{json.dumps(known_unknowns, indent=2, default=str)}


REASONING RULES
---------------

1. Deterministic engineering evidence has higher authority than the
   user's interpretation.

2. UNKNOWN is not FAILURE.

3. Never invent physical measurements.

4. Never invent physical observations.

5. Never invent hardware faults.

6. Never infer physical wiring unless explicit schematic evidence
   establishes it.

7. If the deterministic validator reports PASS for a condition,
   do not describe that same condition as a confirmed failure.

8. If the deterministic validator reports FAIL, describe the failed
   check using the supplied evidence only.

9. If the deterministic validator reports UNKNOWN, preserve UNKNOWN.
   Do not convert UNKNOWN into FAILURE.

10. Static source-code analysis does not prove physical hardware
    behavior.

11. If evidence is insufficient to identify a specific technical
    cause, explicitly state that it is insufficient.

12. Do not recommend unnecessary hardware replacement.

13. Do not fabricate test results.

14. Stay within CircuitSage's supported diagnostic scope.

15. Never treat the user problem report as proof of a malfunction.

16. The user's problem description describes what the user reports.
    It is not, by itself, proof that a physical fault exists.


OUTPUT REQUIREMENTS
-------------------

Return ONLY a JSON object.

The JSON object MUST contain exactly these keys:

{{
  "confirmed_issue": "...",
  "confirmed_evidence": ["..."],
  "unknown_information": ["..."],
  "possible_explanations": ["..."],
  "potential_consequences": ["..."],
  "next_engineering_verification": ["..."]
}}

Return ONLY those six keys.

Do NOT add any other keys.

Field requirements:

- "confirmed_issue" must be a string.
- "confirmed_evidence" must be a list of strings.
- "unknown_information" must be a list of strings.
- "possible_explanations" must be a list of strings.
- "potential_consequences" must be a list of strings.
- "next_engineering_verification" must be a list of strings.

Maximum 3 items in confirmed_evidence.
Maximum 3 items in unknown_information.
Maximum 3 items in possible_explanations.
Maximum 3 items in potential_consequences.
Maximum 3 items in next_engineering_verification.

Do not return Markdown.
Do not return a code fence.
Do not return explanatory text outside the JSON object.
"""

    return prompt.strip()


def parse_reasoning_json(raw_response: str) -> Dict[str, Any]:
    """
    Parse and strictly validate Gemma's JSON response.
    """

    if not isinstance(raw_response, str):
        raise ValueError("Reasoning response must be a string.")

    text = raw_response.strip()

    if not text:
        raise ValueError("Reasoning response is empty.")

    # Handle accidental Markdown code fences.
    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Reasoning output is not valid JSON: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(
            "Reasoning output must be a JSON object."
        )

    actual_keys = set(parsed.keys())

    missing_keys = REQUIRED_KEYS - actual_keys

    if missing_keys:
        raise ValueError(
            "Reasoning output is missing required keys: "
            + ", ".join(sorted(missing_keys))
        )

    unexpected_keys = actual_keys - REQUIRED_KEYS

    if unexpected_keys:
        raise ValueError(
            "Reasoning output contains unexpected keys: "
            + ", ".join(sorted(unexpected_keys))
        )

    if not isinstance(parsed["confirmed_issue"], str):
        raise ValueError(
            '"confirmed_issue" must be a string.'
        )

    for field in LIST_FIELDS:
        value = parsed[field]

        if not isinstance(value, list):
            raise ValueError(
                f'"{field}" must be a list.'
            )

        if not all(isinstance(item, str) for item in value):
            raise ValueError(
                f'"{field}" must contain only strings.'
            )

        if len(value) > 3:
            raise ValueError(
                f'"{field}" may contain at most 3 items.'
            )

    return parsed


def _render_list(value: Any) -> str:
    """
    Render a structured reasoning field as bullet points.
    """

    if not isinstance(value, list) or not value:
        return "- None established."

    return "\n".join(
        f"- {str(item)}"
        for item in value[:3]
    )


def render_reasoning_sections(reasoning: Dict[str, Any]) -> str:
    """
    Convert structured reasoning JSON into CircuitSage's required
    six-section human-readable format.

    This function is intentionally public because the structured-output
    tests and the reasoning pipeline use it as the rendering boundary.
    """

    if not isinstance(reasoning, dict):
        raise ValueError(
            "Reasoning must be a dictionary."
        )

    confirmed_issue = str(
        reasoning.get(
            "confirmed_issue",
            NO_CONFIRMED_MALFUNCTION,
        )
    ).strip()

    if not confirmed_issue:
        confirmed_issue = NO_CONFIRMED_MALFUNCTION

    return (
        f"{SECTION_1}\n"
        f"{confirmed_issue}\n\n"
        f"{SECTION_2}\n"
        f"{_render_list(reasoning.get('confirmed_evidence', []))}\n\n"
        f"{SECTION_3}\n"
        f"{_render_list(reasoning.get('unknown_information', []))}\n\n"
        f"{SECTION_4}\n"
        f"{_render_list(reasoning.get('possible_explanations', []))}\n\n"
        f"{SECTION_5}\n"
        f"{_render_list(reasoning.get('potential_consequences', []))}\n\n"
        f"{SECTION_6}\n"
        f"{_render_list(reasoning.get('next_engineering_verification', []))}"
    )


def reason_from_evidence(package) -> Dict[str, Any]:
    """
    Ask local Gemma to reason over the EvidencePackage.

    Returns the validated structured reasoning dictionary.

    Malformed output raises an exception so the reasoning pipeline
    can safely fall back to deterministic reasoning.
    """

    prompt = build_reasoning_prompt(package)

    raw_response = ask_local_model(prompt)

    return parse_reasoning_json(raw_response)