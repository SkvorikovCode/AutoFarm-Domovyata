# --- Требуемые библиотеки ---
# pip install pyautogui pynput pystray pillow speedtest-cli win10toast
# Если что-то не установлено — скрипт выведет предупреждение в лог

import time
import random
import threading
import sys
import os
import subprocess
import requests
import glob

# Импортируем pyautogui
try:
    import pyautogui
except ImportError:
    pyautogui = None
    print('pyautogui не установлен!')

# Импортируем pynput
try:
    from pynput import keyboard
except ImportError:
    keyboard = None
    print('pynput не установлен!')

# Импортируем pystray
try:
    import pystray
except ImportError:
    pystray = None
    print('pystray не установлен!')

# Импортируем Pillow
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None
    print('Pillow (PIL) не установлен!')

# Импортируем speedtest
try:
    import speedtest
except ImportError:
    speedtest = None
    print('speedtest-cli не установлен!')

# Импорт для tkinter alert
try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None
    messagebox = None
    print('tkinter не установлен!')

# Импортируем win10toast для уведомлений (только Windows)
try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None

# Импортируем colorama для поддержки ANSI-цветов в Windows
try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

# Импортируем opencv-python (cv2) для работы с шаблонами
try:
    import cv2
except ImportError:
    cv2 = None
    print('opencv-python (cv2) не установлен!')

# Импортируем numpy для работы с изображениями
try:
    import numpy as np
except ImportError:
    np = None
    print('numpy не установлен!')

# --- Настройки ---
# START_KEY = keyboard.KeyCode.from_vk(97)  # Numpad 1
# STOP_KEY = keyboard.KeyCode.from_vk(98)   # Numpad 2

# --- Настройки шагов ---
# Было: STEP_BOTTOM_BEFORE = 12, STEP_BOTTOM_AFTER = 12
STEP_BOTTOM = 12  # основной шаг по низу
STEP_CROSS = 18   # шаг по области крестика (ещё реже)
STEP_TOP = 3      # верх (оставим как было)
CLICK_DELAY = 55  # задержка между кликами (мс), замедлено на 30%

# --- Настройки циклов ---
CACHE_CLEAN_INTERVAL = 3  # Очистка кеша каждые N циклов

# --- Вспомогательные функции ---
def rnd(a, b):
    return random.randint(a, b)

def waitms(ms):
    time.sleep(ms / 1000.0)

def wait(s):
    time.sleep(s)

# --- Для контроля мыши ---
last_target_pos = [None, None]  # Последняя целевая позиция (x, y)
user_moved_mouse = False

def notify_user(title, msg):
    # Уведомление в консоль
    print(f"\033[91m[УВЕДОМЛЕНИЕ]\033[0m {title}: {msg}")
    # Уведомление в Windows
    if ToastNotifier is not None:
        try:
            toaster = ToastNotifier()
            result = toaster.show_toast(title, msg, duration=5, threaded=False)
            if not result:
                log(f"win10toast: уведомление не было показано (show_toast вернул False)")
        except Exception as e:
            log(f"Ошибка показа win10toast: {e}")
    else:
        log('win10toast не установлен! Не могу показать системное уведомление.')

# --- Переопределяем функции клика и перемещения ---
def lclick(x, y, ms_delay=0):
    global last_target_pos
    last_target_pos = [x, y]
    if pyautogui:
        pyautogui.click(x, y, button='left')
    else:
        log(f"pyautogui не установлен! Не могу кликнуть по ({x},{y})")
    if ms_delay:
        waitms(ms_delay)

def ldown(x, y):
    global last_target_pos
    last_target_pos = [x, y]
    if pyautogui:
        pyautogui.mouseDown(x, y, button='left')
    else:
        log(f"pyautogui не установлен! Не могу mouseDown по ({x},{y})")

def lup(x, y):
    global last_target_pos
    last_target_pos = [x, y]
    if pyautogui:
        pyautogui.mouseUp(x, y, button='left')
    else:
        log(f"pyautogui не установлен! Не могу mouseUp по ({x},{y})")

def move(x, y):
    global last_target_pos
    last_target_pos = [x, y]
    if pyautogui:
        pyautogui.moveTo(x, y)
    else:
        log(f"pyautogui не установлен! Не могу moveTo ({x},{y})")

LOG_FILE = 'logs.txt'

def log(*args, **kwargs):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(' '.join(str(a) for a in args) + '\n')
        f.flush()

# --- Глобальные переменные ---
stop_script = False
script_running = False
script_thread = None
cycle_counter = 0  # Счетчик циклов для очистки кеша

