import re
import requests
from config import DOMAIN, PROJECT_ROOT
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent

r = requests.get("http://nosslstreams.ufreetv.com/")

txt='#EXTM3U'

def build_inf(variant,slug,title):
    global txt
    link=f"https://{DOMAIN}/ufreetv-{variant}/{slug}"
    txt+=f'\n#EXTINF:-1 group-title="DLHD",{title}\n{link}'

variants_map={}

items = re.findall("<div class=\"channel\".*?(?=</div>)",r.text,re.DOTALL)
for item in items:
    title = re.findall("(?<=<span>).*?(?=<{0,1}/span>)",item)[0]
    title = title.strip().strip('#').strip()

    link = re.findall("(?<=playStream\\(').*?(?=')",item)[0]
    link_parsed = urlparse(link)
    hostname = link_parsed.netloc

    variant=hostname[:3]+hostname[-1]
    variants_map[variant] = hostname

    path = link_parsed.path
    slug=path.split('/')[1]

    build_inf(variant,slug,title)

with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)

util_file = PROJECT_ROOT / "utils/ufreetv.py"
with open(util_file, 'r') as f:
    lines = ["variants_map = "+str(variants_map)+"\n" if "variants_map = {" in line else line for line in f]

with open(util_file, 'w') as f:
    f.writelines(lines)

cf_index_js = PROJECT_ROOT / "cf/index.js"
with open(cf_index_js, 'r') as f:
    lines = ["const variants_map = "+str(variants_map)+";\n" if "const variants_map = {" in line else line for line in f]

with open(cf_index_js, 'w') as f:
    f.writelines(lines)

