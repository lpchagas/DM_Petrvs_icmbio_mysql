# Indicadores OCDE do PGD no ICMBio — Frame MySQL (origem)

Este documento contem as consultas SQL para todos os 12 indicadores do *Performance Toolkit* OCDE/PGD, adaptadas para execucao direta na base original PETRVS em MySQL, sem datamart.

Para o contexto estrategico, formulas e status de cada indicador, consulte [05-contexto-ocde-pgd.md](05-contexto-ocde-pgd.md).

Eixo 1 — Trabalho Remoto

- I01: Proporcao de servidores por regime de trabalho

Eixo 2 — Execucao

- I02: Taxa de cumprimento das entregas
- I03: Taxa de cumprimento de metas por entrega
- I04: Indice de atingimento de metas

Eixo 3 — Carga de Trabalho

- I05: Distribuicao das entregas entre os servidores
- I06: Grau de responsabilidade pelas entregas
- I07: Horas por entrega — planejadas
- I08: Proporcao de horas por entrega — planejadas

Eixo 4 — Desempenho e Avaliacao (requer validacao de campos — ver secao de mapeamento antes de executar)

- I09: Media da avaliacao do Plano de Trabalho
- I10: Percentual de avaliacoes inadequadas (nota 2)
- I11: Percentual de avaliacoes excepcionais (nota 5)
- I12: Coerencia entre avaliacao do PT e do PE

## 1. Regras gerais de uso

### Como usar no DBeaver

1. Conecte no MySQL `petrvs_icmbio`.
2. Abra um SQL Editor.
3. Execute a consulta completa.
4. Ajuste as datas no bloco `parametros`.

### Padrao de datas

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
)
```

- `incluir_excluidos = 0`: considera apenas registros ativos (`deleted_at is null`)
- `incluir_excluidos = 1`: inclui tambem registros excluidos logicamente

## 2. Mapeamento logico no MySQL (origem)

Para o Indicador 2 no frame MySQL:

- tabela base: `planos_entregas_entregas`
- unidade: `unidades` (via `unidade_id`)
- meta planejada: `progresso_esperado`
- meta executada: `progresso_realizado`
- entrega concluida: `progresso_realizado >= progresso_esperado`

Observacao de nomenclatura:

- o nome principal da entrega deve priorizar `descricao`
- se `descricao` estiver vazio, usar `descricao_entrega`
- para os Indicadores 2 e 3, a mesma regra de nomenclatura deve ser mantida

---

## Indicador I01 — Proporcao de servidores por regime de trabalho (MySQL)

### O que esse indicador responde (I01)

A pergunta central e: qual e a distribuicao da forca de trabalho do ICMBio entre os regimes presencial, hibrido e teletrabalho?

E o ponto de partida do *Performance Toolkit* da OCDE porque o regime molda como cada servidor estrutura seu Plano de Trabalho e, por consequencia, afeta todos os indicadores de execucao (Eixo 2) e carga (Eixo 3). Uma unidade majoritariamente em teletrabalho tem dinamica de distribuicao de entregas diferente de uma unidade presencial.

**Tabela base:** `planos_trabalhos` (campo `tipo_modalidade_id`) → `tipos_modalidades`

### Mapeamento I01: confirmar regimes no banco (executar primeiro)

```sql
-- Regimes cadastrados em tipos_modalidades
select id, nome, descricao
from tipos_modalidades
order by nome;

-- Preenchimento do campo tipo_modalidade_id nos planos de trabalho
select
    count(*) as total_planos,
    sum(case when tipo_modalidade_id is null then 1 else 0 end) as sem_modalidade,
    sum(case when tipo_modalidade_id is not null then 1 else 0 end) as com_modalidade
from planos_trabalhos
where deleted_at is null;
```

### I01 — Consulta: proporcao geral por regime

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
servidores_no_periodo as (
    select distinct
        pt.usuario_id,
        coalesce(tm.nome, 'N.I.') as modalidade
    from planos_trabalhos pt
    left join tipos_modalidades tm
        on tm.id = pt.tipo_modalidade_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
),
contagem_por_regime as (
    select
        modalidade,
        count(distinct usuario_id) as total_servidores
    from servidores_no_periodo
    group by modalidade
)
select
    modalidade,
    total_servidores,
    round(
        total_servidores * 100.0 / nullif(sum(total_servidores) over (), 0),
        2
    ) as proporcao_perc
from contagem_por_regime
order by total_servidores desc;
```

### I01 — Consulta variante: proporcao por regime dentro de cada unidade

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
servidores_por_unidade as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        pt.usuario_id,
        coalesce(tm.nome, 'N.I.') as modalidade
    from planos_trabalhos pt
    left join tipos_modalidades tm
        on tm.id = pt.tipo_modalidade_id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
),
contagem as (
    select
        unidade_sigla,
        min(unidade_nome) as unidade_nome,
        modalidade,
        count(distinct usuario_id) as total_servidores
    from servidores_por_unidade
    group by unidade_sigla, modalidade
)
select
    unidade_sigla,
    unidade_nome,
    modalidade,
    total_servidores,
    round(
        total_servidores * 100.0
            / nullif(sum(total_servidores) over (partition by unidade_sigla), 0),
        2
    ) as proporcao_na_unidade_perc
from contagem
order by unidade_sigla, total_servidores desc;
```

### I01 — Como interpretar o resultado

| Coluna | Significado |
| --- | --- |
| `modalidade` | Nome do regime conforme `tipos_modalidades.nome` |
| `total_servidores` | Servidores distintos com plano ativo no periodo neste regime |
| `proporcao_perc` | Percentual do total institucional de servidores com planos ativos |
| `proporcao_na_unidade_perc` | Percentual dentro da propria unidade (variante por unidade) |

**Atencao sobre dupla contagem:** se um servidor teve planos com regimes diferentes no mesmo periodo (ex: mudou de teletrabalho para hibrido), ele aparece em ambas as linhas. Isso e o comportamento correto — reflete que ele atuou nos dois regimes. Para um snapshot do regime atual, filtre apenas o plano mais recente por servidor usando `ROW_NUMBER() OVER (PARTITION BY usuario_id ORDER BY data_inicio DESC) = 1`.

---

## 3. Indicador 2: Taxa de cumprimento das entregas (MySQL)

### I02 — Consulta completa

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
entregas_base as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        pee.id as id_entrega,
        nullif(trim(coalesce(pee.descricao, '')), '') as nome_entrega_base,
        nullif(trim(coalesce(pee.descricao_entrega, '')), '') as descricao_entrega,
        pee.progresso_esperado as meta_planejada,
        coalesce(pee.progresso_realizado, 0) as meta_executada,
        pee.deleted_at,
        case
            when pee.deleted_at is null then 'ATIVO'
            else 'EXCLUIDO'
        end as status_registro
    from planos_entregas_entregas pee
    left join unidades u
        on u.id = pee.unidade_id
    cross join parametros p
    where date(pee.data_fim) between p.data_inicio and p.data_fim
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
)
select
    unidade_sigla,
    count(*) as total_entregas_planejadas,
    sum(case when meta_executada >= meta_planejada then 1 else 0 end) as total_entregas_concluidas,
    round(
        (
            sum(case when meta_executada >= meta_planejada then 1 else 0 end)
            / nullif(count(*), 0)
        ) * 100,
        2
    ) as taxa_cumprimento_perc
from entregas_base
group by unidade_sigla
order by unidade_sigla;
```

### I02 — O que essa consulta faz?

Ela calcula a **Taxa de cumprimento das entregas (Indicador 2)**, mas lendo diretamente da base MySQL do PETRVS, sem passar pelo datamart.

A pergunta que ela responde e: **"De todas as entregas planejadas pelas unidades do ICMBio no periodo, qual a porcentagem que foi efetivamente concluida?"**

O codigo usa `WITH` para criar blocos intermediarios - pense nisso como tabelas temporarias que so existem durante a execucao da consulta. Cada bloco resolve um problema menor antes do calculo final.

Vamos ver cada um deles:

---

### Passo 1: O bloco `parametros` (Definindo o periodo e o filtro de exclusao)

```sql
parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
)
```

**O que significa:**

Aqui voce esta criando um "bloco de configuracao" que serve como painel de controle para toda a consulta. Em vez de precisar mudar as datas em varios lugares espalhados, voce muda so aqui e o restante da consulta se ajusta automaticamente.

- `data_inicio` e `data_fim`: definem o periodo que voce quer analisar. No exemplo, e o ano inteiro de 2025.
- `incluir_excluidos`: no PETRVS, registros apagados nao sao removidos fisicamente do banco - eles recebem uma marcacao em `deleted_at`. Com `0`, voce analisa apenas os registros ainda ativos. Com `1`, voce inclui tambem os excluidos (util para auditoria ou comparacao historica).

**Analogia pratica:** e como configurar os filtros de um relatorio no Excel antes de abri-lo: voce escolhe o periodo e se quer ver so os ativos ou tudo.

---

### Passo 2: O bloco `entregas_base` (Buscando e preparando os dados)

Este e o bloco mais longo e mais importante. Aqui o banco de dados busca os registros de entregas na tabela `planos_entregas_entregas` e os organiza para o calculo.

**A estrutura basica:**

```sql
from planos_entregas_entregas pee
left join unidades u
    on u.id = pee.unidade_id
cross join parametros p
```

- `planos_entregas_entregas pee`: e a tabela principal, que contem cada entrega registrada no sistema. O `pee` e apenas um apelido (alias) para nao precisar escrever o nome completo toda vez.
- `left join unidades u`: vai buscar o nome/sigla da unidade responsavel pela entrega. O `left join` garante que mesmo que uma entrega nao tenha unidade vinculada, ela nao sera perdida - ela aparecera com a sigla `'N.I.'` (Nao Informado), gracias ao `coalesce(u.sigla, 'N.I.')`.
- `cross join parametros p`: inclui os parametros de configuracao do Passo 1 para que os filtros de data e exclusao possam ser usados dentro deste bloco.

**O tratamento dos nomes de entrega:**

```sql
nullif(trim(coalesce(pee.descricao, '')), '') as nome_entrega_base,
nullif(trim(coalesce(pee.descricao_entrega, '')), '') as descricao_entrega,
```

No PETRVS MySQL, as entregas podem ter o nome em dois campos diferentes: `descricao` e `descricao_entrega`. As funcoes aqui fazem uma "faxina" em cada campo:

1. `coalesce(pee.descricao, '')`: se o campo `descricao` estiver vazio (NULL), usa texto em branco no lugar - assim as funcoes seguintes nao travam.
2. `trim(...)`: remove espacos em branco no inicio e no fim do texto (e comum campos preenchidos com espaco em branco, o que confunde o sistema).
3. `nullif(..., '')`: se depois da limpeza o texto ficou vazio, transforma em NULL - o que facilita identificar campos realmente sem informacao.

**O tratamento das metas:**

```sql
pee.progresso_esperado as meta_planejada,
coalesce(pee.progresso_realizado, 0) as meta_executada,
```

Ao contrario do datamart (que armazena os valores como texto e precisa de limpeza pesada), no MySQL do PETRVS os valores de progresso ja estao em formato numerico. Por isso o tratamento e mais simples:

- `meta_planejada`: o valor numerico de progresso esperado, sem alteracao.
- `meta_executada`: o progresso realizado, com `coalesce(..., 0)` para garantir que entregas sem preenchimento sejam tratadas como zero (em vez de NULL, que causaria problemas nas contas).

**O status do registro:**

```sql
case
    when pee.deleted_at is null then 'ATIVO'
    else 'EXCLUIDO'
end as status_registro
```

Este bloco cria um campo legivel para indicar se a entrega ainda existe no sistema ou foi excluida logicamente. `deleted_at` e o campo que o PETRVS preenche quando alguem exclui um registro - se estiver vazio (NULL), o registro esta ativo.

**Os filtros (`where`):**

```sql
where date(pee.data_fim) between p.data_inicio and p.data_fim
  and (p.incluir_excluidos = 1 or pee.deleted_at is null)
  and pee.progresso_esperado is not null
  and pee.progresso_esperado > 0
```

- `date(pee.data_fim) between p.data_inicio and p.data_fim`: filtra apenas entregas cuja data de encerramento cai dentro do periodo configurado. O `date()` converte o campo para formato de data pura (sem hora), evitando problemas de comparacao.
- `(p.incluir_excluidos = 1 or pee.deleted_at is null)`: aplica o filtro de exclusao logica conforme o parametro configurado. Se `incluir_excluidos = 0`, so passa registros com `deleted_at` nulo (ativos).
- `pee.progresso_esperado is not null` e `> 0`: garante que so entram no calculo entregas que de fato tinham uma meta definida e valida. Entrega sem meta nao pode ser avaliada.

---

### I02 — Passo 3: O calculo final (`SELECT` principal)

```sql
select
    unidade_sigla,
    count(*) as total_entregas_planejadas,
    sum(case when meta_executada >= meta_planejada then 1 else 0 end) as total_entregas_concluidas,
    round(
        (
            sum(case when meta_executada >= meta_planejada then 1 else 0 end)
            / nullif(count(*), 0)
        ) * 100,
        2
    ) as taxa_cumprimento_perc
from entregas_base
group by unidade_sigla
order by unidade_sigla;
```

Agora que os dados estao limpos e filtrados, o banco de dados faz as contas agrupadas por unidade.

- `count(*) as total_entregas_planejadas`: conta quantas entregas validas existem no periodo para cada unidade.

- `sum(case when meta_executada >= meta_planejada then 1 else 0 end) as total_entregas_concluidas`: para cada entrega, o `case when` funciona como um "se" no Excel: se o progresso realizado foi igual ou maior que o esperado, conta 1 (concluida); senao, conta 0 (nao concluida). O `sum` soma todos esses 1s, dando o total de entregas concluidas.

- `taxa_cumprimento_perc`: divide o total de entregas concluidas pelo total de entregas planejadas e multiplica por 100 para virar percentual. O `nullif(count(*), 0)` e uma protecao: se por algum motivo uma unidade nao tiver nenhuma entrega, impede a divisao por zero (que causaria erro). O `round(..., 2)` arredonda o resultado para 2 casas decimais.

- `group by unidade_sigla`: agrupa todos os calculos acima por unidade - ou seja, o resultado final tera uma linha por unidade.

- `order by unidade_sigla`: ordena o resultado em ordem alfabetica pela sigla da unidade.

---

## 4. Consulta de auditoria de base (opcional)

Se voce quiser validar o perfil dos registros antes de executar o indicador:

```sql
select
    count(*) as total_registros,
    sum(case when deleted_at is null then 1 else 0 end) as ativos,
    sum(case when deleted_at is not null then 1 else 0 end) as excluidos,
    sum(case when coalesce(trim(descricao), '') = '' then 1 else 0 end) as sem_descricao,
    sum(case when coalesce(trim(descricao_entrega), '') = '' then 1 else 0 end) as sem_descricao_entrega
from planos_entregas_entregas;
```

### Auditoria — O que essa consulta faz?

Ela e um **diagnostico rapido da qualidade dos dados** na tabela `planos_entregas_entregas`. Antes de calcular indicadores, e util saber com o que voce esta lidando.

**Linha a linha:**

- `count(*) as total_registros`: conta o total absoluto de linhas na tabela, incluindo ativos e excluidos.

- `sum(case when deleted_at is null then 1 else 0 end) as ativos`: conta quantos registros estao ativos (nao foram excluidos logicamente). `deleted_at is null` significa que o campo de exclusao esta vazio, ou seja, o registro ainda existe.

- `sum(case when deleted_at is not null then 1 else 0 end) as excluidos`: o inverso do anterior - conta quantos registros foram marcados como excluidos em algum momento.

- `sum(case when coalesce(trim(descricao), '') = '' then 1 else 0 end) as sem_descricao`: conta quantas entregas estao sem preenchimento no campo `descricao`. O `coalesce` trata os NULLs transformando-os em texto vazio antes da comparacao, e o `trim` remove espacos em branco (para nao contar como preenchido um campo que so tem espaco).

- `sum(case when coalesce(trim(descricao_entrega), '') = '' then 1 else 0 end) as sem_descricao_entrega`: o mesmo para o campo alternativo de descricao.

**Para que serve na pratica:** se voce ver que muitos registros estao sem descricao em ambos os campos, isso significa que o nome da entrega aparecera como `N.I.` nos indicadores. Isso nao quebra o calculo, mas e um sinal de que o preenchimento no sistema esta incompleto.

---

## 5. Indicador 3: Taxa de cumprimento de metas por entrega (MySQL)

### I03 — Consulta completa

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
entregas_base as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        pee.id as id_entrega,
        nullif(trim(coalesce(pee.descricao, '')), '') as nome_entrega_base,
        nullif(trim(coalesce(pee.descricao_entrega, '')), '') as descricao_entrega,
        pee.progresso_esperado as meta_planejada,
        coalesce(pee.progresso_realizado, 0) as meta_executada,
        pee.deleted_at,
        case
            when pee.deleted_at is null then 'ATIVO'
            else 'EXCLUIDO'
        end as status_registro
    from planos_entregas_entregas pee
    left join unidades u
        on u.id = pee.unidade_id
    cross join parametros p
    where date(pee.data_fim) between p.data_inicio and p.data_fim
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
)
select
    id_entrega as id,
    unidade_sigla,
    coalesce(nome_entrega_base, descricao_entrega, 'N.I.') as nome_entrega,
    descricao_entrega,
    meta_planejada,
    meta_executada,
    round((meta_executada / nullif(meta_planejada, 0)) * 100, 2) as taxa_atingimento_meta_perc,
    case
        when meta_executada > meta_planejada then 'Superexecutada'
        when meta_executada = meta_planejada then 'No alvo'
        else 'Subexecutada'
    end as classificacao_execucao,
    status_registro
from entregas_base
order by unidade_sigla, id_entrega;
```

### I03 — O que essa consulta faz?

Ela calcula a **Taxa de cumprimento de metas por entrega (Indicador 3)**.

A diferenca em relacao ao Indicador 2 e que **aqui o resultado e linha a linha**, ou seja, uma linha por entrega. O Indicador 2 resumia os dados por unidade (quantas entregas foram concluidas?). O Indicador 3 vai mais fundo: mostra exatamente **o quanto cada entrega individual foi executada** e classifica o desempenho dela.

Os blocos `parametros` e `entregas_base` sao identicos aos do Indicador 2 - leia as explicacoes acima para entende-los. A diferenca esta no `SELECT` final.

---

### Passo 3: O calculo final (`SELECT` principal do Indicador 3)

```sql
select
    id_entrega as id,
    unidade_sigla,
    coalesce(nome_entrega_base, descricao_entrega, 'N.I.') as nome_entrega,
    descricao_entrega,
    meta_planejada,
    meta_executada,
    round((meta_executada / nullif(meta_planejada, 0)) * 100, 2) as taxa_atingimento_meta_perc,
    case
        when meta_executada > meta_planejada then 'Superexecutada'
        when meta_executada = meta_planejada then 'No alvo'
        else 'Subexecutada'
    end as classificacao_execucao,
    status_registro
