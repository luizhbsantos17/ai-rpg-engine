# SPEC — Especificação completa

> AI RPG ENGINE

ESPECIFICAÇÃO COMPLETA E PROMPT MESTRE DE DESENVOLVIMENTO

Versão: 1.0
Tipo de projeto: Plataforma de RPG narrativo com inteligência artificial
Nome provisório: AI RPG Engine
Objetivo: Desenvolver uma plataforma completa, modular, expansível e funcional de RPG com IA.

---

PARTE 1 — SEU PAPEL E OBJETIVO

1.1. Responsabilidades

Você será o principal responsável pelo planejamento, arquitetura, desenvolvimento, implementação, testes, documentação e manutenção deste projeto.

Atue como:

- Arquiteto de software.
- Desenvolvedor full-stack.
- Engenheiro de integração com inteligência artificial.
- Desenvolvedor de sistemas de RPG.
- Designer de interfaces.
- Engenheiro de banco de dados.
- Responsável por testes e qualidade.
- Responsável pela documentação técnica.

O objetivo é desenvolver uma plataforma de RPG narrativo com inteligência artificial, capaz de criar, administrar e executar campanhas extremamente dinâmicas, criativas, complexas e personalizáveis.

Não quero simplesmente um chatbot que interpreta um mestre de RPG.

Quero um verdadeiro sistema de RPG, com motor de regras, gerenciamento persistente de mundo, personagens autônomos, progressão, combate, inventário, habilidades, relacionamentos, eventos e uma interface própria.

A inteligência artificial deverá atuar como narradora, mestre de jogo, criadora de conteúdo, controladora de NPCs e responsável pela evolução narrativa do mundo.

Entretanto, ela deverá trabalhar em conjunto com um motor de jogo responsável por processar, validar e registrar os acontecimentos e as alterações de estado.

O resultado deverá ser um programa realmente funcional, não apenas uma demonstração ou protótipo visual.

1.2. Contexto do usuário

Considere que o proprietário do projeto está aprendendo desenvolvimento de software e não possui conhecimento avançado de programação.

Portanto:

- Não presuma que ele conhece arquitetura de software.
- Não presuma conhecimentos avançados de backend, APIs, banco de dados ou inteligência artificial.
- Explique decisões técnicas importantes em linguagem acessível.
- Não utilize termos técnicos sem explicar seu significado quando isso for relevante.
- Não transfira para ele tarefas que você consegue executar.
- Não exija que ele implemente manualmente partes do sistema.
- Forneça instruções passo a passo para instalação, configuração e utilização.

Você deverá realizar o trabalho diretamente no ambiente de desenvolvimento disponível, sempre que possível.

1.3. Princípios obrigatórios

1. Não considere uma funcionalidade implementada apenas porque existe um botão ou uma tela para ela.
2. Não utilize dados falsos ou simulações disfarçadas de funcionalidades reais.
3. Não deixe funcionalidades importantes como placeholders sem informar claramente.
4. Não reduza a complexidade dos requisitos apenas para facilitar a implementação.
5. Não limite desnecessariamente a criatividade da IA por meio de listas fixas.
6. Não dependa exclusivamente do histórico de conversa para manter a memória das campanhas.
7. Não permita que a IA seja a única responsável pela integridade dos dados.
8. Não concentre toda a lógica em poucos arquivos gigantes.
9. Não sacrifique a experiência narrativa em favor de regras excessivamente rígidas.
10. Não declare o projeto concluído sem executar testes reais.
11. Não faça alterações destrutivas sem verificar suas consequências e obter autorização quando necessário.
12. Não substitua funcionalidades existentes sem analisar o impacto.
13. Não invente resultados de testes, integrações ou funcionalidades.
14. Mantenha a documentação atualizada durante todo o desenvolvimento.

Quando uma funcionalidade for complexa demais para ser concluída imediatamente, implemente uma versão inicial funcional, modular e preparada para expansão.

---

PARTE 2 — VISÃO GERAL DO PRODUTO

2.1. Conceito central

O AI RPG Engine deverá ser uma plataforma universal de RPG narrativo com inteligência artificial.

A plataforma permitirá criar diversas campanhas independentes, cada uma com seu próprio:

- Universo.
- Mundo.
- História.
- Sistema de regras.
- Personagens.
- NPCs.
- Atributos.
- Classes.
- Raças e espécies.
- Habilidades.
- Equipamentos.
- Criaturas.
- Facções.
- Reinos.
- Economia.
- Progressão.
- Eventos.
- Relacionamentos.
- Histórico.

Uma campanha não deverá interferir nos dados de outra.

A plataforma deverá permitir experiências de diferentes gêneros, incluindo:

- Fantasia medieval.
- Isekai.
- Fantasia sombria.
- Ficção científica.
- Mundos modernos.
- Pós-apocalipse.
- Horror.
- Aventura.
- Mistério.
- Universos originais.
- Universos inspirados em obras existentes.
- Universos personalizados pelo jogador.

Esses gêneros são exemplos, não limitações.

A IA deverá poder criar conceitos e gêneros híbridos ou completamente inéditos.

2.2. Estrutura conceitual

Organize o projeto em três grandes níveis.

Nível 1 — Plataforma

Responsável pela interface, gerenciamento de campanhas, integração com modelos de IA, configurações, armazenamento, ferramentas administrativas e recursos gerais.

Nível 2 — Sistema de RPG

Responsável pelas regras de cada campanha: atributos, habilidades, combate, testes, progressão, morte, avaliação, economia, relacionamentos e demais mecânicas.

Cada campanha poderá possuir seu próprio sistema de regras.

Nível 3 — Campanhas e universos

Cada campanha representa uma experiência independente, com seu próprio mundo, personagens, acontecimentos, regras e estado persistente.

2.3. Filosofia do projeto

O projeto deverá equilibrar dois elementos:

Liberdade criativa: a inteligência artificial deve ter capacidade de inventar personagens, mundos, mecânicas, habilidades, acontecimentos e possibilidades extraordinárias.

Consistência sistêmica: o motor deverá garantir que as regras estabelecidas, os acontecimentos e os dados permaneçam coerentes e persistentes.

Não quero uma IA limitada a selecionar opções de um catálogo fechado.

Também não quero uma IA que possa inventar qualquer resultado sem respeitar o que já aconteceu.

A arquitetura deverá conciliar essas duas necessidades.

---

PARTE 3 — GERAÇÃO DE CAMPANHAS E UNIVERSOS

3.1. Aleatoriedade extrema

A geração de campanhas será uma das funcionalidades centrais do projeto.

O comportamento padrão deverá ser extremamente aleatório.

A aleatoriedade deverá abranger:

- Premissa da história.
- Universo.
- Gênero.
- Época.
- Circunstâncias iniciais.
- Origem do protagonista.
- Personagens envolvidos.
- Regras do mundo.
- Sistema de atributos.
- Classes.
- Espécies.
- Habilidades.
- Facções.
- Conflitos.
- Acontecimentos.
- Possibilidades narrativas.

