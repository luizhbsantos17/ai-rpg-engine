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

Na Etapa 1 (sem motor de regras ainda) há só a chamada de narração. A partir da Etapa 2,
o passo 4 (intérprete, JSON) e o passo 8 (narradora, streaming) são chamadas separadas,
e a narração sempre vem depois dos resultados reais (DECISIONS D-013).

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
