from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
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


def build_pdf_prompt(base_prompt, pdf_text, start_page, end_page, total_pages, chunk_index, total_chunks):
    return f"""
{base_prompt}

Du bekommst nur einen Teil des PDFs. Verarbeite ausschliesslich die Informationen
aus diesem Teil und gib nur SQL fuer die Daten zurueck, die in diesem Teil sicher
erkennbar sind.

Teil {chunk_index} von {total_chunks}, Seiten {start_page}-{end_page} von {total_pages}.

---------------- PDF INHALT ----------------

{pdf_text}
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


def ask_openrouter_with_fallback(prompt, api_key):
    sql = ""
    success_model = None
    last_errors = []

    for model in MODELS:
        print(f"Testing model: {model}", flush=True)
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
                    "max_tokens": 4000
                },
                timeout=180
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                if content:
                    sql = content
                    success_model = model
                    break
            else:
                error_msg = f"Model {model} returned status {response.status_code}: {response.text}"
                print(error_msg, flush=True)
                last_errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error with model {model}: {str(e)}"
            print(error_msg, flush=True)
            last_errors.append(error_msg)

    return sql, success_model, last_errors

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

    # 4. Call OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY", API_KEY)
    sql_parts = []
    success_models = []
    last_errors = []
    failed_chunk_error = None
    
    # Let's check if the API key is set to the default placeholder
    if api_key == "API-KEY":
        print("[WARNING] OpenRouter API key is set to default placeholder 'API-KEY'. Requests will likely fail.", flush=True)
        last_errors.append("API key is set to default 'API-KEY'. Please specify a valid API key.")
    
    total_chunks = len(pdf_chunks)

    for chunk_index, chunk in enumerate(pdf_chunks, start=1):
        print(
            f"Processing PDF chunk {chunk_index}/{total_chunks}: "
            f"pages {chunk['start_page']}-{chunk['end_page']}",
            flush=True
        )

        prompt = build_pdf_prompt(
            base_prompt=base_prompt,
            pdf_text=chunk["text"],
            start_page=chunk["start_page"],
            end_page=chunk["end_page"],
            total_pages=chunk["total_pages"],
            chunk_index=chunk_index,
            total_chunks=total_chunks
        )
        chunk_sql, success_model, chunk_errors = ask_openrouter_with_fallback(prompt, api_key)
        last_errors.extend(chunk_errors)

        if not chunk_sql:
            failed_chunk_error = (
                f"No SQL generated for PDF chunk {chunk_index}/{total_chunks} "
                f"(pages {chunk['start_page']}-{chunk['end_page']})."
            )
            last_errors.append(failed_chunk_error)
            break

        chunk_sql = clean_sql_response(chunk_sql)
        if not chunk_sql:
            failed_chunk_error = (
                f"Empty SQL generated for PDF chunk {chunk_index}/{total_chunks} "
                f"(pages {chunk['start_page']}-{chunk['end_page']})."
            )
            last_errors.append(failed_chunk_error)
            break

        sql_parts.append(chunk_sql)
        if success_model:
            success_models.append(success_model)
            
    # Clean up temp file
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    sql = "\n\n".join(sql_parts)
        
    if failed_chunk_error or not sql:
        return jsonify({
            "error": "Failed to generate SQL from LLM models.",
            "details": failed_chunk_error or "All tried models failed to return a response. Please check your API key, your internet connection, or if your context size is too large.",
            "api_key_used": "API-KEY (placeholder)" if api_key == "API-KEY" else "Custom Key",
            "errors": last_errors
        }), 500
        
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

        successful_model_names = ", ".join(dict.fromkeys(success_models))
        
        return jsonify({
            "message": f"Successfully processed datasheet using {successful_model_names}.",
            "status": "success",
            "chunks_processed": len(sql_parts),
            "statements_executed": executed_count,
            "sql": sql_clean
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": f"Database insertion failed: {str(e)}",
            "sql": sql
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
