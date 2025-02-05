from farmbot import Farmbot
import json
import os
from getpass import getpass

TOKEN_FILE = 'farmbot_authorization_token.json'

def load_token():
    """Load the authorization token from the file or fetch a new one if not present."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            return json.load(file)
    else:
        return fetch_token()

def fetch_token():
    """Prompt the user for credentials to fetch a new authorization token."""
    SERVER = input('FarmBot Web App account server (press <Enter> for https://my.farm.bot): ') or 'https://my.farm.bot'
    EMAIL = input('FarmBot Web App account login email: ')
    PASSWORD = getpass('FarmBot Web App account login password: ')

    fb = Farmbot()
    token = fb.get_token(EMAIL, PASSWORD, SERVER)

    with open(TOKEN_FILE, 'w') as file:
        json.dump(token, file)

    print('Token saved to file')
    return token
