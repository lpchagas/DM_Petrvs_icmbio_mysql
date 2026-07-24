# I02 — Taxa de Cumprimento das Entregas por Unidade — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_02.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Mede a taxa de cumprimento das entregas por unidade — entregas com
`progresso_realizado >= progresso_esperado`, entre as entregas cujo Plano de
Entregas (PE) se **sobrepõe** ao período consultado.

## 2. Pré-requisitos

- IP da máquina liberado pelo Dataprev; driver JDBC instalado (ver CLAUDE.md seção 2).
- Notebook `consultas_denodo.ipynb` (raiz do projeto) aberto no VS Code.
- Célula 2 (conexão) já configurada localmente com usuário/senha do Denodo —
  **não copie credenciais para este arquivo**; ver CLAUDE.md seção 2
  (arquivo local, não versionado).

## 3. Instrumento e periodicidade

- Instrumento: **Plano de Entregas (PE)** → `build_periods_pe()`.
- Regra vigente: 2025 trimestral (T3–T4, H1/2025 excluído) | 2026+ quadrimestral (Q1–Q3).
  Base: 01/07/2025.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pe()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| Q1-2026 | quadrimestral | 2026-01-01 | 2026-04-30 | encerrado |
| Q2-2026 | quadrimestral | 2026-05-01 | 2026-08-31 | em_andamento |

## 4. Query SQL_I02

Exemplo com o primeiro período (T3-2025) já preenchido — troque as duas datas
de `parametros` a cada rodada, conforme a tabela da seção 3.

```sql
WITH parametros AS (
    SELECT
        CAST('2025-07-01' AS DATE) AS data_inicio,
        CAST('2025-09-30' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
universo_bruto AS (
    SELECT
        u.sigla     AS unidade_sigla,
        MIN(u.nome) AS unidade_nome,
        COUNT(*)    AS total_cadastradas
    FROM petrvs_icmbio_planos_entregas pe
    JOIN petrvs_icmbio_planos_entregas_entregas pee
        ON pee.plano_entrega_id = pe.id
    JOIN petrvs_icmbio_unidades u
        ON u.id = pe.unidade_id
    CROSS JOIN parametros p
    WHERE CAST(pe.data_inicio AS DATE) <= p.data_fim
      AND CAST(pe.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pe.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pee.deleted_at IS NULL)
    GROUP BY u.sigla
),
entregas_ciclo AS (
    SELECT
        u.sigla                              AS unidade_sigla,
        u.nome                               AS unidade_nome,
        pee.id                               AS id_entrega,
        pee.progresso_esperado               AS meta_planejada,
        COALESCE(pee.progresso_realizado, 0) AS meta_executada,
        CASE
            WHEN CAST(pee.data_fim AS DATE) BETWEEN p.data_inicio AND p.data_fim
            THEN 1 ELSE 0
        END                                  AS vence_no_periodo,
        CASE
            WHEN pe.status IN ('AVALIADO', 'CONCLUIDO') THEN 1 ELSE 0
        END                                  AS plano_avaliado
    FROM petrvs_icmbio_planos_entregas pe
    JOIN petrvs_icmbio_planos_entregas_entregas pee
        ON pee.plano_entrega_id = pe.id
    JOIN petrvs_icmbio_unidades u
        ON u.id = pe.unidade_id
    CROSS JOIN parametros p
    WHERE CAST(pe.data_inicio AS DATE) <= p.data_fim
      AND CAST(pe.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pe.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pee.deleted_at IS NULL)
      AND pee.progresso_esperado IS NOT NULL
      AND pee.progresso_esperado > 0
),
resumo AS (
    SELECT
        unidade_sigla,
        MIN(unidade_nome)                                                     AS unidade_nome,
        COUNT(*)                                                              AS total_no_ciclo,
        SUM(vence_no_periodo)                                                 AS total_vence_no_periodo,
        SUM(CASE WHEN meta_executada >= meta_planejada THEN 1 ELSE 0 END)     AS total_concluidas,
        ROUND(
            SUM(CASE WHEN meta_executada >= meta_planejada THEN 1 ELSE 0 END)
                * 100.0 / NULLIF(COUNT(*), 0),
            2
        )                                                                     AS taxa_cumprimento_perc,
        SUM(plano_avaliado)                                                   AS total_em_plano_avaliado,
        SUM(CASE WHEN plano_avaliado = 1 AND meta_executada >= meta_planejada
                 THEN 1 ELSE 0 END)                                           AS concluidas_em_plano_avaliado
    FROM entregas_ciclo
    GROUP BY unidade_sigla
)
SELECT
    r.unidade_sigla,
    r.unidade_nome,
    b.total_cadastradas,
    r.total_no_ciclo,
    r.total_vence_no_periodo,
    ROUND(r.total_vence_no_periodo * 100.0 / NULLIF(r.total_no_ciclo, 0), 1)
        AS proporcao_vence_no_periodo_perc,
    r.total_concluidas,
    r.taxa_cumprimento_perc,
    r.total_em_plano_avaliado,
    r.concluidas_em_plano_avaliado,
    CASE
        WHEN r.taxa_cumprimento_perc >= 90 THEN 'A — Alto desempenho'
        WHEN r.taxa_cumprimento_perc >= 70 THEN 'B — Bom desempenho'
        WHEN r.taxa_cumprimento_perc >= 50 THEN 'C — Desempenho intermediario'
        ELSE                                    'D — Baixo desempenho'
    END AS grupo_performance,
    CASE
        WHEN r.total_no_ciclo > r.total_em_plano_avaliado
        THEN 'atencao: ha entregas em planos nao avaliados'
        ELSE 'ciclo avaliado'
    END AS alerta_avaliacao
FROM resumo r
LEFT JOIN universo_bruto b ON b.unidade_sigla = r.unidade_sigla
ORDER BY r.taxa_cumprimento_perc DESC, r.unidade_sigla
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i02`.
4. Rodar `df_i02 = run_query(sql_i02)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3 (uma rodada por período). Use `pd.concat([...], ignore_index=True)`
   se quiser consolidar todos os períodos num único DataFrame, acrescentando
   manualmente as colunas de metadado (`ciclo_tipo`, `periodo`, `periodo_status`)
   a cada rodada.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_02.2_taxa_cumprimento_temporal_{stamp}.csv"
df_i02.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

O exemplo genérico do notebook (`sql_i02` na seção "3. Exemplos de indicadores")
usa `sep=";"` e salva em `Tabelas CSV\` — **não use esse padrão**; siga o
`sep="|"` + `utf-8-sig` + `artefatos_local/ocde/entregas/YYYY-MM/` acima,
conforme a seção 4 do CLAUDE.md.

## 7. Observações e pontos críticos

- Diferença metodológica **I02 vs I03**: I02 usa PEs que **se sobrepõem** ao
  período (`pe.data_inicio`/`pe.data_fim`); I03 usa entregas que **vencem** no
  período (`pee.data_fim BETWEEN`).
- Critério OCDE (`progresso_realizado >= progresso_esperado`) é o principal;
  o critério formal PETRVS (`pe.status IN ('AVALIADO','CONCLUIDO')`) aparece
  nas colunas `total_em_plano_avaliado`/`concluidas_em_plano_avaliado`.
- `pee.progresso_esperado IS NOT NULL AND > 0` é o gate de meta válida —
  entregas sem meta não entram no cálculo.
- Validação A3 (11.05.2026): fórmula confirmada.
- `ciclo_tipo` muda entre 2025 (trimestral) e 2026+ (quadrimestral) — não
  comparar taxas por período entre anos, usar totais anuais.

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_02.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.2.1-i02.md`
