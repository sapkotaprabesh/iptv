import re
import requests
import json
from config import DOMAIN
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

r = requests.get("https://api.cdnlivetv.tv/api/v1/channels?user=cdnlivetv&plan=free").json()

txt='#EXTM3U x-tvg-url="https://epg.pw/xmltv/epg_US.xml.gz"'

def fix_broken_json(text):
    # 0. Replace single quotes around keys/values with double quotes
    # text = re.sub(r"'(.*?)'", r'"\1"', text)
    # Matches '{' followed by quote
    text = re.sub(r'{\s*"?', r'{"', text)
    # 2. Ensure quote exists Before closing curly bracket }
    text = re.sub(r'"?\s*}', r'"}', text)
    # 3. Before and after colon :
    text = re.sub(r'"?\s*:\s*"?', r'":"', text)
    # 4. Before and after comma ,
    text = re.sub(r'"?\s*,\s*"?', r'","', text)
    text = json.loads(text)
    return text

map1 = open(BASE_DIR / "input-map1.js").read()
map1 = re.findall('(?<=const e={).*?(?=};)',map1)[0]
map1 = fix_broken_json("{"+map1+"}")

map2 = open(BASE_DIR / "input-map2.js").read()
map2 = re.findall('(?<=,S={).*?(?=},)',map2)[0]
map2 = fix_broken_json("{"+map2+"}")

def build_inf(idz,name,code,logo):
    global txt
    link=f"https://{DOMAIN}/streamsports99/{name}__{code}"
    txt+=f'\n#EXTINF:-1 tvg-id="{idz}"  tvg-logo="{logo}" group-title="streamsports99",{name}\n{link}'

for channel in r['channels']:
    name = channel['name']
    name_l = name.lower()
    idz=""
    if name_l in map1:
        map2_key=map1[name_l]
        if map2_key in map2:
            idz=map2[map2_key]
    if name_l in map2:
        idz=map2[name_l]
    if idz: print(idz, name_l)
    build_inf(idz,name,channel['code'],channel['image'])

with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)