from entregas_base
order by unidade_sigla, id_entrega;
```

**Linha a linha:**

- `id_entrega as id`: o identificador unico de cada entrega no banco de dados. Util para rastrear registros especificos se necessario.

- `unidade_sigla`: a sigla da unidade responsavel, vinda da preparacao no bloco `entregas_base`.

- `coalesce(nome_entrega_base, descricao_entrega, 'N.I.') as nome_entrega`: aqui e aplicada a regra de fallback para o nome da entrega. O `coalesce` retorna o primeiro valor nao-nulo da lista:
  - Primeiro tenta usar `nome_entrega_base` (campo `descricao`).
  - Se estiver vazio, tenta `descricao_entrega`.
  - Se ambos estiverem vazios, usa o texto `'N.I.'` (Nao Informado).
  Isso garante que nenhuma entrega suma do resultado so por problema de preenchimento.

- `meta_planejada` e `meta_executada`: os valores numericos diretamente da tabela, ja preparados no bloco anterior.

- `round((meta_executada / nullif(meta_planejada, 0)) * 100, 2) as taxa_atingimento_meta_perc`: calcula o percentual de atingimento da meta para cada entrega individualmente. Por exemplo, se a meta era 50 e foi executado 40, o resultado sera 80.00%. O `nullif(meta_planejada, 0)` protege contra divisao por zero.

- O bloco `case` de classificacao:
  ```sql
  case
      when meta_executada > meta_planejada then 'Superexecutada'
      when meta_executada = meta_planejada then 'No alvo'
      else 'Subexecutada'
  end as classificacao_execucao
  ```
  Este bloco funciona como uma serie de "se/senao" para categorizar cada entrega em um dos tres grupos:
  - **Superexecutada**: o progresso realizado ultrapassou o esperado (bom desempenho ou meta subestimada).
  - **No alvo**: realizou exatamente o que foi planejado (desempenho perfeito).
  - **Subexecutada**: ficou abaixo do esperado (necessita de atencao ou justificativa).

- `status_registro`: mostra se o registro esta `ATIVO` ou `EXCLUIDO` no sistema, calculado no bloco `entregas_base`.

- `order by unidade_sigla, id_entrega`: ordena o resultado primeiro pela sigla da unidade (alfabetico) e depois pelo ID da entrega dentro de cada unidade.

---

### Diferenca pratica entre os Indicadores 2 e 3

| Aspecto | Indicador 2 | Indicador 3 |
|---|---|---|
| Nivel de detalhe | Resumido por unidade | Detalhado por entrega |
| Linhas no resultado | Uma por unidade | Uma por entrega |
| Pergunta respondida | Quantas entregas foram concluidas? | Qual o percentual de cada entrega? |
| Util para | Painel gerencial, comparacao entre unidades | Auditoria, identificar entregas especificas com problema |

---

## 6. Indicador 4: Indice de atingimento de metas (MySQL)

### I04 — Consulta completa

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
calculo_por_entrega as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        pee.id as id_entrega,
        abs(coalesce(pee.progresso_realizado, 0))
            / nullif(abs(pee.progresso_esperado), 0) as proporcao_atingimento
    from planos_entregas_entregas pee
    left join unidades u
        on u.id = pee.unidade_id
    cross join parametros p
    where date(pee.data_fim) between p.data_inicio and p.data_fim
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
)
select
    unidade_sigla,
    count(id_entrega) as total_entregas_planejadas,
    round(avg(proporcao_atingimento) * 100, 2) as score_atingimento_metas_perc
from calculo_por_entrega
where proporcao_atingimento is not null
group by unidade_sigla
order by unidade_sigla;
```

### I04 — O que essa consulta faz?

Ela calcula o **Indice de atingimento de metas (Indicador 4)**, que e um **score resumido por unidade** representando o desempenho medio de todas as suas entregas no periodo.

A pergunta que ela responde e: **"Em media, qual o percentual de atingimento das metas em cada unidade?"**

Para entender a diferenca em relacao ao Indicador 3, pense assim:

- **Indicador 3**: e como um boletim escolar com a nota de cada disciplina. Voce ve o desempenho entrega por entrega.
- **Indicador 4**: e a media final do boletim. Um unico numero que resume o desempenho geral da unidade.

O codigo usa dois blocos `WITH` antes do calculo final:

---

### Passo 1: O bloco `parametros` (Painel de configuracao)

```sql
parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
)
```

Identico ao dos Indicadores 2 e 3. Define o periodo de analise e o comportamento para registros excluidos logicamente. Consulte a explicacao detalhada na secao 3 deste documento.

---

### Passo 2: O bloco `calculo_por_entrega` (Calculando a proporcao de cada entrega)

```sql
calculo_por_entrega as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        pee.id as id_entrega,
        abs(coalesce(pee.progresso_realizado, 0))
            / nullif(abs(pee.progresso_esperado), 0) as proporcao_atingimento
    from planos_entregas_entregas pee
    left join unidades u
        on u.id = pee.unidade_id
    cross join parametros p
    where date(pee.data_fim) between p.data_inicio and p.data_fim
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
)
```

O `from`, o `left join`, o `cross join` e os filtros `where` seguem exatamente o mesmo padrao dos Indicadores 2 e 3. A novidade esta na coluna calculada `proporcao_atingimento`:

```sql
abs(coalesce(pee.progresso_realizado, 0))
    / nullif(abs(pee.progresso_esperado), 0) as proporcao_atingimento
```

Esta linha calcula, para **cada entrega**, a proporcao entre o que foi realizado e o que era esperado. Vamos destrinchar:

- `coalesce(pee.progresso_realizado, 0)`: se o progresso realizado estiver vazio (NULL), usa 0 no lugar. Garante que entregas sem preenchimento entrem no calculo como zero.

- `abs(...)` no numerador (realizado): a funcao `abs` retorna o valor absoluto, ou seja, remove o sinal negativo se houver. Isso e uma protecao para casos onde metas sao expressas como reducao (ex: uma meta de reducao de 50 unidades poderia ser registrada como -50). Com `abs`, o calculo fica correto independentemente do sinal.

- `abs(pee.progresso_esperado)` no denominador: mesma logica para o valor esperado.

- `nullif(abs(pee.progresso_esperado), 0)`: protecao contra divisao por zero. Se o denominador for 0, a divisao retorna NULL em vez de erro.

**Exemplo pratico:**
- Meta planejada: 100 unidades (`progresso_esperado = 100`)
- Meta executada: 75 unidades (`progresso_realizado = 75`)
- `proporcao_atingimento` = 75 / 100 = 0.75

Este valor (0.75) sera usado no proximo passo para calcular a media.

**Diferenca em relacao ao Indicador 3:** o Indicador 3 ja multiplica por 100 nesta etapa e mostra o percentual por entrega. O Indicador 4 guarda a proporcao crua (sem multiplicar) para poder calcular a media no passo seguinte.

---

### I04 — Passo 3: O calculo final (`SELECT` principal)

```sql
select
    unidade_sigla,
    count(id_entrega) as total_entregas_planejadas,
    round(avg(proporcao_atingimento) * 100, 2) as score_atingimento_metas_perc
from calculo_por_entrega
where proporcao_atingimento is not null
group by unidade_sigla
order by unidade_sigla;
```

**Linha a linha:**

- `count(id_entrega) as total_entregas_planejadas`: conta quantas entregas validas entraram no calculo para cada unidade. Importante para entender o peso do score - uma unidade com 2 entregas e score 80% e diferente de uma com 50 entregas e score 80%.

- `avg(proporcao_atingimento) * 100 as score_atingimento_metas_perc`: aqui esta o coracao do Indicador 4. O `avg` calcula a **media aritmetica** de todas as proporcoes de atingimento de cada unidade, e multiplica por 100 para transformar em percentual.

  **Exemplo com 3 entregas de uma unidade:**
  - Entrega A: proporcao = 1.0 (atingiu 100%)
  - Entrega B: proporcao = 0.5 (atingiu 50%)
  - Entrega C: proporcao = 1.2 (superou em 20%)
  - Media = (1.0 + 0.5 + 1.2) / 3 = 0.9 → score = **90.00%**

- `where proporcao_atingimento is not null`: exclui do calculo final as entregas em que a divisao resultou em NULL (denominador zero, ou seja, `progresso_esperado = 0`). Isso ja e filtrado no bloco anterior, mas este filtro garante robustez adicional.

- `group by unidade_sigla`: agrupa tudo por unidade para gerar uma linha por unidade no resultado.

- `round(..., 2)`: arredonda o score para 2 casas decimais.

---

### I04 — Como interpretar o resultado

| score_atingimento_metas_perc | Interpretacao |
|---|---|
| 100.00% | A unidade atingiu exatamente todas as metas em media |
| Acima de 100% | A unidade superou as metas em media (superexecucao) |
| Abaixo de 100% | A unidade ficou abaixo das metas em media |
| 0.00% | Nenhuma entrega teve progresso realizado registrado |

**Atencao:** um score acima de 100% pode indicar tanto bom desempenho quanto metas subestimadas no planejamento. Para diagnosticar, use o Indicador 3 para ver entrega a entrega.

---

### Diferenca pratica entre Indicadores 3 e 4

| Aspecto | Indicador 3 | Indicador 4 |
|---|---|---|
| Nivel de detalhe | Uma linha por entrega | Uma linha por unidade |
| O que mostra | Taxa de atingimento individual | Score medio da unidade |
| Formula central | `(realizado / planejado) * 100` por entrega | `avg(realizado / planejado) * 100` por unidade |
| Util para | Identificar entregas especificas com problema | Comparar desempenho geral entre unidades |
| Valores acima de 100% | Possivel (entrega superexecutada) | Possivel (media da unidade acima de 100%) |

---

### Observacao sobre o uso do `abs()`

No frame MySQL (base de origem), os campos `progresso_esperado` e `progresso_realizado` sao numericos e em geral positivos. O `abs()` e mantido como salvaguarda para o caso de metas expressas como reducao (ex: reduzir em 10 o numero de ocorrencias). Nesse cenario, sem `abs()` a proporcao poderia ser negativa e distorcer a media. Nos Indicadores 2 e 3 esse tratamento nao e necessario porque a comparacao e direta (realizado >= planejado), mas no Indicador 4 a divisao exige essa precaucao.

---

## 7. Indicador 5: Distribuicao das entregas entre os servidores (MySQL)

### I05 — Consulta completa

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
vinculos_entregas as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        pt.usuario_id as id_servidor,
        coalesce(us.nome, 'N.I.') as nome_servidor,
        pte.plano_entrega_entrega_id as id_entrega
    from planos_trabalhos pt
    join planos_trabalhos_entregas pte
        on pte.plano_trabalho_id = pt.id
    left join unidades un
        on un.id = pt.unidade_id
    left join usuarios us
        on us.id = pt.usuario_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
      and pte.plano_entrega_entrega_id is not null
),
entregas_por_servidor as (
    select
        unidade_sigla,
        min(unidade_nome) as unidade_nome,
        id_servidor,
        min(nome_servidor) as nome_servidor,
        count(distinct id_entrega) as qtd_entregas_por_servidor
    from vinculos_entregas
    group by unidade_sigla, id_servidor
),
com_media as (
    select
        unidade_sigla,
        unidade_nome,
        id_servidor,
        nome_servidor,
        qtd_entregas_por_servidor,
        round(avg(qtd_entregas_por_servidor) over (partition by unidade_sigla), 2) as media_entregas_por_servidor_unidade
    from entregas_por_servidor
)
select
    unidade_sigla,
    unidade_nome,
    id_servidor,
    nome_servidor,
    qtd_entregas_por_servidor,
    media_entregas_por_servidor_unidade,
    case
        when qtd_entregas_por_servidor > media_entregas_por_servidor_unidade then 'Acima da media'
        when qtd_entregas_por_servidor < media_entregas_por_servidor_unidade then 'Abaixo da media'
        else 'Na media'
    end as posicao_relativa_media
