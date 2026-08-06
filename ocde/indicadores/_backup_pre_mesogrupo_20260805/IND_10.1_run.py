"""IND_10.1_run.py — I10: Percentual de Avaliações Inadequadas por Unidade.

Instrumento: Plano de Trabalho (PT).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ mensal (M01–M12). Base: 01/07/2025.

Correção de escala (12.06.2026): o script original usava sequencia=2 para identificar
"Inadequado", mas sequencia=2 é "Alto desempenho" no banco ICMBio. Resultado incorreto:
82–86% das unidades classificadas em "Atencao critica" em todos os períodos.

Mapeamento correto da escala ICMBio (confirmado 12.06.2026):
  sequencia=1 → Excepcional
  sequencia=2 → Alto desempenho
  sequencia=3 → Adequado
  sequencia=4 → Inadequado     ← critério correto para I10
  sequencia=5 → Não executado

Resultado após correção: 98,9% das unidades em "Baixa prevalencia".
Alerta recorrente confirmado: PARNAEMAS (T1–T3/2025).

Nota: o SQL não usa JSON_UNQUOTE(tan.nota) — função que não funciona no Denodo VQL
via JDBC. A identificação de "Inadequado" é feita diretamente via tan.sequencia = 4.
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
from lib.periodos import build_periods_pt, period_metadata

SQL_I10 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
avaliacoes_pt AS (
    SELECT
        av.id          AS id_avaliacao,
        pt.unidade_id,
        tan.sequencia  AS sequencia_nota
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
proporcao_por_unidade AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                                   AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                                   AS unidade_nome,
        COUNT(avpt.id_avaliacao)                                     AS total_avaliacoes_pt,
        SUM(CASE WHEN avpt.sequencia_nota = 4 THEN 1 ELSE 0 END)    AS qtd_inadequado,
        ROUND(
            SUM(CASE WHEN avpt.sequencia_nota = 4 THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(avpt.id_avaliacao), 0),
            2
        )                                                            AS perc_inadequado
    FROM avaliacoes_pt avpt
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = avpt.unidade_id
    GROUP BY COALESCE(un.sigla, 'N.I.'), COALESCE(un.nome, 'N.I.')
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    qtd_inadequado,
    perc_inadequado,
    CASE
        WHEN perc_inadequado >= 30 THEN 'Atencao critica'
        WHEN perc_inadequado >= 15 THEN 'Atencao moderada'
        WHEN perc_inadequado >=  5 THEN 'Observacao'
        ELSE 'Baixa prevalencia'
    END AS nivel_alerta
FROM proporcao_por_unidade
ORDER BY perc_inadequado DESC, unidade_sigla
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
    output = out_dir / f"IND_10.2_perc_inadequado_pt_{stamp}.csv"

    periods = build_periods_pt()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I10.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I10 {label} ({start} a {end})...")
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

    # Colunas apos meta_cols (6): sigla(0) nome(1) total_av(2) qtd_inadequado(3) perc_inadequado(4) nivel_alerta(5)
    n = len(meta_cols)
    offset_total = n + 2   # total_avaliacoes_pt
    offset_perc  = n + 4   # perc_inadequado

    encerrados = [r for r in all_rows if r[4] == "encerrado"]

    # Unidades em "Atencao critica" (>= 30% inadequado) em periodos encerrados
    criticos = [r for r in encerrados if _to_float(r[offset_perc]) >= 30]
    if criticos:
        unids = set(r[n] for r in criticos)
        print(f"  AVISO: {len(unids)} unidade(s) com perc_inadequado >= 30% em periodos encerrados — requer acompanhamento.")

    # Unidades com < 5 avaliacoes (resultado fragil)
    low_count = sum(1 for r in encerrados if int(r[offset_total] or 0) < 5)
    if low_count:
        print(f"  NOTA: {low_count} linha(s) com < 5 avaliacoes em periodos encerrados — percentuais estatisticamente frageis.")

    em_andamento = sum(1 for r in all_rows if r[4] == "em_andamento")
    if em_andamento:
        print(f"  NOTA: {em_andamento} linha(s) em periodo em_andamento — valores preliminares.")


if __name__ == "__main__":
    main()
