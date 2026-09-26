import re
from typing import Callable, Dict, Optional

from diagnostics.evidence import CheckResult, ValidatorResult


# ============================================================
# Shared helpers
# ============================================================

def _line_number(
    source: str,
    pattern: str,
    flags: int = re.IGNORECASE,
):
    regex = re.compile(pattern, flags)

    for line_number, line in enumerate(
        source.splitlines(),
        start=1,
    ):
        if regex.search(line):
            return line_number

    return None


def _check(
    check_id: str,
    name: str,
    status: str,
    evidence: str,
    source_file: str,
    line_reference: Optional[int] = None,
    expected: Optional[str] = None,
    observed: Optional[str] = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=name,
        status=status,
        evidence=evidence,
        source_file=source_file,
        line_reference=(
            str(line_reference)
            if line_reference is not None
            else None
        ),
        expected=expected,
        observed=observed,
    )


def _has(source: str, pattern: str):
    return re.search(
        pattern,
        source,
        re.IGNORECASE,
    )


def _result(
    validator_id: str,
    component: str,
    source_file: str,
    checks,
):
    return ValidatorResult(
        validator_id=validator_id,
        component=component,
        source_file=source_file,
        checks=checks,
    )


# ============================================================
# DHT11 / DHT22
# ============================================================

