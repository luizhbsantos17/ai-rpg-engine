# CHANGELOG

## [0.4.0] — Etapa 4 (concluída)
- Avaliação, ocultação e falsificação (`knowledge.assess`, `disguise.*`); painel "Personagens conhecidos".
- Regras de morte por universo aplicadas pelo motor (permanente, desmaio, ressurreição, reencarnação, narrativa).
- Recarga de habilidades no tempo do mundo.
- Simulação de NPCs relevantes fora de cena e eventos mundiais em passagens longas de tempo.
- Teste do critério: duas campanhas com sistemas de regras muito diferentes lado a lado.

## [0.3.0] — Etapa 3 (concluída)
- Registro canônico versionado (fatos confirmados, rumores, crenças falsas); fatos iniciais e regras de morte.
- Relógio do mundo (`time.advance`), acontecimentos agendados com operações, efeitos com duração.
- Relacionamentos direcionais multidimensionais com causa e histórico.
- Conhecimento por observador e memória individual; testemunhas lembram o que viram.
- Missões (principais, secundárias, ocultas, falháveis) e diário na interface.
- Memória em camadas: resumos em segundo plano + busca FTS5 no passado, no contexto da IA.
- Geração aleatória de campanhas com rascunho no servidor, manter campos, ingredientes do motor; tela nova.
- Turmas/grupos com personalidade, objetivo, laço e atributos próprios.
- Testado com Ollama real: geração de campanha em 7–9 s.

## [0.2.0] — Etapa 2 (concluída)
- Turno em duas fases (D-013): preparação da campanha (1º turno), intérprete com JSON validado e reenvio
  do erro, motor aplica operações, narrador recebe os fatos; repetição segura via `turns.mechanics`.
- Operações condicionais (`when`) e `skill.use` (cobra custos tudo-ou-nada).
- Ficha do protagonista (API + painel "STATUS") e avisos [SISTEMA]/[TESTE]/[ALERTA] no chat.
- `AI_MECHANICS` e `AI_JSON_ATTEMPTS`; limites próprios de tokens para intérprete e preparação.
- Correção: valor "anterior" errado nas operações de atributo.
- Testado com Ollama real (`qwen2.5:1.5b`): operações aplicadas e persistidas; dados rolados pelo motor.
- Motor: `engine/dice` (sementes registradas e reproduzíveis), `engine/expressions` (fórmulas seguras, Decimal
  com 100 dígitos), `engine/rules` (definições abertas versionadas), `engine/operations` (18 operações primitivas
  com validação, savepoint por operação e registro no log).
- Tabelas: definitions, entities, entity_attributes, entity_skills, item_instances, effects, dice_rolls.
- Prompt do narrador com regras de formato mais explícitas.

## [0.1.0] — Etapa 1 (concluída)
- Subtarefa 9: Ollama 0.40.14 portátil + `qwen2.5:1.5b`; teste externo e critério da Etapa 1 verificados com IA real.
- Subtarefa 10: README com instalação e uso reais; `instalar.cmd`/`iniciar.cmd`; documentação atualizada.
- Subtarefa 8: teste de fluxo completo com reinício do programa.
- Subtarefa 7: frontend Vue 3 + Vite (lista, criação, jogo com SSE, falhas repetíveis).
- Subtarefa 6: orquestrador de turno idempotente; API de campanhas e turnos.
- Subtarefa 5: provedores (base, fake, ollama).
- Subtarefa 4: repositórios com filtro obrigatório por campaign_id.
- Subtarefa 3: SQLAlchemy + Alembic, primeira migração.
- Subtarefa 2: configuração (`app/config.py`) lendo `.env` com validação; fábrica Flask `create_app`;
  rota `GET /api/health`; erros da API em JSON. 22 testes passando.
- Subtarefa 1: `backend/pyproject.toml`, pacote `app`, ambiente virtual e pytest com teste mínimo (2 testes passando).
- Revisão da arquitetura contra a SPEC: decisões D-011 a D-016 (Python 3.13, transações curtas,
  narrar depois de resolver, backups por campanha, ordem explícita de turnos, pastas criadas sob demanda).
- Ramo Git principal renomeado para `main`.

## [0.0.1] — Etapa 0
- Documentação inicial de arquitetura, banco de dados, decisões, requisitos, provedores e comandos administrativos.
- Sem código ainda.
