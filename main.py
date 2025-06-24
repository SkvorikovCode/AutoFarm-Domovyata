import pyautogui
import time
import random
from pynput import keyboard

# --- Настройки ---
STOP_KEY = keyboard.Key.esc  # Клавиша для остановки скрипта

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

# --- Остановка по ESC ---
stop_script = False
def on_press(key):
    global stop_script
    if key == STOP_KEY:
        stop_script = True
        print("Скрипт остановлен пользователем.")

listener = keyboard.Listener(on_press=on_press)
listener.start()

# --- Основная логика ---

def main():
    global stop_script

    # --- Посадка низ ---
    lclick(50, 404)
    waitms(100)

    ldown(290, 276)
    wait(1)
    lup(290, 276)
    wait(1)

    move(1142, 612)
    waitms(200)
    ldown(745, 405)
    waitms(200)
    lup(745, 405)
    waitms(400)

    for var in range(175, 1850, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 276 + rnd(-3, 1), 90)

    lclick(1850, 350)
    wait(8)

    # --- Посадка верх ---
    ldown(580, 132)
    wait(1)
    lup(580, 132)
    wait(1)

    move(1142, 612)
    waitms(200)
    ldown(745, 405)
    waitms(200)
    lup(745, 405)
    waitms(400)

    for var in range(517, 1410, 2):
        if stop_script: return
        lclick(var + rnd(-2, 0), 132 + rnd(-3, 1), 90)

    lclick(1850, 350)
    wait(8)

    # --- Сбор низ до крестика ---
    for var in range(150, 1145, 4):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), 67)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 45)

    # --- Сбор низ после крестика ---
    for var in range(1260, 1825, 4):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 155 + rnd(-1, 1), 67)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 45)

    # --- Сбор верх ---
    for var in range(480, 1410, 3):
        if stop_script: return
        for offset in range(0, 7, 2):
            lclick(var + offset + rnd(-2, 1), 49 + rnd(-2, 2), 40)
        lclick(1265 + rnd(-3, 3), 160 + rnd(-3, 3), 33)

    wait(rnd(-3, 3))

if __name__ == "__main__":
    print("Запуск скрипта. Для остановки нажмите ESC.")
    main()
    print("Скрипт завершён.")
