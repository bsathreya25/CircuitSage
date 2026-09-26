from evidence import CheckResult, ValidatorResult


def test_all_pass():

    checks = [
        CheckResult(
            check_id="HC001",
            name="TRIG pin defined",
            status="PASS",
            evidence="trigPin is assigned to pin 11.",
            source_file="test.ino",
            expected="TRIG pin must be defined",
            observed="trigPin = 11",
        ),
        CheckResult(
            check_id="HC002",
            name="ECHO pin defined",
            status="PASS",
            evidence="echoPin is assigned to pin 12.",
            source_file="test.ino",
            expected="ECHO pin must be defined",
            observed="echoPin = 12",
        ),
    ]

    result = ValidatorResult(
        validator_id="hcsr04_v1",
        component="HC-SR04",
        source_file="test.ino",
        checks=checks,
    )

    assert result.overall_status() == "PASS"
    assert result.passed == 2
    assert result.failed == 0
    assert result.unknown == 0


def test_unknown_does_not_become_fail():

    checks = [
        CheckResult(
            check_id="HC003",
            name="Schematic wiring verification",
            status="UNKNOWN",
            evidence="No schematic evidence was available.",
            source_file="test.ino",
            expected="Physical wiring should match firmware",
            observed="Not observable from source code",
        )
    ]

    result = ValidatorResult(
        validator_id="hcsr04_v1",
        component="HC-SR04",
        source_file="test.ino",
        checks=checks,
    )

    assert result.overall_status() == "UNKNOWN"
    assert result.failed == 0
    assert result.unknown == 1


def test_fail_overrides_unknown():

    checks = [
        CheckResult(
            check_id="HC004",
            name="TRIG configured OUTPUT",
            status="FAIL",
            evidence="TRIG pin is configured as INPUT.",
            source_file="test.ino",
            expected="OUTPUT",
            observed="INPUT",
        ),
        CheckResult(
            check_id="HC005",
            name="Physical wiring",
            status="UNKNOWN",
            evidence="No physical wiring evidence.",
        ),
    ]

    result = ValidatorResult(
        validator_id="hcsr04_v1",
        component="HC-SR04",
        source_file="test.ino",
        checks=checks,
    )

    assert result.overall_status() == "FAIL"
