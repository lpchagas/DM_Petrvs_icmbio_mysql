"""IND_03.1_run.py — I03: Taxa de Cumprimento de Metas por Entrega.

Instrumento: Plano de Entregas (PE).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ quadrimestral (Q1–Q3). Base: 01/07/2025.

Diferença metodológica I02 vs I03:
  I02: PEs que se SOBREPÕEM ao período (pe.data_inicio/pe.data_fim)
  I03: entregas que VENCEM no período (pee.data_fim BETWEEN ini E fim)

Essa distinção garante que o I03 foca nas entregas cujo prazo individual
cai dentro do recorte — permitindo análise por vencimento, não por ciclo.

Abordagem dupla de cálculo:
  Principal (ciclo): taxa = meta_executada / meta_planejada * 100
  Alternativa (meta integral): extrai valores do campo JSON pee.meta e
  pee.realizado para uma segunda perspectiva independente.

Correção de escala: metas entre 0–1 são convertidas para 0–100 pelo
CASE WHEN no SQL (anomalia_escala='S'); a abordagem integral usa JSON.

Validação A3 (17.05.2026): fórmula confirmada. Dupla abordagem aprovada.

NOTA: A versão anterior (thin wrapper via run_sql_indicator) NÃO executava
parse_meta_integral — as colunas taxa_meta_integral_perc, status_meta_integral
e tipo_meta estavam ausentes do CSV. Esta versão reintroduz esse processamento.

Correção de dado inconsistente (19.06.2026): valores negativos de progresso_realizado
geram taxa_atingimento_perc < 0, que é semanticamente diferente de "Nao executada".
O CASE no SQL agora classifica esses casos como 'Dado inconsistente' para facilitar
auditoria de qualidade de dados no PETRVS.
"""
from __future__ import annotations

import json
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

SQL_I03 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
entregas_base AS (
    SELECT
        u.sigla AS unidade_sigla,
        u.nome  AS unidade_nome,
        pee.id  AS id_entrega,
        COALESCE(
            NULLIF(TRIM(pee.descricao), ''),
            NULLIF(TRIM(pee.descricao_entrega), ''),
            'N.I.'
        ) AS nome_entrega,
        COALESCE(NULLIF(TRIM(pee.descricao_entrega), ''), 'N.I.') AS descricao_entrega,
        pee.progresso_esperado AS progresso_esperado_bruto,
        CASE
            WHEN pee.progresso_esperado > 0 AND pee.progresso_esperado <= 1
            THEN pee.progresso_esperado * 100
            ELSE pee.progresso_esperado
        END AS meta_planejada,
        COALESCE(pee.progresso_realizado, 0) AS meta_executada,
        pee.meta      AS meta_json,
        pee.realizado AS realizado_json
    FROM petrvs_icmbio_planos_entregas pe
    JOIN petrvs_icmbio_planos_entregas_entregas pee
        ON pee.plano_entrega_id = pe.id
    JOIN petrvs_icmbio_unidades u
        ON u.id = pe.unidade_id
    CROSS JOIN parametros p
    WHERE CAST(pee.data_fim AS DATE) BETWEEN p.data_inicio AND p.data_fim
      AND (p.incluir_excluidos = 1 OR pe.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pee.deleted_at IS NULL)
      AND pee.progresso_esperado IS NOT NULL
      AND pee.progresso_esperado > 0
),
entregas_com_taxa AS (
    SELECT
        unidade_sigla,
        unidade_nome,
        id_entrega,
        nome_entrega,
        descricao_entrega,
        progresso_esperado_bruto,
        CASE
            WHEN progresso_esperado_bruto > 0 AND progresso_esperado_bruto <= 1
            THEN 'S'
            ELSE 'N'
        END AS anomalia_escala,
        meta_planejada,
        meta_executada,
        ROUND(meta_executada / NULLIF(meta_planejada, 0) * 100, 2) AS taxa_atingimento_perc,
        meta_json,
        realizado_json
    FROM entregas_base
)
SELECT
    unidade_sigla,
    unidade_nome,
    id_entrega,
    nome_entrega,
    descricao_entrega,
    progresso_esperado_bruto,
    anomalia_escala,
    meta_planejada,
    meta_executada,
    taxa_atingimento_perc,
    CASE
        WHEN taxa_atingimento_perc <    0 THEN 'Dado inconsistente'
        WHEN taxa_atingimento_perc >  100 THEN 'Superexecutada'
        WHEN taxa_atingimento_perc =  100 THEN 'Concluida'
        WHEN taxa_atingimento_perc >= 70  THEN 'Parcialmente cumprida'
        WHEN taxa_atingimento_perc >    0 THEN 'Em andamento'
        ELSE                                   'Nao executada'
    END AS status_entrega,
    meta_json,
    realizado_json
