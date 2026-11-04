@echo off
rem ============================================================
rem  AI RPG Engine - instalacao (rode uma vez, ou apos atualizar)
rem  Cria o ambiente do backend e instala as dependencias.
rem ============================================================
setlocal
set "ROOT=%~dp0"
rem Node.js portatil (fora do disco C:). Se nao existir, usa o Node do sistema.
set "NODE_DIR=F:\Tools\node-v24.22.2-win-x64"
if exist "%NODE_DIR%\node.exe" set "PATH=%NODE_DIR%;%PATH%"
set "npm_config_cache=F:\Tools\npm-cache"
set "PIP_NO_CACHE_DIR=1"

where py >nul 2>nul || (echo [ERRO] Python nao encontrado. Instale o Python 3.12 ou mais novo. & goto :fim_erro)
where node >nul 2>nul || (echo [ERRO] Node.js nao encontrado. & goto :fim_erro)

echo.
echo [1/3] Backend: ambiente virtual e bibliotecas...
cd /d "%ROOT%backend"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto :fim_erro
)
.venv\Scripts\python.exe -m pip install --quiet -e ".[dev]" || goto :fim_erro

echo [2/3] Frontend: bibliotecas...
cd /d "%ROOT%frontend"
call npm install --no-fund --no-audit || goto :fim_erro

echo [3/3] Configuracao...
if not exist "%ROOT%.env" (
  copy "%ROOT%.env.example" "%ROOT%.env" >nul
  echo Arquivo .env criado a partir do .env.example.
) else (
  echo Arquivo .env ja existe; nada alterado.
)

echo.
echo Instalacao concluida. Para jogar, de dois cliques em iniciar.cmd
if not "%~1"=="--sem-pausa" pause
exit /b 0

:fim_erro
echo.
echo [ERRO] A instalacao falhou. Veja a mensagem acima.
if not "%~1"=="--sem-pausa" pause
exit /b 1
