from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src")
)

from diagnostics.validators import (
    read_source_file,
    check_hcsr04
)


TEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "Ultrasonic_Sensor_HC-SR04"
    / "Ultrasonic_Sensor_HC-SR04.ino"
)


def main():

    print("=" * 60)
    print("CIRCUITSAGE HC-SR04 DETERMINISTIC VALIDATOR")
    print("=" * 60)

    print()
    print("Source:", TEST_FILE)

    source = read_source_file(TEST_FILE)

    result = check_hcsr04(source)

    print()
    print("Validator:", result["validator"])
    print()

    for check in result["checks"]:

        print(
            f"{check['status']:7} | "
            f"{check['check']}"
        )

        print(
            f"         {check['evidence']}"
        )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
