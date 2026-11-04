# DECISIONS — Registro de decisões

Formato: contexto → decisão → alternativas → motivo. Decisões novas vão no final.

---

### D-001 — Backend em Python com Flask
- Decisão: Python 3.12 + Flask + Pydantic v2.
- Alternativas: FastAPI (validação e documentação automáticas, assíncrono nativo); Node.js.
- Motivo: o dono do projeto já estuda Python e usa Flask no trabalho, então o aprendizado serve nos dois lugares. Pydantic cobre a validação. FastAPI continua uma alternativa razoável se o streaming e a concorrência ficarem difíceis em Flask; reavaliar ao fim da Etapa 1.

### D-002 — SQLite agora, PostgreSQL depois
- Decisão: SQLite (WAL + FTS5) via SQLAlchemy 2, migrações com Alembic.
- Alternativas: PostgreSQL desde o início; arquivos JSON.
- Motivo: SQLite não exige instalar servidor; SQLAlchemy permite trocar de banco depois. JSON solto foi descartado pela SPEC (Parte 18.2).

### D-003 — Vue 3 com CSS próprio
- Decisão: Vue 3 + Vite + Pinia, sem framework visual pronto como base.
- Alternativas: Bootstrap; React.
- Motivo: Vue é o que o dono estuda. Bootstrap deixaria a interface com cara genérica, contra a Parte 12.

### D-004 — Definições abertas, operações fechadas
- Decisão: a IA cria definições livres (JSON versionado), mas só altera estado por um catálogo fechado de operações primitivas (ARCHITECTURE.md §5).
- Alternativas: catálogo fechado de habilidades (mata a criatividade); IA altera estado livremente (mata a consistência).
- Motivo: é a forma de atender ao mesmo tempo a liberdade criativa e a consistência sistêmica (SPEC Parte 2.3).

### D-005 — O motor rola os dados
- Decisão: aleatoriedade só pelo módulo `engine/dice`, com seed registrada em `dice_rolls`.
- Motivo: auditoria e reprodução (SPEC 7.2); impede a IA de escolher resultados convenientes.

### D-006 — Intérprete e narrador começam na mesma chamada (SUBSTITUÍDA por D-013)
- Decisão: na Etapa 1–2, uma chamada à IA devolve operações + narração provisória; após o motor processar, uma segunda chamada curta ajusta a narração ao resultado real dos testes.
- Motivo: custo e simplicidade. A arquitetura mantém os papéis separados para dividir depois.

### D-007 — Conteúdo adulto depende do provedor (ajuste à SPEC Parte 14)
- Contexto: várias APIs comerciais, incluindo a da Anthropic, não permitem gerar conteúdo sexual explícito por suas políticas de uso.
- Decisão: as configurações de maturidade existem por campanha, mas cada provedor declara quais categorias suporta; a interface avisa quando a configuração escolhida não é suportada pelo provedor ativo. As regras da Parte 14 sobre idade e violência sexual valem para todos os provedores.
- Motivo: honestidade sobre limitações reais (SPEC princípio 13).

### D-008 — Respostas inválidas da IA são esperadas
- Decisão: toda resposta estruturada passa por validação; inválida → reenvio com a mensagem de erro (máximo configurável de tentativas) → se persistir, a operação é descartada e registrada.
- Motivo: modelos, principalmente locais, erram o formato com frequência.

### D-009 — Sem Docker obrigatório na v1
- Decisão: instalação direta (Python + Node). Dockerfile opcional na Etapa 7.
- Motivo: facilidade de instalação para iniciante.

### D-010 — Recorte da Etapa 1
- Decisão: a Etapa 1 entrega só o ciclo mínimo (criar campanha → turno com IA → salvar → reabrir e continuar), com interface simples, antes de qualquer painel avançado.
- Motivo: SPEC Parte 23; escopo total é muito grande e precisa de uma base comprovada.

