@echo off
REM -------------------------------
REM Script para ejecutar Backend en consola
REM -------------------------------

REM Ir al directorio del backend
cd /d "%~dp0Backend"

REM Activar el virtualenv
call venv\Scripts\activate.bat

REM Ejecutar main.py en modo consola
python main.py

REM Mantener la consola abierta al terminar
pause
