import requests
import json
import os
from datetime import datetime, timedelta
import jwt
from config import SESSION_DIR

nettv_session = SESSION_DIR / "nettv.json"
try: token_data = json.loads(open(nettv_session).read())
except: token_data={"access_token":"","refresh_token":""}

wmsauthsign=""
lastupdt=datetime.now()-timedelta(hours=1)

def do_refresh_token(access_token=None,refresh_token=None):
    global token_data

    if not access_token:
        access_token=token_data['access_token']
        refresh_token=token_data['refresh_token']

    if not access_token or not refresh_token:
        print("Empty tokens")
        return False

    try:
        session_id=jwt.decode(access_token, options={"verify_signature": False})['sid']
        r=requests.post('https://auth.geniustv.geniussystems.com.np/v2/subscribers/refresh-token',json={"refresh_token":refresh_token,"session_id":session_id}).json()
        token_data['access_token']=r['access_token']
        token_data['refresh_token']=r['refresh_token']
    except: 
        print("Invalid tokens")
        return False

    with open(nettv_session,'w') as f: 
        json.dump(token_data, f)

    return True


def get_authsign(is_retry=False):
    global wmsauthsign, lastupdt

    if (datetime.now()-lastupdt).seconds<2400: 
        return wmsauthsign

    try:
        wmsauthsign=requests.get('https://resources.geniustv.geniussystems.com.np/nimble/wmsauthsign/',headers={"Authorization": f"Bearer {token_data['access_token']}"}).json()['wmsauthsign']
        lastupdt=datetime.now()        
    except:
        if not is_retry:
            if do_refresh_token():
                return get_authsign(is_retry=True)

        wmsauthsign=''
        lastupdt=datetime.now()-timedelta(hours=1)

    return wmsauthsign


def receive_token(data):
    if not ('access_token' or 'refresh_token') in data: 
        return "missing parameters"

    legit = do_refresh_token(access_token=data['access_token'], refresh_token=data['refresh_token'])

    if legit: return "SUCCESS"
    else: return "INVALID"


get_authsign()