Não se limite a sortear elementos de uma lista previamente definida.

A IA deverá conseguir inventar combinações e conceitos completamente novos.

3.2. Exemplos de premissas

A IA poderá gerar situações como:

- Uma pessoa comum reencarnada em um mundo de fantasia.
- Uma turma inteira transportada para outro mundo.
- Um protagonista que começa extremamente poderoso.
- Um protagonista que começa completamente fraco.
- Um personagem traído pelos próprios companheiros.
- Um personagem que recebe uma habilidade aparentemente inútil.
- Um personagem que desperta um poder extraordinário.
- Um personagem com uma condição especial desconhecida.
- Um personagem que precisa sobreviver em um mundo hostil.
- Uma pessoa que nasce em uma família nobre ou extremamente pobre.
- Um protagonista que começa como uma criatura incomum.
- Um personagem que não possui acesso ao sistema utilizado pelos demais habitantes.
- Uma pessoa que recebe poderes capazes de violar as regras convencionais daquele universo.

A IA também poderá criar premissas que não se encaixem em nenhum desses exemplos.

3.3. Geração e personalização

O usuário deverá poder:

1. Criar uma campanha completamente aleatória.
2. Gerar novamente uma campanha que não tenha agradado.
3. Personalizar elementos antes de iniciar.
4. Definir temas e gêneros.
5. Escolher algumas características do universo.
6. Preservar elementos específicos durante uma nova geração.
7. Combinar características personalizadas com elementos aleatórios.

A interface deverá apresentar informações introdutórias da campanha sem revelar necessariamente seus segredos.

Deverá existir uma diferença entre informações apresentadas ao jogador e informações internas utilizadas pela IA.

3.4. Geração coerente de universos

A IA deverá conseguir construir universos com:

- História.
- Geografia.
- Regiões.
- Cidades.
- Reinos.
- Civilizações.
- Culturas.
- Religiões e crenças fictícias.
- Espécies.
- Criaturas.
- Sistemas políticos.
- Economia.
- Organizações.
- Facções.
- Conflitos.
- Lendas.
- Entidades especiais.
- Regras sobrenaturais.
- Sistemas de magia.
- Sistemas tecnológicos.

O mundo deverá possuir uma estrutura inicial coerente e poderá expandir conforme a exploração.

Não é necessário gerar absolutamente tudo antes do início da campanha.

Entretanto, informações importantes já estabelecidas deverão ser registradas para impedir contradições.

Implemente uma espécie de registro canônico do universo, contendo os fatos confirmados e as regras estabelecidas.

A IA poderá adicionar informações novas, mas deverá verificar se elas contradizem informações anteriores.

Caso uma alteração realmente modifique uma regra ou um fato estabelecido, ela deverá ser registrada como uma mudança, e não simplesmente substituir silenciosamente o passado.

---

PARTE 4 — PERSONAGEM DO JOGADOR E REENCARNAÇÃO

4.1. Ficha do protagonista

O jogador deverá possuir um personagem persistente, com ficha completa.

A ficha deverá permitir armazenar informações tradicionais e características específicas de cada universo.

4.2. Reencarnação e renascimento

Quando uma campanha envolver reencarnação, renascimento ou nascimento em outro universo, a geração do novo corpo e da identidade deverá ser completamente aleatória por padrão.

Não limite essa geração a nome, classe e atributos.

Considere:

- Nome.
- Sobrenome.
- Aparência.
- Corpo.
- Espécie ou raça.
- Sexo e características biológicas.
- Identidade de gênero.
- Orientação sexual.
- Idade.
- Personalidade.
- Tendências comportamentais.
- Aptidões naturais.
- Limitações.
- Características especiais.
- Potencial de desenvolvimento.
- Talentos.
- Origem familiar.
- Condição social.
- Local de nascimento.
- Circunstâncias da reencarnação.
- Memórias de vidas anteriores.
- Características herdadas.
- Particularidades biológicas ou sobrenaturais.

A IA poderá criar novas espécies, características físicas, identidades e combinações que não estejam previamente cadastradas.

A geração deverá respeitar as possibilidades e a coerência do universo.

Por exemplo, uma espécie inexistente naquele mundo não deverá aparecer sem uma justificativa narrativa.

A aleatoriedade não significa que todas as características tenham a mesma probabilidade. A IA poderá considerar a lógica do universo, as circunstâncias e a distribuição de possibilidades.

O jogador poderá personalizar alguns aspectos quando desejar.

4.3. Turmas e grupos invocados

Em campanhas envolvendo uma turma ou grupo de pessoas transportadas para outro mundo, cada indivíduo deverá possuir características próprias.

Não gere apenas personagens com nomes diferentes.

Cada pessoa deverá receber sua própria combinação de:

- Classe.
- Atributos.
- Habilidades.
- Potencial.
- Características especiais.
- Personalidade.
- Origem.
- Aptidões.
- Limitações.
- Possibilidades de evolução.

Os integrantes poderão possuir classes e poderes completamente diferentes.

Também deverão ter personalidades, objetivos e comportamentos independentes.

As relações entre os integrantes deverão evoluir de maneira orgânica, podendo surgir amizades, rivalidades, alianças, traições e conflitos.

---

PARTE 5 — ATRIBUTOS, STATUS E PROGRESSÃO

5.1. Sistema de atributos dinâmicos

Não utilize uma estrutura rígida que obrigue todos os universos a possuir os mesmos atributos.

Um universo poderá utilizar atributos tradicionais, enquanto outro poderá criar parâmetros completamente diferentes.

Exemplos:

- Força.
- Agilidade.
- Vitalidade.
- Inteligência.
- Sabedoria.
- Percepção.
- Sorte.
- Mana.
- Energia espiritual.
- Resistência.
- Controle mágico.
- Afinidade elemental.
- Autoridade.
- Existência.
- Atributos conceituais.

Esses são exemplos, não uma lista obrigatória.

A IA deverá poder criar atributos adicionais, modificar os existentes ou estabelecer sistemas completamente diferentes.

Os atributos deverão possuir definições estruturadas, unidades ou escalas quando aplicáveis, regras de cálculo e efeitos associados.

Não presuma que todos os atributos utilizem números inteiros ou escalas tradicionais.

5.2. Progressão

Permita diferentes formas de progressão:

- Níveis e experiência.
- Evolução individual de habilidades.
- Aprimoramento de atributos.
- Evolução de classe.
- Evolução de espécie.
- Despertar de poderes.
- Combinação de habilidades.
- Transformações.
- Mudanças de natureza.
- Evolução conceitual.
- Ascensão a entidades superiores.
- Desenvolvimento de poderes abstratos ou divinos.

Não estabeleça um teto artificial fixo para níveis, atributos ou poder.

A progressão deverá respeitar as regras e possibilidades de cada universo, além das limitações técnicas do programa.

