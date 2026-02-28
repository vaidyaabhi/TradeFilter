import os
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv, set_key

# 1. Load your credentials from .env
load_dotenv()
client_id = os.getenv("FYERS_CLIENT_ID")
secret_key = os.getenv("FYERS_SECRET_KEY")
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html" 

def get_access_token():
    # 2. Setup Fyers Session
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )

    # 3. Generate Auth URL
    auth_url = session.generate_auth_code()
    print(f"👉 Open this link in your browser:\n{auth_url}\n")
    
    # 4. Paste the code from the redirect URL
    auth_code = input("Enter the 'auth_code' from the URL: ")
    
    session.set_token(auth_code)
    response = session.generate_token()
    
    if "access_token" in response:
        token = response["access_token"]
        # 5. Automatically save token to your .env file
        set_key(".env", "FYERS_ACCESS_TOKEN", token)
        print("✅ Access Token generated and saved to .env!")
    else:
        print(f"❌ Error: {response}")

if __name__ == "__main__":
    get_access_token()
