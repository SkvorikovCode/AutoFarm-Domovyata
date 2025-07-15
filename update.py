import os
import sys
import time
import subprocess
import requests

GITHUB_REPO = 'SkvorikovCode/Valya'
RELEASE_ASSET = 'main_console.exe'
LOCAL_EXE = 'main_console.exe'

# --- Функция завершения main_console.exe ---
def kill_main():
    try:
        # Windows: taskkill
        subprocess.call(['taskkill', '/F', '/IM', LOCAL_EXE])
    except Exception as e:
        print(f'Ошибка завершения {LOCAL_EXE}: {e}')

# --- Функция скачивания нового exe ---
def download_new_exe(download_url, dest):
    try:
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
        print(f'Скачан новый {dest}')
        return True
    except Exception as e:
        print(f'Ошибка скачивания: {e}')
        return False

# --- Проверка новой версии через GitHub Releases ---
def get_latest_release_asset_url():
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        for asset in data.get('assets', []):
            if asset['name'] == RELEASE_ASSET:
                return asset['browser_download_url']
    except Exception as e:
        print(f'Ошибка получения релиза: {e}')
    return None

# --- Основная логика ---
def main():
    print('Проверка обновлений...')
    url = get_latest_release_asset_url()
    if not url:
        print('Не удалось получить ссылку на новую версию.')
        return
    # TODO: сравнить версию/хэш локального exe и удалённого (можно по времени или версии)
    # Для простоты — всегда обновлять
    print('Обновление найдено! Завершаю main_console.exe...')
    kill_main()
    time.sleep(2)
    print('Удаляю старый main_console.exe...')
    try:
        os.remove(LOCAL_EXE)
    except Exception as e:
        print(f'Ошибка удаления: {e}')
    print('Скачиваю новую версию...')
    if download_new_exe(url, LOCAL_EXE):
        print('Запускаю новый main_console.exe...')
        subprocess.Popen([LOCAL_EXE], close_fds=True)
    else:
        print('Не удалось обновить main_console.exe!')

if __name__ == '__main__':
    main() 