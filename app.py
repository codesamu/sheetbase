from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from pdf_extractor import extract_text_from_pdf

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

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/docs")
def docs():
    return render_template("docs.html")

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
            
    # 2. Extract text from PDF (limiting to first 10 pages for speed and token limit safety)
    try:
        pdf_text = extract_text_from_pdf(pdf_path, max_pages=100)
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
        
    if not pdf_text or not base_prompt:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({"error": "Empty PDF text or prompt"}), 400
        
    prompt = f"""
{base_prompt}

---------------- PDF INHALT ----------------

{pdf_text}
"""

    # 4. Call OpenRouter
    api_key = os.environ.get("OPENROUTER_API_KEY", API_KEY)
    sql = ""
    success_model = None
    last_errors = []
    
    # Let's check if the API key is set to the default placeholder
    if api_key == "API-KEY":
        print("[WARNING] OpenRouter API key is set to default placeholder 'API-KEY'. Requests will likely fail.", flush=True)
        last_errors.append("API key is set to default 'API-KEY'. Please specify a valid API key.")
    
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
            
    # Clean up temp file
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass
        
    if not sql:
        return jsonify({
            "error": "Failed to generate SQL from LLM models.",
            "details": "All tried models failed to return a response. Please check your API key, your internet connection, or if your context size is too large.",
            "api_key_used": "API-KEY (placeholder)" if api_key == "API-KEY" else "Custom Key",
            "errors": last_errors
        }), 500
        
    # 5. Write to DB like in test-post.py (try, execute, commit, rollback)
    try:
        # Clean the SQL
        sql_clean = sql.strip()
        if sql_clean.startswith("```"):
            first_newline = sql_clean.find("\n")
            if first_newline != -1:
                sql_clean = sql_clean[first_newline:].strip()
            if sql_clean.endswith("```"):
                sql_clean = sql_clean[:-3].strip()
                
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
        
        return jsonify({
            "message": f"Successfully processed datasheet using {success_model}.",
            "status": "success",
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