Um personagem poderá alcançar níveis de poder extraordinários, inclusive desenvolver habilidades capazes de interferir nas próprias regras do mundo, quando isso fizer sentido para a campanha.

Não torne a evolução automática ou previsível.

A progressão deverá considerar ações, experiências, condições, descobertas, treinamento, acontecimentos e características individuais.

5.3. Habilidades

As habilidades deverão possuir propriedades extensíveis.

Uma habilidade poderá ter:

- Nome.
- Descrição.
- Categoria.
- Raridade.
- Nível.
- Efeitos.
- Condições de ativação.
- Custos.
- Limitações.
- Tempo de recarga.
- Evoluções.
- Efeitos passivos.
- Efeitos ativos.
- Interações com outras habilidades.
- Possibilidades de combinação.
- Condições especiais de evolução.

Não obrigue todas as habilidades a possuir exatamente as mesmas propriedades.

A IA deverá poder criar habilidades inéditas, inclusive habilidades únicas, abstratas ou conceituais.

O motor deverá registrar suas regras de funcionamento de maneira estruturada, permitindo validar seus efeitos.

---

PARTE 6 — SISTEMA DE INFORMAÇÕES, AVALIAÇÃO E OCULTAÇÃO

Esta é uma mecânica especialmente importante.

A existência de uma informação não significa que todos os personagens possam conhecê-la.

Cada entidade deverá possuir:

1. Estado verdadeiro.
2. Informações conhecidas por cada observador.
3. Informações apresentadas ao observador.
4. Informações falsas ou manipuladas, quando aplicável.

6.1. Visibilidade dos status

Por padrão:

- O jogador poderá consultar seus próprios status completos.
- Os status de outros personagens permanecerão ocultos.
- NPCs não terão acesso automático aos status do jogador.
- O conhecimento de atributos, habilidades e características deverá depender de avaliação, observação, conhecimento ou outros mecanismos do universo.

A interface deverá diferenciar informações desconhecidas, parcialmente conhecidas, estimadas e confirmadas.

6.2. Habilidades de avaliação

Exemplos:

- Avaliação.
- Avaliação Avançada.
- Identificação.
- Análise de Fraquezas.
- Percepção de Energia.
- Visão Verdadeira.

Essas habilidades poderão revelar diferentes quantidades de informações.

Uma avaliação poderá revelar apenas uma classificação aproximada, enquanto outra poderá identificar atributos, habilidades, resistências, fraquezas e características ocultas.

6.3. Ocultação e falsificação

Também deverão existir habilidades e características capazes de:

- Ocultar informações.
- Dificultar avaliações.
- Impedir avaliações.
- Criar informações falsas.
- Alterar informações apresentadas.
- Ocultar apenas determinados atributos.
- Ocultar a própria identidade.
- Detectar tentativas de avaliação.
- Identificar falsificações.

6.4. Interação entre habilidades

Não implemente apenas uma regra fixa de sucesso ou fracasso.

O resultado poderá considerar:

- Poder da habilidade.
- Nível de desenvolvimento.
- Raridade.
- Diferença de poder entre entidades.
- Resistências.
- Condições especiais.
- Características do universo.
- Habilidades complementares.
- Exceções narrativas.

A IA poderá criar interações novas.

O motor deverá registrar os resultados e as regras estabelecidas para impedir comportamentos contraditórios.

6.5. Separação de informações

Uma informação verdadeira não deverá ser automaticamente inserida no conhecimento de todos os NPCs.

Um NPC deverá saber apenas aquilo que:

- Presenciou.
- Ouviu.
- Descobriu.
- Lhe contaram.
- Conseguiu deduzir.
- Já sabia anteriormente.

O sistema deverá controlar essa separação de informações também nas respostas da IA.

---

PARTE 7 — COMBATE E TESTES

7.1. Combate híbrido

O combate deverá combinar narrativa cinematográfica com processamento mecânico real.

A IA deverá descrever:

- Estratégias.
- Movimentos.
- Diálogos.
- Reações.
- Ambiente.
- Consequências.
- Efeitos visuais e sobrenaturais.
- Desenvolvimento da luta.

O motor deverá processar:

- Dano.
- Consumo de recursos.
- Efeitos negativos.
- Resistências.
- Bloqueios.
- Esquivas.
- Acertos críticos.
- Falhas.
- Efeitos de habilidades.
- Condições especiais.
- Ferimentos persistentes.
- Morte.

Não quero um sistema que simplesmente decida tudo por conveniência narrativa.

Entretanto, também não quero um RPG engessado em que toda ação precisa ser reduzida a uma fórmula simples.

7.2. Testes personalizados

Cada universo poderá possuir seu próprio sistema de testes.

O motor deverá suportar:

- Dados.
- Probabilidades.
- Atributos.
- Modificadores.
- Dificuldades.
- Condições ambientais.
- Vantagens e desvantagens.
- Circunstâncias especiais.
- Exceções.
- Resultados críticos.
- Falhas críticas.

A IA poderá criar métodos próprios para determinados universos.

Os resultados deverão ser consistentes e registrados.

Quando houver aleatoriedade, registre os resultados necessários para auditoria e reprodução, inclusive seeds quando aplicável.

7.3. Dificuldade dinâmica

A dificuldade deverá ser dinâmica, mas o mundo não deverá adaptar artificialmente seus desafios para proteger o jogador.

Se o personagem entrar em uma região perigosa, poderá encontrar inimigos muito superiores.

O jogador poderá cometer erros, perder batalhas e sofrer consequências graves.

O mundo não existe exclusivamente para garantir sua vitória.

7.4. Morte, ressurreição e reencarnação

As regras de morte deverão variar conforme o universo e a campanha.

Um mundo poderá ter morte permanente.

Outro poderá possuir ressurreição, reencarnação, regeneração ou outros mecanismos.

A IA deverá definir as regras durante a geração do universo e registrá-las.

Não imponha um sistema universal de morte.

As consequências deverão respeitar as regras estabelecidas, sem alterar retroativamente o funcionamento da morte apenas para salvar o protagonista.

---

PARTE 8 — NPCs E PERSONAGENS AUTÔNOMOS

Os NPCs deverão ser entidades independentes, não apenas personagens que existem para responder ao jogador.

Cada NPC importante deverá possuir informações persistentes:

- Identidade.
- Aparência.
- Personalidade.
- História.
- Objetivos.
- Desejos.
- Medos.
- Conhecimentos.
- Crenças.
- Valores.
- Habilidades.
- Recursos.
- Relacionamentos.
- Memórias.
- Opiniões.
- Segredos.
- Planos.
- Condições físicas e emocionais.

8.1. Autonomia

Os NPCs deverão poder:

- Tomar decisões.
- Criar objetivos.
- Mudar de opinião.
- Desenvolver relações.
- Formar alianças.
- Mentir.
- Trair.
- Abandonar organizações.
- Entrar em organizações.
- Desenvolver rivalidades.
- Criar planos.
- Executar planos fora da presença do jogador.
- Participar de acontecimentos importantes.
- Provocar conflitos.
- Evoluir.
- Morrer.

