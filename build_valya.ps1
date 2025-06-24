# Установка pip (если не установлен)
if (-not (Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "pip не найден, пробую установить..."
    python -m ensurepip --upgrade
}

# Установка зависимостей
pip install -r requirements.txt

# Установка pyinstaller
pip install pyinstaller

# Сборка main.py в exe
pyinstaller --onefile main.py

Write-Host "\nГотово! Файл main.exe находится в папке dist." 