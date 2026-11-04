# PROJECT_STATUS

Última atualização: 2026-11-04 (pedidos do dono depois de testar: outra versão, IA gratuita, ficha, disco C:).

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída (decisões D-001 a D-057) |
| 1 — Fundação | **concluída** e verificada com Ollama real |
| 2 — Motor de RPG | **concluída** e verificada com Ollama real |
| 3 — Narrativa e mundo | **concluída** (teste de campanha simulada com reinício) |
| 4 — Sistemas avançados | **concluída** (`tests/e2e/test_different_rule_systems.py`) |
| 5 — Interface completa | **concluída** (testes de componentes; falta o dono olhar a tela) |
| 6 — Imagens e administração | **concluída** (imagens: só a estrutura, desligada; gerador real pendente) |
| 7 — Qualidade e expansão | **concluída** (Dockerfile escrito, não testado: sem Docker nesta máquina) |

## Última tarefa concluída
Pedidos do dono depois de testar (D-054 a D-057):
- **Disco C:**: temporários dos testes (~270 MB por execução), cache do pip/npm e sobra do teste de desempenho
  saíram do C: (liberados ~390 MB); agora tudo fica em `.tmp/` e `.cache/` no projeto. **Causa principal
  do C: enchendo, medida**: `C:\pagefile.sys` (memória virtual do Windows) cresceu de 3,7 para 4,8 GB em
  1 hora enquanto um modelo de IA estava carregado; `C:\hiberfil.sys` ocupa 5,6 GB. Ver "Decisões pendentes" 5.
- **"↻ Outra versão"** da última narração (D-055): mesmos dados e resultados, texto novo; se falhar, a
  anterior fica. Testado com Ollama real: troca ok; o 1,5B copiava a versão recusada quando ela era mostrada,
  então ela deixou de ser mostrada (e a criatividade sobe +0,3 só nessa hora). Depois disso, texto diferente.
- **IA gratuita na internet** (D-054): `AI_PROVIDER=gemini|groq|openrouter` + chave. Limites pesquisados nas
  páginas oficiais (AI_PROVIDERS.md). **Não testado com os serviços reais** (falta a chave do dono); testado
  com servidor simulado; teste real pronto em `tests/external/test_free_service_real.py`.
- **Ficha inicial mais completa** (D-056): 5 a 10 atributos (energia, nível/experiência quando estilo jogo),
  habilidades e itens iniciais equipados; regra de progressão no intérprete. Com o 1,5B real: vieram
  habilidade e 4 itens (1 equipado), mas só 5 atributos e sem mana: o modelo pequeno ignora parte das regras.
- **Narrador mais coerente**: recebe a CENA ATUAL (local, hora, presentes) e regras de ofício.
- **Guia do desenvolvedor/admin**: `docs/GUIA_DO_DESENVOLVEDOR.md`.
- Modelo local `gemma3:4b` (3,3 GB) **baixado** em `F:\Tools\ollama-models`, **não testado**: com 99 MB
  livres no C:, carregar 4 GB de modelo pode travar o Windows (a memória extra vai para o C:).

Antes: adaptador para servidores no formato OpenAI (D-053), testado com o Ollama em `/v1`.

Adaptador para servidores no formato OpenAI (D-053): `AI_PROVIDER=openai_compat`, com serviços pagos
bloqueados. Testado de verdade (sem custo) contra o Ollama em `/v1`: `pytest -m external` e um jogo completo.

Antes, Equipamentos e classe/raça (D-052), itens 9 e 11 da interface da SPEC que faltavam: `item.equip` /
`item.unequip`, um item por espaço, bônus somado pelo motor nos testes, seção "Equipamento" na ficha,
classe e raça na ficha e no contexto da IA, preparação da campanha pede classe e raça.
Testado com Ollama real: fluxo completo ok; preparação preenche classe/raça coerentes (ver AI_PROVIDERS.md).

Antes, Etapa 7.5: documentação final e preparação para hospedagem (D-051): README atualizado, guia do jogador
(`docs/GUIA_DO_JOGADOR.md`), guia de hospedagem (`docs/HOSTING.md`), `FRONTEND_DIST` (backend serve o
frontend compilado; testado com `npm run build` real em modo produção na porta 5001), `Dockerfile` e
`.dockerignore` (**não testados**: o Docker não está instalado). Com isso a Etapa 7 está concluída.

