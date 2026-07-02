import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DOMAIN="iptv.prax.to"

SESSION_DIR = PROJECT_ROOT / "sessions"

CHANNEL_MAP=json.loads(open(PROJECT_ROOT / "cf/servicewise_channels_map.json").read())
