"""IND_04.1_run.py — I04: Índice de Atingimento de Metas por Unidade.

Instrumento: Plano de Entregas (PE).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ quadrimestral (Q1–Q3). Base: 01/07/2025.

O I04 calcula o score médio de execução por unidade: média aritmética das
proporções de atingimento (realizado / planejado) de todas as entregas do
ciclo, expressas em percentual. Cada entrega tem peso igual, independente
do volume absoluto da meta. O score pode ultrapassar 100% quando há
superexecução — isso é legítimo e indica metas sistematicamente subestimadas.

Escopo idêntico ao I02: sobrepõe datas do PE (pe.data_inicio/pe.data_fim),
não o vencimento individual de cada entrega — o que garante que
total_no_ciclo seja comparável entre I02 e I04.

AVISO METODOLÓGICO: scores > 100% indicam superexecução, não necessariamente
desempenho excepcional. Verificar subestimação de metas no planejamento.

Validação A3 (17.05.2026): fórmula confirmada para COGEP (dump 208,33% vs
PETRVS 208,25% — diferença de 0,08 pp por precisão decimal).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib" / "__init__.py").exists())
sys.path.insert(0, str(ROOT))

from lib.csv_utils import indicator_csv_dir, write_pipe_csv
from lib.denodo_config import connect, get_config
from lib.monthly_runner import query_rows
from lib.periodos import build_periods_pe, period_metadata

SQL_I04 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
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
"""


def _to_float(s: str) -> float:
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _to_int(s: str) -> int:
    try:
        return int(float(s)) if s else 0
    except ValueError:
        return 0


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_04.2_score_atingimento_metas_{stamp}.csv"

    periods = build_periods_pe()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I04.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I04 {label} ({start} a {end})...")
            try:
                columns, rows = query_rows(conn, sql)
            except Exception as exc:
                print(f"  ERRO: {exc}")
                continue
            if all_cols is None:
                all_cols = meta_cols + columns
            duration = (end - start).days + 1
            for row in rows:
                all_rows.append([kind, label, str(start), str(end), status, duration] + row)
            print(f"  {len(rows)} unidades retornadas.")
    finally:
        conn.close()

    if not all_rows:
        print("Nenhum dado retornado. CSV nao gerado.")
        return

    write_pipe_csv(output, all_cols or [], all_rows)
    print(f"\nArquivo salvo: {output}")

    # ── Resumo por período ────────────────────────────────────────────────────
    cols = all_cols or []
    idx_per   = cols.index("periodo")
    idx_tipo  = cols.index("ciclo_tipo")
    idx_score = cols.index("score_atingimento_perc")
    idx_pst   = cols.index("periodo_status")
    idx_cad   = cols.index("total_cadastradas")
    idx_ciclo = cols.index("total_no_ciclo")

    print()
    print(
        f"{'Periodo':10s}  {'Tipo':14s}  {'Unidades':>8s}  "
        f"{'MediaScore%':>11s}  {'Acima100':>8s}  {'Status':12s}"
    )
    print("-" * 72)
    for label, kind, start, end, status in periods:
        p_rows = [r for r in all_rows if r[idx_per] == label]
        if not p_rows:
            continue
        scores = [_to_float(r[idx_score]) for r in p_rows]
        media = round(sum(scores) / len(scores), 1) if scores else 0.0
        n_acima = sum(1 for s in scores if s > 100)
        pst = p_rows[0][idx_pst]
        print(
            f"  {label:10s}  {kind:14s}  {len(p_rows):>8d}  "
            f"{media:>11.1f}  {n_acima:>8d}  {pst}"
        )
    print()

    # ── Aviso de qualidade de dados (> 10% sem meta válida) ──────────────────
    avisos = {}
    for label, kind, start, end, status in periods:
        p_rows = [r for r in all_rows if r[idx_per] == label]
        total_cad   = sum(_to_int(r[idx_cad])   for r in p_rows)
        total_ciclo = sum(_to_int(r[idx_ciclo]) for r in p_rows)
        sem = total_cad - total_ciclo
        if total_cad > 0 and sem / total_cad > 0.10:
            avisos[label] = (sem, total_cad, status)
    if avisos:
        print("AVISO DE QUALIDADE — periodos com > 10% de entregas sem meta valida:")
        for lbl, (sem, total, pst) in avisos.items():
            pct = round(sem * 100.0 / total, 1)
            print(f"  {lbl}: {sem} sem meta de {total} cadastradas ({pct}%) [{pst}]")
        print("  -> Entregas sem progresso_esperado > 0 nao entram no calculo do I04.")
        print()

    print("AVISO: ciclo_tipo='trimestral' (2025) e 'quadrimestral' (2026+).")
    print("Nao compare scores entre anos por periodo — use totais anuais.")
    print("Scores acima de 100% indicam superexecucao — verificar subestimacao de metas.")
    print("Concluido.")


if __name__ == "__main__":
    main()
