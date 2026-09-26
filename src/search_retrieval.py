from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_FILE = PROJECT_ROOT / "knowledge_base" / "retrieval_index.json"
VOCAB_FILE = PROJECT_ROOT / "knowledge_base" / "query_vocabulary.json"


# Retrieval weights.
# These are ranking weights, NOT engineering correctness scores.
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

    # Deduplicate while preserving order.
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

                        # Avoid duplicate identical matches.
                        if match not in results[project_id]["matches"]:
                            results[project_id]["matches"].append(match)
                            results[project_id]["score"] += weight

    return results


def evidence_level(score):

    if score >= 10:
        return "HIGH"

    if score >= 5:
        return "MEDIUM"

    return "LOW"


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print('python3 src/search_retrieval.py "HC-SR04"')
        return

    query = " ".join(sys.argv[1:])

    index_data = load_json(INDEX_FILE)
    vocabulary = load_json(VOCAB_FILE)

    query_terms = expand_query(
        query,
        vocabulary
    )

    results = search(
        index_data,
        query_terms
    )

    print()
    print("=" * 60)
    print(f"RETRIEVAL QUERY: {query}")
    print("=" * 60)

    print()
    print("Expanded query terms:")

    for term in query_terms:
        print(f"  - {term}")

    print()

    if not results:
        print("No matching projects found.")
        return

    # Rank by:
    # 1. total evidence score
    # 2. number of distinct matching fields
    # 3. project ID for deterministic ordering
    ranked_results = sorted(
        results.items(),
        key=lambda item: (
            -item[1]["score"],
            -len(
                set(
                    match["field"]
                    for match in item[1]["matches"]
                )
            ),
            int(item[0])
        )
    )

    print(f"Projects matched: {len(ranked_results)}")
    print()

    for project_id, result in ranked_results:

        score = result["score"]

        print(
            f"Project ID: {project_id} "
            f"| Evidence score: {score} "
            f"| Level: {evidence_level(score)}"
        )

        # Show strongest evidence first.
        matches = sorted(
            result["matches"],
            key=lambda match: (
                -match["weight"],
                match["field"],
                match["match"]
            )
        )

        for match in matches:

            print(
                f"  {match['field']}: "
                f"{match['match']} "
                f"[weight={match['weight']}, "
                f"query={match['query_term']}]"
            )

        print()


if __name__ == "__main__":
    main()
