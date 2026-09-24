"""Minimal Vobiz answer-URL app: plays a TTS message with <Speak>.

Docs: https://www.vobiz.ai/docs/xml/speak/play-a-message
"""

import os
from flask import Flask, Response, request

app = Flask(__name__)

# <Speak> attributes: voice (WOMAN|MAN), language (default en-US), loop (0 = forever)
MESSAGE = os.environ.get("SPEAK_TEXT", "Welcome to Vobiz.")
VOICE = os.environ.get("SPEAK_VOICE", "WOMAN")
LANGUAGE = os.environ.get("SPEAK_LANGUAGE", "en-US")
LOOP = os.environ.get("SPEAK_LOOP", "1")


@app.route("/answer", methods=["GET"])
def answer():
    """Vobiz GETs this when the call is answered and executes the XML it returns."""
    params = request.args.to_dict()
    app.logger.info("ANSWER %s", params)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Speak voice="{VOICE}" language="{LANGUAGE}" loop="{LOOP}">{MESSAGE}</Speak>
</Response>"""
    # Content-Type must be application/xml or text/xml, or Vobiz drops the call.
    return Response(xml, mimetype="application/xml")


@app.route("/hangup", methods=["GET", "POST"])
def hangup():
    """Optional: Vobiz posts the call result here when the call ends."""
    app.logger.info("HANGUP %s", request.form.to_dict() or request.args.to_dict())
    return ("", 204)


@app.route("/", methods=["GET"])
def health():
    return {"ok": True, "answer_url": "/answer"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
