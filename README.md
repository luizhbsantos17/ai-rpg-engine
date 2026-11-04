# AI RPG Engine

Plataforma de RPG narrativo com inteligência artificial: a IA cria mundos, narra e interpreta
personagens, enquanto um motor de jogo valida as regras e guarda tudo de forma persistente.

> **Status: Etapa 1 (Fundação).** Já funciona: criar campanhas, jogar com a IA narrando em tempo real,
> fechar o programa e continuar exatamente de onde parou. Ainda não há motor de regras (atributos,
> dados, habilidades): isso é a Etapa 2. Detalhes em [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Funcionalidades planejadas
Campanhas independentes e geradas aleatoriamente · sistemas de regras próprios por universo ·
atributos e habilidades dinâmicos · NPCs autônomos com memória individual · avaliação,
ocultação e falsificação de informações · combate híbrido · mundo vivo · modo administrador ·
imagens opcionais · IA local ou externa.

## Tecnologias
Python 3.12+ (desenvolvido com 3.13), Flask, SQLAlchemy, Alembic, Pydantic, SQLite ·
Vue 3, Vite, Pinia, Vue Router · Ollama (IA local). Motivos em [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Pré-requisitos
| Programa | Versão | Observação |
|---|---|---|
| Windows | 10 ou 11 | os atalhos `.cmd` são para Windows |
| Python | 3.12 ou mais novo | https://www.python.org |
| Node.js | 20.19+ ou 22.12+ (recomendado 24 LTS) | neste computador: versão portátil em `F:\Tools\node-v24.22.2-win-x64` |
| Ollama | atual | IA local e gratuita; neste computador: versão portátil em `F:\Tools\ollama` |

Os atalhos usam automaticamente o Node e o Ollama de `F:\Tools` quando existem.
Em outro computador, ajuste os caminhos no topo de `instalar.cmd` e `iniciar.cmd`.

## Instalação (uma vez)
1. Dê dois cliques em **`instalar.cmd`** (na pasta do projeto).
2. Espere aparecer `Instalacao concluida.` e aperte qualquer tecla.

Ele cria o ambiente do backend (`backend\.venv`), instala as bibliotecas do frontend
(`frontend\node_modules`) e cria o arquivo `.env` (suas configurações) se ainda não existir.

## Jogar
1. Dê dois cliques em **`iniciar.cmd`**.
2. Abrem-se janelas pretas (backend, frontend e, se instalado, Ollama) e depois o navegador em
   http://127.0.0.1:5173. **Não feche as janelas pretas enquanto joga.**
3. Para encerrar: feche o navegador e as janelas pretas. Tudo já fica salvo a cada jogada.

## Configuração (`.env`)
O arquivo `.env` fica na raiz do projeto e **nunca vai para o Git** (pode ter senhas e chaves).
O modelo comentado é o [`.env.example`](.env.example). Os mais usados:

| Variável | Para que serve | Padrão |
|---|---|---|
| `AI_MODEL` | modelo do Ollama (ex.: `qwen2.5:1.5b`); vazio = primeiro instalado | vazio |
| `AI_TEMPERATURE` | criatividade (0 a 2) | 0.8 |
| `AI_MAX_OUTPUT_TOKENS` | tamanho máximo de cada narração | 1024 |
| `AI_CONTEXT_WINDOW` | quanto histórico o modelo considera (mais = mais RAM) | 8192 |
| `AI_TIMEOUT_SECONDS` | espera máxima por uma resposta | 600 |
| `DATA_DIR` | pasta do banco de dados e backups | `./data` |

Depois de mudar o `.env`, feche e abra o jogo de novo.

## Para desenvolvedores
Comandos no PowerShell, a partir da pasta do projeto:
```
# Testes do backend (não precisam de internet nem de IA)
cd backend; .\.venv\Scripts\python.exe -m pytest

# Teste com o Ollama real (precisa do Ollama aberto e de um modelo instalado)
cd backend; .\.venv\Scripts\python.exe -m pytest -m external -s

# Testes e build do frontend (com o Node portátil no PATH desta janela)
$env:Path = "F:\Tools\node-v24.22.2-win-x64;" + $env:Path
cd frontend; npm test; npm run build

# Servidores separados, para desenvolvimento
cd backend; .\.venv\Scripts\flask.exe --app app run --debug    # http://127.0.0.1:5000/api/health
cd frontend; npm run dev                                         # http://127.0.0.1:5173
```

## Documentação
- [Comece aqui (como usar o Claude Code neste projeto)](COMECE_AQUI.md)
- [Status do projeto](PROJECT_STATUS.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Banco de dados](docs/DATABASE.md)
- [Requisitos](docs/REQUIREMENTS.md)
- [Decisões](docs/DECISIONS.md)
- [Provedores de IA](docs/AI_PROVIDERS.md)
- [Comandos administrativos](docs/ADMIN_COMMANDS.md)
- [Especificação completa](docs/SPEC.md)