### D-011 — Python 3.13 (compatível com 3.12+)
- Contexto: o computador do dono já tem Python 3.13.3 instalado; a arquitetura previa 3.12.
- Decisão: usar o 3.13 já instalado; `pyproject.toml` exige `>=3.12`.
- Alternativas: instalar o 3.12 (trabalho extra, sem ganho).
- Motivo: Flask, SQLAlchemy 2, Alembic e Pydantic 2 suportam 3.13; evita uma instalação para iniciante.

### D-012 — Chamadas à IA nunca acontecem dentro de uma transação do banco
- Contexto: DATABASE.md dizia "cada turno = uma transação". Com IA local em CPU, uma chamada pode levar minutos; no SQLite, uma transação de escrita aberta bloqueia todas as outras gravações nesse tempo.
- Decisão: o turno usa transações curtas. (1) registra o turno com status `processing` e confirma; (2) chama a IA sem transação aberta; (3) aplica operações + eventos + narração em UMA transação. O que precisa ser "tudo ou nada" (a aplicação dos resultados) continua sendo uma transação só.
- Turnos que ficarem em `processing` porque o programa fechou no meio viram `failed` ao reabrir e podem ser repetidos com o mesmo `turn_id`.
- Motivo: evita travamentos e mantém a garantia de não gravar resultado pela metade.

### D-013 — Interpretar, resolver e só então narrar (substitui D-006)
- Contexto: D-006 previa uma narração "provisória" antes do motor rolar os dados, ajustada depois. Isso faz a IA narrar resultados que ainda não existem, e o jogador veria o texto mudar.
- Decisão: Etapa 1 (ainda sem motor de regras): uma chamada só, de narração, com texto em tempo real. Etapa 2 em diante: chamada 1 = intérprete (JSON curto, sem streaming) → motor valida e rola → chamada 2 = narradora (streaming) com os resultados reais.
- Motivo: mesmo número de chamadas que D-006, mas segue a ordem da SPEC 17.5 (a IA narra depois de receber os resultados).

### D-014 — Backups por campanha via exportação, não cópia do arquivo do banco
- Contexto: todas as campanhas ficam no mesmo arquivo SQLite. Copiar e restaurar o arquivo inteiro para desfazer algo em UMA campanha voltaria no tempo TODAS as outras (perda de dados).
- Decisão: snapshot = exportação JSON da campanha (o mesmo formato de "Exportar campanha"); restaurar = apagar as linhas daquela campanha e importar o snapshot, numa transação. Cópia do arquivo inteiro fica só como backup geral do programa.
- Alternativas: um arquivo SQLite por campanha (isola bem, mas complica migrações e a futura troca por PostgreSQL).
- Motivo: isolamento entre campanhas (SPEC 2.1) e compatível com PostgreSQL.

### D-015 — Ordem explícita de turnos e mensagens
- Decisão: `turns.number` (sequencial por campanha, único junto com `campaign_id`) e `messages.seq`. A ordem nunca depende de `created_at`.
- Motivo: dois registros no mesmo instante teriam ordem indefinida; a retomada exata (SPEC 15) exige ordem garantida.

### D-016 — Pastas do backend criadas quando recebem código
- Decisão: a estrutura do ARCHITECTURE.md §4 é o mapa; cada pasta é criada na subtarefa que coloca código nela, não antes.
- Motivo: pastas vazias parecem funcionalidade pronta (SPEC 1.3, princípio 3).

### D-017 — Migrações aplicadas automaticamente ao iniciar
- Decisão: ao iniciar, o backend roda `alembic upgrade head` e cria o usuário local se não existir.
- Alternativas: o usuário rodar `alembic upgrade head` à mão.
- Motivo: instalação simples (RNF-07). O comando manual continua disponível para desenvolvimento.

### D-018 — Quebras de linha padronizadas
- Decisão: `.gitattributes` com `* text=auto eol=lf`; arquivos `.cmd`/`.bat` com CRLF (o `cmd` do Windows exige).

