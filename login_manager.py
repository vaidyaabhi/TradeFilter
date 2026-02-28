#!/usr/bin/env python3
import os
import time
import webbrowser
import threading
import logging
from flask import Flask, request
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv, set_key

# --- SETUP ---
load_dotenv()
CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
# Ensure this matches your Fyers App dashboard exactly
REDIRECT_URI = "http://127.0.0.1:5000/login" 

REFRESH_TOKEN_FILE = "refresh_token.txt"
captured_auth_code = None

# Reduce Flask logging clutter
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/login')
def callback_handler():
    global captured_auth_code
    code = request.args.get('auth_code')
    if code:
        captured_auth_code = code
        return """
        <html>
            <body style="background-color:#e8f5e9; text-align:center; padding-top:50px; font-family:sans-serif;">
                <h1 style="color:#2e7d32;">✅ Login Successful!</h1>
                <p>The code has been captured. You can close this window.</p>
            </body>
        </html>
        """
    return "❌ Error: No auth_code found."

def start_listener_server():
    app.run(port=5000, debug=False, use_reloader=False)

def get_new_token():
    global captured_auth_code

    # 1. Try Auto-Renewal (Silent)
    if os.path.exists(REFRESH_TOKEN_FILE):
        print("🔄 Attempting silent renewal...")
        with open(REFRESH_TOKEN_FILE, "r") as f:
            refresh_token = f.read().strip()
        
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID, secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI, response_type="code", grant_type="refresh_token"
        )
        session.set_token(refresh_token)
        response = session.generate_token()
        
        if "access_token" in response:
            print("🚀 Auto-Renewal Successful!")
            return response["access_token"]

    # 2. Automated Browser Login
    session = fyersModel.SessionModel(
        client_id=CLIENT_ID, secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI, response_type="code", grant_type="authorization_code"
    )

    server_thread = threading.Thread(target=start_listener_server, daemon=True)
    server_thread.start()

    print("\n🌐 Opening Fyers Login...")
    webbrowser.open(session.generate_authcode())
    
    while captured_auth_code is None:
        time.sleep(1)
    
    session.set_token(captured_auth_code)
    response = session.generate_token()

    if "access_token" in response:
        with open(REFRESH_TOKEN_FILE, "w") as f:
            f.write(response["refresh_token"])
        return response["access_token"]
    return None

if __name__ == "__main__":
    token = get_new_token()
    if token:
        set_key(".env", "FYERS_ACCESS_TOKEN", token)
        print("✅ Access Token saved to .env!")
        os._exit(0)