def run_dht_validator(
    source: str,
    source_file: str = "unknown",
) -> ValidatorResult:

    checks = []

    # DHT001 — DHT library
    match = _has(
        source,
        r'#include\s*[<"]DHT\.h[>"]',
    )

    checks.append(
        _check(
            "DHT001",
            "DHT library included",
            "PASS" if match else "UNKNOWN",
            (
                "DHT.h library include was detected."
                if match
                else
                "No DHT.h library include was detected."
            ),
            source_file,
            _line_number(
                source,
                r'#include\s*[<"]DHT\.h[>"]',
            ),
            "The DHT library should be included.",
            (
                "DHT.h include detected."
                if match
                else
                "No DHT.h include detected."
            ),
        )
    )

    # DHT002 — sensor type
    type_match = re.search(
        r'#define\s+DHTTYPE\s+(DHT11|DHT22)',
        source,
        re.IGNORECASE,
    )

    if type_match:
        sensor_type = type_match.group(1).upper()

        checks.append(
            _check(
                "DHT002",
                "DHT sensor type defined",
                "PASS",
                f"DHT sensor type defined as {sensor_type}.",
                source_file,
                _line_number(
                    source,
                    r'#define\s+DHTTYPE\s+(DHT11|DHT22)',
                ),
                "DHT11 or DHT22 should be explicitly identified.",
                f"DHTTYPE = {sensor_type}",
            )
        )
    else:
        checks.append(
            _check(
                "DHT002",
                "DHT sensor type defined",
                "UNKNOWN",
                "No DHT11/DHT22 type definition was detected.",
                source_file,
                None,
                "DHT11 or DHT22 should be explicitly identified.",
                "No matching DHTTYPE definition detected.",
            )
        )

    # DHT003 — sensor pin
    pin_match = re.search(
        r'#define\s+DHTPIN\s+(\d+)',
        source,
        re.IGNORECASE,
    )

    if pin_match:
        checks.append(
            _check(
                "DHT003",
                "DHT data pin defined",
                "PASS",
                f"DHT data pin defined as {pin_match.group(1)}.",
                source_file,
                _line_number(
                    source,
                    r'#define\s+DHTPIN\s+\d+',
                ),
                "A DHT data pin should be defined.",
                f"DHTPIN = {pin_match.group(1)}",
            )
        )
    else:
        checks.append(
            _check(
                "DHT003",
                "DHT data pin defined",
                "UNKNOWN",
                "No DHTPIN definition was detected.",
                source_file,
                None,
                "A DHT data pin should be defined.",
                "No DHTPIN definition detected.",
            )
        )

    # DHT004 — object initialization
    object_match = _has(
        source,
        r'\bDHT\s+\w+\s*\(\s*DHTPIN\s*,\s*DHTTYPE\s*\)',
    )

    checks.append(
        _check(
            "DHT004",
            "DHT sensor object initialized",
            "PASS" if object_match else "UNKNOWN",
            (
                "A DHT sensor object using DHTPIN and DHTTYPE "
                "was detected."
                if object_match
                else
                "No DHT object using DHTPIN and DHTTYPE was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\bDHT\s+\w+\s*\(\s*DHTPIN\s*,\s*DHTTYPE\s*\)',
            ),
            "The DHT object should be constructed from the sensor pin and type.",
            (
                "DHT(DHTPIN, DHTTYPE) detected."
                if object_match
                else
                "No matching DHT constructor detected."
            ),
        )
    )

    # DHT005 — begin()
    begin_match = _has(
        source,
        r'\b\w+\.begin\s*\(\s*\)',
    )

    checks.append(
        _check(
            "DHT005",
            "DHT sensor initialized",
            "PASS" if begin_match else "UNKNOWN",
            (
                "A sensor begin() call was detected."
                if begin_match
                else
                "No sensor begin() call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.begin\s*\(\s*\)',
            ),
            "The DHT sensor should be initialized.",
            (
                "begin() call detected."
                if begin_match
                else
                "No begin() call detected."
            ),
        )
    )

    # DHT006 — humidity read
    humidity_match = _has(
        source,
        r'\.readHumidity\s*\(\s*\)',
    )

    checks.append(
        _check(
            "DHT006",
            "Humidity reading performed",
            "PASS" if humidity_match else "UNKNOWN",
            (
                "readHumidity() was detected."
                if humidity_match
                else
                "No readHumidity() call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\.readHumidity\s*\(\s*\)',
            ),
            "Humidity data should be requested from the sensor.",
            (
                "readHumidity() detected."
                if humidity_match
                else
                "No humidity read detected."
            ),
        )
    )

    # DHT007 — temperature read
    temperature_match = _has(
        source,
        r'\.readTemperature\s*\(',
    )

    checks.append(
        _check(
            "DHT007",
            "Temperature reading performed",
            "PASS" if temperature_match else "UNKNOWN",
            (
                "readTemperature() was detected."
                if temperature_match
                else
                "No readTemperature() call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\.readTemperature\s*\(',
            ),
            "Temperature data should be requested from the sensor.",
            (
                "readTemperature() detected."
                if temperature_match
                else
                "No temperature read detected."
            ),
        )
    )

    # DHT008 — Serial output
    serial_match = _has(
        source,
        r'Serial\.(print|println)\s*\(',
    )

    checks.append(
        _check(
            "DHT008",
            "Serial output",
            "PASS" if serial_match else "UNKNOWN",
            (
                "Serial output statements were detected."
                if serial_match
                else
                "No Serial.print/Serial.println statement was detected."
            ),
            source_file,
            _line_number(
                source,
                r'Serial\.(print|println)\s*\(',
            ),
            "Diagnostic/output information should be available through Serial.",
            (
                "Serial output detected."
                if serial_match
                else
                "No Serial output detected."
            ),
        )
    )

    return _result(
        "dht_v1",
        "DHT11/DHT22",
        source_file,
        checks,
    )


# ============================================================
# MPU6050
# ============================================================

