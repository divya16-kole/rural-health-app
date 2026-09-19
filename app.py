from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# AI TRIAGE API
# --------------------------------------------------

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


# --------------------------------------------------
# HEALTH CHECK API
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "RuralCare AI backend is running"
    })


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )