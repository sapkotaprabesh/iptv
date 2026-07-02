import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import importlib
import urllib.parse
from config import CHANNEL_MAP
from utils import nettv

from apscheduler.schedulers.background import BackgroundScheduler

class Redirect(BaseHTTPRequestHandler):
    def do_GET(self):
        splits = self.path.split('/')
        option = splits[1]
        p_option = option.split('-')[0]
        path = '/'.join(splits[2:])
        p_path = urllib.parse.unquote(path)

        util = importlib.import_module(f"utils.{p_option}")

        out = util.get_link(option,path)

        if not out: return

        self.send_response(302)
        self.send_header('Location', out)
        self.end_headers()

    def do_POST(self):
        option = self.path.split('/')[1].split('-')[0]

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        parsed_post_data = json.loads(post_data)

        try: util = importlib.import_module(f"utils.{option}")
        except: return

        response = util.hadle_post(parsed_post_data)

        self.wfile.write(bytes(response, 'UTF-8'))


def run_crons():
    nettv.do_refresh_token()

scheduler = BackgroundScheduler()
scheduler.add_job(run_crons, 'interval', hours=6)
scheduler.start()

port = int(os.environ.get("PORT", 10000))
HTTPServer(("0.0.0.0", port), Redirect).serve_forever()
