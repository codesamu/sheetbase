from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# =========================
# FLASK APP SETUP
# =========================
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql+psycopg2://flaskusr:sheetbase@192.168.1.21:5432/datasheetdb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# MODEL (OPV TABLE)
# =========================
class OPV(db.Model):
    __tablename__ = "opv"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    power_supply_voltage = db.Column(db.Text)

# =========================
# TEST CONNECTION
# =========================
with app.app_context():
    try:
        # 1. Simple connection test
        result = db.session.execute(db.text("SELECT 1"))
        print("DB Connection OK:", result.fetchone())

        # 2. OPTIONAL: insert test row (comment out if not needed)
        test_opv = OPV(
            name="TEST_OPV",
            power_supply_voltage="5V"
        )

        db.session.add(test_opv)
        db.session.commit()

        print("Inserted test OPV with ID:", test_opv.id)

        # 3. Read back data
        rows = OPV.query.all()

        print("\nOPV TABLE CONTENTS:")
        for r in rows:
            print(f"ID={r.id}, Name={r.name}, V={r.power_supply_voltage}")

    except Exception as e:
        print("ERROR:", e)
