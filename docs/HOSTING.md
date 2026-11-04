# HOSTING — Preparação para hospedagem

Para jogar no próprio computador **nada disto é necessário**: use `iniciar.cmd`.
Este guia é para rodar o jogo num servidor (ou num computador da casa acessado por outros aparelhos).

## Estado atual (leia antes)
- O programa ainda **não tem contas de usuário**: existe um único "usuário local". Quem acessar o endereço
  pode jogar, criar e excluir campanhas (excluir pede o título exato; o modo administrador pede senha).
  **Não exponha na internet aberta.** Use só numa rede privada, ou atrás de um proxy com login
  (ex.: autenticação básica no Nginx/Caddy). Contas de usuário estão previstas (SPEC 18), não implementadas.
- O `Dockerfile` foi escrito na Etapa 7.5, mas **não foi testado** (o Docker não está instalado neste
  computador). O modo que ele usa, backend servindo o frontend compilado, foi testado sem Docker.

## Como funciona em produção (D-051)
- Um processo só: o backend serve a API (`/api/...`) e o frontend compilado (`FRONTEND_DIST`).
- Servidor `gunicorn` com **1 processo e várias linhas de execução**: as sessões do modo administrador e as
  travas do resumo ficam na memória do processo, e o SQLite aceita um escritor por vez. Não aumente `--workers`.
- `APP_ENV=production` exige `APP_SECRET_KEY` e `ADMIN_PASSWORD` próprios (o programa recusa os de exemplo).
- As jogadas usam SSE (texto aos poucos); o backend já envia `X-Accel-Buffering: no` e `Cache-Control: no-cache`.
  Num proxy, desligue o buffer dessa rota e aumente o tempo limite (uma jogada com IA local pode levar minutos).

## Com Docker (não testado)
```
docker build -t ai-rpg-engine .
docker run -d --name rpg -p 5000:5000 -v rpg-dados:/data --env-file .env \
  --add-host=host.docker.internal:host-gateway ai-rpg-engine
```
- `-v rpg-dados:/data`: banco, cópias e imagens ficam num volume (sobrevivem à troca da imagem).
- O Ollama roda fora do contêiner; o padrão é `OLLAMA_BASE_URL=http://host.docker.internal:11434`.
  No servidor, o Ollama precisa aceitar conexões do contêiner (`OLLAMA_HOST=0.0.0.0`) — só em rede privada.
- No `.env` do servidor: `APP_SECRET_KEY` e `ADMIN_PASSWORD` fortes, `AI_MODEL`. Não defina `DATA_DIR`,
  `DATABASE_URL` nem `FRONTEND_DIST` (a imagem já define).

## Sem Docker (Linux)
```
cd frontend && npm ci && npm run build
cd ../backend && python -m venv .venv && .venv/bin/pip install -e ".[hosting]"
APP_ENV=production FRONTEND_DIST=frontend/dist .venv/bin/gunicorn --workers 1 --threads 8 \
  --timeout 120 --bind 0.0.0.0:5000 "app:create_app()"
```
`FRONTEND_DIST` relativo é lido a partir da raiz do projeto. O banco é migrado sozinho ao iniciar.

## Testar o modo produção no Windows (sem gunicorn, que não roda no Windows)
```
$env:Path = "F:\Tools\node-v24.22.2-win-x64;" + $env:Path
cd frontend; npm run build; cd ..\backend
$env:APP_ENV="production"; $env:FRONTEND_DIST="frontend/dist"
$env:APP_SECRET_KEY="um-texto-longo-qualquer"; $env:ADMIN_PASSWORD="uma-senha"
.\.venv\Scripts\flask.exe --app app run --port 5001
```
Abra http://127.0.0.1:5001: o jogo inteiro numa porta só. (Isto usa o banco real em `data\`.)

## Backups no servidor
Os snapshots ficam em `/data/backups/<campanha>/` (automáticos a cada `AUTO_SNAPSHOT_EVERY` jogadas).
Para cópia completa, pare o contêiner e copie o volume, ou exporte cada campanha pela interface.
