from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DiagnosticRequest:
    """
    User-facing request received by CircuitSage.

    The frontend will eventually send this information
    to the backend.
    """

    problem_description: str

    code: Optional[str] = None

    schematic_path: Optional[str] = None

    serial_output: Optional[str] = None

    project_name: Optional[str] = None


@dataclass
class DiagnosticResponse:
    """
    Standard response returned by CircuitSage.

    The frontend should consume this object rather than
    depending on internal backend modules.
    """

    status: str

    accepted: bool

    component: Optional[str] = None

    diagnosis: str = ""

    evidence: List[Dict[str, Any]] = field(
        default_factory=list
    )

    unknowns: List[str] = field(
        default_factory=list
    )

    verification_steps: List[str] = field(
        default_factory=list
    )

    retrieved_projects: List[Dict[str, Any]] = field(
        default_factory=list
    )

    validator: Dict[str, Any] = field(
        default_factory=dict
    )

    limitations: List[str] = field(
        default_factory=list
    )

    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "accepted": self.accepted,
            "component": self.component,
            "diagnosis": self.diagnosis,
            "evidence": self.evidence,
            "unknowns": self.unknowns,
            "verification_steps": self.verification_steps,
            "retrieved_projects": self.retrieved_projects,
            "validator": self.validator,
            "limitations": self.limitations,
            "error": self.error,
        }