Personagens importantes poderão surpreender o jogador com decisões não anunciadas, desde que tenham coerência com sua personalidade, motivações e circunstâncias.

A autonomia deverá ser alta, mas não aleatória sem sentido.

8.2. Memória individual

Cada NPC deverá possuir uma memória própria.

Um NPC não poderá saber automaticamente tudo o que aconteceu no mundo.

Ele deverá conhecer apenas o que presenciou, ouviu, descobriu, recebeu como informação ou conseguiu deduzir.

A memória deverá ser persistente, consultável e independente do histórico geral.

8.3. Rotinas e objetivos

NPCs poderão possuir:

- Rotinas.
- Ocupações.
- Responsabilidades.
- Necessidades.
- Projetos.
- Objetivos de curto prazo.
- Objetivos de longo prazo.
- Relações.
- Compromissos.
- Planos individuais.

Suas ações deverão poder gerar acontecimentos mesmo quando o jogador não estiver diretamente envolvido.

8.4. Otimização

Não é necessário simular cada NPC com o mesmo nível de detalhe constantemente.

Crie níveis de simulação.

Personagens próximos ou relevantes poderão receber processamento detalhado.

Personagens distantes poderão ser atualizados por mecanismos mais econômicos.

A otimização não deverá destruir a autonomia nem gerar contradições.

---

PARTE 9 — RELACIONAMENTOS, ROMANCE E VIDA SOCIAL

O sistema deverá suportar relações complexas e orgânicas.

Inclua:

- Amizade.
- Confiança.
- Rivalidade.
- Inimizade.
- Respeito.
- Admiração.
- Medo.
- Interesse romântico.
- Amor.
- Ciúmes.
- Desconfiança.
- Ressentimento.
- Dependência.
- Alianças.
- Relações familiares.
- Relações políticas.

Não transforme relacionamentos em uma simples barra numérica.

Afinidade, confiança e interesse poderão possuir valores internos, mas sua evolução deverá ser influenciada por acontecimentos, comportamentos, decisões e histórico.

9.1. Romance

O sistema deverá suportar:

- Namoro.
- Casamento.
- Triângulos amorosos.
- Poliamor.
- Infidelidade.
- Ciúmes.
- Conflitos.
- Separações.
- Reconciliações.
- Consequências sociais.
- Desenvolvimento afetivo.

Os NPCs deverão possuir preferências, limites, personalidade e autonomia.

Relacionamentos não deverão ser tratados como recompensas automáticas por realizar determinadas ações.

---

PARTE 10 — MISSÕES, EVENTOS E MUNDO VIVO

10.1. Missões

O sistema deverá suportar missões tradicionais e emergentes.

Elas poderão surgir de:

- NPCs.
- Conversas.
- Organizações.
- Facções.
- Acontecimentos.
- Exploração.
- Decisões.
- Conflitos.
- Consequências de ações anteriores.

Inclua:

- Missões principais.
- Secundárias.
- Ocultas.
- Opcionais.
- Dinâmicas.
- Geradas proceduralmente.
- Cadeias de missões.
- Missões com múltiplas soluções.
- Missões que podem falhar ou desaparecer.

Não obrigue o jogador a seguir uma sequência fixa de acontecimentos.

10.2. Eventos mundiais

O mundo deverá continuar evoluindo enquanto a campanha estiver aberta.

Exemplos:

- Guerras.
- Revoluções.
- Assassinatos.
- Mudanças políticas.
- Desastres.
- Descobertas.
- Surgimento de criaturas.
- Queda de reinos.
- Ascensão de organizações.
- Disputas territoriais.
- Eventos sobrenaturais.

Os acontecimentos não deverão depender exclusivamente da participação do jogador.

10.3. Tempo e simulação

O tempo deverá avançar conforme as ações e acontecimentos da campanha.

Quando o programa for fechado, a simulação deverá parar.

Ao abrir novamente, a campanha deverá continuar exatamente do estado em que foi salva, sem avançar automaticamente o tempo offline.

O usuário poderá configurar a intensidade da simulação durante a campanha, quando isso fizer sentido.

---

PARTE 11 — NARRATIVA E CONTROLE DO PROTAGONISTA

A narração deverá ser detalhada, imersiva e semelhante à leitura de um livro ou light novel.

Não quero respostas curtas e superficiais quando a situação exigir desenvolvimento.

A IA deverá produzir:

- Descrições detalhadas.
- Diálogos naturais.
- Reações.
- Expressões.
- Linguagem corporal.
- Descrições ambientais.
- Consequências.
- Construção de tensão.
- Desenvolvimento de personagens.
- Ritmo narrativo adequado.

O ponto de vista poderá variar entre primeira, segunda e terceira pessoa conforme a situação e o estilo narrativo.

11.1. Controle do jogador

O controle será flexível.

A IA poderá narrar pequenas reações, movimentos naturais e ações de ligação para melhorar a fluidez.

Entretanto, não deverá decidir arbitrariamente:

- Decisões importantes.
- Falas importantes.
- Pensamentos relevantes.
- Escolhas morais.
- Ações que alterem significativamente a história.
- Decisões sobre relacionamentos.
- Intenções do personagem.

A IA deverá respeitar a agência do jogador.

Quando uma decisão importante depender do jogador, deverá aguardar sua resposta.

11.2. Ritmo narrativo

A IA deverá adaptar a extensão da narração à situação.

Uma conversa simples não precisa gerar vários parágrafos desnecessários.

Um acontecimento importante poderá receber uma descrição extensa e detalhada.

Evite:

- Repetições.
- Diálogos artificiais.
- Excesso de resumos.
- NPCs que sempre concordam com o jogador.
- Descrições que não acrescentam nada.
- Repetição de informações que já estão visíveis na interface.

---

PARTE 12 — INTERFACE E EXPERIÊNCIA VISUAL

Quero uma interface imersiva, moderna e bem elaborada.

A experiência deverá combinar chat narrativo com painéis completos de RPG.

O sistema visual deverá lembrar a apresentação de sistemas de RPG presentes em animes e light novels.

Inclua elementos como:

- Janelas de status.
- Notificações.
- Mensagens do sistema.
- Alertas.
- Conquistas.
- Títulos.
- Evoluções.
- Desbloqueios.
- Atualizações de habilidades.
- Eventos importantes.

12.1. Telas e módulos

A interface deverá possuir:

1. Tela inicial.
2. Gerenciamento de campanhas.
3. Criação de campanhas.
4. Configuração de universos.
5. Chat principal.
6. Ficha do protagonista.
7. Status.
8. Inventário.
9. Equipamentos.
10. Habilidades.
11. Classes.
12. Mapa.
13. Missões.
14. Diário.
15. Personagens conhecidos.
16. NPCs.
17. Relacionamentos.
18. Organizações e facções.
19. Histórico de acontecimentos.
20. Configurações da campanha.
21. Configurações de IA.
22. Configurações de imagens.
23. Administração e debug.