def run_mpu6050_validator(
    source: str,
    source_file: str = "unknown",
) -> ValidatorResult:

    checks = []

    # MPU001 — MPU6050 library
    library_match = _has(
        source,
        r'#include\s*[<"].*MPU6050.*[>"]',
    )

    checks.append(
        _check(
            "MPU001",
            "MPU6050 library included",
            "PASS" if library_match else "UNKNOWN",
            (
                "An MPU6050 library include was detected."
                if library_match
                else
                "No MPU6050 library include was detected."
            ),
            source_file,
            _line_number(
                source,
                r'#include\s*[<"].*MPU6050.*[>"]',
            ),
            "An MPU6050 library should be included.",
            (
                "MPU6050 include detected."
                if library_match
                else
                "No MPU6050 include detected."
            ),
        )
    )

    # MPU002 — I2C/Wire
    wire_match = _has(
        source,
        r'#include\s*[<"]Wire\.h[>"]',
    )

    wire_begin_match = _has(
        source,
        r'\bWire\.begin\s*\(',
    )

    if wire_match or wire_begin_match:
        line = (
            _line_number(
                source,
                r'\bWire\.begin\s*\(',
            )
            or _line_number(
                source,
                r'#include\s*[<"]Wire\.h[>"]',
            )
        )

        checks.append(
            _check(
                "MPU002",
                "I2C interface detected",
                "PASS",
                "Wire/I2C support was detected in the source.",
                source_file,
                line,
                "The MPU6050 communication path should expose I2C support.",
                "Wire/I2C support detected.",
            )
        )
    else:
        checks.append(
            _check(
                "MPU002",
                "I2C interface detected",
                "UNKNOWN",
                "No Wire.h or Wire.begin() usage was detected.",
                source_file,
                None,
                "I2C communication support should be detectable.",
                "No explicit Wire/I2C usage detected.",
            )
        )

    # MPU003 — object
    object_match = _has(
        source,
        r'\bMPU6050\s+\w+\s*(?:\([^;]*\))?\s*;',
    )

    checks.append(
        _check(
            "MPU003",
            "MPU6050 object declared",
            "PASS" if object_match else "UNKNOWN",
            (
                "An MPU6050 object declaration was detected."
                if object_match
                else
                "No MPU6050 object declaration was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\bMPU6050\s+\w+\s*(?:\([^;]*\))?\s*;',
            ),
            "An MPU6050 device object should be declared.",
            (
                "MPU6050 object detected."
                if object_match
                else
                "No MPU6050 object detected."
            ),
        )
    )

    # MPU004 — initialize
    initialize_match = _has(
        source,
        r'\b\w+\.initialize\s*\(\s*\)',
    )

    checks.append(
        _check(
            "MPU004",
            "MPU6050 initialized",
            "PASS" if initialize_match else "UNKNOWN",
            (
                "An MPU6050 initialize() call was detected."
                if initialize_match
                else
                "No MPU6050 initialize() call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.initialize\s*\(\s*\)',
            ),
            "The MPU6050 device should be initialized.",
            (
                "initialize() detected."
                if initialize_match
                else
                "No initialize() call detected."
            ),
        )
    )

    # MPU005 — connection test
    connection_match = _has(
        source,
        r'\b\w+\.testConnection\s*\(\s*\)',
    )

    checks.append(
        _check(
            "MPU005",
            "MPU6050 connection check",
            "PASS" if connection_match else "UNKNOWN",
            (
                "An MPU6050 testConnection() call was detected."
                if connection_match
                else
                "No MPU6050 testConnection() call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.testConnection\s*\(\s*\)',
            ),
            "The source should provide an explicit connection check when available.",
            (
                "testConnection() detected."
                if connection_match
                else
                "No connection test detected."
            ),
        )
    )

    # MPU006 — sensor/DMP operation
    data_operation_match = _has(
        source,
        r'\b\w+\.(dmpInitialize|getMotion|getAcceleration|getRotation)\s*\(',
    )

    checks.append(
        _check(
            "MPU006",
            "MPU6050 data/DMP operation",
            "PASS" if data_operation_match else "UNKNOWN",
            (
                "An MPU6050 data or DMP operation was detected."
                if data_operation_match
                else
                "No recognized MPU6050 data/DMP operation was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.(dmpInitialize|getMotion|getAcceleration|getRotation)\s*\(',
            ),
            "The source should perform a recognizable MPU6050 operation.",
            (
                "MPU6050 data/DMP operation detected."
                if data_operation_match
                else
                "No recognized data/DMP operation detected."
            ),
        )
    )

    # MPU007 — serial output
    serial_match = _has(
        source,
        r'Serial\.(print|println)\s*\(',
    )

    checks.append(
        _check(
            "MPU007",
            "Serial output",
            "PASS" if serial_match else "UNKNOWN",
            (
                "Serial output statements were detected."
                if serial_match
                else
                "No Serial output statements were detected."
            ),
            source_file,
            _line_number(
                source,
                r'Serial\.(print|println)\s*\(',
            ),
            "Diagnostic information should be observable through Serial.",
            (
                "Serial output detected."
                if serial_match
                else
                "No Serial output detected."
            ),
        )
    )

    return _result(
        "mpu6050_v1",
        "MPU6050",
        source_file,
        checks,
    )


