from pathlib import Path

from evidence_package import EvidencePackage
from validators import read_source_file, run_hcsr04_validator
from reasoning_pipeline import run_reasoning_pipeline


def main():
    project_root = Path(__file__).resolve().parents[2]

    source_path = (
        project_root
        / "data"
        / "Ultrasonic_Sensor_HC-SR04"
        / "Ultrasonic_Sensor_HC-SR04.ino"
    )

    if not source_path.exists():
        raise FileNotFoundError(
            f"HC-SR04 source file not found: {source_path}"
        )

    # --------------------------------------------------
    # 1. Read real Arduino source
    # --------------------------------------------------

    source = read_source_file(source_path)

    # --------------------------------------------------
    # 2. Run deterministic engineering validation
    # --------------------------------------------------

    validator_result = run_hcsr04_validator(
        source,
        source_file=str(source_path),
    )

    # --------------------------------------------------
    # 3. Build Evidence Package
    # --------------------------------------------------

    package = EvidencePackage(
        user_query=(
            "The HC-SR04 ultrasonic sensor is not giving "
            "the expected distance reading."
        ),
        scope_status="SUPPORTED",
        component="HC-SR04",

        retrieved_projects=[
            {
                "project_id": 8,
                "project_name": "HC-SR04 Ultrasonic",
                "evidence_level": "HIGH",
            }
        ],

        validator_result=validator_result.to_dict(),

        schematic_evidence=[],

        engineering_parameters={
            "sensor": "HC-SR04",
            "trigger_pin": "11",
            "echo_pin": "12",
            "serial_baud": 9600,
            "loop_delay_ms": 250,
            "trigger_pulse_us": 10,
        },

        known_unknowns=[
            "Physical wiring has not been verified.",
            "Physical sensor response has not been verified.",
            "Power supply has not been physically measured.",
            "Serial Monitor output has not been observed.",
            "Schematic analysis is unavailable.",
        ],
    )

    # --------------------------------------------------
    # 4. Run REAL Gemma + validation pipeline
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("CIRCUITSAGE — REAL REASONING PIPELINE")
    print("=" * 70)

    print("\nDETERMINISTIC VALIDATION")
    print("-" * 70)

    print(f"Overall status : {validator_result.overall_status()}")
    print(f"Passed         : {validator_result.passed}")
    print(f"Failed         : {validator_result.failed}")
    print(f"Unknown        : {validator_result.unknown}")

    print("\nRUNNING REAL GEMMA 3:4B...")
    print("-" * 70)

    result = run_reasoning_pipeline(package)

    # --------------------------------------------------
    # 5. Display validation result
    # --------------------------------------------------

    print("\nPIPELINE RESULT")
    print("-" * 70)

    print(f"Accepted : {result['accepted']}")

    print("\nVALIDATION")
    print("-" * 70)

    print(result["validation"])

    print("\nGEMMA DIAGNOSIS")
    print("-" * 70)

    print(result["diagnosis"])

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()