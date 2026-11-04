@echo off
rem ============================================================
rem  AI RPG Engine - iniciar o jogo
rem  Abre o backend (Flask, porta 5000) e o frontend (Vite, porta 5173)
rem  em duas janelas e abre o navegador. Para encerrar, feche as duas janelas.
rem ============================================================
setlocal
set "ROOT=%~dp0"
set "NODE_DIR=F:\Tools\node-v24.22.2-win-x64"
if exist "%NODE_DIR%\node.exe" set "PATH=%NODE_DIR%;%PATH%"
set "npm_config_cache=F:\Tools\npm-cache"

if not exist "%ROOT%backend\.venv\Scripts\flask.exe" (
  echo [ERRO] Backend nao instalado. Rode primeiro: instalar.cmd
  pause
  exit /b 1
)
if not exist "%ROOT%frontend\node_modules" (
  echo [ERRO] Frontend nao instalado. Rode primeiro: instalar.cmd
  pause
  exit /b 1
)

start "AI RPG Engine - backend (nao feche durante o jogo)" /D "%ROOT%backend" cmd /k ".venv\Scripts\flask.exe --app app run"
start "AI RPG Engine - frontend (nao feche durante o jogo)" /D "%ROOT%frontend" cmd /k "npm run dev"

echo Iniciando... o navegador vai abrir em alguns segundos.
rem Espera ~5 segundos (ping funciona mesmo sem teclado, ao contrario de "timeout").
ping -n 6 127.0.0.1 >nul
if not "%~1"=="--sem-navegador" start "" "http://127.0.0.1:5173/"
exit /b 0