Antes, Etapa 7.6: snapshots e exportações de versões anteriores do programa voltam a ser restauráveis (D-050):
o arquivo é convertido num banco temporário pelas próprias migrações. Testado com um arquivo da versão da
Etapa 2 (sem cânone, sem mecânicas no turno): importação pela API e restauração pelo `/admin`.

Antes, Etapa 7.4: desempenho com campanha grande (D-049). Medição com `scripts/benchmark_large_campaign.py`
(IA falsa; mede só motor e banco), 2.000 NPCs, 1.000 turnos, 12 mil eventos:
- estado do jogo enviado à IA **não cresce**: ~1.900 tokens com 100 ou 2.000 NPCs; ~133 consultas, ~35–65 ms;
- turno (sem a IA) caiu de ~152 ms para ~69 ms numa campanha de 1.000 turnos (índice das lembranças de NPC:
  35,6 ms → 0,6 ms por turno); cópia automática deixou de carregar todos os turnos (25 → 6 ms);
- abrir histórico ~50–70 ms; ficha ~5–9 ms; mapa/diário ~80 ms; exportar snapshot ~0,9–1,5 s (agora em segundo plano).
Antes: 7.1 (segurança, D-047), 7.2 (teste real ponta a ponta com Ollama), 7.3 (snapshot automático, D-048).

## Próxima tarefa
1. **Dono**: liberar espaço no C: (decisão pendente 5) e criar uma chave gratuita do Gemini (passo a passo em
   `docs/GUIA_DO_DESENVOLVEDOR.md`, seção 2). Com a chave: rodar `pytest -m external` (teste real) e jogar.
2. Com espaço no C:: testar o `gemma3:4b` local (velocidade e qualidade), com
   `cd backend; .\.venv\Scripts\python.exe scripts\real_turn_check.py gemma3:4b` (banco separado).
3. Possíveis melhorias sem decisão do dono: "desfazer a jogada inteira" (novos dados, usando snapshots);
   ordem de iniciativa no combate; contas de usuário para hospedagem.

## Arquivos modificados nesta sessão
`backend/app/ai/orchestrator/{turns.py, events.py, mechanics.py}`, `backend/app/ai/context/narration.py`,
`backend/app/ai/prompts/{narrator.py, interpreter.py, setup.py}`, `backend/app/ai/schemas/setup.py`,
`backend/app/api/turns.py`, `backend/app/engine/witness.py`,
`backend/app/persistence/repositories/{memory.py, narrative.py}`, `backend/app/services/summaries.py`,
`backend/app/providers/{free_services.py (novo), openai_compat.py, registry.py, base.py}`, `backend/app/config.py`,
`backend/tests/conftest.py`, `backend/tests/integration/{test_regenerate_narration.py (novo),
test_setup_progression.py (novo), test_turn_mechanics.py}`, `backend/tests/unit/{test_free_services.py (novo),
test_openai_compat_provider.py}`, `backend/tests/external/test_free_service_real.py (novo)`,
`backend/scripts/benchmark_large_campaign.py`, `frontend/src/{api/campaigns.js, stores/play.js,
stores/play.test.js, views/PlayView.vue}`, `frontend/.npmrc (novo)`, `iniciar.cmd`, `instalar.cmd`, `.gitignore`,
`.env.example`, `README.md`, `docs/{GUIA_DO_DESENVOLVEDOR.md (novo), GUIA_DO_JOGADOR.md, AI_PROVIDERS.md,
DECISIONS.md}`, `CHANGELOG.md`, `PROJECT_STATUS.md`. No `.env` do dono: só foram ACRESCENTADAS linhas vazias
`GEMINI_API_KEY=`, `GROQ_API_KEY=`, `OPENROUTER_API_KEY=` (nada existente mudou).


## Pendências menores
- Combate sem ordem de iniciativa dedicada (funciona por testes + dano condicional + efeitos + morte).
- **Troque `ADMIN_PASSWORD` no `.env`**: hoje está com o valor de exemplo (`troque-esta-senha`).

## O que existe e funciona (com testes)
- **Backend** (Python 3.13, Flask 3.1, SQLAlchemy 2.1, Alembic 1.20, Pydantic 2.14, httpx):
  - 14 migrações, 26 tabelas + índice de busca FTS5; repositórios com filtro obrigatório por `campaign_id`;
  - provedores `fake` (só testes) e `ollama` (streaming, JSON com esquema);
  - turno: preparação (1º turno) → intérprete → motor (30 operações) → narrador com fatos e "o que cada NPC sabe";
    idempotente, repetição segura, retomada após reiniciar;
  - motor: dados com semente, fórmulas seguras, definições versionadas, cânone, relógio, agendamentos,
    efeitos, relações, conhecimento, memória de NPCs, missões;
  - memória em camadas: resumos a cada 8 turnos (segundo plano) + busca no passado;
  - geração aleatória de campanhas (rascunho com segredos só no servidor).
