@echo off
rem ============================================================
rem  AI RPG Engine - iniciar o jogo
rem  Abre o Ollama (IA local, porta 11434, se instalado em OLLAMA_DIR),
rem  o backend (Flask, porta 5000) e o frontend (Vite, porta 5173) em janelas
rem  separadas e abre o navegador. Para encerrar, feche as janelas.
rem ============================================================
setlocal
set "ROOT=%~dp0"
set "NODE_DIR=F:\Tools\node-v24.22.2-win-x64"
if exist "%NODE_DIR%\node.exe" set "PATH=%NODE_DIR%;%PATH%"
rem Temporarios e caches no projeto (o disco C: esta quase cheio).
set "npm_config_cache=%ROOT%.cache\npm"
if not exist "%ROOT%.tmp" mkdir "%ROOT%.tmp"
set "TEMP=%ROOT%.tmp"
set "TMP=%ROOT%.tmp"
rem Ollama portatil e pasta dos modelos (fora do disco C:).
set "OLLAMA_DIR=F:\Tools\ollama"
set "OLLAMA_MODELS=F:\Tools\ollama-models"

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

rem Inicia o Ollama so se ele existir e ainda nao estiver rodando.
netstat -ano | findstr /R /C:":11434 .*LISTENING" >nul
if errorlevel 1 (
  if exist "%OLLAMA_DIR%\ollama.exe" (
    start "AI RPG Engine - Ollama (nao feche durante o jogo)" /D "%OLLAMA_DIR%" cmd /k "ollama.exe serve"
  ) else (
    echo [AVISO] Ollama nao encontrado em %OLLAMA_DIR%. O jogo abre, mas a IA nao vai responder.
  )
)

start "AI RPG Engine - backend (nao feche durante o jogo)" /D "%ROOT%backend" cmd /k ".venv\Scripts\flask.exe --app app run"
start "AI RPG Engine - frontend (nao feche durante o jogo)" /D "%ROOT%frontend" cmd /k "npm run dev"

echo Iniciando... o navegador vai abrir em alguns segundos.
rem Espera ~5 segundos (ping funciona mesmo sem teclado, ao contrario de "timeout").
ping -n 6 127.0.0.1 >nul
if not "%~1"=="--sem-navegador" start "" "http://127.0.0.1:5173/"
exit /b 0
