import subprocess

def git_sync():
    try:
        print("[*] Подготовка Git...")
        # 1. Добавляем все новые файлы в индекс (чтобы они перестали быть untracked)
        subprocess.run(["git", "add", "."], check=True)
        
        # 2. Делаем временный коммит, чтобы сохранить текущее состояние
        # Это предотвращает ошибку "could not detach HEAD"
        subprocess.run(["git", "commit", "-m", "Auto-update configs and sorted results"], capture_output=True)
        
        # 3. Синхронизируемся с облаком через rebase
        # Если в облаке есть изменения, он просто поставит твои файлы поверх них
        print("[*] Синхронизация с репозиторием...")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        
        # 4. Отправляем всё в GitHub
        print("[*] Отправка данных...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("✅ GitHub успешно обновлен!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка Git: {e}")
        # Если совсем всё плохо, можно попробовать сброс (ОСТОРОЖНО: удалит локальные несохраненные правки)
        # subprocess.run(["git", "reset", "--hard", "origin/main"])