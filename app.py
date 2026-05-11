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
# MODEL
# =========================
class OPV(db.Model):
    __tablename__ = "opv"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    power_supply_voltage = db.Column(db.Text)

# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# GET ALL OPVs
# =========================
@app.route("/opv")
def get_opvs():

    rows = OPV.query.all()

    result = []

    for r in rows:
        result.append({
            "id": r.id,
            "name": r.name,
            "power_supply_voltage": r.power_supply_voltage
        })

    return jsonify(result)

# =========================
# INSERT NEW OPV
# =========================
@app.route("/add-opv", methods=["POST"])
def add_opv():

    data = request.json

    new_opv = OPV(
        name=data["name"],
        power_supply_voltage=data["power_supply_voltage"]
    )

    db.session.add(new_opv)
    db.session.commit()

    return jsonify({
        "message": "OPV added successfully",
        "id": new_opv.id
    })

# =========================
# TEST DB CONNECTION
# =========================
@app.route("/test-db")
def test_db():

    result = db.session.execute(db.text("SELECT 1"))

    return jsonify({
        "database": "connected",
        "result": str(result.fetchone())
    })

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
