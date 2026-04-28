# Contexto Estrategico dos Indicadores PGD (Projeto OCDE/ICMBio)

Este documento consolida as diretrizes do projeto piloto da OCDE no ICMBio para o Programa de Gestao e Desempenho (PGD), servindo como base de contexto para as consultas SQL deste repositorio.

---

## 1. Visao Geral

O projeto piloto **"Fortalecendo a capacidade organizacional no Brasil"** (OCDE, MGI, SPU, ICMBio, UFRN) visa transformar o PGD de uma ferramenta de controle de frequencia em um instrumento de **gestao de desempenho e tomada de decisao baseada em evidencias**.

Este esforco esta diretamente alinhado as competencias da **Coordenacao de Governanca (CGOV)** (Portaria ICMBio n. 5.592/2025), fornecendo dados quantitativos para:

- Monitoramento da Cadeia de Valor e Alinhamento Estrategico
- Dimensionamento da Forca de Trabalho (DFT)
- Governanca, Cultura de Controle e Gestao de Riscos

O *Performance Toolkit* da OCDE estabelece **12 indicadores chave**, divididos em 4 eixos estruturantes.

---

## 2. Os 4 Eixos e os 12 Indicadores

### Eixo 1: Trabalho Remoto

Mede como a forca de trabalho esta distribuida entre os regimes de atuacao (presencial, hibrido, teletrabalho). E o contexto que enquadra todos os outros indicadores — o regime de trabalho afeta diretamente como os planos sao estruturados e executados.

| Indicador | Descricao resumida | Tabela base | Status |
| --- | --- | --- | --- |
| I01 | Proporcao de servidores por regime de trabalho | `planos_trabalhos` + `tipos_modalidades` | Disponivel (validar campo) |

### Eixo 2: Execucao

Mede o cumprimento das metas pactuadas nos Planos de Entregas. Responde se o que foi planejado foi efetivamente entregue, tanto em nivel binario (cumpriu ou nao) quanto em nivel escalar (qual percentual da meta foi atingido).

| Indicador | Descricao resumida | Tabela base | Status |
| --- | --- | --- | --- |
| I02 | Taxa de cumprimento das entregas (por unidade) | `planos_entregas_entregas` | Disponivel |
| I03 | Taxa de cumprimento de metas por entrega | `planos_entregas_entregas` | Disponivel |
| I04 | Indice de atingimento de metas — score medio por unidade | `planos_entregas_entregas` | Disponivel |

### Eixo 3: Carga de Trabalho

Mede como o esforco esta distribuido entre servidores e entregas. Identifica concentracao de trabalho, gargalos de dependencia e proporcao de horas alocadas por entrega.

| Indicador | Descricao resumida | Tabela base | Status |
| --- | --- | --- | --- |
| I05 | Distribuicao das entregas entre os servidores | `planos_trabalhos_entregas` | Disponivel |
| I06 | Grau de responsabilidade pelas entregas | `planos_trabalhos_entregas` | Disponivel |
| I07 | Horas por entrega — planejadas (absoluto) | `planos_trabalhos_entregas` | Disponivel |
| I08 | Proporcao de horas por entrega — planejadas (%) | `planos_trabalhos_entregas` | Disponivel |

### Eixo 4: Desempenho e Avaliacao

Mede a qualidade percebida do desempenho via as avaliacoes registradas no PETRVS. Complementa o Eixo 2: enquanto I02-I04 medem *o que foi entregue*, os indicadores deste eixo medem *como o trabalho foi avaliado*. O I12 verifica se as avaliacoes individuais (PT) sao coerentes com as avaliacoes coletivas (PE) da mesma unidade.

| Indicador | Descricao resumida | Tabela base | Status |
| --- | --- | --- | --- |
| I09 | Media da avaliacao do Plano de Trabalho por unidade | `avaliacoes` + `tipos_avaliacoes_notas` | Disponivel (validar campos) |
| I10 | Percentual de avaliacoes inadequadas (nota 2) | `avaliacoes` + `tipos_avaliacoes_notas` | Disponivel (validar campos) |
| I11 | Percentual de avaliacoes excepcionais (nota 5) | `avaliacoes` + `tipos_avaliacoes_notas` | Disponivel (validar campos) |
| I12 | Coerencia entre avaliacao do PT e do PE por unidade | `avaliacoes` + `planos_entregas` | Disponivel (validar campos) |

---

## 3. Formulas dos 12 Indicadores

### I01 — Proporcao de servidores por regime de trabalho

