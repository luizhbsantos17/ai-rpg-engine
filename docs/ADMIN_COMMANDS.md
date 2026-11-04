# ADMIN_COMMANDS — Comandos administrativos

Status: sintaxe proposta; nenhum comando implementado ainda.

## Regras gerais
- Só valem mensagens que **começam** com `/admin` ou `/debug`. Qualquer outra coisa é fala do jogador.
- Exigem a senha `ADMIN_PASSWORD` (sessão administrativa com tempo de expiração).
- Comandos que alteram estado viram operações do motor com origem `admin` e ficam em `admin_audit`.
- Comandos destrutivos pedem confirmação: o sistema responde com um código e o comando só roda com `--confirm <código>`.
- `/admin undo` desfaz o último comando administrativo reversível.

## Sintaxe
```
/<grupo> <verbo> [alvo] [argumentos] [--opção valor]
```
- Alvos: `player`, `npc "Nome"`, `entity <id>`, `location "Nome"`, `campaign`.
- Caminhos com ponto: `player.level`, `npc "Ana".attributes.forca`.
- Textos com espaço entre aspas.
- Durações: `30d`, `4h`, `15m`.

## Catálogo inicial
| Comando | Efeito | Destrutivo? |
|---|---|---|
| `/admin help [comando]` | lista comandos ou explica um | não |
| `/admin status player` | ficha verdadeira completa do protagonista | não |
| `/admin inspect npc "Nome"` | estado verdadeiro + o que ele sabe | não |
| `/admin set <caminho> <valor>` | altera valor | não (reversível) |
| `/admin give <alvo> skill\|item "Nome" [--qty n]` | concede | não (reversível) |
| `/admin remove <alvo> skill\|item "Nome"` | remove | sim |
| `/admin teleport <alvo> "Local"` | muda localização | não (reversível) |
| `/admin create npc "Nome" [--desc "..."]` | cria NPC | não |
| `/admin kill <alvo>` | marca como morto | sim |
| `/admin world.time advance <duração>` | avança o relógio e roda a simulação | sim |
| `/admin snapshot create ["rótulo"]` | backup manual | não |
| `/admin snapshot restore <id>` | restaura backup | sim |
| `/admin undo` | desfaz o último comando reversível | — |
| `/debug show_context` | contexto enviado à IA no último turno | não |
| `/debug show_memory [alvo]` | memórias e resumos | não |
| `/debug show_events [--last n]` | log de eventos | não |
| `/debug inspect_entity "Nome"` | dados brutos da entidade | não |
| `/debug inspect_rules [kind]` | definições e versões | não |
| `/debug inspect_ai_requests [--last n]` | chamadas à IA, tokens, erros | não |
| `/debug validate_world` | procura inconsistências (referências quebradas, itens duplicados...) | não |
