# PROJECT_STATUS

Última atualização: 2026-11-04 (sessão autônoma da madrugada).

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída (decisões D-001 a D-030) |
| 1 — Fundação | **concluída** e verificada com Ollama real (falta só o usuário olhar a interface) |
| 2 — Motor de RPG | **concluída**: critério verificado com Ollama real (operações alteram dados reais e persistentes) |
| 3 — Narrativa e mundo | não iniciada (plano abaixo) |
| 4 a 7 | não iniciadas |

## Última tarefa concluída
Etapa 2 — turno em duas fases (intérprete → motor → narrador), ficha do protagonista, `skill.use`.

## Próxima tarefa: Etapa 3 — Narrativa e mundo
Critério (SPEC Parte 23): a campanha possui continuidade narrativa e acontecimentos persistentes.
Subtarefas planejadas, nesta ordem:
1. **Registro canônico** (SPEC 3.4): tabela `canon_facts` com versões; operações `canon.assert` / `canon.amend`
   (alterar exige motivo e cria versão nova); fatos relevantes entram no contexto do intérprete e do narrador.
2. **Relógio do mundo** (SPEC 10.3): `time.advance`; `scheduled_events` + `event.schedule`; eventos vencidos
   processados quando o relógio anda; fechar o programa não avança o tempo (já testado).
3. **Relacionamentos** (SPEC 9): `relationships` (direcional, várias dimensões) + `relationship_events`;
   operação `relationship.change` sempre com o acontecimento que causou.
4. **Conhecimento e memória de NPCs** (SPEC 6.5 e 8.2): `knowledge` + `npc_memories`; `knowledge.record`;
   NPCs presentes numa cena guardam memória do que viram; contexto de NPC só com o que ele sabe.
5. **Missões** (SPEC 10.1): `quests` + `quest.create` / `quest.update`; painel na interface.
6. **Memória em camadas** (SPEC 15.1): `summaries` por cena/arco gerados pela IA "resumidora"; busca FTS5 em
   eventos e resumos para recuperar fatos antigos sem mandar o histórico inteiro.
7. **Geração de campanhas** (SPEC 3): campanha aleatória pela IA, gerar de novo, preservar elementos,
   separação `player_visible` × `gm_secret`; tela de criação nova.
8. **Turmas e grupos** (SPEC 4.3): vários personagens com atributos, personalidades e objetivos próprios.
9. Testes de fluxo: campanha simulada com NPCs, relacionamentos e retomada.

## O que existe e funciona (com testes)
- **Backend** (`backend/`, Python 3.13, Flask 3.1, SQLAlchemy 2.1, Alembic 1.20, Pydantic 2.14, httpx):
  - configuração por `.env` com validação; migrações automáticas ao iniciar (3 migrações, 14 tabelas);
  - repositórios com filtro obrigatório por `campaign_id` (+ testes guardiões no código-fonte);
  - provedores `fake` (só testes) e `ollama` (real, streaming, saída JSON com esquema);
  - turno idempotente: preparação da campanha → intérprete (JSON validado + reenvio do erro) → motor →
    narrador com os fatos; repetição segura; retomada após reiniciar;
  - motor: `engine/dice` (semente registrada), `engine/expressions` (fórmulas sem `eval`), `engine/rules`
    (definições abertas versionadas), `engine/operations` (19 operações, `when` condicional, savepoint por operação);
  - API: campanhas, histórico, ficha do protagonista, turno com SSE (eventos `turn`, `mechanics`, `delta`, `done`, `error`).
- **Frontend** (`frontend/`, Vue 3.5, Vite 8, Pinia 4, Vue Router 5): lista/criação/exclusão de campanhas;
  jogo com narração em tempo real, avisos `[SISTEMA]`/`[TESTE]`/`[ALERTA]`, painel "STATUS" do protagonista
  (barras de recurso, atributos, habilidades, inventário), falhas com "Tentar de novo".
- **Atalhos**: `instalar.cmd` e `iniciar.cmd` (abre Ollama portátil, backend, frontend e navegador).

## Ambiente do usuário (verificado em 2026-11-03/04)
| Item | Situação |
|---|---|
| Windows 11 Pro, Ryzen 5 4600G (só GPU integrada), 13,8 GB RAM | IA local em CPU |
| Python 3.13.3 | ok |
| Node.js | sistema: 20.11.1 (não usado); **projeto: 24.22.2 LTS portátil em `F:\Tools\node-v24.22.2-win-x64`** |
| Ollama | **0.40.14 portátil em `F:\Tools\ollama`**, modelos em `F:\Tools\ollama-models` |
| Modelo instalado | `qwen2.5:1.5b` (986 MB) |
| Disco | C: ~3,3 GB livres (nada instalado no C:); F: ~21 GB livres |
| `F:\Tools\downloads` | zips do Node e do Ollama (~1,7 GB) já extraídos; podem ser apagados pelo usuário |

