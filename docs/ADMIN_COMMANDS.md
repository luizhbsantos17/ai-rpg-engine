# ADMIN_COMMANDS — Comandos administrativos

Status: **implementado** (Etapa 6) em `backend/app/admin/`. Testes: `backend/tests/integration/test_admin.py`.

## Como usar
1. Defina uma senha no `.env`: `ADMIN_PASSWORD=sua-senha` (sem senha, o modo administrador fica desligado).
2. No jogo, digite na caixa de texto um comando que **comece** com `/admin` ou `/debug`.
3. Na primeira vez a página pede a senha. A sessão dura 30 minutos (renova a cada uso) e acaba ao fechar
   o navegador ou reiniciar o programa.
4. A resposta aparece no **CONSOLE ADMIN**, fora da história. Comandos nunca vão para a IA nem viram fala.

## Regras gerais
- Só valem mensagens que **começam** com `/admin` ou `/debug`. "Eu grito /admin" é fala do jogador.
- O endpoint de jogadas recusa textos que começam com esses prefixos (eles nunca chegam à IA).
- Comandos de alteração viram **operações do motor** com origem `admin`: mesma validação e mesmo log de
  eventos da IA. Se o motor recusar, nada é gravado.
- Comandos destrutivos (⚠) pedem confirmação: o sistema responde um código e o comando só roda repetido com
  `--confirm CÓDIGO` (vale 2 minutos e só para exatamente o mesmo comando).
- Todo comando executado fica em `admin_audit`. `/admin undo` desfaz o último comando reversível.

## Sintaxe
```
/<grupo> <verbo> [alvo] [argumentos] [--opção valor]
```
- Alvos: `player`, `npc "Nome"`, `location "Nome"`, `entity <id>` ou só `"Nome"` (qualquer entidade).
  Nome repetido → o sistema lista os ids para usar `entity <id>`.
- Atributo: `<alvo>.<chave>` — `player.forca`, `"Ana Clara".vida`. Recurso aceita `valor/máximo`: `15/30`.
- Textos com espaço vão entre aspas. Durações: `30m`, `4h`, `2d`, `1d12h`.

## Catálogo
| Comando | Efeito | Desfaz? |
|---|---|---|
| `/admin help [comando]` | lista os comandos ou explica um | — |
| `/admin status [alvo]` | ficha VERDADEIRA completa (padrão: protagonista) | — |
| `/admin inspect <alvo>` | estado verdadeiro + o que sabe e lembra | — |
| `/admin audit [--last n]` | últimos comandos administrativos | — |
| `/admin set <alvo>.<atributo> <valor>` | altera atributo (validado pelo motor) | sim |
| `/admin give <alvo> skill <chave ou nome> [--level n]` | concede habilidade | sim |
| `/admin give <alvo> item <chave ou nome> [--qty n]` | cria item no inventário | sim |
| `/admin remove <alvo> skill\|item <chave ou nome>` ⚠ | remove habilidade / todos os itens do tipo | não |
| `/admin teleport <alvo> <local>` | move a entidade | sim |
| `/admin create npc "Nome" [--desc "..."] [--kind creature]` | cria personagem no local do protagonista | sim |
| `/admin kill <alvo>` ⚠ | marca como morto (sem aplicar a regra de morte) | não |
| `/admin world.time advance <duração>` ⚠ | avança o relógio (dispara agendamentos e efeitos) | não |
| `/admin undo` | desfaz o último comando reversível | — |
| `/debug show_context [--role narrator]` | mensagens enviadas à IA na última chamada daquele papel | — |
| `/debug show_events [--last n]` | log de eventos | — |
| `/debug show_memory [alvo]` | resumos da campanha, ou memórias e conhecimento do alvo | — |
| `/debug inspect_entity <alvo>` | dados brutos da entidade | — |
| `/debug inspect_rules [tipo]` | definições atuais e versões | — |
| `/debug inspect_ai_requests [--last n]` | chamadas à IA: papel, modelo, tokens, tempo, erros | — |
| `/debug validate_world` | procura inconsistências (itens sem dono, locais inexistentes, atributos sem definição, recursos acima do máximo, jogada travada...) | — |

## API (para referência)
- `POST /api/admin/login` `{password}` → `{token}` · `POST /api/admin/logout`
- `POST /api/campaigns/<id>/admin` `{command}` com cabeçalho `X-Admin-Token`
  → `{ok, command, lines, confirmation_code, data}`

## Ainda não implementado
- `/admin snapshot create|restore` (Etapa 6.5: backups por campanha, D-014).
