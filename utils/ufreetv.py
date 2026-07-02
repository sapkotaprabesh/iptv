from config import CHANNEL_MAP

variants_map={"23":"23.237.104.106:8080","84":"84.17.50.102"}

def get_link(option,path):
    variant = "23"
    if "-" in option: variant = option.split("-")[-1]

    slug = CHANNEL_MAP[path][option]
    server = variants_map[variant]

    return f"http://{server}/{slug}/index.m3u8"
