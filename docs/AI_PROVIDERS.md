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

### Motor ligado (intérprete + narrador), `qwen2.5:1.5b`, 2026-11-04
| Chamada | Tokens gerados | Tempo |
|---|---|---|
| preparação da campanha (1º turno) | 360 | 15,7 s |
| intérprete | 81–151 | 7,5–14,4 s |
| narrador | 325–334 | 13,4–16,3 s |
Turno completo: ~21 s (com preparação no 1º turno: ~46 s). JSON sempre válido depois do limite de 512 tokens
(D-028). Preparação funcionou (atributos, protagonista, local). O intérprete pediu um teste quando fazia
sentido em um caso, mas em outro aumentou "Força" por um chute numa porta: **as escolhas mecânicas do
modelo de 1,5B não são confiáveis**; o motor impede estados inválidos, mas não escolhas ruins.

### Fluxo completo pela API, `qwen2.5:1.5b`, 2026-11-04 (Etapa 7.2)
Gerar campanha → começar → 3 turnos → ficha/mapa → admin (status, validate_world, snapshot, inspect) →
desligar e religar o backend → 4º turno. Tudo funcionou; histórico (3 turnos `completed`), ficha e snapshot
continuaram iguais depois do reinício; `/debug validate_world` sem inconsistências.

| Chamada | Tokens entrada → saída | Tempo |
|---|---|---|
| geração da campanha | 364 → 313 | 14,5 s |
| preparação (1º turno) | 894 → 634 | 26,1 s |
| intérprete | 2.859–4.108 → 14–25 | 5,9–19,6 s |
| narrador | 1.452–2.637 → 321–882 | 21,6–40,2 s |

