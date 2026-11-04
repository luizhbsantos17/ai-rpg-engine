# PROJECT_STATUS

Última atualização: 2026-11-04 (sessão autônoma da madrugada).

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída (decisões D-001 a D-037) |
| 1 — Fundação | **concluída** e verificada com Ollama real |
| 2 — Motor de RPG | **concluída** e verificada com Ollama real |
| 3 — Narrativa e mundo | **concluída**: critério verificado por teste de campanha simulada com reinício |
| 4 — Sistemas avançados | **em andamento**: 4.1 backend concluído (avaliação/ocultação/falsificação); falta o painel na interface |
| 5 a 7 | não iniciadas |

## Última tarefa concluída
Etapa 3 completa: cânone, relógio/agendamentos/efeitos, relacionamentos, conhecimento/memória,
missões, memória em camadas (resumos + busca), geração aleatória de campanhas, turmas, teste de fluxo.

## Próxima tarefa: Etapa 4.1 (interface) — painel "Personagens conhecidos" usando `GET /api/campaigns/<id>/known`; depois 4.2

Feito em 4.1 (backend, testado): tabela `disguises` (migração 10), operações `disguise.apply/remove` e
`knowledge.assess` (regra em `app/engine/operations/handlers/assessment.py`), avisos `[ANÁLISE]`, rota `/known`.

## Plano da Etapa 4 — Sistemas avançados
Critério (SPEC Parte 23): campanhas diferentes conseguem usar sistemas de regras significativamente diferentes.
Subtarefas planejadas, nesta ordem:
1. **Avaliação, ocultação e falsificação** (SPEC 6): tabela `disguises`; operações `disguise.apply/remove` e
   `knowledge.assess` (poder de avaliação × ocultação, rolado pelo motor; resultado vira `knowledge` com nível
   estimado/parcial/confirmado/falso). Painel "Personagens conhecidos" mostrando só o que o protagonista sabe.
2. **Regras de morte por universo** (SPEC 7.4): definição `death_rule` (permanente, ressurreição, reencarnação,
   inconsciência...); recurso vital chegando a 0 aplica a regra automaticamente, sem mudar retroativamente.
3. **Recarga de habilidades** (cooldown no tempo do mundo) e **progressão** com regras definidas pela campanha.
4. **Simulação de NPCs fora de cena** (SPEC 8.4): níveis de simulação; quando o tempo avança bastante, a IA
   propõe o que NPCs relevantes fizeram (operações validadas); NPCs distantes avançam por agenda.
5. **Eventos mundiais** (SPEC 10.2) gerados durante passagens longas de tempo.
6. Teste do critério: duas campanhas com sistemas de regras bem diferentes (ex.: atributos numéricos ×
   ranks nominais e conceituais), operando lado a lado.

## O que existe e funciona (com testes)
- **Backend** (Python 3.13, Flask 3.1, SQLAlchemy 2.1, Alembic 1.20, Pydantic 2.14, httpx):
  - 9 migrações, 22 tabelas + índice de busca FTS5; repositórios com filtro obrigatório por `campaign_id`;
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
| 2026-11-04 | backend `pytest` (unit + integração + fluxo completo) | **265 passed**, 1 deselected (externo) |
| 2026-11-04 | frontend `npm test` (Vitest) | **32 passed** |
| 2026-11-04 | frontend `npm run build` | ok |
| 2026-11-04 | `pytest -m external` com Ollama real | **1 passed** |
| 2026-11-04 | Etapa 1 com IA real: criar → jogar → desligar → religar → continuar | ok |
| 2026-11-04 | Etapa 2 com IA real (motor ligado) | ok: preparação, teste 1d20 rolado pelo motor, operação persistida; turno ~21 s |
| 2026-11-04 | Etapa 3: campanha simulada (FakeProvider) com NPC, relação, missão, cânone, agendamento, tempo e reinício | ok (`tests/e2e/test_living_campaign.py`) |
| 2026-11-04 | Geração de campanha com IA real | ok: 7–9 s; ingredientes usados; segredos só no banco |

**Não testado por mim**: a interface no navegador com os olhos (não tenho como ver a tela).

## Problemas conhecidos
- **Qualidade com `qwen2.5:1.5b`**: narração razoável, mas repetitiva; escolhas mecânicas do intérprete muitas
  vezes sem sentido; preenche pouco os formatos mais ricos (gêneros, companheiros). O motor impede estados
  inválidos, não escolhas ruins. Precisa de modelo maior (decisão pendente 1).
- Turno com motor ~21 s nesta máquina (1º turno ~46 s com a preparação).
- A busca no passado é por palavras (FTS5); sinônimos não são encontrados (embeddings: melhoria futura).
- 5 vulnerabilidades "moderadas" no `npm audit` só em dependência de testes.

## Decisões pendentes (dependem do dono)
1. **Modelo de IA**: baixar um maior? `qwen2.5:3b` (1,9 GB), `gemma3:4b` (3,4 GB), `qwen2.5:7b` (4,7 GB).
   Ou serviço externo (pode ter custo; exige pesquisa de preços e autorização).
2. **GPU integrada** no Ollama (`OLLAMA_IGPU_ENABLE=1`): testar se acelera?
3. Apagar `F:\Tools\downloads` (~1,7 GB de zips já extraídos)? Não apaguei por segurança.

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
1, 2, 3, 4, 5, 6, 7, 8 (parcial), 9 (parcial), 13, 14 (parcial: agendados), 15, 18, 19, 20, 21, 22, 24,
25 (parcial: dono), 26. Faltam: 10, 11, 12 (avaliação/ocultação/falsificação — Etapa 4), 16 (admin — Etapa 6),
17 (backup — Etapa 6/7), 23 (morte — Etapa 4).

## Riscos principais
| Risco | Mitigação |
|---|---|
| Escopo muito grande | Etapas pequenas e executáveis; nada marcado pronto sem teste |
| Modelos locais erram JSON e escolhas | Validação + reenvio (D-008/D-026); operações recusadas uma a uma; modelo maior |
| Lentidão com 2 chamadas por turno | Limites de tokens (D-028); `AI_MECHANICS=false`; modelo/hardware melhores |
| Contexto grande demais | Orçamento de tokens; resumos + busca (Etapa 3.6) |
| IA contradizer fatos antigos | Regras e fatos versionados; cânone e resumos no contexto |
