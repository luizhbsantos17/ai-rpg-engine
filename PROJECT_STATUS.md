# PROJECT_STATUS

Última atualização: Etapa 0 (planejamento) — documentos criados fora do Claude Code.

## Resumo
| Etapa | Status |
|---|---|
| 0 — Planejamento e arquitetura | documentos prontos; falta validar com o código real |
| 1 — Fundação | não iniciada |
| 2 a 7 | não iniciadas |

## O que existe
- Documentação: `CLAUDE.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`,
  `docs/DECISIONS.md`, `docs/REQUIREMENTS.md`, `docs/AI_PROVIDERS.md`, `docs/ADMIN_COMMANDS.md`.
- Nenhum código ainda. Nenhum teste executado.

## Pendências da Etapa 0
- [ ] Usuário colar a especificação completa em `docs/SPEC.md`.
- [ ] Verificar o ambiente do usuário: sistema operacional, versões de Python, Node e Git, memória RAM e placa de vídeo (decide quais modelos locais são viáveis).
- [ ] Pesquisar modelos e provedores atuais e preencher `docs/AI_PROVIDERS.md` com fonte e data.

## Próxima tarefa: Etapa 1 — Fundação
Critério de conclusão (SPEC Parte 23): criar uma campanha, interagir com a IA, salvar,
fechar o programa, reabrir e continuar exatamente do mesmo ponto.

Subtarefas, nesta ordem:
1. Estrutura de pastas do backend, `pyproject.toml`, ambiente virtual, `pytest` rodando um teste vazio.
2. Configuração (`config.py` lendo `.env`) e fábrica da aplicação Flask com rota `/api/health`.
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
| Custo e lentidão com várias chamadas por turno | Uma chamada por turno no início (D-006); níveis de simulação; limite de gasto |
| Contexto grande demais para a IA | Construtor de contexto com orçamento de tokens; resumos em camadas |
| IA contradizer fatos antigos | Registro canônico consultado no contexto; validação de `canon.amend` |
| Regras criadas pela IA quebrarem o motor | Esquemas por tipo de definição; avaliador de fórmulas seguro; testes |
| Conteúdo adulto indisponível em provedores comerciais | Declarado por provedor e avisado na interface (D-007) |
| Computador do usuário fraco para modelos locais | Verificar hardware antes; permitir provedor externo |

## Testes executados
Nenhum ainda.

## Problemas conhecidos
Nenhum ainda.
