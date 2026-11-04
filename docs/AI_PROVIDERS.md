# AI_PROVIDERS — Provedores de IA

Regra (SPEC 17): não registrar preço, limite gratuito ou capacidade sem fonte verificada e data.

## Adaptadores
| Adaptador | Cobre | Custo | Status |
|---|---|---|---|
| `fake` | testes automatizados (respostas roteirizadas); recusado fora de `APP_ENV=test` | nenhum | pronto (Etapa 1) |
| `ollama` | modelos locais via Ollama (`/api/chat` com streaming, `/api/tags`) | grátis (usa seu computador) | pronto e testado com Ollama real (Etapa 1) |
| `openai_compat` | serviços com API no formato da OpenAI | depende do serviço | planejado (Etapa 2+) |
| `anthropic` | modelos Claude via API | pago | planejado; só com autorização e limite de gasto |

## Interface comum (`backend/app/providers/base.py`)
- `stream(messages, options)` → pedaços de texto (`TextDelta`) e, no fim, `StreamCompleted` com o resultado.
- `complete(messages, options)` → resultado inteiro (usa o `stream`).
- `list_models()` → modelos disponíveis.
- Resultado: texto, provedor, modelo, tokens de entrada/saída (quando o provedor informa; nunca inventados), duração.
- Erros traduzidos: `ProviderUnavailableError` (não conecta), `ProviderTimeoutError`, `ModelNotFoundError`,
  `ProviderResponseError`. Cada um diz se tentar de novo pode funcionar (`retryable`).
- `complete_json` (resposta estruturada validada, com reenvio do erro — D-008) entra na Etapa 2 com o
  papel "intérprete" (D-024).
- `is_paid`: provedor pago é recusado enquanto `AI_SPEND_LIMIT_PER_SESSION` for 0.

## Configuração (`.env`)
`AI_PROVIDER`, `AI_MODEL` (vazio = primeiro instalado), `AI_TEMPERATURE`, `AI_MAX_OUTPUT_TOKENS`,
`AI_CONTEXT_WINDOW` (enviado ao Ollama como `num_ctx`), `AI_TIMEOUT_SECONDS`, `OLLAMA_BASE_URL`.

## Ollama neste computador (instalado em 2026-11-04)
- Versão: **0.40.14**, pacote portátil oficial `ollama-windows-amd64.zip` do GitHub
  (https://github.com/ollama/ollama/releases), SHA-256 conferido. Extraído em `F:\Tools\ollama`.
- Modelos em `F:\Tools\ollama-models` (variável `OLLAMA_MODELS`, definida pelo `iniciar.cmd`).
- Hardware visto pelo Ollama: só CPU (13,8 GiB de RAM, ~4,9 GiB livres no momento do teste). A GPU
  integrada (Radeon do Ryzen 5 4600G, via Vulkan) é ignorada por padrão; liga com `OLLAMA_IGPU_ENABLE=1`
  (não testado ainda).
- Contexto padrão do Ollama nesta máquina: 4096 tokens; o projeto envia `num_ctx` = `AI_CONTEXT_WINDOW` (8192).

## Modelos testados (medições reais, nesta máquina)
| Modelo | Tamanho | Fonte do tamanho | Velocidade medida | Qualidade observada | Data |
|---|---|---|---|---|---|
| `qwen2.5:1.5b` | 986 MB | https://ollama.com/library/qwen2.5/tags | 25–28 tokens/s; 1º pedaço em 2,6–5,0 s; turno de ~1.400–2.200 caracteres em 16–23 s | **Fraca para narrar**: repete frases, escreve falas do protagonista apesar da instrução, começa parágrafos com "-", às vezes troca nomes. Segue o português e mantém o assunto | 2026-11-04 |

Conclusão: a integração está comprovada, mas uma narração de qualidade precisa de um modelo maior
(**decisão pendente do dono**, por ocupar mais disco/RAM). Candidatos na biblioteca do Ollama
(tamanhos da página oficial de cada modelo, consultada em 2026-11-04; desempenho NÃO medido ainda):

| Modelo | Tamanho | Observação |
|---|---|---|
| `qwen2.5:3b` | 1,9 GB | mesma família, 2× maior; contexto 32K |
| `gemma3:4b` | 3,4 GB | contexto 128K; texto e imagem |
| `qwen2.5:7b` | 4,7 GB | provavelmente o limite prático nesta RAM; mais lento |

Modelos com modo "pensamento" (ex.: família `qwen3`) foram evitados por enquanto: o texto de raciocínio
precisaria ser separado da narração.

## Provedores externos
Ainda não pesquisados em detalhe (o adaptador `openai_compat` é da Etapa 2). Antes de usar qualquer
serviço pago: registrar aqui preço e limites com fonte e data, e pedir autorização ao dono.

## Suporte a categorias de conteúdo (ver DECISIONS D-007)
| Provedor | Violência | Horror | Linguagem pesada | Sexual explícito | Fonte |
|---|---|---|---|---|---|
| Ollama (modelos locais) | depende do modelo | depende do modelo | depende do modelo | depende do modelo e da licença | a avaliar por modelo |

## Testes
- Com `fake`: rodam sempre, sem internet; verificam a lógica interna (não são integração real).
- Adaptador do Ollama com servidor simulado (`tests/unit/test_ollama_provider.py`): formato do pedido e erros.
- `@pytest.mark.external` (`tests/external/test_ollama_real.py`): Ollama de verdade; só roda com
  `pytest -m external`. Resultado em 2026-11-04: **1 passed** (`qwen2.5:1.5b`, 3 tokens em 4,2 s com carga do modelo).
