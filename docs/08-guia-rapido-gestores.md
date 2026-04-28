# Guia Rapido para Gestores — Indicadores OCDE/PGD ICMBio

Este guia e para **gestores e lideres de equipe** que precisam entender os indicadores OCDE/PGD sem precisar conhecer banco de dados ou SQL. Se voce e analista buscando as consultas, consulte [06-indicadores-ocde-mysql.md](06-indicadores-ocde-mysql.md).

---

## 1. Contexto: por que esses indicadores existem?

O ICMBio participa de um piloto conduzido pela OCDE, pelo MGI e pela UFRN para transformar o **Programa de Gestao e Desempenho (PGD)** de um simples controle de frequencia em um verdadeiro instrumento de gestao de resultados.

A ideia central e medir o que realmente aconteceu: as metas foram cumpridas? O trabalho foi bem distribuido? As horas foram usadas de forma proporcional?

Os indicadores sao calculados a partir dos dados que voce e sua equipe ja registram no PETRVS — nao e necessario preencher nada novo.

---

## 2. Como o PETRVS organiza as informacoes

O PETRVS trabalha com dois tipos de planos. Entender a diferenca entre eles e a chave para interpretar os indicadores.

### Plano de Entregas (PE) — o contrato da unidade

E o conjunto de resultados que a **unidade** se compromete a entregar num periodo (semestre ou ano). Cada entrega tem:

- Um **nome** descrevendo o resultado esperado
- Uma **meta planejada** (quanto vai ser entregue, em numeros)
- Uma **meta executada** (quanto foi de fato entregue)

**Analogia ICMBio:** e como o planejamento anual de uma coordenacao. A CGOV define no inicio do ano: "vamos produzir 3 relatorios de governanca, realizar 2 auditorias e capacitar 50 servidores." Cada item desse e uma *entrega*.

### Plano de Trabalho (PT) — a agenda do servidor

E o planejamento individual de cada servidor. Nele, o servidor indica:

- Em quais entregas da unidade vai trabalhar
- Qual percentual da sua carga horaria vai dedicar a cada uma

**Analogia ICMBio:** e como a agenda de um auditor que diz: "vou dedicar 40% do meu tempo a auditoria X, 30% ao relatorio Y e 30% a capacitacao Z."

A combinacao de PE + PT e o que permite calcular: *as metas foram atingidas? o esforco foi distribuido de forma equilibrada?*

---

## 3. Os indicadores e o que cada um responde

### I02 — Taxa de cumprimento das entregas (por unidade)

**Pergunta:** De todas as entregas planejadas pela unidade, quantas foram efetivamente concluidas?

**Como interpretar:**
- 100%: todas as entregas foram concluidas
- 80%: 8 de cada 10 entregas foram concluidas
- Abaixo de 70%: sinal de atencao — revisar planejamento ou execucao

**Nivel de detalhe:** uma linha por unidade (visao gerencial)

**Exemplo de resultado:**

| unidade | total planejadas | concluidas | taxa |
|---|---|---|---|
| CGOV | 20 | 17 | 85.00% |
| AUDIT | 12 | 10 | 83.33% |
| DIMAN | 30 | 18 | 60.00% |

---

### I03 — Taxa de cumprimento de metas por entrega

**Pergunta:** Para cada entrega individualmente, qual percentual da meta foi atingido?

**Como interpretar:**
- 100%: meta atingida exatamente
- Acima de 100%: superexecutada (mais que o planejado)
- Abaixo de 100%: subexecutada (nao atingiu a meta)
- Classificacao automatica: *Superexecutada / No alvo / Subexecutada*

**Nivel de detalhe:** uma linha por entrega (visao auditoria/detalhamento)

**Quando usar:** quando o I02 mostra problema em uma unidade e voce quer saber *quais entregas especificas* ficaram abaixo do esperado.

---

### I04 — Indice de atingimento de metas (score medio por unidade)

**Pergunta:** Em media, qual o percentual de atingimento das metas em cada unidade?

**Como interpretar:**
- E a "media do boletim" da unidade — um unico numero resumindo o desempenho geral
- 100%: atingiu exatamente todas as metas em media
- Acima de 100%: superou as metas em media (cuidado: pode ser meta subestimada)
- Abaixo de 100%: ficou abaixo em media

**Diferenca pratica em relacao ao I02:**

| Indicador | O que mede | Exemplo |
|---|---|---|
| I02 | Quantas entregas foram concluidas (sim/nao) | 8 de 10 = 80% |
| I04 | Qual foi o nivel de execucao em media | Media = 92% do que era esperado |

Uma unidade pode ter I02 = 80% (2 entregas nao concluidas) mas I04 = 95% (essas 2 entregas chegaram perto da meta, so nao cruzaram a linha).

---

### I05 — Distribuicao das entregas entre os servidores

**Pergunta:** As entregas estao distribuidas de forma equilibrada entre os servidores, ou esta concentrada em poucas pessoas?

**Como interpretar:**
- Mostra quantas entregas cada servidor tem dentro da unidade
- Compara cada servidor com a media da unidade
- Classificacao: *Acima da media / Na media / Abaixo da media*

