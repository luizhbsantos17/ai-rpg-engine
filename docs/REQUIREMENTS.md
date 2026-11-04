# REQUIREMENTS — Requisitos organizados

O detalhe de cada requisito está na parte indicada de `docs/SPEC.md`.
Status possíveis: `pendente`, `parcial`, `pronto` (só com teste executado).

## Funcionais
| ID | Requisito | SPEC | Etapa | Status |
|---|---|---|---|---|
| RF-01 | Criar, listar, abrir e excluir campanhas independentes | 2.1, 15 | 1 | pronto |
| RF-02 | Salvamento automático e retomada exata após reiniciar | 15 | 1 | pronto |
| RF-03 | Turno de jogo com IA (entrada → narração) | 11, 17.5 | 1 | pronto |
| RF-04 | Camada de provedores (local e externo) com troca sem mexer no motor | 17.1–17.2 | 1 | parcial (local pronto; externo na Etapa 2+) |
| RF-05 | Entidades, atributos dinâmicos, habilidades, inventário persistentes | 5 | 2 | pronto |
| RF-06 | Pipeline de operações estruturadas com validação | 17.5, 20 | 2 | pronto (qualidade das escolhas depende do modelo) |
| RF-07 | Testes com dados, modificadores e seeds registradas | 7.2 | 2 | pronto |
| RF-08 | Progressão sem teto fixo | 5.2 | 2 | parcial (atributos e níveis sem teto; regras de progressão próprias na Etapa 4) |
| RF-09 | Geração aleatória de campanhas, com regenerar, personalizar e preservar elementos | 3 | 3 | pronto |
| RF-10 | Geração de protagonista, reencarnação e turmas com indivíduos distintos | 4 | 3 | parcial (protagonista e turma prontos; reencarnação detalhada depende da premissa) |
| RF-11 | Registro canônico com versões (sem sobrescrever o passado) | 3.4 | 3 | pronto |
| RF-12 | NPCs com memória individual, objetivos e autonomia | 8 | 3 | pronto (qualidade das decisões depende do modelo) |
| RF-13 | Relacionamentos multidimensionais e romance | 9 | 3 | pronto (dimensões livres incluem afeto/ciúme; romance é narrativo) |
| RF-14 | Missões tradicionais e emergentes | 10.1 | 3 | pronto |
| RF-15 | Relógio do mundo sem avanço offline; eventos mundiais | 10.2–10.3 | 3–4 | pronto |
| RF-16 | Combate híbrido (narrativo + mecânico) | 7.1 | 4 | parcial (testes, dano condicional, efeitos, morte; sem ordem de iniciativa dedicada) |
| RF-17 | Avaliação, ocultação e falsificação de informações | 6 | 4 | pronto |
| RF-18 | Regras de morte por universo | 7.4 | 4 | pronto |
| RF-19 | Mecânicas e regras criadas pela IA, validadas | 5.3, 6.4 | 4 | pronto |
| RF-20 | Interface completa (23 telas/módulos) e mensagens diegéticas | 12 | 5 | pendente |
| RF-21 | Geração opcional de imagens associadas a entidades | 13 | 6 | pendente |
| RF-22 | Modo administrador e debug com interpretador próprio | 16 | 6 | pendente |
| RF-23 | Configurações durante a campanha (experiência × regras × narrativa) | 19 | 5 | pendente |
| RF-24 | Níveis de maturidade por categoria, limitados pelo provedor | 14, D-007 | 5 | pendente |
| RF-25 | Backup, restauração, exportação e importação | 15 | 6–7 | pendente |

## Não funcionais
| ID | Requisito | SPEC |
|---|---|---|
| RNF-01 | Banco é a fonte da verdade; IA tratada como não confiável | 15.3, 20 |
| RNF-02 | Isolamento total entre campanhas | 2.1, 22 |
| RNF-03 | Operações idempotentes e transacionais | 20 |
| RNF-04 | Segredos só em variáveis de ambiente | 17.2 |
| RNF-05 | Controle de contexto e de gasto com IA | 17.6 |
| RNF-06 | Código modular, sem arquivos gigantes | 18.3 |
| RNF-07 | Instalação simples no computador do usuário | 18 |
| RNF-08 | Preparado para hospedagem e multiplayer futuros, sem implementá-los | 18.4 |
| RNF-09 | Interface responsiva com identidade visual própria | 12 |
| RNF-10 | Documentação atualizada a cada etapa | 21 |