```text
I (por regime) = (A / B) * 100
A = Servidores distintos com planos ativos no regime R durante o periodo
B = Total de servidores distintos com planos ativos no periodo (todos os regimes)

Regimes tipicos: Presencial / Hibrido / Teletrabalho (nomes conforme tipos_modalidades)
```

Variante adicional: proporcao por regime dentro de cada unidade (usa `PARTITION BY unidade_sigla`).

---

### I02 — Taxa de cumprimento das entregas

```text
I = (A / B) * 100
A = Entregas concluidas (progresso_realizado >= progresso_esperado)
B = Total de entregas planejadas no periodo com meta valida (progresso_esperado > 0)

Nivel de agregacao: por unidade

Classificacao opcional por grupo de performance:
  A (>= 90%)  -> Alto desempenho
  B (70-89%)  -> Bom desempenho
  C (50-69%)  -> Desempenho intermediario
  D (< 50%)   -> Baixo desempenho
```

---

### I03 — Taxa de cumprimento de metas por entrega

```text
I = (A / B) * 100  (calculado por entrega individual)
A = progresso_realizado
B = progresso_esperado

Classificacao automatica:
  A > B  -> Superexecutada
  A = B  -> No alvo
  A < B  -> Subexecutada

Nivel de agregacao: por entrega (uma linha por entrega)
```

---

### I04 — Indice de atingimento de metas

```text
I = (SUM(Ai / Bi) / C) * 100
Ai = progresso_realizado de cada entrega i
Bi = progresso_esperado de cada entrega i
C  = total de entregas validas da unidade

Equivalente a: AVG(proporcao_atingimento) * 100 por unidade
Nivel de agregacao: por unidade (score medio)
```

---

### I05 — Distribuicao das entregas entre os servidores

```text
Media da unidade = Total de atribuicoes distintas / Total de servidores com plano ativo

Por servidor:
  posicao = 'Acima da media' se qtd_entregas_servidor > media_unidade
  posicao = 'Abaixo da media' se qtd_entregas_servidor < media_unidade
  posicao = 'Na media' se igual

Nivel de agregacao: por servidor dentro de cada unidade
```

---

### I06 — Grau de responsabilidade pelas entregas

```text
Por entrega:
  qtd_responsaveis = COUNT(DISTINCT usuario_id) dos planos vinculados a entrega

Agrupamento em faixas:
  '1 servidor'    -> entrega individual
  '2 servidores'  -> dupla
  '3 servidores'  -> trio
  '4+ servidores' -> grupo amplo

Nivel de agregacao: contagem de entregas por faixa, por unidade
```

---

### I07 — Horas por entrega — planejadas (absoluto)

```text
Horas_entrega = SUM(horas_planejadas_plano_i * forca_trabalho_i / 100)

Onde para cada plano de trabalho i vinculado a entrega:
  horas_planejadas_plano_i = dias_uteis_plano * horas_por_dia
  dias_uteis_plano = dias no periodo, excluindo fins de semana e feriados nacionais
  forca_trabalho_i = percentual declarado em planos_trabalhos_entregas.forca_trabalho

Nivel de agregacao: por entrega (soma de contribuicoes de todos os servidores)
```

---

### I08 — Proporcao de horas por entrega — planejadas (%)

```text
I = (A / B) * 100
A = Horas alocadas a entrega (resultado do I07)
B = Total de horas disponiveis de todos os servidores da unidade no periodo
    (soma de horas_planejadas por plano, SEM aplicar forca_trabalho — capacidade bruta)

Nota: a soma das proporcoes de todas as entregas de uma unidade NAO precisa ser 100%.
O restante representa horas disponiveis nao atribuidas explicitamente a nenhuma entrega.

Nivel de agregacao: por entrega + proporcao em relacao a capacidade da unidade
```

---

### I09 — Media da avaliacao do Plano de Trabalho

```text
I = AVG(nota_avaliacao_PT) por unidade

Onde:
  nota_avaliacao_PT = valor numerico de tipos_avaliacoes_notas.nota
  Filtro: avaliacoes com plano_trabalho_consolidacao_id preenchido (avaliacao de PT)

Escala de notas:
  1 = Nao executado
  2 = Inadequado
  3 = Adequado
  4 = Alto desempenho
  5 = Excepcional

Nivel de agregacao: por unidade
```

---

### I10 — Percentual de avaliacoes inadequadas (nota 2)