TRAY_STATUS = 'red'  # red (остановлен), green (работает), yellow (пауза)
tray_icon = None
tray_thread = None

# --- Слушатель мыши ---
try:
    from pynput import mouse
except ImportError:
    mouse = None

mouse_listener = None

def on_mouse_move(x, y):
    global user_moved_mouse, last_target_pos, script_running
    if script_running and last_target_pos[0] is not None and last_target_pos[1] is not None:
        # Если пользователь двигает мышь далеко от целевой точки
        dist = ((x - last_target_pos[0]) ** 2 + (y - last_target_pos[1]) ** 2) ** 0.5
        if dist > 30:  # Порог чувствительности (пиксели)
            user_moved_mouse = True
            # Возвращаем мышь на место
            if pyautogui:
                pyautogui.moveTo(last_target_pos[0], last_target_pos[1])
            notify_user(
                "Вмешательство мыши!",
                "Скрипт продолжает работу. Для остановки нажмите Numpad 2."
            )
            log("Пользователь переместил мышь, возвращаем на ({}, {})".format(last_target_pos[0], last_target_pos[1]))

if mouse is not None:
    mouse_listener = mouse.Listener(on_move=on_mouse_move)
    mouse_listener.start()
else:
    log('pynput.mouse не установлен! Контроль мыши не работает.')

def create_icon(color):
    if Image is None or ImageDraw is None:
        log('Pillow (PIL) не установлен!')
        return None
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if color == 'green':
        fill = (0, 200, 0, 255)
    elif color == 'yellow':
        fill = (255, 200, 0, 255)
    else:
        fill = (200, 0, 0, 255)
    draw.ellipse((8, 8, 56, 56), fill=fill)
    return img

def on_tray_exit(icon, item):
    log('Выход по меню трея')
    icon.stop()
    os._exit(0)

def tray_run():
    global tray_icon, TRAY_STATUS
    if pystray is None:
        log('pystray не установлен! Трей не будет запущен.')
        return
    menu = pystray.Menu(pystray.MenuItem('Закрыть', on_tray_exit))
    tray_icon = pystray.Icon('valya', create_icon(TRAY_STATUS), 'Valya', menu)
    tray_icon.run()

def update_tray_status(status):
    global tray_icon, TRAY_STATUS
    TRAY_STATUS = status
    if tray_icon:
        tray_icon.icon = create_icon(status)
        tray_icon.visible = True

# Запуск трея в отдельном потоке
tray_thread = threading.Thread(target=tray_run, daemon=True)
tray_thread.start()

# --- Функция очистки кеша игры ---
# Удаляем функцию clean_game_cache и все её вызовы

# --- Функция очистки сухостоя ---
def clean_withered_plants():
    log("===> Начало очистки сухостоя")
    update_tray_status('yellow')
    try:
        # КООРДИНАТЫ ДЛЯ ЗАПОЛНЕНИЯ - ОЧИСТКА СУХОСТОЯ
        # Примерный алгоритм:
        
        # 1. Выбор инструмента для удаления сухостоя (если требуется)
        lclick(0, 0)  # ЗАМЕНИТЬ! КООРДИНАТЫ КНОПКИ/ИНСТРУМЕНТА ДЛЯ УДАЛЕНИЯ
        wait(1)
        
        # 2. Очистка сухостоя на нижней грядке
        log("Очистка сухостоя на нижней грядке")
        for var in range(150, 1825, 10):  # Шаг можно скорректировать
            if stop_script: return
            lclick(var, 278)  # На 2 пикселя ниже обычных растений (было 276)
            waitms(50)
        
        # 3. Очистка сухостоя на верхней грядке
        log("Очистка сухостоя на верхней грядке")
        for var in range(480, 1410, 10):  # Шаг можно скорректировать
            if stop_script: return
            lclick(var, 134)  # На 2 пикселя ниже обычных растений (было 132)
            waitms(50)
        
        log("Сухостой очищен")
    except Exception as e:
        log(f"ОШИБКА ПРИ ОЧИСТКЕ СУХОСТОЯ: {e}")
    update_tray_status('green')
    log("<=== Завершение очистки сухостоя")