### D-019 — Atalhos de instalação e início; Node portátil no F:
- Decisão: `instalar.cmd` (ambiente Python + `npm install` + `.env`) e `iniciar.cmd` (abre backend e frontend e o navegador).
  Node.js 24 LTS (v24.22.2) em formato portátil em `F:\Tools\node-v24.22.2-win-x64`, cache do npm em `F:\Tools\npm-cache`.
- Alternativas: instalador do Node (grava no C:, quase cheio) ou trocar o PATH do Windows (mudança no sistema).
- Motivo: regras do dono (instalar no F:, não alterar o Windows). Node 24 em vez do 26 porque o 26 virou LTS há dias (2026-10-28).
- Scripts `.cmd` em vez de `.ps1`: o Windows bloqueia scripts PowerShell por padrão.

### D-020 — Frontend: Vue Router + Pinia; SSE lido com fetch
- Decisão: o turno é um `POST` que devolve `text/event-stream`, lido com `fetch` + leitor próprio (`src/api/sse.js`).
  O `EventSource` do navegador só faz `GET`, e o turno precisa enviar o texto do jogador.
- O Vite repassa `/api` para o Flask (sem CORS). Texto da IA é sempre exibido como texto puro, nunca como HTML.

### D-021 — Provedor falso só nos testes; modelo padrão automático
- Decisão: `AI_PROVIDER=fake` é recusado fora de `APP_ENV=test` (SPEC 1.3: sem simulação disfarçada).
  `AI_MODEL` vazio = primeiro modelo instalado no Ollama; nenhum instalado = erro claro com o comando para instalar.

### D-022 — Ollama portátil no F: e modelo pequeno de teste
- Decisão: Ollama em `.zip` oficial (GitHub, v0.40.14) extraído em `F:\Tools\ollama`, sem instalador (não cria atalhos,
  inicialização automática nem entradas no PATH). Modelos em `F:\Tools\ollama-models` (variável `OLLAMA_MODELS`
  definida só ao iniciar o Ollama). Modelo de teste: `qwen2.5:1.5b` (986 MB).
- Regra adotada: até ~1 GB conta como "modelo pequeno" (autorizado para testes). Maiores dependem de autorização do dono.

### D-023 — Repetição de turnos com falha
- Decisão: só a jogada mais recente pode ser repetida; o jogador também pode seguir com uma ação nova.
  Turnos com falha ficam no histórico (marcados "não concluída") e ficam fora do contexto enviado à IA.
- Motivo: repetir um turno antigo colocaria a narração fora de ordem.

### D-024 — `complete_json` fica para a Etapa 2
- Decisão: a interface de provedores da Etapa 1 tem `stream`, `complete` e `list_models`. A resposta estruturada
  (JSON validado, com reenvio do erro — D-008) entra com o papel "intérprete" na Etapa 2, que é quando ela é usada.

### D-025 — Operações condicionais ao resultado de testes
- Contexto: o intérprete propõe todas as operações numa resposta, antes de o motor rolar os dados; mas o dano
  de um ataque depende de o ataque acertar.
- Decisão: toda operação aceita `"when": {"check": "<ref de um check.request anterior>", "success": true|false}`.
  O pipeline aplica só se o teste teve aquele resultado; senão a operação fica `skipped` (sem efeito).
- Alternativas: uma segunda chamada ao intérprete depois dos dados (mais lenta, ~+10 s por turno em CPU).

### D-026 — Reenvio à IA só para erros de formato
- Decisão: JSON inválido ou fora do esquema → reenvio com o erro (até `AI_JSON_ATTEMPTS`). Operação válida no
  formato mas recusada pelas regras (ex.: mana insuficiente) NÃO é reenviada: fica registrada
  (`operation.rejected`) e o narrador é avisado de que "não aconteceu".
- Motivo: cada reenvio custa uma chamada à IA; o motor já impede o dano, e a narração explica a falha.

