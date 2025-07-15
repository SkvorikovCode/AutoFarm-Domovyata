import os
import sys
import time
import subprocess
import requests

GITHUB_REPO = 'SkvorikovCode/Valya'
RELEASE_ASSET = 'main_console.exe'
LOCAL_EXE = 'main_console.exe'
VERSION_FILE = 'version.txt'

# --- Функция завершения main_console.exe ---
def kill_main():
    try:
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

# --- Получение информации о последнем релизе ---
def get_latest_release_info():
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        tag = data.get('tag_name')
        for asset in data.get('assets', []):
            if asset['name'] == RELEASE_ASSET:
                return tag, asset['browser_download_url']
    except Exception as e:
        print(f'Ошибка получения релиза: {e}')
    return None, None

# --- Работа с локальной версией ---
def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_local_version(version):
    with open(VERSION_FILE, 'w') as f:
        f.write(version)

# --- Основная логика ---
def main():
    print('Проверка обновлений...')
    tag, url = get_latest_release_info()
    local_version = get_local_version()
    if not tag or not url:
        print('Не удалось получить информацию о новой версии.')
        return
    if tag == local_version:
        print(f'У вас уже последняя версия ({tag}).')
        return
    print(f'Обнаружена новая версия: {tag} (текущая: {local_version})')
    print('Завершаю main_console.exe...')
    kill_main()
    time.sleep(2)
    print('Удаляю старый main_console.exe...')
    try:
        os.remove(LOCAL_EXE)
    except Exception as e:
        print(f'Ошибка удаления: {e}')
    print('Скачиваю новую версию...')
    if download_new_exe(url, LOCAL_EXE):
        print('Сохраняю новый тег версии...')
        save_local_version(tag)
        print('Запускаю новый main_console.exe...')
        subprocess.Popen([LOCAL_EXE], close_fds=True)
    else:
        print('Не удалось обновить main_console.exe!')

if __name__ == '__main__':
    main() 