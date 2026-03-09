import os, json, time, base64, asyncio, httpx, shutil, re, sys, zipfile
from urllib.parse import urlparse, parse_qs, quote
from tqdm.asyncio import tqdm
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- НАСТРОЙКИ ---
VERSION = "1.4.1 Ultimate"
XRAY_PATH = os.path.abspath("xray.exe")
SOURCE_FILE = "configs.txt" 
RESULT_FILE = "V2rayCompletetest.txt"
WHITELIST_RESULT = "Whitelist_Configs.txt" 
MAX_CONCURRENT = 180      
START_PORT = 10100
CHECK_URL = "http://www.google.com/generate_204"

COUNTRY_MAP = {
    "RU": ("🇷🇺", "Russia"), "UA": ("🇺🇦", "Ukraine"), "KZ": ("🇰🇿", "Kazakhstan"),
    "BY": ("🇧🇾", "Belarus"), "UZ": ("🇺🇿", "Uzbekistan"), "GE": ("🇬🇪", "Georgia"),
    "AM": ("🇦🇲", "Armenia"), "AZ": ("🇦🇿", "Azerbaijan"), "MD": ("🇲🇩", "Moldova"),
    "DE": ("🇩🇪", "Germany"), "NL": ("🇳🇱", "Netherlands"), "FR": ("🇫🇷", "France"),
    "GB": ("🇬🇧", "United Kingdom"), "FI": ("🇫🇮", "Finland"), "PL": ("🇵🇱", "Poland"),
    "US": ("🇺🇸", "USA"), "CA": ("🇨🇦", "Canada"), "BR": ("🇧🇷", "Brazil"), 
    "SG": ("🇸🇬", "Singapore"), "HK": ("🇭🇰", "Hong Kong"), "JP": ("🇯🇵", "Japan"),
    "TR": ("🇹🇷", "Turkey"), "AE": ("🇦🇪", "UAE"), "AU": ("🇦🇺", "Australia")
}

FIRMFOX_SOURCES = [
    "https://raw.githubusercontent.com/Firmfox/proxify/main/v2ray_configs/mixed/subscription-1.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt"
]

live_count = 0
geo_cache = {}

# --- УТИЛИТЫ ---

def check_and_download_xray():
    if os.path.exists(XRAY_PATH): return True
    print("🚀 Ядро Xray не найдено! Начинаю загрузку...")
    url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-windows-64.zip"
    try:
        with httpx.Client(follow_redirects=True) as client:
            r = client.get(url)
            with open("xray.zip", "wb") as f: f.write(r.content)
        with zipfile.ZipFile("xray.zip", 'r') as z: z.extractall(".")
        os.remove("xray.zip")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}"); return False

async def get_geo_pretty(client, ip):
    if ip in geo_cache: return geo_cache[ip]
    try:
        r = await client.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=2.0)
        data = r.json()
        if data.get("status") == "success":
            code = data['countryCode']
            emoji, name = COUNTRY_MAP.get(code, ("🌐", code))
            res = f"{emoji}{name}"
            geo_cache[ip] = res
            return res
    except: pass
    return "🌐Unknown"

def parse_link(link):
    try:
        base_link = link.split('#')[0]
        if base_link.startswith(("hysteria2://", "hy2://")):
            u = urlparse(base_link)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return {"protocol": "hysteria2", "addr": u.hostname, "port": u.port or 443, "id": u.username, "sni": q.get("sni") or u.hostname}
        if base_link.startswith("vmess://"):
            data = base_link[8:]; data += "=" * ((4 - len(data) % 4) % 4)
            d = json.loads(base64.b64decode(data).decode('utf-8'))
            return {"protocol": "vmess", "addr": d.get("add"), "port": int(d.get("port")), "id": d.get("id"), "net": d.get("net", "tcp"), "sec": d.get("tls", "none"), "sni": d.get("sni") or d.get("host"), "path": d.get("path")}
        if base_link.startswith(("vless://", "trojan://", "ss://")):
            u = urlparse(base_link); q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return {"protocol": u.scheme, "addr": u.hostname, "port": u.port, "id": u.username, "net": q.get("type", "tcp"), "sec": q.get("security") or q.get("tls", "none"), "sni": q.get("sni") or q.get("host") or u.hostname, "pbk": q.get("pbk"), "sid": q.get("sid"), "path": q.get("path")}
    except: return None

