from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RECORDS_FILE = (
    PROJECT_ROOT
    / "knowledge_base"
    / "canonical_records.json"
)


def load_records():
    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_coverage(records):
    components = set()
    interfaces = set()

    for record in records:
        for component in record.get("components", []):
            components.add(component.lower())

        for interface, enabled in record.get(
            "interfaces",
            {},
        ).items():
            if enabled:
                interfaces.add(interface.lower())

    return {
        "components": sorted(components),
        "interfaces": sorted(interfaces),
    }


def evaluate_scope(
    query,
    retrieval_results,
    coverage,
    evidence_context=None,
):
    """
    Determine whether CircuitSage has enough evidence
    to enter the diagnostic pipeline.

    Important distinction:

        Retrieval evidence
            !=
        Diagnostic evidence

    A strong corpus match means CircuitSage knows about
    the component/problem domain. It does not, by itself,
    prove that enough user evidence exists to diagnose it.

    V1.0 diagnostic evidence currently includes:
        - user-supplied Arduino source code
        - user-supplied Serial Monitor output

    The deterministic HC-SR04 validator requires code,
    so an HC-SR04 request without code remains
    INSUFFICIENT_EVIDENCE even when retrieval is strong.
    """

    if evidence_context is None:
        evidence_context = {}

    query_normalized = query.strip().lower()

    has_code = bool(
        evidence_context.get("code")
    )

    has_serial_output = bool(
        evidence_context.get("serial_output")
    )

    # --------------------------------------------------
    # No retrieval evidence
    # --------------------------------------------------

    if not retrieval_results:
        return {
            "status": "UNSUPPORTED",
            "reason": (
                "No matching evidence was found in the "
                "CircuitSage V1.0 canonical corpus."
            ),
            "query": query,
            "candidate_projects": [],
        }

    # --------------------------------------------------
    # Determine evidence strength
    # --------------------------------------------------

    candidates = []

    for project_id, result in retrieval_results.items():
        score = result.get("score", 0)

        if score >= 10:
            evidence_level = "HIGH"

        elif score >= 5:
            evidence_level = "MEDIUM"

        else:
            evidence_level = "LOW"

        candidates.append(
            {
                "project_id": project_id,
                "score": score,
                "evidence_level": evidence_level,
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["score"],
            int(item["project_id"]),
        )
    )

    highest_score = candidates[0]["score"]

    # --------------------------------------------------
    # Strong retrieval exists, but diagnostic evidence
    # has not been supplied.
    #
    # This is the critical distinction between:
    #
    #   "CircuitSage knows this component"
    #
    # and:
    #
    #   "CircuitSage has enough evidence to diagnose it."
    # --------------------------------------------------

    if highest_score >= 10:
        if not has_code and not has_serial_output:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": (
                    "The requested component or scenario is "
                    "supported by the canonical corpus, but "
                    "no diagnostic evidence was supplied."
                ),
                "query": query,
                "candidate_projects": candidates,
            }

        return {
            "status": "SUPPORTED",
            "reason": (
                "Relevant canonical projects contain strong "
                "indexed evidence and diagnostic evidence was "
                "supplied with the request."
            ),
            "query": query,
            "candidate_projects": candidates,
        }

    # --------------------------------------------------
    # Relevant but weak retrieval evidence
    # --------------------------------------------------

    return {
        "status": "INSUFFICIENT_EVIDENCE",
        "reason": (
            "Related canonical projects were found, "
            "but the strongest indexed evidence is "
            "not sufficient for a confident diagnostic."
        ),
        "query": query,
        "candidate_projects": candidates,
    }


def main():
    records = load_records()

    coverage = build_coverage(records)

    print("CIRCUITSAGE V1.0 COVERAGE")
    print("=" * 50)

    print(
        "Known component entries:",
        len(coverage["components"]),
    )

    print(
        "Known interface entries:",
        len(coverage["interfaces"]),
    )

    print()

    print("Components:")

    for component in coverage["components"]:
        print(" -", component)

    print()

    print("Interfaces:")

    for interface in coverage["interfaces"]:
        print(" -", interface)


if __name__ == "__main__":
    main()