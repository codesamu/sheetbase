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

class BJT(db.Model):
    __tablename__ = "bjt"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    bjt_type = db.Column(db.Text)
    dc_current_gain_hfe = db.Column(db.Text)
    collector_emitter_voltage = db.Column(db.Text)
    collector_base_voltage = db.Column(db.Text)
    emitter_base_voltage = db.Column(db.Text)
    base_emitter_on_voltage = db.Column(db.Text)

class MOSFET(db.Model):
    __tablename__ = "mosfet"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    mosfet_type = db.Column(db.Text)
    drain_source_voltage = db.Column(db.Text)
    gate_source_voltage = db.Column(db.Text)
    continuous_drain_current = db.Column(db.Text)
    gate_threshold_voltage = db.Column(db.Text)

# =========================
# TEST INSERTION
# =========================
def run_test_insert():
    with app.app_context():
        try:
            print("--- Starting Database Insertion Test ---")

            # 1. Insert OPV (Full Parameters)
            new_opv = OPV(
                name="OPA2134",
                power_supply_voltage="±2.5V to ±18V",
                input_offset_voltage="0.5mV",
                input_offset_current="5pA",
                input_common_mode_voltage_range="(V-) + 2.5V to (V+) - 2.5V",
                large_signal_open_loop_gain="120dB",
                input_bias_current="20pA",
                output_voltage_high_low_limit="(V+) - 1.2V / (V-) + 1.2V",
                output_source_current="35mA",
                power_supply_current="4mA/channel"
            )
            db.session.add(new_opv)
            print(f"Adding OPV: {new_opv.name}...")

            # 2. Insert BJT (Full Parameters)
            new_bjt = BJT(
                name="2N2222A",
                bjt_type="NPN",
                dc_current_gain_hfe="100-300",
                collector_emitter_voltage="40V",
                collector_base_voltage="75V",
                emitter_base_voltage="6V",
                base_emitter_on_voltage="0.6V to 1.2V"
            )
            db.session.add(new_bjt)
            print(f"Adding BJT: {new_bjt.name}...")

            # 3. Insert MOSFET (Full Parameters)
            new_mosfet = MOSFET(
                name="IRFZ44N",
                mosfet_type="N-Kanal",
                drain_source_voltage="55V",
                gate_source_voltage="±20V",
                continuous_drain_current="49A",
                gate_threshold_voltage="2.0V to 4.0V"
            )
            db.session.add(new_mosfet)
            print(f"Adding MOSFET: {new_mosfet.name}...")

            # Commit all
            db.session.commit()
            
            print("\nSUCCESS: All components inserted!")
            print(f"-> OPV ID: {new_opv.id}")
            print(f"-> BJT ID: {new_bjt.id}")
            print(f"-> MOSFET ID: {new_mosfet.id}")

        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: Insertion failed. {str(e)}")

if __name__ == "__main__":
    run_test_insert()
