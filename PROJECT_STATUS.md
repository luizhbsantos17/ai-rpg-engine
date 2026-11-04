# PROJECT_STATUS

Última atualização: 2026-11-04 (sessão autônoma da madrugada).

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída (decisões D-001 a D-024) |
| 1 — Fundação | **concluída**: critério verificado com Ollama real (falta só o usuário olhar a interface no navegador) |
| 2 — Motor de RPG | **em andamento**: dados, fórmulas, tabelas e pipeline de operações prontos; falta ligar à IA e à interface |
| 3 a 7 | não iniciadas |

## Última tarefa concluída
Etapa 2.4 — pipeline de operações do motor (validar → aplicar em savepoint → registrar no log).

## Próxima tarefa: Etapa 2.5 — IA intérprete + turno em duas chamadas (D-013)
1. `complete_json` nos provedores: pedir JSON, validar com Pydantic, reenviar o erro à IA (máx. N tentativas, D-008).
2. Prompt do intérprete: recebe estado relevante (protagonista, entidades da cena, definições) e devolve
   `{"operations": [...]}`; operações recusadas voltam com o motivo.
3. Orquestrador: intérprete → `apply_operations` (na transação do turno, com os testes rolados pelo motor) →
   narrador recebe os resultados reais → narração em streaming.
4. Criação do protagonista e das regras iniciais da campanha (operações `definition.create`/`entity.create` geradas pela IA).
5. API e interface: ficha do protagonista (atributos, recursos, habilidades, inventário) e mensagens `[SISTEMA]`
   para operações aplicadas (nova habilidade, item recebido, teste rolado...).
6. Testes: fluxo com FakeProvider roteirizando JSON válido/inválido; teste externo com Ollama.
Critério da Etapa 2 (SPEC Parte 23): as operações do RPG modificam dados reais e persistentes.

## O que existe e funciona (com testes)
- **Backend** (`backend/`, Python 3.13, Flask 3.1, SQLAlchemy 2.1, Alembic 1.20, Pydantic 2.14, httpx):
  - configuração por `.env` com validação; migrações automáticas ao iniciar; usuário local;
  - banco SQLite (WAL, chaves estrangeiras, savepoints) com 2 migrações e 14 tabelas;
  - repositórios com filtro obrigatório por `campaign_id` (+ testes guardiões no código-fonte);
  - provedores `fake` (só testes) e `ollama` (real, com streaming);
  - turno idempotente com recuperação de falhas e retomada após reiniciar;
  - API de campanhas e turnos com SSE;
  - **motor (Etapa 2, ainda não ligado ao turno)**: `engine/dice` (semente registrada, reproduzível),
    `engine/expressions` (fórmulas sem `eval`, Decimal sem teto), `engine/rules` (definições abertas
    versionadas, valores por tipo), `engine/operations` (18 operações primitivas validadas e registradas).
- **Frontend** (`frontend/`, Vue 3.5, Vite 8, Pinia 4, Vue Router 5): lista/criação/exclusão de campanhas e
  tela de jogo com narração em tempo real, falhas com "Tentar de novo". Build de produção ok.
- **Atalhos**: `instalar.cmd` e `iniciar.cmd` (abre Ollama portátil, backend, frontend e navegador).

