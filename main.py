import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import urllib.parse
from utils import nettv

from apscheduler.schedulers.background import BackgroundScheduler

class Redirect(BaseHTTPRequestHandler):
    def do_GET(self):
        out=None
            
        splits = self.path.split('/')
        option = splits[1]
        path = '/'.join(splits[2:])
        p_path = urllib.parse.unquote(path)

        if option=='nettv':
            wmsauthsign = nettv.get_authsign()
            out=f"https://ott-lb.nettv.com.np/{path}/playlist.m3u8?wmsAuthSign="+wmsauthsign
        if option=='ntv':
            out = requests.get("https://ntv.newitventure.com/api/v1/ntv/home/detail?type=channel&slug="+path,headers={"key":"nitv@123_123"}).json()["link"]
        else: return

        self.send_response(302)
        self.send_header('Location', out)
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        parsed_post_data = json.loads(post_data)

        if self.path=="/nettv":
            self.wfile.write(bytes(nettv.receive_token(parsed_post_data), 'UTF-8'))

        return

def run_crons():
    nettv.do_refresh_token()

scheduler = BackgroundScheduler()
scheduler.add_job(run_crons, 'interval', hours=6)
scheduler.start()

port = int(os.environ.get("PORT", 10000))
HTTPServer(("0.0.0.0", port), Redirect).serve_forever()
