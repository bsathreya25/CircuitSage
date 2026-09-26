import json
import re
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
KNOWLEDGE_BASE_FILE = KNOWLEDGE_BASE_DIR / "project_records.json"


# ============================================================
# KNOWN COMPONENTS
# ============================================================

COMPONENT_PATTERNS = {
    "DHT11": r"\bDHT11\b",
    "DHT22": r"\bDHT22\b",
    "HC-SR04": r"\bHC[-_ ]?SR04\b",
    "BMP180": r"\bBMP180\b",
    "BMP280": r"\bBMP280\b",
    "DS18B20": r"\bDS18B20\b",
    "DS1307": r"\bDS1307\b",
    "DS3231": r"\bDS3231\b",
    "MQ-2": r"\bMQ[-_ ]?2\b",
    "PIR": r"\bPIR\b",
    "FC-37": r"\bFC[-_ ]?37\b",
    "YL-69": r"\bYL[-_ ]?69\b",
    "HL-69": r"\bHL[-_ ]?69\b",
    "Servo": r"\bServo\b",
    "LCD": r"\bLCD\b",
    "Keypad": r"\bKeypad\b",
    "MPU6050": r"\bMPU[-_ ]?6050\b",
}


# ============================================================
# REGEX PATTERNS
# ============================================================

LIBRARY_PATTERN = re.compile(
    r'#include\s*[<"]([^>"]+)[>"]',
    re.IGNORECASE
)

DEFINE_PATTERN = re.compile(
    r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$',
    re.MULTILINE
)

PIN_MODE_PATTERN = re.compile(
    r'\bpinMode\s*\(\s*([^,]+?)\s*,\s*(INPUT_PULLUP|INPUT|OUTPUT)\s*\)',
    re.IGNORECASE
)

DIGITAL_WRITE_PATTERN = re.compile(
    r'\bdigitalWrite\s*\(\s*([^,]+?)\s*,\s*(HIGH|LOW)\s*\)',
    re.IGNORECASE
)

DIGITAL_READ_PATTERN = re.compile(
    r'\bdigitalRead\s*\(\s*([^)]+?)\s*\)',
    re.IGNORECASE
)

ANALOG_WRITE_PATTERN = re.compile(
    r'\banalogWrite\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)',
    re.IGNORECASE
)

ANALOG_READ_PATTERN = re.compile(
    r'\banalogRead\s*\(\s*([^)]+?)\s*\)',
    re.IGNORECASE
)

SERIAL_BAUD_PATTERN = re.compile(
    r'\bSerial(?:\w*)?\s*\.\s*begin\s*\(\s*(\d+)',
    re.IGNORECASE
)

DELAY_PATTERN = re.compile(
    r'\bdelay\s*\(\s*(\d+)\s*\)',
    re.IGNORECASE
)

DELAY_MICROSECONDS_PATTERN = re.compile(
    r'\bdelayMicroseconds\s*\(\s*(\d+)\s*\)',
    re.IGNORECASE
)

PULSE_IN_PATTERN = re.compile(
    r'\bpulseIn\s*\(\s*([^,]+?)\s*,\s*(HIGH|LOW)',
    re.IGNORECASE
)


# ============================================================
# FILE READING
# ============================================================

def read_text_file(path):
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as error:
        print(f"Could not read {path}: {error}")
        return ""


# ============================================================
# SCHEMATIC DISCOVERY
# ============================================================

def find_schematic(project_folder):
    extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    }

    for file in sorted(project_folder.iterdir()):
        if (
            file.is_file()
            and file.suffix.lower() in extensions
        ):
            return str(
                file.relative_to(PROJECT_ROOT)
            )

    return None


# ============================================================
# COMPONENT DETECTION
# ============================================================

def detect_components(code):
    components = []

    for component, pattern in COMPONENT_PATTERNS.items():
        if re.search(
            pattern,
            code,
            re.IGNORECASE
        ):
            components.append(component)

    return components


# ============================================================
# INTERFACE DETECTION
# ============================================================

def detect_interfaces(code, libraries):
    interfaces = []

    if (
        re.search(r'\bWire\s*\.', code)
        or any("Wire" in library for library in libraries)
    ):
        interfaces.append("I2C")

    if (
        re.search(r'\bSPI\s*\.', code)
        or any("SPI" in library for library in libraries)
    ):
        interfaces.append("SPI")

    if re.search(
        r'\bSerial\s*\.',
        code
    ):
        interfaces.append("UART/Serial")

    return interfaces


