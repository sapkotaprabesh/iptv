import argparse
import asyncio
import csv
import time
from pathlib import Path

import requests

try:
    import aiohttp
except ImportError:
    raise SystemExit("Missing dependency: pip install aiohttp tqdm --break-system-packages")

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(it, **kwargs):
        return it

BASE_DIR = Path(__file__).resolve().parent


# ---------- Step 1: fetch + flatten ----------

def fetch_candidates():
    r = requests.get("https://livegrid.app/famelack/channels/raw/categories/all-channels.json").json()
    countries = requests.get("https://livegrid.app/famelack/channels/raw/countries_metadata.json").json()

    candidates = []  # list of dicts: name, group, url
    for ch in r:
        if ch.get("isGeoBlocked"):
            continue
        if not ch.get("iptv_urls"):
            continue
        name = ch["name"]
        country_code = ch["country"].upper()
        if country_code not in countries:
            continue
        grp = countries[country_code]["country"]
        for url in ch["iptv_urls"]:
            candidates.append({"name": name, "group": grp, "url": url})
    return candidates


# ---------- Step 2: Stage 1 - HTTP reachability ----------

async def check_http(session, url, timeout, sem):
    async with sem:
        try:
            try:
                async with session.head(url, timeout=timeout, allow_redirects=True) as resp:
                    if resp.status < 400:
                        return url, "pass", f"HTTP {resp.status}"
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass

            async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                await resp.content.read(2048)
                if resp.status < 400:
                    return url, "pass", f"HTTP {resp.status}"
                return url, "fail", f"HTTP {resp.status}"
        except asyncio.TimeoutError:
            return url, "fail", "timeout"
        except aiohttp.ClientConnectorError as e:
            return url, "fail", f"connect error: {e}"
        except Exception as e:
            return url, "fail", f"error: {type(e).__name__}"


async def stage1(urls, concurrency, timeout):
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=0, ssl=False)
    results = {}
    async with aiohttp.ClientSession(connector=connector,
                                      headers={"User-Agent": "Mozilla/5.0"}) as session:
        tasks = [check_http(session, u, timeout, sem) for u in urls]
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Stage 1 (HTTP filter)"):
            url, status, detail = await coro
            results[url] = (status, detail)
    return results


# ---------- Step 3: Stage 2 - ffprobe validation ----------

async def check_ffprobe(url, timeout, sem):
    async with sem:
        cmd = [
            "ffprobe", "-v", "error",
            "-user_agent", "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "-timeout", "5000000",
            "-analyzeduration", "2000000",
            "-probesize", "2000000",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            "-i", url,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 10)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return url, "fail", "ffprobe timeout"

            if proc.returncode == 0 and stdout.strip():
                return url, "pass", stdout.decode(errors="ignore").strip().replace("\n", "|")
            err = stderr.decode(errors="ignore").strip().splitlines()
            return url, "fail", (err[-1] if err else f"ffprobe exit {proc.returncode}")
        except Exception as e:
            return url, "fail", f"error: {type(e).__name__}"


async def stage2(urls, concurrency, timeout):
    sem = asyncio.Semaphore(concurrency)
    results = {}
    tasks = [check_ffprobe(u, timeout, sem) for u in urls]
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Stage 2 (ffprobe)"):
        url, status, detail = await coro
        results[url] = (status, detail)
    return results


# ---------- Step 4: orchestration ----------

async def run(args):
    print("Fetching channel data...")
    candidates = fetch_candidates()
    print(f"Flattened to {len(candidates)} (channel, url) candidates")

    unique_urls = list({c["url"] for c in candidates})
    print(f"{len(unique_urls)} unique URLs to check")

    t0 = time.time()
    s1_results = await stage1(unique_urls, args.s1_conc, args.s1_timeout)
    survivors = [u for u, (status, _) in s1_results.items() if status == "pass"]
    print(f"Stage 1 done in {time.time()-t0:.1f}s — {len(survivors)}/{len(unique_urls)} reachable")

    s2_results = {}
    if not args.skip_stage2 and survivors:
        t1 = time.time()
        s2_results = await stage2(survivors, args.s2_conc, args.s2_timeout)
        passed = sum(1 for v in s2_results.values() if v[0] == "pass")
        print(f"Stage 2 done in {time.time()-t1:.1f}s — {passed}/{len(survivors)} confirmed streamable")

    # Determine final working url set
    if s2_results:
        working = {u for u, (status, _) in s2_results.items() if status == "pass"}
    else:
        working = set(survivors)

    # Optional: keep only first working url per channel
    seen_channels = set()
    kept = []
    for c in candidates:
        if c["url"] not in working:
            continue
        key = (c["name"], c["group"])
        if args.first_only:
            if key in seen_channels:
                continue
            seen_channels.add(key)
        kept.append(c)

    # Write playlist — one #EXTINF per url, as the spec requires
    lines = ["#EXTM3U"]
    for c in kept:
        lines.append(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}')
        lines.append(c["url"])
    (BASE_DIR / "playlist.m3u").write_text("\n".join(lines) + "\n")

    # Also dump a CSV audit log of every url checked
    with open(BASE_DIR / "check_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "stage1", "stage1_detail", "stage2", "stage2_detail"])
        for u in unique_urls:
            s1_status, s1_detail = s1_results.get(u, ("skip", ""))
            s2_status, s2_detail = s2_results.get(u, ("skip", ""))
            w.writerow([u, s1_status, s1_detail, s2_status, s2_detail])

    total = time.time() - t0
    print(f"\nTotal time: {total:.1f}s ({total/60:.1f} min)")
    print(f"Playlist entries written: {len(kept)} (from {len(candidates)} original candidates)")
    print(f"-> {BASE_DIR / 'playlist.m3u'}")
    print(f"-> {BASE_DIR / 'check_results.csv'} (full audit log)")


def main():
    p = argparse.ArgumentParser(description="Build + validate an M3U playlist from livegrid.app data")
    p.add_argument("--s1-conc", type=int, default=250, help="Stage 1 concurrency (HTTP)")
    p.add_argument("--s1-timeout", type=float, default=6.0, help="Stage 1 per-request timeout (s)")
    p.add_argument("--s2-conc", type=int, default=30, help="Stage 2 concurrency (ffprobe)")
    p.add_argument("--s2-timeout", type=float, default=8.0, help="Stage 2 per-probe timeout (s)")
    p.add_argument("--skip-stage2", action="store_true", help="Only run the fast HTTP filter, skip ffprobe")
    p.add_argument("--first-only", action="store_true", help="Keep only the first working url per channel")
    args = p.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
