# ARCHITECTURE — Arquitetura do AI RPG Engine

Status: proposta da Etapa 0, a ser confirmada durante a Etapa 1.
Termos técnicos são explicados entre parênteses na primeira vez que aparecem.

---

## 1. A ideia central em uma frase

A IA **propõe**, o motor **decide e registra**, a IA **narra o resultado**.

A IA tem liberdade para inventar mundos, habilidades e regras, mas nunca mexe no
banco de dados. Ela devolve uma lista de *operações* (pedidos estruturados, como
"aplicar 12 de dano em Fulano"). O motor confere se cada operação é válida,
aplica, guarda no banco e só então a IA descreve o que aconteceu.

---

## 2. Visão geral dos componentes

```
┌──────────────────────── FRONTEND (Vue 3) ────────────────────────┐
│ Tela inicial · Campanhas · Chat narrativo · Painéis de RPG · Admin │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP/JSON (API REST) + SSE (texto em tempo real)
┌───────────────────────────────┴──────────────────────────────────┐
│                       BACKEND (Python / Flask)                     │
│                                                                    │
│  API ──► Roteador de entrada ──┬──► Interpretador /admin /debug    │
│                                │                                   │
│                                └──► Orquestrador de turno          │
│                                      │                             │
│      ┌───────────────┬──────────────┼───────────────┐             │
│      ▼               ▼              ▼               ▼             │
│  Construtor de   Camada de IA   MOTOR DE RPG    Simulação do      │
│  contexto        (provedores)   (operações,     mundo (NPCs,      │
│  (memória)                      regras, dados)  tempo, eventos)   │
│      │                              │                              │
│      └──────────────┬───────────────┘                              │
│                     ▼                                              │
│              Persistência (repositórios + transações)              │
└─────────────────────┬────────────────────────────────────────────┘
                      ▼
        Banco de dados (SQLite local → PostgreSQL no futuro)
```

Definições rápidas:
- **API REST**: o jeito como o frontend conversa com o backend, por endereços como `/api/campaigns`.
- **SSE** (Server-Sent Events): permite o backend ir mandando o texto da narração aos poucos, enquanto a IA escreve.
- **Repositório**: a única camada de código que lê e grava no banco. O resto do sistema pede dados a ela.
- **Transação**: um conjunto de gravações que acontece por inteiro ou não acontece. Se algo falhar no meio, nada é gravado.

---

## 3. Tecnologias escolhidas (resumo — justificativas em DECISIONS.md)

| Camada | Escolha | Motivo curto |
|---|---|---|
| Backend | Python 3.12+ (usando 3.13) + Flask | Mesmo ecossistema que o dono do projeto já estuda; maduro e simples |
| Validação de dados | Pydantic v2 | Valida as operações propostas pela IA com esquemas (regras de formato) |
| Acesso ao banco | SQLAlchemy 2 + Alembic | Permite trocar SQLite por PostgreSQL sem reescrever; Alembic versiona o esquema |
| Banco local | SQLite (modo WAL) com FTS5 | Zero instalação; FTS5 dá busca de texto nas memórias |
| Frontend | Vue 3 + Vite + Pinia + CSS próprio | Vue é o que o dono já estuda; CSS próprio para identidade visual de RPG |
| Testes | pytest (backend), Vitest (frontend) | Padrões das duas linguagens |
| IA local | Ollama | Servidor local de modelos, gratuito |
| IA externa | Adaptadores: compatível-OpenAI, Anthropic | O formato compatível-OpenAI cobre vários provedores de uma vez |

Docker é opcional nesta fase (facilita a hospedagem futura, mas complica a instalação para iniciante).

### 3.1. Convenções já implementadas
- **Configuração** (`app/config.py`): variável de ambiente real > `.env` na raiz > padrão.
  Caminhos relativos são resolvidos a partir da raiz do projeto. Em `production`, valores
  de exemplo de `APP_SECRET_KEY`/`ADMIN_PASSWORD` são recusados. Segredos não aparecem em logs.