# --- Остановка и запуск ---
def on_press(key):
    global stop_script, script_running, script_thread
    vk_code = getattr(key, 'vk', None)
    char = getattr(key, 'char', None)
    name = getattr(key, 'name', None)
    log(f"Нажата клавиша: {key}, vk: {vk_code}, char: {char}, name: {name}")

    # Проверяем только Numpad клавиши 1/2/3
    if (vk_code == 97 or name == 'num1') and not script_running:
        log("Скрипт запущен (Numpad 1)")
        stop_script = False
        script_running = True
        update_tray_status('green')
        script_thread = threading.Thread(target=main_loop)
        script_thread.start()
    elif (vk_code == 98 or name == 'num2') and script_running:
        log("Скрипт остановлен (Numpad 2)")
        stop_script = True
        script_running = False
        update_tray_status('red')
    elif (vk_code == 99 or name == 'num3') and not script_running:
        log("Скрипт запущен только сбор (Numpad 3)")
        stop_script = False
        script_running = True
        update_tray_status('green')
        script_thread = threading.Thread(target=collect_rows_loop)
        script_thread.start()
    elif (vk_code == 100 or name == 'num4') and not script_running:
        # Удаляем запуск очистки кеша и сухостоя по Numpad 4
        pass

if keyboard is not None:
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
else:
    log('pynput не установлен! Горячие клавиши не будут работать.')

# --- Функция обслуживания (очистка кеша + очистка сухостоя) ---
# Удаляем функцию clean_maintenance и все её вызовы

# --- Основная логика ---
def main():
    global stop_script
    log("===> Начало main()")
    update_tray_status('green')
    # --- Посадка низ ---
    lclick(50, 404)
    waitms(40)
    ldown(290, 276)
    wait(0.4)
    lup(290, 276)
    wait(0.4)
    move(1142, 612)
    wait(1.5)
    waitms(80)
    ldown(745, 405)
    waitms(80)
    lup(745, 405)
    waitms(160)
    for var in range(175, 1850, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 276 + rnd(-3, 1), 36)
    lclick(1850, 350)
    wait(3.2)
    log("[main] Посадка низ завершена")
    wait(8)
    # --- Посадка верх ---
    ldown(580, 132)
    wait(0.4)
    lup(580, 132)
    wait(0.4)
    move(1142, 612)
    wait(1.5)
    waitms(80)
    ldown(745, 405)
    waitms(80)
    lup(745, 405)
    waitms(160)
    for var in range(517, 1410, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 132 + rnd(-3, 1), 36)
    lclick(1850, 350)
    log("[main] Посадка верх завершена")
    wait(10)  # Пауза перед сбором низа
    # --- Сбор низ (единый проход, включая крестик) ---
    last_lutic_check = time.time()
    last_close_check = time.time()
    for var in range(147, 1825, STEP_BOTTOM):  # было 140, теперь 143
        if stop_script: return
        # Если в области крестика — кликаем реже
        if 1260 <= var <= 1320:
            step = STEP_CROSS
        else:
            step = STEP_BOTTOM
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), CLICK_DELAY)
        # lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), CLICK_DELAY)  # УБРАНО: клик по крестику
        var += step - STEP_BOTTOM  # увеличиваем var дополнительно, если шаг увеличен
        # --- Дополнительный сбор лютиков по шаблону каждые 10 сек ---
        if time.time() - last_lutic_check > 10:
            for lutic_template in ["lutic.png", "lutic2.png"]:
                screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name=lutic_template)
            last_lutic_check = time.time()
        # --- Поиск и клик по крестику через шаблон каждые 5 сек ---
        if time.time() - last_close_check > 5:
            screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name="close.png")
            last_close_check = time.time()
    log("[main] Сбор низ завершён")
    wait(10)  # Пауза между сбором низа и сбором верха
    # --- Сбор верх ---
    last_lutic_check = time.time()
    last_close_check = time.time()
    for var in range(480, 1410, STEP_TOP):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 49 + rnd(-2, 2), 9)
        # lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 7)  # УБРАНО: клик по крестику
        # --- Дополнительный сбор лютиков по шаблону каждые 10 сек ---
        if time.time() - last_lutic_check > 10:
            for lutic_template in ["lutic.png", "lutic2.png"]:
                screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name=lutic_template)
            last_lutic_check = time.time()
        # --- Поиск и клик по крестику через шаблон каждые 5 сек ---
        if time.time() - last_close_check > 5:
            screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name="close.png")
            last_close_check = time.time()
    log("[main] Сбор верх завершён")
    wait(random.uniform(-1.2, 1.2))
    update_tray_status('yellow')
    log("<=== Конец main()")

