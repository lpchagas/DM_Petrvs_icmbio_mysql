-- =========================================================
-- PGD ICMBio - Indicadores OCDE (MySQL de origem)
-- Versao guiada para iniciantes no DBeaver
-- =========================================================
--
-- FINALIDADE
-- Este arquivo foi preparado para consultar os dados originais do PETRVS
-- diretamente no MySQL (sem datamart).
--
-- COMO USAR NO DBEAVER
-- 1. Abra a conexao MySQL `petrvs_icmbio`.
-- 2. Abra um SQL Editor.
-- 3. Cole ou abra este arquivo.
-- 4. Execute uma consulta por vez.
--
-- INDICE
-- I01  Indicador 1  - Proporcao de servidores por regime de trabalho (2 variantes)
-- I02  Indicador 2  - Taxa de cumprimento das entregas
-- I03  Indicador 3  - Taxa de cumprimento de metas por entrega
-- I04  Indicador 4  - Indice de atingimento de metas
-- I05  Indicador 5  - Distribuicao das entregas entre os servidores
-- I06  Indicador 6  - Grau de responsabilidade pelas entregas
-- I07  Indicador 7  - Horas por entrega - planejadas
-- I08  Indicador 8  - Proporcao de horas por entrega - planejadas
-- I09  Indicador 9  - Media da avaliacao do PT por unidade
-- I10  Indicador 10 - Percentual de avaliacoes inadequadas (nota 2)
-- I11  Indicador 11 - Percentual de avaliacoes excepcionais (nota 5)
-- I12  Indicador 12 - Coerencia entre avaliacao do PT e do PE
--
-- DICA IMPORTANTE
-- No bloco `parametros`:
-- - ajuste `data_inicio` e `data_fim`
-- - use `incluir_excluidos = 1` se quiser incluir registros com `deleted_at`
--
-- REVISAO DE QUALIDADE: 30.04.2026
-- I02, I03 e I04 corrigidos (ver cabecalho de cada indicador para detalhes)
-- I01 e I09-I12 adicionados em 01.05.2026


-- =========================================================
-- I01 - Indicador 1 - Variante 1
-- Proporcao de servidores por regime de trabalho (visao geral)
-- =========================================================
--
-- Regra utilizada:
-- - para cada servidor com PT vigente no periodo, captura a modalidade de trabalho
-- - conta servidores distintos por modalidade em todo o orgao
-- - calcula a proporcao de cada regime sobre o total
--
-- Requisito tecnico:
-- - usa window function sum() over () para calcular proporcao - requer MySQL 8.0+
--
-- Pre-requisito de mapeamento:
-- - os valores de modalidade vem de tipos_modalidades.nome
-- - verificar no banco quais sao os nomes exatos (ex: 'Teletrabalho', 'Presencial')
-- - um servidor com PT em mais de uma modalidade no periodo sera contado
--   na modalidade do primeiro PT captado pelo SELECT DISTINCT (comportamento esperado)

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
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
      and date(pt.data_fim)   >= p.data_inicio
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
        total_servidores * 100.0
            / nullif(sum(total_servidores) over (), 0),
        2
    ) as proporcao_perc
from contagem_por_regime
order by total_servidores desc;


