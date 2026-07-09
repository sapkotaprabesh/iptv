import requests
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

r = requests.get("https://livegrid.app/famelack/channels/raw/categories/all-channels.json").json()
countries = requests.get("https://livegrid.app/famelack/channels/raw/countries_metadata.json").json()

txt='#EXTM3U'

def build_inf(name,urls,grp):
    global txt
    txt+=f'\n#EXTINF:-1 group-title="{grp}",{name}'
    for url in urls: txt+=f"\n{url}"

for ch in r:
    if ch["isGeoBlocked"]: continue

    name = ch['name']

    urls=[]
    if ch['iptv_urls']: urls += ch['iptv_urls']
    if ch['youtube_urls']: urls += ch['youtube_urls']
    if not urls: continue

    grp = countries[ch["country"].upper()]['country']

    build_inf(name,urls,grp)

with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)






