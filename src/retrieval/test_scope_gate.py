from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

INDEX_FILE = (
    PROJECT_ROOT
    / "knowledge_base"
    / "retrieval_index.json"
)

VOCAB_FILE = (
    PROJECT_ROOT
    / "knowledge_base"
    / "query_vocabulary.json"
)

# Import the Scope Gate.
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval.scope_gate import (
    load_records,
    build_coverage,
    evaluate_scope
)


EVIDENCE_WEIGHTS = {
    "component": 10,
    "library": 10,
    "diagnostic_signal": 10,
    "source_file": 7,
    "artifact_file": 5,
    "project_name": 4,
    "interface": 3,
    "category": 1,
}


def normalize(text):
    return str(text).strip().lower()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def expand_query(query, vocabulary):

    normalized = normalize(query)

    expanded = [normalized]

    aliases = vocabulary.get("aliases", {})

    if normalized in aliases:
        expanded.extend(
            normalize(value)
            for value in aliases[normalized]
        )

    result = []

    for item in expanded:
        if item not in result:
            result.append(item)

    return result


def search(index_data, query_terms):

    index = index_data["index"]

    results = {}

    for field, values in index.items():

        weight = EVIDENCE_WEIGHTS.get(field, 0)

        for key, project_ids in values.items():

            normalized_key = normalize(key)

            for term in query_terms:

                if term in normalized_key:

                    for project_id in project_ids:

                        if project_id not in results:
                            results[project_id] = {
                                "score": 0,
                                "matches": []
                            }

                        match = {
                            "field": field,
                            "match": key,
                            "query_term": term,
                            "weight": weight
                        }

                        if match not in results[project_id]["matches"]:
                            results[project_id]["matches"].append(match)
                            results[project_id]["score"] += weight

    return results


def run_test(query):

    index_data = load_json(INDEX_FILE)
    vocabulary = load_json(VOCAB_FILE)

    query_terms = expand_query(
        query,
        vocabulary
    )

    retrieval_results = search(
        index_data,
        query_terms
    )

    records = load_records()
    coverage = build_coverage(records)

    result = evaluate_scope(
        query,
        retrieval_results,
        coverage
    )

    print()
    print("=" * 60)
    print("QUERY:", query)
    print("=" * 60)

    print("STATUS:", result["status"])
    print("REASON:", result["reason"])

    print()
    print("CANDIDATES:")

    for candidate in result["candidate_projects"]:
        print(
            f"  Project {candidate['project_id']} "
            f"| score={candidate['score']} "
            f"| evidence={candidate['evidence_level']}"
        )


def main():

    tests = [
        "GSM",
        "pulseIn",
        "completely_unknown_component_xyz"
    ]

    for query in tests:
        run_test(query)


if __name__ == "__main__":
    main()
