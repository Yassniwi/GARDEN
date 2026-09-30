import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_HISTORY = 20  # number of past messages sent to the model


def build_contents(history, message):
    """Convert chat history and the new message into Gemini's format."""
    contents = []
    for turn in history[-MAX_HISTORY:]:
        role = "user" if turn.get("role") == "user" else "model"
        text = str(turn.get("text", "")).strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please type a message."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.6,
            ),
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "Sorry, I couldn't come up with an answer. Please try again."
        return jsonify({"reply": reply})
    except Exception:
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