# ============================================================
# PIN EXTRACTION
# ============================================================

def extract_pins(code):
    """
    Extract Arduino pin assignments from common coding styles.

    Supported examples:

        #define TRIG_PIN 9
        #define ECHO_PIN 10

        int trigPin = 11;
        int echoPin = 12;

        const int sensorPin = 7;
        byte ledPin = 13;
    """

    pins = {}

    # --------------------------------------------------------
    # 1. #define STYLE
    # --------------------------------------------------------

    defines = dict(
        DEFINE_PATTERN.findall(code)
    )

    for name, value in defines.items():

        if "PIN" in name.upper():

            cleaned_value = value.strip()

            cleaned_value = cleaned_value.split(
                "//"
            )[0].strip()

            pins[name] = cleaned_value

    # --------------------------------------------------------
    # 2. VARIABLE DECLARATION STYLE
    # --------------------------------------------------------

    variable_pin_pattern = re.compile(
        r'\b(?:const\s+)?'
        r'(?:int|byte|uint8_t|uint16_t|uint32_t|long)'
        r'\s+'
        r'([A-Za-z_][A-Za-z0-9_]*[Pp][Ii][Nn])'
        r'\s*=\s*'
        r'(\d+)'
        r'\s*;'
    )

    for name, value in variable_pin_pattern.findall(code):
        pins[name] = value

    return pins


# ============================================================
# PIN MODES
# ============================================================

def extract_pin_modes(code):
    modes = {}

    for pin, mode in PIN_MODE_PATTERN.findall(code):

        modes[pin.strip()] = mode.upper()

    return modes


# ============================================================
# DIGITAL OPERATIONS
# ============================================================

def extract_digital_operations(code):
    operations = []

    for pin, value in DIGITAL_WRITE_PATTERN.findall(code):

        operations.append(
            {
                "type": "digitalWrite",
                "pin": pin.strip(),
                "value": value.upper(),
            }
        )

    for pin in DIGITAL_READ_PATTERN.findall(code):

        operations.append(
            {
                "type": "digitalRead",
                "pin": pin.strip(),
            }
        )

    return operations


# ============================================================
# ANALOG OPERATIONS
# ============================================================

def extract_analog_operations(code):
    operations = []

    for pin, value in ANALOG_WRITE_PATTERN.findall(code):

        operations.append(
            {
                "type": "analogWrite",
                "pin": pin.strip(),
                "value": value.strip(),
            }
        )

    for pin in ANALOG_READ_PATTERN.findall(code):

        operations.append(
            {
                "type": "analogRead",
                "pin": pin.strip(),
            }
        )

    return operations


# ============================================================
# TIMING EXTRACTION
# ============================================================

def extract_timing(code):

    delays_ms = [
        int(value)
        for value in DELAY_PATTERN.findall(code)
    ]

    delays_us = [
        int(value)
        for value in DELAY_MICROSECONDS_PATTERN.findall(code)
    ]

    pulse_measurements = []

    for pin, state in PULSE_IN_PATTERN.findall(code):

        pulse_measurements.append(
            {
                "pin": pin.strip(),
                "state": state.upper(),
            }
        )

    return {
        "delay_ms": delays_ms,
        "delay_microseconds": delays_us,
        "pulseIn": pulse_measurements,
    }


# ============================================================
# SERIAL BAUD RATE
# ============================================================

def extract_baud_rate(code):

    matches = SERIAL_BAUD_PATTERN.findall(code)

    if not matches:
        return None

    return int(matches[0])


# ============================================================
# SPECIAL SENSOR FIELDS
# ============================================================