Turnos completos: 1º 86 s (preparação + narração longa de 882 tokens), depois 27–34 s. O contexto cresceu
(intérprete com ~4 mil tokens de entrada no 3º turno), o que pesa no tempo em CPU.
Qualidade: o intérprete devolveu quase sempre "nenhuma operação" (14–25 tokens); em "Durmo até o amanhecer"
não avançou o relógio, então a simulação do mundo não rodou. Narração confusa ("dormindo... completamente
acordada"). Reforça a decisão pendente de um modelo maior.

### Classe e raça na preparação, `qwen2.5:1.5b`, 2026-11-04
Com texto explicativo DENTRO do exemplo JSON, o modelo copiou a explicação literalmente como valor; com exemplos
concretos nas regras ("meio-elfa"), copiou o exemplo até em ficção científica. Versão final: campos vazios no
exemplo e a regra em palavras. Resultado: fantasia → Arqueiro/Humano, ficção científica → Guerreiro/Humano
(coerente, ainda pouco criativo). 1º turno 52–56 s. Lição para os prompts: modelo pequeno copia exemplos.

Modelos com modo "pensamento" (ex.: família `qwen3`) foram evitados por enquanto: o texto de raciocínio
precisaria ser separado da narração.

## Servidores no formato OpenAI (`AI_PROVIDER=openai_compat`, D-053)
Adaptador `backend/app/providers/openai_compat.py`: `POST {base}/chat/completions` com streaming SSE,
`GET {base}/models`, chave opcional (`Authorization: Bearer`), saída estruturada por `response_format`
`json_schema`. Serve para LM Studio, llama.cpp, vLLM, o próprio Ollama em `/v1`, e serviços externos.

```
AI_PROVIDER=openai_compat
OPENAI_COMPAT_BASE_URL=http://127.0.0.1:11434/v1   # exemplo: o Ollama local nesse formato
OPENAI_COMPAT_PAID=false                            # obrigatório: serviços pagos estão bloqueados
OPENAI_COMPAT_API_KEY=                              # só se o servidor pedir
AI_MODEL=qwen2.5:1.5b                               # nome do modelo no servidor
```

**Serviços pagos ficam bloqueados** (o programa recusa iniciar com `OPENAI_COMPAT_PAID=true`, o padrão):
o controle de gasto ainda não existe e preços não foram pesquisados. Liberar exige decisão do dono.

Diferença importante: este formato não tem como pedir o tamanho de contexto (`AI_CONTEXT_WINDOW` é
ignorado); quem decide é o servidor. Para o Ollama, prefira o adaptador nativo (`AI_PROVIDER=ollama`).

### Teste real, Ollama em /v1 com `qwen2.5:1.5b`, 2026-11-04
- `pytest -m external`: streaming, contagem de tokens (`stream_options.include_usage`) e JSON com esquema ok.
- Jogo completo pela API (gerar → começar → 3 turnos → admin): tudo ok, `validate_world` sem inconsistências.
  Geração 7,2 s; 1º turno 66 s; depois 13–19 s. Intérprete com até 3.544 tokens de entrada.

## Serviços gratuitos na internet (D-054)
| `AI_PROVIDER` | Chave (`.env`) | Onde criar | Modelos preferidos (escolha automática) |
|---|---|---|---|
| `gemini` | `GEMINI_API_KEY` | https://aistudio.google.com/apikey | `gemini-3.8-flash`, `gemini-2.5-flash` |
| `groq` | `GROQ_API_KEY` | https://console.groq.com/keys | `openai/gpt-oss-120b`, `qwen/qwen3.8-27b` |
| `openrouter` | `OPENROUTER_API_KEY` | https://openrouter.ai/keys | `google/gemma-4-31b-it:free` (**só `:free`**) |

Limites conferidos em 2026-11-04 (mudam sem aviso):
- **OpenRouter** (página oficial de preços): modelos `:free` com 20 pedidos/min e 50/dia; 1.000/dia depois de
  comprar US$ 10 em créditos; pedidos que falham também contam. Havia 12 modelos `:free` na lista pública
  (`/api/v1/models`), nenhum específico de roleplay. Com 50/dia: ~20 jogadas (cada jogada = 2 ou mais pedidos).
  Fonte: https://openrouter.ai/pricing
- **Groq** (página oficial de limites): a tabela publicada é a "base do plano Developer": `openai/gpt-oss-120b`
  e `qwen/qwen3.8-27b` com 30 pedidos/min, 1.000/dia, 8.000 tokens/min. Os limites do plano Free aparecem só no
  painel da conta. 8.000 tokens/min é apertado: uma jogada usa ~6–7 mil. Fonte: https://console.groq.com/docs/rate-limits
- **Gemini** (AI Studio): o nível gratuito não exige faturamento; a página oficial não publica números (mostra
  os limites no AI Studio). Endereço no formato OpenAI: `https://generativelanguage.googleapis.com/v1beta/openai/`.
  O nível gratuito pode usar os dados para melhorar produtos do Google. Fonte: https://aistudio.google.com/docs/rate-limits
  e https://aistudio.google.com/docs/openai

Cuidados: não cadastrar cartão/faturamento (Gemini, Groq); na OpenRouter o programa recusa modelo que não seja
`:free`. Conteúdo: os três têm regras próprias e podem recusar cenas explícitas (aviso mostrado nas configurações
da campanha).

### Teste real com as chaves gratuitas do dono, 2026-11-04
| Serviço | Resultado |
|---|---|
| **Groq** (`openai/gpt-oss-120b`) | **recomendado**. Jogo completo ok: ficha com 7 atributos (Vida, Mana, Nível, Experiência...), 2 habilidades, itens equipados com bônus; 2ª jogada gastou mana e o motor rolou o teste. Jogada de 7 a 54 s: o limite de 8.000 tokens/min obriga a esperar (o programa espera sozinho). |
| **Gemini** | Texto muito bom e rápido (2–11 s), mas a cota gratuita é de **20 pedidos por dia POR MODELO** (mensagem oficial do erro 429: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, limite 20) ≈ 5 jogadas por modelo. `gemini-3.8-flash` deu 503 (alta demanda), `gemini-3.7-flash` sem cota no gratuito, `gemini-2.5-flash` indisponível para contas novas. Sem `reasoning_effort: "none"`, o 3.5 misturou o "pensamento" em inglês no texto ou gastou o limite pensando. |
| **OpenRouter** | Os Gemma `:free` deram 429 do provedor de origem (congestionados) nas 2 tentativas. |

Correções feitas a partir desses testes: erro do Gemini vem como lista JSON; 502/503/504 são tratados como
"tente de novo"; troca automática para o próximo modelo recomendado (só com `AI_MODEL` vazio) e uso continuado
do que respondeu; espera longa (cota diária, `retryDelay` do Gemini) pula direto para o próximo modelo; limite
por minuto (429 curto) espera até 3 vezes antes de trocar; limites de tokens do intérprete (1.024) e da
preparação (2.048) aumentados (o Gemini cortava o JSON); laço de companheiro longo é cortado, não recusado.

`pytest -m external` com `AI_PROVIDER=gemini` e `groq`: **2 passed** cada (texto em português + JSON válido).

## Provedores externos (pagos)
Não pesquisados. Antes de usar qualquer serviço pago: implementar o controle de gasto, registrar aqui preço e
limites com fonte e data, e pedir autorização ao dono.

## Suporte a categorias de conteúdo (ver DECISIONS D-007)
| Provedor | Violência | Horror | Linguagem pesada | Sexual explícito | Fonte |
|---|---|---|---|---|---|
| Ollama (modelos locais) | depende do modelo | depende do modelo | depende do modelo | depende do modelo e da licença | a avaliar por modelo |

## Testes
- Com `fake`: rodam sempre, sem internet; verificam a lógica interna (não são integração real).
- Adaptador do Ollama com servidor simulado (`tests/unit/test_ollama_provider.py`): formato do pedido e erros.
- `@pytest.mark.external` (`tests/external/test_ollama_real.py`): Ollama de verdade; só roda com
  `pytest -m external`. Resultado em 2026-11-04: **1 passed** (`qwen2.5:1.5b`, 3 tokens em 4,2 s com carga do modelo).