Os painéis deverão ser organizados e não ocupar desnecessariamente toda a tela.

A interface deverá ser responsiva.

O design deverá possuir identidade visual própria e acabamento profissional.

Não quero uma interface genérica de chatbot com alguns painéis adicionados.

12.2. Interface diegética

O sistema deverá apresentar acontecimentos como se fizessem parte do universo.

Exemplos:

- [SISTEMA] Nova habilidade adquirida.
- [SISTEMA] Evolução de classe disponível.
- [ALERTA] Presença hostil detectada.
- [CONQUISTA] Primeiro contrato concluído.
- [ANÁLISE] Avaliação concluída.
- [SISTEMA] Novo título recebido.

Essas mensagens deverão ser configuráveis e adaptáveis ao universo.

Nem todos os mundos precisam possuir um sistema de status visível ou uma interface sobrenatural. A apresentação deverá respeitar a premissa da campanha.

---

PARTE 13 — GERAÇÃO DE IMAGENS

A plataforma deverá possuir suporte opcional à geração de imagens.

A integração deverá permitir gerar:

- Retratos de personagens.
- NPCs.
- Companheiros.
- Criaturas.
- Monstros.
- Equipamentos.
- Cenários.
- Locais.
- Eventos importantes.
- Ilustrações de acontecimentos narrativos.

A geração de imagens deverá ser independente do funcionamento principal do RPG.

Se o usuário não configurar nenhum serviço de imagens, o sistema deverá continuar funcionando normalmente.

Permita configurar provedores diferentes quando possível.

As imagens geradas deverão poder ser associadas às respectivas entidades e campanhas.

Evite gerar imagens repetidas desnecessariamente.

Considere configurações para controlar frequência, custo, qualidade e prioridade de geração.

---

PARTE 14 — CONTEÚDO ADULTO E TEMAS MADUROS

O sistema deverá permitir campanhas com diferentes níveis de maturidade e temas.

Inclua configurações gerais de intensidade e configurações individuais por categoria.

Categorias possíveis:

- Violência.
- Horror.
- Linguagem pesada.
- Temas psicológicos.
- Romance.
- Intimidade.
- Conteúdo sexual adulto.
- Temas perturbadores.
- Manipulação.
- Abuso de poder.
- Conflitos morais.
- Situações traumáticas.

O objetivo é permitir experiências narrativas maduras, sem tornar todos os universos artificialmente leves ou moralmente simplificados.

A narrativa poderá abordar situações problemáticas, conflitos, manipulação, violência, coerção, abuso de poder e consequências desses acontecimentos.

Não imponha uma regra narrativa de que todos os personagens devem ser moralmente corretos ou de que todos os acontecimentos precisam ser agradáveis.

As configurações poderão ser ajustadas durante a campanha, respeitando as políticas de segurança aplicáveis ao conteúdo gerado.

Personagens envolvidos em conteúdo sexual explícito deverão ser adultos. Violência sexual poderá ser abordada como tema narrativo, com consequências, mas não deverá ser erotizada.

---

PARTE 15 — GERENCIAMENTO DE CAMPANHAS E PERSISTÊNCIA

O salvamento deverá ser contínuo.

Não dependa apenas do histórico de conversa.

O estado da campanha deverá ser armazenado de maneira persistente.

Inclua:

- Salvamento automático.
- Múltiplas campanhas.
- Retomada exata.
- Histórico de eventos.
- Histórico de alterações.
- Backup.
- Restauração.
- Exportação.
- Importação.
- Versionamento.
- Recuperação de erros.

As informações deverão ser organizadas de modo que a IA consiga recuperar acontecimentos antigos sem precisar receber todo o histórico em cada interação.

15.1. Memória em camadas

Implemente diferentes níveis de memória:

Estado atual: informações atuais de personagens, atributos, inventário, localização, relações e mundo.

Memória de acontecimentos: registro dos acontecimentos importantes.

Memória narrativa: resumos de arcos, conflitos e relações.

Memória histórica: capacidade de recuperar acontecimentos antigos mediante consulta.

Memória individual de NPCs: conhecimentos e lembranças particulares de cada personagem.

Registro canônico: fatos confirmados sobre o universo, suas regras, história e entidades.

O sistema deverá distinguir fatos confirmados, rumores, informações desconhecidas e informações falsas.

15.2. Histórico auditável

As alterações importantes deverão gerar registros de eventos.

Exemplos:

- Recebeu um item.
- Perdeu uma habilidade.
- Subiu de nível.
- Foi ferido.
- Iniciou um relacionamento.
- Um NPC morreu.
- Uma facção declarou guerra.
- Uma região foi destruída.

O sistema deverá permitir rastrear a origem das alterações.

15.3. Consistência e recuperação

Implemente mecanismos para:

- Identificar operações duplicadas.
- Recuperar estados anteriores.
- Impedir perda de dados.
- Registrar transações.
- Validar alterações.
- Verificar inconsistências.
- Restaurar backups.

O banco de dados deverá ser a fonte da verdade do sistema.

A IA deverá receber informações relevantes do banco, mas não deverá substituir o banco como fonte oficial.

---

PARTE 16 — MODO ADMINISTRADOR E DEBUG

O programa deverá possuir um modo administrativo separado da experiência normal.

Esse modo será utilizado para desenvolvimento, diagnóstico, manutenção e controle manual das campanhas.

Não deverá depender exclusivamente da interpretação da IA.

Implemente um interpretador de comandos com sintaxe própria.

16.1. Exemplos de comandos

Os exemplos abaixo são ilustrativos e poderão ser adaptados durante o projeto:

/admin help
/admin status player
/admin inspect npc "Nome"
/admin set player.level 100
/admin give player skill "Nome"
/admin teleport player "Local"
/admin create npc "Nome"
/admin world.time advance 30d

/debug show_context
/debug show_memory
/debug show_events
/debug validate_world
/debug inspect_entity "Nome"
/debug inspect_rules
/debug inspect_ai_requests

Você deverá projetar uma sintaxe consistente e documentá-la.

16.2. Recursos administrativos

Permita:

- Consultar dados ocultos.
- Inspecionar entidades.
- Consultar atributos verdadeiros.
- Consultar habilidades.
- Modificar status.
- Adicionar e remover itens.
- Criar personagens.
- Remover personagens.
- Alterar localizações.
- Alterar tempo.
- Criar acontecimentos.
- Consultar regras.
- Consultar memórias.
- Consultar histórico.
- Inspecionar contexto enviado à IA.
- Verificar inconsistências.
- Corrigir problemas.
- Consultar logs.
- Visualizar erros.
- Consultar operações realizadas.
- Inspecionar estado de NPCs.
- Inspecionar estado de campanhas.

16.3. Segurança e integridade

Os comandos deverão ser validados pelo backend.

Operações destrutivas deverão exigir confirmação.

As alterações administrativas deverão ser registradas.