def detect_special_fields(
    project_name,
    components,
    pins,
    code
):
    fields = {}

    # --------------------------------------------------------
    # HC-SR04
    # --------------------------------------------------------

    if "HC-SR04" in components:

        trigger_pin = None
        echo_pin = None

        # Common #define naming
        if "TRIG_PIN" in pins:
            trigger_pin = pins["TRIG_PIN"]

        if "ECHO_PIN" in pins:
            echo_pin = pins["ECHO_PIN"]

        # Common variable naming
        if "trigPin" in pins:
            trigger_pin = pins["trigPin"]

        if "echoPin" in pins:
            echo_pin = pins["echoPin"]

        # Case-insensitive fallback
        for name, value in pins.items():

            normalized = name.lower()

            if normalized == "trigpin":
                trigger_pin = value

            elif normalized == "echopin":
                echo_pin = value

        if trigger_pin is not None:
            fields["trigger_pin"] = trigger_pin

        if echo_pin is not None:
            fields["echo_pin"] = echo_pin

        fields["sensor"] = "HC-SR04"

    # --------------------------------------------------------
    # DHT11
    # --------------------------------------------------------

    elif "DHT11" in components:

        data_pin = pins.get("DHTPIN")

        if data_pin is not None:
            fields["data_pin"] = data_pin

        fields["sensor"] = "DHT11"

    # --------------------------------------------------------
    # DHT22
    # --------------------------------------------------------

    elif "DHT22" in components:

        data_pin = pins.get("DHTPIN")

        if data_pin is not None:
            fields["data_pin"] = data_pin

        fields["sensor"] = "DHT22"

    return fields


# ============================================================
# BUILD PROJECT RECORD
# ============================================================

def build_project_record(code_file):

    code = read_text_file(code_file)

    if not code:
        return None

    project_folder = code_file.parent

    project_name = project_folder.name

    libraries = LIBRARY_PATTERN.findall(code)

    defines = dict(
        DEFINE_PATTERN.findall(code)
    )

    pins = extract_pins(code)

    pin_modes = extract_pin_modes(code)

    digital_operations = (
        extract_digital_operations(code)
    )

    analog_operations = (
        extract_analog_operations(code)
    )

    timing = extract_timing(code)

    baud_rate = extract_baud_rate(code)

    components = detect_components(code)

    interfaces = detect_interfaces(
        code,
        libraries
    )

    schematic_file = find_schematic(
        project_folder
    )

    record = {
        "project_name": project_name,

        "components": components,

        "libraries": libraries,

        "pins": pins,

        "pin_modes": pin_modes,

        "interfaces": interfaces,

        "operations": {
            "digital": digital_operations,
            "analog": analog_operations,
        },

        "timing": timing,

        "baud_rate": baud_rate,

        "defines": defines,

        "code_file": str(
            code_file.relative_to(PROJECT_ROOT)
        ),

        "schematic_file": schematic_file,
    }

    special_fields = detect_special_fields(
        project_name,
        components,
        pins,
        code
    )

    record.update(
        special_fields
    )

    return record


# ============================================================
# LOAD EXISTING KNOWLEDGE BASE
# ============================================================

def load_existing_records():

    if not KNOWLEDGE_BASE_FILE.exists():
        return []

    try:

        with open(
            KNOWLEDGE_BASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception as error:

        print(
            f"Could not load existing knowledge base: {error}"
        )

    return []


# ============================================================
# UPDATE RECORDS
# ============================================================

def update_records(
    existing_records,
    new_records
):

    records_by_code_file = {
        record.get("code_file"): record
        for record in existing_records
        if record.get("code_file")
    }

    for record in new_records:

        records_by_code_file[
            record["code_file"]
        ] = record

    return sorted(
        records_by_code_file.values(),
        key=lambda record:
            record.get(
                "project_name",
                ""
            ).lower()
    )


# ============================================================
# FIND ARDUINO PROJECTS
# ============================================================

def find_arduino_projects():

    return sorted(
        DATA_DIR.rglob("*.ino")
    )


# ============================================================
# SAVE KNOWLEDGE BASE
# ============================================================

def save_knowledge_base(records):

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        KNOWLEDGE_BASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4
        )

    print(
        "\nKnowledge base saved successfully!"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Scanning Arduino projects..."
    )

    code_files = find_arduino_projects()

    print(
        f"\nArduino projects found: {len(code_files)}"
    )

    new_records = []

    for code_file in code_files:

        print(
            f"- {code_file}"
        )

        record = build_project_record(
            code_file
        )

        if record:
            new_records.append(record)

    existing_records = (
        load_existing_records()
    )

    final_records = update_records(
        existing_records,
        new_records
    )

    save_knowledge_base(
        final_records
    )

    print(
        f"Total knowledge-base records: "
        f"{len(final_records)}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
