from bs4 import BeautifulSoup
import requests
from config import DOMAIN
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

r = requests.get("https://dlhd.st/24-7-channels.php")

txt='#EXTM3U'

def build_inf(slug,title):
    global txt
    link=f"https://{DOMAIN}/dlhd/{slug}"
    txt+=f'\n#EXTINF:-1 group-title="DLHD",{title}\n{link}'

soup = BeautifulSoup(r.content, 'html.parser')

items = soup.find_all('a', class_='card')
for item in items:
    title = item.find("div", class_="card__title").text
    slug = item.get("href").split("=")[-1]
    build_inf(slug,title)

with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt)



