@echo off
title NOVA PRO LAUNCHER
color 0B

REM ============================================
REM            NOVA PRO LAUNCHER v2
REM  Auto-restart, logging, crash recovery
REM ============================================

set BACKEND_PATH=D:\NovaProject\nova-agent
set FRONTEND_PATH=D:\NovaProject\nova-agent\ui
set BACKEND_LOG=%BACKEND_PATH%\backend.log
set FRONTEND_LOG=%FRONTEND_PATH%\frontend.log

echo ============================================
echo        NOVA PRO LAUNCHER STARTING...
echo ============================================
echo.

REM ---------------------------------------------------
REM   START BACKEND WATCHER (auto-restart on crash)
REM ---------------------------------------------------
echo [+] Starting Backend Supervisor...

start "NOVA Backend" cmd /k ^
"cd /d %BACKEND_PATH% && ^
.\venv\Scripts\activate && ^
:backend_loop ^
echo [Backend] Starting... >> backend.log && ^
uvicorn app:app --host 127.0.0.1 --port 9001 --reload >> backend.log 2>&1 && ^
echo [Backend] CRASHED! Restarting in 3 sec... >> backend.log && ^
timeout /t 3 >nul && ^
goto backend_loop"

REM wait for backend to start
timeout /t 3 >nul

REM ---------------------------------------------------
REM   START FRONTEND WATCHER (auto-restart on crash)
REM ---------------------------------------------------
echo [+] Starting Frontend Supervisor...

start "NOVA UI" cmd /k ^
"cd /d %FRONTEND_PATH% && ^
:ui_loop ^
echo [UI] Starting... >> frontend.log && ^
npm run dev >> frontend.log 2>&1 && ^
echo [UI] CRASHED! Restarting in 3 sec... >> frontend.log && ^
timeout /t 3 >nul && ^
goto ui_loop"

REM wait for frontend
timeout /t 4 >nul

REM ---------------------------------------------------
REM   OPEN UI IN BROWSER
REM ---------------------------------------------------
echo [+] Opening Nova UI...
start http://localhost:5173

echo.
echo ============================================
echo           NOVA IS NOW RUNNING
echo --------------------------------------------
echo - Backend logs: %BACKEND_LOG%
echo - Frontend logs: %FRONTEND_LOG%
echo - Auto-restart enabled for both
echo ============================================
echo.
echo [Press CTRL + C to stop Nova completely]
echo.

pause
exit