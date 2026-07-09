import asyncio
import aiohttp
from tqdm.asyncio import tqdm_asyncio

import json
from config import DOMAIN
from pathlib import Path
from utils.tvivu import extract_main_stream, extract_all_urls

BASE_DIR = Path(__file__).resolve().parent

url = "https://tvivu.com/api/channels/trending"

MAX_CONCURRENT_REQUESTS = 50

async def fetch_page(session, page):
    async with session.get(f"{url}?page={page}") as resp:
        data = await resp.json()
        return data.get('channels', [])

async def test_stream(session, url):
    async with session.get(url, timeout=25, allow_redirects=True) as resp:
        # await resp.content.read(2048)
        if resp.status < 400: return True
    return False


async def fetch_channel_streams(session, ch, sem):
    async with sem:
        url = f"https://tvivu.com/watch/{ch['slug']}"
        try:
            async with session.get(url, timeout=10) as resp:
                html = await resp.text()
                main_stream_link = extract_main_stream(html)
                
                if not main_stream_link:
                    return None
                    
                all_streams = extract_all_urls(html)

                candidates = [main_stream_link] + all_streams[:3]
                valid_links = []
                for link in all_streams[:3]:
                    if await test_stream(session, link):
                        valid_links.append(link)

                is_ok = await test_stream(session, main_stream_link)
                if not is_ok:
                    if not valid_links: return None
                    main_stream_link = valid_links[0]
                if not valid_links: valid_links=[main_stream_link]

                return {
                    'id': ch['id'],
                    'slug': ch['slug'],
                    'name': ch['name'],
                    'languageCode': ch['languageCode'],
                    'countryCode': ch['countryCode'],
                    'logoUrl': ch['logoUrl'],
                    'main_stream_link': main_stream_link,
                    'major_stream_links': valid_links[:2]
                }
        except Exception as e:
            print(e)
            return None


async def main():
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:

        async with session.get(url) as resp:
            first_page_data = await resp.json()
            total_pages = first_page_data.get('totalPages', 1)
            all_channels = first_page_data.get('channels', [])

        page_tasks = [fetch_page(session, i) for i in range(1, total_pages + 1)]
        remaining_pages = await asyncio.gather(*page_tasks)
        for page_channels in remaining_pages:
            all_channels.extend(page_channels)

        sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        stream_tasks = [fetch_channel_streams(session, ch, sem) for ch in all_channels]

        valid_channels = []
        for coro in tqdm_asyncio.as_completed(stream_tasks, total=len(all_channels), desc="Extracting Streams"):
            result = await coro
            if result:
                valid_channels.append(result)

    txt_direct = txt_proxy = txt_proxy_language_wise_multilinks = '#EXTM3U'
    for ch in valid_channels:
        idz = ch['id']
        slug = ch['slug']
        name = ch['name']
        logo = ch['logoUrl']
        country = ch['countryCode']
        language = ch['languageCode']

        link=f"https://{DOMAIN}/tvivu/{slug}"
        direct_link = ch['main_stream_link']
        links = ch['major_stream_links']

        txt_proxy += f'\n#EXTINF:-1 tvg-id="{idz}" tvg-logo="{logo}" group-title="{country}",{name}\n{link}'
        txt_proxy_language_wise_multilinks += f'\n#EXTINF:-1 tvg-id="{idz}" tvg-logo="{logo}" group-title="{country}",{name}\n{"\n".join(links)}\n'
        txt_direct += f'\n#EXTINF:-1 tvg-id="{idz}" tvg-logo="{logo}" group-title="{country}",{name}\n{direct_link}'

    with open(BASE_DIR / 'playlist.m3u','w') as f: f.write(txt_proxy)
    with open(BASE_DIR / 'playlist-direct.m3u','w') as f: f.write(txt_direct)
    with open(BASE_DIR / 'playlist-languagewise.m3u','w') as f: f.write(txt_proxy_language_wise_multilinks)


if __name__ == "__main__":
    asyncio.run(main())

