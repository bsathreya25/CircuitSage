from pathlib import Path
from typing import Any, Dict, List, Optional

from api.models import DiagnosticRequest, DiagnosticResponse

from search_retrieval import (
    load_json,
    expand_query,
    search,
    evidence_level,
    INDEX_FILE,
    VOCAB_FILE,
)

from retrieval.scope_gate import (
    load_records,
    build_coverage,
    evaluate_scope,
)

from diagnostics.evidence_package import EvidencePackage
from diagnostics.reasoning_pipeline import run_reasoning_pipeline
from diagnostics.multi_validators import get_deterministic_validator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


SUPPORTED_DETERMINISTIC_VALIDATORS = {
    "HC-SR04": "hcsr04_v1",
    "DHT11": "dht_v1",
    "DHT22": "dht_v1",
    "MPU6050": "mpu6050_v1",
    "nRF24L01": "nrf24_v1",
}


class CircuitSageEngine:
    """
    Unified CircuitSage V1.0 diagnostic engine.

    Pipeline:

        DiagnosticRequest
            ↓
        Query processing
            ↓
        Evidence-weighted retrieval
            ↓
        Scope Gate
            ↓
        Deterministic validation
            ↓
        EvidencePackage
            ↓
        Gemma reasoning
            ↓
        Output validation
            ↓
        DiagnosticResponse
    """

    def __init__(self):
        self.index_data = load_json(INDEX_FILE)
        self.vocabulary = load_json(VOCAB_FILE)
        self.records = load_records()

        self.coverage = build_coverage(
            self.records
        )

        self.records_by_id = {
            str(record["project_id"]): record
            for record in self.records
        }

    # --------------------------------------------------
    # QUERY PROCESSING
    # --------------------------------------------------

    def build_query_terms(
        self,
        query: str,
    ) -> List[str]:
        """
        Convert a natural-language problem description
        into retrieval terms.
        """

        normalized_query = query.strip().lower()

        terms = []

        # Preserve exact-query behavior.
        terms.extend(
            expand_query(
                normalized_query,
                self.vocabulary,
            )
        )

        # Match known vocabulary aliases appearing
        # inside the natural-language query.
        aliases = self.vocabulary.get(
            "aliases",
            {},
        )

        for alias, mapped_values in aliases.items():
            alias_normalized = (
                str(alias)
                .strip()
                .lower()
            )

            if not alias_normalized:
                continue

            if alias_normalized in normalized_query:
                if alias_normalized not in terms:
                    terms.append(
                        alias_normalized
                    )

                for value in mapped_values:
                    value_normalized = (
                        str(value)
                        .strip()
                        .lower()
                    )

                    if (
                        value_normalized
                        and value_normalized not in terms
                    ):
                        terms.append(
                            value_normalized
                        )

        # Deduplicate while preserving order.
        deduplicated = []

        for term in terms:
            if term not in deduplicated:
                deduplicated.append(term)

        return deduplicated

    # --------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------

    def retrieve(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Perform evidence-weighted retrieval against
        the canonical CircuitSage corpus.
        """

        query_terms = self.build_query_terms(
            query
        )

        retrieval_results = search(
            self.index_data,
            query_terms,
        )

        ranked_results = []

        for project_id, result in retrieval_results.items():
            score = result.get(
                "score",
                0,
            )

            record = self.records_by_id.get(
                str(project_id)
            )

            ranked_results.append(
                {
                    "project_id": str(
                        project_id
                    ),
                    "project_name": (
                        record.get(
                            "project_name"
                        )
                        if record
                        else None
                    ),
                    "category": (
                        record.get(
                            "category"
                        )
                        if record
                        else None
                    ),
                    "score": score,
                    "evidence_level": evidence_level(
                        score
                    ),
                    "matches": result.get(
                        "matches",
                        [],
                    ),
                }
            )

        ranked_results.sort(
            key=lambda item: (
                -item["score"],
                int(item["project_id"]),
            )
        )

        return {
            "query": query,
            "expanded_terms": query_terms,
            "results": ranked_results,
        }

    # --------------------------------------------------
    # COMPONENT IDENTIFICATION
    # --------------------------------------------------

    def identify_component(
        self,
        query: str,
        retrieval_results: List[
            Dict[str, Any]
        ],
    ) -> Optional[str]:
        """
        Identify a component conservatively.

        Direct component mentions in the user query
        have priority over inferred retrieval evidence.
        """

        normalized_query = query.lower()

        # Direct component mention.
        for record in self.records:
            for component in record.get(
                "components",
                [],
            ):
                if component.lower() in normalized_query:
                    return component

        # Strong retrieval candidate.
        for result in retrieval_results:
            if result["evidence_level"] != "HIGH":
                continue

            record = self.records_by_id.get(
                str(result["project_id"])
            )

            if not record:
                continue

            components = record.get(
                "components",
                [],
            )

            if len(components) == 1:
                return components[0]

        return None

    # --------------------------------------------------
    # DETERMINISTIC VALIDATION
    # --------------------------------------------------

    def run_deterministic_validation(
        self,
        component: Optional[str],
        code: Optional[str],
        project_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Run a deterministic validator when one exists.

        Validators are selected through the centralized
        deterministic-validator registry.
        """

        if not component:
            return None

        if not code:
            return None

        validator = get_deterministic_validator(
            component
        )

        if validator is None:
            return None

        result = validator(
            code,
            source_file=(
                project_name
                or "user_submitted_code"
            ),
        )

        return result.to_dict()

    # --------------------------------------------------
    # RETRIEVED EVIDENCE
    # --------------------------------------------------

    def build_retrieved_project_evidence(
        self,
        retrieval_results: List[
            Dict[str, Any]
        ],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Convert retrieval results into compact evidence
        for the EvidencePackage.
        """

        evidence = []

        for result in retrieval_results[:limit]:
            record = self.records_by_id.get(
                str(result["project_id"])
            )

            if not record:
                continue

            evidence.append(
                {
                    "project_id": record.get(
                        "project_id"
                    ),
                    "project_name": record.get(
                        "project_name"
                    ),
                    "category": record.get(
                        "category"
                    ),
                    "evidence_level": result.get(
                        "evidence_level"
                    ),
                    "retrieval_score": result.get(
                        "score"
                    ),
                    "matches": result.get(
                        "matches",
                        [],
                    ),
                    "components": record.get(
                        "components",
                        [],
                    ),
                    "libraries": record.get(
                        "libraries",
                        [],
                    ),
                    "interfaces": record.get(
                        "interfaces",
                        {},
                    ),
                    "diagnostic_signals": record.get(
                        "diagnostic_signals",
                        [],
                    ),
                    "source_files": record.get(
                        "source_files",
                        [],
                    ),
                    "artifact_files": record.get(
                        "artifact_files",
                        [],
                    ),
                }
            )

        return evidence

    # --------------------------------------------------
    # KNOWN UNKNOWNS
    # --------------------------------------------------

    def build_known_unknowns(
        self,
        request: DiagnosticRequest,
        validator_result: Optional[
            Dict[str, Any]
        ],
    ) -> List[str]:

        unknowns = []

        if not request.schematic_path:
            unknowns.append(
                "Schematic analysis is unavailable "
                "for this request."
            )

        if not request.serial_output:
            unknowns.append(
                "Actual Serial Monitor output was "
                "not supplied."
            )

        if validator_result is None:
            unknowns.append(
                "No deterministic component validator "
                "was run."
            )

        if request.code:
            unknowns.append(
                "Static code analysis does not prove "
                "physical hardware operation."
            )
        else:
            unknowns.append(
                "Arduino source code was not supplied."
            )

        unknowns.append(
            "Physical wiring, power measurements, "
            "and hardware condition have not been "
            "directly verified."
        )

        return unknowns

    # --------------------------------------------------
    # SAFE SCOPE RESPONSES
    # --------------------------------------------------

    def unsupported_response(
        self,
        scope_result: Dict[str, Any],
        retrieval: Dict[str, Any],
    ) -> DiagnosticResponse:

        return DiagnosticResponse(
            status="UNSUPPORTED",
            accepted=True,
            component=None,
            diagnosis=(
                "This component or diagnostic scenario "
                "isn't currently supported by "
                "CircuitSage V1.0. Please try a "
                "supported system."
            ),
            evidence=[],
            unknowns=[
                "No matching canonical evidence "
                "was found."
            ],
            verification_steps=[],
            retrieved_projects=[],
            validator={},
            limitations=[
                scope_result.get(
                    "reason",
                    "No supported evidence was found.",
                )
            ],
        )

    def insufficient_response(
        self,
        scope_result: Dict[str, Any],
        retrieval: Dict[str, Any],
    ) -> DiagnosticResponse:

        return DiagnosticResponse(
            status="INSUFFICIENT_EVIDENCE",
            accepted=True,
            component=None,
            diagnosis=(
                "CircuitSage recognizes the requested "
                "component or diagnostic domain, but "
                "the available evidence is not sufficient "
                "for a confident diagnostic."
            ),
            evidence=[],
            unknowns=[
                "No diagnostic evidence was supplied "
                "for validation."
            ],
            verification_steps=[
                "Provide the relevant Arduino source "
                "code if available.",
                "Provide actual Serial Monitor output "
                "or measured behavior if available.",
                "Provide a more specific description "
                "of the observed failure.",
            ],
            retrieved_projects=(
                retrieval["results"][:5]
            ),
            validator={},
            limitations=[
                scope_result.get(
                    "reason",
                    "Evidence is insufficient.",
                )
            ],
        )

    # --------------------------------------------------
    # MAIN DIAGNOSTIC PIPELINE
    # --------------------------------------------------

    def diagnose(
        self,
        request: DiagnosticRequest,
    ) -> DiagnosticResponse:
        """
        Execute the complete CircuitSage diagnostic flow.
        """

        query = (
            request.problem_description.strip()
        )

        # --------------------------------------------------
        # Empty request
        # --------------------------------------------------

        if not query:
            return DiagnosticResponse(
                status="INVALID_REQUEST",
                accepted=True,
                diagnosis=(
                    "Please provide a description "
                    "of the embedded-system problem."
                ),
                limitations=[
                    "problem_description is required."
                ],
            )

        # --------------------------------------------------
        # 1. Retrieval
        # --------------------------------------------------

        retrieval = self.retrieve(
            query
        )

        # --------------------------------------------------
        # 2. Scope Gate
        # --------------------------------------------------

        retrieval_for_scope = {
            result["project_id"]: {
                "score": result["score"],
                "matches": result["matches"],
            }
            for result in retrieval["results"]
        }

        scope_result = evaluate_scope(
            query,
            retrieval_for_scope,
            self.coverage,
            evidence_context={
                "code": request.code,
                "serial_output": request.serial_output,
            },
        )

        # --------------------------------------------------
        # 3. Scope handling
        # --------------------------------------------------

        if (
            scope_result["status"]
            == "UNSUPPORTED"
        ):
            return self.unsupported_response(
                scope_result,
                retrieval,
            )

        if (
            scope_result["status"]
            == "INSUFFICIENT_EVIDENCE"
        ):
            return self.insufficient_response(
                scope_result,
                retrieval,
            )

        # --------------------------------------------------
        # 4. Identify component
        # --------------------------------------------------

        component = self.identify_component(
            query,
            retrieval["results"],
        )

        # --------------------------------------------------
        # 5. Deterministic validation
        # --------------------------------------------------

        validator_result = (
            self.run_deterministic_validation(
                component,
                request.code,
                request.project_name,
            )
        )

        # --------------------------------------------------
        # 6. Build EvidencePackage
        # --------------------------------------------------

        retrieved_project_evidence = (
            self.build_retrieved_project_evidence(
                retrieval["results"]
            )
        )

        known_unknowns = (
            self.build_known_unknowns(
                request,
                validator_result,
            )
        )

        engineering_parameters = None

        if (
            component
            and component.lower() == "hc-sr04"
            and request.code
        ):
            engineering_parameters = {
                "sensor": "HC-SR04",
                "trigger_pin": "11",
                "echo_pin": "12",
                "serial_baud": 9600,
                "loop_delay_ms": 250,
                "trigger_pulse_us": 10,
            }

        evidence_package = EvidencePackage(
            user_query=query,
            scope_status=scope_result["status"],
            component=component,
            retrieved_projects=(
                retrieved_project_evidence
            ),
            validator_result=validator_result,
            schematic_evidence=None,
            engineering_parameters=(
                engineering_parameters
            ),
            known_unknowns=known_unknowns,
        )

        # --------------------------------------------------
        # 7. Reasoning
        # --------------------------------------------------

        reasoning_result = run_reasoning_pipeline(
            evidence_package
        )

        # --------------------------------------------------
        # 8. Final response
        # --------------------------------------------------

        return DiagnosticResponse(
            status=scope_result["status"],
            accepted=reasoning_result.get(
                "accepted",
                False,
            ),
            component=component,
            diagnosis=reasoning_result.get(
                "diagnosis",
                "",
            ),
            evidence=retrieved_project_evidence,
            unknowns=known_unknowns,
            verification_steps=reasoning_result.get(
                "verification_steps",
                [],
            ),
            retrieved_projects=(
                retrieved_project_evidence
            ),
            validator=(
                validator_result
                or {}
            ),
            limitations=[
                "Schematic analysis is not integrated "
                "into the V1.0 reasoning pipeline."
            ],
            error=reasoning_result.get(
                "error"
            ),
        )