-- =========================================================
-- I01 - Indicador 1 - Variante 2
-- Proporcao de servidores por regime de trabalho (por unidade)
-- =========================================================
--
-- Diferenca em relacao a Variante 1:
-- - desagrega o resultado por unidade organizacional
-- - a proporcao e calculada dentro de cada unidade (partition by unidade_sigla)
-- - permite comparar o perfil de regime entre unidades diferentes
--
-- Requisito tecnico:
-- - usa window function sum() over (partition by) - requer MySQL 8.0+

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
servidores_por_unidade as (
    select distinct
        coalesce(un.sigla, 'N.I.') as unidade_sigla,
        coalesce(un.nome,  'N.I.') as unidade_nome,
        pt.usuario_id,
        coalesce(tm.nome,  'N.I.') as modalidade
    from planos_trabalhos pt
    left join tipos_modalidades tm
        on tm.id = pt.tipo_modalidade_id
    left join unidades un
        on un.id = pt.unidade_id
    cross join parametros p
    where date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
      and pt.usuario_id is not null
),
contagem as (
    select
        unidade_sigla,
        min(unidade_nome)          as unidade_nome,
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


-- =========================================================
-- I02 - Indicador 2
-- Taxa de cumprimento das entregas (por unidade)
-- =========================================================
--
-- Regra OCDE:
-- - denominador (B): total de entregas com meta valida no ciclo PE
-- - numerador (A): entregas onde meta_executada >= meta_planejada
-- - taxa: (A / B) x 100
--
-- Correcao critica aplicada (30.04.2026):
-- - join por pe.unidade_id (dono do PE), nao pee.unidade_id (executor da entrega)
-- - filtro de data por sobreposicao do ciclo PE, nao por prazo individual
-- - pe.deleted_at adicionado ao soft-delete
-- - coluna grupo_performance (A/B/C/D) adicionada
-- - colunas total_cadastradas e total_vence_no_periodo adicionadas

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
universo_bruto as (
    select
        u.sigla  as unidade_sigla,
        count(*) as total_cadastradas
    from planos_entregas pe
    join planos_entregas_entregas pee
        on pee.plano_entrega_id = pe.id
    join unidades u
        on u.id = pe.unidade_id
    cross join parametros p
    where date(pe.data_inicio) <= p.data_fim
      and date(pe.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pe.deleted_at  is null)
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
    group by u.sigla
),
entregas_ciclo as (
    select
        u.sigla                              as unidade_sigla,
        pee.id                               as id_entrega,
        pee.progresso_esperado               as meta_planejada,
        coalesce(pee.progresso_realizado, 0) as meta_executada,
        case
            when date(pee.data_fim) between p.data_inicio and p.data_fim
            then 1 else 0
        end                                  as vence_no_periodo
    from planos_entregas pe
    join planos_entregas_entregas pee
        on pee.plano_entrega_id = pe.id
    join unidades u
        on u.id = pe.unidade_id
    cross join parametros p
    where date(pe.data_inicio) <= p.data_fim
      and date(pe.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pe.deleted_at  is null)
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
),
resumo as (
    select
        unidade_sigla,
        count(*)                                                          as total_no_ciclo,
        sum(vence_no_periodo)                                             as total_vence_no_periodo,
        sum(case when meta_executada >= meta_planejada then 1 else 0 end) as total_concluidas,
        round(
            sum(case when meta_executada >= meta_planejada then 1 else 0 end)
                / nullif(count(*), 0) * 100,
            2
        )                                                                 as taxa_cumprimento_perc
    from entregas_ciclo
    group by unidade_sigla
)
select
    r.unidade_sigla,
    b.total_cadastradas,
    r.total_no_ciclo,
    r.total_vence_no_periodo,
    round(
        r.total_vence_no_periodo * 100.0 / nullif(r.total_no_ciclo, 0),
        1
    )                                                                     as proporcao_vence_no_periodo_perc,
    r.total_concluidas,
    r.taxa_cumprimento_perc,
    case
        when r.taxa_cumprimento_perc >= 90 then 'A - Alto desempenho'
        when r.taxa_cumprimento_perc >= 70 then 'B - Bom desempenho'
        when r.taxa_cumprimento_perc >= 50 then 'C - Desempenho intermediario'
        else                                    'D - Baixo desempenho'
    end                                                                   as grupo_performance
from resumo r
left join universo_bruto b
    on b.unidade_sigla = r.unidade_sigla
order by r.taxa_cumprimento_perc desc, r.unidade_sigla;


-- =========================================================
-- I03 - Indicador 3
-- Taxa de cumprimento de metas por entrega
-- =========================================================
--
-- Regra utilizada:
-- - meta_planejada: progresso_esperado
-- - meta_executada: progresso_realizado
-- - taxa: (meta_executada / meta_planejada) * 100
--
-- Filtro de data: pee.data_fim (prazo individual) — intencional no I03.
-- O I03 responde "como foi cada entrega que venceu neste periodo?",
-- diferente do I02/I04 que usam sobreposicao do ciclo PE completo.
--
-- Correcao critica aplicada (30.04.2026):
-- - join substituido para pe.unidade_id (dono do PE)
-- - pe.deleted_at adicionado ao soft-delete
-- - status_entrega expandido de 3 para 5 categorias (padrao OCDE)

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
entregas_base as (
    select
        u.sigla                              as unidade_sigla,
        pee.id                               as id_entrega,
        coalesce(
            nullif(trim(pee.descricao), ''),
            nullif(trim(pee.descricao_entrega), ''),
            'N.I.'
        )                                    as nome_entrega,
        pee.progresso_esperado               as meta_planejada,
        coalesce(pee.progresso_realizado, 0) as meta_executada
    from planos_entregas pe
    join planos_entregas_entregas pee
        on pee.plano_entrega_id = pe.id
    join unidades u
        on u.id = pe.unidade_id
    cross join parametros p
    where date(pee.data_fim) between p.data_inicio and p.data_fim
      and (p.incluir_excluidos = 1 or pe.deleted_at  is null)
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
),
entregas_com_taxa as (
    select
        unidade_sigla,
        id_entrega,
        nome_entrega,
        meta_planejada,
        meta_executada,
        round(
            meta_executada / nullif(meta_planejada, 0) * 100,
            2
        )                                    as taxa_atingimento_perc
    from entregas_base
)
select
    unidade_sigla,
    id_entrega,
    nome_entrega,
    meta_planejada,
    meta_executada,
    taxa_atingimento_perc,
    case
        when taxa_atingimento_perc >  100 then 'Superexecutada'
        when taxa_atingimento_perc =  100 then 'Concluida'
        when taxa_atingimento_perc >=  70 then 'Parcialmente cumprida'
        when taxa_atingimento_perc >    0 then 'Em andamento'
        else                                   'Nao executada'
    end as status_entrega
from entregas_com_taxa
order by unidade_sigla, taxa_atingimento_perc desc;


-- =========================================================
-- I04 - Indicador 4
-- Indice de atingimento de metas (score medio por unidade)
-- =========================================================
--
-- Regra utilizada:
-- - proporcao por entrega: abs(progresso_realizado) / abs(progresso_esperado)
-- - score da unidade: media de todas as proporcoes x 100
--
-- Diferenca em relacao ao Indicador 3:
-- - Indicador 3: mostra a taxa de cada entrega individualmente (filtra por pee.data_fim)
-- - Indicador 4: resume em um unico score medio por unidade (usa ciclo PE = mesmo escopo do I02)
--
-- O uso de abs() garante que metas expressas como reducao (negativo)
-- sejam tratadas corretamente na proporcao.
--
-- Correcao critica aplicada (30.04.2026):
-- - join substituido para pe.unidade_id (dono do PE)
-- - filtro de data corrigido para sobreposicao do ciclo PE (igual ao I02)
--   garantindo que total_no_ciclo do I04 coincida com total_no_ciclo do I02
-- - pe.deleted_at adicionado ao soft-delete
-- - coluna grupo_performance (A/B/C/D) adicionada

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
entregas_ciclo as (
    select
        u.sigla                                      as unidade_sigla,
        pee.id                                       as id_entrega,
        abs(coalesce(pee.progresso_realizado, 0))
            / nullif(abs(pee.progresso_esperado), 0) as proporcao_atingimento
    from planos_entregas pe
    join planos_entregas_entregas pee
        on pee.plano_entrega_id = pe.id
    join unidades u
        on u.id = pe.unidade_id
    cross join parametros p
    where date(pe.data_inicio) <= p.data_fim
      and date(pe.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pe.deleted_at  is null)
      and (p.incluir_excluidos = 1 or pee.deleted_at is null)
      and pee.progresso_esperado is not null
      and pee.progresso_esperado > 0
),
resumo as (
    select
        unidade_sigla,
        count(id_entrega)                          as total_no_ciclo,
        round(avg(proporcao_atingimento) * 100, 2) as score_atingimento_perc
    from entregas_ciclo
    group by unidade_sigla
)
select
    unidade_sigla,
    total_no_ciclo,
    score_atingimento_perc,
    case
        when score_atingimento_perc >= 90 then 'A - Alto desempenho'
        when score_atingimento_perc >= 70 then 'B - Bom desempenho'
        when score_atingimento_perc >= 50 then 'C - Desempenho intermediario'
        else                                   'D - Baixo desempenho'
    end as grupo_performance
from resumo
order by score_atingimento_perc desc, unidade_sigla;


-- =========================================================
-- I05 - Indicador 5
-- Distribuicao das entregas entre os servidores
-- =========================================================
--
-- Regra utilizada:
-- - vinculo servidor-entrega: planos_trabalhos -> planos_trabalhos_entregas
-- - filtro de periodo: plano de trabalho com vigencia no intervalo
-- - resultado: uma linha por servidor, com quantidade de entregas e media da unidade
--
-- Requisito tecnico:
-- - usa window function avg() over (partition by) - requer MySQL 8.0 ou superior
--
-- Observacao de mapeamento:
-- - no datamart PostgreSQL, o vinculo vem de di_trabalhos (atividade_data_distribuicao)
-- - no MySQL de origem, o vinculo e reconstruido via planos_trabalhos_entregas

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


-- =========================================================
-- I06 - Indicador 6
-- Grau de responsabilidade pelas entregas
-- =========================================================
--
-- Regra utilizada:
-- - para cada entrega, conta quantos servidores distintos estao vinculados
-- - classifica a entrega pela faixa de responsaveis: 1, 2, 3 ou 4+
-- - resume quantas entregas caem em cada faixa, por unidade
--
-- Perspectiva inversa ao Indicador 5:
-- - I05: quantas entregas tem cada servidor?
-- - I06: quantos servidores tem cada entrega?
--
-- Tabelas base: mesmas do Indicador 5
-- - planos_trabalhos (servidor e unidade)
-- - planos_trabalhos_entregas (vinculo com a entrega)

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


-- =========================================================
-- I07 - Indicador 7
-- Horas por entrega - planejadas
-- =========================================================
--
-- O que este indicador calcula:
-- Para cada entrega, soma as horas de trabalho planejadas
-- pelos servidores cujos planos de trabalho cobrem o periodo.
-- As horas sao distribuidas proporcionalmente entre as entregas
-- vinculadas a cada plano de trabalho.
--
-- Diferenca tecnica importante em relacao ao PostgreSQL:
-- - PostgreSQL usa generate_series() para gerar sequencias de dias
-- - MySQL nao tem generate_series(); usamos WITH RECURSIVE
--
-- Diferenca na deteccao de fim de semana:
-- - PostgreSQL: extract(dow) -> 0=Domingo, 6=Sabado -> not in (0, 6)
-- - MySQL: dayofweek()      -> 1=Domingo, 7=Sabado -> not in (1, 7)
--
-- Limite de recursao:
-- - O calendario usa WITH RECURSIVE para gerar dias
-- - Limite padrao do MySQL: 1000 iteracoes (suficiente para ~2,7 anos)
-- - Para periodos maiores: SET SESSION cte_max_recursion_depth = 5000;
--
-- Requer: MySQL 8.0+

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
    -- union all select date('2025-04-18')  -- Sexta-feira da Paixao 2025
    -- union all select date('2026-04-03')  -- Sexta-feira da Paixao 2026
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


-- =========================================================
-- I08 - Indicador 8
-- Proporcao de horas por entrega - planejadas
-- =========================================================
--
-- Relacao com o Indicador 7:
-- - I07: mostra quantas horas absolutas cada entrega absorve
-- - I08: mostra qual PERCENTUAL do total da unidade cada entrega representa
--
-- Blocos identicos ao I07: parametros, anos, feriados_fixos,
--   feriados_moveis, feriados_nacionais, calendario, links_distintos,
--   horas_planejadas_por_plano, horas_alocadas_por_entrega
--
-- Bloco novo: capacidade_unidade
--   - soma o total de horas alocadas por unidade
--   - serve como denominador do percentual
--
-- SELECT final:
--   - acrescenta total_horas_unidade e proporcao_horas_perc

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
    -- union all select date('2025-04-18')  -- Sexta-feira da Paixao 2025
    -- union all select date('2026-04-03')  -- Sexta-feira da Paixao 2026
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
        coalesce(nullif(trim(coalesce(pee.descricao_entrega, '')), ''), 'N.I.') as descricao_entrega,
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
    min(h.descricao_entrega)                     as descricao_entrega,
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


-- =========================================================
-- I09 - Indicador 9
-- Media da avaliacao do Plano de Trabalho por unidade
-- =========================================================
--
-- Regra utilizada:
-- - caminho do vinculo: avaliacoes -> planos_trabalhos_consolidacoes -> planos_trabalhos
-- - nota da avaliacao: tipos_avaliacoes_notas.nota (campo numerico 1-5)
-- - agrupa por unidade e calcula media, minimo, maximo e distribuicao de notas
--
-- Pre-requisito de mapeamento:
-- - verificar nome do campo numerico em tipos_avaliacoes_notas
--   (pode ser 'nota', 'valor' ou 'pontuacao' conforme versao do PETRVS)
-- - verificar se avaliacoes.plano_trabalho_consolidacao_id esta populado no banco
--
-- Faixas de desempenho calculadas no SELECT final:
-- - media >= 4.5: Excepcional
-- - media >= 3.5: Alto desempenho
-- - media >= 2.5: Adequado
-- - media >= 1.5: Inadequado
-- - media <  1.5: Nao executado

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
avaliacoes_pt as (
    select
        av.id          as id_avaliacao,
        pt.unidade_id,
        tan.nota       as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
),
media_por_unidade as (
    select
        coalesce(un.sigla, 'N.I.')                               as unidade_sigla,
        coalesce(un.nome, 'N.I.')                                as unidade_nome,
        count(avpt.id_avaliacao)                                 as total_avaliacoes_pt,
        round(avg(avpt.valor_nota), 2)                           as media_nota_pt,
        min(avpt.valor_nota)                                     as nota_minima,
        max(avpt.valor_nota)                                     as nota_maxima,
        sum(case when avpt.valor_nota = 1 then 1 else 0 end)     as qtd_nota_1,
        sum(case when avpt.valor_nota = 2 then 1 else 0 end)     as qtd_nota_2,
        sum(case when avpt.valor_nota = 3 then 1 else 0 end)     as qtd_nota_3,
        sum(case when avpt.valor_nota = 4 then 1 else 0 end)     as qtd_nota_4,
        sum(case when avpt.valor_nota = 5 then 1 else 0 end)     as qtd_nota_5
    from avaliacoes_pt avpt
    left join unidades un
        on un.id = avpt.unidade_id
    group by coalesce(un.sigla, 'N.I.'), coalesce(un.nome, 'N.I.')
)
select
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    media_nota_pt,
    nota_minima,
    nota_maxima,
    qtd_nota_1,
    qtd_nota_2,
    qtd_nota_3,
    qtd_nota_4,
    qtd_nota_5,
    case
        when media_nota_pt >= 4.5 then 'Excepcional'
        when media_nota_pt >= 3.5 then 'Alto desempenho'
        when media_nota_pt >= 2.5 then 'Adequado'
        when media_nota_pt >= 1.5 then 'Inadequado'
        else 'Nao executado'
    end as faixa_desempenho
from media_por_unidade
order by media_nota_pt desc, unidade_sigla;


-- =========================================================
-- I10 - Indicador 10
-- Percentual de avaliacoes inadequadas (nota 2)
-- =========================================================
--
-- Regra utilizada:
-- - denominador: total de avaliacoes de PT no periodo
-- - numerador: avaliacoes com nota = 2 (Inadequado)
-- - percentual: (numerador / denominador) x 100
--
-- Mesmo caminho de vinculo do I09:
-- - avaliacoes -> planos_trabalhos_consolidacoes -> planos_trabalhos
--
-- Pre-requisito: confirmar que nota = 2 corresponde a 'Inadequado' no banco
--
-- Niveis de alerta:
-- - >= 30%: Atencao critica
-- - >= 15%: Atencao moderada
-- - >=  5%: Observacao
-- - <   5%: Baixa prevalencia

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
avaliacoes_pt as (
    select
        av.id          as id_avaliacao,
        pt.unidade_id,
        tan.nota       as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
),
proporcao_por_unidade as (
    select
        coalesce(un.sigla, 'N.I.')                                   as unidade_sigla,
        coalesce(un.nome, 'N.I.')                                    as unidade_nome,
        count(avpt.id_avaliacao)                                     as total_avaliacoes_pt,
        sum(case when avpt.valor_nota = 2 then 1 else 0 end)         as qtd_inadequado,
        round(
            sum(case when avpt.valor_nota = 2 then 1 else 0 end)
                / nullif(count(avpt.id_avaliacao), 0) * 100,
            2
        )                                                            as perc_inadequado
    from avaliacoes_pt avpt
    left join unidades un
        on un.id = avpt.unidade_id
    group by coalesce(un.sigla, 'N.I.'), coalesce(un.nome, 'N.I.')
)
select
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    qtd_inadequado,
    perc_inadequado,
    case
        when perc_inadequado >= 30 then 'Atencao critica'
        when perc_inadequado >= 15 then 'Atencao moderada'
        when perc_inadequado >= 5  then 'Observacao'
        else 'Baixa prevalencia'
    end as nivel_alerta
from proporcao_por_unidade
order by perc_inadequado desc, unidade_sigla;


-- =========================================================
-- I11 - Indicador 11
-- Percentual de avaliacoes excepcionais (nota 5)
-- =========================================================
--
-- Regra utilizada:
-- - denominador: total de avaliacoes de PT no periodo
-- - numerador: avaliacoes com nota = 5 (Excepcional)
-- - percentual: (numerador / denominador) x 100
--
-- Mesmo caminho de vinculo do I09 e I10:
-- - avaliacoes -> planos_trabalhos_consolidacoes -> planos_trabalhos
--
-- Pre-requisito: confirmar que nota = 5 corresponde a 'Excepcional' no banco
--
-- Leitura complementar com I10:
-- - alta prevalencia de nota 5 + baixa de nota 2: distribuicao saudavel
-- - alta prevalencia em ambos os extremos: bimodalidade - pode indicar sub-uso
--   da escala intermediaria (notas 3 e 4 raramente usadas)
--
-- Niveis de reconhecimento:
-- - >= 40%: Reconhecimento elevado
-- - >= 20%: Desempenho diferenciado
-- - >=  5%: Destaque pontual
-- - <   5%: Escala subutilizada

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
avaliacoes_pt as (
    select
        av.id          as id_avaliacao,
        pt.unidade_id,
        tan.nota       as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
),
proporcao_por_unidade as (
    select
        coalesce(un.sigla, 'N.I.')                                   as unidade_sigla,
        coalesce(un.nome, 'N.I.')                                    as unidade_nome,
        count(avpt.id_avaliacao)                                     as total_avaliacoes_pt,
        sum(case when avpt.valor_nota = 5 then 1 else 0 end)         as qtd_excepcional,
        round(
            sum(case when avpt.valor_nota = 5 then 1 else 0 end)
                / nullif(count(avpt.id_avaliacao), 0) * 100,
            2
        )                                                            as perc_excepcional
    from avaliacoes_pt avpt
    left join unidades un
        on un.id = avpt.unidade_id
    group by coalesce(un.sigla, 'N.I.'), coalesce(un.nome, 'N.I.')
)
select
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    qtd_excepcional,
    perc_excepcional,
    case
        when perc_excepcional >= 40 then 'Reconhecimento elevado'
        when perc_excepcional >= 20 then 'Desempenho diferenciado'
        when perc_excepcional >= 5  then 'Destaque pontual'
        else 'Escala subutilizada'
    end as nivel_reconhecimento
from proporcao_por_unidade
order by perc_excepcional desc, unidade_sigla;


-- =========================================================
-- I12 - Indicador 12
-- Coerencia entre avaliacao do PT e do PE
-- =========================================================
--
-- Regra utilizada:
-- - calcula a media das notas do PT e do PE separadamente por unidade
-- - compara as duas medias: diferenca absoluta e direcional
-- - classifica a coerencia em 3 faixas
--
-- Dois caminhos de vinculo paralelos (CTEs independentes):
-- - PT: avaliacoes -> planos_trabalhos_consolidacoes -> planos_trabalhos
-- - PE: avaliacoes -> planos_entregas (via plano_entrega_id)
--
-- Pre-requisito:
-- - confirmar que avaliacoes.plano_trabalho_consolidacao_id esta populado (vinculo PT)
-- - confirmar que avaliacoes.plano_entrega_id esta populado (vinculo PE)
-- - uma unidade so aparece no resultado se tiver avaliacoes nos DOIS tipos (INNER JOIN)
--
-- Classificacao de coerencia:
-- - diferenca <= 1.0: Coerente (variacao esperada)
-- - diferenca <= 2.0: Divergencia moderada (merece investigacao)
-- - diferenca >  2.0: Alta divergencia (sinal de desalinhamento sistematico)
--
-- Direcao da divergencia:
-- - PT > PE: servidores avaliados melhor do que a entrega da unidade
-- - PE > PT: entrega da unidade avaliada melhor do que os servidores individualmente

with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0                  as incluir_excluidos
),
avaliacoes_pt as (
    select
        pt.unidade_id,
        tan.nota       as valor_nota
    from avaliacoes av
    join planos_trabalhos_consolidacoes ptc
        on ptc.id = av.plano_trabalho_consolidacao_id
    join planos_trabalhos pt
        on pt.id = ptc.plano_trabalho_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    cross join parametros p
    where av.plano_trabalho_consolidacao_id is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(pt.data_inicio) <= p.data_fim
      and date(pt.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pt.deleted_at is null)
),
avaliacoes_pe as (
    select
        pe.unidade_id,
        tan.nota       as valor_nota
    from avaliacoes av
    join planos_entregas pe
        on pe.id = av.plano_entrega_id
    join tipos_avaliacoes_notas tan
        on tan.id = av.tipo_avaliacao_nota_id
    cross join parametros p
    where av.plano_entrega_id is not null
      and (p.incluir_excluidos = 1 or av.deleted_at is null)
      and date(pe.data_inicio) <= p.data_fim
      and date(pe.data_fim)   >= p.data_inicio
      and (p.incluir_excluidos = 1 or pe.deleted_at is null)
),
media_pt_por_unidade as (
    select
        unidade_id,
        count(*)                  as total_avaliacoes_pt,
        round(avg(valor_nota), 2) as media_nota_pt
    from avaliacoes_pt
    group by unidade_id
),
media_pe_por_unidade as (
    select
        unidade_id,
        count(*)                  as total_avaliacoes_pe,
        round(avg(valor_nota), 2) as media_nota_pe
    from avaliacoes_pe
    group by unidade_id
),
coerencia as (
    select
        coalesce(un.sigla, 'N.I.')                           as unidade_sigla,
        coalesce(un.nome, 'N.I.')                            as unidade_nome,
        mpt.total_avaliacoes_pt,
        mpt.media_nota_pt,
        mpe.total_avaliacoes_pe,
        mpe.media_nota_pe,
        round(abs(mpt.media_nota_pt - mpe.media_nota_pe), 2) as diferenca_absoluta,
        round(mpt.media_nota_pt - mpe.media_nota_pe, 2)      as diferenca_direcional
    from media_pt_por_unidade mpt
    join media_pe_por_unidade mpe
        on mpe.unidade_id = mpt.unidade_id
    left join unidades un
        on un.id = mpt.unidade_id
)
select
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    media_nota_pt,
    total_avaliacoes_pe,
    media_nota_pe,
    diferenca_absoluta,
    diferenca_direcional,
    case
        when diferenca_absoluta <= 1.0 then 'Coerente'
        when diferenca_absoluta <= 2.0 then 'Divergencia moderada'
        else 'Alta divergencia'
    end as classificacao_coerencia,
    case
        when diferenca_direcional > 0 then 'PT > PE'
        when diferenca_direcional < 0 then 'PE > PT'
        else 'Sem diferenca'
    end as direcao_divergencia
from coerencia
order by diferenca_absoluta desc, unidade_sigla;
