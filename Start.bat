@echo off
start cmd /k "npm run dev"
timeout /t 10 /nobreak >nul
start cmd /k "cd backend && python main.py"

