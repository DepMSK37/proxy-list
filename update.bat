@echo off
cd /d "C:\Users\BYBIT\OneDrive\Desktop\telegram-proxy-collector-main2"
"C:\Python314\python.exe" main.py
if %errorlevel% neq 0 exit /b 1
"C:\Program Files\Git\cmd\git.exe" add verified/
"C:\Program Files\Git\cmd\git.exe" commit -m "update"
"C:\Program Files\Git\cmd\git.exe" push