### D-027 — Preparação da campanha com formato próprio e simples
- Decisão: no 1º turno (sem protagonista), a IA responde um JSON simples (`CampaignSetup`: atributos,
  protagonista, local) que o motor converte em operações. Atributos repetidos são descartados; se nenhum
  vier marcado como recurso, um com nome típico (vida, energia, mana...) é marcado.
- Motivo: medido com `qwen2.5:1.5b`: com operações livres a IA não criava nada; com o formato simples criou.

### D-028 — Limites de tamanho próprios para intérprete (512) e preparação (800 tokens)
- Motivo: medido com Ollama real: sem limite, o intérprete às vezes gerava até o máximo da narração e o JSON
  saía cortado (90 s perdidos por turno).

### D-029 — Testes do fluxo de narração com o motor desligado
- Decisão: a fixture padrão dos testes usa `AI_MECHANICS=false` (Etapa 1); os testes do motor usam
  `mechanics_settings`. Os dois modos são suportados pelo produto (`AI_MECHANICS` no `.env`).

### D-030 — `skill.use` cobra custos de forma atômica
- Decisão: usar habilidade é uma operação; o motor cobra todos os custos declarados na definição (número ou
  fórmula com `level` e atributos) ou nenhum. Recarga (cooldown) fica para a Etapa 4 (depende do relógio do mundo).

### D-031 — Escala comum das relações
- Decisão: dimensões de relacionamento vão de -100 a 100 e mudam no máximo ±50 por acontecimento; toda
  mudança exige a causa (`cause`). Dimensões e rótulos são livres.
- Motivo: uma escala comum deixa a IA consistente entre turnos; o limite por acontecimento evita "amor eterno"
  num único gesto (SPEC 9.1: relações não são recompensas automáticas).

### D-032 — Memória das testemunhas sem chamada à IA
- Decisão: ao fim das mecânicas de cada turno, os NPCs ativos no mesmo local do protagonista ganham uma
  lembrança curta (ação do jogador + resultados). NPCs longe não ficam sabendo.
- Motivo: SPEC 8.2 (só sabe o que presenciou) sem custo extra; lembranças especiais usam `memory.record`.

### D-033 — Busca no passado com FTS5 do SQLite
- Decisão: tabela virtual `memory_fts` (criada à mão na migração; `unicode61 remove_diacritics 2`), acessada só
  por `MemorySearchRepository`, sempre filtrada por `campaign_id`; apagar campanha limpa o índice.
- Limitação: específico do SQLite. Na troca por PostgreSQL, o repositório precisa de outra implementação
  (ex.: `tsvector`). Embeddings ficam como melhoria futura (ARCHITECTURE §7).

### D-034 — Resumos em segundo plano
- Decisão: a cada `AI_SUMMARY_EVERY` turnos (padrão 8) um resumo é gerado numa thread depois do turno; com
  `APP_ENV=test` roda na hora (testes determinísticos). Falha da IA só adia o resumo.

### D-035 — Campanha gerada nasce como rascunho no servidor
- Decisão: `POST /api/campaigns/generate` cria uma campanha com status `draft`; segredos ficam em
  `campaign_intro.gm_secret` e nunca vão para o navegador (nem nas respostas da API). Gerar de novo atualiza o
  mesmo rascunho, preservando os campos marcados; jogadas só depois de `start`.
- Ingredientes de inspiração sorteados pelo motor (semente registrada) para variedade; a IA pode ignorá-los.

### D-036 — Agendamentos são segredo do mestre
- Decisão: `event.schedule` não é narrado nem mostrado ao jogador; apelidos da lista viram ids ao agendar;
  operações agendadas não podem avançar o tempo; cada agendamento dispara uma única vez, em ordem de data.

### D-037 — Fatos canônicos versionados por chave
- Decisão: `canon.assert` recusa chave já existente; `canon.amend` exige motivo e cria versão nova (a antiga
  fica com `is_current=false`). Status: confirmado, rumor ou crença falsa.
