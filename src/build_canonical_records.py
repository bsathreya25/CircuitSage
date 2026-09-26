import csv
import json
import re
from pathlib import Path

from read_arduino import (
    read_text_file,
    find_schematic,
    detect_components,
    detect_interfaces,
    extract_pins,
    extract_pin_modes,
    extract_digital_operations,
    extract_analog_operations,
    extract_timing,
    extract_baud_rate,
    detect_special_fields,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_ROOT = PROJECT_ROOT / "data" / "canonical"
MANIFEST_FILE = (
    PROJECT_ROOT
    / "knowledge_base"
    / "canonical_project_manifest.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT
    / "knowledge_base"
    / "canonical_records.json"
)


def project_id_from_name(name):
    match = re.match(r"^\s*(\d+)\s*[-–—]", name)
    return int(match.group(1)) if match else None


def load_canonical_manifest():
    records = []

    with open(
        MANIFEST_FILE,
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            project_name = row["project_name"].strip()
            project_id = project_id_from_name(project_name)

            # 421 - LoRa_AT is the known alias of 276 - LoRa_AT.
            if project_id == 421:
                continue

            if project_id is None:
                raise ValueError(
                    f"Could not determine project ID: {project_name}"
                )

            records.append(
                {
                    "project_id": project_id,
                    "project_name": project_name,
                    "category": infer_category(row),
                }
            )

    # Remove accidental duplicates by project ID.
    unique = {}

    for record in records:
        unique[record["project_id"]] = record

    records = list(unique.values())

    if len(records) != 89:
        raise ValueError(
            f"Expected 89 canonical projects, got {len(records)}"
        )

    return sorted(
        records,
        key=lambda record: record["project_id"],
    )


def infer_category(row):
    if row.get("wifi") == "True":
        return "Wi-Fi / ESP / IoT"

    if (
        row.get("gsm") == "True"
        or row.get("gps") == "True"
        or row.get("lora") == "True"
    ):
        return "GSM / GPS / LoRa"

    if (
        row.get("bluetooth") == "True"
        or row.get("rf") == "True"
    ):
        return "Wireless / RF / Bluetooth"

    if (
        row.get("motor") == "True"
        or row.get("servo") == "True"
    ):
        return "Motors / Robotics / Control"

    if row.get("sensor") == "True":
        return "Sensors & Measurement"

    if row.get("display") == "True":
        return "RFID / Displays / Interfaces"

    if row.get("storage") == "True":
        return "Advanced / Multi-file / Specialized"

    if (
        row.get("timing") == "True"
        or row.get("interrupts") == "True"
    ):
        return "Timing / Measurement Systems"

    return "Uncategorized"


def find_project_folder(project_name):
    matches = [
        path
        for path in CANONICAL_ROOT.iterdir()
        if path.is_dir() and path.name == project_name
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one canonical folder for "
            f"{project_name}, found {len(matches)}"
        )

    return matches[0]


def source_files_for_project(project_folder):
    extensions = {".ino", ".cpp", ".h"}

    return sorted(
        path
        for path in project_folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in extensions
    )


def artifact_files_for_project(project_folder):
    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".pdf",
    }

    return sorted(
        path
        for path in project_folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in extensions
    )


def relative_path(path):
    return str(path.relative_to(PROJECT_ROOT))


def build_source_summary(source_files):
    combined_code = []

    for source_file in source_files:
        text = read_text_file(source_file)

        if text:
            combined_code.append(text)

    return "\n\n".join(combined_code)


def detect_diagnostic_signals(
    code,
    components,
    interfaces,
    pins,
    timing,
):
    signals = []

    if "HC-SR04" in components:
        signals.extend(
            [
                "trigger_pin",
                "echo_pin",
                "trigger_pulse",
                "pulseIn_echo",
                "distance_calculation",
            ]
        )

    if "DHT11" in components or "DHT22" in components:
        signals.append("sensor_data_pin")

    if "I2C" in interfaces:
        signals.append("i2c_bus")

    if "SPI" in interfaces:
        signals.append("spi_bus")

    if "UART/Serial" in interfaces:
        signals.append("serial_communication")

    if timing.get("delay_microseconds"):
        signals.append("microsecond_timing")

    if timing.get("pulseIn"):
        signals.append("pulse_width_measurement")

    if any(
        operation["type"] == "analogRead"
        for operation in extract_analog_operations(code)
    ):
        signals.append("analog_input")

    if any(
        operation["type"] == "analogWrite"
        for operation in extract_analog_operations(code)
    ):
        signals.append("pwm_output")

    if any(
        operation["type"] == "digitalRead"
        for operation in extract_digital_operations(code)
    ):
        signals.append("digital_input")

    if any(
        operation["type"] == "digitalWrite"
        for operation in extract_digital_operations(code)
    ):
        signals.append("digital_output")

    return sorted(set(signals))


def build_record(project):
    project_name = project["project_name"]
    project_id = project["project_id"]
    category = project["category"]

    project_folder = find_project_folder(project_name)

    source_files = source_files_for_project(project_folder)
    artifact_files = artifact_files_for_project(project_folder)

    if not source_files:
        code = ""
    else:
        code = build_source_summary(source_files)

    libraries = sorted(
        set(
            re.findall(
                r'#include\s*[<"]([^>"]+)[>"]',
                code,
                re.IGNORECASE,
            )
        )
    )

    components = detect_components(code)
    interfaces = detect_interfaces(code, libraries)
    pins = extract_pins(code)
    pin_modes = extract_pin_modes(code)
    digital_operations = extract_digital_operations(code)
    analog_operations = extract_analog_operations(code)
    timing = extract_timing(code)
    baud_rate = extract_baud_rate(code)

    special_fields = detect_special_fields(
        project_name,
        components,
        pins,
        code,
    )

    interface_flags = {
        "uart": "UART/Serial" in interfaces,
        "i2c": "I2C" in interfaces,
        "spi": "SPI" in interfaces,
        "wifi": bool(
            re.search(
                r"\b(WiFi|ESP8266WiFi|ESP32|AsyncWebServer)\b",
                code,
                re.IGNORECASE,
            )
        ),
        "bluetooth": bool(
            re.search(
                r"\b(Bluetooth|BT|PS4|PS3|HC05|HC-05)\b",
                code,
                re.IGNORECASE,
            )
        ),
        "rf": bool(
            re.search(
                r"\b(nRF24|RF24|RCSwitch|RF)\b",
                code,
                re.IGNORECASE,
            )
        ),
        "gsm": bool(
            re.search(
                r"\b(GSM|SIM900|SIM800)\b",
                code,
                re.IGNORECASE,
            )
        ),
        "gps": bool(
            re.search(
                r"\b(GPS|TinyGPS)\b",
                code,
                re.IGNORECASE,
            )
        ),
        "lora": bool(
            re.search(
                r"\b(LoRa|SX127|AT\+)\b",
                code,
                re.IGNORECASE,
            )
        ),
    }

    known_unknowns = []

    if not source_files:
        known_unknowns.append(
            "No direct source files were found."
        )

    if not artifact_files:
        known_unknowns.append(
            "No schematic/image/PDF artifact was found."
        )

    diagnostic_signals = detect_diagnostic_signals(
        code,
        components,
        interfaces,
        pins,
        timing,
    )

    record = {
        "project_id": project_id,
        "project_name": project_name,
        "category": category,

        "source_files": [
            relative_path(path)
            for path in source_files
        ],

        "artifact_files": [
            relative_path(path)
            for path in artifact_files
        ],

        "libraries": libraries,

        "interfaces": interface_flags,

        "pins": [
            {
                "name": name,
                "value": value,
                "mode": pin_modes.get(name),
            }
            for name, value in sorted(pins.items())
        ],

        "components": sorted(components),

        "timing": timing,

        "diagnostic_signals": diagnostic_signals,

        "known_unknowns": known_unknowns,

        "provenance": {
            "canonical": True,
            "project_id": project_id,
            "source_directory": relative_path(
                project_folder
            ),
            "source_file_count": len(source_files),
            "artifact_file_count": len(artifact_files),
            "special_fields": special_fields,
            "baud_rate": baud_rate,
            "digital_operations": digital_operations,
            "analog_operations": analog_operations,
        },
    }

    return record


def main():
    print("Loading canonical manifest...")

    projects = load_canonical_manifest()

    print(
        f"Canonical projects loaded: {len(projects)}"
    )

    records = []

    for index, project in enumerate(projects, start=1):
        print(
            f"[{index:02d}/89] "
            f"{project['project_id']} - "
            f"{project['project_name']}"
        )

        record = build_record(project)
        records.append(record)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=2,
        )

    print("\n========================================")
    print("CANONICAL RECORD BUILD COMPLETE")
    print("========================================")
    print(f"Records generated : {len(records)}")
    print(f"Output            : {OUTPUT_FILE}")
    print("Old project_records.json was NOT modified.")


if __name__ == "__main__":
    main()
