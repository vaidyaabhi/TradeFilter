#!/usr/bin/env python3
import os
import time
import webbrowser
import threading
import logging
from flask import Flask, request
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv, set_key, find_dotenv

# --- SETUP ---
ENV_PATH = find_dotenv()
load_dotenv(ENV_PATH)

# Fetching directly from .env
CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
REDIRECT_URI = "http://127.0.0.1:5000/login" 
REFRESH_TOKEN_FILE = "refresh_token.txt"

captured_auth_code = None

# Mute Flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/login')
def callback_handler():
    global captured_auth_code
    code = request.args.get('auth_code')
    if code:
        captured_auth_code = code
        return "<h1>✅ Login Successful!</h1><p>Captured. Close this tab.</p>"
    return "❌ Error: No code found."

def start_server():
    app.run(port=5000, debug=False, use_reloader=False)

def get_new_token():
    global captured_auth_code
    
    # 1. SILENT RENEWAL
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, "r") as f:
            refresh_token = f.read().strip()
        
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID, secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI, response_type="code", grant_type="refresh_token"
        )
        session.set_token(refresh_token)
        response = session.generate_token()
        
        if "access_token" in response:
            print("🔄 Token refreshed silently!")
            return response["access_token"]

    # 2. BROWSER LOGIN
    session = fyersModel.SessionModel(
        client_id=CLIENT_ID, secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI, response_type="code", grant_type="authorization_code"
    )

    threading.Thread(target=start_server, daemon=True).start()
    print("🌐 Opening Fyers Login...")
    webbrowser.open(session.generate_authcode())
    
    while not captured_auth_code:
        time.sleep(1)
    
    session.set_token(captured_auth_code)
    response = session.generate_token()

    if "access_token" in response:
        with open(REFRESH_TOKEN_FILE, "w") as f:
            f.write(response["refresh_token"])
        return response["access_token"]
    return None

def verify_and_login():
    token = os.getenv("FYERS_ACCESS_TOKEN")
    
    # Check if existing token works
    fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=token, is_async=False)
    profile = fyers.get_profile()

    if profile.get('s') == 'ok':
        name = profile.get('data', {}).get('name', 'Trader')
        print(f"✨ Session active for {name}. No login required.")
    else:
        print("⚠️ Session expired. Renewing...")
        new_token = get_new_token()
        if new_token:
            set_key(ENV_PATH, "FYERS_ACCESS_TOKEN", new_token)
            print("✅ .env updated successfully!")

if __name__ == "__main__":
    verify_and_login()
    os._exit(0)