- **Fábrica da aplicação** (`app/__init__.py: create_app`): recebe as configurações prontas,
  o que permite aos testes usar pasta de dados temporária e nunca ler o `.env` real.
- **API**: tudo sob `/api`. Erros sempre em JSON: `{"error": {"code", "name", "message"}}`.
  Erros inesperados respondem 500 sem detalhes internos (o detalhe vai para o log).
- O servidor escuta só em `127.0.0.1` (acessível apenas do próprio computador).
- **Inicialização** (`app/services/startup.py`): aplica migrações, garante o usuário local, marca como
  `failed` turnos que ficaram em `processing` (programa fechado no meio) e monta os serviços.

### 3.2. Módulos implementados na Etapa 1
| Módulo | Responsabilidade |
|---|---|
| `app/persistence/models/` | tabelas (`platform.py`, `narrative.py`, `audit.py`) |
| `app/persistence/db.py` | conexão (SQLite WAL + chaves estrangeiras), `Database.transaction()` |
| `app/persistence/repositories/` | única porta de acesso aos dados; filtro obrigatório por `campaign_id` |
| `app/providers/` | `base.py` (interface + streaming), `fake.py` (só testes), `ollama.py`, `registry.py` |
| `app/ai/prompts/narrator.py` | regras do narrador (SPEC Parte 11) + dados da campanha |
| `app/ai/context/narration.py` | contexto com orçamento de tokens (histórico mais recente que couber) |
| `app/ai/orchestrator/turns.py` | pipeline do turno, idempotência e recuperação de falhas |
| `app/services/campaigns.py` | criar, listar, abrir, histórico, excluir (com confirmação) |
| `app/api/` | rotas HTTP, validação (Pydantic), erros em JSON, SSE |
| `frontend/src/api/` | chamadas ao backend e leitor de SSE |
| `frontend/src/stores/` | estado da lista de campanhas e da partida (Pinia) |
| `frontend/src/views/`, `components/` | telas e peças visuais |

### 3.2.1. Módulos do motor (Etapa 2)
| Módulo | Responsabilidade |
|---|---|
| `app/engine/dice/` | notação de dados, rolagem com semente, `derive_seed` (única fonte de aleatoriedade) |
| `app/engine/expressions/` | avaliador de fórmulas sem `eval` (árvore `ast` + lista do que é permitido; Decimal, 100 dígitos) |
| `app/engine/rules/` | esquemas de definições (parte obrigatória + livre), valores por tipo, variáveis para fórmulas |
| `app/engine/operations/` | catálogo (Pydantic), contexto (apelidos, "player"), aplicadores, pipeline com savepoint |
| `app/engine/notifications.py` | texto para o narrador (verdade) e avisos do jogador (só o protagonista) |
| `app/ai/structured.py` | JSON com esquema + validação + reenvio do erro |
| `app/ai/context/game_state.py` | regras, ficha do protagonista e cena para o intérprete (apelidos e1, i1...) |
| `app/ai/orchestrator/mechanics.py` | preparação da campanha → intérprete → motor → resumo guardado no turno |
| `app/services/sheet.py` | ficha do protagonista (+ tempo do mundo, efeitos, missões visíveis) |

### 3.2.2. Módulos da Etapa 3 (narrativa e mundo)
| Módulo | Responsabilidade |
|---|---|
| `app/engine/time.py` | durações ("4h", "2d") e formato do relógio do mundo |
| `app/engine/witness.py` | memória das testemunhas e notas "o que cada NPC presente sabe" para o narrador |
| `app/persistence/repositories/memory.py` | resumos e busca FTS5 no passado (por campanha) |
| `app/services/summaries.py` | resumidor a cada N turnos, em segundo plano |
| `app/services/generation.py` + `app/ai/prompts/generator.py` | geração aleatória de campanhas (rascunho, manter campos, ingredientes) |
| `app/ai/schemas/setup.py` | preparação: atributos, protagonista, local, fatos iniciais (incl. morte), companheiros |

