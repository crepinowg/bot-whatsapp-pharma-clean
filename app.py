from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# === Initialisation ===
app = Flask(__name__)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# === Chargement des données pharmacie ===
with open("pharmacies.json", encoding='utf-8') as f:
    pharmacies = json.load(f)

def format_pharmacies(pharmacies):
    infos = []
    for p in pharmacies:
        ligne = f"- {p['nom']} ({p['quartier']}, {p['ville']}) | Responsable : {p.get('responsable', 'N/A')} | "
        ligne += f"Assurances : {', '.join(p.get('assurances_acceptees', []))} | "
        ligne += f"Garde : Nuit={p['garde_nuit']}, Weekend={p['garde_weekend']} | "
        ligne += f"Services : {', '.join(p.get('services_disponibles', []))}"
        infos.append(ligne)
    return "\n".join(infos[:15])

base_context = format_pharmacies(pharmacies)

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot WhatsApp Pharma avec Gemini est en ligne !"

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    response = MessagingResponse()
    msg = response.message()

    if not incoming_msg:
        msg.body("Bonjour ! Posez-moi une question sur les pharmacies.")
        return str(response)

    try:
        model = genai.GenerativeModel("models/gemini-pro")  # correct name
        prompt = f"""Tu es un assistant pharmacie pour le Togo. Voici les données à ta disposition :\n{base_context}\n
Réponds précisément à cette question de l'utilisateur :
\"{incoming_msg}\""""

        gemini_response = model.generate_content(prompt)
        msg.body(gemini_response.text)

    except Exception as e:
        msg.body(e)
        print("Erreur Gemini:", e)

    return str(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)