from com_media
order by unidade_sigla, qtd_entregas_por_servidor desc, nome_servidor;
```

### Observacao de mapeamento

Esta e a primeira consulta do frame MySQL que envolve a relacao entre **servidores e entregas**. Nos Indicadores 2, 3 e 4, a entidade central era a entrega em si (`planos_entregas_entregas`). Aqui, a pergunta muda: **quem** esta fazendo **o que**.

No datamart PostgreSQL, esse vinculo fica em uma unica tabela `di_trabalhos`, que ja consolida o servidor, a entrega e a data de distribuicao. No MySQL de origem, essa informacao e reconstruida a partir de duas tabelas:

- `planos_trabalhos`: cada linha e um plano de trabalho de um servidor, com `usuario_id` e `unidade_id`
- `planos_trabalhos_entregas`: cada linha e um vinculo entre um plano de trabalho e uma entrega especifica

O filtro de periodo tambem e diferente: no datamart usava-se `atividade_data_distribuicao`. No MySQL, como essa data granular nao esta disponivel facilmente, o filtro e feito pela **vigencia do plano de trabalho** (`data_inicio` e `data_fim` do plano sobrepondo o periodo de analise).

### Requisito tecnico

Esta consulta usa uma **window function** (`avg() over (partition by ...)`), que requer **MySQL 8.0 ou superior**. Se o seu ambiente usar uma versao anterior, a consulta retornara erro. Nesse caso, o calculo da media pode ser refeito com um subselect.

---

### I05 — Passo 1: O bloco `parametros`

Identico aos indicadores anteriores. Consulte a explicacao na secao 3 deste documento.

---

### Passo 2: O bloco `vinculos_entregas` (Quem faz o que)

```sql
vinculos_entregas as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        pt.usuario_id as id_servidor,
        coalesce(us.nome, 'N.I.') as nome_servidor,
        pte.plano_entrega_entrega_id as id_entrega
    from planos_trabalhos pt
    join planos_trabalhos_entregas pte
        on pte.plano_trabalho_id = pt.id
    left join unidades un
        on un.id = pt.unidade_id
    left join usuarios us
        on us.id = pt.usuario_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
      and pte.plano_entrega_entrega_id is not null
)
```

Este bloco constroi a lista de **pares unicos servidor-entrega** dentro do periodo.

**A estrutura dos joins:**

- `from planos_trabalhos pt`: ponto de partida e o plano de trabalho do servidor. Cada plano pertence a um servidor (`usuario_id`) e a uma unidade (`unidade_id`).
- `join planos_trabalhos_entregas pte on pte.plano_trabalho_id = pt.id`: conecta o plano de trabalho com as entregas que esse servidor tem responsabilidade. Um plano pode estar vinculado a varias entregas - e esse `join` que expande as linhas.
- `left join unidades un on un.id = pt.unidade_id`: busca o nome e a sigla da unidade. `left join` garante que planos sem unidade cadastrada nao sejam perdidos.
- `left join usuarios us on us.id = pt.usuario_id`: busca o nome do servidor. `left join` pelo mesmo motivo.

**Os filtros (`where`):**

- `date(pt.data_inicio) <= p.data_fim and date(pt.data_fim) >= p.data_inicio`: seleciona planos cuja vigencia tem qualquer sobreposicao com o periodo de analise. Isso e diferente de filtrar por uma data exata - um plano que comecou em outubro/2024 e vai ate marco/2025 seria incluido numa analise de 2025.
- `(p.incluir_excluidos = 1 or pt.deleted_at is null)`: controla registros excluidos logicamente.
- `pt.usuario_id is not null`: descarta planos sem servidor atribuido.
- `pte.plano_entrega_entrega_id is not null`: descarta vinculos sem entrega associada.

**O `select distinct`**: como um servidor pode ter multiplos registros de atividade para a mesma entrega (ex: atualizacoes no plano), o `distinct` garante que cada par servidor-entrega apareca **apenas uma vez** no resultado.

---

### Passo 3: O bloco `entregas_por_servidor` (Contando as entregas de cada servidor)

```sql
entregas_por_servidor as (
    select
        unidade_sigla,
        min(unidade_nome) as unidade_nome,
        id_servidor,
        min(nome_servidor) as nome_servidor,
        count(distinct id_entrega) as qtd_entregas_por_servidor
    from vinculos_entregas
    group by unidade_sigla, id_servidor
)
```

Aqui o banco agrupa por servidor dentro de cada unidade e conta quantas entregas distintas cada um tem.

- `group by unidade_sigla, id_servidor`: agrupa **apenas pelas chaves reais** — sigla da unidade e id do servidor. Esta e a correcao critica em relacao a uma versao anterior que agrupava tambem por `unidade_nome` e `nome_servidor`. O problema: se o cadastro do servidor tiver pequenas inconsistencias (espaco extra, atualizacao de nome), o mesmo servidor apareceria em duas linhas, distorcendo o denominador da media.
- `min(unidade_nome)` e `min(nome_servidor)`: como o `group by` nao inclui mais esses campos de texto, usamos `min()` para "escolher" um valor representativo para exibicao. Como cada `id_servidor` tipicamente tem um unico nome, o `min()` simplesmente retorna esse valor.
- `count(distinct id_entrega)`: conta entregas unicas por servidor.

O resultado e **uma linha por servidor por unidade**, sem duplicatas.

---

### Passo 4: O bloco `com_media` (Calculando a media com window function)

```sql
com_media as (
    select
        unidade_sigla,
        unidade_nome,
        id_servidor,
        nome_servidor,
        qtd_entregas_por_servidor,
        round(avg(qtd_entregas_por_servidor) over (partition by unidade_sigla), 2) as media_entregas_por_servidor_unidade
    from entregas_por_servidor
)
```

Este CTE intermediario existe por uma razao tecnica do MySQL: nao e possivel usar o alias de uma window function (`media_entregas_por_servidor_unidade`) no mesmo `SELECT` onde ela e calculada. Para classificar cada servidor como acima/abaixo da media no passo seguinte, o valor da media precisa estar "materializado" em um bloco anterior.

A window function `avg(qtd_entregas_por_servidor) over (partition by unidade_sigla)` faz um calculo "ao lado" dos dados sem colapsar as linhas. Ela permite ver ao mesmo tempo o valor individual de cada servidor e a media da unidade dele.

**Como funciona o `partition by`:** e como um `GROUP BY` invisivel so para o calculo da media. Cada linha (servidor) recebe a media de todos os servidores da mesma `unidade_sigla`, sem que o numero de linhas seja reduzido.

---

### Passo 5: O calculo final com classificacao

```sql
select
    unidade_sigla,
    unidade_nome,
    id_servidor,
    nome_servidor,
    qtd_entregas_por_servidor,
    media_entregas_por_servidor_unidade,
    case
        when qtd_entregas_por_servidor > media_entregas_por_servidor_unidade then 'Acima da media'
        when qtd_entregas_por_servidor < media_entregas_por_servidor_unidade then 'Abaixo da media'
        else 'Na media'
    end as posicao_relativa_media
from com_media
order by unidade_sigla, qtd_entregas_por_servidor desc, nome_servidor;
```

O `case` classifica cada servidor em relacao a media da sua unidade:

- **Acima da media**: o servidor tem mais entregas que a media da unidade — pode indicar sobrecarga ou maior engajamento.
- **Abaixo da media**: o servidor tem menos entregas que a media — pode indicar disponibilidade, ausencias ou inicio recente.
- **Na media**: o servidor tem exatamente a media (arredondada a 2 casas).

**Exemplo completo com resultado:**

| unidade_sigla | nome_servidor | qtd_entregas | media_unidade | posicao |
|---|---|---|---|---|
| AUDIT | Ana Silva | 5 | 3.67 | Acima da media |
| AUDIT | Carlos Souza | 3 | 3.67 | Abaixo da media |
| AUDIT | Maria Costa | 3 | 3.67 | Abaixo da media |
| CGOV | Joao Lima | 8 | 6.00 | Acima da media |
| CGOV | Pedro Nunes | 4 | 6.00 | Abaixo da media |

- `order by unidade_sigla, qtd_entregas_por_servidor desc, nome_servidor`: ordena por unidade, servidores com mais entregas primeiro, e alfabetico em caso de empate.

---

## 8. Indicador 6: Grau de responsabilidade pelas entregas (MySQL)

### I06 — Consulta completa

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
vinculos as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        pte.plano_entrega_entrega_id as id_entrega,
        pt.usuario_id as id_servidor
    from planos_trabalhos pt
    join planos_trabalhos_entregas pte
        on pte.plano_trabalho_id = pt.id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
      and pte.plano_entrega_entrega_id is not null
),
responsaveis_por_entrega as (
    select
        unidade_sigla,
        min(unidade_nome) as unidade_nome,
        id_entrega,
        count(distinct id_servidor) as qtd_responsaveis
    from vinculos
    group by unidade_sigla, id_entrega
),
com_classificacao as (
    select
        unidade_sigla,
        unidade_nome,
        id_entrega,
        qtd_responsaveis,
        case
            when qtd_responsaveis = 1 then '1 servidor'
            when qtd_responsaveis = 2 then '2 servidores'
            when qtd_responsaveis = 3 then '3 servidores'
            else '4+ servidores'
        end as tamanho_grupo_responsavel
    from responsaveis_por_entrega
)
select
    unidade_sigla,
    min(unidade_nome) as unidade_nome,
    tamanho_grupo_responsavel,
    count(id_entrega) as total_entregas_na_categoria
from com_classificacao
group by unidade_sigla, tamanho_grupo_responsavel
order by unidade_sigla, tamanho_grupo_responsavel;
```

### I06 — O que essa consulta faz?

Ela calcula o **Grau de responsabilidade pelas entregas (Indicador 6)**, respondendo: **"Cada entrega tende a ser responsabilidade de um servidor so, ou e um conjunto compartilhado de servidores?"**

E a perspectiva **invertida do Indicador 5**:

| Indicador | Pergunta central | Unidade de analise |
|---|---|---|
| I05 | Quantas entregas tem cada servidor? | Servidor |
| I06 | Quantos servidores tem cada entrega? | Entrega |

O resultado final nao lista servidores nem entregas individualmente — ele agrupa as entregas em **faixas de tamanho de grupo** e conta quantas entregas caem em cada faixa, por unidade.

**Exemplo de resultado:**

