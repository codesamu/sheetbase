import requests
from pdf_extractor import extract_text_from_pdf

API_KEY = "API-KEY"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free"
]

PDF_PATH = "datenblatt.pdf"
PROMPT_PATH = "prompt.txt"
OUTPUT_PATH = "generated_sql.sql"


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Fehler beim Lesen von {path}: {e}")
        return ""


def ask_model(model: str, prompt: str) -> str:
    print(f"Teste Modell: {model}")

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4000
            },
            timeout=180
        )

        if response.status_code != 200:
            print(response.text)
            return ""

        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Fehler mit {model}: {e}")
        return ""


def generate_sql() -> str:
    print("Lese PDF...")
    pdf_text = extract_text_from_pdf(PDF_PATH)

    print("Lese Prompt...")
    base_prompt = read_file(PROMPT_PATH)

    if not pdf_text or not base_prompt:
        return ""

    prompt = f"""
{base_prompt}

---------------- PDF INHALT ----------------

{pdf_text}
"""

    for model in MODELS:
        result = ask_model(model, prompt)

        if result:
            print(f"Erfolgreich mit {model}")
            return result

        print("Fallback zum nächsten Modell...")

    return ""


if __name__ == "__main__":
    sql = generate_sql()

    if sql:
        print(sql)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(sql)

        print(f"Gespeichert in: {OUTPUT_PATH}")
    else:
        print("Keine SQL generiert.")