Contexto da IA por turno (o banco guarda tudo; vai só o necessário): regras do papel; campanha (título,
premissa, segredos do mestre); fatos canônicos; últimos resumos; trechos antigos achados pela busca;
estado da cena (tempo, protagonista, presentes com personalidade/objetivo/relação/conhecimento, missões);
histórico recente; ação atual; e, para o narrador, os resultados reais do motor e o que cada NPC presente sabe.

### 3.2.3. Módulos da Etapa 4
| Módulo | Responsabilidade |
|---|---|
| `app/engine/operations/handlers/assessment.py` | avaliação × ocultação/falsificação |
| `app/engine/death.py` | regras de morte por universo |
| `app/ai/orchestrator/simulation.py` + `app/ai/prompts/simulation.py` | NPCs relevantes fora de cena e eventos mundiais |
| `app/services/known.py` | personagens conhecidos (só o que o protagonista sabe) |

### 3.3. API HTTP (Etapa 1)
| Método e endereço | O que faz |
|---|---|
| `GET /api/health` | servidor no ar |
| `GET /api/campaigns` | lista as campanhas do usuário (mais recentes primeiro) |
| `POST /api/campaigns` | cria: `{title, premise?, genre_tags?}` |
| `GET /api/campaigns/<id>` | dados visíveis da campanha (nunca os segredos do mestre) |
| `GET /api/campaigns/<id>/history?after_seq=n` | turnos e mensagens, para retomar exatamente |
| `DELETE /api/campaigns/<id>` | exclui: exige `{confirm_title}` igual ao título |
| `GET /api/campaigns/<id>/sheet` | ficha do protagonista, tempo do mundo e missões visíveis |
| `POST /api/campaigns/generate` | gera (ou gera de novo: `draft_id`, `keep`) campanha aleatória como rascunho |
| `PATCH /api/campaigns/<id>` | ajusta título/premissa/gêneros de um rascunho |
| `POST /api/campaigns/<id>/start` | começa o rascunho (passa a aceitar jogadas) |
| `GET /api/campaigns/<id>/known` | personagens conhecidos pelo protagonista (falso aparece como confirmado) |
| `POST /api/campaigns/<id>/turns` | joga: `{turn_id (UUID do frontend), input}` → stream SSE |

Eventos do stream do turno: `turn` (turno registrado + mensagem do jogador), `mechanics` (avisos
`[SISTEMA]`/`[TESTE]` do motor), `delta` (pedaço da narração), `done` (narração salva) ou `error`
(`message`, `retryable`). Erros do pedido (404, 409, 400) voltam como JSON comum, antes do stream.

---

## 4. Estrutura de diretórios planejada

Este é o mapa completo. Cada pasta só é criada quando recebe código (D-016).