| unidade_sigla | unidade_nome | tamanho_grupo_responsavel | total_entregas_na_categoria |
|---|---|---|---|
| AUDIT | Auditoria Interna | 1 servidor | 12 |
| AUDIT | Auditoria Interna | 2 servidores | 5 |
| AUDIT | Auditoria Interna | 4+ servidores | 2 |
| CGOV | Coordenacao de Governanca | 1 servidor | 8 |

Neste exemplo, na AUDIT: 12 entregas sao individuais, 5 sao compartilhadas entre 2 servidores e 2 sao de grande grupo.

---

### I06 — Passo 1: O bloco `parametros`

Identico aos indicadores anteriores. Consulte a explicacao na secao 3 deste documento.

---

### Passo 2: O bloco `vinculos` (Os pares entrega-servidor)

```sql
vinculos as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        pte.plano_entrega_entrega_id as id_entrega,
        pt.usuario_id as id_servidor
    from planos_trabalhos pt
    join planos_trabalhos_entregas pte
        on pte.plano_trabalho_id = pt.id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
      and pte.plano_entrega_entrega_id is not null
)
```

Identico ao bloco `vinculos_entregas` do Indicador 5 em estrutura e logica, com uma diferenca sutil na **ordem das colunas**: aqui o foco e `id_entrega` como entidade principal (nao o servidor). Isso nao afeta o resultado, mas deixa explicita a inversao de perspectiva.

O `select distinct` garante que cada par (entrega, servidor) apareca uma unica vez, eliminando duplicatas que poderiam surgir de servidores com multiplos planos de trabalho no mesmo periodo.

---

### Passo 3: O bloco `responsaveis_por_entrega` (Contando servidores por entrega)

```sql
responsaveis_por_entrega as (
    select
        unidade_sigla,
        min(unidade_nome) as unidade_nome,
        id_entrega,
        count(distinct id_servidor) as qtd_responsaveis
    from vinculos
    group by unidade_sigla, id_entrega
)
```

Aqui o agrupamento e feito por `(unidade_sigla, id_entrega)` — ou seja, uma linha por entrega. O `count(distinct id_servidor)` conta quantos servidores distintos estao vinculados a cada entrega.

- `min(unidade_nome)`: pelo mesmo motivo do Indicador 5 — evita duplicatas por inconsistencia cadastral e garante uma unica linha por entrega.

O resultado e uma tabela com uma linha por entrega e o campo `qtd_responsaveis` indicando o tamanho do grupo.

---

### Passo 4: O bloco `com_classificacao` (Aplicando as faixas)

```sql
com_classificacao as (
    select
        unidade_sigla,
        unidade_nome,
        id_entrega,
        qtd_responsaveis,
        case
            when qtd_responsaveis = 1 then '1 servidor'
            when qtd_responsaveis = 2 then '2 servidores'
            when qtd_responsaveis = 3 then '3 servidores'
            else '4+ servidores'
        end as tamanho_grupo_responsavel
    from responsaveis_por_entrega
)
```

Este CTE existe pela mesma razao do CTE `com_media` no Indicador 5: em MySQL nao e possivel usar um alias calculado no mesmo `SELECT` onde ele foi definido. Ao separar a classificacao em um bloco proprio, o alias `tamanho_grupo_responsavel` fica disponivel para o `GROUP BY` do passo seguinte.

O `case` traduz o numero bruto de responsaveis em uma categoria legivel. A faixa `4+ servidores` agrupa todos os casos com 4 ou mais responsaveis para evitar um numero excessivo de categorias no resultado final.

---

### Passo 5: O calculo final (Contando entregas por categoria)

```sql
select
    unidade_sigla,
    min(unidade_nome) as unidade_nome,
    tamanho_grupo_responsavel,
    count(id_entrega) as total_entregas_na_categoria
from com_classificacao
group by unidade_sigla, tamanho_grupo_responsavel
order by unidade_sigla, tamanho_grupo_responsavel;
```

Aqui o banco **colapsa** os dados: em vez de uma linha por entrega, gera uma linha por **combinacao de unidade e faixa**.

- `count(id_entrega) as total_entregas_na_categoria`: conta quantas entregas caem em cada faixa para cada unidade.
- `group by unidade_sigla, tamanho_grupo_responsavel`: a coluna `tamanho_grupo_responsavel` ja e um alias calculado no CTE anterior, entao pode ser usada diretamente aqui.
- `min(unidade_nome) as unidade_nome`: picks o nome da unidade para exibicao (todos os valores no grupo sao iguais).
- `order by unidade_sigla, tamanho_grupo_responsavel`: ordena por unidade e depois pelas faixas em ordem crescente. Como as faixas comecam com '1', '2', '3' e '4+', a ordem alfabetica coincide com a ordem numerica corretamente.

---

### I06 — Como interpretar o resultado

- **Muitas entregas com `1 servidor`**: alta concentracao individual — cada entrega depende de uma unica pessoa. Risco de gargalo em caso de ausencia.
- **Muitas entregas com `4+ servidores`**: alta diluicao de responsabilidade — pode indicar entregas estrategicas ou ausencia de dono claro.
- **Equilibrio entre faixas**: distribuicao saudavel de responsabilidade.

---

## 9. Indicador 7: Horas por entrega - planejadas (MySQL)

### O desafio tecnico: `generate_series` vs `WITH RECURSIVE`

Este e o indicador mais complexo do conjunto. No PostgreSQL, a query usa `generate_series()` para criar uma sequencia de datas e contar os dias uteis dentro do periodo de cada plano de trabalho. O MySQL nao tem essa funcao.

A solucao e usar `WITH RECURSIVE`, um recurso do MySQL 8.0+ que permite criar uma CTE que referencia a si mesma para gerar sequencias iterativas. O resultado e funcionalmente identico, mas com sintaxe diferente.

Outra diferenca importante: a deteccao de fins de semana.

| Banco | Funcao | Domingo | Sabado |
|---|---|---|---|
| PostgreSQL | `extract(dow from data)` | 0 | 6 |
| MySQL | `dayofweek(data)` | 1 | 7 |

Por isso o PostgreSQL usa `not in (0, 6)` e o MySQL usa `not in (1, 7)`.

**Limite de recursao:** O MySQL tem um limite padrao de 1000 iteracoes por CTE recursiva. Para um periodo de um ano (365 dias), isso e suficiente. Para periodos maiores, execute antes: `SET SESSION cte_max_recursion_depth = 5000;`

---

### I07 — Consulta completa

```sql
with recursive
parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        8 as horas_por_dia,
        0 as incluir_excluidos
),
anos as (
    select year((select data_inicio from parametros)) as ano
    union all
    select ano + 1
    from anos
    where ano < year((select data_fim from parametros))
),
feriados_fixos as (
    select date(concat(ano, '-01-01')) as data_feriado from anos
    union all select date(concat(ano, '-04-21')) from anos
    union all select date(concat(ano, '-05-01')) from anos
    union all select date(concat(ano, '-09-07')) from anos
    union all select date(concat(ano, '-10-12')) from anos
    union all select date(concat(ano, '-11-02')) from anos
    union all select date(concat(ano, '-11-15')) from anos
    union all select date(concat(ano, '-11-20')) from anos
    union all select date(concat(ano, '-12-25')) from anos
),
feriados_moveis as (
    select null as data_feriado where 1 = 0
    -- union all select date('2025-04-18')
    -- union all select date('2026-04-03')
),
feriados_nacionais as (
    select data_feriado from feriados_fixos
    union
    select data_feriado from feriados_moveis
),
calendario as (
    select (select data_inicio from parametros) as data_dia
    union all
    select date_add(data_dia, interval 1 day)
    from calendario
    where data_dia < (select data_fim from parametros)
),
links_distintos as (
    select
        pte.plano_trabalho_id,
        pte.plano_entrega_entrega_id as id_entrega,
        coalesce(pte.forca_trabalho, 0) as forca_trabalho
    from planos_trabalhos_entregas pte
    where pte.plano_entrega_entrega_id is not null
),
horas_planejadas_por_plano as (
    select
        pt.id as plano_trabalho_id,
        pt.unidade_id,
        count(c.data_dia) as dias_uteis_plano,
        count(c.data_dia) * p.horas_por_dia as horas_planejadas_plano
    from planos_trabalhos pt
    cross join parametros p
    join calendario c
        on c.data_dia between greatest(date(pt.data_inicio), p.data_inicio)
                          and least(date(pt.data_fim), p.data_fim)
    left join feriados_nacionais fn
        on fn.data_feriado = c.data_dia
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and dayofweek(c.data_dia) not in (1, 7)
      and fn.data_feriado is null
    group by pt.id, pt.unidade_id, p.horas_por_dia
),
horas_alocadas_por_entrega as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        ld.id_entrega,
        coalesce(
            nullif(trim(coalesce(pee.descricao, '')), ''),
            nullif(trim(coalesce(pee.descricao_entrega, '')), ''),
            'N.I.'
        ) as nome_entrega,
        pe.id                      as id_plano_entrega,
        date(pe.data_inicio)       as inicio_vigencia_plano_entrega,
        date(pe.data_fim)          as fim_vigencia_plano_entrega,
        hpp.horas_planejadas_plano * (ld.forca_trabalho / 100.0) as horas_planejadas_alocadas
    from links_distintos ld
    join horas_planejadas_por_plano hpp
        on hpp.plano_trabalho_id = ld.plano_trabalho_id
    left join planos_entregas_entregas pee
        on pee.id = ld.id_entrega
    left join planos_entregas pe
        on pe.id = pee.plano_entrega_id
    left join unidades un
        on un.id = hpp.unidade_id
)
select
    unidade_sigla,
    unidade_nome,
    id_entrega,
    nome_entrega,
    id_plano_entrega,
    inicio_vigencia_plano_entrega,
    fim_vigencia_plano_entrega,
    round(sum(horas_planejadas_alocadas), 2) as total_horas_planejadas_entrega
from horas_alocadas_por_entrega
group by unidade_sigla, unidade_nome, id_entrega, nome_entrega,
         id_plano_entrega, inicio_vigencia_plano_entrega, fim_vigencia_plano_entrega
order by unidade_sigla, total_horas_planejadas_entrega desc;
```

---

### Mapa dos blocos (visao geral antes de detalhar)

