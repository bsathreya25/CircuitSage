"""
CircuitSage reasoning pipeline.

Gemma is an optional reasoning layer.

Deterministic validator evidence remains authoritative.

If deterministic validation reports UNKNOWN, the pipeline does not
allow the language model to reinterpret that uncertainty as a
confirmed malfunction.

If Gemma fails validation or is unavailable, deterministic reasoning
is used as the authoritative fallback.
"""

from typing import Any, Dict, List

from diagnostics.gemma_reasoner import reason_from_evidence
from diagnostics.reasoning_output_validator import validate_reasoning_output


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


def _validator_status(package) -> str:
    """Safely extract the deterministic validator status."""

    validator_result = package.validator_result or {}

    status = validator_result.get(
        "overall_status",
        "UNKNOWN",
    )

    if not isinstance(status, str):
        return "UNKNOWN"

    status = status.upper().strip()

    if status not in {"PASS", "FAIL", "UNKNOWN"}:
        return "UNKNOWN"

    return status


def _validator_checks(package) -> List[Dict[str, Any]]:
    """Safely retrieve deterministic validator checks."""

    validator_result = package.validator_result or {}

    checks = validator_result.get(
        "checks",
        [],
    )

    if not isinstance(checks, list):
        return []

    return [
        check
        for check in checks
        if isinstance(check, dict)
    ]


def _format_validator_evidence(package) -> List[str]:
    """Convert deterministic checks into concise evidence statements."""

    evidence = []

    for check in _validator_checks(package):
        check_id = check.get("check_id", "")
        name = check.get("name", "")
        status = check.get("status", "")
        check_evidence = check.get("evidence", "")

        if check_evidence:
            evidence.append(
                f"{check_id} {status} — {name}: {check_evidence}"
            )
        else:
            evidence.append(
                f"{check_id} {status} — {name}"
            )

    return evidence[:3]


def _format_unknowns(package) -> List[str]:
    """Return known unknowns in a compact form."""

    unknowns = package.known_unknowns or []

    if not isinstance(unknowns, list):
        return []

    return [
        str(item)
        for item in unknowns[:3]
    ]