def main_loop():
    global stop_script, script_running, tray_icon, cycle_counter
    update_tray_status('yellow')
    script_running = True
    while not stop_script:
        log("===> Новый цикл main()")
        cycle_counter += 1
        log(f"Текущий цикл: {cycle_counter}")
        
        try:
            main()
        except Exception as e:
            log(f"ОШИБКА В main(): {e}")
        
        # Временно отключено:
        # if cycle_counter % CACHE_CLEAN_INTERVAL == 0:
        #     log(f"Достигнут {cycle_counter}-й цикл, выполняем очистку кеша и сухостоя")
        #     clean_game_cache()
        #     if stop_script:
        #         break
        #     clean_withered_plants()
        #     if stop_script:
        #         break
        
        log("<=== main() завершён, пауза перед следующим циклом")
        if stop_script:
            break
        update_tray_status('yellow')
        log('Пауза 30 секунд перед следующим циклом...')
        # --- Чистим мусор по шаблонам bad_lutic.png и bad_lutic_up.png ---
        for template_name in ["bad_lutic.png", "bad_lutic_up.png"]:
            screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name=template_name)
        for i in range(60, 0, -1):
            if stop_script:
                break
            log(f'До следующего запуска: {i} сек.')
            time.sleep(1)
        update_tray_status('yellow')
    script_running = False
    update_tray_status('red')

def collect_rows_only():
    global stop_script
    log("===> Начало collect_rows_only() (только сбор)")
    update_tray_status('green')
    # --- Сбор низ (единый проход, включая крестик) ---
    for var in range(147, 1825, STEP_BOTTOM):  # было 140, теперь 143
        if stop_script: return
        if 1260 <= var <= 1320:
            step = STEP_CROSS
        else:
            step = STEP_BOTTOM
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), CLICK_DELAY)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), CLICK_DELAY)
        var += step - STEP_BOTTOM
    log("[collect_rows_only] Сбор низ завершён")
    # --- Сбор верх ---
    for var in range(480, 1410, STEP_TOP):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 49 + rnd(-2, 2), 9)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 7)
    log("[collect_rows_only] Сбор верх завершён")
    wait(rnd(-1.2, 1.2))
    update_tray_status('yellow')
    log("<=== Конец collect_rows_only() (только сбор)")

def collect_rows_loop():
    global stop_script, script_running, tray_icon, cycle_counter
    update_tray_status('yellow')
    script_running = True
    while not stop_script:
        log("===> Новый цикл collect_rows_only()")
        cycle_counter += 1
        log(f"Текущий цикл: {cycle_counter}")
        
        try:
            collect_rows_only()
        except Exception as e:
            log(f"ОШИБКА В collect_rows_only(): {e}")
        
        # Временно отключено:
        # if cycle_counter % CACHE_CLEAN_INTERVAL == 0:
        #     log(f"Достигнут {cycle_counter}-й цикл, выполняем очистку кеша и сухостоя")
        #     clean_game_cache()
        #     if stop_script:
        #         break
        #     clean_withered_plants()
        #     if stop_script:
        #         break
        
        log("<=== collect_rows_only() завершён, пауза перед следующим циклом")
        if stop_script:
            break
        update_tray_status('yellow')
        log('Пауза 30 секунд перед следующим циклом...')
        # --- Чистим мусор по шаблонам bad_lutic.png и bad_lutic_up.png ---
        for template_name in ["bad_lutic.png", "bad_lutic_up.png"]:
            screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name=template_name)
        for i in range(30, 0, -1):
            if stop_script:
                break
            log(f'До следующего запуска: {i} сек.')
            time.sleep(1)
        update_tray_status('yellow')
    script_running = False
    update_tray_status('red')

def check_internet_speed_and_alert():
    if speedtest is None:
        log('speedtest-cli не установлен! Пропускаю проверку скорости интернета.')
        return
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000  # Мбит/с
        upload = st.upload() / 1_000_000      # Мбит/с
        ping = st.results.ping
        log(f"Скорость загрузки: {download:.2f} Мбит/с, отдачи: {upload:.2f} Мбит/с, пинг: {ping:.2f} мс")
        # Пороговые значения (можно скорректировать)
        min_download = 60  # Мбит/с
        min_upload = 20    # Мбит/с
        max_ping = 100     # мс
        if download < min_download or upload < min_upload or ping > max_ping:
            msg = (f"ВНИМАНИЕ! Плохое интернет-соединение:\n"
                   f"Скорость загрузки: {download:.2f} Мбит/с\n"
                   f"Скорость отдачи: {upload:.2f} Мбит/с\n"
                   f"Пинг: {ping:.2f} мс\n"
                   f"Рекомендуется проверить подключение!")
            log(msg)
            try:
                if tk and messagebox:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showwarning('Плохое интернет-соединение', msg)
                    root.destroy()
                else:
                    log('tkinter не установлен! Не могу показать окно предупреждения.')
            except Exception as e:
                log(f"Ошибка показа алерта: {e}")
    except Exception as e:
        log(f"Ошибка проверки скорости интернета: {e}")