- **Frontend** (Vue 3.5, Vite 8, Pinia 4, Vue Router 5): lista com rascunhos; criação aleatória (gerar,
  manter, gerar de novo, editar, começar) ou manual; jogo com narração em tempo real, avisos
  `[SISTEMA]`/`[TESTE]`/`[ALERTA]`/`[MISSÃO]`, ficha "STATUS" (tempo, recursos, efeitos, atributos,
  habilidades, inventário) e diário de missões.
- **Atalhos**: `instalar.cmd` e `iniciar.cmd` (Ollama portátil, backend, frontend, navegador).

## Ambiente do usuário (verificado em 2026-11-03/04)
| Item | Situação |
|---|---|
| Windows 11 Pro, Ryzen 5 4600G (só GPU integrada), 13,8 GB RAM | IA local em CPU |
| Python 3.13.3 | ok |
| Node.js | sistema: 20.11.1 (não usado); **projeto: 24.22.2 LTS portátil em `F:\Tools\node-v24.22.2-win-x64`** |
| Ollama | **0.40.14 portátil em `F:\Tools\ollama`**, modelos em `F:\Tools\ollama-models` |
| Modelos instalados | `qwen2.5:1.5b` (986 MB), `gemma3:4b` (3,3 GB, ainda não testado) |
| Disco | C: **~0,1 GB livre** (pagefile 4,8 GB + hiberfil 5,6 GB; nada do projeto no C:); F: ~14 GB livres |

## Testes executados (resultados reais)
| Data | O quê | Resultado |
|---|---|---|
| 2026-11-04 | backend `pytest` (unit + integração + fluxo completo) | **367 passed**, 5 deselected (externos) |
| 2026-11-04 | frontend `npm test` (Vitest) | **48 passed** (uma execução antes caiu por falta de RAM do PC; repetida ok) |
| 2026-11-04 | `pytest -m external` (Ollama nativo + /v1; serviços gratuitos sem chave) | **3 passed, 2 skipped** |
| 2026-11-04 | "outra versão" com Ollama real (`qwen2.5:1.5b`), banco separado | ok: troca feita, texto novo diferente; 1ª jogada 77–90 s, outra versão 25 s |
| 2026-11-04 | serviços Gemini/Groq/OpenRouter de verdade | **não testado** (sem chave do dono) |
| 2026-11-04 | `gemma3:4b` local | **não testado** (baixado; C: com 99 MB livres) |
| 2026-11-04 | frontend `npm run build` | ok |
| 2026-11-04 | `pytest -m external` com Ollama real (nativo + formato OpenAI em /v1) | **3 passed** |
| 2026-11-04 | jogo completo com `AI_PROVIDER=openai_compat` (Ollama /v1) | ok: geração 7 s; 1º turno 66 s; depois 13–19 s |
| 2026-11-04 | Etapa 1 com IA real: criar → jogar → desligar → religar → continuar | ok |
| 2026-11-04 | Etapa 2 com IA real (motor ligado) | ok: preparação, teste 1d20 rolado pelo motor, operação persistida; turno ~21 s |
| 2026-11-04 | Etapa 3: campanha simulada (FakeProvider) com NPC, relação, missão, cânone, agendamento, tempo e reinício | ok (`tests/e2e/test_living_campaign.py`) |
| 2026-11-04 | Geração de campanha com IA real | ok: 7–9 s; ingredientes usados; segredos só no banco |
| 2026-11-04 | Etapa 7.5: modo produção com `FRONTEND_DIST` e build real do frontend | ok: página, rotas do Vue, arquivos e erro JSON da API numa porta só |
| 2026-11-04 | Etapa 7.5: `Dockerfile` | **não testado** (Docker não instalado) |
| 2026-11-04 | Etapa 7.4: `scripts/benchmark_large_campaign.py 2000 1000` | ok: contexto da IA ~1.900 tokens (fixo); turno sem IA ~69 ms |
| 2026-11-04 | Etapa 7.2: fluxo completo pela API com IA real + reinício | ok: geração 14,6 s; 1º turno 86 s; depois 27–34 s; histórico, ficha e snapshot intactos após religar; `validate_world` sem inconsistências |

**Não testado por mim**: a interface no navegador com os olhos (não tenho como ver a tela).

