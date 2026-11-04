# AI_PROVIDERS — Provedores de IA

Status: estrutura definida; modelos, preços e limites AINDA NÃO PESQUISADOS.
Regra (SPEC 17): não registrar preço, limite gratuito ou capacidade sem fonte verificada e data.

## Adaptadores planejados
| Adaptador | Cobre | Custo | Etapa |
|---|---|---|---|
| `fake` | testes automatizados (respostas roteirizadas) | nenhum | 1 |
| `ollama` | modelos locais via Ollama | grátis (usa seu computador) | 1 |
| `openai_compat` | qualquer serviço com API no formato da OpenAI | depende do serviço | 1–2 |
| `anthropic` | modelos Claude via API | pago | 2 |

## Interface comum (`providers/base.py`)
- `complete(messages, options)` → texto
- `complete_json(messages, schema, options)` → objeto validado ou erro
- `stream(messages, options)` → texto em partes
- Retorno sempre inclui: tokens de entrada/saída (quando o provedor informa), duração, erro.

## Papéis da IA (configuráveis por campanha)
narrador · intérprete de ações · NPCs · gerador de mundo · criador de mecânicas · simulação · resumos

## Tabela de modelos (preencher na Etapa 1, com fonte e data)
| Provedor | Modelo | Bom para | Saída JSON confiável? | Custo (fonte, data) | Testado? |
|---|---|---|---|---|---|
| | | | | | |

## Suporte a categorias de conteúdo (ver DECISIONS D-007)
| Provedor | Violência | Horror | Linguagem pesada | Sexual explícito | Fonte |
|---|---|---|---|---|---|
| | | | | | |

## Testes
- Testes com `fake`: rodam sempre, sem internet, verificam a lógica interna.
- Testes marcados `@pytest.mark.external`: chamam provedor real; só rodam quando pedidos explicitamente e podem ter custo.
