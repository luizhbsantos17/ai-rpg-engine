# Guia do desenvolvedor e administrador

Este guia é para você, dono do projeto, quando estiver no papel de **desenvolvedor** (mudar o programa)
ou de **administrador** (inspecionar e corrigir uma campanha). Para só jogar, use o
[Guia do jogador](GUIA_DO_JOGADOR.md). A referência completa dos comandos está em
[ADMIN_COMMANDS.md](ADMIN_COMMANDS.md).

Todos os comandos abaixo são para o **PowerShell**, a partir da pasta do projeto
`F:\Projetos\AI-RPG-Engine` (a não ser quando dizem `cd backend` ou `cd frontend`).

---

## 1. Mapa rápido das pastas

| Pasta / arquivo | O que tem |
|---|---|
| `iniciar.cmd`, `instalar.cmd` | Abrir o jogo / instalar (dois cliques) |
| `.env` | **Sua** configuração (IA, senha de admin, chaves). Nunca vai para o Git |
| `.env.example` | Modelo comentado de todas as opções do `.env` |
| `data/` | **Seus dados**: banco `rpg.db`, backups (`data/backups/<campanha>/`). Nunca apague sem backup |
| `.tmp/`, `.cache/` | Temporários e caches (testes, npm). Pode apagar à vontade com o jogo fechado |
| `backend/app/` | O servidor (Python/Flask) |
| `backend/app/ai/prompts/` | **Instruções dadas à IA** (o que mais muda o "jeito" da história) |
| `backend/app/engine/` | Motor de regras: dados, testes, operações, morte, tempo |
| `backend/app/providers/` | Conexão com cada IA (Ollama, Gemini, Groq, OpenRouter...) |
| `backend/tests/` | Testes automáticos do backend |
| `frontend/src/` | A tela do jogo (Vue). `views/PlayView.vue` é a tela de jogar |
| `docs/` | Especificação, arquitetura, decisões (`DECISIONS.md`), guias |
| `PROJECT_STATUS.md`, `CHANGELOG.md` | O que está pronto, o que mudou, próximos passos |

---

## 2. Trocar a IA (o que mais muda a qualidade)

Abra o `.env` no Bloco de Notas, mude a linha `AI_PROVIDER=` e salve. Depois **feche e abra o jogo de novo**
(a configuração só é lida ao iniciar).

| `AI_PROVIDER=` | Onde roda | Custo | Precisa |
|---|---|---|---|
| `ollama` | No seu PC | grátis | Ollama aberto (o `iniciar.cmd` abre) e um modelo baixado |
| `gemini` | Internet (Google) | gratuito (sem faturamento) | `GEMINI_API_KEY` |
| `groq` | Internet (Groq) | gratuito (plano Free) | `GROQ_API_KEY` |
| `openrouter` | Internet | só modelos `:free` | `OPENROUTER_API_KEY` |
| `openai_compat` | Outro servidor (LM Studio...) | depende | `OPENAI_COMPAT_BASE_URL` |

### Como pegar uma chave gratuita (exemplo: Gemini)
1. Entre em https://aistudio.google.com/apikey com sua conta Google.
2. Clique em **Create API key** (Criar chave). Copie o texto que aparecer.
3. No `.env`: `AI_PROVIDER=gemini` e `GEMINI_API_KEY=<cole a chave aqui>`.
4. **Não** ative faturamento ("billing") no projeto do Google: sem ele, não há cobrança.
5. Feche e abra o jogo. Para testar sem jogar:
   `cd backend; .\.venv\Scripts\python.exe -m pytest -m external -s tests/external/test_free_service_real.py`
   (deve terminar com `2 passed` e mostrar um texto de taverna).

Groq: https://console.groq.com/keys · OpenRouter: https://openrouter.ai/keys (na OpenRouter, o programa
recusa qualquer modelo que não termine em `:free`, para nunca cobrar).

Limites gratuitos (conferidos em 04/11/2026; mudam sem aviso — detalhes e fontes em
[AI_PROVIDERS.md](AI_PROVIDERS.md)): OpenRouter = 20 pedidos/min e 50/dia (cada jogada usa 2 ou mais).
Se aparecer "limite de pedidos", o programa espera e tenta de novo sozinho; se continuar, espere um pouco.

**Privacidade:** serviços na internet recebem o texto da sua história. O Google usa dados do nível
gratuito para melhorar produtos. Para total privacidade, use `ollama`.

### Modelo
`AI_MODEL=` vazio escolhe sozinho (recomendado). Para forçar um: `AI_MODEL=gemini-2.5-flash`,
`AI_MODEL=gemma3:4b` (Ollama)... Ver modelos do Ollama instalados: `F:\Tools\ollama\ollama.exe list`.

---

## 3. Modo administrador (dentro do jogo)

1. Defina a senha no `.env`: `ADMIN_PASSWORD=uma-senha-sua` (a atual ainda é a do exemplo; troque).
2. No jogo, digite na caixa de texto um comando começando com `/admin` ou `/debug`.
3. Na primeira vez a página pede a senha. A resposta aparece no **CONSOLE ADMIN**, fora da história.

Comandos mais úteis:

| Para... | Digite |
|---|---|
| Ver a ficha verdadeira (inclusive o oculto) | `/admin status` ou `/admin status Nome` |
| Ver o que um NPC sabe e lembra | `/admin inspect Nome` |
| Mudar um valor | `/admin set player.vida 30` · `/admin set player.mana 10/20` |
| Dar item ou habilidade | `/admin give player item "Espada" --qty 1` · `/admin give player skill "Faísca" --level 2` |
| Teletransportar | `/admin teleport player "Taverna"` |
| Avançar o tempo | `/admin world.time advance 8h` |
| Desfazer o último comando admin | `/admin undo` |
| Backup agora / listar / voltar | `/admin snapshot create "antes do chefe"` · `/admin snapshot list` · `/admin snapshot.restore <id>` |
| Ver o que foi mandado para a IA | `/debug show_context` (ou `--role interpreter`) |
| Ver chamadas à IA (tempo, tokens, erros) | `/debug inspect_ai_requests --last 10` |
| Ver o log de eventos | `/debug show_events --last 20` |
| Procurar inconsistências | `/debug validate_world` |
| Lista completa | `/admin help` e `/debug help` |

Comandos destrutivos (⚠) pedem confirmação: o console mostra um código; repita o comando com `--confirm CÓDIGO`.

---

## 4. Uma jogada saiu ruim. E agora?

1. **Só o texto ficou ruim?** Clique em **↻ Outra versão** embaixo da última narração. A IA reescreve a
   cena com os mesmos resultados de dados (nada no mundo muda de novo). A versão anterior fica guardada no
   log de eventos (`/debug show_events`, evento `turn.narration_regenerated`).
2. **A IA entendeu errado a ação?** Veja o que ela propôs: `/debug show_context --role interpreter` e
   `/debug show_events --last 15`. Corrija com `/admin set`, `/admin give`, `/admin teleport`...
3. **A história desandou?** Volte a um backup: `/admin snapshot list` e `/admin snapshot.restore <id>`
   (há um automático a cada 20 jogadas; faça um manual antes de momentos importantes).
4. **A IA está sempre fraca?** Troque o modelo ou o provedor (seção 2). O modelo local `qwen2.5:1.5b` é
   pequeno: serve para testar, mas erra regras e escreve de forma simples.

---

## 5. Mudar o "jeito" da IA (prompts)

As instruções estão em texto comum, em português, dentro de `backend/app/ai/prompts/`:

| Arquivo | Papel da IA |
|---|---|
| `narrator.py` | Narrador: estilo, tamanho, como tratar o jogador |
| `interpreter.py` | Intérprete de regras: transforma a ação em operações (testes, dano, itens) |
| `setup.py` | Preparação da campanha: atributos, protagonista, habilidades e itens iniciais |
| `generator.py` | Gerador de campanhas aleatórias |
| `simulation.py` | O que os NPCs fazem longe do jogador |
| `summarizer.py` | Resumos da história (memória de longo prazo) |

Depois de mudar: rode os testes (seção 7). Alguns testes conferem frases do prompt; se um falhar por isso,
peça ao Claude Code para ajustar junto.

---

## 6. Backups e dados

- Tudo fica em `data/rpg.db` (banco SQLite). Backups automáticos: `data/backups/<id-da-campanha>/`.
- Exportar uma campanha para arquivo: botão **Exportar** na lista de campanhas (gera um `.json`).
- Cópia completa manual (com o jogo fechado): copie a pasta `data` inteira para outro lugar.
- Backups de versões antigas do programa são convertidos sozinhos ao restaurar.

---

## 7. Testes e comandos de desenvolvimento

| O quê | Comando | Resultado esperado |
|---|---|---|
| Testes do backend | `cd backend; .\.venv\Scripts\python.exe -m pytest` | `... passed` sem `failed` |
| Testes com IA real (Ollama aberto / chave) | `cd backend; .\.venv\Scripts\python.exe -m pytest -m external -s` | `passed` (pulados sem chave) |
| Testes da tela | `cd frontend; npm test` | `Tests ... passed` |
| Compilar a tela | `cd frontend; npm run build` | `built in ...` |
| Servidor sozinho | `cd backend; .\.venv\Scripts\flask.exe --app app run --debug` | abre em http://127.0.0.1:5000/api/health |
| Desempenho | `cd backend; .\.venv\Scripts\python.exe scripts\benchmark_large_campaign.py 500 300` | tempos por jogada |
| Uma jogada real com o Ollama (banco à parte) | `cd backend; .\.venv\Scripts\python.exe scripts\real_turn_check.py gemma3:4b` | ficha, narração e "outra versão" |

Se `npm` não for reconhecido, rode antes: `$env:PATH = "F:\Tools\node-v24.22.2-win-x64;" + $env:PATH`.

Erros do servidor aparecem na janela preta **"backend"** aberta pelo `iniciar.cmd`.

---

## 8. Regras que o programa segue (para não quebrar ao mudar)

- O banco é a fonte da verdade. A IA **propõe**; o motor valida e grava (com log de eventos).
- Dados só pelo motor (`engine/dice`), com semente gravada. A IA nunca "rola dados".
- Toda tabela de jogo tem `campaign_id`; todo acesso passa pelos repositórios.
- `/admin` e `/debug` só são lidos pelo interpretador de comandos, nunca pela IA.
- Chaves de API só no `.env`. Serviços pagos estão bloqueados até existir controle de gasto.
- Detalhes: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.

---

## 9. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| "Não foi possível conectar ao servidor de IA" | Ollama fechado ou internet fora | Abra pelo `iniciar.cmd`; confira a internet |
| "precisa da chave ... no .env" | `AI_PROVIDER` de serviço sem chave | Cole a chave (seção 2) e reabra |
| "limite de pedidos" | Cota gratuita do minuto/dia acabou | Espere; na OpenRouter o limite diário é baixo |
| Jogada demora 1–2 min | IA local em CPU | Normal no Ollama; use um serviço gratuito na internet |
| Disco C: enchendo | Programas fora do projeto (Windows, apps) | O projeto usa só o F:; veja `PROJECT_STATUS.md` |
| Senha de admin recusada | `ADMIN_PASSWORD` diferente / jogo não reaberto | Confira o `.env` e reabra o jogo |
