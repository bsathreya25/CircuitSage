from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(http_options={"timeout": 30000})

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Explain the difference between UART and SPI in three simple bullet points."
    )

    print(response.text)

except Exception as error:
    print("Gemini request failed:", error)