## Testes executados (resultados reais)
| Data | O quê | Resultado |
|---|---|---|
| 2026-11-04 | backend `pytest` (unit + integração + fluxo completo, FakeProvider) | **206 passed**, 1 deselected (externo) |
| 2026-11-04 | frontend `npm test` (Vitest) | **26 passed** |
| 2026-11-04 | frontend `npm run build` | ok (113 kB JS / 10 kB CSS) |
| 2026-11-04 | `pytest -m external` com Ollama real (`qwen2.5:1.5b`) | **1 passed** |
| 2026-11-04 | manual: `instalar.cmd`, `iniciar.cmd`, backend + Vite pelo proxy | ok |
| 2026-11-04 | **critério da Etapa 1 com IA real**: criar → 2 turnos → desligar → religar → 3º turno | ok (3 turnos `completed`, história completa no contexto) |
| 2026-11-04 | **critério da Etapa 2 com IA real** (motor ligado) | ok: preparação criou 4 atributos + protagonista + local; um teste `1d20` rolado pelo motor (semente gravada); `Força 5→8` aplicada e persistida; operação malformada recusada com motivo no log. Turno ~21 s |

**Não testado por mim**: a interface no navegador com os olhos (não tenho como ver a tela).

## Problemas conhecidos
- **Qualidade com `qwen2.5:1.5b`**: narração razoável com o motor ligado, mas repetitiva; as **escolhas
  mecânicas** do intérprete muitas vezes não fazem sentido (ex.: aumentar Força por um chute). O motor impede
  estados inválidos, não escolhas ruins. Precisa de modelo maior (decisão pendente 1).
- Turno com motor ligado ~21 s nesta máquina (1º turno ~46 s, com a preparação). `AI_MECHANICS=false` volta a ~15 s.
- 5 vulnerabilidades "moderadas" no `npm audit` só em dependência de testes (`@vue/test-utils` → `js-beautify`).
- Recarga de habilidades (cooldown) e efeitos com duração ainda não aplicados (dependem do relógio — Etapa 3/4).

## Decisões pendentes (dependem do dono)
1. **Modelo de IA**: baixar um maior? Tamanhos (página oficial do Ollama, 2026-11-04; desempenho não medido):
   `qwen2.5:3b` (1,9 GB), `gemma3:4b` (3,4 GB), `qwen2.5:7b` (4,7 GB, provável limite desta RAM).
   Ou serviço externo (pode ter custo; exige pesquisa de preços e autorização).
2. **GPU integrada** no Ollama (`OLLAMA_IGPU_ENABLE=1`): testar se acelera?
3. Apagar `F:\Tools\downloads` (~1,7 GB)? Não apaguei por segurança.

## Como testar (passo a passo para o dono)
1. Dois cliques em `F:\Projetos\AI-RPG-Engine\iniciar.cmd`. Abrem 3 janelas pretas (Ollama, backend, frontend) e o navegador.
2. **+ Nova campanha** → título e premissa → **Criar e começar**.
3. **Começar a história**. O 1º turno demora mais (~45 s): a IA cria as regras e o personagem. Devem aparecer
   avisos `[SISTEMA]` e a ficha "STATUS" à direita (no celular, botão "Ficha").
4. Escreva ações (ex.: "Tento escalar o muro"). Testes aparecem como `[TESTE] ... → sucesso/falha`.
5. Feche tudo e abra de novo: **Continuar** deve mostrar a história e a ficha iguais.

## Arquivos principais
Backend: `app/{config.py, persistence, providers, ai, engine, services, api}`, `alembic/versions` (3 migrações),
`tests/{unit, integration, e2e, external}`. Frontend: `frontend/src/{api, stores, views, components, utils, styles}`.
Raiz: `instalar.cmd`, `iniciar.cmd`. Docs: `docs/*.md`.

## Casos da SPEC Parte 22 cobertos por testes
1, 2, 3, 4, 5, 6, 7, 8 (parcial), 9 (parcial: dano/recursos; efeitos na Etapa 4), 18, 19, 20, 24, 25 (parcial), 26.

## Riscos principais
| Risco | Mitigação |
|---|---|
| Escopo muito grande | Etapas pequenas e executáveis; nada marcado pronto sem teste |
| Modelos locais erram JSON e escolhas | Validação + reenvio (D-008/D-026); operações recusadas uma a uma; modelo maior |
| Lentidão com 2 chamadas por turno | Limites de tokens (D-028); `AI_MECHANICS=false`; modelo/hardware melhores |
| Contexto grande demais | Orçamento de tokens; resumos em camadas (Etapa 3.6) |
| IA contradizer fatos antigos | Regras versionadas (pronto); registro canônico (Etapa 3.1) |
