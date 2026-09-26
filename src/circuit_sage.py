from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).with_name(".env"))

client = genai.Client(http_options={"timeout": 30000})

print("CircuitSage is ready!")
print("Ask an electronics question. Type 'quit' to exit.")

while True:
    question = input("\nYour question: ").strip()

    if question.lower() in {"quit", "exit"}:
        print("Goodbye!")
        break

    if not question:
        print("Please type a question.")
        continue

    prompt = f"""
You are CircuitSage, a careful embedded-systems troubleshooting assistant.

User problem:
{question}

Give a beginner-friendly response using exactly these headings:

1. What the problem may mean
2. Likely causes
3. Checks to perform
4. Expected results
5. Recommended next action

Rules:
- Use simple language.
- Do not assume a component is faulty without evidence.
- Mention missing measurements or details.
- Prioritize safe, practical checks.
- Keep the response under 300 words.
"""

Question: {question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        print("\nCircuitSage:\n")
        print(response.text)

    except Exception as error:
        print("\nGemini request failed:", error)