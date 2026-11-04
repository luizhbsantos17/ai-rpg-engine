# PROJECT_STATUS

Última atualização: 2026-11-03 — Etapa 1, subtarefa 2 concluída.

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | concluída; arquitetura revisada contra a SPEC (D-011 a D-016) |
| 1 — Fundação | em andamento: subtarefas 1 e 2 de 10 concluídas |
| 2 a 7 | não iniciadas |

## O que existe
- Documentação completa em `docs/` (SPEC colada pelo usuário).
- Repositório Git no ramo `main`.
- `backend/`: `pyproject.toml`, ambiente virtual `backend/.venv` (Python 3.13.3, fora do Git),
  pytest 9.2.0 com o marcador `external`.
- `backend/app/config.py`: lê `.env` + variáveis de ambiente, valida valores (Flask 3.1.3, python-dotenv 1.2.4).
- `backend/app/__init__.py`: fábrica `create_app`; `app/api/`: rota `GET /api/health` e erros em JSON.
- `.env` local do usuário criado a partir do exemplo, com chave secreta aleatória (fora do Git).

## Ambiente do usuário (verificado em 2026-11-03)
| Item | Encontrado | Situação |
|---|---|---|
| Sistema | Windows 11 Pro 64 bits (10.0.26200) | ok |
| Python | 3.13.3 (também há 3.11) | ok (D-011) |
| Git | 2.56.0 | ok |
| Node / npm | 20.11.1 / 10.2.4 | **atualizar antes da subtarefa 7** (Node 20 está fora de suporte e é antigo para o Vite atual) |
| Ollama | não instalado | **instalar antes da subtarefa 9**, fora do disco C: |
| CPU | Ryzen 5 4600G (6 núcleos / 12 threads) | ok |
| RAM | 13,8 GB visíveis | suficiente só para modelos locais pequenos |
| Placa de vídeo | só a integrada (Radeon do 4600G), sem placa dedicada | IA local vai rodar no processador: lenta |
| Disco | C: **0,6 GB livres**; E: 10,7 GB; F: 25,1 GB | **C: quase cheio — liberar espaço** |
| SQLite (do Python) | 3.49.1, com FTS5 e funções JSON | ok |

## Pendências da Etapa 0
- [x] Usuário colar a especificação completa em `docs/SPEC.md`.
- [x] Verificar o ambiente do usuário (tabela acima).
- [ ] Pesquisar modelos e provedores atuais e preencher `docs/AI_PROVIDERS.md` com fonte e data
  (fazer junto com a subtarefa 5; considerar que o hardware só roda modelos locais pequenos).

## Próxima tarefa: Etapa 1, subtarefa 3 — SQLAlchemy + Alembic + primeira migração
Critério de conclusão (SPEC Parte 23): criar uma campanha, interagir com a IA, salvar,
fechar o programa, reabrir e continuar exatamente do mesmo ponto.

Subtarefas, nesta ordem:
1. ~~Estrutura de pastas do backend, `pyproject.toml`, ambiente virtual, `pytest` rodando um teste vazio.~~ **Concluída.**
2. ~~Configuração (`config.py` lendo `.env`) e fábrica da aplicação Flask com rota `/api/health`.~~ **Concluída.**
3. SQLAlchemy + Alembic + primeira migração: `users`, `campaigns`, `turns`, `messages`, `events`, `ai_requests`.
4. Repositórios com filtro obrigatório por `campaign_id` + teste de isolamento entre campanhas.
5. Camada de provedores: `base.py`, `fake.py`, `ollama.py` + testes com o fake.
6. Orquestrador mínimo de turno (entrada → contexto simples → IA → mensagem salva), idempotente pelo `turn_id`.
7. Frontend mínimo: lista de campanhas, criar campanha, tela de chat com texto chegando aos poucos.
8. Teste de fluxo completo: criar → jogar 3 turnos (fake) → reiniciar app → retomar → histórico idêntico.
9. Teste manual com Ollama real, registrado aqui com o resultado.
10. Atualizar todos os documentos e o `README.md` com instruções reais de instalação.

## Plano de testes (visão geral)
- **Unitários**: validadores de operações, avaliador de fórmulas, dados com seed, interpretador de comandos.
- **Integração**: pipeline de turno com `FakeProvider` e banco SQLite temporário.
- **Fluxo completo**: campanhas simuladas do início à retomada (os 26 casos da SPEC Parte 22 viram testes ao longo das etapas).
- **Externos** (`@pytest.mark.external`): provedores reais; não rodam por padrão.
- Respostas inválidas da IA são roteirizadas no fake para testar a recuperação.

## Riscos principais
| Risco | Mitigação |
|---|---|
| Escopo muito grande para uma pessoa | Etapas pequenas e executáveis; recusar avançar sem a anterior testada |
| Modelos locais erram o formato JSON | Validação + reenvio com o erro (D-008); prompts curtos e esquemas simples |
| Custo e lentidão com várias chamadas por turno | Uma chamada na Etapa 1, duas a partir da Etapa 2 (D-013); níveis de simulação; limite de gasto |
| Contexto grande demais para a IA | Construtor de contexto com orçamento de tokens; resumos em camadas |
| IA contradizer fatos antigos | Registro canônico consultado no contexto; validação de `canon.amend` |
| Regras criadas pela IA quebrarem o motor | Esquemas por tipo de definição; avaliador de fórmulas seguro; testes |
| Conteúdo adulto indisponível em provedores comerciais | Declarado por provedor e avisado na interface (D-007) |
| Computador do usuário fraco para modelos locais | Verificar hardware antes; permitir provedor externo |

## Testes executados
| Data | Comando | Resultado |
|---|---|---|
| 2026-11-03 | `cd backend; .\.venv\Scripts\python.exe -m pytest` | 2 passed (Python 3.13.3, pytest 9.2.0) |
| 2026-11-03 | mesmo comando, após subtarefa 2 | 22 passed |
| 2026-11-03 | manual: servidor real (`flask --app app run`) + `GET /api/health` | HTTP 200 `{"env":"development","status":"ok","version":"0.1.0"}`; rota inexistente → HTTP 404 em JSON |

## Problemas conhecidos
- Disco C: com 0,6 GB livres. Pode travar o Windows e impede instalar o Ollama no local padrão.
- Sem placa de vídeo dedicada: velocidade da IA local ainda não medida (será medida na subtarefa 9).
