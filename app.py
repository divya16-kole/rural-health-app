from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# AI Triage API
@app.route("/api/triage", methods=["POST"])
def triage():

    data = request.get_json(silent=True) or {}

    symptoms = data.get("symptoms", [])
    details = (data.get("details") or "").strip()
    language = data.get("language", "English")

    if isinstance(symptoms, str):
        symptoms = [symptoms] if symptoms else []

    # Combine symptoms and additional details
    combined_text = " ".join(str(s) for s in symptoms)
    combined_text += " " + details

    text = combined_text.lower()

    # Symptoms that need urgent professional assessment
    urgent_keywords = [
        "chest pain",
        "shortness of breath",
        "difficulty breathing",
        "severe bleeding",
        "unconscious",
        "fainting",
        "seizure"
    ]

    # Symptoms for which medical consultation may be appropriate
    consultation_keywords = [
        "fever",
        "vomiting",
        "diarrhea",
        "dizziness",
        "burning urination",
        "frequent urination"
    ]

    # Determine urgency
    if any(keyword in text for keyword in urgent_keywords):

        urgency = "Urgent Care Required"

        message = (
            "Some reported symptoms may need prompt professional "
            "medical assessment. Please contact a qualified healthcare "
            "professional or local emergency service."
        )

    elif any(keyword in text for keyword in consultation_keywords):

        urgency = "Medical Consultation Recommended"

        message = (
            "Consider speaking with a qualified healthcare professional, "
            "especially if the symptoms persist, worsen, or are concerning."
        )

    else:

        urgency = "No Urgent Red Flag Detected"

        message = (
            "The prototype did not detect an urgent symptom from the "
            "information provided. Continue monitoring your symptoms "
            "and seek professional medical care if they persist or worsen."
        )

    return jsonify({
        "success": True,
        "urgency": urgency,
        "message": message,
        "language": language,
        "symptoms": symptoms,
        "details": details
    })


# Start application
if __name__ == "__main__":
    app.run(debug=True)