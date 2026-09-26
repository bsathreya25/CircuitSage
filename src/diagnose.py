from pathlib import Path
import json
import os
import re

from dotenv import load_dotenv
from google import genai

from validate_circuit import validate_connections
from analyze_schematic import analyze_schematic
from ollama_client import ask_local_model


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent

KNOWLEDGE_BASE_FILE = (
    PROJECT_ROOT / "knowledge_base/project_records.json"
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

gemini_client = None

if api_key:
    try:
        gemini_client = genai.Client(
            api_key=api_key
        )
    except Exception as error:
        print()
        print(
            f"Gemini client initialization failed: {error}"
        )


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    if not KNOWLEDGE_BASE_FILE.exists():

        print()
        print("Knowledge base not found.")

        return []

    try:

        with open(
            KNOWLEDGE_BASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print()
        print(
            f"Failed to load knowledge base: {error}"
        )

        return []


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_project(
    question,
    projects
):
    """
    Deterministic technical-project retrieval.

    Priority:
    1. Exact sensor/component match
    2. Exact project-name match
    3. Component-name match
    4. Technical metadata match
    5. Generic word overlap

    This is intentionally deterministic for the MVP.
    """

    question_lower = question.lower()

    question_words = set(
        re.findall(
            r"\b[a-zA-Z0-9_-]+\b",
            question_lower
        )
    )

    best_project = None
    best_score = -1

    for project in projects:

        score = 0

        project_name = str(
            project.get(
                "project_name",
                ""
            )
        ).lower()

        sensor = str(
            project.get(
                "sensor",
                ""
            )
        ).lower()

        components = [
            str(component).lower()
            for component in project.get(
                "components",
                []
            )
        ]

        libraries = [
            str(library).lower()
            for library in project.get(
                "libraries",
                []
            )
        ]

        # ====================================================
        # 1. Exact sensor match
        # ====================================================

        if sensor and sensor in question_lower:

            score += 100

        # ====================================================
        # 2. Exact project-name match
        # ====================================================

        if (
            project_name
            and
            project_name in question_lower
        ):

            score += 80

        # ====================================================
        # 3. Component match
        # ====================================================

        for component in components:

            if (
                component
                and
                component in question_lower
            ):

                score += 60

        # ====================================================
        # 4. Technical metadata matches
        # ====================================================

        technical_metadata = " ".join(
            [
                project_name,
                sensor,
                " ".join(components),
                " ".join(libraries)
            ]
        )

        for word in question_words:

            if len(word) <= 2:
                continue

            if word in technical_metadata:

                score += 5

        # ====================================================
        # 5. Generic project-record overlap
        # ====================================================

        project_text = json.dumps(
            project
        ).lower()

        for word in question_words:

            if len(word) <= 2:
                continue

            if word in project_text:

                score += 1

        # ====================================================
        # Select highest-scoring project
        # ====================================================

        if score > best_score:

            best_score = score
            best_project = project

    return best_project, best_score


def load_code(project):

    code_file = project.get(
        "code_file"
    )

    if not code_file:

        return None

    code_path = PROJECT_ROOT / code_file

    if not code_path.exists():

        print()
        print(
            f"Arduino code not found: {code_path}"
        )

        return None

    try:

        return code_path.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        print()
        print(
            f"Failed to read Arduino code: {error}"
        )

        return None


# ============================================================
# HC-SR04 TRIGGER PULSE ANALYSIS
# ============================================================

def extract_hcsr04_trigger_pulse(
    code
):
    """
    Detect an HC-SR04 trigger pulse.

    Supports both common Arduino naming styles:

        TRIG_PIN
        trigPin

    The function looks for:

        digitalWrite(TRIG, HIGH);
        delayMicroseconds(X);
        digitalWrite(TRIG, LOW);

    and returns X as the confirmed trigger pulse duration.
    """

    patterns = [

        # -----------------------------------------------
        # TRIG_PIN style
        # -----------------------------------------------

        re.compile(
            r"digitalWrite\s*\(\s*TRIG_PIN\s*,\s*HIGH\s*\)"
            r"\s*;"
            r"\s*"
            r"delayMicroseconds\s*\(\s*(\d+)\s*\)"
            r"\s*;"
            r"\s*"
            r"digitalWrite\s*\(\s*TRIG_PIN\s*,\s*LOW\s*\)"
            r"\s*;",
            re.IGNORECASE
        ),

        # -----------------------------------------------
        # trigPin style
        # -----------------------------------------------

        re.compile(
            r"digitalWrite\s*\(\s*trigPin\s*,\s*HIGH\s*\)"
            r"\s*;"
            r"\s*"
            r"delayMicroseconds\s*\(\s*(\d+)\s*\)"
            r"\s*;"
            r"\s*"
            r"digitalWrite\s*\(\s*trigPin\s*,\s*LOW\s*\)"
            r"\s*;",
            re.IGNORECASE
        )
    ]

    for pattern in patterns:

        match = pattern.search(code)

        if match:

            return {
                "value_us": int(
                    match.group(1)
                ),
                "status": "CONFIRMED",
                "method": (
                    "Detected delayMicroseconds() "
                    "between TRIG HIGH and TRIG LOW."
                )
            }

    return {
        "value_us": None,
        "status": "NOT_DETECTED",
        "method": (
            "Could not identify the complete "
            "TRIG HIGH → delay → TRIG LOW sequence."
        )
    }

# ============================================================
# ENGINEERING CHECKS
# ============================================================

def run_engineering_checks(
    project,
    code
):
    """
    Run deterministic engineering checks using the structured
    knowledge-base record produced by read_arduino.py.

    Structured project metadata is preferred. Raw-code regex
    checks are retained as fallbacks for older projects.
    """

    sensor = str(
        project.get("sensor", "")
    ).upper()

    checks = []

    parameters = {
        "sensor": project.get("sensor")
    }

    # ========================================================
    # DHT11 / DHT22
    # ========================================================

    if "DHT11" in sensor or "DHT22" in sensor:

        parameters["data_pin"] = project.get(
            "data_pin"
        )

        baud_rate = project.get("baud_rate")

        if baud_rate is not None:
            parameters["serial_baud"] = baud_rate
        else:
            baud_match = re.search(
                r"Serial\.begin\(\s*(\d+)\s*\)",
                code
            )

            if baud_match:
                parameters["serial_baud"] = int(
                    baud_match.group(1)
                )

        timing = project.get("timing", {})

        delay_values = timing.get(
            "delay_ms",
            []
        )

        if delay_values:
            parameters["loop_delay_ms"] = delay_values[-1]
        else:
            delay_match = re.search(
                r"delay\(\s*(\d+)\s*\)",
                code
            )

            if delay_match:
                parameters["loop_delay_ms"] = int(
                    delay_match.group(1)
                )

        checks.append({
            "check": "DHT library",
            "status": (
                "PASS"
                if "#include <DHT.h>" in code
                else "FAIL"
            )
        })

        checks.append({
            "check": "DHT initialization",
            "status": (
                "PASS"
                if "dht.begin()" in code
                else "FAIL"
            )
        })

        checks.append({
            "check": "Temperature reading",
            "status": (
                "PASS"
                if "readTemperature()" in code
                else "FAIL"
            )
        })

        checks.append({
            "check": "Humidity reading",
            "status": (
                "PASS"
                if "readHumidity()" in code
                else "FAIL"
            )
        })

    # ========================================================
    # HC-SR04
    # ========================================================

    elif "HC-SR04" in sensor:

        pins = project.get(
            "pins",
            {}
        )

        pin_modes = project.get(
            "pin_modes",
            {}
        )

        operations = project.get(
            "operations",
            {}
        )

        timing = project.get(
            "timing",
            {}
        )

        # ----------------------------------------------------
        # Pin identification
        # ----------------------------------------------------

        trigger_pin = project.get(
            "trigger_pin"
        )

        echo_pin = project.get(
            "echo_pin"
        )

        if trigger_pin is None:
            for name, value in pins.items():
                if name.lower() == "trigpin":
                    trigger_pin = value
                    break

        if echo_pin is None:
            for name, value in pins.items():
                if name.lower() == "echopin":
                    echo_pin = value
                    break

        # ----------------------------------------------------
        # Raw-code fallback for older #define projects
        # ----------------------------------------------------

        if trigger_pin is None:

            trigger_match = re.search(
                r"#define\s+TRIG_PIN\s+(\d+)",
                code
            )

            if trigger_match:
                trigger_pin = trigger_match.group(1)

        if echo_pin is None:

            echo_match = re.search(
                r"#define\s+ECHO_PIN\s+(\d+)",
                code
            )

            if echo_match:
                echo_pin = echo_match.group(1)

        if trigger_pin is not None:
            parameters["trigger_pin"] = str(
                trigger_pin
            )

        if echo_pin is not None:
            parameters["echo_pin"] = str(
                echo_pin
            )

        # ----------------------------------------------------
        # Serial baud rate
        # ----------------------------------------------------

        baud_rate = project.get(
            "baud_rate"
        )

        if baud_rate is not None:

            parameters["serial_baud"] = baud_rate

        else:

            baud_match = re.search(
                r"Serial\.begin\(\s*(\d+)\s*\)",
                code
            )

            if baud_match:
                parameters["serial_baud"] = int(
                    baud_match.group(1)
                )

        # ----------------------------------------------------
        # Loop delay
        # ----------------------------------------------------

        delay_values = timing.get(
            "delay_ms",
            []
        )

        if delay_values:

            parameters["loop_delay_ms"] = (
                delay_values[-1]
            )

        else:

            delay_match = re.search(
                r"delay\(\s*(\d+)\s*\)",
                code
            )

            if delay_match:
                parameters["loop_delay_ms"] = int(
                    delay_match.group(1)
                )

        # ----------------------------------------------------
        # Trigger pulse
        # ----------------------------------------------------

        trigger_pulse = extract_hcsr04_trigger_pulse(
            code
        )

        if trigger_pulse["value_us"] is not None:

            parameters["trigger_pulse_us"] = (
                trigger_pulse["value_us"]
            )

        # ----------------------------------------------------
        # Pin definitions
        # ----------------------------------------------------

        checks.append({
            "check": "TRIG pin defined",
            "status": (
                "PASS"
                if trigger_pin is not None
                else "FAIL"
            )
        })

        checks.append({
            "check": "ECHO pin defined",
            "status": (
                "PASS"
                if echo_pin is not None
                else "FAIL"
            )
        })

        # ----------------------------------------------------
        # Pin modes
        # ----------------------------------------------------

        trig_mode = None
        echo_mode = None

        for name, mode in pin_modes.items():

            name_lower = str(name).lower()

            if name_lower == "trigpin":
                trig_mode = str(mode).upper()

            elif name_lower == "echopin":
                echo_mode = str(mode).upper()

        # Raw-code fallback

        if trig_mode is None:

            if re.search(
                r"pinMode\(\s*TRIG_PIN\s*,\s*OUTPUT\s*\)",
                code
            ) or re.search(
                r"pinMode\(\s*trigPin\s*,\s*OUTPUT\s*\)",
                code
            ):
                trig_mode = "OUTPUT"

        if echo_mode is None:

            if re.search(
                r"pinMode\(\s*ECHO_PIN\s*,\s*INPUT\s*\)",
                code
            ) or re.search(
                r"pinMode\(\s*echoPin\s*,\s*INPUT\s*\)",
                code
            ):
                echo_mode = "INPUT"

        checks.append({
            "check": "TRIG configured as OUTPUT",
            "status": (
                "PASS"
                if trig_mode == "OUTPUT"
                else "FAIL"
            )
        })

        checks.append({
            "check": "ECHO configured as INPUT",
            "status": (
                "PASS"
                if echo_mode == "INPUT"
                else "FAIL"
            )
        })

        # ----------------------------------------------------
        # Trigger sequence
        # ----------------------------------------------------

        digital_operations = operations.get(
            "digital",
            []
        )

        trigger_high = False
        trigger_low = False

        for operation in digital_operations:

            operation_type = operation.get(
                "type"
            )

            operation_pin = str(
                operation.get("pin", "")
            ).lower()

            operation_value = str(
                operation.get("value", "")
            ).upper()

            if (
                operation_type == "digitalWrite"
                and
                operation_pin in {
                    "trigpin",
                    "trig_pin",
                    "trig"
                }
            ):

                if operation_value == "HIGH":
                    trigger_high = True

                elif operation_value == "LOW":
                    trigger_low = True

        # Raw-code fallback

        if not trigger_high:

            trigger_high = bool(
                re.search(
                    r"digitalWrite\(\s*trigPin\s*,\s*HIGH\s*\)",
                    code
                )
                or
                re.search(
                    r"digitalWrite\(\s*TRIG_PIN\s*,\s*HIGH\s*\)",
                    code
                )
            )

        if not trigger_low:

            trigger_low = bool(
                re.search(
                    r"digitalWrite\(\s*trigPin\s*,\s*LOW\s*\)",
                    code
                )
                or
                re.search(
                    r"digitalWrite\(\s*TRIG_PIN\s*,\s*LOW\s*\)",
                    code
                )
            )

        checks.append({
            "check": "Trigger pulse generated",
            "status": (
                "PASS"
                if trigger_high and trigger_low
                else "FAIL"
            )
        })

        # ----------------------------------------------------
        # Trigger pulse duration
        # ----------------------------------------------------

        checks.append({
            "check": "HC-SR04 trigger HIGH pulse detected",
            "status": (
                "PASS"
                if trigger_pulse["value_us"] is not None
                else "FAIL"
            )
        })

        # ----------------------------------------------------
        # Echo measurement
        # ----------------------------------------------------

        pulse_measurement_present = False

        pulse_entries = timing.get(
            "pulseIn",
            []
        )

        for entry in pulse_entries:

            entry_pin = str(
                entry.get("pin", "")
            ).lower()

            if entry_pin in {
                "echopin",
                "echo_pin",
                "echo"
            }:

                pulse_measurement_present = True
                break

        # Raw-code fallback

        if not pulse_measurement_present:

            pulse_measurement_present = bool(
                re.search(
                    r"pulseIn\(\s*echoPin\s*,",
                    code
                )
                or
                re.search(
                    r"pulseIn\(\s*ECHO_PIN\s*,",
                    code
                )
            )

        checks.append({
            "check": "Echo measurement performed",
            "status": (
                "PASS"
                if pulse_measurement_present
                else "FAIL"
            )
        })

        # ----------------------------------------------------
        # Distance calculation
        # ----------------------------------------------------

        distance_calculation_present = (
            "duration" in code
            and
            (
                "/ 2" in code
                or
                "/2" in code
            )
        )

        checks.append({
            "check": "Distance calculation present",
            "status": (
                "PASS"
                if distance_calculation_present
                else "FAIL"
            )
        })

    return parameters, checks

# ============================================================
# PRINT ENGINEERING CHECKS
# ============================================================

def print_engineering_checks(
    checks
):

    print()

    print(
        "Engineering evidence:"
    )

    for check in checks:

        status_symbol = (
            "✓"
            if check["status"] == "PASS"
            else "✗"
        )

        print(
            f"{status_symbol} "
            f"{check['check']} : "
            f"{check['status']}"
        )


# ============================================================
# LOCAL GEMMA REASONING
# ============================================================

def run_local_reasoning(
    evidence
):

    prompt = f"""
You are CircuitSage, an evidence-grounded
embedded-systems engineering diagnostic engine.

Analyze ONLY the engineering evidence supplied below.

==================================================
STRICT EVIDENCE RULES
==================================================

1. Never invent evidence.

2. Never convert an assumption into a confirmed fact.

3. A generic user statement such as
   "HC-SR04 ultrasonic sensor problem"
   does NOT prove that the sensor is malfunctioning.

4. Code analysis establishes what the source code
   contains. It does not prove physical behavior.

5. Schematic analysis establishes what the schematic
   indicates. It does not prove physical wiring.

6. Code-to-schematic validation establishes whether
   documented configurations agree. It does not prove
   which configuration is physically correct.

7. If schematic analysis is unavailable, explicitly
   state that schematic-derived conclusions cannot
   be made.

8. Physical wiring is UNKNOWN unless explicitly
   verified by the supplied evidence.

9. Never claim sensor failure or hardware damage unless
   directly established.

10. Never invent:
    - measurements
    - Serial Monitor output
    - voltages
    - currents
    - resistance
    - oscilloscope results
    - physical wiring
    - source-code line numbers

11. Do not recommend changing firmware merely because
    another configuration is possible.

12. If evidence is insufficient to establish a
    malfunction, explicitly state:

    "No confirmed malfunction has been established
    from the available evidence."

13. A code/schematic mismatch is a confirmed
    consistency issue if validation explicitly
    establishes it.

14. Potential consequences must be conditional.

==================================================
ENGINEERING EVIDENCE
==================================================

{evidence}

==================================================
REQUIRED OUTPUT
==================================================

Return EXACTLY these six sections:

1. CONFIRMED ISSUE

2. CONFIRMED EVIDENCE

3. UNKNOWN INFORMATION

4. POSSIBLE EXPLANATIONS

5. POTENTIAL CONSEQUENCES

6. NEXT ENGINEERING VERIFICATION

Rules for the sections:

- Confirmed Issue: only established facts.
- Confirmed Evidence: only supplied evidence.
- Unknown Information: things not established.
- Possible Explanations: clearly label possibilities.
- Potential Consequences: use conditional language.
- Next Engineering Verification: propose tests that
  distinguish between the possible explanations.

Do not add additional sections.
"""

    return ask_local_model(
        prompt
    )


# ============================================================
# GEMINI CLOUD REASONING
# ============================================================

def run_gemini_reasoning(
    evidence
):

    if gemini_client is None:

        return (
            "Gemini unavailable because "
            "the client could not be initialized."
        )

    prompt = f"""
You are CircuitSage, an evidence-grounded
embedded-systems engineering diagnostic engine.

Use ONLY the supplied engineering evidence.

Do not infer physical hardware behavior from source
code alone.

Do not infer component failure from a generic problem
description.

If schematic analysis is unavailable, explicitly state
that schematic-derived conclusions cannot be made.

Do not assume:
- firmware is wrong
- schematic is wrong
- physical wiring is wrong
- sensor is faulty
- hardware is damaged

Do not invent measurements, physical observations,
Serial Monitor output, or line numbers.

If no malfunction is established, explicitly state:

"No confirmed malfunction has been established
from the available evidence."

ENGINEERING EVIDENCE:

{evidence}

Return EXACTLY these six sections:

1. CONFIRMED ISSUE
2. CONFIRMED EVIDENCE
3. UNKNOWN INFORMATION
4. POSSIBLE EXPLANATIONS
5. POTENTIAL CONSEQUENCES
6. NEXT ENGINEERING VERIFICATION
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as error:

        return (
            f"Gemini reasoning unavailable: {error}"
        )


# ============================================================
# MAIN CIRCUITSAGE PIPELINE
# ============================================================

def main():

    print()
    print("========================================")
    print("          CIRCUITSAGE DIAGNOSTIC")
    print("========================================")
    print()

    question = input(
        "Describe your problem: "
    ).strip()

    if not question:

        print()
        print(
            "No problem description provided."
        )

        return

    # --------------------------------------------------------
    # LOAD KNOWLEDGE BASE
    # --------------------------------------------------------

    projects = load_knowledge_base()

    if not projects:

        return

    # --------------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------------

    project, score = retrieve_project(
        question,
        projects
    )

    if project is None:

        print()
        print(
            "No relevant project found."
        )

        return

    print()
    print(
        "Relevant project information:"
    )

    print(
        json.dumps(
            project,
            indent=4
        )
    )

    print()
    print(
        f"Retrieval relevance score: {score}"
    )

    # --------------------------------------------------------
    # LOAD CODE
    # --------------------------------------------------------

    code = load_code(
        project
    )

    if code is None:

        return

    print()
    print(
        "Arduino code loaded successfully."
    )

    # --------------------------------------------------------
    # ENGINEERING ANALYSIS
    # --------------------------------------------------------

    parameters, checks = (
        run_engineering_checks(
            project,
            code
        )
    )

    print_engineering_checks(
        checks
    )

    print()

    print(
        "Engineering parameters:"
    )

    print(
        json.dumps(
            parameters,
            indent=4
        )
    )

    # --------------------------------------------------------
    # SCHEMATIC ANALYSIS
    # --------------------------------------------------------

    schematic_data = None

    schematic_file = project.get(
        "schematic_file"
    )

    schematic_analysis_status = {
        "status": "NOT_ATTEMPTED",
        "reason": None
    }

    if schematic_file:

        schematic_path = (
            PROJECT_ROOT / schematic_file
        )

        print()
        print(
            "Analyzing schematic..."
        )

        schematic_data = analyze_schematic(
            schematic_path
        )

        if (
            not schematic_data
            or
            schematic_data.get("error")
        ):

            error_message = (
                schematic_data.get("error")
                if schematic_data
                else "No schematic analysis result returned."
            )

            schematic_analysis_status = {
                "status": "UNAVAILABLE",
                "reason": str(error_message)
            }

            print()
            print(
                "Schematic analysis unavailable:"
            )

            print(
                error_message
            )

        else:

            schematic_analysis_status = {
                "status": "SUCCESS",
                "reason": None
            }

            print()
            print(
                "Schematic analysis:"
            )

            print(
                json.dumps(
                    schematic_data,
                    indent=4
                )
            )

    else:

        schematic_analysis_status = {
            "status": "NOT_AVAILABLE",
            "reason": (
                "No schematic file is associated "
                "with this project."
            )
        }

        print()
        print(
            "No schematic available for this project."
        )

    # --------------------------------------------------------
    # CODE ↔ SCHEMATIC VALIDATION
    # --------------------------------------------------------

    validation_results = []

    if (
        schematic_data
        and
        not schematic_data.get("error")
    ):

        validation_results = (
            validate_connections(
                parameters,
                schematic_data
            )
        )

    print()
    print(
        "========================================"
    )
    print(
        "      CODE ↔ SCHEMATIC VALIDATION"
    )
    print(
        "========================================"
    )

    if validation_results:

        for result in validation_results:

            print(
                f"{result['connection']} | "
                f"CODE: {result['code']} | "
                f"SCHEMATIC: {result['schematic']} | "
                f"{result['status']}"
            )

            print(
                f"→ {result['message']}"
            )

    else:

        print(
            "No validation results available."
        )

    # --------------------------------------------------------
    # VALIDATION SUMMARY
    # --------------------------------------------------------

    validation_summary = []

    for result in validation_results:

        if result["status"] == "MISMATCH":

            validation_summary.append(
                {
                    "connection": result[
                        "connection"
                    ],
                    "status": "CONFIRMED_MISMATCH",
                    "code": result["code"],
                    "schematic": result[
                        "schematic"
                    ]
                }
            )

        elif result["status"] == "PASS":

            validation_summary.append(
                {
                    "connection": result[
                        "connection"
                    ],
                    "status": "MATCH",
                    "code": result["code"],
                    "schematic": result[
                        "schematic"
                    ]
                }
            )

    # --------------------------------------------------------
    # EVIDENCE STATE
    # --------------------------------------------------------

    confirmed_mismatches = [
        item
        for item in validation_summary
        if item["status"] == "CONFIRMED_MISMATCH"
    ]

    code_failures = [
        check
        for check in checks
        if check["status"] == "FAIL"
    ]

    malfunction_established = False

    evidence_state = {

        "malfunction_established": (
            malfunction_established
        ),

        "confirmed_code_failures": (
            code_failures
        ),

        "confirmed_documentation_mismatches": (
            confirmed_mismatches
        ),

        "schematic_analysis_status": (
            schematic_analysis_status
        ),

        "physical_wiring_verified": False,

        "physical_hardware_tested": False
    }

    # --------------------------------------------------------
    # BUILD ENGINEERING EVIDENCE
    # --------------------------------------------------------

    evidence = {

        "user_problem": question,

        "diagnostic_interpretation": {
            "important": (
                "The user's problem description alone "
                "does not establish hardware malfunction."
            ),
            "malfunction_established": (
                malfunction_established
            )
        },

        "selected_project": project,

        "retrieval_score": score,

        "arduino_source_code": code,

        "engineering_parameters": parameters,

        "engineering_checks": checks,

        "schematic_analysis": schematic_data,

        "schematic_analysis_status": (
            schematic_analysis_status
        ),

        "connection_validation": validation_summary,

        "evidence_state": evidence_state
    }

    evidence_text = json.dumps(
        evidence,
        indent=2
    )

    # --------------------------------------------------------
    # LOCAL GEMMA
    # --------------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "       LOCAL GEMMA REASONING"
    )
    print(
        "========================================"
    )

    local_diagnosis = run_local_reasoning(
        evidence_text
    )

    print()
    print(
        local_diagnosis
    )

    # --------------------------------------------------------
    # GEMINI CLOUD REASONING
    # --------------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "       GEMINI CLOUD REASONING"
    )
    print(
        "========================================"
    )

    gemini_diagnosis = run_gemini_reasoning(
        evidence_text
    )

    print()
    print(
        gemini_diagnosis
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
