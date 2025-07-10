from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
import json
from dotenv import load_dotenv

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🚀 Bot WhatsApp Pharmacie est en ligne !"


# === Initialisation ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Chargement du fichier pharmacies.json ===
with open("pharmacies.json", encoding='utf-8') as f:
    pharmacies = json.load(f)

# === Formatage des données à injecter dans le prompt ===
def format_pharmacies(pharmacies):
    infos = []
    for p in pharmacies:
        ligne = f"- {p['nom']} ({p['quartier']}, {p['ville']}) | Responsable : {p.get('responsable', 'N/A')} | "
        ligne += f"Assurances : {', '.join(p.get('assurances_acceptees', []))} | "
        ligne += f"Garde : Nuit={p['garde_nuit']}, Weekend={p['garde_weekend']} | "
        ligne += f"Services : {', '.join(p.get('services_disponibles', []))}"
        infos.append(ligne)
    return "\n".join(infos[:15])  # Ne pas dépasser la limite de tokens

base_context = format_pharmacies(pharmacies)

# === Route Flask pour le bot WhatsApp ===
@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    response = MessagingResponse()
    msg = response.message()

    if not incoming_msg:
        msg.body("Bonjour ! Posez-moi une question sur les pharmacies.")
        return str(response)

    try:
        client = openai.OpenAI()  # SDK v1+

        system_prompt = f"""
        Tu es un assistant pharmacie intelligent pour le Togo. Voici des informations à ta disposition :\n{base_context}

        Règles :
        - Tu ne réponds qu'à partir des données fournies.
        - Si tu ne trouves pas une info, dis : "Je ne peux pas répondre précisément à cette question pour l’instant."
        - Sois clair, concis et professionnel.
        - Réponds toujours en français.

        Exemples de questions à traiter :
        - Où se trouve la pharmacie Huet ?
        - Quelles pharmacies acceptent CNSS ?
        - Quelles sont les pharmacies de garde ce week-end ?
        - Qui est le responsable de la pharmacie Jean S.A.S. ?
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=300,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": incoming_msg}
            ]
        )

        bot_reply = response.choices[0].message.content.strip()
        msg.body(bot_reply)

    except Exception as e:
        msg.body("Désolé, une erreur est survenue. Réessaie plus tard. Erreur OpenAI :")
        print("Erreur OpenAI :", e)

    return str(response) 

# === Lancement du serveur Flask ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)