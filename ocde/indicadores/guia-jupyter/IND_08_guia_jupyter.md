# I08 — Proporção de Horas por Entrega (%) — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_08.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula qual percentual da capacidade total planejada de cada unidade foi
alocado a cada entrega — normaliza o valor absoluto do I07 pelo total de horas
disponíveis da unidade. Responde: "qual o peso relativo de cada entrega no
esforço total planejado da unidade?"

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **misto PT + PE**, ciclo alinhado ao Plano de Entregas (PE) →
  `build_periods_pe()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ quadrimestral (Q1–Q3).
  Base: 01/07/2025.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pe()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| Q1-2026 | quadrimestral | 2026-01-01 | 2026-04-30 | encerrado |
| Q2-2026 | quadrimestral | 2026-05-01 | 2026-08-31 | em_andamento |

## 4. Query SQL_I08

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
planos_horas AS (
    SELECT
        pt.id        AS plano_trabalho_id,
        pt.unidade_id,
        CASE pt.forma_contagem_carga_horaria
            WHEN 'DIAS' THEN pt.carga_horaria * 8.0
            ELSE             pt.carga_horaria
        END
        * (
            (CASE WHEN CAST(pt.data_fim   AS DATE) < p.data_fim
                  THEN CAST(pt.data_fim   AS DATE)
                  ELSE p.data_fim END)
            - (CASE WHEN CAST(pt.data_inicio AS DATE) > p.data_inicio
                    THEN CAST(pt.data_inicio AS DATE)
                    ELSE p.data_inicio END)
            + 1
          )
        / NULLIF(
              (CAST(pt.data_fim AS DATE) - CAST(pt.data_inicio AS DATE)) + 1,
              0
          )
        AS horas_proporcionais
    FROM petrvs_icmbio_planos_trabalhos pt
    CROSS JOIN parametros p
    WHERE CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at IS NULL)
      AND pt.carga_horaria IS NOT NULL
      AND pt.carga_horaria > 0
),
vinculos_ativos AS (
    SELECT
        pte.plano_trabalho_id,
        pte.plano_entrega_entrega_id    AS id_entrega,
        COALESCE(pte.forca_trabalho, 0) AS forca_trabalho
    FROM petrvs_icmbio_planos_trabalhos_entregas pte
    WHERE pte.plano_entrega_entrega_id IS NOT NULL
      AND pte.deleted_at IS NULL
),
capacidade_unidade AS (
    SELECT
        ph.unidade_id,
        SUM(ph.horas_proporcionais) AS total_horas_disponiveis_unidade
    FROM planos_horas ph
    GROUP BY ph.unidade_id
),
linhas AS (
    SELECT
        COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
        COALESCE(un.nome,  'N.I.') AS unidade_nome,
        va.id_entrega,
        COALESCE(
            NULLIF(TRIM(COALESCE(pee.descricao,         '')), ''),
            NULLIF(TRIM(COALESCE(pee.descricao_entrega, '')), ''),
            'N.I.'
        )                          AS nome_entrega,
        ph.horas_proporcionais * (va.forca_trabalho / 100.0) AS horas_servidor,
        cu.total_horas_disponiveis_unidade
    FROM vinculos_ativos va
    JOIN planos_horas ph
        ON ph.plano_trabalho_id = va.plano_trabalho_id
    LEFT JOIN petrvs_icmbio_planos_entregas_entregas pee
        ON pee.id = va.id_entrega
       AND pee.deleted_at IS NULL
    LEFT JOIN petrvs_icmbio_planos_entregas pe
        ON pe.id = pee.plano_entrega_id
       AND pe.deleted_at IS NULL
    LEFT JOIN petrvs_icmbio_unidades un
        ON un.id = COALESCE(pe.unidade_id, ph.unidade_id)
    LEFT JOIN capacidade_unidade cu
        ON cu.unidade_id = COALESCE(pe.unidade_id, ph.unidade_id)
    CROSS JOIN parametros p
    WHERE pe.id IS NOT NULL
      AND CAST(pe.data_inicio AS DATE) <= p.data_fim
      AND CAST(pe.data_fim   AS DATE) >= p.data_inicio
)
SELECT
    unidade_sigla,
    unidade_nome,
    id_entrega,
    nome_entrega,
    ROUND(SUM(horas_servidor), 2)                                AS horas_planejadas_entrega,
    ROUND(MAX(total_horas_disponiveis_unidade), 2)               AS total_horas_disponiveis_unidade,
    ROUND(
        SUM(horas_servidor)
        / NULLIF(MAX(total_horas_disponiveis_unidade), 0) * 100,
        2
    )                                                            AS proporcao_horas_perc
FROM linhas
GROUP BY
    unidade_sigla, unidade_nome, id_entrega, nome_entrega
ORDER BY unidade_sigla, proporcao_horas_perc DESC
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i08`.
4. Rodar `df_i08 = run_query(sql_i08)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_08.2_proporcao_horas_entrega_{stamp}.csv"
df_i08.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- Fórmula: `proporcao_horas_perc = horas_planejadas_entrega /
  total_horas_disponiveis_unidade × 100`.
- Mesma aritmética proporcional do I07 (sem `WITH RECURSIVE`), com o bloco
  extra `capacidade_unidade` (denominador = capacidade total declarada).
- Correções alinhadas ao I07 (14.06.2026): unidade =
  `COALESCE(pe.unidade_id, ph.unidade_id)`; filtro temporal do PE no CTE
  `linhas` para eliminar duplicatas entre períodos.
- `proporcao_horas_perc > 100%` indica `forca_trabalho` inconsistente no
  PETRVS — dado inválido, não erro de cálculo (achado de produção: 19
  entregas nesse estado).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_08.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.3.4-i08.md`