| Bloco | Papel |
|---|---|
| `parametros` | Periodo, horas/dia, flag de exclusao |
| `anos` | Gera os anos do periodo (recursivo) |
| `feriados_fixos` | Feriados nacionais fixos para cada ano |
| `feriados_moveis` | Feriados moveis (Sexta da Paixao etc.) |
| `feriados_nacionais` | Uniao dos dois tipos de feriado |
| `calendario` | Todos os dias do periodo (recursivo) |
| `links_distintos` | Pares (plano_trabalho, entrega) com percentual `forca_trabalho` |
| `horas_planejadas_por_plano` | Dias uteis e horas totais por plano |
| `horas_alocadas_por_entrega` | Horas proporcionais por entrega |
| SELECT final | Soma e arredonda por entrega |

---

### Passo 1: `parametros` (com novidade: `horas_por_dia`)

```sql
parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        8 as horas_por_dia,
        0 as incluir_excluidos
)
```

Segue o mesmo padrao dos outros indicadores, com um campo novo: `horas_por_dia = 8`. Esse valor e usado para converter dias uteis em horas. Se sua organizacao adota jornada diferente (ex: 6 horas), altere aqui.

---

### Passo 2: `anos` (CTE recursiva para gerar anos)

```sql
anos as (
    select year((select data_inicio from parametros)) as ano
    union all
    select ano + 1
    from anos
    where ano < year((select data_fim from parametros))
)
```

Esta e a primeira CTE recursiva da query. Ela gera os numeros dos anos cobertos pelo periodo. Para 2025-01-01 a 2025-12-31, gera apenas `[2025]`. Para 2024-07-01 a 2026-06-30, geraria `[2024, 2025, 2026]`.

**Como funciona a recursao:**
- **Caso base** (`select year(...)`) : começa com o ano de `data_inicio`.
- **Caso recursivo** (`select ano + 1`): adiciona 1 ao ano anterior, enquanto ainda for menor que o ano de `data_fim`.
- O banco executa o caso base uma vez, depois executa o caso recursivo repetidamente ate a condicao `where` ser falsa.

Isso e necessario porque os feriados precisam ser gerados para cada ano do periodo.

---

### Passo 3: `feriados_fixos` (feriados para cada ano)

```sql
feriados_fixos as (
    select date(concat(ano, '-01-01')) as data_feriado from anos
    union all select date(concat(ano, '-04-21')) from anos
    ...
)
```

Para cada ano gerado pelo bloco anterior, esta CTE cria as datas dos 9 feriados nacionais fixos. A funcao `concat(ano, '-01-01')` monta uma string como `'2025-01-01'`, e `date()` converte para formato de data.

No PostgreSQL, o equivalente e `make_date(ano, 1, 1)`. No MySQL, `make_date()` existe mas usa dia-do-ano (nao mes/dia), entao a abordagem com `concat` e mais legivel.

---

### Passo 4: `feriados_moveis` e `feriados_nacionais`

```sql
feriados_moveis as (
    select null as data_feriado where 1 = 0
    -- union all select date('2025-04-18')
),
feriados_nacionais as (
    select data_feriado from feriados_fixos
    union
    select data_feriado from feriados_moveis
)
```

`feriados_moveis` e um placeholder vazio — `where 1 = 0` nunca e verdade, entao retorna zero linhas. Para adicionar a Sexta da Paixao (que muda de data todo ano), basta descomentar as linhas.

`feriados_nacionais` une os dois. O `UNION` (sem ALL) elimina duplicatas, protegendo contra o caso de um feriado ser listado nos dois blocos por engano.

---

### Passo 5: `calendario` (CTE recursiva que gera todos os dias)

```sql
calendario as (
    select (select data_inicio from parametros) as data_dia
    union all
    select date_add(data_dia, interval 1 day)
    from calendario
    where data_dia < (select data_fim from parametros)
)
```

Esta e a CTE que substitui o `generate_series` do PostgreSQL. Ela gera uma linha para cada dia do periodo de analise.

- **Caso base**: começa em `data_inicio` (01/01/2025 no exemplo).
- **Caso recursivo**: adiciona 1 dia enquanto a data for menor que `data_fim`.
- Para 2025 inteiro: gera 365 linhas (uma por dia).

O subselect `(select data_inicio from parametros)` e necessario porque CTEs recursivas nao podem referenciar diretamente outras CTEs no caso base no MySQL.

---

### Passo 6: `links_distintos` (vinculo plano-entrega com percentual declarado)

```sql
links_distintos as (
    select
        pte.plano_trabalho_id,
        pte.plano_entrega_entrega_id as id_entrega,
        coalesce(pte.forca_trabalho, 0) as forca_trabalho
    from planos_trabalhos_entregas pte
    where pte.plano_entrega_entrega_id is not null
)
```

`links_distintos`: busca todos os pares (plano_trabalho, entrega) junto com o percentual de carga horaria dedicado a cada entrega.

A coluna `forca_trabalho` indica o percentual da carga horaria disponivel do plano que o servidor declarou para esta entrega. Exemplo: `forca_trabalho = 40` significa que 40% das horas daquele plano sao dedicadas a essa entrega. A soma dos valores por plano e majoritariamente 100%, podendo ultrapassar esse limite quando o servidor compensa horas devidas de planos anteriores.

Diferentemente de uma versao que dividiria as horas igualmente entre todas as entregas, aqui o percentual e o declarado pelo proprio servidor no planejamento — o que reflete com maior fidelidade a intencao real.

---

### Passo 7: `horas_planejadas_por_plano` (o calculo central)

```sql
horas_planejadas_por_plano as (
    select
        pt.id as plano_trabalho_id,
        pt.unidade_id,
        count(c.data_dia) as dias_uteis_plano,
        count(c.data_dia) * p.horas_por_dia as horas_planejadas_plano
    from planos_trabalhos pt
    cross join parametros p
    join calendario c
        on c.data_dia between greatest(date(pt.data_inicio), p.data_inicio)
                          and least(date(pt.data_fim), p.data_fim)
    left join feriados_nacionais fn
        on fn.data_feriado = c.data_dia
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and dayofweek(c.data_dia) not in (1, 7)
      and fn.data_feriado is null
    group by pt.id, pt.unidade_id, p.horas_por_dia
)
```

Este e o bloco mais importante. Para cada plano de trabalho, ele conta os dias uteis dentro do periodo de analise.

**Como funciona o join com o calendario:**

```sql
join calendario c
    on c.data_dia between greatest(date(pt.data_inicio), p.data_inicio)
                      and least(date(pt.data_fim), p.data_fim)
```
`greatest(inicio_plano, inicio_periodo)` pega a data mais tardia entre o inicio do plano e o inicio do periodo de analise — ou seja, o inicio real da sobreposicao. `least(fim_plano, fim_periodo)` pega a data mais cedo entre o fim do plano e o fim do periodo — o fim real da sobreposicao. Isso garante que so contamos dias dentro da intersecao entre o plano e o periodo de analise.

**Como os fins de semana sao excluidos:**

```sql
and dayofweek(c.data_dia) not in (1, 7)
```
`DAYOFWEEK()` no MySQL retorna 1 para domingo e 7 para sabado. Excluindo 1 e 7, ficamos apenas com dias de segunda (2) a sexta (6).

**Como os feriados sao excluidos:**

```sql
left join feriados_nacionais fn on fn.data_feriado = c.data_dia
...
and fn.data_feriado is null
```
O `left join` tenta encontrar uma correspondencia entre o dia do calendario e os feriados. Se o dia for feriado, `fn.data_feriado` tera um valor. Se nao for feriado, `fn.data_feriado` sera NULL. O filtro `and fn.data_feriado is null` mantem apenas os dias que NAO sao feriados.

**O resultado:** `count(c.data_dia)` conta os dias que sobram apos os filtros (somente dias uteis nao feriados dentro da sobreposicao). Multiplicar por `horas_por_dia` da o total de horas planejadas para aquele plano.

---

### Passo 8: `horas_alocadas_por_entrega` (distribuicao por forca_trabalho e vinculo ao plano)

```sql
pe.id                      as id_plano_entrega,
date(pe.data_inicio)       as inicio_vigencia_plano_entrega,
date(pe.data_fim)          as fim_vigencia_plano_entrega,
hpp.horas_planejadas_plano * (ld.forca_trabalho / 100.0) as horas_planejadas_alocadas
...
left join planos_entregas pe
    on pe.id = pee.plano_entrega_id
```

**Formula de alocacao:** multiplica o total de horas planejadas do plano pelo percentual declarado em `forca_trabalho`. Exemplo: um servidor com 200 horas planejadas e `forca_trabalho = 40` para uma entrega recebe `200 * 0.40 = 80 horas` alocadas a essa entrega.

Quando multiplos servidores contribuem para a mesma entrega — cada um com seu proprio plano e percentual — o SELECT final soma todas as contribuicoes com `sum(horas_planejadas_alocadas)`.

**Caso especial:** quando o servidor precisa compensar horas devidas de um plano anterior, a soma dos `forca_trabalho` no plano atual pode ultrapassar 100%. Nesse caso, as horas alocadas serao superiores ao total de horas do periodo — o que e o comportamento esperado e correto metodologicamente.

**Colunas novas — vinculo ao Plano de Entregas:**

- `id_plano_entrega`: identificador do Plano de Entregas ao qual a entrega (`planos_entregas_entregas`) pertence. Cada entrega so pertence a um unico Plano de Entregas, entao esse campo e determinista — nao multiplica linhas.
- `inicio_vigencia_plano_entrega` e `fim_vigencia_plano_entrega`: periodo de vigencia do Plano de Entregas. Permitem identificar a qual ciclo de planejamento (semestral, anual etc.) cada entrega pertence — util quando a mesma entrega aparece com nomes identicos mas em ciclos diferentes, gerando linhas distintas no resultado.

---

### Passo 9: SELECT final

```sql
select
    unidade_sigla,
    unidade_nome,
    id_entrega,
    nome_entrega,
    round(sum(horas_planejadas_alocadas), 2) as total_horas_planejadas_entrega
from horas_alocadas_por_entrega
group by unidade_sigla, unidade_nome, id_entrega, nome_entrega
order by unidade_sigla, total_horas_planejadas_entrega desc;
```

O `sum(horas_planejadas_alocadas)` acumula as contribuicoes de todos os planos de trabalho que apontam para a mesma entrega. O resultado e o total de horas planejadas para cada entrega, ordenado do maior para o menor dentro de cada unidade.

---

## 10. Indicador 8: Proporcao de horas por entrega - planejadas (MySQL)

### Relacao com o Indicador 7

