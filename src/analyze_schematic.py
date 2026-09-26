import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# SCHEMATIC ANALYSIS
# ============================================================

def analyze_schematic(schematic_file):
    """
    Analyze an Arduino schematic image using Gemini
    and return structured connection data.

    The function is intentionally conservative:
    - Only visually supported connections should be returned.
    - Unknown connections remain UNKNOWN.
    - Gemini failures are returned as structured errors.
    """

    schematic_file = Path(schematic_file)

    # --------------------------------------------------------
    # FILE CHECK
    # --------------------------------------------------------

    if not schematic_file.exists():
        return {
            "status": "ERROR",
            "error": "Schematic image not found."
        }

    # --------------------------------------------------------
    # LOAD ENVIRONMENT
    # --------------------------------------------------------

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "status": "ERROR",
            "error": "GEMINI_API_KEY not found."
        }

    # --------------------------------------------------------
    # DETERMINE IMAGE TYPE
    # --------------------------------------------------------

    extension = schematic_file.suffix.lower()

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }

    mime_type = mime_types.get(extension)

    if mime_type is None:
        return {
            "status": "ERROR",
            "error": f"Unsupported schematic image format: {extension}"
        }

    # --------------------------------------------------------
    # CREATE GEMINI CLIENT
    # --------------------------------------------------------

    client = genai.Client(
        api_key=api_key
    )

    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image_bytes = schematic_file.read_bytes()

    # --------------------------------------------------------
    # ENGINEERING ANALYSIS PROMPT
    # --------------------------------------------------------

    prompt = """
You are an embedded systems engineering assistant.

Analyze the Arduino circuit schematic image.

Your task is to extract ONLY electrical connections that are
visibly supported by the schematic.

Return ONLY valid JSON.

Use exactly this structure:

{
    "board": "Arduino Uno",
    "sensor": "HC-SR04",
    "connections": {
        "VCC": "5V",
        "GND": "GND",
        "TRIG": "D9",
        "ECHO": "D12"
    }
}

Rules:

1. Return valid JSON only.
2. Do not use Markdown.
3. Do not include explanations.
4. Do not invent connections.
5. Do not infer a connection that cannot be visually established.
6. If a connection cannot be clearly determined, use "UNKNOWN".
7. Use Arduino digital pin notation such as D9, D10, D12.
8. Preserve the actual pin numbers visible in the schematic.
9. The schematic is documentation only. Do not assume that it
   represents the user's physical wiring.
10. Do not modify or "correct" the schematic.
"""

    # --------------------------------------------------------
    # GEMINI REQUEST
    # --------------------------------------------------------

    try:

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                prompt,
                image_part
            ]
        )

        raw_output = response.text.strip()

    # --------------------------------------------------------
    # GEMINI FAILURE
    # --------------------------------------------------------

    except Exception as error:

        error_text = str(error)

        return {
            "status": "UNAVAILABLE",
            "error": error_text
        }

    # --------------------------------------------------------
    # CLEAN POSSIBLE MARKDOWN WRAPPER
    # --------------------------------------------------------

    if raw_output.startswith("```"):

        lines = raw_output.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        raw_output = "\n".join(lines).strip()

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        schematic_data = json.loads(
            raw_output
        )

    except json.JSONDecodeError:

        return {
            "status": "ERROR",
            "error": "Gemini returned invalid JSON.",
            "raw_output": raw_output
        }

    # --------------------------------------------------------
    # BASIC STRUCTURE VALIDATION
    # --------------------------------------------------------

    if not isinstance(schematic_data, dict):

        return {
            "status": "ERROR",
            "error": "Schematic analysis did not return a JSON object.",
            "raw_output": raw_output
        }

    if "connections" not in schematic_data:

        return {
            "status": "ERROR",
            "error": "Schematic analysis did not contain a connections object.",
            "raw_output": raw_output
        }

    if not isinstance(
        schematic_data["connections"],
        dict
    ):

        return {
            "status": "ERROR",
            "error": "Schematic connections are not a JSON object.",
            "raw_output": raw_output
        }

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    schematic_data["status"] = "SUCCESS"

    return schematic_data


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    project_root = Path(__file__).parent.parent

    schematic_file = (
        project_root
        / "data/test_hcsr04/Schematics.png"
    )

    print("========================================")
    print("     SCHEMATIC ANALYSIS TEST")
    print("========================================")
    print()

    result = analyze_schematic(
        schematic_file
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )