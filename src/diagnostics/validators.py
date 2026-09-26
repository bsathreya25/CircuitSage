import re
from pathlib import Path

from diagnostics.evidence import CheckResult, ValidatorResult


def read_source_file(path):
    return Path(path).read_text(encoding="utf-8")


def find_line_number(source, pattern, flags=0):
    regex = re.compile(pattern, flags)

    for line_number, line in enumerate(source.splitlines(), start=1):
        if regex.search(line):
            return line_number

    return None


def _find_pin_mode(source, pin_name):
    """
    Find the first pinMode(pin_name, MODE) statement.

    Returns:
        {
            "mode": str,
            "line": int,
            "text": str,
        }
        or None if no matching pinMode statement exists.
    """

    pattern = re.compile(
        rf"pinMode\s*\(\s*{re.escape(pin_name)}\s*,\s*"
        rf"(INPUT_PULLUP|INPUT|OUTPUT)\s*\)",
        re.IGNORECASE,
    )

    for line_number, line in enumerate(source.splitlines(), start=1):
        match = pattern.search(line)

        if match:
            return {
                "mode": match.group(1).upper(),
                "line": line_number,
                "text": line.strip(),
            }

    return None


def check_hcsr04(source):
    checks = []

    # ------------------------------------------------------------
    # HC001 — TRIG pin defined
    # ------------------------------------------------------------

    trig_match = re.search(
        r"\btrigPin\s*=\s*(\d+)",
        source,
        re.IGNORECASE,
    )

    if trig_match:
        trig_pin = trig_match.group(1)

        line = find_line_number(
            source,
            r"\btrigPin\s*=\s*\d+",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "TRIG pin defined",
                "status": "PASS",
                "evidence": f"trigPin assignment found: {trig_pin}.",
                "line_reference": line,
                "expected": "A TRIG pin assignment should exist.",
                "observed": f"trigPin = {trig_pin}",
            }
        )

    else:
        checks.append(
            {
                "check": "TRIG pin defined",
                "status": "UNKNOWN",
                "evidence": (
                    "No trigPin assignment was detected by the parser."
                ),
                "line_reference": None,
                "expected": "A TRIG pin assignment should exist.",
                "observed": "No assignment detected.",
            }
        )

    # ------------------------------------------------------------
    # HC002 — ECHO pin defined
    # ------------------------------------------------------------

    echo_match = re.search(
        r"\bechoPin\s*=\s*(\d+)",
        source,
        re.IGNORECASE,
    )

    if echo_match:
        echo_pin = echo_match.group(1)

        line = find_line_number(
            source,
            r"\bechoPin\s*=\s*\d+",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "ECHO pin defined",
                "status": "PASS",
                "evidence": f"echoPin assignment found: {echo_pin}.",
                "line_reference": line,
                "expected": "An ECHO pin assignment should exist.",
                "observed": f"echoPin = {echo_pin}",
            }
        )

    else:
        checks.append(
            {
                "check": "ECHO pin defined",
                "status": "UNKNOWN",
                "evidence": (
                    "No echoPin assignment was detected by the parser."
                ),
                "line_reference": None,
                "expected": "An ECHO pin assignment should exist.",
                "observed": "No assignment detected.",
            }
        )

    # ------------------------------------------------------------
    # HC003 — TRIG configured OUTPUT
    # ------------------------------------------------------------

    trig_pin_mode = _find_pin_mode(source, "trigPin")

    if trig_pin_mode is None:
        checks.append(
            {
                "check": "TRIG configured OUTPUT",
                "status": "UNKNOWN",
                "evidence": (
                    "No TRIG pinMode configuration was detected."
                ),
                "line_reference": None,
                "expected": "TRIG should be configured as OUTPUT.",
                "observed": "No matching pinMode statement detected.",
            }
        )

    elif trig_pin_mode["mode"] == "OUTPUT":
        checks.append(
            {
                "check": "TRIG configured OUTPUT",
                "status": "PASS",
                "evidence": "TRIG pin is configured as OUTPUT.",
                "line_reference": trig_pin_mode["line"],
                "expected": "TRIG should be configured as OUTPUT.",
                "observed": trig_pin_mode["text"],
            }
        )

    else:
        checks.append(
            {
                "check": "TRIG configured OUTPUT",
                "status": "FAIL",
                "evidence": (
                    "TRIG pin is explicitly configured with the wrong mode."
                ),
                "line_reference": trig_pin_mode["line"],
                "expected": "TRIG should be configured as OUTPUT.",
                "observed": trig_pin_mode["text"],
            }
        )

    # ------------------------------------------------------------
    # HC004 — ECHO configured INPUT
    # ------------------------------------------------------------

    echo_pin_mode = _find_pin_mode(source, "echoPin")

    if echo_pin_mode is None:
        checks.append(
            {
                "check": "ECHO configured INPUT",
                "status": "UNKNOWN",
                "evidence": (
                    "No ECHO pinMode configuration was detected."
                ),
                "line_reference": None,
                "expected": "ECHO should be configured as INPUT.",
                "observed": "No matching pinMode statement detected.",
            }
        )

    elif echo_pin_mode["mode"] == "INPUT":
        checks.append(
            {
                "check": "ECHO configured INPUT",
                "status": "PASS",
                "evidence": "ECHO pin is configured as INPUT.",
                "line_reference": echo_pin_mode["line"],
                "expected": "ECHO should be configured as INPUT.",
                "observed": echo_pin_mode["text"],
            }
        )

    else:
        checks.append(
            {
                "check": "ECHO configured INPUT",
                "status": "FAIL",
                "evidence": (
                    "ECHO pin is explicitly configured with the wrong mode."
                ),
                "line_reference": echo_pin_mode["line"],
                "expected": "ECHO should be configured as INPUT.",
                "observed": echo_pin_mode["text"],
            }
        )

    # ------------------------------------------------------------
    # HC005 — Trigger pulse generated
    # ------------------------------------------------------------

    trigger_pulse = re.search(
        r"digitalWrite\s*\(\s*trigPin\s*,\s*HIGH\s*\)",
        source,
        re.IGNORECASE,
    )

    microsecond_timing = re.search(
        r"delayMicroseconds\s*\(",
        source,
        re.IGNORECASE,
    )

    if trigger_pulse and microsecond_timing:
        trigger_line = find_line_number(
            source,
            r"digitalWrite\s*\(\s*trigPin\s*,\s*HIGH\s*\)",
            re.IGNORECASE,
        )

        timing_line = find_line_number(
            source,
            r"delayMicroseconds\s*\(",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "Trigger pulse generated",
                "status": "PASS",
                "evidence": (
                    "TRIG HIGH transition and microsecond timing "
                    "were detected."
                ),
                "line_reference": (
                    f"{trigger_line}; timing at line {timing_line}"
                ),
                "expected": (
                    "A TRIG HIGH transition with microsecond timing "
                    "should be present."
                ),
                "observed": (
                    "digitalWrite(trigPin, HIGH) and "
                    "delayMicroseconds(...) detected."
                ),
            }
        )

    elif trigger_pulse and not microsecond_timing:
        trigger_line = find_line_number(
            source,
            r"digitalWrite\s*\(\s*trigPin\s*,\s*HIGH\s*\)",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "Trigger pulse generated",
                "status": "UNKNOWN",
                "evidence": (
                    "TRIG HIGH transition was detected, but "
                    "microsecond timing was not detected."
                ),
                "line_reference": trigger_line,
                "expected": (
                    "A TRIG HIGH transition with microsecond timing "
                    "should be present."
                ),
                "observed": (
                    "TRIG HIGH detected without a matching "
                    "delayMicroseconds(...) call."
                ),
            }
        )

    else:
        checks.append(
            {
                "check": "Trigger pulse generated",
                "status": "UNKNOWN",
                "evidence": (
                    "A complete trigger-pulse pattern was not detected."
                ),
                "line_reference": None,
                "expected": (
                    "A TRIG HIGH transition with microsecond timing "
                    "should be present."
                ),
                "observed": (
                    "Complete trigger-pulse pattern not detected."
                ),
            }
        )

    # ------------------------------------------------------------
    # HC006 — ECHO pulse measurement
    # ------------------------------------------------------------

    pulse_match = re.search(
        r"pulseIn\s*\(\s*echoPin\s*,",
        source,
        re.IGNORECASE,
    )

    if pulse_match:
        line = find_line_number(
            source,
            r"pulseIn\s*\(\s*echoPin\s*,",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "ECHO pulse measurement",
                "status": "PASS",
                "evidence": "pulseIn(echoPin, ...) was detected.",
                "line_reference": line,
                "expected": "The ECHO pulse should be measured.",
                "observed": "pulseIn(echoPin, ...) detected.",
            }
        )

    else:
        checks.append(
            {
                "check": "ECHO pulse measurement",
                "status": "UNKNOWN",
                "evidence": (
                    "No pulseIn(echoPin, ...) call was detected."
                ),
                "line_reference": None,
                "expected": "The ECHO pulse should be measured.",
                "observed": "No matching pulseIn call detected.",
            }
        )

    # ------------------------------------------------------------
    # HC007 — Distance calculation
    # ------------------------------------------------------------

    distance_match = re.search(
        r"\b(cm|inches|distance)\s*=",
        source,
        re.IGNORECASE,
    )

    if distance_match:
        line = find_line_number(
            source,
            r"\b(cm|inches|distance)\s*=",
            re.IGNORECASE,
        )

        matched_text = source.splitlines()[line - 1].strip()

        checks.append(
            {
                "check": "Distance calculation",
                "status": "PASS",
                "evidence": "A distance-related assignment was detected.",
                "line_reference": line,
                "expected": (
                    "A calculated distance value should be assigned."
                ),
                "observed": matched_text,
            }
        )

    else:
        checks.append(
            {
                "check": "Distance calculation",
                "status": "UNKNOWN",
                "evidence": (
                    "No distance-related assignment was detected."
                ),
                "line_reference": None,
                "expected": (
                    "A calculated distance value should be assigned."
                ),
                "observed": (
                    "No matching distance assignment detected."
                ),
            }
        )

    # ------------------------------------------------------------
    # HC008 — Serial output
    # ------------------------------------------------------------

    serial_match = re.search(
        r"Serial\.(print|println)\s*\(",
        source,
        re.IGNORECASE,
    )

    if serial_match:
        line = find_line_number(
            source,
            r"Serial\.(print|println)\s*\(",
            re.IGNORECASE,
        )

        checks.append(
            {
                "check": "Serial output",
                "status": "PASS",
                "evidence": "Serial output statements were detected.",
                "line_reference": line,
                "expected": (
                    "Diagnostic/output information should be sent "
                    "through Serial."
                ),
                "observed": (
                    "Serial.print/Serial.println detected."
                ),
            }
        )

    else:
        checks.append(
            {
                "check": "Serial output",
                "status": "UNKNOWN",
                "evidence": (
                    "No Serial.print/Serial.println statement "
                    "was detected."
                ),
                "line_reference": None,
                "expected": (
                    "Diagnostic/output information should be sent "
                    "through Serial."
                ),
                "observed": "No matching Serial output detected.",
            }
        )

    return {"checks": checks}


def run_hcsr04_validator(source, source_file="unknown"):
    raw_result = check_hcsr04(source)

    evidence_checks = []

    for index, check in enumerate(raw_result["checks"], start=1):
        evidence_checks.append(
            CheckResult(
                check_id=f"HC{index:03d}",
                name=check["check"],
                status=check["status"],
                evidence=check["evidence"],
                source_file=source_file,
                line_reference=(
                    str(check["line_reference"])
                    if check.get("line_reference") is not None
                    else None
                ),
                expected=check.get("expected"),
                observed=check.get("observed"),
            )
        )

    return ValidatorResult(
        validator_id="hcsr04_v1",
        component="HC-SR04",
        source_file=source_file,
        checks=evidence_checks,
    )