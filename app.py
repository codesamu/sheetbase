from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

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
    # Placeholder for PDF processing + AI Classification logic
    return jsonify({
        "message": "Analyzing datasheet and routing to correct category...",
        "status": "success",
        "action": "classification_started"
    })

@app.route("/test-db")
def test_db():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"database": "connected"})
    except Exception as e:
        return jsonify({"database": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)