# ============================================================
# nRF24L01
# ============================================================

def run_nrf24_validator(
    source: str,
    source_file: str = "unknown",
) -> ValidatorResult:

    checks = []

    # NRF001 — RF24/nRF24 library
    library_match = _has(
        source,
        r'#include\s*[<"].*(RH_NRF24|RF24).*',
    )

    spi_match = _has(
        source,
        r'#include\s*[<"]SPI\.h[>"]',
    )

    if library_match:
        checks.append(
            _check(
                "NRF001",
                "nRF24/RF24 library included",
                "PASS",
                "An nRF24/RF24 radio library include was detected.",
                source_file,
                _line_number(
                    source,
                    r'#include\s*[<"].*(RH_NRF24|RF24).*',
                ),
                "An nRF24/RF24 library should be included.",
                "nRF24/RF24 library detected.",
            )
        )
    else:
        checks.append(
            _check(
                "NRF001",
                "nRF24/RF24 library included",
                "UNKNOWN",
                "No recognized nRF24/RF24 library include was detected.",
                source_file,
                None,
                "An nRF24/RF24 library should be included.",
                "No recognized radio library detected.",
            )
        )

    # NRF002 — SPI
    checks.append(
        _check(
            "NRF002",
            "SPI interface detected",
            "PASS" if spi_match else "UNKNOWN",
            (
                "SPI.h include was detected."
                if spi_match
                else
                "No SPI.h include was detected."
            ),
            source_file,
            _line_number(
                source,
                r'#include\s*[<"]SPI\.h[>"]',
            ),
            "SPI support should be detectable for the radio interface.",
            (
                "SPI.h detected."
                if spi_match
                else
                "No SPI.h detected."
            ),
        )
    )

    # NRF003 — radio object
    object_match = _has(
        source,
        r'\b(?:RH_NRF24|RF24)\s+\w+\s*(?:\([^;]*\))?\s*;',
    )

    checks.append(
        _check(
            "NRF003",
            "Radio object declared",
            "PASS" if object_match else "UNKNOWN",
            (
                "An nRF24/RF24 radio object was detected."
                if object_match
                else
                "No recognized radio object declaration was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b(?:RH_NRF24|RF24)\s+\w+\s*(?:\([^;]*\))?\s*;',
            ),
            "A radio object should be declared.",
            (
                "Radio object detected."
                if object_match
                else
                "No radio object detected."
            ),
        )
    )

    # NRF004 — initialization
    init_match = _has(
        source,
        r'\b\w+\.init\s*\(\s*\)|\b\w+\.begin\s*\(\s*\)',
    )

    checks.append(
        _check(
            "NRF004",
            "Radio initialization",
            "PASS" if init_match else "UNKNOWN",
            (
                "A radio initialization call was detected."
                if init_match
                else
                "No recognized radio initialization call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.init\s*\(\s*\)|\b\w+\.begin\s*\(\s*\)',
            ),
            "The radio should be initialized.",
            (
                "Radio initialization detected."
                if init_match
                else
                "No radio initialization detected."
            ),
        )
    )

    # NRF005 — RF/channel configuration
    config_match = _has(
        source,
        r'\b\w+\.(setChannel|setRF|setDataRate|setPALevel|setChannel)\s*\(',
    )

    checks.append(
        _check(
            "NRF005",
            "Radio configuration",
            "PASS" if config_match else "UNKNOWN",
            (
                "An nRF24/RF24 configuration call was detected."
                if config_match
                else
                "No recognized radio configuration call was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.(setChannel|setRF|setDataRate|setPALevel|setChannel)\s*\(',
            ),
            "The radio should expose a recognizable configuration operation.",
            (
                "Radio configuration detected."
                if config_match
                else
                "No recognized configuration detected."
            ),
        )
    )

    # NRF006 — transmit/receive
    data_path_match = _has(
        source,
        r'\b\w+\.(send|write|recv|read|available|waitAvailableTimeout)\s*\(',
    )

    checks.append(
        _check(
            "NRF006",
            "Radio data path",
            "PASS" if data_path_match else "UNKNOWN",
            (
                "A radio transmit/receive operation was detected."
                if data_path_match
                else
                "No recognized radio data-path operation was detected."
            ),
            source_file,
            _line_number(
                source,
                r'\b\w+\.(send|write|recv|read|available|waitAvailableTimeout)\s*\(',
            ),
            "The source should contain a recognizable transmit or receive operation.",
            (
                "Radio data-path operation detected."
                if data_path_match
                else
                "No recognized transmit/receive operation detected."
            ),
        )
    )

    # NRF007 — serial output
    serial_match = _has(
        source,
        r'Serial\.(print|println)\s*\(',
    )

    checks.append(
        _check(
            "NRF007",
            "Serial output",
            "PASS" if serial_match else "UNKNOWN",
            (
                "Serial output statements were detected."
                if serial_match
                else
                "No Serial output statements were detected."
            ),
            source_file,
            _line_number(
                source,
                r'Serial\.(print|println)\s*\(',
            ),
            "Diagnostic information should be observable through Serial.",
            (
                "Serial output detected."
                if serial_match
                else
                "No Serial output detected."
            ),
        )
    )

    return _result(
        "nrf24_v1",
        "nRF24L01",
        source_file,
        checks,
    )


