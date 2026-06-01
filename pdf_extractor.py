import fitz
import re
import sys
import os

def extract_text_from_pdf(pdf_path, max_pages=None):

    if not os.path.exists(pdf_path):
        print("Datei nicht gefunden:", pdf_path)
        return ""

    doc = fitz.open(pdf_path)
    full_text = ""

    total_pages = len(doc)
    pages_to_read = min(total_pages, max_pages) if max_pages is not None else total_pages
    print(f"Seiten im PDF (Gesamt): {total_pages}, Lese: {pages_to_read}")

    for page_num in range(pages_to_read):
        page = doc.load_page(page_num)
        text = page.get_text("text")

        full_text += f"\n--- Seite {page_num+1} ---\n"
        full_text += text

    doc.close()
    return full_text


def extract_text_chunks_from_pdf(pdf_path, chunk_size=10, max_pages=None):
    if not os.path.exists(pdf_path):
        print("Datei nicht gefunden:", pdf_path)
        return []

    doc = fitz.open(pdf_path)
    chunks = []

    try:
        total_pages = len(doc)
        pages_to_read = min(total_pages, max_pages) if max_pages is not None else total_pages
        print(
            f"Seiten im PDF (Gesamt): {total_pages}, Lese: {pages_to_read}, "
            f"Chunk-Groesse: {chunk_size}"
        )

        for start_page in range(0, pages_to_read, chunk_size):
            end_page = min(start_page + chunk_size, pages_to_read)
            chunk_text = ""

            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)
                text = page.get_text("text")

                chunk_text += f"\n--- Seite {page_num+1} ---\n"
                chunk_text += text

            chunks.append({
                "start_page": start_page + 1,
                "end_page": end_page,
                "total_pages": total_pages,
                "text": chunk_text
            })
    finally:
        doc.close()

    return chunks

def clean_text(text):

    replacements = {
        "µ": "u",
        "Ω": "Ohm",
        "℃": "°C",
        "\xa0": " ",
        "\t": " "
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Seitenmarker entfernen
    text = re.sub(r"--- Seite \d+ ---", "", text)

    # URLs entfernen
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Seitenzahlen entfernen
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Seite\s+\d+\s+von\s+\d+", "", text, flags=re.IGNORECASE)

    # Mehrere Leerzeichen
    text = re.sub(r"[ ]{2,}", " ", text)

    # Mehrere Leerzeilen
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Getrennte Sätze zusammenführen
    lines = text.splitlines()
    result = []

    for line in lines:
        line = line.strip()

        if not line:
            result.append("")
            continue

        if result and result[-1] != "":
            prev = result[-1]

            if not prev.endswith((".", ":", ";")) and line[0].islower():
                result[-1] += " " + line
            else:
                result.append(line)
        else:
            result.append(line)

    return "\n".join(result).strip()


def save_text(text, filename="cleaned_output.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    print("Gespeichert:", filename)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Verwendung:")
        print("python pdf_text_extractor_clean.py datenblatt.pdf")
        sys.exit()

    pdf_file = sys.argv[1]

    print("PDF wird gelesen...")
    raw_text = extract_text_from_pdf(pdf_file)

    print("Text wird bereinigt...")
    cleaned_text = clean_text(raw_text)

    print("\n===== VORSCHAU =====\n")
    print(cleaned_text[:5000])

    save_text(cleaned_text)
