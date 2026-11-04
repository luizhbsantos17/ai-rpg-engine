# Comece aqui — usando o Claude Code neste projeto

Este arquivo é para você. O `CLAUDE.md` é para o Claude Code.

## O que é cada coisa nesta pasta
- `CLAUDE.md`: o Claude Code lê este arquivo sozinho toda vez que você abre uma sessão.
  É ele que garante que cada sessão continue de onde a anterior parou.
- `PROJECT_STATUS.md`: o "diário de bordo". Diz o que está pronto e qual é a próxima tarefa.
- `docs/`: a especificação e as decisões técnicas.

## Passo 1 — Instalar o Claude Code
Jeito mais simples: o **app Claude para computador** (Windows ou macOS), que já inclui o Claude Code.
1. Baixe em https://code.claude.com/docs (seção "Desktop app").
2. Abra o app, entre com sua conta e clique na aba **Code**.

Observação: o Claude Code exige um plano pago do Claude.

## Passo 2 — Preparar a pasta do projeto
1. Extraia este arquivo .zip em um lugar fácil, por exemplo `Documentos/ai-rpg-engine`.
2. Abra `docs/SPEC.md` e cole ali o texto completo da sua especificação (o documento
   "AI RPG ENGINE — ESPECIFICAÇÃO COMPLETA..."), substituindo o aviso que está no arquivo.

Você não precisa instalar Python, Node ou outras ferramentas agora: na primeira sessão
o Claude Code verifica o que falta e te passa o passo a passo.

## Passo 3 — Abrir o projeto no Claude Code
Na aba Code, escolha a pasta `ai-rpg-engine` como pasta de trabalho.

## Passo 4 — Primeira mensagem (copie e cole)
```
Esta é a primeira sessão do projeto. Leia o CLAUDE.md, o PROJECT_STATUS.md e os documentos
em docs/. Depois:
1. Verifique meu ambiente (sistema operacional, Python, Node, Git, memória RAM e placa de vídeo)
   e me diga o que preciso instalar, com passo a passo para iniciante.
2. Revise a arquitetura comparando com docs/SPEC.md e me aponte problemas antes de programar.
3. Inicie o repositório Git e comece a Etapa 1 pela subtarefa 1.
Pare ao fim de cada subtarefa para me mostrar o que fez e como eu testo.
```

## Como trabalhar no dia a dia
- **Permissões**: o Claude Code pede autorização antes de rodar comandos ou mexer em arquivos.
  Leia o que ele vai fazer. Se não entender, pergunte "o que esse comando faz?" antes de aprovar.
- **Uma subtarefa por vez**: peça pequenas entregas e teste cada uma. Ele vai te dizer como.
- **Pergunte à vontade**: "explique o que você acabou de fazer", "por que escolheu isso?".
  Você aprende mais assim do que só aprovando.
- **Sessões longas ficam piores**: quando a conversa ficar muito grande, encerre e abra outra.
  O `PROJECT_STATUS.md` garante a continuidade.

### Para começar uma sessão nova
```
Nova sessão. Siga o "Início de toda sessão" do CLAUDE.md e continue a próxima tarefa.
```

### Para encerrar uma sessão
```
Vamos encerrar. Siga o "Fim de toda sessão" do CLAUDE.md.
```

### Se algo der errado
```
Deu este erro: [cole o erro]. Explique a causa em linguagem simples e corrija.
```

## Documentação oficial
- Visão geral e instalação: https://code.claude.com/docs
- Curso gratuito para iniciantes (Claude Code 101): https://academy.claude.com/