## Ambiente do usuário (verificado em 2026-11-03/04)
| Item | Situação |
|---|---|
| Windows 11 Pro, Ryzen 5 4600G (só GPU integrada), 13,8 GB RAM | IA local só com modelos pequenos/médios, em CPU |
| Python 3.13.3 | ok |
| Node.js | sistema: 20.11.1 (antigo, não usado); **projeto: 24.22.2 LTS portátil em `F:\Tools\node-v24.22.2-win-x64`** |
| Ollama | **0.40.14 portátil em `F:\Tools\ollama`**, modelos em `F:\Tools\ollama-models` |
| Modelo instalado | `qwen2.5:1.5b` (986 MB) |
| Disco | C: ~3,3 GB livres (nada foi instalado no C:); F: ~21 GB livres após Node + Ollama + modelo |
| Pastas no F:\Tools | `downloads\` (zips do Node e do Ollama, ~1,7 GB, podem ser apagados pelo usuário), `npm-cache\` |

## Testes executados (resultados reais)
| Data | O quê | Resultado |
|---|---|---|
| 2026-11-04 | backend `pytest` (unit + integração + fluxo completo, FakeProvider) | **186 passed**, 1 deselected (externo) |
| 2026-11-04 | frontend `npm test` (Vitest) | **19 passed** |
| 2026-11-04 | frontend `npm run build` | ok (109 kB JS / 7 kB CSS) |
| 2026-11-04 | `pytest -m external` com Ollama real (`qwen2.5:1.5b`) | **1 passed** ("Pronto", 3 tokens, 4,2 s com carga) |
| 2026-11-04 | manual: backend + Vite juntos, API pelo proxy, SSE, falha sem Ollama | ok: erro claro e repetível, sem duplicar mensagem |
| 2026-11-04 | manual: `instalar.cmd` e `iniciar.cmd` | ok (portas 5000 e 5173 respondendo) |
| 2026-11-04 | **critério da Etapa 1 com IA real**: criar campanha → 2 turnos → desligar backend → religar → 3º turno | ok: 3 turnos `completed`; no 3º a IA recebeu as 2 jogadas e narrações anteriores. Velocidade 25–28 tokens/s, 1º pedaço em 2,6–5 s, turno de 16–23 s |

**Não testado por mim**: a interface no navegador com os olhos (não tenho como ver a tela).
Ver "Como testar" abaixo.

## Problemas conhecidos
- **Qualidade da narração com `qwen2.5:1.5b` é fraca** (repete frases, escreve falas do protagonista,
  usa "-" no início de parágrafos). A integração funciona; o modelo é pequeno demais. Ver decisões pendentes.
- 5 vulnerabilidades "moderadas" no `npm audit`, todas em dependência só de testes
  (`@vue/test-utils` → `js-beautify` → `glob`/`minimatch`); não entram no programa. Reavaliar quando houver versão corrigida.
- O motor de regras ainda não está ligado ao turno: o narrador é instruído a não inventar números.

## Decisões pendentes (dependem do dono)
1. **Modelo de IA para narrar**: baixar um maior? Opções medidas só em tamanho (desempenho não testado):
   `qwen2.5:3b` (1,9 GB), `gemma3:4b` (3,4 GB), `qwen2.5:7b` (4,7 GB, provavelmente o limite desta RAM).
   Ou usar um serviço externo (pode ter custo; precisa de pesquisa de preços e autorização).
2. **Testar a GPU integrada** no Ollama (`OLLAMA_IGPU_ENABLE=1`)? Pode acelerar ou não; é só um teste.
3. Apagar `F:\Tools\downloads` (zips já extraídos, ~1,7 GB)? Não apaguei por segurança.

## Como testar (passo a passo para o dono)
1. Dois cliques em `F:\Projetos\AI-RPG-Engine\iniciar.cmd`. Abrem 3 janelas pretas (Ollama, backend, frontend) e o navegador.
2. Clique em **+ Nova campanha**, preencha título e premissa, **Criar e começar**.
3. Clique em **Começar a história** ou escreva uma ação e aperte Enter. O texto deve aparecer aos poucos.
4. Feche tudo (navegador e janelas pretas). Abra de novo com `iniciar.cmd`, clique em **Continuar**:
   a história deve estar igual e continuar dali.

## Arquivos principais modificados nesta sessão
Backend: `app/config.py`, `app/persistence/**`, `app/providers/**`, `app/ai/**`, `app/services/**`, `app/api/**`,
`app/engine/**`, `alembic/**`, `tests/**`. Frontend: `frontend/**`. Raiz: `instalar.cmd`, `iniciar.cmd`,
`.gitattributes`, `.env.example`, `README.md`, `CLAUDE.md`. Docs: todos em `docs/`.

## Plano de testes (visão geral)
- Unitários: dados, fórmulas, configuração, provedores, regras de arquitetura (guardiões).
- Integração: banco, repositórios/isolamento, pipeline de operações, orquestrador, API.
- Fluxo completo: criar → jogar → reiniciar → retomar (`tests/e2e`).
- Externos (`-m external`): Ollama real.
- Casos da SPEC Parte 22 já cobertos: 1, 2, 3, 4, 5, 6, 7, 8 (parcial: evolução de habilidades),
  18 (falhas de provedor), 19 (respostas inválidas), 20 (consistência de regras), 24, 25 (parcial: dono), 26.

## Riscos principais
| Risco | Mitigação |
|---|---|
| Escopo muito grande | Etapas pequenas e executáveis; nada marcado pronto sem teste |
| Modelos locais erram o formato JSON | Validação + reenvio com o erro (D-008); operações recusadas uma a uma |
| Qualidade da narração com modelo pequeno | Modelo maior ou provedor externo (decisão pendente) |
| Lentidão com duas chamadas por turno (Etapa 2) | Intérprete curto (JSON); medir com Ollama real |
| Contexto grande demais | Orçamento de tokens; resumos em camadas (Etapa 3) |
| IA contradizer fatos antigos | Regras versionadas (pronto); registro canônico (Etapa 3) |