```text
I = (A / B) * 100
A = COUNT(avaliacoes de PT com nota = 2) por unidade
B = COUNT(total de avaliacoes de PT) por unidade

Nota 2 = avaliacao classificada como "inadequada" ou equivalente na escala do sistema

Nivel de agregacao: por unidade
```

---

### I11 — Percentual de avaliacoes excepcionais (nota 5)

```text
I = (A / B) * 100
A = COUNT(avaliacoes de PT com nota = 5) por unidade
B = COUNT(total de avaliacoes de PT) por unidade

Nota 5 = avaliacao classificada como "excepcional" ou equivalente na escala do sistema

Nivel de agregacao: por unidade
```

---

### I12 — Coerencia entre avaliacao do PT e do PE

```text
Diferenca_unidade = |media_nota_PT - media_nota_PE| por unidade

Onde:
  media_nota_PT = AVG(nota) das avaliacoes de Planos de Trabalho da unidade
  media_nota_PE = AVG(nota) das avaliacoes de Planos de Entrega da unidade

Classificacao da coerencia:
  |diferenca| <= 1.0  -> 'Coerente'
  |diferenca| <= 2.0  -> 'Divergencia moderada'
  |diferenca|  > 2.0  -> 'Alta divergencia'

Interpretacao: se a unidade avalia bem os PT individuais mas mal o PE coletivo (ou vice-versa),
ha uma incoerencia que merece investigacao — pode indicar avaliacao por cordialidade,
subestimacao coletiva ou desalinhamento entre lider e equipe.
Quanto maior a divergencia, menor a maturidade da gestao de desempenho da unidade.

Nivel de agregacao: por unidade (uma linha por unidade com PT e PE avaliados)
```

---

## 4. Regras gerais de uso das consultas

### Bloco de parametros padrao

Todas as consultas usam um bloco `parametros` no inicio:

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
)
```

- Ajuste `data_inicio` e `data_fim` conforme o periodo de analise.
- `incluir_excluidos = 0`: apenas registros ativos (`deleted_at is null`).
- `incluir_excluidos = 1`: inclui registros excluidos logicamente (util para auditoria).

### Exclusao logica no PETRVS

O PETRVS nao apaga registros fisicamente. Registros excluidos recebem uma data em `deleted_at`. O campo `incluir_excluidos` controla se esses registros entram nos indicadores.

### Nomenclatura das entregas

O campo principal do nome da entrega e `descricao`. Se estiver vazio, usa-se `descricao_entrega` como fallback. Nenhuma entrega deve aparecer com nome em branco nos resultados.

### Nota sobre I01 e I09-I12

Esses cinco indicadores dependem de tabelas (`tipos_modalidades`, `tipos_avaliacoes_notas`) cujo conteudo exato varia conforme a versao e configuracao do PETRVS. Antes de executar, rode as consultas de mapeamento documentadas em [06-indicadores-ocde-mysql.md](06-indicadores-ocde-mysql.md) para confirmar os nomes de campo e os valores de referencia.

---

## 5. Tabelas do PETRVS utilizadas

| Tabela | Indicadores | Campos criticos |
| --- | --- | --- |
| `planos_entregas_entregas` | I02, I03, I04, I07, I08 | `progresso_esperado`, `progresso_realizado`, `data_fim`, `unidade_id` |
| `planos_trabalhos` | I01, I05, I06, I07, I08 | `usuario_id`, `unidade_id`, `tipo_modalidade_id`, `data_inicio`, `data_fim` |
| `planos_trabalhos_entregas` | I05, I06, I07, I08 | `plano_trabalho_id`, `plano_entrega_entrega_id`, `forca_trabalho` |
| `planos_entregas` | I07, I08, I12 | `unidade_id`, `data_inicio`, `data_fim` |
| `unidades` | Todos | `id`, `sigla`, `nome` |
| `usuarios` | I05, I06, I09 | `id`, `nome` |
| `tipos_modalidades` | I01 | `id`, `nome` |
| `avaliacoes` | I09, I10, I11, I12 | `plano_trabalho_consolidacao_id`, `plano_entrega_id`, `tipo_avaliacao_id`, `tipo_avaliacao_nota_id` |
| `planos_trabalhos_consolidacoes` | I09, I10, I11, I12 | `id`, `plano_trabalho_id` |
| `tipos_avaliacoes` | I09, I10, I11, I12 | `id`, `nome` |
| `tipos_avaliacoes_notas` | I09, I10, I11, I12 | `id`, `nota` (validar nome) |
