def validate_connections(code_data, schematic_data):
    """
    Compare firmware pin assignments with
    schematic connections.
    """

    results = []

    code_trigger = code_data.get("trigger_pin")
    code_echo = code_data.get("echo_pin")

    schematic_connections = schematic_data.get(
        "connections",
        {}
    )

    schematic_trigger = schematic_connections.get(
        "TRIG"
    )

    schematic_echo = schematic_connections.get(
        "ECHO"
    )

    # --------------------------------------------------
    # TRIGGER CHECK
    # --------------------------------------------------

    if code_trigger and schematic_trigger:

        expected_trigger = f"D{code_trigger}"

        if expected_trigger == schematic_trigger:

            results.append({
                "connection": "TRIG",
                "code": expected_trigger,
                "schematic": schematic_trigger,
                "status": "PASS",
                "message": "TRIG pin matches."
            })

        else:

            results.append({
                "connection": "TRIG",
                "code": expected_trigger,
                "schematic": schematic_trigger,
                "status": "MISMATCH",
                "message": "TRIG pin mismatch detected."
            })

    # --------------------------------------------------
    # ECHO CHECK
    # --------------------------------------------------

    if code_echo and schematic_echo:

        expected_echo = f"D{code_echo}"

        if expected_echo == schematic_echo:

            results.append({
                "connection": "ECHO",
                "code": expected_echo,
                "schematic": schematic_echo,
                "status": "PASS",
                "message": "ECHO pin matches."
            })

        else:

            results.append({
                "connection": "ECHO",
                "code": expected_echo,
                "schematic": schematic_echo,
                "status": "MISMATCH",
                "message": "ECHO pin mismatch detected."
            })

    return results