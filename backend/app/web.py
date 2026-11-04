"""Serve o frontend já compilado (`npm run build`) pelo próprio backend, para hospedagem com um só processo.

Desligado por padrão: em casa, o `iniciar.cmd` usa o servidor do Vite. Ligado com `FRONTEND_DIST`.
Qualquer caminho fora de /api que não seja um arquivo devolve o `index.html` (as rotas são do Vue Router).
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, send_from_directory

INDEX = "index.html"


def register_frontend(flask_app: Flask, dist: Path, api_prefix: str) -> None:
    api = api_prefix.strip("/")

    @flask_app.get("/", defaults={"path": ""})
    @flask_app.get("/<path:path>")
    def frontend(path: str):
        if path == api or path.startswith(api + "/"):
            abort(404)  # rota de API inexistente: responde o erro em JSON da API, não a página
        if path and (dist / path).is_file():
            # send_from_directory recusa caminhos que saem da pasta (ex.: "../.env")
            return send_from_directory(dist, path, max_age=_cache_seconds(path))
        return send_from_directory(dist, INDEX, max_age=0)


def _cache_seconds(path: str) -> int:
    """Arquivos de `assets/` têm o conteúdo no nome (o Vite muda o nome a cada build): podem ficar em cache."""
    return 31_536_000 if path.startswith("assets/") else 0