def generate_xray_config(p, port):
    outbound = {"protocol": p["protocol"], "settings": {}}
    if p["protocol"] == "hysteria2":
        outbound["settings"] = {"servers": [{"address": p["addr"], "port": p["port"], "password": p["id"]}]}
        outbound["streamSettings"] = {"network": "udp", "security": "tls", "tlsSettings": {"serverName": p["sni"]}}
    elif p["protocol"] == "ss":
        user_data = p.get("id") or ""
        if user_data and ":" not in user_data:
            try: user_data = base64.b64decode(user_data + "==").decode('utf-8')
            except: pass
        m, pwd = user_data.split(':', 1) if ":" in user_data else ("aes-256-gcm", user_data)
        outbound["settings"] = {"servers": [{"address": p["addr"], "port": p["port"], "method": m, "password": pwd}]}
    elif p["protocol"] == "trojan":
        outbound["settings"] = {"servers": [{"address": p["addr"], "port": p["port"], "password": p["id"]}]}
    else:
        outbound["settings"] = {"vnext": [{"address": p["addr"], "port": p["port"], "users": [{"id": p["id"], "encryption": "none"}]}]}

    if p["protocol"] != "hysteria2":
        outbound["streamSettings"] = {
            "network": p.get("net", "tcp"),
            "security": p.get("sec", "none") if p.get("sec") != "none" else "",
            "tlsSettings": {"serverName": p.get("sni") or p["addr"]} if p.get("sec") in ["tls", "reality"] else {},
            "realitySettings": {"serverName": p.get("sni") or p["addr"], "publicKey": p.get("pbk"), "shortId": p.get("sid"), "fingerprint": "chrome"} if p.get("sec") == "reality" else {},
            "wsSettings": {"path": p.get("path", "/")} if p.get("net") == "ws" else {}
        }
    return json.dumps({"log": {"loglevel": "none"}, "inbounds": [{"port": port, "protocol": "socks", "settings": {"udp": True}}], "outbounds": [outbound]})

# --- ЧЕКЕР ---

async def check_link(semaphore, geo_client, link, idx, pbar, results, wl):
    global live_count
    # Микро-задержка для стабильности запуска
    await asyncio.sleep(idx * 0.01 % 0.5) 
    
    async with semaphore:
        p = parse_link(link)
        if not p: pbar.update(1); return
        
        port = START_PORT + (idx % MAX_CONCURRENT)
        cfg_json = generate_xray_config(p, port)
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                XRAY_PATH, "run", "-c", "stdin:", 
                stdin=asyncio.subprocess.PIPE, 
                stdout=asyncio.subprocess.DEVNULL, 
                stderr=asyncio.subprocess.DEVNULL, 
                creationflags=0x08000000 
            )
            proc.stdin.write(cfg_json.encode()); await proc.stdin.drain(); proc.stdin.close()
            
            await asyncio.sleep(0.7) 
            
            start_t = time.time()
            try:
                async with httpx.AsyncClient(proxy=f"socks5://127.0.0.1:{port}", verify=False, timeout=3.5) as client:
                    resp = await client.get(CHECK_URL)
                    if resp.status_code == 204:
                        ping = int((time.time() - start_t) * 1000)
                        geo = await get_geo_pretty(geo_client, p["addr"])
                        live_count += 1
                        is_wl = str(p.get("sni", "")).lower() in wl
                        mark = "[WHITE-SNI]" if is_wl else f"[{geo}]"
                        results.append({"link": f"{link.split('#')[0]}#{quote(f'{mark} {ping}ms')}", "ping": ping, "white": is_wl})
                        tqdm.write(f" + [{live_count}] {geo} | {ping}ms")
            except: pass
        except: pass
        finally:
            if proc:
                try: proc.kill()
                except: pass
            pbar.update(1)

async def main():
    print(f"--- V2Ray Tester {VERSION} ---")
    if not check_and_download_xray(): return
    
    # Очистка перед стартом
    os.system("taskkill /F /IM xray.exe /T >nul 2>&1")
    
    async with httpx.AsyncClient(timeout=10.0, verify=False) as c:
        # Вайтлист
        try: 
            r_wl = await c.get("https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt")
            wl = set(d.strip().lower() for d in r_wl.text.splitlines() if d.strip() and not d.startswith('#'))
        except: wl = set()
        
        # Сбор ссылок
        all_links = []
        regex = r'(?:vless|vmess|trojan|ss|hysteria2|hy2)://[^\s|<>"\']+'
        for url in FIRMFOX_SOURCES:
            try: r = await c.get(url); all_links.extend(re.findall(regex, r.text))
            except: pass
        if os.path.exists(SOURCE_FILE):
            with open(SOURCE_FILE, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("http"):
                        try: r = await c.get(line.strip()); all_links.extend(re.findall(regex, r.text))
                        except: pass
                    else: all_links.extend(re.findall(regex, line))

    unique_links = list(set(all_links))
    print(f"[*] Собрано уникальных: {len(unique_links)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT); results = []
    async with httpx.AsyncClient() as geo_client:
        with tqdm(total=len(unique_links), unit="cfg", desc="Ultimate Check") as pbar:
            tasks = [asyncio.create_task(check_link(semaphore, geo_client, link, i, pbar, results, wl)) for i, link in enumerate(unique_links)]
            await asyncio.gather(*tasks)

    # Сохранение
    sorted_res = sorted(results, key=lambda x: x['ping'])
    with open(RESULT_FILE, "w", encoding="utf-8") as f: f.write("\n".join([r['link'] for r in sorted_res]))
    with open(WHITELIST_RESULT, "w", encoding="utf-8") as f: f.write("\n".join([r['link'] for r in sorted_res if r['white']]))
    
    # Итоговая зачистка
    os.system("taskkill /F /IM xray.exe /T >nul 2>&1")
    print(f"\n[+] Тест завершен. Рабочих конфигов: {len(results)}")
    
    # АВТОМАТИЧЕСКАЯ ОТПРАВКА В GITHUB
    print("\n[*] Отправка результатов в GitHub...")
    import subprocess
    subprocess.run(["python", "deploy.py"])

if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt: 
        os.system("taskkill /F /IM xray.exe /T >nul 2>&1")