def print_info():
    # Цвета ANSI
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    print(f"{BOLD}{CYAN}Добро пожаловать в помощник Valya!{RESET}")
    print(f"{BOLD}Назначение:{RESET} автоматизация действий в игре (посадка, сбор, обслуживание).\n")
    print(f"{BOLD}Горячие клавиши:{RESET}")
    print(f"  {GREEN}Numpad 1{RESET}  — ▶️  Запуск полного цикла (посадка + сбор)")
    print(f"  {RED}Numpad 2{RESET}  — ⏹️  Остановка скрипта")
    print(f"  {YELLOW}Numpad 3{RESET}  — 🔄  Запуск только сбора урожая")
    print(f"  {CYAN}Numpad 4{RESET}  — 🧹  Очистка кеша и сухостоя (обслуживание)\n")
    print(f"{BOLD}Статусы трея:{RESET}")
    print(f"  {GREEN}🟢  Зеленый{RESET} — скрипт работает")
    print(f"  {YELLOW}🟡  Желтый{RESET} — пауза/обслуживание")
    print(f"  {RED}🔴  Красный{RESET} — скрипт остановлен\n")
    print(f"{BOLD}Логи:{RESET} пишутся в файл logs.txt")
    print(f"{BOLD}Внимание:{RESET} для работы нужны разрешения на управление мышью и клавиатурой!")
    print(f"{CYAN}Удачной автоматизации! 🚀{RESET}\n")

# --- ВРЕМЕННО ОТКЛЮЧЕНО: система обновления ---
# def download_update_exe():
#     """Скачивает update.exe из последнего релиза на GitHub, если его нет."""
#     url = "https://github.com/SkvorikovCode/AutoFarm-Domovyata/releases/latest/download/update.exe"
#     try:
#         r = requests.get(url, stream=True, timeout=30)
#         r.raise_for_status()
#         with open('update.exe', 'wb') as f:
#             for chunk in r.iter_content(1024 * 1024):
#                 f.write(chunk)
#         print('update.exe успешно скачан из GitHub Releases.')
#         log('update.exe успешно скачан из GitHub Releases.')
#         return True
#     except Exception as e:
#         print(f'Ошибка скачивания update.exe: {e}')
#         log(f'Ошибка скачивания update.exe: {e}')
#         return False

# def run_updater():
#     updater_path = os.path.join(os.path.dirname(sys.executable), 'update.exe')
#     if not os.path.exists(updater_path):
#         print('update.exe не найден! Пробую скачать из GitHub Releases...')
#         if not download_update_exe():
#             print('Автообновление не работает: не удалось скачать update.exe.')
#             return
#     try:
#         subprocess.Popen([updater_path], close_fds=True)
#     except Exception as e:
#         print(f'Ошибка запуска update.exe: {e}')

# run_updater()  # <--- Временно отключено для отладки на MacOS

def screenshot_and_click_template(templates_dir="templates", threshold=0.85, template_name=None):
    """
    Делает скриншот экрана, ищет шаблон(ы) из templates_dir.
    Если указан template_name — ищет только этот шаблон.
    Кликает по центру первого найденного совпадения.
    threshold — порог совпадения (0..1)
    """
    if pyautogui is None or cv2 is None or Image is None or np is None:
        print("pyautogui, cv2, numpy или Pillow не установлены!")
        return False
    # Скриншот экрана
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.convert('RGB')
    screen_np = np.array(screenshot)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
    # Определяем список шаблонов
    if template_name:
        template_files = [os.path.join(templates_dir, template_name)]
    else:
        template_files = glob.glob(os.path.join(templates_dir, "*.png"))
    for template_path in template_files:
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            continue
        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        print(f"Пробую {template_path}: max_val={max_val}")
        if max_val >= threshold:
            h, w = template.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            print(f"Шаблон найден: {template_path}, совпадение: {max_val:.2f}, координаты: ({center_x}, {center_y})")
            lclick(center_x, center_y)
            return True
    print("Совпадений с шаблонами не найдено.")
    return False

if __name__ == "__main__":
    print_info()
    check_internet_speed_and_alert()
    log("Для запуска нажмите Numpad 1, для остановки — Numpad 2, для запуска только сбора — Numpad 3, для очистки кеша и сухостоя — Numpad 4.")
    while True:
        time.sleep(0.1)
