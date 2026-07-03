import re
import requests
import base64

site_url='https://dlhd.st'
headers={"Referer":site_url}

def get_link(option,path):
    r = requests.get(f"{site_url}/stream/stream-{path}.php", headers=headers)
    link1 = re.findall("(?<=<iframe src=\").*?(?=\")",r.text,re.DOTALL)[0]

    r = requests.get(link1, headers=headers)
    link2=re.findall("(?<=window.atob\\(').*?(?=')",r.text,re.DOTALL)[0]

    return base64.b64decode(link2).decode('utf-8')
