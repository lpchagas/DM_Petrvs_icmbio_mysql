"""IND_12.1_run.py — I12: Coerência entre Avaliação do PT e do PE.

Instrumento: misto PT + PE — ciclo alinhado ao Plano de Entregas (PE).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ quadrimestral (Q1–Q3). Base: 01/07/2025.

Correção de escala (19.06.2026): o SQL original usava JSON_UNQUOTE(tan.nota) com
CASE WHEN textual — que não funciona no Denodo VQL via JDBC. Isso fazia as médias
de PT e PE retornarem NULL, e todas as unidades classificadas em "Alta divergencia"
(o ELSE do CASE WHEN quando diferenca_absoluta IS NULL).

Correção: usar (6 - tan.sequencia) em ambos os blocos (PT e PE):
  sequencia=1 → Excepcional     → score 5
  sequencia=2 → Alto desempenho → score 4
  sequencia=3 → Adequado        → score 3
  sequencia=4 → Inadequado      → score 2
  sequencia=5 → Não executado   → score 1

Correção de sinal (12.06.2026): diferenca_direcional = media_nota_pt - media_nota_pe
é positivo quando PT > PE — confirmado em validação COCAGE.

Achados de validação (12.06.2026):
  - 96–100% das unidades classificadas como "Coerente" por período.
  - Diferença média 0,24–0,34 pts (escala 1–5).
  - Padrão PE > PT (38%) > PT > PE (27%): avaliador coletivo tende a dar nota
    levemente superior à média dos PTs (oposto de leniência avaliativa).
  - 77 unidades com ciclo incompleto em T1/T2-2025 (PT sem PE correspondente)
    excluídas do JOIN — fora do período base (H1/2025 não analisado).

Nota: o JOIN interno entre PT e PE exclui unidades sem as duas perspectivas.
Para listar essas unidades, executar o diagnóstico A4 (IND_12.4).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib" / "__init__.py").exists())
sys.path.insert(0, str(ROOT))

from lib.csv_utils import indicator_csv_dir, write_pipe_csv
from lib.denodo_config import connect, get_config
from lib.monthly_runner import query_rows
from lib.periodos import build_periods_pe, period_metadata

SQL_I12 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
avaliacoes_pt AS (
    SELECT
        pt.unidade_id,
        (6 - tan.sequencia) AS valor_nota
    FROM petrvs_icmbio_avaliacoes av
    JOIN petrvs_icmbio_planos_trabalhos_consolidacoes ptc
        ON ptc.id = av.plano_trabalho_consolidacao_id
    JOIN petrvs_icmbio_planos_trabalhos pt
        ON pt.id = ptc.plano_trabalho_id
    JOIN petrvs_icmbio_tipos_avaliacoes_notas tan
        ON tan.id = av.tipo_avaliacao_nota_id
    CROSS JOIN parametros p
    WHERE av.plano_trabalho_consolidacao_id IS NOT NULL
      AND (p.incluir_excluidos = 1 OR av.deleted_at IS NULL)
      AND CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at IS NULL)
),
avaliacoes_pe AS (
    SELECT
        pe.unidade_id,
        (6 - tan.sequencia) AS valor_nota
    FROM petrvs_icmbio_avaliacoes av
    JOIN petrvs_icmbio_planos_entregas pe
        ON pe.id = av.plano_entrega_id
    JOIN petrvs_icmbio_tipos_avaliacoes_notas tan
        ON tan.id = av.tipo_avaliacao_nota_id
    CROSS JOIN parametros p
    WHERE av.plano_entrega_id IS NOT NULL
      AND (p.incluir_excluidos = 1 OR av.deleted_at IS NULL)
      AND CAST(pe.data_inicio AS DATE) <= p.data_fim
      AND CAST(pe.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pe.deleted_at IS NULL)
),
media_pt_por_unidade AS (
    SELECT
        unidade_id,
        COUNT(*)                           AS total_avaliacoes_pt,
        ROUND(AVG(valor_nota * 1.0), 2)    AS media_nota_pt
    FROM avaliacoes_pt
    GROUP BY unidade_id
),
media_pe_por_unidade AS (
    SELECT
        unidade_id,
        COUNT(*)                           AS total_avaliacoes_pe,
        ROUND(AVG(valor_nota * 1.0), 2)    AS media_nota_pe
    FROM avaliacoes_pe
    GROUP BY unidade_id
),
coerencia AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                                     AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                                     AS unidade_nome,
        mpt.total_avaliacoes_pt,
        mpt.media_nota_pt,
        mpe.total_avaliacoes_pe,
        mpe.media_nota_pe,
        ROUND(ABS(mpt.media_nota_pt - mpe.media_nota_pe), 2)           AS diferenca_absoluta,
        ROUND(mpt.media_nota_pt - mpe.media_nota_pe, 2)                AS diferenca_direcional
    FROM media_pt_por_unidade mpt
    JOIN media_pe_por_unidade mpe ON mpe.unidade_id = mpt.unidade_id
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = mpt.unidade_id
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    media_nota_pt,
    total_avaliacoes_pe,
    media_nota_pe,
    diferenca_absoluta,
    diferenca_direcional,
    CASE
        WHEN diferenca_absoluta <= 1.0 THEN 'Coerente'
        WHEN diferenca_absoluta <= 2.0 THEN 'Divergencia moderada'
        ELSE 'Alta divergencia'
    END AS classificacao_coerencia,
    CASE
        WHEN diferenca_direcional > 0 THEN 'PT > PE'
        WHEN diferenca_direcional < 0 THEN 'PE > PT'
        ELSE 'Sem diferenca'
    END AS direcao_divergencia
FROM coerencia
ORDER BY diferenca_absoluta DESC, unidade_sigla
"""


