-- Arquivo de consultas SQL (MySQL - origem PETRVS)
-- Indicadores OCDE do PGD no ICMBio
-- Indicadores disponiveis neste arquivo: 2, 3, 4, 5, 6, 7, 8

-- =========================================================
-- Indicador 2
-- Taxa de cumprimento das entregas
-- Base de origem: planos_entregas_entregas
-- =========================================================
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
entregas_base as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        coalesce(u.nome, 'N.I.') as unidade_nome,
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
    min(unidade_nome) as unidade_nome,
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


-- =========================================================
-- Indicador 3
-- Taxa de cumprimento de metas por entrega
-- Base de origem: planos_entregas_entregas
-- =========================================================
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
entregas_base as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        coalesce(u.nome, 'N.I.') as unidade_nome,
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
    unidade_nome,
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


-- =========================================================
-- Indicador 4
-- Indice de atingimento de metas
-- Base de origem: planos_entregas_entregas
-- =========================================================
with parametros as (
    select
        date('2025-01-01') as data_inicio,
        date('2025-12-31') as data_fim,
        0 as incluir_excluidos
),
calculo_por_entrega as (
    select
        coalesce(u.sigla, 'N.I.') as unidade_sigla,
        coalesce(u.nome, 'N.I.') as unidade_nome,
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
    min(unidade_nome) as unidade_nome,
    count(id_entrega) as total_entregas_planejadas,
    round(avg(proporcao_atingimento) * 100, 2) as score_atingimento_metas_perc
from calculo_por_entrega
where proporcao_atingimento is not null
group by unidade_sigla
order by unidade_sigla;


-- =========================================================
-- Indicador 5
-- Distribuicao das entregas entre os servidores
-- Base de origem: planos_trabalhos + planos_trabalhos_entregas
-- =========================================================
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
-- Indicador 6
-- Grau de responsabilidade pelas entregas
-- Base de origem: planos_trabalhos + planos_trabalhos_entregas
-- =========================================================
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
-- Indicador 7
-- Horas por entrega - planejadas
-- Base de origem: planos_trabalhos + planos_trabalhos_entregas
-- Requer: MySQL 8.0+ (WITH RECURSIVE)
-- =========================================================
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


-- =========================================================
-- Indicador 8
-- Proporcao de horas por entrega - planejadas
-- Base de origem: planos_trabalhos + planos_trabalhos_entregas
-- Requer: MySQL 8.0+ (WITH RECURSIVE)
-- =========================================================
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
