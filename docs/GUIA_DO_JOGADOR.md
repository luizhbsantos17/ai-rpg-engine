# Guia do jogador

Como jogar o AI RPG Engine. Instalação e configuração estão no [README](../README.md).

## A ideia em uma frase
A IA narra e interpreta o mundo; o **motor de jogo** decide o que de fato acontece (dados, atributos,
itens, quem sabe o quê) e guarda tudo. Por isso a ficha, o inventário e as missões sempre batem com a
história, e nada some quando você fecha o programa.

## 1. Abrir o jogo
Dois cliques em `iniciar.cmd`. Abrem janelas pretas (não feche enquanto joga) e o navegador em
http://127.0.0.1:5173, na tela **Suas campanhas**.

## 2. Criar uma campanha
Clique em **+ Nova campanha**. Duas formas:
- **Gerar aleatória**: escreva gêneros e preferências se quiser (opcional) e clique em **Gerar campanha**
  (~10–15 s). Marque "manter" nos campos de que gostou e clique em **Gerar de novo** para trocar só o resto,
  ou **Editar** à mão. O rascunho fica salvo na lista (selo "Rascunho") até você clicar em **Começar**.
- **Escrever a minha**: título, premissa e gêneros escritos por você.

Segredos do mundo gerado (reviravoltas, vilões ocultos) ficam só no servidor: você não os vê, a IA usa.

## 3. Jogar
- Clique em **Começar a história**. O **primeiro turno demora mais** (até ~1,5 min neste computador): a IA cria
  as regras do universo, o seu personagem e o lugar inicial.
- Escreva o que você **faz ou diz** e aperte **Enter** (Shift+Enter quebra a linha). "O narrador está
  pensando…" aparece enquanto a IA trabalha; o texto chega aos poucos.
- Avisos do motor aparecem no meio da história:
  `[SISTEMA]` (algo mudou: atributo, item, habilidade), `[TESTE]` (rolagem de dados feita pelo motor),
  `[ALERTA]` (perigo, morte), `[MISSÃO]` (missão nova ou atualizada). O nome da "janela de sistema" pode
  mudar por universo nas configurações.
- Se der erro (IA desligada, demora demais), aparece **Tentar de novo**: a jogada é repetida sem duplicar nada.

Equipamento: diga o que veste ou empunha ("visto a cota de malha", "empunho o escudo"). O bônus do item
entra nos testes do motor enquanto estiver equipado; dar ou largar o item o desequipa.

Dica: frases claras ajudam a IA a entender a mecânica ("tento arrombar a porta com o ombro", "durmo até o
amanhecer"). Com o modelo pequeno instalado hoje, ela às vezes ignora a parte mecânica; o motor nunca deixa
o estado ficar inválido, mas pode não aplicar o que você esperava.

### Não gostou do texto?
Embaixo da última narração há o botão **↻ Outra versão**: a IA escreve a mesma cena de outro jeito.
Os dados rolados e o que aconteceu no mundo continuam iguais; só o texto muda. Se der erro, o texto
anterior fica.

## 4. Painéis à direita (no celular: botão **Ficha**)
| Aba | O que mostra |
|---|---|
| **Status** | classe e raça, hora do mundo, recursos (vida, mana...), efeitos ativos, atributos, habilidades (com recarga), **equipamento** (o que está em uso, em qual espaço e o bônus) e inventário |
| **Missões** | missões ativas, concluídas e falhadas, com objetivos |
| **Conhecidos** | personagens que você conhece e o que você **acha** que sabe deles (pode estar errado ou disfarçado) |
| **Mapa** | lugares que você visitou e o que está à vista agora |
| **Diário** | resumos automáticos da história (a cada 8 turnos) e avisos importantes |
| **Laços** | o que você sente por cada personagem |

Tudo é do **ponto de vista do seu personagem**: o jogo não mostra o que os outros sentem nem o que está escondido.

## 5. Configurações da campanha
Botão **Configurações** na tela de jogo:
- **Experiência**: modelo de IA, criatividade, motor de regras ligado/desligado ("só narração" é mais rápido),
  mundo vivo, avisos de dados. Vale a partir da próxima jogada; o passado não muda.
- **Conteúdo e maturidade**: intensidade geral e por categoria. Algumas regras de segurança são fixas.
- **Regras do universo**: só para ler. As regras mudam pela história (pelo motor), nunca por aqui.

## 6. Guardar, levar e recuperar
- **Tudo é salvo a cada jogada.** Feche quando quiser; na lista, **Continuar** volta exatamente de onde parou.
- **Cópias automáticas**: a cada 20 jogadas o programa guarda uma cópia da campanha em `data\backups\` (ficam as
  5 mais recentes). Antes de excluir uma campanha também é feita uma cópia.
- **Exportar** (na lista) baixa a campanha inteira num arquivo `.json`. **Importar** traz de volta (em outro
  computador ou depois de excluir). Arquivos de versões anteriores do programa são convertidos sozinhos.
- **Excluir** pede para digitar o título exato, para evitar acidentes.

## 7. Modo administrador (opcional)
Para corrigir ou investigar algo sem passar pela história. Defina `ADMIN_PASSWORD` no `.env`, depois digite na
caixa de texto um comando que **comece** com `/admin` ou `/debug` (ex.: `/admin status`, `/admin help`).
A página pede a senha; a resposta aparece no **CONSOLE ADMIN**, fora da história, e nunca vai para a IA.
Comandos perigosos pedem um código de confirmação, e `/admin undo` desfaz o último comando reversível.
Lista completa: [ADMIN_COMMANDS.md](ADMIN_COMMANDS.md).

## 8. Problemas comuns
| O que acontece | O que fazer |
|---|---|
| Aparece um erro ao jogar | Confira se a janela preta do Ollama está aberta; clique em **Tentar de novo** |
| Turno muito lento | Normal em computador sem placa de vídeo dedicada (~30 s). Desligar o motor de regras nas configurações acelera |
| Página não abre | Feche todas as janelas pretas e abra `iniciar.cmd` de novo |
| A história contradiz algo | O motor guarda os fatos; use `/admin status` ou `/debug validate_world` para ver o estado real |
