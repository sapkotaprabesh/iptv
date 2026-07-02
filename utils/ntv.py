import requests
import json

def get_link(option,path):
    return requests.get("https://ntv.newitventure.com/api/v1/ntv/home/detail?type=channel&slug="+path,headers={"key":"nitv@123_123"}).json()["link"]