def _to_float(value: object) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_12.2_coerencia_pt_pe_{stamp}.csv"

    periods = build_periods_pe()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I12.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I12 {label} ({start} a {end})...")
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
            print(f"  {len(rows)} linhas retornadas.")
    finally:
        conn.close()

    if not all_rows:
        print("Nenhum dado retornado. CSV nao gerado.")
        return

    write_pipe_csv(output, all_cols or [], all_rows)
    print(f"Arquivo salvo: {output}")

    # Colunas apos meta_cols (6):
    # sigla(0) nome(1) total_pt(2) media_pt(3) total_pe(4) media_pe(5)
    # dif_abs(6) dif_dir(7) classif(8) direcao(9)
    n = len(meta_cols)
    offset_dif_abs = n + 6   # diferenca_absoluta
    offset_classif = n + 8   # classificacao_coerencia

    encerrados = [r for r in all_rows if r[4] == "encerrado"]

    # Unidades com Alta divergencia (dif_abs > 2.0) — sinal de disfuncao avaliativa
    alta_div = [r for r in encerrados if _to_float(r[offset_dif_abs]) > 2.0]
    if alta_div:
        unids = set(r[n] for r in alta_div)
        print(f"  AVISO: {len(unids)} unidade(s) com 'Alta divergencia' (dif_abs > 2.0) em periodos encerrados"
              f" — revisar processo avaliativo.")

    # Unidades com Divergencia moderada
    div_mod = [r for r in encerrados if r[offset_classif] == "Divergencia moderada"]
    if div_mod:
        unids = set(r[n] for r in div_mod)
        print(f"  NOTA: {len(unids)} unidade(s) com 'Divergencia moderada' (1.0 < dif_abs <= 2.0) em periodos encerrados.")

    # Nota sobre exclusao do JOIN interno (unidades sem PT ou sem PE)
    print("  NOTA: unidades sem avaliacao de PE no periodo sao excluidas do resultado (JOIN interno PT x PE).")
    print("        Para listar essas unidades, executar o diagnostico A4 (IND_12.4).")

    em_andamento = sum(1 for r in all_rows if r[4] == "em_andamento")
    if em_andamento:
        print(f"  NOTA: {em_andamento} linha(s) em periodo em_andamento — valores de coerencia preliminares.")


if __name__ == "__main__":
    main()
