# Vobiz Speak Demo

A minimal Flask app that acts as a **Vobiz answer URL**. When a call comes in,
Vobiz fetches this app over HTTP and executes the VobizXML it returns — here, a
single [`<Speak>`](https://www.vobiz.ai/docs/xml/speak) element that reads a
text-to-speech message to the caller.

The XML served is exactly:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Speak voice="WOMAN" language="en-US" loop="1">Welcome to Vobiz.</Speak>
</Response>
```

Reference: [Speak — Play a message](https://www.vobiz.ai/docs/xml/speak/play-a-message)

## How it works

```
caller ──▶ Vobiz ──GET──▶ tunnel (Cloudflare/ngrok) ──▶ Flask :5001 /answer
                 ◀── VobizXML (application/xml) ──────────────┘
```

1. A call reaches your Vobiz number or application.
2. Vobiz sends a **GET** request to your configured Answer URL.
3. This app responds with VobizXML and `Content-Type: application/xml`.
4. Vobiz executes the `<Speak>` verb and the caller hears the message.

Because Vobiz must reach your machine from the public internet, local
development needs a tunnel.

## Endpoints

| Method     | Path      | Purpose                                                                 |
| ---------- | --------- | ----------------------------------------------------------------------- |
| `GET`      | `/answer` | The answer URL. Returns the `<Speak>` VobizXML. **GET only** — POST 405s. |
| `GET/POST` | `/hangup` | Optional end-of-call webhook; logs the payload and returns `204`.        |
| `GET`      | `/`       | Health check, returns `{"ok": true, "answer_url": "/answer"}`.           |

## Quick start (step by step)

Requires **Python 3.9+** and a terminal. Every command below is meant to be run
in order.

### 1. Clone the repo

```bash
git clone https://github.com/Piyush-sahoo/vobiz-demo-xml.git
cd vobiz-demo-xml
```

### 2. Create a virtual environment

A venv keeps this project's packages isolated from your system Python.

```bash
python3 -m venv .venv
```

This creates a `.venv/` folder (already git-ignored). You only do this once.

### 3. Activate the virtual environment

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

Your prompt now starts with `(.venv)`. You must re-activate it in every new
terminal window. To leave it later, run `deactivate`.

### 4. Install the dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

That installs Flask, the only dependency.

### 5. Start the app

```bash
PORT=5001 python3 app.py
```

You should see Flask report that it is running on `http://0.0.0.0:5001`.
**Leave this terminal open** — the server runs in the foreground.

### 6. Verify it locally

Open a **second terminal** and run:

```bash
curl "http://127.0.0.1:5001/answer?CallUUID=test123&From=919999999999"
```

Expected output:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Speak voice="WOMAN" language="en-US" loop="1">Welcome to Vobiz.</Speak>
</Response>
```

If you see that XML, the app is working. If you get "connection refused", the
server in step 5 isn't running.

### 7. Expose it to the internet with a tunnel

Vobiz is a cloud service, so it cannot reach `127.0.0.1`. A tunnel gives your
local server a public HTTPS URL.

#### Option A — Cloudflare Tunnel (recommended, no account needed)

Install it once:

```bash
# macOS
brew install cloudflared

# Linux / Windows: see https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

Then, in a **third terminal**, start the tunnel:

```bash
cloudflared tunnel --url http://localhost:5001
```

It prints a public hostname, for example:

```
https://random-words-go-here.trycloudflare.com
```

Leave this terminal open too. Your answer URL is that hostname + `/answer`.

#### Option B — ngrok

Install it once (`brew install ngrok`), authenticate with
`ngrok config add-authtoken <your-token>`, then run:

```bash
ngrok http 5001
```

Copy the `https://....ngrok-free.dev` forwarding URL it displays.

> **Note:** ngrok's free plan allows only **one agent session at a time**. If you
> already have a tunnel running elsewhere, either stop it first or use
> Cloudflare (Option A) instead.

### 8. Confirm the public URL works

```bash
curl "https://<your-tunnel-host>/answer"
```

You should get the same XML as in step 6. Only then move on.

> **Heads up:** quick-tunnel hostnames from both Cloudflare and ngrok are
> **ephemeral**. Restarting the tunnel gives you a new hostname, and you must
> update the Answer URL in the Vobiz console to match.

### 9. Point Vobiz at it

In the Vobiz console, edit your application and set:

- **Answer URL:** `https://<your-tunnel-host>/answer`
- **Method:** `GET`
- **Hangup URL** (optional): `https://<your-tunnel-host>/hangup`

Then call the number attached to that application. You should hear the message.

### Stopping everything

Press `Ctrl+C` in the tunnel terminal, then in the Flask terminal, then run
`deactivate` to exit the virtual environment.

## Configuration

All `<Speak>` attributes are overridable by environment variable — no code
changes needed.

| Variable         | Default            | Notes                                           |
| ---------------- | ------------------ | ----------------------------------------------- |
| `SPEAK_TEXT`     | `Welcome to Vobiz.` | The text read to the caller.                    |
| `SPEAK_VOICE`    | `WOMAN`            | `WOMAN` or `MAN`.                               |
| `SPEAK_LANGUAGE` | `en-US`            | See Vobiz's supported voices and languages.     |
| `SPEAK_LOOP`     | `1`                | Times to repeat; `0` loops indefinitely.        |
| `PORT`           | `5001`             | Local port Flask binds to.                      |

Example:

```bash
SPEAK_TEXT="Thanks for calling support." SPEAK_VOICE=MAN PORT=5001 python3 app.py
```

## Troubleshooting

| Symptom                        | Cause                                                                                     |
| ------------------------------ | ----------------------------------------------------------------------------------------- |
| Call connects then drops       | Wrong `Content-Type`. Vobiz needs `application/xml` or `text/xml`; `text/html` kills the call. |
| `405 Method Not Allowed`       | Vobiz is configured for POST. Set the Answer URL method to **GET**.                        |
| Vobiz can't reach the endpoint | Tunnel is down or the hostname changed after a restart. Re-check the URL in the console.   |
| No audio on the call           | Confirm the tunnel URL answers `curl`, and check `SPEAK_LANGUAGE` is a supported value.    |

## Docs

- [VobizXML `<Speak>`](https://www.vobiz.ai/docs/xml/speak)
- [Play a message](https://www.vobiz.ai/docs/xml/speak/play-a-message)
- [`<Response>` and Content-Type rules](https://www.vobiz.ai/docs/xml/response)
