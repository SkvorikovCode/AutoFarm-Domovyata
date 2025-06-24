import pyautogui
import time
import random
from pynput import keyboard
import threading
import sys
import pystray
from PIL import Image, ImageDraw

sys.stdout = open('valya_log.txt', 'w', encoding='utf-8')
sys.stderr = sys.stdout

# --- Настройки ---
# START_KEY = keyboard.KeyCode.from_vk(97)  # Numpad 1
# STOP_KEY = keyboard.KeyCode.from_vk(98)   # Numpad 2

# --- Настройки шагов ---
STEP_BOTTOM_BEFORE = 6  # до крестика (рекомендуется 6-8, можно менять)
STEP_BOTTOM_AFTER = 6   # после крестика
STEP_TOP = 3            # верх (оставим как было, если нужно - меняй)

# --- Вспомогательные функции ---
def rnd(a, b):
    return random.randint(a, b)

def waitms(ms):
    time.sleep(ms / 1000.0)

def wait(s):
    time.sleep(s)

def lclick(x, y, ms_delay=0):
    pyautogui.click(x, y, button='left')
    if ms_delay:
        waitms(ms_delay)

def ldown(x, y):
    pyautogui.mouseDown(x, y, button='left')

def lup(x, y):
    pyautogui.mouseUp(x, y, button='left')

def move(x, y):
    pyautogui.moveTo(x, y)

def log(*args, **kwargs):
    print(*args, **kwargs)
    try:
        if sys.__stdout__ is not None:
            sys.__stdout__.write(' '.join(str(a) for a in args) + '\n')
            sys.__stdout__.flush()
    except Exception:
        pass

# --- Глобальные переменные ---
stop_script = False
script_running = False
script_thread = None

TRAY_STATUS = 'red'  # red (остановлен), green (работает), yellow (пауза)
tray_icon = None
tray_thread = None

def create_icon(color):
    # Создаём иконку-кружок нужного цвета
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

def tray_run():
    global tray_icon, TRAY_STATUS
    tray_icon = pystray.Icon('valya', create_icon(TRAY_STATUS), 'Valya')
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

# --- Остановка и запуск ---
def on_press(key):
    global stop_script, script_running, script_thread
    vk_code = getattr(key, 'vk', None)
    char = getattr(key, 'char', None)
    name = getattr(key, 'name', None)
    log(f"Нажата клавиша: {key}, vk: {vk_code}, char: {char}, name: {name}")

    # Проверяем все возможные варианты для Num1/Num2 и обычных 1/2
    if (vk_code == 97 or char == '1' or name == 'num1') and not script_running:
        log("Скрипт запущен (Numpad 1, '1', или 'num1')")
        stop_script = False
        script_running = True
        update_tray_status('green')
        script_thread = threading.Thread(target=main_loop)
        script_thread.start()
    elif (vk_code == 98 or char == '2' or name == 'num2') and script_running:
        log("Скрипт остановлен (Numpad 2, '2', или 'num2')")
        stop_script = True
        script_running = False
        update_tray_status('red')

listener = keyboard.Listener(on_press=on_press)
listener.start()

# --- Основная логика ---
def main():
    global stop_script, script_running
    update_tray_status('green')
    # --- Посадка низ ---
    lclick(50, 404)
    waitms(40)

    ldown(290, 276)
    wait(0.4)
    lup(290, 276)
    wait(0.4)

    move(1142, 612)
    waitms(80)
    ldown(745, 405)
    waitms(80)
    lup(745, 405)
    waitms(160)

    for var in range(175, 1850, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 276 + rnd(-3, 1), 36)

    lclick(1850, 350)
    wait(3.2)  # Пауза перед сбором снизу

    wait(8)  # Пауза между посадкой низа и посадкой верха

    # --- Посадка верх ---
    ldown(580, 132)
    wait(0.4)
    lup(580, 132)
    wait(0.4)

    move(1142, 612)
    waitms(80)
    ldown(745, 405)
    waitms(80)
    lup(745, 405)
    waitms(160)

    for var in range(517, 1410, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 132 + rnd(-3, 1), 36)

    lclick(1850, 350)
    # wait(1.6)  # Пауза перед сбором сверху

    # --- Сбор низ до крестика ---
    for var in range(150, 1145, STEP_BOTTOM_BEFORE):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), 9)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 7)

    # --- Сбор низ после крестика ---
    for var in range(1260, 1825, STEP_BOTTOM_AFTER):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), 9)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 7)

    # --- Сбор верх ---
    for var in range(480, 1410, STEP_TOP):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 49 + rnd(-2, 2), 9)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 7)

    wait(rnd(-1.2, 1.2))
    script_running = False
    update_tray_status('yellow')

def main_loop():
    global stop_script, script_running
    update_tray_status('yellow')
    while not stop_script:
        main()
        if stop_script:
            break
        update_tray_status('yellow')
        log('Пауза 30 секунд перед следующим циклом...')
        for i in range(30, 0, -1):
            if stop_script:
                break
            log(f'До следующего запуска: {i} сек.')
            time.sleep(1)
    script_running = False
    update_tray_status('red')

if __name__ == "__main__":
    log("Для запуска нажмите Numpad 1, для остановки — Numpad 2.")
    while True:
        time.sleep(0.1)