O Indicador 8 e uma extensao direta do 7. Todos os blocos de preparacao de dados sao identicos. A diferenca esta apenas na pergunta respondida:

| Indicador | Pergunta | Coluna principal |
|---|---|---|
| I07 | Quantas horas absolutas esta entrega absorve? | `total_horas_planejadas_entrega` |
| I08 | Qual percentual do total da unidade esta entrega representa? | `proporcao_horas_perc` |

Por isso a explicacao abaixo se concentra somente no que e diferente.

---

### I08 — Consulta completa

Os blocos `parametros`, `anos`, `feriados_fixos`, `feriados_moveis`, `feriados_nacionais`, `calendario`, `links_distintos`, `horas_planejadas_por_plano` e `horas_alocadas_por_entrega` sao identicos ao Indicador 7. Consulte a secao 9 para a explicacao detalhada de cada um. Abaixo esta a consulta completa para uso direto.

```sql
with recursive
parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        8 as horas_por_dia,
        0 as incluir_excluidos
),
anos as (
    select year((select data_inicio from parametros)) as ano
    union all
    select ano + 1
    from anos
    where ano < year((select data_fim from parametros))
),
feriados_fixos as (
    select date(concat(ano, '-01-01')) as data_feriado from anos
    union all select date(concat(ano, '-04-21')) from anos
    union all select date(concat(ano, '-05-01')) from anos
    union all select date(concat(ano, '-09-07')) from anos
    union all select date(concat(ano, '-10-12')) from anos
    union all select date(concat(ano, '-11-02')) from anos
    union all select date(concat(ano, '-11-15')) from anos
    union all select date(concat(ano, '-11-20')) from anos
    union all select date(concat(ano, '-12-25')) from anos
),
feriados_moveis as (
    select null as data_feriado where 1 = 0
    -- union all select date('2025-04-18')
    -- union all select date('2026-04-03')
),
feriados_nacionais as (
    select data_feriado from feriados_fixos
    union
    select data_feriado from feriados_moveis
),
calendario as (
    select (select data_inicio from parametros) as data_dia
    union all
    select date_add(data_dia, interval 1 day)
    from calendario
    where data_dia < (select data_fim from parametros)
),
links_distintos as (
    select
        pte.plano_trabalho_id,
        pte.plano_entrega_entrega_id as id_entrega,
        coalesce(pte.forca_trabalho, 0) as forca_trabalho
    from planos_trabalhos_entregas pte
    where pte.plano_entrega_entrega_id is not null
),
horas_planejadas_por_plano as (
    select
        pt.id as plano_trabalho_id,
        pt.unidade_id,
        count(c.data_dia) * p.horas_por_dia as horas_planejadas_plano
    from planos_trabalhos pt
    cross join parametros p
    join calendario c
        on c.data_dia between greatest(date(pt.data_inicio), p.data_inicio)
                          and least(date(pt.data_fim), p.data_fim)
    left join feriados_nacionais fn
        on fn.data_feriado = c.data_dia
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim) >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and dayofweek(c.data_dia) not in (1, 7)
      and fn.data_feriado is null
    group by pt.id, pt.unidade_id, p.horas_por_dia
),
horas_alocadas_por_entrega as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        coalesce(
            nullif(trim(coalesce(pee.descricao, '')), ''),
            nullif(trim(coalesce(pee.descricao_entrega, '')), ''),
            'N.I.'
        ) as nome_entrega,
        hpp.horas_planejadas_plano * (ld.forca_trabalho / 100.0) as horas_planejadas_alocadas
    from links_distintos ld
    join horas_planejadas_por_plano hpp
        on hpp.plano_trabalho_id = ld.plano_trabalho_id
    left join planos_entregas_entregas pee
        on pee.id = ld.id_entrega
    left join unidades un
        on un.id = hpp.unidade_id
),
capacidade_unidade as (
    select
        coalesce(un.sigla, 'N.I.')      as unidade_sigla,
        sum(hpp.horas_planejadas_plano) as total_horas_disponiveis_unidade
    from horas_planejadas_por_plano hpp
    left join unidades un
        on un.id = hpp.unidade_id
    group by coalesce(un.sigla, 'N.I.')
)
select
    h.unidade_sigla,
    min(h.unidade_nome)                          as unidade_nome,
    h.nome_entrega,
    round(sum(h.horas_planejadas_alocadas), 2)   as horas_planejadas_entrega,
    round(c.total_horas_disponiveis_unidade, 2)  as total_horas_disponiveis_unidade,
    round(
        (sum(h.horas_planejadas_alocadas) / nullif(c.total_horas_disponiveis_unidade, 0)) * 100,
        2
    ) as proporcao_horas_perc
from horas_alocadas_por_entrega h
join capacidade_unidade c
    on c.unidade_sigla = h.unidade_sigla
group by h.unidade_sigla, h.nome_entrega,
         c.total_horas_disponiveis_unidade
order by h.unidade_sigla, proporcao_horas_perc desc;
```

---

### O bloco novo: `capacidade_unidade`

```sql
capacidade_unidade as (
    select
        coalesce(un.sigla, 'N.I.')      as unidade_sigla,
        sum(hpp.horas_planejadas_plano) as total_horas_disponiveis_unidade
    from horas_planejadas_por_plano hpp
    left join unidades un
        on un.id = hpp.unidade_id
    group by coalesce(un.sigla, 'N.I.')
)
```

Este e o unico bloco que nao existe no Indicador 7. Ele calcula o **total de horas de trabalho disponiveis** de todos os servidores da unidade no periodo — o denominador `B` da formula OCDE.

**Diferenca fundamental em relacao ao numerador:**

| Grandeza | Fonte | O que representa |
|---|---|---|
| `horas_planejadas_alocadas` (A) | `horas_planejadas_por_plano × forca_trabalho%` | Horas que o servidor dedicou a uma entrega especifica |
| `total_horas_disponiveis_unidade` (B) | `horas_planejadas_por_plano` (soma bruta) | Total de horas disponiveis de todos os servidores da unidade, independente de alocacao |

A fonte e `horas_planejadas_por_plano` — o mesmo CTE que calcula dias uteis por plano, mas sem aplicar o percentual de `forca_trabalho`. Isso garante que o denominador represente a capacidade total real da unidade, inclusive horas de servidores que nao linkaram nenhuma entrega no periodo.

**Por que isso importa:** se uma unidade tem 3 servidores com 200h disponiveis cada (600h total) e apenas 400h foram alocadas a entregas, o denominador correto e 600h — nao 400h. Usar 400h inflaria artificialmente as proporcoes e a soma ultrapassaria 100%.

**Exemplo com a formula correta:**

| entrega | horas (A) | total disponivel (B) | proporcao |
|---|---|---|---|
| Entrega X | 80h | 600h | 13.33% |
| Entrega Y | 60h | 600h | 10.00% |
| Entrega Z | 40h | 600h | 6.67% |
| (nao alocado) | 420h | — | — |
| **Total** | **600h** | **600h** | **30.00%** |

A soma das proporcoes das entregas nao precisa ser 100% — o restante representa horas disponiveis nao atribuidas explicitamente a nenhuma entrega do sistema.

---

### O SELECT final (o que muda em relacao ao I07)

```sql
select
    h.unidade_sigla,
    min(h.unidade_nome)                          as unidade_nome,
    h.nome_entrega,
    round(sum(h.horas_planejadas_alocadas), 2)   as horas_planejadas_entrega,
    round(c.total_horas_disponiveis_unidade, 2)  as total_horas_disponiveis_unidade,
    round(
        (sum(h.horas_planejadas_alocadas) / nullif(c.total_horas_disponiveis_unidade, 0)) * 100,
        2
    ) as proporcao_horas_perc
from horas_alocadas_por_entrega h
join capacidade_unidade c
    on c.unidade_sigla = h.unidade_sigla
group by h.unidade_sigla, h.nome_entrega,
         c.total_horas_disponiveis_unidade
order by h.unidade_sigla, proporcao_horas_perc desc;
```

**O join com `capacidade_unidade`:** traz o total disponivel da unidade para cada linha de entrega. E um `join` normal (nao `left join`) porque toda entrega pertence a alguma unidade.

**Uma linha por entrega (nao por ciclo de planejamento):** ao contrario do I07, o I08 agrupa por `nome_entrega` — e nao por `id_entrega`. Isso consolida todos os ciclos de planejamento de uma mesma entrega em uma unica linha, somando as horas alocadas ao longo de todo o periodo de analise.

A entrega "EVENTOS PREVISTOS NO PDP ICMBIO REALIZADOS", que no I07 aparece em quatro linhas (uma por ciclo), no I08 aparece em uma unica linha com o total acumulado:

| nome_entrega | horas (A) | total disponivel (B) | proporcao |
|---|---|---|---|
| EVENTOS PREVISTOS NO PDP ICMBIO REALIZADOS | 300h | 1200h | 25.00% |

**O `min()` para `unidade_nome`:** evita problemas com `ONLY_FULL_GROUP_BY` do MySQL — garante que o nome da unidade apareca mesmo sem estar no `GROUP BY`.

---

---

## Eixo 4: Mapeamento das tabelas de avaliacao (executar antes de I09-I12)

Os indicadores I09 a I12 dependem das tabelas `avaliacoes`, `tipos_avaliacoes` e `tipos_avaliacoes_notas`. O conteudo exato dessas tabelas varia conforme a versao e configuracao do PETRVS. Execute as consultas abaixo **antes** de rodar qualquer indicador deste eixo para confirmar os nomes de campo e os valores de referencia.

```sql
-- 1. Tipos de avaliacao disponiveis no banco
select id, nome, descricao
from tipos_avaliacoes
where deleted_at is null
order by nome;

-- 2. Escala de notas (confirmar nome do campo numerico: nota, valor, pontuacao?)
select id, nota, descricao
from tipos_avaliacoes_notas
order by nota;

-- 3. Volume de avaliacoes por tipo
select
    ta.nome as tipo_avaliacao,
    count(*) as total,
    sum(case when av.deleted_at is null then 1 else 0 end) as ativos
from avaliacoes av
join tipos_avaliacoes ta on ta.id = av.tipo_avaliacao_id
group by ta.nome
order by total desc;

-- 4. Exemplos de avaliacoes de Plano de Trabalho (via consolidacao)
select
    av.id,
    ta.nome as tipo_avaliacao,
    tan.nota as valor_nota,
    tan.descricao as descricao_nota,
    av.created_at
from avaliacoes av
join tipos_avaliacoes ta on ta.id = av.tipo_avaliacao_id
join tipos_avaliacoes_notas tan on tan.id = av.tipo_avaliacao_nota_id
where av.plano_trabalho_consolidacao_id is not null
  and av.deleted_at is null
limit 20;

-- 5. Exemplos de avaliacoes de Plano de Entregas
select
    av.id,
    ta.nome as tipo_avaliacao,
    tan.nota as valor_nota,
    tan.descricao as descricao_nota,
    av.created_at
from avaliacoes av
join tipos_avaliacoes ta on ta.id = av.tipo_avaliacao_id
join tipos_avaliacoes_notas tan on tan.id = av.tipo_avaliacao_nota_id
where av.plano_entrega_id is not null
  and av.deleted_at is null
limit 20;
```

