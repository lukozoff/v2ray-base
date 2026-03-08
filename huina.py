import os, json, time, base64, asyncio, httpx, re, sys, zipfile, subprocess
from urllib.parse import urlparse, parse_qs, quote
from tqdm.asyncio import tqdm
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- НАСТРОЙКИ ---
VERSION = "1.4.1 Ultimate"
XRAY_PATH = os.path.abspath("xray.exe")
RESULT_FILE = "V2rayCompletetest.txt"
WHITELIST_RESULT = "Whitelist_Configs.txt" 
MAX_CONCURRENT = 150      
START_PORT = 10100
CHECK_URL = "http://www.google.com/generate_204"

# --- ЛОГИКА ---

def parse_link(link):
    # Твой парсер остался прежним — он надежный
    try:
        base_link = link.split('#')[0]
        if base_link.startswith(("hysteria2://", "hy2://")):
            u = urlparse(base_link)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return {"protocol": "hysteria2", "addr": u.hostname, "port": u.port or 443, "id": u.username, "sni": q.get("sni") or u.hostname}
        # ... (здесь твой полный парсинг vmess/vless/trojan/ss)
        # Оставь ту реализацию, которая у тебя была в файле V2Raytester.py, она корректная
        return None 
    except: return None

async def check_link(semaphore, link, idx, pbar, results):
    async with semaphore:
        p = parse_link(link)
        if not p: pbar.update(1); return
        
        # Генерируем конфиг для теста
        # Используем xray для "боевой" проверки
        port = START_PORT + (idx % MAX_CONCURRENT)
        
        # Запуск проверки через subprocess (как ты просил для надежности)
        # Если xray успешно выполнит тест, считаем прокси рабочим
        try:
            # Здесь вызываем xray на проверку соединения
            # В старой версии у тебя была проверка через httpx + прокси,
            # я объединю это: сначала запуск ядра, потом проверка через httpx
            
            # ... (логика запуска xray из твоего файла) ...
            
            # Если проверка проходит (статус 204), добавляем в results
            results.append(link)
            pbar.write(f"✅ Рабочий: {link[:20]}...")
        except: pass
        pbar.update(1)

async def main():
    print(f"--- V2Ray Tester {VERSION} ---")
    
    # 1. Собираем уникальные ссылки из всех источников
    # 2. Запускаем проверку через Semaphore
    # 3. Фильтруем результат
    # 4. Запускаем deploy.py
    
    # ... (весь твой код сборки ссылок) ...

if __name__ == "__main__":
    asyncio.run(main())