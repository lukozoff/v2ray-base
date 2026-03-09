import subprocess
import os

def run_pipeline():
    print("[*] Запуск полного цикла автоматизации...")
    
    # 1. Запуск основного тестера
    print("[*] Шаг 1: Тестирование конфигов...")
    subprocess.run(["python", "V2RayTester.py"], check=True)
    
    # 2. Сортировка по протоколам
    print("[*] Шаг 2: Сортировка по протоколам...")
    subprocess.run(["python", "Sorter.py"], check=True)
    
    # 3. Отправка в GitHub
    print("[*] Шаг 3: Отправка результатов в облако отключенно...")
    
    print("\n[+] Полный цикл успешно завершен!")

if __name__ == "__main__":
    run_pipeline()