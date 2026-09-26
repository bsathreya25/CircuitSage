from pathlib import Path
import json
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RECORDS_FILE = PROJECT_ROOT / "knowledge_base" / "canonical_records.json"
OUTPUT_FILE = PROJECT_ROOT / "knowledge_base" / "retrieval_index.json"


def normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def add_to_index(index, field, value, project_id):
    if not value:
        return

    value = normalize(value)

    if not value:
        return

    index[field].setdefault(value, [])

    if project_id not in index[field][value]:
        index[field][value].append(project_id)


def main():

    print("Loading canonical records...")

    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Canonical records loaded: {len(records)}")

    index = {
        "project_id": {},
        "project_name": {},
        "category": {},
        "component": {},
        "library": {},
        "interface": {},
        "diagnostic_signal": {},
        "source_file": {},
        "artifact_file": {}
    }

    for i, record in enumerate(records, start=1):

        project_id = str(record["project_id"])

        print(
            f"[{i:02d}/{len(records)}] "
            f"{project_id} - {record['project_name']}"
        )

        # Project ID
        add_to_index(
            index,
            "project_id",
            project_id,
            project_id
        )

        # Project name
        add_to_index(
            index,
            "project_name",
            record.get("project_name", ""),
            project_id
        )

        # Category
        add_to_index(
            index,
            "category",
            record.get("category", ""),
            project_id
        )

        # Components
        for component in record.get("components", []):
            add_to_index(
                index,
                "component",
                component,
                project_id
            )

        # Libraries
        for library in record.get("libraries", []):
            add_to_index(
                index,
                "library",
                library,
                project_id
            )

        # Interfaces
        interfaces = record.get("interfaces", {})

        for interface_name, enabled in interfaces.items():
            if enabled:
                add_to_index(
                    index,
                    "interface",
                    interface_name,
                    project_id
                )

        # Diagnostic signals
        for signal in record.get("diagnostic_signals", []):
            add_to_index(
                index,
                "diagnostic_signal",
                signal,
                project_id
            )

        # Source files
        for source_file in record.get("source_files", []):
            add_to_index(
                index,
                "source_file",
                Path(source_file).name,
                project_id
            )

        # Artifact files
        for artifact_file in record.get("artifact_files", []):
            add_to_index(
                index,
                "artifact_file",
                Path(artifact_file).name,
                project_id
            )

    # Sort project IDs inside every index bucket
    for field in index:
        for key in index[field]:
            index[field][key] = sorted(
                index[field][key],
                key=lambda x: int(x)
            )

    output = {
        "schema_version": "1.0",
        "record_count": len(records),
        "index": index
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 50)
    print("RETRIEVAL INDEX BUILD COMPLETE")
    print("=" * 50)
    print(f"Records indexed : {len(records)}")
    print(f"Output          : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