def _deterministic_reasoning(package) -> str:
    """
    Generate conservative reasoning directly from deterministic
    evidence.

    This function never invents a physical hardware observation.
    """

    status = _validator_status(package)

    evidence = _format_validator_evidence(package)
    unknowns = _format_unknowns(package)

    # ------------------------------------------------------------
    # CONFIRMED ISSUE
    # ------------------------------------------------------------

    if status == "FAIL":
        failed_checks = [
            check
            for check in _validator_checks(package)
            if check.get("status") == "FAIL"
        ]

        if failed_checks:
            issue_names = [
                str(
                    check.get(
                        "name",
                        check.get(
                            "check_id",
                            "deterministic validation check",
                        ),
                    )
                )
                for check in failed_checks[:3]
            ]

            confirmed_issue = (
                "A code-level issue was detected in deterministic "
                "validation: "
                + "; ".join(issue_names)
                + "."
            )
        else:
            confirmed_issue = (
                "A code-level issue was detected in deterministic "
                "validation."
            )

    else:
        confirmed_issue = NO_CONFIRMED_MALFUNCTION

    # ------------------------------------------------------------
    # CONFIRMED EVIDENCE
    # ------------------------------------------------------------

    if evidence:
        confirmed_evidence = "\n".join(
            f"- {item}"
            for item in evidence
        )
    else:
        confirmed_evidence = (
            "- No deterministic validator evidence was supplied."
        )

    # ------------------------------------------------------------
    # UNKNOWN INFORMATION
    # ------------------------------------------------------------

    if unknowns:
        unknown_information = "\n".join(
            f"- {item}"
            for item in unknowns
        )
    else:
        unknown_information = (
            "- Physical hardware behavior has not been established "
            "unless explicitly measured."
        )

    # ------------------------------------------------------------
    # POSSIBLE EXPLANATIONS
    # ------------------------------------------------------------

    if status == "FAIL":
        failed_checks = [
            check
            for check in _validator_checks(package)
            if check.get("status") == "FAIL"
        ]

        explanations = []

        for check in failed_checks[:3]:
            name = check.get(
                "name",
                check.get(
                    "check_id",
                    "deterministic validation check",
                ),
            )

            explanations.append(
                "The code-level validation failure is associated "
                f"with {name}."
            )

        if explanations:
            possible_explanations = "\n".join(
                f"- {item}"
                for item in explanations
            )
        else:
            possible_explanations = (
                f"- {INSUFFICIENT_EVIDENCE}"
            )

    else:
        possible_explanations = (
            f"- {INSUFFICIENT_EVIDENCE}"
        )

    # ------------------------------------------------------------
    # POTENTIAL CONSEQUENCES
    # ------------------------------------------------------------

    if status == "FAIL":
        potential_consequences = (
            "- The failed code-level condition may prevent the "
            "corresponding firmware behavior from operating as intended."
        )
    else:
        potential_consequences = (
            "- No specific consequence has been established from "
            "the available evidence."
        )

    # ------------------------------------------------------------
    # NEXT ENGINEERING VERIFICATION
    # ------------------------------------------------------------

    if status == "FAIL":
        verification_steps = [
            "Correct the identified code-level condition and rerun "
            "the deterministic validator.",
            "Verify the physical circuit wiring and connections "
            "directly, because source-code validation does not "
            "establish physical wiring.",
            "Capture Serial Monitor output or measured behavior "
            "after the correction.",
        ]

    elif status == "UNKNOWN":
        verification_steps = [
            "Provide the missing source-code evidence needed to "
            "complete the deterministic validation.",
            "Verify the physical circuit wiring and connections "
            "directly, because source-code validation does not "
            "establish physical wiring.",
            "Capture Serial Monitor output or measured behavior "
            "to generate new diagnostic evidence.",
        ]

    else:
        verification_steps = [
            "Verify the physical circuit wiring and connections "
            "directly, because source-code validation does not "
            "establish physical wiring.",
            "Capture Serial Monitor output or measured behavior "
            "to generate new diagnostic evidence.",
            "Test the system under a known physical condition.",
        ]

    next_verification = "\n".join(
        f"- {step}"
        for step in verification_steps
    )

    return (
        f"{SECTION_1}\n"
        f"{confirmed_issue}\n\n"
        f"{SECTION_2}\n"
        f"{confirmed_evidence}\n\n"
        f"{SECTION_3}\n"
        f"{unknown_information}\n\n"
        f"{SECTION_4}\n"
        f"{possible_explanations}\n\n"
        f"{SECTION_5}\n"
        f"{potential_consequences}\n\n"
        f"{SECTION_6}\n"
        f"{next_verification}"
    )


def _validate_reasoning(
    diagnosis: str,
    validator_status: str,
) -> Dict[str, Any]:
    """Validate the six-section human-readable reasoning output."""

    try:
        return validate_reasoning_output(
            diagnosis,
            validator_status,
        )
    except Exception as exc:
        return {
            "valid": False,
            "error": str(exc),
        }


def _render_structured_reasoning(
    result: Dict[str, Any],
) -> str:
    """
    Convert structured Gemma fields into CircuitSage's six-section
    human-readable diagnosis.
    """

    confirmed_issue = str(
        result.get(
            "confirmed_issue",
            NO_CONFIRMED_MALFUNCTION,
        )
    ).strip()

    if not confirmed_issue:
        confirmed_issue = NO_CONFIRMED_MALFUNCTION

    confirmed_evidence = result.get(
        "confirmed_evidence",
        [],
    )

    unknown_information = result.get(
        "unknown_information",
        [],
    )

    possible_explanations = result.get(
        "possible_explanations",
        [],
    )

    potential_consequences = result.get(
        "potential_consequences",
        [],
    )

    next_engineering_verification = result.get(
        "next_engineering_verification",
        [],
    )

    def render_items(items: Any) -> str:
        if not isinstance(items, list) or not items:
            return "- None established."

        return "\n".join(
            f"- {str(item)}"
            for item in items[:3]
        )

    return (
        f"{SECTION_1}\n"
        f"{confirmed_issue}\n\n"
        f"{SECTION_2}\n"
        f"{render_items(confirmed_evidence)}\n\n"
        f"{SECTION_3}\n"
        f"{render_items(unknown_information)}\n\n"
        f"{SECTION_4}\n"
        f"{render_items(possible_explanations)}\n\n"
        f"{SECTION_5}\n"
        f"{render_items(potential_consequences)}\n\n"
        f"{SECTION_6}\n"
        f"{render_items(next_engineering_verification)}"
    )