```
ai-rpg-engine/
├── CLAUDE.md                  instruções para o Claude Code
├── README.md
├── PROJECT_STATUS.md
├── CHANGELOG.md
├── .env.example
├── docs/
│   ├── SPEC.md                especificação original
│   ├── ARCHITECTURE.md        este arquivo
│   ├── REQUIREMENTS.md
│   ├── DATABASE.md
│   ├── AI_PROVIDERS.md
│   ├── ADMIN_COMMANDS.md
│   └── DECISIONS.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic/               migrações do banco
│   ├── app/
│   │   ├── __init__.py        cria a aplicação Flask
│   │   ├── config.py          lê o .env
│   │   ├── api/               rotas HTTP (campaigns, play, sheets, settings, admin)
│   │   ├── auth/              usuários, dono da campanha, permissões, senha admin
│   │   ├── campaigns/         criar, listar, gerar, exportar, importar, backup
│   │   ├── engine/            MOTOR DE RPG
│   │   │   ├── operations/    catálogo de operações primitivas + aplicação
│   │   │   ├── validation/    validadores de operações
│   │   │   ├── rules/         definições de atributos, habilidades, regras (versionadas)
│   │   │   ├── expressions/   avaliador seguro de fórmulas
│   │   │   ├── dice/          aleatoriedade com seed registrada
│   │   │   ├── checks/        testes (perícia, resistência, etc.)
│   │   │   ├── combat/
│   │   │   ├── progression/
│   │   │   ├── knowledge/     visibilidade, avaliação, ocultação, falsificação
│   │   │   └── death/
│   │   ├── world/
│   │   │   ├── npcs/          estado, agenda, níveis de simulação
│   │   │   ├── relationships/
│   │   │   ├── quests/
│   │   │   ├── events/        eventos mundiais e agendados
│   │   │   ├── time/          relógio do mundo
│   │   │   └── canon/         registro canônico (fatos e regras confirmados)
│   │   ├── memory/            resumos, busca, memória individual de NPCs
│   │   ├── ai/
│   │   │   ├── orchestrator/  pipeline do turno
│   │   │   ├── context/       seleciona o que mandar para a IA
│   │   │   ├── prompts/       textos-base dos papéis (narrador, intérprete, NPC...)
│   │   │   └── schemas/       formato JSON que a IA deve devolver
│   │   ├── providers/         base.py, ollama.py, openai_compat.py, anthropic.py, fake.py
│   │   ├── images/            geração opcional de imagens
│   │   ├── admin/             interpretador de comandos /admin e /debug
│   │   └── persistence/       modelos, repositórios, unidade de trabalho
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/               campanhas completas simuladas
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api/               chamadas ao backend
│       ├── stores/            estado da interface (Pinia)
│       ├── views/             telas
│       ├── components/        painéis, janelas de status, notificações
│       └── styles/            identidade visual
└── data/                      (fora do Git) banco, backups, imagens
```

---

## 5. Como criatividade e validação convivem (o coração do projeto)

### 5.1. Definições abertas, operações fechadas

- **Definições** (atributos, habilidades, itens, espécies, regras de teste, regras de morte)
  são **abertas**: a IA pode criar quantas quiser, com propriedades livres guardadas em JSON.
  Toda definição nova é registrada, versionada e passa a valer na campanha.
- **Operações** são **fechadas**: um conjunto pequeno de verbos que o motor entende e valida.
  Qualquer mecânica inventada precisa ser expressa combinando esses verbos.

Assim a IA pode criar a habilidade "Eco do Destino" com efeitos inéditos, mas o efeito
dela vira, por exemplo, `effect.apply` + `attribute.modify` + `knowledge.record`.

### 5.2. Catálogo inicial de operações primitivas

| Operação | O que faz |
|---|---|
| `entity.create` / `entity.update` / `entity.remove` | personagens, criaturas, locais, facções |
| `definition.create` / `definition.amend` | cria ou altera (versionando) atributo, habilidade, item, regra |
| `attribute.set` / `attribute.modify` | muda valor de atributo, com motivo |
| `resource.spend` / `resource.restore` | mana, energia, vida, qualquer recurso definido |
| `effect.apply` / `effect.remove` | efeitos com duração, gatilhos e intensidade |
| `skill.grant` / `skill.revoke` / `skill.evolve` | habilidades de uma entidade |
| `item.create` / `item.transfer` / `item.destroy` | inventário (sem duplicação: cada item tem dono único) |
| `check.request` | pede ao motor um teste; **o motor rola**, a IA nunca escolhe o resultado |
| `relationship.change` | muda dimensões de relação, sempre com o acontecimento que causou |
| `knowledge.record` | registra o que um observador sabe, acha ou foi enganado a achar |
| `canon.assert` / `canon.amend` | fatos do mundo; alterar cria nova versão, não apaga a antiga |
| `quest.create` / `quest.update` | missões e etapas |
| `event.record` / `event.schedule` | acontecimentos agora ou no futuro do relógio do mundo |
| `time.advance` | avança o relógio do mundo |
| `entity.move` | muda localização |

