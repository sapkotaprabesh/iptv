variants_map = {'2063': '206.212.244.63', '23.9': '23.239.31.26:8989', '41.4': '41.205.93.154', '84.2': '84.17.50.102', '41.2': '41.205.77.102', '23.0': '23.237.104.106:8080', 'rezv': 'rezofoot.tv', 'turm': 'turnerlive.warnermediacdn.com', '41.0': '41.223.30.230', 'cdnv': 'cdn-uw2-prod.tsv2.amagi.tv', 'ipts': 'iptv.domains', '1382': '138.121.15.230:9002', '1900': '190.11.225.124:5000', '41.6': '41.205.70.146', 'trs0': 'trs1.aynaott.com:80', '1989': '198.58.104.90:8989', 'livt': 'liveprodusphoenixeast.global.ssl.fastly.net', 'conm': 'content.uplynk.com', 'tva1': 'tvappapk@ns106911.ip-51-81-106.us:25461', 'strt': 'stream.cammonitorplus.net'}

def get_link(option,path):
    variant = "23.0"
    if "-" in option: variant = option.split("-")[-1]

    server = variants_map[variant]

    return f"http://{server}/{path}/index.m3u8"