# ============================================================
# HC-SR04
# ============================================================

def _load_hcsr04_validator():
    """
    Import the existing HC-SR04 validator lazily.

    Keeping this import local avoids creating an unnecessary
    module-level dependency cycle between the validator registry
    and the original HC-SR04 validator module.
    """
    from diagnostics.validators import run_hcsr04_validator

    return run_hcsr04_validator


def run_hcsr04_validator(
    source: str,
    source_file: str = "unknown",
) -> ValidatorResult:
    """
    Compatibility wrapper around the existing HC-SR04 validator.

    The canonical HC-SR04 implementation remains in
    diagnostics.validators. This wrapper allows the multi-validator
    registry to dispatch HC-SR04 through the same interface as the
    newer validators.
    """
    validator = _load_hcsr04_validator()

    return validator(
        source,
        source_file=source_file,
    )


# ============================================================
# Registry
# ============================================================

DETERMINISTIC_VALIDATORS: Dict[str, Callable] = {
    # HC-SR04
    "hc-sr04": run_hcsr04_validator,
    "hcsr04": run_hcsr04_validator,

    # DHT
    "dht11": run_dht_validator,
    "dht22": run_dht_validator,
    "dht11/dht22": run_dht_validator,

    # MPU6050
    "mpu6050": run_mpu6050_validator,

    # nRF24L01
    "nrf24l01": run_nrf24_validator,
    "nrf24": run_nrf24_validator,
}


def get_deterministic_validator(
    component: Optional[str],
) -> Optional[Callable]:

    if not component:
        return None

    normalized = component.strip().lower()

    return DETERMINISTIC_VALIDATORS.get(
        normalized
    )