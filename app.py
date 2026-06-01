from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import requests
from pdf_extractor import extract_text_chunks_from_pdf

# =========================
# OPENROUTER CONFIG
# =========================
API_KEY = "API-KEY"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free"
]
PDF_CHUNK_SIZE = 10
MAX_PDF_PAGES = 100
PDF_CLEANUP_MAX_WORKERS = 4

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# DATABASE CONFIG
# =========================
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql+psycopg2://flaskusr:sheetbase@192.168.1.21:5432/datasheetdb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =========================
# INIT SQLALCHEMY
# =========================
db = SQLAlchemy(app)

# =========================
# MODELS
# =========================
class OPV(db.Model):
    __tablename__ = "opv"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    power_supply_voltage = db.Column(db.Text)
    input_offset_voltage = db.Column(db.Text)
    input_offset_current = db.Column(db.Text)
    input_common_mode_voltage_range = db.Column(db.Text)
    large_signal_open_loop_gain = db.Column(db.Text)
    input_bias_current = db.Column(db.Text)
    output_voltage_high_low_limit = db.Column(db.Text)
    output_source_current = db.Column(db.Text)
    power_supply_current = db.Column(db.Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class BJT(db.Model):
    __tablename__ = "bjt"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    bjt_type = db.Column(db.Text) # 'NPN' or 'PNP'
    dc_current_gain_hfe = db.Column(db.Text)
    collector_emitter_voltage = db.Column(db.Text)
    collector_base_voltage = db.Column(db.Text)
    emitter_base_voltage = db.Column(db.Text)
    base_emitter_on_voltage = db.Column(db.Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class MOSFET(db.Model):
    __tablename__ = "mosfet"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    mosfet_type = db.Column(db.Text) # 'N-Kanal' or 'P-Kanal'
    drain_source_voltage = db.Column(db.Text)
    gate_source_voltage = db.Column(db.Text)
    continuous_drain_current = db.Column(db.Text)
    gate_threshold_voltage = db.Column(db.Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def build_cleanup_prompt(pdf_text, start_page, end_page, total_pages, chunk_index, total_chunks):
    return f"""
Du bist ein technischer Datenblatt-Kompressor fuer elektronische Bauteile.

Ziel:
Reduziere diesen PDF-Text drastisch, damit weniger Tokens verbraucht werden,
aber verliere keine technische Information, die fuer die spaetere Extraktion von
OPV-, BJT- oder MOSFET-Daten relevant sein koennte.

Strikte Regeln:
- Gib KEIN SQL aus.
- Gib KEINE Erklaerungen aus.
- Behalte alle exakten Teilenummern, Varianten, Suffixe, Familiennamen und Grade.
- Behalte alle elektrischen Grenzwerte, Min/Typ/Max-Werte, Bereiche, Einheiten,
  Messbedingungen, Tabellenueberschriften und Fussnoten mit Parameterbezug.
- Behalte insbesondere OPV-, BJT- und MOSFET-Parameter wie Versorgungsspannung,
  Offset, Bias, Common Mode, Open Loop Gain, Ausgangsstrom, hFE, VCEO, VCBO,
  VEBO, VBE, VDS, VGS, ID und VGS(th).
- Entferne Marketingtext, Fliesstext ohne Parameter, Wiederholungen,
  Navigations-/Layout-Reste, Copyright, URLs, Bestellblaetter ohne technische
  Relevanz und sonstige Zeichen, die nur Tokens kosten.
- Wenn du unsicher bist, ob eine Information relevant ist, behalte sie.
- Schreibe kompakt in Klartext mit kurzen Abschnitten und Tabellenzeilen.

Teil {chunk_index} von {total_chunks}, Seiten {start_page}-{end_page} von {total_pages}.

---------------- PDF INHALT ----------------

{pdf_text}
"""


def build_final_pdf_prompt(base_prompt, cleaned_pdf_text, total_pages, total_chunks):
    return f"""
{base_prompt}

Du bekommst nun den bereinigten technischen Gesamtinhalt des kompletten PDFs.
Die urspruenglichen PDF-Seiten wurden zuerst in {total_chunks} Chunks aufgeteilt,
parallel komprimiert und danach wieder zusammengefuegt.

Nutze den Gesamtzusammenhang ueber alle Seiten hinweg. Varianten-, Klassifizierungs-,
Suffix-, Fussnoten- und Tabelleninformationen koennen in unterschiedlichen Teilen
stehen und muessen zusammen betrachtet werden.

Gib ausschliesslich SQL INSERT Statements zurueck.

Gesamtseiten im Original-PDF: {total_pages}

---------------- BEREINIGTER PDF-GESAMTKONTEXT ----------------

{cleaned_pdf_text}
"""


def clean_sql_response(sql):
    sql_clean = sql.strip()
    if sql_clean.startswith("```"):
        first_newline = sql_clean.find("\n")
        if first_newline != -1:
            sql_clean = sql_clean[first_newline:].strip()
        if sql_clean.endswith("```"):
            sql_clean = sql_clean[:-3].strip()

    return sql_clean


def ask_openrouter_with_fallback(prompt, api_key, debug_label="OpenRouter", max_tokens=4000):
    content_result = ""
    success_model = None
    last_errors = []

    for model in MODELS:
        print(f"[{debug_label}] Testing model: {model}", flush=True)
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": max_tokens
                },
                timeout=180
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                if content:
                    content_result = content
                    success_model = model
                    print(f"[{debug_label}] Success with model: {model}", flush=True)
                    break
            else:
                error_msg = f"[{debug_label}] Model {model} returned status {response.status_code}: {response.text}"
                print(error_msg, flush=True)
                last_errors.append(error_msg)
        except Exception as e:
            error_msg = f"[{debug_label}] Error with model {model}: {str(e)}"
            print(error_msg, flush=True)
            last_errors.append(error_msg)

    return content_result, success_model, last_errors


def clean_pdf_chunk_with_ai(chunk_index, total_chunks, chunk, api_key):
    debug_label = (
        f"Cleanup chunk {chunk_index}/{total_chunks} "
        f"pages {chunk['start_page']}-{chunk['end_page']}"
    )
    print(f"[{debug_label}] Starting cleanup request", flush=True)

    prompt = build_cleanup_prompt(
        pdf_text=chunk["text"],
        start_page=chunk["start_page"],
        end_page=chunk["end_page"],
        total_pages=chunk["total_pages"],
        chunk_index=chunk_index,
        total_chunks=total_chunks
    )
    cleaned_text, success_model, errors = ask_openrouter_with_fallback(
        prompt,
        api_key,
        debug_label=debug_label,
        max_tokens=4000
    )
    cleaned_text = clean_sql_response(cleaned_text)

    if not cleaned_text:
        errors.append(f"[{debug_label}] Empty cleanup response")

    print(
        f"[{debug_label}] Finished cleanup. "
        f"Input chars: {len(chunk['text'])}, output chars: {len(cleaned_text)}",
        flush=True
    )

    return {
        "chunk_index": chunk_index,
        "start_page": chunk["start_page"],
        "end_page": chunk["end_page"],
        "total_pages": chunk["total_pages"],
        "text": cleaned_text,
        "model": success_model,
        "errors": errors
    }


def clean_pdf_chunks_concurrently(pdf_chunks, api_key):
    total_chunks = len(pdf_chunks)
    max_workers = min(PDF_CLEANUP_MAX_WORKERS, total_chunks)
    results = []
    errors = []

    print(
        f"[Cleanup] Starting parallel cleanup for {total_chunks} chunks "
        f"with {max_workers} workers",
        flush=True
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(clean_pdf_chunk_with_ai, index, total_chunks, chunk, api_key): index
            for index, chunk in enumerate(pdf_chunks, start=1)
        }

        for future in as_completed(futures):
            chunk_index = futures[future]
            try:
                result = future.result()
                results.append(result)
                errors.extend(result["errors"])
                print(
                    f"[Cleanup] Chunk {chunk_index}/{total_chunks} completed",
                    flush=True
                )
            except Exception as e:
                error_msg = f"[Cleanup] Chunk {chunk_index}/{total_chunks} failed: {str(e)}"
                print(error_msg, flush=True)
                errors.append(error_msg)

    results.sort(key=lambda item: item["chunk_index"])
    failed_chunks = [result for result in results if not result["text"]]

    if failed_chunks or len(results) != total_chunks:
        missing_indexes = sorted(
            set(range(1, total_chunks + 1)) -
            {result["chunk_index"] for result in results}
        )
        if missing_indexes:
            errors.append(f"[Cleanup] Missing cleanup results for chunks: {missing_indexes}")

        failed_indexes = [result["chunk_index"] for result in failed_chunks]
        if failed_indexes:
            errors.append(f"[Cleanup] Empty cleanup results for chunks: {failed_indexes}")

    return results, errors

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.template_folder,
        "favicon.svg",
        mimetype="image/svg+xml"
    )

@app.route("/favicon.svg")
def favicon_svg():
    return send_from_directory(
        app.template_folder,
        "favicon.svg",
        mimetype="image/svg+xml"
    )

@app.route("/data/<category>")
def get_data(category):
    model_map = {
        "opv": OPV,
        "bjt": BJT,
        "mosfet": MOSFET
    }
    
    model = model_map.get(category.lower())
    if not model:
        return jsonify({"error": "Invalid category"}), 400
        
    rows = model.query.all()
    return jsonify([r.to_dict() for r in rows])

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    # 1. Determine PDF path (use the uploaded pdf, comment out the datenblatt.pdf)
    # pdf_path = "datenblatt.pdf"
    temp_path = None
    
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    temp_path = "temp_uploaded.pdf"
    file.save(temp_path)
    pdf_path = temp_path
            
    # 2. Extract text from PDF in 10-page chunks
    try:
        pdf_chunks = extract_text_chunks_from_pdf(
            pdf_path,
            chunk_size=PDF_CHUNK_SIZE,
            max_pages=MAX_PDF_PAGES
        )
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({"error": f"Failed to extract text from PDF: {str(e)}"}), 500
        
    # 3. Read prompt
    prompt_path = "prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({"error": f"Failed to read prompt file: {str(e)}"}), 500
        
    pdf_chunks = [chunk for chunk in pdf_chunks if chunk.get("text", "").strip()]

    if not pdf_chunks or not base_prompt:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({"error": "Empty PDF text or prompt"}), 400

    # 4. Call OpenRouter in two phases:
    #    A) parallel cleanup/compression per chunk
    #    B) one final SQL generation request with the full cleaned context
    api_key = os.environ.get("OPENROUTER_API_KEY", API_KEY)
    debug_messages = []
    last_errors = []

    def debug(message):
        print(message, flush=True)
        debug_messages.append(message)
    
    # Let's check if the API key is set to the default placeholder
    if api_key == "API-KEY":
        warning = "[WARNING] OpenRouter API key is set to default placeholder 'API-KEY'. Requests will likely fail."
        debug(warning)
        last_errors.append("API key is set to default 'API-KEY'. Please specify a valid API key.")
    
    total_chunks = len(pdf_chunks)
    total_pages = pdf_chunks[0]["total_pages"] if pdf_chunks else 0
    original_char_count = sum(len(chunk.get("text", "")) for chunk in pdf_chunks)

    debug(
        f"[Pipeline] Extracted {total_chunks} PDF chunks "
        f"({PDF_CHUNK_SIZE} pages each, max {MAX_PDF_PAGES} pages)."
    )
    debug(f"[Pipeline] Original extracted text size: {original_char_count} characters.")
    debug("[Pipeline] Starting parallel AI cleanup phase.")

    cleaned_chunks, cleanup_errors = clean_pdf_chunks_concurrently(pdf_chunks, api_key)
    last_errors.extend(cleanup_errors)

    original_lengths_by_index = {
        index: len(chunk.get("text", ""))
        for index, chunk in enumerate(pdf_chunks, start=1)
    }

    for cleaned_chunk in cleaned_chunks:
        debug(
            f"[Cleanup] Chunk {cleaned_chunk['chunk_index']}/{total_chunks} "
            f"pages {cleaned_chunk['start_page']}-{cleaned_chunk['end_page']} "
            f"cleaned with {cleaned_chunk.get('model') or 'unknown'} "
            f"({original_lengths_by_index.get(cleaned_chunk['chunk_index'], 0)} -> "
            f"{len(cleaned_chunk.get('text', ''))} chars)."
        )

    cleanup_failed = (
        len(cleaned_chunks) != total_chunks or
        any(not chunk.get("text", "").strip() for chunk in cleaned_chunks)
    )

    if cleanup_failed:
        debug("[Pipeline] Cleanup phase failed. Aborting before final SQL generation.")

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        return jsonify({
            "error": "Failed to clean PDF chunks with LLM models.",
            "details": "At least one PDF chunk could not be cleaned. Final SQL generation was not started to avoid losing context.",
            "api_key_used": "API-KEY (placeholder)" if api_key == "API-KEY" else "Custom Key",
            "errors": last_errors,
            "debug_messages": debug_messages
        }), 500

    cleaned_text_parts = []
    cleanup_models = []

    for chunk in cleaned_chunks:
        cleaned_text_parts.append(
            f"\n--- Bereinigter Chunk {chunk['chunk_index']}/{total_chunks}, "
            f"Seiten {chunk['start_page']}-{chunk['end_page']} ---\n"
            f"{chunk['text']}"
        )
        if chunk.get("model"):
            cleanup_models.append(chunk["model"])

    cleaned_pdf_text = "\n\n".join(cleaned_text_parts)
    cleaned_char_count = len(cleaned_pdf_text)
    reduction_percent = 0

    if original_char_count:
        reduction_percent = round((1 - cleaned_char_count / original_char_count) * 100, 1)

    debug("[Pipeline] Cleanup phase complete.")
    debug(f"[Pipeline] Cleaned context size: {cleaned_char_count} characters.")
    debug(f"[Pipeline] Approximate text reduction: {reduction_percent}%.")
    debug("[Pipeline] Starting final SQL generation with merged cleaned context.")

    final_prompt = build_final_pdf_prompt(
        base_prompt=base_prompt,
        cleaned_pdf_text=cleaned_pdf_text,
        total_pages=total_pages,
        total_chunks=total_chunks
    )
    sql, sql_model, sql_errors = ask_openrouter_with_fallback(
        final_prompt,
        api_key,
        debug_label="Final SQL generation",
        max_tokens=4000
    )
    last_errors.extend(sql_errors)
    sql = clean_sql_response(sql)
            
    # Clean up temp file
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass
        
    if not sql:
        debug("[Pipeline] Final SQL generation returned no SQL.")
        return jsonify({
            "error": "Failed to generate SQL from LLM models.",
            "details": "All tried models failed to return final SQL. Please check your API key, internet connection, or if the merged context is still too large.",
            "api_key_used": "API-KEY (placeholder)" if api_key == "API-KEY" else "Custom Key",
            "errors": last_errors,
            "debug_messages": debug_messages
        }), 500

    debug(f"[Pipeline] Final SQL generated with model: {sql_model or 'unknown'}.")
        
    # 5. Write to DB like in test-post.py (try, execute, commit, rollback)
    try:
        # Clean the SQL
        sql_clean = clean_sql_response(sql)
                
        # Split by semicolon to execute separate statements safely
        statements = sql_clean.split(";")
        executed_count = 0
        
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            db.session.execute(db.text(statement))
            executed_count += 1
            
        db.session.commit()
        debug(f"[Database] Commit successful. Statements executed: {executed_count}.")

        cleanup_model_names = ", ".join(dict.fromkeys(cleanup_models)) or "unknown"
        sql_model_name = sql_model or "unknown"
        
        return jsonify({
            "message": f"Successfully processed datasheet using {sql_model_name}.",
            "status": "success",
            "chunks_processed": total_chunks,
            "cleanup_models": cleanup_model_names,
            "sql_model": sql_model_name,
            "original_char_count": original_char_count,
            "cleaned_char_count": cleaned_char_count,
            "text_reduction_percent": reduction_percent,
            "statements_executed": executed_count,
            "sql": sql_clean,
            "debug_messages": debug_messages
        })
        
    except Exception as e:
        db.session.rollback()
        debug(f"[Database] Rollback after insertion failure: {str(e)}")
        return jsonify({
            "error": f"Database insertion failed: {str(e)}",
            "sql": sql,
            "debug_messages": debug_messages
        }), 500

@app.route("/test-db")
def test_db():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"database": "connected"})
    except Exception as e:
        return jsonify({"database": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
