from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class EvidencePackage:
    """
    Structured evidence passed to the reasoning layer.

    The package contains observations gathered by deterministic
    components of CircuitSage. The LLM must reason from this
    package rather than inventing observations.
    """

    user_query: str
    scope_status: str

    component: Optional[str] = None

    retrieved_projects: Optional[List[Dict[str, Any]]] = None

    validator_result: Optional[Dict[str, Any]] = None

    schematic_evidence: Optional[List[Dict[str, Any]]] = None

    engineering_parameters: Optional[Dict[str, Any]] = None

    known_unknowns: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json_ready(self) -> Dict[str, Any]:
        """
        Return a clean dictionary suitable for JSON serialization
        and later LLM prompting.
        """

        data = self.to_dict()

        if data["retrieved_projects"] is None:
            data["retrieved_projects"] = []

        if data["schematic_evidence"] is None:
            data["schematic_evidence"] = []

        if data["engineering_parameters"] is None:
            data["engineering_parameters"] = {}

        if data["known_unknowns"] is None:
            data["known_unknowns"] = []

        return data
