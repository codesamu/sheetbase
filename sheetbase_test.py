import requests
from pdf_extractor import extract_text_from_pdf

# OpenRouter API-Key
OPENROUTER_API_KEY = "API-KEY"

# OpenRouter Endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Beste verfügbare Free-Modelle mit Fallback
MODELS = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free"
]


def load_prompt_from_file(prompt_file_path: str) -> str:
    """
    Lädt den Prompt aus einer Datei.
    """

    try:

        with open(
            prompt_file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except Exception as e:

        print(f"Fehler beim Laden des Prompts: {e}")

        return ""


def extract_pdf_text(pdf_file_path: str) -> str:
    """
    Extrahiert Text aus PDF.
    """

    try:

        return extract_text_from_pdf(pdf_file_path)

    except Exception as e:

        print(f"Fehler beim PDF-Extrahieren: {e}")

        return ""


def combine_prompt_with_pdf_text(
    base_prompt: str,
    pdf_text: str
) -> str:
    """
    Kombiniert Prompt + PDF-Text.
    """

    return f"""
{base_prompt}

---------------- PDF INHALT ----------------

{pdf_text}
"""


def try_model(
    model_name: str,
    combined_prompt: str
) -> str:
    """
    Testet ein einzelnes Modell.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "PDF SQL Generator"
    }

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": combined_prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }

    try:

        print(f"\nTeste Modell: {model_name}")

        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=180
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:

            print(response.text)

            return ""

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        print(f"Erfolgreich mit: {model_name}")

        return answer

    except Exception as e:

        print(f"Fehler mit Modell {model_name}: {e}")

        return ""


def call_ai_api(combined_prompt: str) -> str:
    """
    Probiert Modelle nacheinander durch.
    """

    for model in MODELS:

        result = try_model(
            model,
            combined_prompt
        )

        if result:

            return result

        print("Fallback zum nächsten Modell...")

    print("Kein Modell hat funktioniert.")

    return ""


def generate_sql_from_pdf(
    pdf_file_path: str,
    prompt_file_path: str
) -> str:
    """
    Hauptfunktion.
    """

    print("Extrahiere PDF-Text...")

    pdf_text = extract_pdf_text(pdf_file_path)

    if not pdf_text:

        print("PDF-Text konnte nicht extrahiert werden.")

        return ""

    print("PDF erfolgreich gelesen.")

    print("Lade Prompt...")

    base_prompt = load_prompt_from_file(
        prompt_file_path
    )

    if not base_prompt:

        print("Prompt konnte nicht geladen werden.")

        return ""

    print("Prompt geladen.")

    combined_prompt = combine_prompt_with_pdf_text(
        base_prompt,
        pdf_text
    )

    print("Sende Anfrage an OpenRouter...")

    sql_commands = call_ai_api(
        combined_prompt
    )

    if not sql_commands:

        print("Keine Antwort erhalten.")

        return ""

    print("SQL erfolgreich generiert.")

    return sql_commands


def save_sql_to_file(
    sql_commands: str,
    output_file_path: str
):
    """
    Speichert SQL in Datei.
    """

    try:

        with open(
            output_file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(sql_commands)

        print(f"Datei gespeichert: {output_file_path}")

    except Exception as e:

        print(f"Fehler beim Speichern: {e}")


if __name__ == "__main__":

    PDF_PATH = "datenblatt.pdf"

    PROMPT_PATH = "prompt.txt"

    OUTPUT_PATH = "generated_sql.sql"

    result = generate_sql_from_pdf(
        PDF_PATH,
        PROMPT_PATH
    )

    if result:

        print("\nGenerierte SQL:")
        print("-" * 50)
        print(result)
        print("-" * 50)

        save_sql_to_file(
            result,
            OUTPUT_PATH
        )