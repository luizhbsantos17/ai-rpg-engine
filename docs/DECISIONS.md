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
