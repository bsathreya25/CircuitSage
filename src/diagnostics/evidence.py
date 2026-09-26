from dataclasses import dataclass, asdict
from typing import Optional


VALID_STATUSES = {"PASS", "FAIL", "UNKNOWN"}


@dataclass
class CheckResult:
    check_id: str
    name: str
    status: str
    evidence: str
    source_file: Optional[str] = None
    line_reference: Optional[str] = None
    expected: Optional[str] = None
    observed: Optional[str] = None

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. "
                f"Expected one of {sorted(VALID_STATUSES)}."
            )

    def to_dict(self):
        return asdict(self)


@dataclass
class ValidatorResult:
    validator_id: str
    component: str
    source_file: str
    checks: list[CheckResult]

    @property
    def passed(self):
        return sum(c.status == "PASS" for c in self.checks)

    @property
    def failed(self):
        return sum(c.status == "FAIL" for c in self.checks)

    @property
    def unknown(self):
        return sum(c.status == "UNKNOWN" for c in self.checks)

    def overall_status(self):
        if self.failed > 0:
            return "FAIL"

        if self.unknown > 0:
            return "UNKNOWN"

        return "PASS"

    def to_dict(self):
        return {
            "validator_id": self.validator_id,
            "component": self.component,
            "source_file": self.source_file,
            "overall_status": self.overall_status(),
            "summary": {
                "total": len(self.checks),
                "passed": self.passed,
                "failed": self.failed,
                "unknown": self.unknown,
            },
            "checks": [check.to_dict() for check in self.checks],
        }