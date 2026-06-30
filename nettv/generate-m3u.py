import json
from pathlib import Path

from config import DOMAIN

BASE_DIR = Path(__file__).resolve().parent

data=json.load(open(BASE_DIR / 'input.json','r'))['result']
cats=data["categories"]
maps=data["category_channel_map"]
chans=data["channels"]

txt='#EXTM3U x-tvg-url="https://sapkotaprabesh.github.io/nettv-epg/out/nettv.xml.gz"'

def build_inf(idz,link,title,logo,grp):
    global txt
    link=f"https://{DOMAIN}/nettv/{link}"
    txt+=f'\n#EXTINF:-1 tvg-id="nettv-{idz}" tvg-logo="{logo}" group-title="{grp}",{title}\n{link}'

for ch in chans:
    for mapp in maps:
        if mapp['channel_id']==ch['id']:
            for cat in cats: 
                if cat['id']==mapp['category_id']: grp=cat['category']
                if not grp in ['All','Nepali','HD']: 
                    break
    if grp=="All": grp="Nepali"

    build_inf(ch['id'],ch['channel_urls'][0]['path'],ch['name'],ch['logo'],grp)
	
with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)