FROM entregas_com_taxa
ORDER BY unidade_sigla, taxa_atingimento_perc DESC
"""

EXTRA_COLS = ["taxa_meta_integral_perc", "status_meta_integral", "tipo_meta"]


def classify_status(taxa: float) -> str:
    if taxa > 100:
        return "Superexecutada"
    if taxa == 100:
        return "Concluida"
    if taxa >= 70:
        return "Parcialmente cumprida"
    if taxa > 0:
        return "Em andamento"
    return "Nao executada"


def parse_meta_integral(
    meta_str: str, realizado_str: str
) -> tuple[str, str, str]:
    """Calcula taxa pela meta integral a partir dos campos JSON.

    Retorna (taxa_perc_str, status_str, tipo_str).
    Retorna ("", "N.D.", "N.D.") quando JSON ausente, inválido ou sem valor.
    """
    try:
        if not meta_str or meta_str.strip().lower() in ("null", ""):
            return "", "N.D.", "N.D."
        if not realizado_str or realizado_str.strip().lower() in ("null", ""):
            return "", "N.D.", "N.D."
        meta = json.loads(meta_str)
        real = json.loads(realizado_str)
        if "quantitativo" in meta:
            meta_val = float(str(meta["quantitativo"]))
            real_val = float(str(real.get("quantitativo", 0)))
            tipo = "quantitativo"
        elif "porcentagem" in meta:
            meta_val = float(str(meta["porcentagem"]))
            real_val = float(str(real.get("porcentagem", 0)))
            tipo = "porcentagem"
        else:
            return "", "N.D.", "N.D."
        if meta_val <= 0:
            return "", "N.D.", tipo
        taxa = round(real_val / meta_val * 100, 2)
        return str(taxa), classify_status(taxa), tipo
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return "", "N.D.", "N.D."


def _to_float(s: str) -> float:
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_03.2_taxa_cumprimento_entrega_{stamp}.csv"

    periods = build_periods_pe()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    # Índices dos campos JSON e anomalia — definidos na primeira execução bem-sucedida
    idx_meta: int | None = None
    idx_real: int | None = None
    idx_anom: int | None = None
    idx_taxa_sql: int | None = None
    idx_status_sql: int | None = None

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I03.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I03 {label} ({start} a {end})...")
            try:
                columns, rows = query_rows(conn, sql)
            except Exception as exc:
                print(f"  ERRO: {exc}")
                continue

            if all_cols is None:
                all_cols = meta_cols + columns + EXTRA_COLS
                idx_meta     = columns.index("meta_json")
                idx_real     = columns.index("realizado_json")
                idx_anom     = columns.index("anomalia_escala")
                idx_taxa_sql = columns.index("taxa_atingimento_perc")
                idx_status_sql = columns.index("status_entrega")

            duration = (end - start).days + 1
            n_anom = 0
            n_integ = 0
            for row in rows:
                taxa_int, status_int, tipo_meta = parse_meta_integral(
                    row[idx_meta] if idx_meta is not None else "",
                    row[idx_real] if idx_real is not None else "",
                )
                if idx_anom is not None and row[idx_anom] == "S":
                    n_anom += 1
                if taxa_int:
                    n_integ += 1
                all_rows.append(
                    [kind, label, str(start), str(end), status, duration]
                    + row
                    + [taxa_int, status_int, tipo_meta]
                )
            print(
                f"  {len(rows):>5} entregas  "
                f"| anomalia_escala: {n_anom}  "
                f"| meta_integral: {n_integ}"
            )
    finally:
        conn.close()

    if not all_rows:
        print("Nenhum dado retornado. CSV nao gerado.")
        return

    write_pipe_csv(output, all_cols or [], all_rows)
    print(f"\nArquivo salvo: {output}")

    # ── Resumo por período ────────────────────────────────────────────────────
    cols = all_cols or []
    idx_per    = cols.index("periodo")
    idx_pst    = cols.index("periodo_status")
    idx_taxa_f = cols.index("taxa_atingimento_perc")
    idx_sts_f  = cols.index("status_entrega")

    print()
    print(
        f"{'Periodo':10s}  {'Tipo':14s}  {'Entregas':>8s}  "
        f"{'Media%':>7s}  {'Conc%':>6s}  {'Parc%':>6s}  {'Nao%':>5s}  "
        f"{'Status':12s}"
    )
    print("-" * 80)
    for label, kind, start, end, status in periods:
        p_rows = [r for r in all_rows if r[idx_per] == label]
        if not p_rows:
            continue
        taxas = [_to_float(r[idx_taxa_f]) for r in p_rows if r[idx_taxa_f]]
        media = round(sum(taxas) / len(taxas), 1) if taxas else 0.0
        total = len(p_rows)
        n_conc = sum(
            1 for r in p_rows if r[idx_sts_f] in ("Concluida", "Superexecutada")
        )
        n_parc = sum(1 for r in p_rows if r[idx_sts_f] == "Parcialmente cumprida")
        n_nao  = sum(1 for r in p_rows if r[idx_sts_f] == "Nao executada")
        pst = p_rows[0][idx_pst]
        print(
            f"  {label:10s}  {kind:14s}  {total:>8d}  "
            f"{media:>7.1f}  {n_conc / total * 100:>6.1f}  "
            f"{n_parc / total * 100:>6.1f}  {n_nao / total * 100:>5.1f}  "
            f"{pst}"
        )
    print()

    print(f"{len(all_rows)} linhas retornadas.")
    print(f"Total: {len(all_rows)} entregas | {len(periods)} periodos")
    print("AVISO: ciclo_tipo='trimestral' (2025) e 'quadrimestral' (2026+).")
    print("Nao compare taxas entre anos por periodo — use totais anuais.")
    print("Scores > 100% sao legítimos (superexecucao) — boxplots aplicam cap em 300%.")
    print("Concluido.")


if __name__ == "__main__":
    main()