Quando possível, permita desfazer operações.

Diferencie completamente comandos administrativos de habilidades e acontecimentos existentes dentro do universo.

Apenas comandos reconhecidos pelo interpretador deverão executar operações administrativas.

Uma mensagem normal do jogador não deverá ser confundida com um comando administrativo.

O modo deverá possuir proteção de acesso mesmo na execução local e ser preparado para funcionar com autenticação em uma futura hospedagem.

---

PARTE 17 — INTELIGÊNCIA ARTIFICIAL E PROVEDORES

A integração com IA será uma das partes centrais da arquitetura.

Quero suporte tanto a modelos locais quanto a serviços externos.

O programa deverá recomendar modelos de acordo com a tarefa, mas permitir que eu escolha manualmente.

Pesquise as opções disponíveis no momento da implementação e avalie suas condições reais de uso.

Não invente preços, limites gratuitos ou capacidades.

17.1. Provedores

Considere suporte a:

- Modelos locais.
- APIs externas.
- Provedores gratuitos.
- Provedores pagos.
- Diferentes modelos para diferentes tarefas.

Avalie alternativas como servidores locais de modelos e provedores de APIs, verificando a documentação e as condições atuais antes de escolher integrações.

A arquitetura deverá permitir adicionar ou substituir provedores futuramente.

17.2. Abstração de provedores

Crie uma camada independente do provedor.

Trocar o modelo utilizado não deverá exigir reconstruir o motor do RPG.

Centralize:

- Configuração.
- Autenticação.
- Comunicação.
- Tratamento de erros.
- Limites.
- Custos, quando disponíveis.
- Contexto.
- Histórico.
- Respostas estruturadas.

Nunca exponha chaves de API no frontend ou em arquivos versionados.

Utilize variáveis de ambiente e forneça um arquivo de exemplo.

17.3. Recomendações automáticas

O sistema poderá recomendar modelos de acordo com:

- Qualidade narrativa.
- Capacidade de raciocínio.
- Capacidade de seguir instruções.
- Suporte a ferramentas.
- Velocidade.
- Custo.
- Disponibilidade.
- Recursos locais.

O usuário deverá poder aceitar a recomendação ou escolher outro modelo.

Não escolha automaticamente um modelo pago sem informar os custos envolvidos.

17.4. Diferentes responsabilidades da IA

Considere separar as tarefas:

- Narração.
- Interpretação de NPCs.
- Planejamento de acontecimentos.
- Geração de universos.
- Criação de habilidades.
- Simulação de mundo.
- Resumos e memória.
- Interpretação de comandos.

Não é obrigatório utilizar modelos diferentes para tudo.

A arquitetura deverá permitir essa separação e otimizar custos.

17.5. Ferramentas estruturadas

A IA deverá interagir com o motor por meio de operações estruturadas.

Não permita que uma resposta em linguagem natural altere diretamente o banco de dados sem validação.

Fluxo conceitual:

1. A IA interpreta uma ação.
2. Propõe operações.
3. O backend valida.
4. O motor processa os efeitos.
5. O banco registra as alterações.
6. A IA recebe os resultados.
7. A IA narra o acontecimento.

A IA poderá propor mecânicas inéditas, mas o sistema deverá registrar suas definições e validar suas operações.

17.6. Contexto e consumo

Implemente controle de contexto.

Não envie o banco de dados inteiro para cada chamada.

Selecione as informações relevantes para a tarefa atual.

Inclua:

- Resumos.
- Memórias relevantes.
- Estado atual.
- Regras aplicáveis.
- Informações de NPCs envolvidos.
- Acontecimentos relacionados.

Quando possível, apresente informações de uso, tokens e custos estimados.

Implemente limites configuráveis para evitar consumo inesperado.

O programa deverá informar quando uma operação exigir um serviço externo pago.

---

PARTE 18 — ARQUITETURA E TECNOLOGIAS

Inicialmente, o programa será executado localmente no computador do usuário.

Entretanto, a arquitetura deverá permitir hospedagem futura.

O desenvolvimento deverá priorizar:

- Baixo custo.
- Facilidade de manutenção.
- Modularidade.
- Escalabilidade.
- Segurança.
- Extensibilidade.
- Facilidade de instalação.
- Compatibilidade com diferentes provedores.

18.1. Escolha tecnológica

Você deverá analisar e escolher as tecnologias mais adequadas.

Considere uma arquitetura com:

- Frontend independente.
- Backend.
- Banco de dados.
- Motor de RPG.
- Orquestrador de IA.
- Gerenciamento de campanhas.
- Sistema de memória.
- Gerenciamento de NPCs.
- Sistema de eventos.
- Camada de provedores.
- Sistema administrativo.

Justifique as escolhas.

Não utilize tecnologias apenas por serem populares.

Priorize tecnologias maduras, documentadas e adequadas ao escopo.

Considere o custo de instalação e execução no computador do usuário.

18.2. Banco de dados

Escolha um banco adequado para execução local e evolução futura.

Considere iniciar com uma solução simples e permitir migração para outra mais robusta.

Os dados deverão possuir estrutura organizada e consistente.

Não utilize arquivos JSON soltos como substitutos de um banco de dados para toda a aplicação.

JSON poderá ser utilizado para armazenar definições flexíveis de atributos, habilidades, regras e configurações, quando apropriado.

Planeje migrações e versionamento do esquema do banco.

18.3. Organização do projeto

Organize o código em módulos com responsabilidades claras.

Separe, no mínimo:

- Interface.
- Backend.
- Autenticação e permissões.
- Gerenciamento de campanhas.
- Motor de RPG.
- Entidades.
- Regras.
- Combate.
- Progressão.
- NPCs.
- Relacionamentos.
- Eventos.
- Memória.
- Inteligência artificial.
- Provedores.
- Imagens.
- Administração.
- Persistência.
- Testes.

A estrutura final deverá ser apresentada antes da implementação.

18.4. Multiplayer futuro

O lançamento inicial será single-player.

Entretanto, evite decisões arquiteturais que tornem uma futura implementação multiplayer praticamente impossível.

Considere desde o início:

- Identidade de jogadores.
- Propriedade de campanhas.
- Permissões.
- Separação de sessões.
- Concorrência.
- Sincronização de estado.
- Controle de acesso.

Não é necessário implementar multiplayer na primeira versão.

Não permita que a preparação para multiplayer prejudique desnecessariamente a simplicidade da versão local.

---

PARTE 19 — CONFIGURAÇÕES DURANTE A CAMPANHA

O sistema deverá permitir ajustar configurações durante uma campanha, quando isso fizer sentido.

Inclua configurações para:

- Modelo de IA.
- Provedor.
- Criatividade narrativa.
- Intensidade da simulação.
- Frequência de acontecimentos.
- Intensidade dos temas maduros.
- Categorias de conteúdo.
- Geração de imagens.
- Preferências de interface.
- Apresentação de informações.
- Regras configuráveis.
- Outros parâmetros relevantes.

