import os
from urllib.parse import urlparse

# --- НАСТРОЙКИ ---
INPUT_FILE = "V2rayCompletetest.txt"
OUTPUT_DIR = "SortedConfigs"

def sort_by_protocol():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден!")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Словарь для хранения ссылок по протоколам
    protocols = {"vless": [], "vmess": [], "trojan": [], "ss": [], "hysteria2": []}

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # Определяем протокол
            protocol = line.split("://")[0]
            if protocol in protocols:
                protocols[protocol].append(line)

    # Сохраняем в разные файлы
    for proto, links in protocols.items():
        if links:
            filename = os.path.join(OUTPUT_DIR, f"{proto}_subs.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(links))
            print(f"✅ Сохранено {len(links)} конфигов для {proto} в {filename}")

if __name__ == "__main__":
    sort_by_protocol()