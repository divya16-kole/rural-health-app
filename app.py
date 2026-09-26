from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)


# ==================================================
# DATABASE
# ==================================================

DATABASE = "ruralcare.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db()
    cursor = conn.cursor()

    # ----------------------------------------------
    # PHARMACIES TABLE
    # ----------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pharmacies (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            owner_name TEXT,

            phone TEXT,

            address TEXT,

            latitude REAL,

            longitude REAL,

            created_at TEXT NOT NULL

        )
    """)


    # ----------------------------------------------
    # MEDICINE INVENTORY TABLE
    # ----------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_inventory (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pharmacy_id INTEGER NOT NULL,

            medicine_name TEXT NOT NULL,

            available INTEGER NOT NULL DEFAULT 0,

            quantity INTEGER DEFAULT 0,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (pharmacy_id)
                REFERENCES pharmacies(id)

        )
    """)


    conn.commit()
    conn.close()


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# AI TRIAGE API
# ==================================================

@app.route("/api/triage", methods=["POST"])
def triage():

    data = request.get_json(silent=True) or {}

    symptoms = data.get("symptoms", [])
    details = (data.get("details") or "").strip()
    language = data.get("language", "English")


    # Make sure symptoms is a list

    if isinstance(symptoms, str):
        symptoms = [symptoms] if symptoms else []


    # Remove empty values

    symptoms = [
        str(symptom).strip()
        for symptom in symptoms
        if str(symptom).strip()
    ]


    # Combine symptoms + additional details

    combined_text = " ".join(symptoms)

    if details:
        combined_text += " " + details

    text = combined_text.lower()


    # --------------------------------------------------
    # URGENT RED FLAGS
    # --------------------------------------------------

    urgent_keywords = [
        "chest pain",
        "shortness of breath",
        "difficulty breathing",
        "severe bleeding",
        "unconscious",
        "fainting",
        "seizure"
    ]


    # --------------------------------------------------
    # MEDICAL CONSULTATION SYMPTOMS
    # --------------------------------------------------

    consultation_keywords = [
        "fever",
        "vomiting",
        "diarrhea",
        "dizziness",
        "burning urination",
        "frequent urination",
        "abdominal pain",
        "stomach pain",
        "persistent cough",
        "weakness"
    ]


    # --------------------------------------------------
    # TRIAGE LOGIC
    # --------------------------------------------------

    if any(keyword in text for keyword in urgent_keywords):

        urgency = "Urgent Care Required"

        message = (
            "Some reported symptoms may need prompt professional "
            "medical assessment. Please contact a qualified healthcare "
            "professional or local emergency service."
        )

        level = "urgent"


    elif any(keyword in text for keyword in consultation_keywords):

        urgency = "Medical Consultation Recommended"

        message = (
            "Consider speaking with a qualified healthcare professional, "
            "especially if the symptoms persist, worsen, or are concerning."
        )

        level = "consultation"


    else:

        urgency = "No Urgent Red Flag Detected"

        message = (
            "The prototype did not detect an urgent symptom from the "
            "information provided. Continue monitoring your symptoms "
            "and seek professional medical care if they persist or worsen."
        )

        level = "low"


    # --------------------------------------------------
    # API RESPONSE
    # --------------------------------------------------

    return jsonify({

        "success": True,

        "urgency": urgency,

        "level": level,

        "message": message,

        "language": language,

        "symptoms": symptoms,

        "details": details

    })


# ==================================================
# PHARMACY SEARCH API
# ==================================================

@app.route("/api/pharmacy/search", methods=["GET"])
def search_medicine():

    medicine = request.args.get("medicine", "").strip()

    if not medicine:

        return jsonify({
            "success": False,
            "message": "Please enter a medicine name."
        }), 400


    conn = get_db()

    cursor = conn.cursor()


    # Search participating pharmacies that have
    # reported the medicine as available.

    cursor.execute("""
        SELECT

            pharmacies.id AS pharmacy_id,

            pharmacies.name AS pharmacy_name,

            pharmacies.owner_name,

            pharmacies.phone,

            pharmacies.address,

            pharmacies.latitude,

            pharmacies.longitude,

            medicine_inventory.medicine_name,

            medicine_inventory.quantity,

            medicine_inventory.updated_at

        FROM medicine_inventory

        INNER JOIN pharmacies

            ON pharmacies.id = medicine_inventory.pharmacy_id

        WHERE

            medicine_inventory.available = 1

            AND LOWER(
                medicine_inventory.medicine_name
            ) LIKE LOWER(?)

        ORDER BY medicine_inventory.updated_at DESC

    """, (f"%{medicine}%",))


    results = cursor.fetchall()

    conn.close()


    pharmacies = []


    for row in results:

        pharmacies.append({

            "pharmacy_id": row["pharmacy_id"],

            "pharmacy_name": row["pharmacy_name"],

            "owner_name": row["owner_name"],

            "phone": row["phone"],

            "address": row["address"],

            "latitude": row["latitude"],

            "longitude": row["longitude"],

            "medicine_name": row["medicine_name"],

            "quantity": row["quantity"],

            "updated_at": row["updated_at"]

        })


    return jsonify({

        "success": True,

        "medicine": medicine,

        "count": len(pharmacies),

        "pharmacies": pharmacies

    })


