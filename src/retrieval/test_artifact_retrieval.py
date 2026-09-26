from pathlib import Path

from src.retrieval.artifact_retrieval import ArtifactRetriever


def test_artifact_index_loads():
    retriever = ArtifactRetriever()

    assert len(retriever.projects) == 89


def test_hcsr04_has_artifact():
    retriever = ArtifactRetriever()

    artifacts = retriever.get_project_artifacts("8")

    assert len(artifacts) > 0


def test_artifact_contains_valid_path():
    retriever = ArtifactRetriever()

    artifacts = retriever.get_project_artifacts("8")

    for artifact in artifacts:
        assert "path" in artifact
        assert "type" in artifact
        assert artifact["type"] in {"image", "pdf"}


def test_unknown_project_is_safe():
    retriever = ArtifactRetriever()

    assert retriever.get_project_artifacts("does-not-exist") == []
    assert retriever.has_artifacts("does-not-exist") is False


def test_missing_index_does_not_break_retriever(tmp_path: Path):
    missing_index = tmp_path / "missing.json"

    retriever = ArtifactRetriever(missing_index)

    assert retriever.projects == {}
    assert retriever.get_project_artifacts("8") == []