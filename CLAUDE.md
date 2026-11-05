# CLAUDE.md — AI RPG Engine

Instruções lidas automaticamente pelo Claude Code no início de cada sessão.

## O projeto
Plataforma de RPG narrativo com IA: a IA narra e cria conteúdo; um motor de jogo
valida, processa e persiste tudo. A especificação completa está em `docs/SPEC.md`
(fonte dos requisitos). A arquitetura aprovada está em `docs/ARCHITECTURE.md`.

## Sobre o dono do projeto
- Desenvolvedor iniciante (lógica, Python e JavaScript básicos, Git). Responda em português.
- Explique decisões técnicas importantes em linguagem simples; defina termos técnicos na primeira vez.
- Faça você mesmo o trabalho que puder fazer. Não peça para ele escrever código.
- Quando ele precisar fazer algo (instalar, configurar, testar na tela), dê o passo a passo exato,
  com o comando completo e o que ele deve ver como resultado.

## Início de toda sessão (obrigatório)
1. Ler `PROJECT_STATUS.md`.
2. Ler os documentos de `docs/` relevantes para a tarefa.
3. Conferir o estado real do código (não confiar só no status) e rodar os testes.
4. Continuar a partir de "Próxima tarefa" do `PROJECT_STATUS.md`.

## Fim de toda sessão (obrigatório)
1. Rodar os testes pertinentes e registrar o resultado real.
2. Atualizar `PROJECT_STATUS.md`, `CHANGELOG.md` e os documentos afetados.
3. Registrar decisões novas em `docs/DECISIONS.md`.
4. Fazer commit no Git com mensagem descritiva.
5. Resumir ao usuário: o que foi feito, o que falta, qual a próxima tarefa.

## Regras invioláveis da arquitetura
- O banco de dados é a fonte da verdade. A IA nunca altera estado diretamente.
- Toda alteração de estado passa pelo pipeline de operações:
  proposta → validação → aplicação em transação → registro no log de eventos.
- Toda tabela de dados de jogo tem `campaign_id`; todo acesso passa pelos repositórios,
  que exigem o `campaign_id`. Nunca consultar dados de jogo sem esse filtro.
- Aleatoriedade só pelo motor (`engine/dice`), com seed registrada. A IA nunca "rola dados".
- Fórmulas de regras criadas pela IA são avaliadas por um avaliador seguro. Nunca usar `eval`/`exec`.
- Chaves de API só em variáveis de ambiente (`.env`, que não vai para o Git).
- Comandos `/admin` e `/debug` só são reconhecidos pelo interpretador de comandos, nunca pela IA.

## Regras de trabalho
- Não marcar nada como concluído sem teste executado (ver "Definição de pronto" na Parte 24 da SPEC).
- Não inventar resultados de testes, preços, limites ou capacidades de provedores de IA.
- Testes com provedor falso (`FakeProvider`) verificam a lógica interna; não são "integração real".
- Antes de mudanças que removam funcionalidade, alterem escopo ou possam perder dados: explicar o impacto e pedir autorização.
- Arquivos pequenos e com responsabilidade clara. Evitar arquivos gigantes.
- Implementar etapa por etapa (Parte 23 da SPEC). Cada etapa termina executável e testada.

## Comandos (atualizar quando forem criados)
Ambiente do dono: Windows 11, PowerShell. O ambiente virtual fica em `backend/.venv`
(criado com `py -3.13 -m venv .venv`); usar o Python dele diretamente, sem "ativar".
- Backend, instalar dependências: `cd backend; .\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- Backend, testes: `cd backend; .\.venv\Scripts\python.exe -m pytest`
- Testes com provedores reais (custo/internet): `... -m pytest -m external`
- Backend, servidor: `cd backend; .\.venv\Scripts\flask.exe --app app run --debug` (abre em http://127.0.0.1:5000; teste: `/api/health`)
- Configuração: `.env` na RAIZ do projeto (copiado de `.env.example`); lido por `backend/app/config.py`
- Frontend: `cd frontend && npm run dev`
- Migrações: `cd backend && alembic upgrade head`
- Enviar para o GitHub (repositório privado luizhbsantos17/ai-rpg-engine): `git push` (login do `gh` em `F:Toolsghbingh.exe`)
- Medir desempenho (campanha grande, IA falsa): `cd backend && python scripts/benchmark_large_campaign.py 500 300`
- Conferir uma jogada com o Ollama real (banco separado em .tmp/): `cd backend && python scripts/real_turn_check.py gemma3:4b`