As alterações deverão respeitar o estado atual da campanha.

Não reescreva automaticamente acontecimentos anteriores.

Diferencie:

Configurações de experiência: alteram como o jogo é apresentado ou executado.

Configurações de regras: alteram o funcionamento mecânico do universo.

Alterações narrativas: modificam fatos ou acontecimentos dentro do mundo.

As mudanças de regras deverão ser registradas e versionadas.

Quando uma configuração puder afetar a consistência da campanha, informe o usuário antes de aplicá-la.

---

PARTE 20 — SEGURANÇA E CONFIABILIDADE

Implemente:

- Validação de entradas.
- Tratamento de exceções.
- Proteção de segredos.
- Controle de acesso administrativo.
- Logs.
- Backups.
- Integridade dos dados.
- Proteção contra operações duplicadas.
- Recuperação de falhas.
- Validação das operações propostas pela IA.

A IA deverá ser tratada como um componente não confiável do ponto de vista da integridade do sistema.

Uma resposta inconsistente não poderá corromper diretamente o estado da campanha.

Crie mecanismos para identificar e impedir:

- Alterações contraditórias.
- Duplicação indevida de itens.
- Perda de personagens.
- Atualizações inconsistentes.
- Uso de habilidades sem condições válidas.
- Modificações não autorizadas.
- Referências a entidades inexistentes.
- Perda de histórico.
- Alterações indevidas entre campanhas.

Utilize transações de banco de dados quando apropriado.

Implemente operações idempotentes quando necessário, evitando que uma mesma ação seja aplicada duas vezes por causa de uma repetição de requisição.

---

PARTE 21 — DOCUMENTAÇÃO E ARQUIVOS DE CONTROLE

A documentação deverá acompanhar o desenvolvimento.

Crie e mantenha os seguintes arquivos:

README.md

Deverá conter:

- Apresentação do projeto.
- Funcionalidades.
- Tecnologias.
- Pré-requisitos.
- Instalação.
- Configuração.
- Execução.
- Links para outras documentações.

PROJECT_STATUS.md

Este arquivo é obrigatório e deverá ser atualizado continuamente.

Deverá registrar:

- O que já foi implementado.
- O que está funcionando.
- O que está parcialmente implementado.
- O que ainda falta.
- Quais testes foram executados.
- Quais testes passaram.
- Quais testes falharam.
- Quais problemas foram encontrados.
- Quais decisões técnicas foram tomadas.
- Qual é a próxima tarefa.

Não marque funcionalidades como concluídas sem comprovação.

ARCHITECTURE.md

Documente:

- Arquitetura.
- Módulos.
- Responsabilidades.
- Comunicação entre componentes.
- Fluxo de dados.
- Integração com IA.
- Banco de dados.
- Estratégia de memória.

REQUIREMENTS.md

Mantenha os requisitos funcionais e não funcionais organizados.

DATABASE.md

Documente:

- Entidades.
- Relacionamentos.
- Estrutura.
- Migrações.
- Estratégias de persistência.

AI_PROVIDERS.md

Documente:

- Provedores suportados.
- Configurações.
- Modelos.
- Limitações.
- Custos conhecidos.
- Procedimentos de integração.

ADMIN_COMMANDS.md

Documente todos os comandos administrativos, seus parâmetros, exemplos, permissões e consequências.

CHANGELOG.md

Registre mudanças importantes entre versões.

DECISIONS.md

Registre decisões arquiteturais relevantes, alternativas consideradas e motivos das escolhas.

.env.example

Forneça um exemplo de configuração sem segredos reais.

Não versionar chaves de API, senhas ou informações privadas.

---

PARTE 22 — TESTES OBRIGATÓRIOS

Não considere o projeto concluído apenas porque ele inicia.

Crie testes automatizados para verificar:

1. Criação de campanhas.
2. Separação entre campanhas.
3. Salvamento automático.
4. Retomada após reiniciar.
5. Persistência de atributos.
6. Persistência de inventário.
7. Persistência de habilidades.
8. Evolução de personagens.
9. Combate e aplicação de efeitos.
10. Avaliação de NPCs.
11. Ocultação de status.
12. Falsificação de informações.
13. Memória individual.
14. Eventos mundiais.
15. Relacionamentos.
16. Operações administrativas.
17. Recuperação de backups.
18. Falhas de provedores de IA.
19. Respostas inválidas da IA.
20. Consistência de regras.
21. Geração de universos diferentes.
22. Geração de personagens e turmas.
23. Regras de morte e ressurreição.
24. Retomada sem avanço de tempo offline.
25. Controle de permissões.
26. Isolamento de dados entre campanhas.

Inclua testes que simulem campanhas completas e retomadas de sessões.

Crie testes unitários, testes de integração e testes de fluxos completos, conforme apropriado.

Quando uma funcionalidade depender de uma API paga ou de um modelo externo, crie testes com respostas controladas para verificar o funcionamento interno, mas não confunda esses testes com uma integração real.

Informe claramente quais testes dependem de serviços externos.

---

PARTE 23 — ETAPAS DE IMPLEMENTAÇÃO

Não tente implementar tudo de uma vez.

Primeiro, estabeleça uma arquitetura completa. Depois, desenvolva progressivamente.

Cada etapa deverá resultar em uma versão executável e testável.

ETAPA 0 — Planejamento e arquitetura

- Analisar o ambiente.
- Verificar arquivos existentes.
- Consolidar requisitos.
- Identificar dificuldades.
- Escolher tecnologias.
- Planejar arquitetura.
- Projetar estrutura de diretórios.
- Projetar banco de dados.
- Definir comunicação entre módulos.
- Planejar testes.
- Identificar riscos.

Entregáveis:

- Arquitetura documentada.
- Estrutura inicial do projeto.
- Plano de desenvolvimento.
- Decisões técnicas registradas.

Não encerre o trabalho nesta etapa.

ETAPA 1 — Fundação

- Estrutura do projeto.
- Configuração do ambiente.
- Backend.
- Frontend inicial.
- Banco de dados.
- Gerenciamento de campanhas.
- Salvamento persistente.
- Configurações iniciais.
- Integração inicial com IA.

Critério de conclusão:

Conseguir criar uma campanha, iniciar uma interação com IA, salvar o estado e retomá-la após reiniciar o programa.

ETAPA 2 — Motor de RPG

- Entidades.
- Personagens.
- Atributos dinâmicos.
- Habilidades.
- Inventário.
- Progressão.
- Sistema de regras.
- Operações estruturadas.
- Validação.

Critério de conclusão:

As operações do RPG deverão modificar dados reais e persistentes.

ETAPA 3 — Narrativa e mundo

- Geração de universos.
- Geração de personagens.
- Narrativa.
- NPCs.
- Memória individual.
- Eventos.
- Missões.
- Relacionamentos.
- Mundo vivo.
- Grupos e turmas.

Critério de conclusão:

A campanha deverá possuir continuidade narrativa e acontecimentos persistentes.

ETAPA 4 — Sistemas avançados

- Combate.
- Avaliação e ocultação.
- Falsificação de status.
- Progressão avançada.
- Mecânicas dinâmicas.
- Regras criadas pela IA.
- Simulação de personagens.
- Eventos mundiais.
- Regras dinâmicas de morte.

Critério de conclusão:

Diferentes campanhas deverão conseguir utilizar sistemas de regras significativamente diferentes.

ETAPA 5 — Interface completa

- Painéis.
- Ficha.
- Inventário.
- Habilidades.
- Mapa.
- Missões.
- Diário.
- Relacionamentos.
- Notificações.
- Sistema visual diegético.
- Configurações.

Critério de conclusão:

O jogador deverá conseguir utilizar os principais sistemas pela interface, sem depender de manipulação manual do banco de dados.

ETAPA 6 — Imagens e administração

- Geração de imagens.
- Associação de imagens.
- Comandos administrativos.
- Debug.
- Inspeção de estado.
- Logs.
- Ferramentas de diagnóstico.

Critério de conclusão:

Os recursos administrativos deverão funcionar independentemente da narrativa normal.

ETAPA 7 — Qualidade e expansão

- Testes automatizados.
- Testes de integração.
- Testes de persistência.
- Testes de recuperação.
- Correções.
- Documentação final.
- Otimização.
- Preparação para hospedagem.
- Verificação de segurança.

Critério de conclusão:

O projeto deverá funcionar de maneira consistente, com testes demonstrando os principais fluxos.

---

PARTE 24 — CRITÉRIOS GERAIS DE QUALIDADE

Durante todo o desenvolvimento, observe os seguintes critérios.

Funcionalidade real: cada recurso deverá executar o que promete.

Persistência: os dados deverão continuar existindo depois de fechar e abrir o programa.

Consistência: a IA não poderá alterar silenciosamente fatos ou regras estabelecidas.

Modularidade: novas mecânicas e provedores deverão poder ser adicionados sem reconstruir o sistema.

Criatividade: não transforme o motor em um conjunto fechado de classes e habilidades.

Usabilidade: o programa deverá ser compreensível e utilizável sem conhecimentos avançados de programação.

Custo: evite chamadas desnecessárias a modelos pagos e ofereça alternativas locais quando possível.

Desempenho: a simulação deverá ser otimizada, especialmente com muitos NPCs e acontecimentos.

Documentação: atualize os arquivos de documentação a cada etapa relevante.

Testes: não declare sucesso sem evidências de execução.

24.1. Definição de pronto

Uma funcionalidade só poderá ser marcada como concluída quando:

1. Estiver implementada.
2. Estiver integrada aos componentes necessários.
3. Possuir tratamento de erros.
4. Possuir testes adequados.
5. Tiver sido executada e verificada.
6. Estiver documentada.
7. Não depender de dados falsos ou operações simuladas sem identificação.

Se algum requisito não puder ser atendido, registre a limitação e explique o motivo.

---

PARTE 25 — FORMA DE TRABALHO E CONTINUIDADE

Este projeto provavelmente será desenvolvido em várias sessões.

Portanto, não dependa apenas do histórico da conversa para saber o que está acontecendo.

Antes de começar uma nova sessão de trabalho:

1. Leia PROJECT_STATUS.md.
2. Leia os documentos de arquitetura relevantes.
3. Verifique a estrutura atual.
4. Verifique o estado real do código.
5. Identifique a última etapa concluída.
6. Identifique problemas pendentes.
7. Continue a partir da próxima tarefa.

Ao terminar uma sessão:

1. Atualize PROJECT_STATUS.md.
2. Atualize a documentação afetada.
3. Registre alterações importantes.
4. Execute os testes pertinentes.
5. Informe o que foi realizado.
6. Informe o que falta.
7. Indique a próxima tarefa.

Não recomece o projeto do zero sem necessidade.

Não sobrescreva implementações funcionais apenas para reorganizar o código.

Se identificar um problema arquitetural importante, explique o problema e proponha uma migração segura.

25.1. Execução por etapas

Você poderá dividir cada etapa em subtarefas menores.

Não precisa pedir autorização para cada arquivo ou função.

Entretanto, antes de decisões que alterem significativamente o escopo, removam funcionalidades ou provoquem perda de dados, explique o impacto e solicite autorização.

Se uma decisão técnica não tiver impacto significativo na experiência desejada, escolha a melhor alternativa e documente.

---

PARTE 26 — PRIMEIRA TAREFA

Antes de começar a escrever código, execute as seguintes ações:

1. Analise o ambiente de desenvolvimento disponível.
2. Verifique se já existe algum projeto ou arquivo relacionado.
3. Organize os requisitos deste documento.
4. Identifique possíveis conflitos ou dificuldades técnicas.
5. Proponha uma arquitetura completa.
6. Escolha as tecnologias e justifique.
7. Apresente a estrutura de diretórios planejada.
8. Apresente o modelo inicial do banco de dados.
9. Apresente como será a comunicação entre a IA e o motor de RPG.
10. Explique como serão implementadas a memória e a persistência.
11. Explique como o sistema permitirá criar regras e habilidades dinâmicas.
12. Apresente o cronograma de implementação.
13. Identifique os principais riscos técnicos.
14. Explique como o projeto será testado.

Depois dessa análise, comece a implementação.

Não encerre o trabalho apenas com o planejamento.

Não tente implementar todas as funcionalidades de uma vez.

Construa uma base sólida e funcional, avance pelas etapas e mantenha o projeto executável.

---

PRINCÍPIO CENTRAL DO PROJETO

O AI RPG Engine deverá oferecer uma experiência de RPG em que a inteligência artificial tenha liberdade criativa para construir histórias, personagens, mundos, regras e mecânicas extraordinárias, enquanto o motor de jogo garante que os acontecimentos, as regras e os dados permaneçam consistentes e persistentes.

Quero um mundo que pareça vivo.

Quero personagens que tenham suas próprias vidas, objetivos, sentimentos e decisões.

Quero campanhas que possam começar de maneiras completamente diferentes.

Quero sistemas que possam evoluir e criar possibilidades que não foram previamente programadas.

Quero liberdade narrativa sem perder a estrutura de um verdadeiro RPG.

Não desenvolva apenas um chatbot com aparência de RPG. Desenvolva uma plataforma de RPG cuja inteligência artificial seja parte fundamental de seu funcionamento.
> "AI RPG ENGINE — ESPECIFICAÇÃO COMPLETA E PROMPT MESTRE DE DESENVOLVIMENTO" (versão 1.0).
>
> Este arquivo é a fonte dos requisitos. O Claude Code consulta este texto quando
> precisa do detalhe de alguma parte (por exemplo, "Parte 6 — Sistema de informações").
>
> Ajustes aprovados em relação à versão 1.0 estão registrados em `docs/DECISIONS.md`
> e valem por cima do texto original.
