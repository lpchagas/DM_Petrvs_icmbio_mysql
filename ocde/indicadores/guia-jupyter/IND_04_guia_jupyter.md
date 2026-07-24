# I04 — Score Médio de Atingimento de Metas por Unidade — Guia de Execução via Jupyter Notebook

> Guia derivado de `ocde/indicadores/IND_04.1_run.py` (fonte canônica — Opção A/C).
> Documenta a Opção B (seção 8 do CLAUDE.md): execução manual via
> `consultas_denodo.ipynb` (não o `consultas_denodo_template.ipynb`).

## 1. Objetivo

Calcula o score médio de execução por unidade: média aritmética das proporções
de atingimento (`realizado / planejado`) de todas as entregas do ciclo,
expressas em percentual. O score pode ultrapassar 100% em caso de
superexecução.

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
- Escopo idêntico ao I02: sobrepõe as datas do PE, não o vencimento individual.

Períodos vigentes em 24.07.2026 (recalcular com `build_periods_pe()` se datas futuras):

| Período | Tipo | Início | Fim | Status |
|---|---|---|---|---|
| T3-2025 | trimestral | 2025-07-01 | 2025-09-30 | encerrado |
| T4-2025 | trimestral | 2025-10-01 | 2025-12-31 | encerrado |
| Q1-2026 | quadrimestral | 2026-01-01 | 2026-04-30 | encerrado |
| Q2-2026 | quadrimestral | 2026-05-01 | 2026-08-31 | em_andamento |

## 4. Query SQL_I04

Exemplo com o primeiro período (T3-2025) preenchido — troque as datas de
`parametros` a cada rodada.

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
        u.sigla                                                    AS unidade_sigla,
        u.nome                                                     AS unidade_nome,
        pee.id                                                     AS id_entrega,
        ABS(COALESCE(pee.progresso_realizado, 0))
            / NULLIF(ABS(pee.progresso_esperado), 0)              AS proporcao_atingimento,
        CASE
            WHEN pe.status IN ('AVALIADO', 'CONCLUIDO') THEN 1 ELSE 0
        END                                                        AS plano_avaliado
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
        MIN(unidade_nome)                         AS unidade_nome,
        COUNT(id_entrega)                         AS total_no_ciclo,
        ROUND(AVG(proporcao_atingimento) * 100.0, 2) AS score_atingimento_perc,
        SUM(plano_avaliado)                       AS total_em_plano_avaliado
    FROM entregas_ciclo
    GROUP BY unidade_sigla
)
SELECT
    r.unidade_sigla,
    r.unidade_nome,
    b.total_cadastradas,
    r.total_no_ciclo,
    r.score_atingimento_perc,
    r.total_em_plano_avaliado,
    CASE
        WHEN r.score_atingimento_perc >= 90  THEN 'A — Alto desempenho'
        WHEN r.score_atingimento_perc >= 70  THEN 'B — Bom desempenho'
        WHEN r.score_atingimento_perc >= 50  THEN 'C — Desempenho intermediario'
        ELSE                                      'D — Baixo desempenho'
    END AS grupo_performance,
    CASE
        WHEN r.total_no_ciclo > r.total_em_plano_avaliado
        THEN 'atencao: ha entregas em planos nao avaliados'
        ELSE 'ciclo avaliado'
    END AS alerta_avaliacao
FROM resumo r
LEFT JOIN universo_bruto b ON b.unidade_sigla = r.unidade_sigla
ORDER BY r.score_atingimento_perc DESC, r.unidade_sigla
```

## 5. Passo a passo no notebook

1. Abrir `consultas_denodo.ipynb`.
2. Rodar a célula 1 (JVM) e a célula 2 (`run_query`) — seção "1. Configuração da conexão".
3. Colar a query da seção 4 numa nova célula, atribuir a `sql_i04`.
4. Rodar `df_i04 = run_query(sql_i04)`.
5. Repetir os passos 3–4 trocando `data_inicio`/`data_fim` para cada período da
   tabela da seção 3.

## 6. Exportação em CSV (padrão pipe-delimited)

```python
from datetime import datetime

stamp = datetime.now().strftime("%Y%m%d_%H%M")
output_path = f"artefatos_local/ocde/entregas/2026-07/IND_04.2_score_atingimento_metas_{stamp}.csv"
df_i04.to_csv(output_path, index=False, sep="|", encoding="utf-8-sig")
print(f"Exportado: {output_path}")
```

## 7. Observações e pontos críticos

- Scores acima de 100% indicam **superexecução**, não necessariamente
  desempenho excepcional — verificar subestimação de metas no planejamento.
- Gate de meta válida: `pee.progresso_esperado IS NOT NULL AND > 0`.
- Validação A3 (17.05.2026): fórmula confirmada para COGEP (dump 208,33% vs.
  PETRVS 208,25% — diferença de 0,08 p.p. por precisão decimal).
- `ciclo_tipo` muda entre 2025 (trimestral) e 2026+ (quadrimestral) — não
  comparar scores por período entre anos, usar totais anuais.
- Pendências QD-02 e QD-03 do diagnóstico A4 ainda em aberto (ver CLAUDE.md seção 11).

## 8. Ver também

- Script canônico: `ocde/indicadores/IND_04.1_run.py` (Opção A/C — fonte de verdade)
- Ficha técnica: `docs/ocde/06.2.3-i04.md`
