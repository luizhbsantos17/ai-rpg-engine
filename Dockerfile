# Imagem opcional para hospedagem (D-009, D-051). Para jogar em casa NÃO é preciso: use iniciar.cmd.
# Guia completo: docs/HOSTING.md
#   docker build -t ai-rpg-engine .
#   docker run -p 5000:5000 -v rpg-dados:/data --env-file .env ai-rpg-engine

# Etapa 1: compila o frontend (só o resultado vai para a imagem final)
FROM node:24-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Etapa 2: backend, que também serve o frontend compilado
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATA_DIR=/data \
    FRONTEND_DIST=/app/frontend/dist \
    OLLAMA_BASE_URL=http://host.docker.internal:11434
WORKDIR /app/backend
COPY backend/pyproject.toml backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
# Editável (-e): o código fica em /app/backend, onde o programa procura alembic.ini e as migrações.
RUN pip install --no-cache-dir -e ".[hosting]"
COPY --from=frontend /src/frontend/dist /app/frontend/dist

RUN useradd --create-home jogo && mkdir -p /data && chown jogo /data
USER jogo
VOLUME /data
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=4)"

# 1 processo com várias linhas de execução: sessões do modo administrador e travas do resumo ficam na
# memória do processo, e o SQLite aceita um escritor por vez (D-051).
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:create_app()"]
