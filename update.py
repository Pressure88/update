#!/usr/bin/env python3

import sys
import os
import json
import threading
import urllib.request

# ══════════════════════════════════════════════
#  НАСТРОЙКИ — измени под себя
# ══════════════════════════════════════════════
GITHUB_USER    = "Pressure88"      # твой GitHub логин
GITHUB_REPO    = "update"          # название репозитория
GITHUB_BRANCH  = "main"               # ветка (main или master)
SCRIPT_FILE    = "update.py"          # имя этого файла в репозитории
CHECK_INTERVAL = 30                   # как часто проверять обновления (секунды)
# ══════════════════════════════════════════════

VERSION = "1.0.6"

RAW_URL   = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{SCRIPT_FILE}"
API_URL   = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?sha={GITHUB_BRANCH}&per_page=1&path={SCRIPT_FILE}"
LOCAL_SHA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_commit_sha")


def _get_remote_sha() -> str | None:
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "auto-updater/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            commits = json.loads(resp.read().decode())
            if commits:
                return commits[0]["sha"]
    except Exception as e:
        print(f"\n[updater] Не удалось проверить обновления: {e}")
    return None


def _get_local_sha() -> str | None:
    if os.path.exists(LOCAL_SHA):
        with open(LOCAL_SHA, "r") as f:
            return f.read().strip()
    return None


def _save_sha(sha: str) -> None:
    with open(LOCAL_SHA, "w") as f:
        f.write(sha)


def _download_and_restart(sha: str) -> None:
    script_path = os.path.abspath(__file__)
    backup_path = script_path + ".bak"

    print("\n[updater] Скачиваю обновление...")
    try:
        req = urllib.request.Request(RAW_URL, headers={"User-Agent": "auto-updater/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            new_code = resp.read()
    except Exception as e:
        print(f"[updater] Ошибка скачивания: {e}. Продолжаю с текущей версией.")
        return

    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(script_path, backup_path)
        with open(script_path, "wb") as f:
            f.write(new_code)
        os.chmod(script_path, 0o755)
        _save_sha(sha)
        print("[updater] Обновление установлено! Перезапускаю...\n")
    except Exception as e:
        print(f"[updater] Не удалось записать файл: {e}")
        if os.path.exists(backup_path):
            os.rename(backup_path, script_path)
        return

    os.execv(sys.executable, [sys.executable] + sys.argv)


def _check_once() -> None:
    """Одна проверка обновления."""
    remote_sha = _get_remote_sha()
    if remote_sha is None:
        return
    local_sha = _get_local_sha()
    if remote_sha == local_sha:
        print(f"[updater] Версия {VERSION} актуальна.")
        return
    print(f"[updater] Найдено обновление (SHA: {remote_sha[:7]})!")
    _download_and_restart(remote_sha)



def _updater_loop(stop_event: threading.Event) -> None:
    """Крутится в фоне и проверяет обновления каждые CHECK_INTERVAL секунд."""
    _check_once()  # сразу при запуске

    while not stop_event.wait(CHECK_INTERVAL):
        print(f"\n[updater] Плановая проверка (каждые {CHECK_INTERVAL} сек)...")
        _check_once()


def start_updater() -> threading.Event:
    """
    Запускает фоновый поток обновления.
    Возвращает stop_event — вызови stop_event.set() для остановки потока.
    """
    stop_event = threading.Event()
    thread = threading.Thread(target=_updater_loop, args=(stop_event,), daemon=True)
    thread.start()
    return stop_event

def main():
    print(f"Скрипт версии {VERSION} запущен.")


    stop_updater = start_updater()


    try:
        import time
        while True:
            print("Программа работает... (Ctrl+C для выхода)")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nВыход.")
        stop_updater.set()


if __name__ == "__main__":
    main()
