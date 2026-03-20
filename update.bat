@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo [%date% %time%] Запуск парсера...
python main.py

if %errorlevel% neq 0 (
    echo [%date% %time%] ОШИБКА: main.py завершился с ошибкой
    exit /b 1
)

echo [%date% %time%] Пушим на GitHub...
git add verified/
git commit -m "update proxies %date% %time%"
git push

echo [%date% %time%] Готово!