O catálogo pode crescer, mas cada verbo novo exige validador e testes.

**Implementado** (`app/engine/operations/`, 33 operações):
- Etapa 2: `definition.create/amend`, `entity.create/update/remove/move`, `attribute.set/modify`,
  `resource.spend/restore`, `skill.grant/revoke/evolve/use`, `item.create/transfer/destroy`, `check.request`,
  `event.record`.
- Etapa 3: `canon.assert/amend`, `time.advance`, `event.schedule`, `effect.apply/remove`,
  `relationship.change`, `knowledge.record`, `memory.record`, `quest.create/update`.
- Etapa 4: `disguise.apply/remove`, `knowledge.assess` (D-038); `skill.use` com recarga; regras de morte
  aplicadas pelo motor após cada operação (`app/engine/death.py`, D-040); `sim_tier` em entidades.

Regras do pipeline: cada operação é aplicada num *savepoint* (se for recusada, só ela é desfeita, inclusive
apelidos `ref`); toda operação aceita `reason` e `when` (condição sobre um teste anterior, D-025); toda
operação aplicada ou recusada fica no log de eventos.

### 5.3. Fórmulas seguras

Regras como "dano = Força × 1.5 + nível da habilidade" são guardadas como texto e
calculadas por um **avaliador de expressões seguro** (só aceita contas, variáveis
conhecidas e funções permitidas como `min`, `max`, `roll`). Nunca se usa `eval` do Python,
porque uma fórmula maliciosa ou errada poderia executar qualquer código.

### 5.4. Escalas sem teto

Atributos podem ser número inteiro, decimal, número muito grande, faixa nominal
("Rank S"), ou conceitual (sem número). Cada definição de atributo declara seu tipo.
Valores numéricos usam `Decimal` em texto no banco para não estourar limites.

---

## 6. O fluxo de um turno

```
1. Jogador envia mensagem
2. Roteador: começa com /admin ou /debug? → interpretador de comandos (fim)
3. Construtor de contexto monta o pacote para a IA (ver seção 7)
4. IA "intérprete" devolve JSON: intenção + operações propostas + testes pedidos
5. Validação: formato (Pydantic) → referências existem? → regras permitem? → custo pago?
   - Inválido: devolve o erro para a IA corrigir (até N tentativas) ou descarta a operação
6. Motor resolve os testes pedidos (dados com seed registrada)
7. Aplicação em UMA transação: estado atualizado + eventos gravados no log
8. IA "narradora" recebe resultados + o que o protagonista pode perceber → escreve a narração
9. Narração salva e enviada ao frontend aos poucos (SSE)
10. Passo de simulação do mundo (NPCs, eventos agendados) conforme intensidade configurada
```

Com `AI_MECHANICS=true` (padrão, Etapa 2), o passo 4 (intérprete, JSON) e o passo 8 (narradora,
streaming) são chamadas separadas, e a narração vem depois dos resultados reais (D-013). No 1º turno de
uma campanha sem protagonista, antes do intérprete roda a **preparação** (D-027). Com
`AI_MECHANICS=false`, só há a chamada de narração (fluxo da Etapa 1).

Repetição segura: as operações do intérprete e o resumo (`turns.mechanics`) são gravados na mesma
transação; se a narração falhar e o turno for repetido, o motor não aplica nada de novo.

**Transações curtas** (D-012): nenhuma chamada à IA acontece com transação do banco aberta.
O turno é registrado como `processing`, a IA é chamada, e só o passo 7 (aplicação) é a
transação "tudo ou nada". Turnos interrompidos viram `failed` ao reabrir e podem ser repetidos.

