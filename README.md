# AI RPG Engine

Plataforma de RPG narrativo com inteligência artificial: a IA cria mundos, narra e interpreta
personagens, enquanto um motor de jogo valida as regras e guarda tudo de forma persistente.

> **Status: as 7 etapas da especificação estão concluídas** (Dockerfile ainda não testado). Detalhes, testes e pendências
> em [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Como jogar: [Guia do jogador](docs/GUIA_DO_JOGADOR.md).

## O que já funciona
- Campanhas independentes, criadas à mão ou **geradas aleatoriamente** (com segredos que só a IA conhece).
- **Motor de regras próprio de cada universo**: atributos, recursos, habilidades com custo e recarga, itens,
  equipamentos com bônus por espaço, classe e raça,
  testes com dados (rolados pelo motor, com semente registrada), efeitos com duração, regras de morte.
- **Mundo persistente**: fatos canônicos, relógio do mundo, acontecimentos agendados, missões,
  relacionamentos, o que cada personagem sabe (com disfarces e informações falsas), memória individual de NPCs,
  NPCs que agem longe do jogador quando o tempo passa, resumos automáticos da história.
- Interface com narração em tempo real, ficha, missões, conhecidos, mapa, diário e laços.
- **Modo administrador** (`/admin`, `/debug`) separado da história, com senha, confirmação, auditoria e desfazer.
- **Cópias de segurança**: snapshots por campanha (automáticos e manuais), exportar e importar.
- IA local e gratuita (Ollama). Imagens: estrutura pronta, desligada (sem gerador escolhido).

Ainda não: contas de usuário/multiplayer, provedores de IA externos, gerador de imagens, ordem de iniciativa
no combate.

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
| `AI_MECHANICS` | motor de regras nos turnos (`false` = só narração, mais rápido) | true |
| `AUTO_SNAPSHOT_EVERY` | cópia automática a cada N jogadas (0 = nunca) | 20 |
| `ADMIN_PASSWORD` | senha do modo administrador (vazio = desligado) | — |

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

# Medir desempenho com uma campanha grande (IA falsa; pasta temporária)
cd backend; .\.venv\Scripts\python.exe scripts\benchmark_large_campaign.py 500 300

# Servidores separados, para desenvolvimento
cd backend; .\.venv\Scripts\flask.exe --app app run --debug    # http://127.0.0.1:5000/api/health
cd frontend; npm run dev                                         # http://127.0.0.1:5173
```

## Documentação
- [Guia do jogador](docs/GUIA_DO_JOGADOR.md)
- [Hospedagem (opcional)](docs/HOSTING.md)
- [Comece aqui (como usar o Claude Code neste projeto)](COMECE_AQUI.md)
- [Status do projeto](PROJECT_STATUS.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Banco de dados](docs/DATABASE.md)
- [Requisitos](docs/REQUIREMENTS.md)
- [Decisões](docs/DECISIONS.md)
- [Provedores de IA](docs/AI_PROVIDERS.md)
- [Comandos administrativos](docs/ADMIN_COMMANDS.md)
- [Especificação completa](docs/SPEC.md)
