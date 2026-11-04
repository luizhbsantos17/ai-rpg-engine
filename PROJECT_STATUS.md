# PROJECT_STATUS

Última atualização: 2026-11-04 (sessão autônoma da madrugada).

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída (decisões D-001 a D-049) |
| 1 — Fundação | **concluída** e verificada com Ollama real |
| 2 — Motor de RPG | **concluída** e verificada com Ollama real |
| 3 — Narrativa e mundo | **concluída** (teste de campanha simulada com reinício) |
| 4 — Sistemas avançados | **concluída** (`tests/e2e/test_different_rule_systems.py`) |
| 5 — Interface completa | **concluída** (testes de componentes; falta o dono olhar a tela) |
| 6 — Imagens e administração | **concluída** (imagens: só a estrutura, desligada; gerador real pendente) |
| 7 — Qualidade e expansão | **em andamento**: 7.1 a 7.4 concluídas; faltam 7.5 e 7.6 |

## Última tarefa concluída
Etapa 7.4: desempenho com campanha grande (D-049). Medição com `scripts/benchmark_large_campaign.py`
(IA falsa; mede só motor e banco), 2.000 NPCs, 1.000 turnos, 12 mil eventos:
- estado do jogo enviado à IA **não cresce**: ~1.900 tokens com 100 ou 2.000 NPCs; ~133 consultas, ~35–65 ms;
- turno (sem a IA) caiu de ~152 ms para ~69 ms numa campanha de 1.000 turnos (índice das lembranças de NPC:
  35,6 ms → 0,6 ms por turno); cópia automática deixou de carregar todos os turnos (25 → 6 ms);
- abrir histórico ~50–70 ms; ficha ~5–9 ms; mapa/diário ~80 ms; exportar snapshot ~0,9–1,5 s (agora em segundo plano).
Antes: 7.1 (segurança, D-047), 7.2 (teste real ponta a ponta com Ollama), 7.3 (snapshot automático, D-048).

## Próxima tarefa: Etapa 7.5 — Documentação final e preparação para hospedagem
Critério (SPEC Parte 23): o projeto funciona de maneira consistente, com testes demonstrando os principais fluxos.
Faltam:
5. Documentação final (README, guia do jogador) e preparação para hospedagem (Dockerfile opcional, D-009).
6. **Snapshots de versões antigas do programa**: hoje restaurar/importar exige a mesma versão do banco (D-045);
   qualquer migração nova (como a 14 desta etapa) torna snapshots e exportações antigas impossíveis de restaurar.
   Plano: restaurar o arquivo num banco temporário na versão dele, rodar as migrações nesse banco e então
   importar. Hoje não afeta nada (o banco real está vazio e não há snapshots), mas precisa existir antes do
   dono jogar de verdade.

## Arquivos modificados nesta sessão (Etapa 7)
`backend/app/__init__.py`, `backend/app/admin/sessions.py`, `backend/app/config.py`,
`backend/app/persistence/snapshots.py`, `backend/app/services/{auto_backup.py, startup.py, background.py,
summaries.py, journal.py}`, `backend/app/persistence/repositories/narrative.py`,
`backend/app/persistence/models/knowledge.py`, `backend/app/ai/context/game_state.py`,
`backend/app/admin/commands.py`, `backend/alembic/versions/...db33890eefb9_indice_memorias_npc.py`,
`backend/scripts/benchmark_large_campaign.py`,
`backend/tests/{integration/test_security.py, integration/test_auto_backup.py,
integration/test_large_campaign.py, unit/test_background.py}`, `.env.example`,
`docs/{AI_PROVIDERS.md, DECISIONS.md, DATABASE.md}`, `CLAUDE.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`.

## Pendências menores
- Combate sem ordem de iniciativa dedicada (funciona por testes + dano condicional + efeitos + morte).
- Equipamento por espaços (mão, armadura...) não existe; itens ficam no inventário.
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
| Modelo instalado | `qwen2.5:1.5b` (986 MB) |
| Disco | C: ~3,3 GB livres (nada instalado no C:); F: ~21 GB livres |

## Testes executados (resultados reais)
| Data | O quê | Resultado |
|---|---|---|
| 2026-11-04 | backend `pytest` (unit + integração + fluxo completo) | **327 passed**, 1 deselected (externo) |
| 2026-11-04 | frontend `npm test` (Vitest) | **43 passed** |
| 2026-11-04 | frontend `npm run build` | ok |
| 2026-11-04 | `pytest -m external` com Ollama real | **1 passed** |
| 2026-11-04 | Etapa 1 com IA real: criar → jogar → desligar → religar → continuar | ok |
| 2026-11-04 | Etapa 2 com IA real (motor ligado) | ok: preparação, teste 1d20 rolado pelo motor, operação persistida; turno ~21 s |
| 2026-11-04 | Etapa 3: campanha simulada (FakeProvider) com NPC, relação, missão, cânone, agendamento, tempo e reinício | ok (`tests/e2e/test_living_campaign.py`) |
| 2026-11-04 | Geração de campanha com IA real | ok: 7–9 s; ingredientes usados; segredos só no banco |
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
1. **Modelo de IA**: baixar um maior? `qwen2.5:3b` (1,9 GB), `gemma3:4b` (3,4 GB), `qwen2.5:7b` (4,7 GB).
   Ou serviço externo (pode ter custo; exige pesquisa de preços e autorização).
2. **GPU integrada** no Ollama (`OLLAMA_IGPU_ENABLE=1`): testar se acelera?
3. Apagar `F:\Tools\downloads` (~1,7 GB de zips já extraídos)? Não apaguei por segurança.
4. **Gerador de imagens**: deixar desligado, ou escolher um (serviço pago ou modelo local grande).

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