## Problemas conhecidos
- **Qualidade com `qwen2.5:1.5b`**: narração razoável, mas repetitiva; escolhas mecânicas do intérprete muitas
  vezes sem sentido; preenche pouco os formatos mais ricos (gêneros, companheiros). O motor impede estados
  inválidos, não escolhas ruins. Precisa de modelo maior (decisão pendente 1).
- Turno com motor ~27–34 s nesta máquina depois de alguns turnos (1º turno até ~86 s com a preparação);
  o contexto cresce (~4 mil tokens de entrada no 3º turno) e pesa em CPU.
- No teste 7.2 o intérprete do modelo 1,5B quase não propôs operações (ex.: "dormir até o amanhecer" não
  avançou o relógio, então o mundo não foi simulado). É limite do modelo, não do motor (testado com FakeProvider).
- A busca no passado é por palavras (FTS5); sinônimos não são encontrados (embeddings: melhoria futura).
- 5 vulnerabilidades "moderadas" no `npm audit` só em dependência de testes.

## Decisões pendentes (dependem do dono)
0. **Serviços de IA pagos**: bloqueados. Liberar exige controle de gasto, pesquisa de preços e sua autorização.
1. **Chave de IA gratuita**: criar a chave (Gemini recomendado; passo a passo no guia do desenvolvedor) e
   colocar no `.env`. Só você pode criar a conta. Lembre: o texto da história vai para o serviço.
2. **GPU integrada** no Ollama (`OLLAMA_IGPU_ENABLE=1`): testar se acelera?
3. Apagar `F:\Tools\downloads` (~1,7 GB de zips já extraídos)? Não apaguei por segurança.
4. **Gerador de imagens**: deixar desligado, ou escolher um.
5. **Espaço no C:** (mudanças no Windows; precisam de você como administrador, e dá para desfazer):
   a. desligar a hibernação (libera ~5,6 GB): PowerShell **como administrador** → `powercfg /h off`
      (desfazer: `powercfg /h on`). O "Início rápido" do Windows deixa de existir; o PC continua igual.
   b. mover a memória virtual para o F:: Configurações avançadas do sistema → Desempenho → Avançado →
      Memória virtual → Alterar → C: "Sem arquivo de paginação", F: "Gerenciado pelo sistema" → reiniciar.
   c. limpar o que não é do projeto: "Limpeza de disco" (arquivos do Windows Update), duas versões do app
      Codex (~2,3 GB cada) em WindowsApps, cache de extensões do VS Code (~700 MB), cache do Google Updater (~500 MB).

## Como testar (passo a passo para o dono)
1. Dois cliques em `F:\Projetos\AI-RPG-Engine\iniciar.cmd`. Abrem 3 janelas pretas e o navegador.
2. **+ Nova campanha** → aba **Gerar aleatória** → **Gerar campanha** (~10 s). Marque "manter" no que gostou e
   **Gerar de novo**, ou **Editar**. Depois **Começar**.
3. **Começar a história**: o 1º turno demora (~45 s) porque a IA cria as regras e o personagem; aparecem avisos
   `[SISTEMA]`, a ficha "STATUS" e o diário de missões à direita (no celular, botão "Ficha").
4. Jogue algumas ações. Feche tudo, abra de novo e clique em **Continuar**: história, ficha e missões iguais.

## Arquivos principais
Backend: `app/{config.py, persistence, providers, ai, engine, services, api}`, `alembic/versions` (9),
`tests/{unit, integration, e2e, external}`. Frontend: `frontend/src/{api, stores, views, components, utils, styles}`.
Raiz: `instalar.cmd`, `iniciar.cmd`. Docs: `docs/*.md`.

## Casos da SPEC Parte 22 cobertos por testes
todos os 26 (o 25, permissões, cobre dono da campanha e modo administrador;
multiplayer ainda não existe).

## Riscos principais
| Risco | Mitigação |
|---|---|
| Escopo muito grande | Etapas pequenas e executáveis; nada marcado pronto sem teste |
| Modelos locais erram JSON e escolhas | Validação + reenvio (D-008/D-026); operações recusadas uma a uma; modelo maior |
| Lentidão com 2 chamadas por turno | Limites de tokens (D-028); `AI_MECHANICS=false`; modelo/hardware melhores |
| Contexto grande demais | Orçamento de tokens; resumos + busca (Etapa 3.6) |
| IA contradizer fatos antigos | Regras e fatos versionados; cânone e resumos no contexto |
