# eyecon_flask_api.py
from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# --- CONFIG ---
DEFAULT_COUNTRY_CODE = "91"  # Add this if number has no country code
EYEON_BASE = "https://api.eyecon-app.com/app/getnames.jsp"

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    'accept': 'application/json',
    'e-auth-v': 'e1',
    'e-auth': 'c5f7d3f2-e7b0-4b42-aac0-07746f095d38',
    'e-auth-c': '40',
    'e-auth-k': 'PgdtSBeR0MumR7fO',
    'accept-charset': 'UTF-8',
    'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
    'Host': 'api.eyecon-app.com',
    'Connection': 'Keep-Alive'
}


def normalize_number(raw):
    """Normalize input number string and return a valid numeric string."""
    if raw is None:
        raise ValueError("No number provided")

    s = str(raw).strip()
    digits = re.sub(r'\D', '', s).lstrip('0')

    if len(digits) == 10:
        digits = DEFAULT_COUNTRY_CODE + digits
    elif len(digits) < 10:
        raise ValueError("Number too short after normalization")

    return digits


@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    if request.method == "GET":
        num_input = request.args.get("number") or request.args.get("cli")
    else:
        j = request.get_json(silent=True) or {}
        num_input = j.get("number") or request.form.get("number") or j.get("cli") or request.form.get("cli")

    try:
        normalized = normalize_number(num_input)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    params = {
        'cli': normalized,
        'lang': 'en',
        'is_callerid': 'true',
        'is_ic': 'true',
        'cv': 'vc_672_vn_4.2025.10.17.1932_a',
        'requestApi': 'URLconnection',
        'source': 'MenifaFragment'
    }

    try:
        resp = requests.get(EYEON_BASE, params=params, headers=DEFAULT_HEADERS, timeout=5)
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = resp.json()
        else:
            data = {"raw": resp.text}
        return jsonify({"ok": True, "cli": normalized, "status_code": resp.status_code, "data": data})
    except requests.Timeout:
        return jsonify({"ok": False, "error": "Request timed out"}), 504
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": "Request failed", "details": str(exc)}), 502


@app.route("/")
def index():
    return jsonify({
        "info": "Eyecon lookup API",
        "endpoints": ["/lookup?number=<number>"]
    })


# ⚠️ IMPORTANT: Do not run app.run() on Vercel
# Vercel uses its own WSGI server automatically.
# You can uncomment this line if you run locally:
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)