# ==================================================
# PHARMACY REGISTRATION API
# ==================================================

@app.route("/api/pharmacy/register", methods=["POST"])
def register_pharmacy():

    data = request.get_json(silent=True) or {}


    name = (data.get("name") or "").strip()

    owner_name = (data.get("owner_name") or "").strip()

    phone = (data.get("phone") or "").strip()

    address = (data.get("address") or "").strip()

    latitude = data.get("latitude")

    longitude = data.get("longitude")


    if not name:

        return jsonify({

            "success": False,

            "message": "Pharmacy name is required."

        }), 400


    conn = get_db()

    cursor = conn.cursor()


    created_at = datetime.now().isoformat(timespec="seconds")


    cursor.execute("""
        INSERT INTO pharmacies
        (
            name,
            owner_name,
            phone,
            address,
            latitude,
            longitude,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

    """, (
        name,
        owner_name,
        phone,
        address,
        latitude,
        longitude,
        created_at
    ))


    pharmacy_id = cursor.lastrowid

    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message": "Pharmacy registered successfully.",

        "pharmacy_id": pharmacy_id

    })


# ==================================================
# PHARMACY INVENTORY UPDATE API
# ==================================================

@app.route("/api/pharmacy/inventory", methods=["POST"])
def update_inventory():

    data = request.get_json(silent=True) or {}


    pharmacy_id = data.get("pharmacy_id")

    medicine_name = (data.get("medicine_name") or "").strip()

    available = data.get("available", False)

    quantity = data.get("quantity", 0)


    if not pharmacy_id:

        return jsonify({

            "success": False,

            "message": "Pharmacy ID is required."

        }), 400


    if not medicine_name:

        return jsonify({

            "success": False,

            "message": "Medicine name is required."

        }), 400


    try:

        quantity = int(quantity)

    except (ValueError, TypeError):

        quantity = 0


    available = 1 if available else 0


    updated_at = datetime.now().isoformat(
        timespec="seconds"
    )


    conn = get_db()

    cursor = conn.cursor()


    # Check whether this pharmacy already
    # has this medicine in its inventory.

    cursor.execute("""
        SELECT id

        FROM medicine_inventory

        WHERE pharmacy_id = ?

        AND LOWER(medicine_name) = LOWER(?)

    """, (
        pharmacy_id,
        medicine_name
    ))


    existing = cursor.fetchone()


    if existing:

        cursor.execute("""
            UPDATE medicine_inventory

            SET

                available = ?,

                quantity = ?,

                updated_at = ?,

                medicine_name = ?

            WHERE id = ?

        """, (
            available,
            quantity,
            updated_at,
            medicine_name,
            existing["id"]
        ))


    else:

        cursor.execute("""
            INSERT INTO medicine_inventory
            (
                pharmacy_id,
                medicine_name,
                available,
                quantity,
                updated_at
            )

            VALUES (?, ?, ?, ?, ?)

        """, (
            pharmacy_id,
            medicine_name,
            available,
            quantity,
            updated_at
        ))


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message": "Medicine availability updated successfully.",

        "medicine": medicine_name,

        "available": bool(available),

        "quantity": quantity,

        "updated_at": updated_at

    })


# ==================================================
# PHARMACY LIST API
# ==================================================

@app.route("/api/pharmacies", methods=["GET"])
def get_pharmacies():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM pharmacies

        ORDER BY name
    """)


    rows = cursor.fetchall()

    conn.close()


    pharmacies = []


    for row in rows:

        pharmacies.append({

            "id": row["id"],

            "name": row["name"],

            "owner_name": row["owner_name"],

            "phone": row["phone"],

            "address": row["address"],

            "latitude": row["latitude"],

            "longitude": row["longitude"],

            "created_at": row["created_at"]

        })


    return jsonify({

        "success": True,

        "count": len(pharmacies),

        "pharmacies": pharmacies

    })
@app.route("/api/pharmacy/<int:pharmacy_id>/inventory", methods=["GET"])
def get_pharmacy_inventory(pharmacy_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            medicine_name,
            available,
            quantity,
            updated_at
        FROM medicine_inventory
        WHERE pharmacy_id = ?
        ORDER BY medicine_name
    """, (pharmacy_id,))

    rows = cursor.fetchall()
    conn.close()

    inventory = []

    for row in rows:
        inventory.append({
            "id": row["id"],
            "medicine_name": row["medicine_name"],
            "available": bool(row["available"]),
            "quantity": row["quantity"],
            "updated_at": row["updated_at"]
        })

    return jsonify({
        "success": True,
        "pharmacy_id": pharmacy_id,
        "count": len(inventory),
        "inventory": inventory
    })


# ==================================================
# HEALTH CHECK API
# ==================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "success": True,

        "status": "RuralCare AI backend is running"

    })


# ==================================================
# INITIALIZE DATABASE
# ==================================================

init_database()


# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
