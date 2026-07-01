## Ready-to-use

- https://sapkotaprabesh.github.io/iptv/nettv/playlist.m3u
- https://sapkotaprabesh.github.io/iptv/ntv/playlist.m3u

## Self-host

- Set domain in `config.py` and generate m3us:
```
python -m nettv.generate-m3u
(Outputs nettv/playlist.m3u)

python -m ntv.generate-m3u
(Outputs ntv/playlist.m3u)
```

- pip install -r requirements.txt

- python main.py

_For cloudflare deployment instead of python, see `cf/`_

## Setup

- Login to nettv and get tokens
```
const data = JSON.parse(decodeURIComponent((document.cookie.match(/(^|; )\s*ntv_u\s*=\s*([^;]+)/) || [])[2] || "{}"));
JSON.stringify(data)
```

- Post it to `/nettv` endpoint as application/json

