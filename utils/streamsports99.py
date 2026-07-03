import re
import requests
import base64
import urllib.parse

def get_link(option,path):
    path=urllib.parse.unquote(path)
    name,code=path.rsplit("__",1)

    url=f"https://cdnlivetv.tv/api/v1/channels/player/?name={name}&code={code}&user=cdnlivetv&plan=free"
    print(url)
    response = requests.get(url)
    html_content = response.text
    print(html_content)

    var_definitions = re.findall(r"(?:var\s+)?(\w+)\s*=\s*'([^']+)'", html_content)
    vars_dict = {name: value for name, value in var_definitions}

    decoder_function_name=re.findall(r"function (\w+)\(s\)\{", html_content)
    url_assembly_sequence = re.findall(fr"{decoder_function_name}\((\w\w+)\)", html_content)

    decoded_chunks = []
    for var_name in url_assembly_sequence:
        b64_str = vars_dict[var_name]

        b64_str = b64_str.replace("-", "+").replace("_", "/")

        while len(b64_str) % 4 != 0:
            b64_str += "="

        try:
            decoded_text = base64.b64decode(b64_str).decode("utf-8")
            decoded_chunks.append(decoded_text)
        except Exception as e:
            print(f"Error decoding variable {var_name}: {e}")
    complete_stream_url = "".join(decoded_chunks)
    return complete_stream_url
