from farmbot import Farmbot
from getpass import getpass
import json

# inputs
SERVER = input('FarmBot Web App account server (press <Enter> for https://my.farm.bot): ') or 'https://my.farm.bot'
EMAIL = input('FarmBot Web App account login email: ')
PASSWORD = getpass('FarmBot Web App account login password: ')

fb = Farmbot()
TOKEN = fb.get_token(EMAIL, PASSWORD, SERVER)
print(f'{TOKEN = }')

# save token to file
with open('farmbot_authorization_token.json', 'w') as f:
    f.write(json.dumps(TOKEN))
    print('token saved to file')