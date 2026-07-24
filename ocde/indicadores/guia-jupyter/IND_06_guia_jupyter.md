# I06 — Grau de Responsabilidade pelas Entregas — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_06.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula quantos servidores estão vinculados a cada entrega do PE, classificando-as
por tamanho do grupo responsável — mede se as entregas têm cobertura distribuída
ou pontos únicos de falha.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **Plano de Trabalho (PT)** → `build_periods_pt()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ mensal (M01–M12).
  Base: 01/07/2025.
- A unidade é derivada de `pt.unidade_id` (unidade do **executor**), não de
  `pe.unidade_id` (planejador) — o I06 mede responsabilidade de quem executa.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pt()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| M01-2026 | mensal | 2026-01-01 | 2026-01-31 | encerrado |
| M02-2026 | mensal | 2026-02-01 | 2026-02-28 | encerrado |
| M03-2026 | mensal | 2026-03-01 | 2026-03-31 | encerrado |
| M04-2026 | mensal | 2026-04-01 | 2026-04-30 | encerrado |
| M05-2026 | mensal | 2026-05-01 | 2026-05-31 | encerrado |
| M06-2026 | mensal | 2026-06-01 | 2026-06-30 | encerrado |
| M07-2026 | mensal | 2026-07-01 | 2026-07-31 | em_andamento |

## 4. Query SQL_I06

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
vinculos AS (
    SELECT DISTINCT
        COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
        COALESCE(un.nome,  'N.I.') AS unidade_nome,
        pte.plano_entrega_entrega_id AS id_entrega,
        pt.usuario_id                AS id_servidor
    FROM petrvs_icmbio_planos_trabalhos pt
    JOIN petrvs_icmbio_planos_trabalhos_entregas pte
        ON pte.plano_trabalho_id = pt.id
    LEFT JOIN petrvs_icmbio_unidades un
        ON un.id = pt.unidade_id
    CROSS JOIN parametros p
    WHERE CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pte.deleted_at IS NULL)
      AND pt.usuario_id IS NOT NULL
      AND pte.plano_entrega_entrega_id IS NOT NULL
),
responsaveis_por_entrega AS (
    SELECT
        unidade_sigla,
        MIN(unidade_nome)           AS unidade_nome,
        id_entrega,
        COUNT(DISTINCT id_servidor) AS qtd_responsaveis
    FROM vinculos
    GROUP BY unidade_sigla, id_entrega
),
com_classificacao AS (
    SELECT
        unidade_sigla,
        unidade_nome,
        id_entrega,
        qtd_responsaveis,
        CASE
            WHEN qtd_responsaveis = 1 THEN '1 servidor'
            WHEN qtd_responsaveis = 2 THEN '2 servidores'
            WHEN qtd_responsaveis = 3 THEN '3 servidores'
            ELSE                           '4+ servidores'
        END AS tamanho_grupo_responsavel
    FROM responsaveis_por_entrega
),
totais_unidade AS (
    SELECT
        unidade_sigla,
        COUNT(id_entrega) AS total_entregas_unidade
    FROM com_classificacao
    GROUP BY unidade_sigla
)
SELECT
    cc.unidade_sigla,
    MIN(cc.unidade_nome)                                                 AS unidade_nome,
    cc.tamanho_grupo_responsavel,
    COUNT(cc.id_entrega)                                                 AS total_entregas_na_categoria,
    tu.total_entregas_unidade,
    ROUND(COUNT(cc.id_entrega) * 100.0 / NULLIF(tu.total_entregas_unidade, 0), 1)
                                                                         AS pct_categoria
FROM com_classificacao cc
JOIN totais_unidade tu ON tu.unidade_sigla = cc.unidade_sigla
GROUP BY cc.unidade_sigla, cc.tamanho_grupo_responsavel, tu.total_entregas_unidade
ORDER BY cc.unidade_sigla, cc.tamanho_grupo_responsavel
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i06`.
4. Rodar `df_i06 = run_query(sql_i06)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_06.2_grau_responsabilidade_entregas_{stamp}.csv"
df_i06.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- Nota metodológica: unidade = unidade do **servidor** (`pt.unidade_id`), não
  do planejador (`pe.unidade_id`) — `total_entregas_unidade` do I06 pode
  diferir do total de PEs por unidade no I02.
- Achado de produção (jun/2026): 64,8% das entregas com 1 único responsável
  (163 unidades > 50% de concentração) — sinal de ponto único de falha.
- Ciclos mistos (2025 trimestral vs. 2026 quadrimestral) afetam
  `total_entregas_unidade` — usar `pct_categoria` para comparar entre períodos.
- Pendência: CGOV decidir a variante I06-PE (ver CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_06.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.3.2-i06.md`
