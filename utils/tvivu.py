import re
import requests
import urllib.parse
import json

site_url='https://tvivu.com/watch'

def extract_main_stream(html_content):
    # pattern = r'https://stream\.tvivu\.com/\?url=[^\s"\'\\<>]+'
    pattern = r'streamUrl\\"\s*:\s*\\"(https://stream\.tvivu\.com/\?url=[^"\\]+)'
    matches = re.findall(pattern, html_content)

    for match in matches:
        clean_url = match.rstrip('\\')
            
        parsed_url = urllib.parse.urlparse(clean_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
            
        if 'url' in query_params:
            return query_params['url'][0]


def extract_all_urls(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', html, re.S)
 
    full_text = ""
    for c in chunks:
        try:
            decoded = json.loads(c)
        except json.JSONDecodeError:
            continue

        decoded = re.sub(r'^[0-9a-f]+:T[0-9a-f]+,', '', decoded)
        full_text += decoded + "\n"
 
    urls = re.findall(r'https://stream\.tvivu\.com/\?url=[^\s"\\<>]+', full_text)
 
    seen = set()
    result = []
    for u in urls:
        parsed_url = urllib.parse.urlparse(u)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        url = query_params['url'][0]

        if url not in seen:
            seen.add(url)
            result.append(url)

    return result 


def get_link(option,path):
    r = requests.get(f"{site_url}/{path}")
 
    return extract_main_stream(r.text)