**Sinal de atencao:** se poucos servidores concentram a maioria das entregas, ha risco de gargalo (o que acontece se essas pessoas se afastarem?).

**Exemplo de resultado:**

| unidade | servidor | entregas | media unidade | posicao |
|---|---|---|---|---|
| CGOV | Ana Silva | 8 | 5.00 | Acima da media |
| CGOV | Carlos Souza | 5 | 5.00 | Na media |
| CGOV | Maria Lima | 2 | 5.00 | Abaixo da media |

---

### I06 — Grau de responsabilidade pelas entregas

**Pergunta:** Cada entrega depende de um unico servidor ou e responsabilidade compartilhada de varios?

**Como interpretar:**
- Mostra quantas entregas tem apenas 1 responsavel, 2, 3, ou 4+
- Muitas entregas com *1 servidor*: alta concentracao individual — risco de gargalo
- Muitas entregas com *4+ servidores*: alta diluicao — pode nao ter dono claro
- Equilibrio entre as faixas: sinal saudavel

**Exemplo de resultado:**

| unidade | tamanho do grupo | total de entregas |
|---|---|---|
| AUDIT | 1 servidor | 12 |
| AUDIT | 2 servidores | 5 |
| AUDIT | 3 servidores | 2 |
| AUDIT | 4+ servidores | 1 |

Neste exemplo: 12 entregas da AUDIT sao individuais (risco de gargalo), 8 sao compartilhadas.

---

### I07 — Horas por entrega — planejadas (valor absoluto)

**Pergunta:** Quantas horas de trabalho foram planejadas para cada entrega?

**Como interpretar:**
- Mostra o total de horas dedicadas a cada entrega no periodo
- Leva em conta: dias uteis do periodo, jornada diaria (8h padrao) e o percentual de dedicacao declarado por cada servidor no Plano de Trabalho
- Entregas com mais horas sao as mais "pesadas" em esforco

**Quando usar:** para identificar quais entregas consomem mais capacidade da equipe.

---

### I08 — Proporcao de horas por entrega (percentual)

**Pergunta:** Qual percentual da capacidade total da unidade esta sendo dedicado a cada entrega?

**Como interpretar:**
- Similar ao I07, mas em percentual em vez de horas absolutas
- Soma das proporcoes nao precisa ser 100% (parte das horas pode estar em atividades nao vinculadas a entregas)
- Entregas com proporcao muito alta merecem atencao — sao as que dominam a agenda

**Exemplo de resultado:**

| entrega | horas planejadas | total disponivel unidade | proporcao |
|---|---|---|---|
| Relatorio de Governanca | 300h | 1200h | 25.00% |
| Capacitacao Servidores | 180h | 1200h | 15.00% |
| Auditoria Interna | 120h | 1200h | 10.00% |

---

## 4. Como solicitar uma analise

Se voce nao tem acesso ao banco de dados ou ao DBeaver, solicite a analise para o analista responsavel da sua unidade. Forne�a:

1. **Periodo de analise:** data de inicio e data de fim (ex: 01/01/2025 a 31/12/2025)
2. **Indicador desejado:** I02, I03, I04, I05, I06, I07 ou I08
3. **Filtro de unidade:** se quiser ver apenas sua unidade, informe a sigla (ex: CGOV)

O analista ira ajustar os parametros na consulta e exportar o resultado em CSV ou Excel.

---

## 5. Como ler um resultado exportado

Os resultados sao exportados em tabelas com as seguintes convencoes:

| Convencao | Significado |
|---|---|
| `N.I.` | Nao Informado — campo vazio no sistema |
| `deleted_at` nao nulo | Registro excluido logicamente (ainda aparece se incluir_excluidos = 1) |
| Sufixo `_perc` | Valor em percentual (ex: `taxa_cumprimento_perc`) |
| Sufixo `_total` | Contagem absoluta |
| Sufixo `_media` | Media aritmetica |

---

## 6. Perguntas frequentes

**Por que algumas entregas aparecem como "N.I."?**
O campo de descricao da entrega esta vazio no PETRVS. Isso nao impede o calculo, mas indica preenchimento incompleto no sistema.

**Por que o I04 pode ser acima de 100%?**
Porque a media considera o quanto cada entrega foi executada — se varias entregas superaram a meta, a media sobe acima de 100%. Pode ser bom desempenho ou meta subestimada no planejamento.

**O indicador I01 (regimes de trabalho) existe?**
Ainda nao esta implementado nesta versao MySQL. Depende do mapeamento de tabelas de modalidade que esta em andamento.

**Quais indicadores de avaliacao (notas) existem?**
Os indicadores I09, I10, I11 e I12 (avaliacoes de planos de trabalho e entregas) estao mapeados para implementacao futura.

---

## 7. Proximos passos

- Para entender o contexto estrategico completo do piloto OCDE/PGD: [05-contexto-ocde-pgd.md](05-contexto-ocde-pgd.md)
- Para executar as consultas voce mesmo: [06-indicadores-ocde-mysql.md](06-indicadores-ocde-mysql.md)
- Para entender a estrutura tecnica do banco: [07-estrutura-banco-dados.md](07-estrutura-banco-dados.md)
