from pathlib import Path

from validators import read_source_file, run_hcsr04_validator


def test_hcsr04_produces_evidence_result():

    # test_validator_evidence.py
    #       ↓ parent = diagnostics
    #       ↓ parent = src
    #       ↓ parent = ai-hackaton
    project_root = Path(__file__).resolve().parents[2]

    source_path = (
        project_root
        / "data"
        / "Ultrasonic_Sensor_HC-SR04"
        / "Ultrasonic_Sensor_HC-SR04.ino"
    )

    assert source_path.exists(), (
        f"HC-SR04 source file not found: {source_path}"
    )

    source = read_source_file(source_path)

    result = run_hcsr04_validator(
        source,
        source_file=str(source_path),
    )

    assert result.component == "HC-SR04"
    assert len(result.checks) == 8

    assert result.overall_status() == "PASS"

    assert result.passed == 8
    assert result.failed == 0
    assert result.unknown == 0
