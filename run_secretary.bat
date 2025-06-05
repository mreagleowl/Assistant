@echo off
chcp 65001

REM Переходим в папку со скриптом
cd /d %~dp0

REM ----------------------------------------------------------------
REM 1) Создаём виртуальное окружение, если его нет
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

REM ----------------------------------------------------------------
REM 2) Используем python прямо из .venv для любых операций с pip
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install -r requirements.txt

REM ----------------------------------------------------------------
REM 3) Запускаем приложение через тот же python внутри .venv
.venv\Scripts\python.exe -m ui.main

pause