**Idempotência** (fazer a mesma coisa duas vezes não duplica o efeito): cada turno tem um
identificador único gerado pelo frontend. Se a requisição for repetida por falha de rede,
o backend reconhece o identificador e devolve o resultado já gravado.

---

## 7. Memória e contexto

O banco guarda tudo; a IA recebe só o necessário.

| Camada | Onde fica | Como chega à IA |
|---|---|---|
| Estado atual | tabelas de entidades, atributos, inventário, local | sempre, filtrado pela cena |
| Log de eventos | `events` | últimos eventos da cena |
| Memória narrativa | `summaries` (por cena, sessão, arco) | resumo do arco atual + anterior |
| Memória histórica | busca FTS5 em eventos e resumos | consultas por palavras da cena |
| Memória de NPC | `npc_memories` + `knowledge` | só dos NPCs presentes |
| Registro canônico | `canon_facts`, `rule_definitions` | regras e fatos ligados à cena |

Regra de ouro: o contexto montado para um NPC **só** contém o que aquele NPC sabe.
O contexto do narrador contém a verdade, mas com instrução explícita do que o
protagonista pode perceber.

Busca por similaridade de significado (embeddings) fica como melhoria futura e opcional.

---

## 8. Verdade, conhecimento e aparência

Três camadas para cada informação sobre uma entidade:
1. **Verdade**: o valor real, nas tabelas de estado.
2. **Apresentação**: o que a entidade mostra ao mundo. Disfarces e falsificações são registros
   em `disguises` que sobrepõem campos específicos.
3. **Conhecimento do observador**: tabela `knowledge`, uma linha por (observador, assunto, campo),
   com valor conhecido, nível (desconhecido / estimado / parcial / confirmado / falso) e origem.

Uma avaliação é um `check.request` em que o poder da habilidade de avaliação disputa
com a ocultação do alvo. O resultado gera linhas em `knowledge`. A interface só mostra
ao jogador o que estiver em `knowledge` para o protagonista.

---

## 9. NPCs e simulação

Níveis de simulação:
- **Nível 0 — em cena**: IA a cada turno, com memória própria.
- **Nível 1 — relevantes**: atualizados pela IA em lote quando o relógio avança bastante.
- **Nível 2 — distantes**: avançam por agenda e regras simples, sem IA; resumo ocasional pela IA.
- **Nível 3 — dormentes**: congelados até voltarem a ser relevantes.

Ao subir de nível, o NPC recebe um "recapitulativo" do que fez fora de cena, gravado como
eventos, para não haver contradição.

O tempo só anda por `time.advance`. Fechar o programa não avança o relógio.

---

## 10. Provedores de IA

Interface comum (`providers/base.py`): enviar mensagens, pedir resposta em JSON,
receber texto em partes, informar tokens usados. Cada provedor é um adaptador.
`FakeProvider` devolve respostas roteirizadas, usado só em testes.

Cada papel (narrador, intérprete, NPC, gerador de mundo, resumidor) pode usar um
modelo diferente, configurado por campanha. Toda chamada é registrada em `ai_requests`
(modelo, tokens, custo estimado quando conhecido, duração, erro).

Antes de usar um serviço pago, o sistema avisa e respeita o limite de gasto configurado.

---

## 11. Modo administrador

- Entrada separada no backend (`/api/admin`), protegida por senha do `.env`.
- O interpretador reconhece só comandos que começam com `/admin` ou `/debug` e estão no catálogo.
- Comandos de alteração viram operações do mesmo pipeline, com origem `admin`, e ficam no log.
- Comandos destrutivos exigem confirmação; desfazer usa operações inversas ou snapshot.

---

## 12. Preparação para hospedagem e multiplayer

Já na primeira versão: tabela `users` (com um usuário local), `campaigns.owner_id`,
`player_id` nos personagens controlados por jogador, e todo acesso verificando permissão.
Não há implementação de multiplayer, só ausência de bloqueios para ele.
