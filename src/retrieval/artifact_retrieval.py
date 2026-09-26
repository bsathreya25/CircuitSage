from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

ARTIFACT_INDEX = (
    ROOT / "knowledge_base" / "artifact_index.json"
)


class ArtifactRetriever:
    """
    Optional artifact lookup layer for CircuitSage.

    This module is intentionally isolated from the core
    diagnostic engine.

    If the artifact index is missing, corrupted, or a project
    has no artifact, the retriever safely returns no artifacts.
    The existing diagnostic pipeline must continue working.
    """

    def __init__(
        self,
        index_path: Path = ARTIFACT_INDEX,
    ):
        self.index_path = index_path
        self.projects: dict[str, dict[str, Any]] = {}

        self._load()

    def _load(self) -> None:
        try:
            with self.index_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            for project in data.get("projects", []):
                project_id = str(
                    project.get("project_id", "")
                )

                if project_id:
                    self.projects[project_id] = project

        except (OSError, json.JSONDecodeError):
            self.projects = {}

    def get_project_artifacts(
        self,
        project_id: str | int,
    ) -> list[dict[str, Any]]:
        """
        Return artifacts associated with a canonical project ID.

        The canonical dataset folders are named like:

            8 - HC-SR04 Ultrasonic

        while CircuitSage internally refers to the project as:

            8

        Therefore we support both forms.
        """

        requested_id = str(project_id)

        # Exact lookup.
        project = self.projects.get(requested_id)

        if project:
            return list(
                project.get("artifacts", [])
            )

        # Canonical folder-name lookup.
        prefix = f"{requested_id} - "

        for project_key, candidate in self.projects.items():
            if project_key.startswith(prefix):
                return list(
                    candidate.get("artifacts", [])
                )

        return []

    def has_artifacts(
        self,
        project_id: str | int,
    ) -> bool:
        return bool(
            self.get_project_artifacts(project_id)
        )

    def summarize_project(
        self,
        project_id: str | int,
    ) -> dict[str, Any]:
        artifacts = self.get_project_artifacts(
            project_id
        )

        return {
            "project_id": str(project_id),
            "artifact_count": len(artifacts),
            "has_artifacts": bool(artifacts),
            "artifacts": artifacts,
        }