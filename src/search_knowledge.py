from pathlib import Path
import json


knowledge_base_file = (
    Path(__file__).parent.parent
    / "knowledge_base"
    / "project_records.json"
)

with knowledge_base_file.open("r", encoding="utf-8") as file:
    projects = json.load(file)


search_term = input("What component or topic are you looking for? ").strip().lower()


print()
print("Search results:")
print()


found = False

for project in projects:
    project_text = json.dumps(project).lower()

    if search_term in project_text:
        print(project)
        print()
        found = True


if not found:
    print("No matching project found.")