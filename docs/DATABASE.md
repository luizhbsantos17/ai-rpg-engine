# DATABASE — Modelo de dados

Status: modelo inicial da Etapa 0. Colunas podem mudar; toda mudança vira migração Alembic.

## Princípios
- Banco = fonte da verdade.
- Toda tabela de jogo tem `campaign_id` (isolamento entre campanhas).
- Colunas fixas para o que o motor precisa consultar; JSON (`data`) para propriedades livres.
- Nada importante é apagado de verdade: entidades mortas/removidas mudam de `status`;
  fatos e regras alterados ganham nova versão apontando para a anterior.
- IDs são UUID (texto), o que facilita exportar/importar e, no futuro, multiplayer.

## Tabelas

### Plataforma
| Tabela | Campos principais | Observação |
|---|---|---|
| `users` | id, name, created_at | um usuário local na v1 |
| `campaigns` | id, owner_id, title, genre_tags, status, world_clock, rng_seed, created_at, updated_at | |
| `campaign_settings` | id, campaign_id, kind (`experience`/`rules`), data JSON, version, created_at | mudanças de regra versionadas |
| `campaign_intro` | campaign_id, player_visible JSON, gm_secret JSON, version | separa o que o jogador vê dos segredos |

Implementadas na Etapa 1 (migração `2026_11_03_2328-32791f394f68`): `users`, `campaigns`,
`campaign_intro`, `turns`, `messages`, `events`, `ai_requests`.
Etapa 2 (migração `2026_11_03_2353-f2dd50ffa852`): `definitions`, `entities`, `entity_attributes`,
`entity_skills`, `item_instances`, `effects`, `dice_rolls`; e (`2026_11_04_0016-d35448393fd0`)
`turns.mechanics` (resumo das mecânicas aplicadas no turno, para repetição segura).
Etapa 3 (migrações 4 a 9): `canon_facts`, `scheduled_events`, `relationships`, `relationship_events`,
`knowledge`, `npc_memories`, `quests`, `summaries` e a tabela virtual FTS5 `memory_fts` (busca no passado,
criada à mão; D-033). Etapa 4 (migração 10): `disguises`. As demais tabelas abaixo são o plano das próximas etapas. `world_clock` = minutos do mundo desde o início da campanha (inteiro).
`ai_requests.request_messages` guarda as mensagens enviadas à IA (para `/debug show_context`).

### Definições (o "sistema de RPG" de cada campanha)
| Tabela | Campos principais |
|---|---|
| `definitions` | id, campaign_id, kind (`attribute`, `skill`, `item`, `species`, `class`, `effect`, `check_rule`, `death_rule`...), key, version, data JSON, supersedes_id, created_by (`ai`/`admin`/`system`), created_at |

Uma tabela só para todas as definições, diferenciadas por `kind`. O campo `data` segue um
esquema Pydantic por `kind`, com uma parte obrigatória (nome, descrição, regras de cálculo)
e uma parte livre.

### Mundo e entidades
| Tabela | Campos principais |
|---|---|
| `entities` | id, campaign_id, kind (`character`, `creature`, `location`, `faction`, `organization`, `deity`...), name, status, location_id, is_player, player_id, sim_tier, data JSON |
| `entity_attributes` | id, campaign_id, entity_id, definition_key, value (texto), updated_at |
| `entity_skills` | id, campaign_id, entity_id, definition_key, level, data JSON |
| `effects` | id, campaign_id, target_id, definition_key, source_id, intensity, starts_at, ends_at, data JSON |
| `item_instances` | id, campaign_id, definition_key, owner_id, location_id, quantity, data JSON |
| `disguises` | id, campaign_id, entity_id, field, presented_value, power, active |
| `knowledge` | id, campaign_id, observer_id, subject_id, field, known_value, level, source_event_id, updated_at |

### Relações e social
| Tabela | Campos principais |
|---|---|
| `relationships` | id, campaign_id, a_id, b_id, dimensions JSON (confiança, afeto, medo, respeito...), labels JSON |
| `relationship_events` | id, campaign_id, relationship_id, event_id, changes JSON, reason |

Relação é direcional (A → B é diferente de B → A).

### Narrativa, memória e cânone
| Tabela | Campos principais |
|---|---|
| `turns` | id (gerado pelo frontend = chave de idempotência), campaign_id, number (sequencial por campanha), player_input, status (`processing`/`completed`/`failed`), created_at |
| `messages` | id, campaign_id, turn_id, seq (ordem), role (`narration`, `system`, `player`), content, created_at |
| `events` | seq, id, campaign_id, turn_id, type, payload JSON, source (`ai`/`engine`/`admin`/`system`), world_time, created_at |
| `summaries` | id, campaign_id, scope (`scene`/`session`/`arc`), covers_from_seq, covers_to_seq, content |
| `npc_memories` | id, campaign_id, npc_id, event_id, content, importance, world_time |
| `canon_facts` | id, campaign_id, subject, statement, status (`confirmed`/`rumor`/`false`/`superseded`), version, supersedes_id, source_event_id |
| `quests` | id, campaign_id, title, kind, status, giver_id, data JSON |
| `scheduled_events` | id, campaign_id, due_world_time, payload JSON, status |
| `dice_rolls` | id, campaign_id, turn_id, expression, seed, result, context JSON |

Busca de texto: tabelas virtuais FTS5 sobre `events`, `summaries`, `npc_memories`, `canon_facts`.

### Operação e auditoria
| Tabela | Campos principais |
|---|---|
| `ai_requests` | id, campaign_id, turn_id, role, provider, model, tokens_in, tokens_out, cost_estimate, duration_ms, error |
| `admin_audit` | id, campaign_id, command, result, undo_payload JSON, created_at |
| `snapshots` | id, campaign_id, label, file_path, events_seq, created_at |
| `images` | id, campaign_id, entity_id, prompt_hash, file_path, provider, created_at |

## Persistência e recuperação
- SQLite em modo WAL (mais seguro contra corrupção ao fechar o programa).
- A aplicação dos resultados de um turno = uma transação. Falha no meio desfaz tudo.
  Chamadas à IA ficam fora de transações (D-012).
- Ordem de turnos e mensagens por `turns.number` e `messages.seq`, nunca por horário (D-015).
- Snapshots: exportação JSON da campanha em `data/backups/`, automática a cada N turnos e antes
  de comandos destrutivos. Restaurar afeta só aquela campanha (D-014).
- Backup geral: cópia do arquivo do banco inteiro (todas as campanhas), feita pelo usuário ou pelo programa.
- Exportar campanha = arquivo JSON com todas as tabelas filtradas por `campaign_id` + versão do esquema.

## Migrações
- Alembic gera arquivos de migração em `backend/alembic/versions/`.
- Nunca editar o banco à mão; sempre criar migração.
