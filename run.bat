@echo off
echo ========================================
echo     SMART HIRE - LANCEMENT COMPLET
echo ========================================
echo.

start "" cmd /k "npm run dev"

timeout /t 10

start "" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python app.py"

echo.
echo Frontend : http://localhost:5173
echo Backend  : http://localhost:5000
pause