# Скрипт сборки Valya для Windows
# Проверка платформы
if (-not $IsWindows -and -not $env:OS -like "*Windows*") {
    Write-Host "ВНИМАНИЕ: Этот скрипт предназначен для запуска только на Windows!" -ForegroundColor Red
    Write-Host "Обнаружена другая платформа. Сборка может работать некорректно." -ForegroundColor Yellow
    $confirmation = Read-Host "Хотите продолжить? (y/n)"
    if ($confirmation -ne 'y') {
        exit
    }
}

# Очистка предыдущей сборки
Write-Host "Очистка предыдущих сборок..." -ForegroundColor Cyan
if (Test-Path -Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
}
if (Test-Path -Path "build") {
    Remove-Item -Path "build" -Recurse -Force
}
if (Test-Path -Path "*.spec") {
    Remove-Item -Path "*.spec" -Force
}

# Установка pip (если не установлен)
Write-Host "Проверка наличия pip..." -ForegroundColor Cyan
if (-not (Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "pip не найден, пробую установить..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
    if (-not $?) {
        Write-Host "Ошибка установки pip. Пожалуйста, установите pip вручную." -ForegroundColor Red
        exit 1
    }
}

# Проверка и установка необходимых зависимостей
Write-Host "Установка зависимостей из requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

# Проверка критических зависимостей, упомянутых в ошибках линтера
Write-Host "Проверка критических зависимостей..." -ForegroundColor Cyan
$critical_packages = @("pystray", "pillow", "speedtest-cli")
foreach ($package in $critical_packages) {
    Write-Host "Проверка пакета $package..." -ForegroundColor Gray
    pip install $package
}

# Установка pyinstaller
Write-Host "Установка pyinstaller..." -ForegroundColor Cyan
pip install pyinstaller

# Сборка main.py в exe с иконкой mouse.ico
Write-Host "Начинаю сборку исполняемого файла..." -ForegroundColor Green
pyinstaller --onefile --noconsole --icon=mouse.ico main.py

# Проверка успешности сборки
if (-not $?) {
    Write-Host "Ошибка при сборке! Проверьте вывод выше." -ForegroundColor Red
    exit 1
}

if (Test-Path -Path "dist\main.exe") {
    # Копирование README или другой документации, если существует
    if (Test-Path -Path "README.md") {
        Copy-Item -Path "README.md" -Destination "dist\"
    }
    
    # Создание версии без консоли и с консолью
    Write-Host "Сборка версии с консолью (для отладки)..." -ForegroundColor Cyan
    pyinstaller --onefile --icon=mouse.ico main.py -n main_console.exe
    
    Write-Host "`nГотово! Файлы находятся в папке dist:" -ForegroundColor Green
    Write-Host "- dist\main.exe - основной файл (без консоли)" -ForegroundColor White
    if (Test-Path -Path "dist\main_console.exe") {
        Write-Host "- dist\main_console.exe - версия с консолью (для отладки)" -ForegroundColor White
    }
    
    # Открытие папки с результатами
    explorer.exe "dist"
} else {
    Write-Host "Файл main.exe не найден в папке dist. Что-то пошло не так!" -ForegroundColor Red
}