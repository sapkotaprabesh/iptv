import requests
import json
from config import DOMAIN
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

r = requests.get("https://ntv.newitventure.com/api/v1/ntv/channels").json()

txt='#EXTM3U'

def build_inf(slug,title,logo):
    global txt
    link=f"https://{DOMAIN}/ntv/{slug}"
    txt+=f'\n#EXTINF:-1 tvg-id="ntv-{slug}" tvg-logo="{logo}" group-title="Nepali",{title}\n{link}'

for item in r['items']:
    build_inf(item['slug'],item['title'],item['logo'])
    
with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)
