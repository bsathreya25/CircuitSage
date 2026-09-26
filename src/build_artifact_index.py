from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = ROOT / "data" / "canonical"
OUTPUT = ROOT / "knowledge_base" / "artifact_index.json"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
}

DOCUMENT_EXTENSIONS = {
    ".pdf",
}


def classify_artifact(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        return "image"

    if suffix in DOCUMENT_EXTENSIONS:
        return "pdf"

    return "other"


def build_index() -> dict:
    projects = []

    for project_dir in sorted(CANONICAL_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        artifacts = []

        for path in sorted(project_dir.rglob("*")):
            if not path.is_file():
                continue

            artifact_type = classify_artifact(path)

            if artifact_type == "other":
                continue

            relative_path = path.relative_to(ROOT).as_posix()

            artifacts.append(
                {
                    "path": relative_path,
                    "type": artifact_type,
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                }
            )

        projects.append(
            {
                "project_id": project_dir.name,
                "project_name": project_dir.name,
                "artifact_count": len(artifacts),
                "artifacts": artifacts,
            }
        )

    total_artifacts = sum(
        project["artifact_count"]
        for project in projects
    )

    return {
        "project": "CircuitSage",
        "version": "1.0",
        "canonical_project_count": len(projects),
        "total_artifacts": total_artifacts,
        "projects": projects,
    }


def main() -> None:
    index = build_index()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(index, indent=2),
        encoding="utf-8",
    )

    print("CircuitSage artifact index built.")
    print(f"Canonical projects: {index['canonical_project_count']}")
    print(f"Image/PDF artifacts: {index['total_artifacts']}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()