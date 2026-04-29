import sys
import os
import json
import subprocess
import urllib.request
import urllib.error


GITHUB_USER   = "pressure88" 
GITHUB_REPO   = "update" 
GITHUB_BRANCH = "main"
SCRIPT_FILE   = "update.pyw" 


VERSION = "1.0.1"

RAW_URL     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{SCRIPT_FILE}"
API_URL     = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits?sha={GITHUB_BRANCH}&per_page=1&path={SCRIPT_FILE}"
LOCAL_SHA   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_commit_sha")


def _get_remote_sha() -> str | None:
    """Получает SHA последнего коммита файла с GitHub API."""
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "auto-updater/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            commits = json.loads(resp.read().decode())
            if commits:
                return commits[0]["sha"]
    except Exception as e:
        print(f"[updater] Не удалось проверить обновления: {e}")
    return None


def _get_local_sha() -> str | None:
    """Читает сохранённый SHA из файла."""
    if os.path.exists(LOCAL_SHA):
        with open(LOCAL_SHA, "r") as f:
            return f.read().strip()
    return None


def _save_sha(sha: str) -> None:
    with open(LOCAL_SHA, "w") as f:
        f.write(sha)


def _download_and_restart(sha: str) -> None:
    """Скачивает новую версию скрипта и перезапускает процесс."""
    script_path = os.path.abspath(__file__)
    backup_path = script_path + ".bak"

    print("[updater] Скачиваю обновление...")
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


def check_for_updates() -> None:
    """Точка входа для проверки обновлений. Вызывай в начале main()."""
    print(f"[updater] Версия {VERSION}. Проверяю обновления на GitHub...")
    remote_sha = _get_remote_sha()
    if remote_sha is None:
        return

    local_sha = _get_local_sha()
    if remote_sha == local_sha:
        print("[updater] Версия актуальна.\n")
        return

    print(f"[updater] Найдено обновление (SHA: {remote_sha[:7]})!")
    _download_and_restart(remote_sha)



def main():
    check_for_updates()   # ← всегда первой строкой

    # --- дальше твой код ---
    print(f"Привет! Скрипт версии {VERSION} работает.")
    print("Добавь сюда свою логику.")


if __name__ == "__main__":
    main()
