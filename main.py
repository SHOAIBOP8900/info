# eyecon_flask_api.py
from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # optional: allow cross-origin requests

# --- CONFIG ---
DEFAULT_COUNTRY_CODE = "91"  # agar number me country code na ho to ye add karega
EYEON_BASE = "https://api.eyecon-app.com/app/getnames.jsp"

# Default headers (tumhare provided headers se liye gaye)
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
    """ Normalize input number string:
        - remove non-digits
        - if 10 digits -> prepend DEFAULT_COUNTRY_CODE
        - if starts with '0' -> strip leading zeros and apply rule
        - return as int-like-string or raise ValueError
    """
    if raw is None:
        raise ValueError("No number provided")
    s = str(raw).strip()
    # remove +, spaces, hyphens, parentheses, etc.
    digits = re.sub(r'\D', '', s)

    # strip leading zeros
    digits = digits.lstrip('0')

    if len(digits) == 10:
        # assume local 10-digit => prepend default country code
        digits = DEFAULT_COUNTRY_CODE + digits
    elif len(digits) < 10:
        raise ValueError("Number too short after normalization")
    # else: assume provided country code already present

    return digits

@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    # Accept number as query param or json/form field
    if request.method == "GET":
        num_input = request.args.get("number") or request.args.get("cli")
    else:
        # POST: accept JSON or form data
        j = {}
        try:
            j = request.get_json(silent=True) or {}
        except Exception:
            j = {}
        num_input = j.get("number") or request.form.get("number") or j.get("cli") or request.form.get("cli")

    try:
        normalized = normalize_number(num_input)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    # Build params similar to original script
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
        resp = requests.get(EYEON_BASE, params=params, headers=DEFAULT_HEADERS, timeout=10)
        # Try to return JSON if API gives JSON, else return text under 'raw'
        content_type = resp.headers.get('Content-Type','')
        if 'application/json' in content_type:
            data = resp.json()
        else:
            data = {"raw": resp.text}
        return jsonify({"ok": True, "cli": normalized, "status_code": resp.status_code, "data": data})
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": "request failed", "details": str(exc)}), 502

@app.route("/")
def index():
    return jsonify({"info": "Eyecon lookup API", "endpoints": ["/lookup?number=<number>"]})

if __name__ == "__main__":
    # Bind to 0.0.0.0 so it's accessible across network, port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
