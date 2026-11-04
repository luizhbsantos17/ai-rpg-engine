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

### D-006 — Intérprete e narrador começam na mesma chamada
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