def _build_result(
    diagnosis: str,
    accepted: bool,
    reasoning_source: str,
    gemma_reasoning: Any = None,
    gemma_error: Any = None,
    validation: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build the stable reasoning-pipeline response contract.

    IMPORTANT:
    The test/API contract expects Gemma failure information under
    the key `gemma_error`.
    """

    result = {
        "diagnosis": diagnosis,
        "accepted": accepted,
        "reasoning_source": reasoning_source,
        "gemma_reasoning": gemma_reasoning,
        "gemma_error": gemma_error,
    }

    if validation is not None:
        result["validation"] = validation

    return result


def run_reasoning_pipeline(package) -> Dict[str, Any]:
    """
    Run the CircuitSage reasoning pipeline.

    Deterministic validator status is authoritative.

    UNKNOWN is handled deterministically before Gemma is called.
    This prevents an LLM from converting missing evidence into a
    confirmed engineering failure.

    PASS and FAIL may use Gemma, subject to the normal reasoning
    validation contract.
    """

    validator_status = _validator_status(package)

    # ============================================================
    # UNKNOWN — deterministic safety boundary
    # ============================================================

    if validator_status == "UNKNOWN":
        deterministic_diagnosis = _deterministic_reasoning(
            package
        )

        deterministic_validation = _validate_reasoning(
            deterministic_diagnosis,
            validator_status,
        )

        return _build_result(
            diagnosis=deterministic_diagnosis,
            accepted=deterministic_validation.get("valid", False),
            reasoning_source="deterministic",
            gemma_reasoning=None,
            gemma_error=(
                "Gemma reasoning skipped because deterministic "
                "validation status is UNKNOWN."
            ),
            validation=deterministic_validation,
        )

    gemma_reasoning = None
    gemma_error = None

    # ============================================================
    # GEMMA
    # ============================================================

    try:
        gemma_result = reason_from_evidence(package)

        gemma_reasoning = gemma_result

        if isinstance(gemma_result, dict):

            diagnosis = gemma_result.get("diagnosis")

            if not isinstance(diagnosis, str) or not diagnosis.strip():
                diagnosis = _render_structured_reasoning(
                    gemma_result
                )

            validation = _validate_reasoning(
                diagnosis,
                validator_status,
            )

            if validation.get("valid", False):
                return _build_result(
                    diagnosis=diagnosis,
                    accepted=True,
                    reasoning_source="gemma",
                    gemma_reasoning=gemma_result,
                    gemma_error=None,
                    validation=validation,
                )

            gemma_error = (
                "Gemma reasoning did not pass CircuitSage validation."
            )

        elif isinstance(gemma_result, str):

            diagnosis = gemma_result

            validation = _validate_reasoning(
                diagnosis,
                validator_status,
            )

            if validation.get("valid", False):
                return _build_result(
                    diagnosis=diagnosis,
                    accepted=True,
                    reasoning_source="gemma",
                    gemma_reasoning=gemma_result,
                    gemma_error=None,
                    validation=validation,
                )

            gemma_error = (
                "Gemma reasoning did not pass CircuitSage validation."
            )

        else:
            gemma_error = (
                "Gemma reasoning returned an unsupported result type."
            )

    except Exception as exc:
        gemma_error = str(exc)
        gemma_reasoning = None

    # ============================================================
    # DETERMINISTIC FALLBACK
    # ============================================================

    deterministic_diagnosis = _deterministic_reasoning(
        package
    )

    deterministic_validation = _validate_reasoning(
        deterministic_diagnosis,
        validator_status,
    )

    if deterministic_validation.get("valid", False):
        return _build_result(
            diagnosis=deterministic_diagnosis,
            accepted=True,
            reasoning_source="deterministic",
            gemma_reasoning=None,
            gemma_error=gemma_error,
            validation=deterministic_validation,
        )

    # ============================================================
    # DEFENSIVE FINAL RESULT
    # ============================================================

    return _build_result(
        diagnosis=deterministic_diagnosis,
        accepted=False,
        reasoning_source="deterministic",
        gemma_reasoning=None,
        gemma_error=gemma_error,
        validation=deterministic_validation,
    )