**Campos a confirmar antes de continuar:**

- `tipos_avaliacoes_notas`: verificar se o campo de valor numerico se chama `nota` (pode ser `valor`, `pontuacao` ou outro)
- `avaliacoes`: verificar que o filtro `plano_trabalho_consolidacao_id is not null` identifica corretamente as avaliacoes de PT e `plano_entrega_id is not null` as de PE

---

## Indicador I09 — Media da avaliacao do Plano de Trabalho (MySQL)

### O que esse indicador responde (I09)

A pergunta central e: em media, qual nota as equipes estao recebendo nas avaliacoes dos seus Planos de Trabalho, por unidade?

Enquanto I02-I04 medem o quanto foi entregue, o I09 mede como o trabalho foi avaliado — a qualidade percebida do desempenho. Uma unidade pode ter I02 = 100% (todas as entregas concluidas) e ainda assim ter I09 baixo se os avaliadores consideraram que o trabalho foi cumprido mas com baixa qualidade.

**Tabelas base:** `avaliacoes` → `planos_trabalhos_consolidacoes` → `planos_trabalhos` → `unidades`

### I09 — Consulta: media por unidade

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
avaliacoes_pt as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        coalesce(us.nome, 'N.I.') as nome_servidor,
        av.id as avaliacao_id,
        ta.nome as tipo_avaliacao,
        tan.nota as valor_nota  -- validar: pode ser valor, pontuacao ou outro campo
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes ta
        on ta.id = av.tipo_avaliacao_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pt.unidade_id
    left join usuarios us
        on us.id = pt.usuario_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
)
select
    unidade_sigla,
    unidade_nome,
    count(avaliacao_id)                                          as total_avaliacoes,
    round(avg(valor_nota), 2)                                    as media_nota_pt,
    min(valor_nota)                                              as nota_minima,
    max(valor_nota)                                              as nota_maxima,
    sum(case when valor_nota = 5 then 1 else 0 end)             as qtd_nota_5,
    sum(case when valor_nota = 2 then 1 else 0 end)             as qtd_nota_2,
    sum(case when valor_nota = 1 then 1 else 0 end)             as qtd_nota_1
from avaliacoes_pt
group by unidade_sigla, unidade_nome
order by unidade_sigla;
```

### I09 — Variante: detalhe por servidor

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
avaliacoes_pt as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(us.nome, 'N.I.') as nome_servidor,
        av.id as avaliacao_id,
        ta.nome as tipo_avaliacao,
        tan.nota as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes ta
        on ta.id = av.tipo_avaliacao_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pt.unidade_id
    left join usuarios us
        on us.id = pt.usuario_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
)
select
    unidade_sigla,
    nome_servidor,
    count(avaliacao_id)        as total_avaliacoes,
    round(avg(valor_nota), 2)  as media_nota_pt,
    min(valor_nota)            as nota_minima,
    max(valor_nota)            as nota_maxima
from avaliacoes_pt
group by unidade_sigla, nome_servidor
order by unidade_sigla, media_nota_pt desc;
```

### I09 — Como interpretar o resultado

| media_nota_pt | Interpretacao |
| --- | --- |
| 5.00 | Excelente — todas as avaliacoes foram excepcionais |
| 4.00 a 4.99 | Bom desempenho geral |
| 3.00 a 3.99 | Desempenho regular — merece acompanhamento |
| Abaixo de 3.00 | Sinal de alerta — investigar causas |

---

## Indicador I10 — Percentual de avaliacoes inadequadas (nota 2) (MySQL)

### O que esse indicador responde (I10)

A pergunta central e: qual percentual das avaliacoes de Planos de Trabalho recebeu nota 2 (inadequada) por unidade?

O I10 nao e apenas a contraface negativa do I11 — ele identifica especificamente servidores ou unidades com avaliacao formal de inadequacao, o que exige acompanhamento gerencial diferenciado (plano de melhoria, feedback estruturado).

**Tabelas base:** mesmas do I09.

### I10 — Consulta

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
avaliacoes_pt as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        av.id as avaliacao_id,
        tan.nota as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
)
select
    unidade_sigla,
    unidade_nome,
    count(avaliacao_id)                                                               as total_avaliacoes,
    sum(case when valor_nota = 2 then 1 else 0 end)                                  as qtd_nota_2,
    round(
        sum(case when valor_nota = 2 then 1 else 0 end) * 100.0
            / nullif(count(avaliacao_id), 0),
        2
    )                                                                                 as perc_inadequadas
from avaliacoes_pt
group by unidade_sigla, unidade_nome
order by perc_inadequadas desc, unidade_sigla;
```

---

## Indicador I11 — Percentual de avaliacoes excepcionais (nota 5) (MySQL)

### O que esse indicador responde (I11)

A pergunta central e: qual percentual das avaliacoes de Planos de Trabalho recebeu nota 5 (excepcional) por unidade?

Identifica unidades com alto nivel de excelencia reconhecida. Cruzado com o I04 (score de atingimento de metas), permite distinguir entre alta performance genuina e possivel avaliacao permissiva (nota 5 com metas nao cumpridas).

**Tabelas base:** mesmas do I09.

### I11 — Consulta

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
avaliacoes_pt as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome, 'N.I.') as unidade_nome,
        av.id as avaliacao_id,
        tan.nota as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
)
select
    unidade_sigla,
    unidade_nome,
    count(avaliacao_id)                                                               as total_avaliacoes,
    sum(case when valor_nota = 5 then 1 else 0 end)                                  as qtd_nota_5,
    round(
        sum(case when valor_nota = 5 then 1 else 0 end) * 100.0
            / nullif(count(avaliacao_id), 0),
        2
    )                                                                                 as perc_excepcionais
from avaliacoes_pt
group by unidade_sigla, unidade_nome
order by perc_excepcionais desc, unidade_sigla;
```

---

## Indicador I12 — Coerencia entre avaliacao do PT e do PE (MySQL)

### O que esse indicador responde (I12)

A pergunta central e: a nota media que a unidade recebe nas avaliacoes individuais (PT) e coerente com a nota que ela recebe na avaliacao coletiva (PE)?

Alta divergencia entre as duas medias pode indicar:

- **PT alto / PE baixo**: servidores bem avaliados individualmente, mas a entrega coletiva da unidade e percebida como insatisfatoria — possivel problema de coordenacao ou avaliacao individual por cordialidade.
- **PT baixo / PE alto**: a unidade entrega bem coletivamente mas os planos individuais nao sao reconhecidos — possivel subavaliacao dos servidores ou desconexao entre planos individuais e resultados da unidade.

**Tabelas base:** `avaliacoes` + `planos_trabalhos_consolidacoes` + `planos_trabalhos` (para PT) e `avaliacoes` + `planos_entregas` (para PE).

### I12 — Mapeamento: verificar avaliacoes de PE

```sql
-- Confirmar que existem avaliacoes com plano_entrega_id preenchido
select count(*) as total_avaliacoes_pe
from avaliacoes
where plano_entrega_id is not null
  and deleted_at is null;
```

### I12 — Consulta

```sql
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
media_pt_por_unidade as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        round(avg(tan.nota), 2)    as media_nota_pt,
        count(av.id)               as total_avaliacoes_pt
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
    group by coalesce(un.sigla, 'N.I.')
),
media_pe_por_unidade as (
    select
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        round(avg(tan.nota), 2)    as media_nota_pe,
        count(av.id)               as total_avaliacoes_pe
    from avaliacoes av
    join planos_entregas pe
        on pe.id = av.plano_entrega_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    left join unidades un
        on un.id = pe.unidade_id
    cross join parametros p
    where av.plano_entrega_id is not null
      and tan.nota is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(av.created_at) between p.data_inicio and p.data_fim
    group by coalesce(un.sigla, 'N.I.')
)
select
    coalesce(pt.unidade_sigla, pe.unidade_sigla)  as unidade_sigla,
    pt.media_nota_pt,
    pt.total_avaliacoes_pt,
    pe.media_nota_pe,
    pe.total_avaliacoes_pe,
    round(abs(pt.media_nota_pt - pe.media_nota_pe), 2) as diferenca_absoluta,
    case
        when pt.media_nota_pt is null or pe.media_nota_pe is null
            then 'Dados insuficientes'
        when abs(pt.media_nota_pt - pe.media_nota_pe) <= 1.0
            then 'Coerente'
        when abs(pt.media_nota_pt - pe.media_nota_pe) <= 2.0
            then 'Divergencia moderada'
        else
            'Alta divergencia'
    end as classificacao_coerencia
from media_pt_por_unidade pt
left join media_pe_por_unidade pe
    on pe.unidade_sigla = pt.unidade_sigla
order by diferenca_absoluta desc nulls last, unidade_sigla;
```

### I12 — Como interpretar o resultado

| classificacao_coerencia | Diferenca | Acao recomendada |
| --- | --- | --- |
| Coerente | <= 1.0 | Nenhuma — as avaliacoes estao alinhadas |
| Divergencia moderada | 1.1 a 2.0 | Monitorar — revisar criterios de avaliacao da unidade |
| Alta divergencia | > 2.0 | Investigar — reuniao de calibragem entre lideranca e equipe |
| Dados insuficientes | — | A unidade nao tem avaliacoes dos dois tipos no periodo |

**Sobre `nulls last`:** unidades sem avaliacao de PE aparecem no final do resultado com `diferenca_absoluta = NULL` e classificacao `Dados insuficientes`. Isso e o comportamento esperado — indica que a unidade tem PT avaliados mas o Plano de Entregas ainda nao passou por avaliacao formal no periodo.
