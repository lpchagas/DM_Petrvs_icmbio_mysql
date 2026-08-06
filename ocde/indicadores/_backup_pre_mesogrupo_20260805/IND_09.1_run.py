"""IND_09.1_run.py — I09: Média da Avaliação do Plano de Trabalho por Unidade.

Instrumento: Plano de Trabalho (PT).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ mensal (M01–M12). Base: 01/07/2025.

Correção de escala (19.06.2026): o SQL original usava JSON_UNQUOTE(tan.nota) com
CASE WHEN textual — que não funciona no Denodo VQL via JDBC (retorna NULL para todos
os registros). Substituído por (6 - tan.sequencia), que usa o campo inteiro nativo:
  sequencia=1 → Excepcional     → score 5
  sequencia=2 → Alto desempenho → score 4
  sequencia=3 → Adequado        → score 3
  sequencia=4 → Inadequado      → score 2
  sequencia=5 → Não executado   → score 1

Achado de validação (19.06.2026): com a correção, média nacional ~4,0
("Alto desempenho"), confirmando perfil ICMBio (9% Excepcional + 71% Alto desempenho).
A coluna total_planos_com_avaliacao (COUNT DISTINCT plano_trabalho_id) é a referência
correta para comparar com o PETRVS — o PETRVS exibe planos distintos (7.421), enquanto
total_avaliacoes_pt conta eventos de avaliação (20.664, ratio ~2,78×) por planos com
múltiplas consolidações mensais em 2026.
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

SQL_I09 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
avaliacoes_pt AS (
    SELECT
        av.id                    AS id_avaliacao,
        pt.unidade_id,
        ptc.plano_trabalho_id,
        (6 - tan.sequencia)      AS valor_nota
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
media_por_unidade AS (
    SELECT
        COALESCE(un.sigla, 'N.I.')                               AS unidade_sigla,
        COALESCE(un.nome,  'N.I.')                               AS unidade_nome,
        COUNT(avpt.id_avaliacao)                                 AS total_avaliacoes_pt,
        COUNT(DISTINCT avpt.plano_trabalho_id)                   AS total_planos_com_avaliacao,
        ROUND(AVG(avpt.valor_nota * 1.0), 2)                     AS media_nota_pt,
        MIN(avpt.valor_nota)                                     AS nota_minima,
        MAX(avpt.valor_nota)                                     AS nota_maxima,
        SUM(CASE WHEN avpt.valor_nota = 1 THEN 1 ELSE 0 END)    AS qtd_nota_1,
        SUM(CASE WHEN avpt.valor_nota = 2 THEN 1 ELSE 0 END)    AS qtd_nota_2,
        SUM(CASE WHEN avpt.valor_nota = 3 THEN 1 ELSE 0 END)    AS qtd_nota_3,
        SUM(CASE WHEN avpt.valor_nota = 4 THEN 1 ELSE 0 END)    AS qtd_nota_4,
        SUM(CASE WHEN avpt.valor_nota = 5 THEN 1 ELSE 0 END)    AS qtd_nota_5
    FROM avaliacoes_pt avpt
    LEFT JOIN petrvs_icmbio_unidades un ON un.id = avpt.unidade_id
    GROUP BY COALESCE(un.sigla, 'N.I.'), COALESCE(un.nome, 'N.I.')
)
SELECT
    unidade_sigla,
    unidade_nome,
    total_avaliacoes_pt,
    total_planos_com_avaliacao,
    media_nota_pt,
    nota_minima,
    nota_maxima,
    qtd_nota_1,
    qtd_nota_2,
    qtd_nota_3,
    qtd_nota_4,
    qtd_nota_5,
    CASE
        WHEN media_nota_pt >= 4.5 THEN 'Excepcional'
        WHEN media_nota_pt >= 3.5 THEN 'Alto desempenho'
        WHEN media_nota_pt >= 2.5 THEN 'Adequado'
        WHEN media_nota_pt >= 1.5 THEN 'Inadequado'
        ELSE 'Nao executado'
    END AS faixa_desempenho
FROM media_por_unidade
ORDER BY media_nota_pt DESC, unidade_sigla
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
    output = out_dir / f"IND_09.2_media_avaliacao_pt_{stamp}.csv"

    periods = build_periods_pt()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I09.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I09 {label} ({start} a {end})...")
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

    # Colunas apos meta_cols (6): sigla(0) nome(1) total_av(2) total_planos(3) media(4) ...
    n = len(meta_cols)
    offset_total = n + 2   # total_avaliacoes_pt
    offset_media = n + 4   # media_nota_pt

    encerrados = [r for r in all_rows if r[4] == "encerrado"]

    # Unidades com < 5 avaliacoes (resultado estatisticamente fragil)
    low_count = sum(1 for r in encerrados if int(r[offset_total] or 0) < 5)
    if low_count:
        print(f"  AVISO: {low_count} linha(s) com < 5 avaliacoes em periodos encerrados — resultados frageis.")

    # Unidades com media abaixo de 2.5 (Inadequado ou pior)
    criticas = [r for r in encerrados if _to_float(r[offset_media]) < 2.5 and r[offset_media] != ""]
    if criticas:
        unids = set(r[n] for r in criticas)
        print(f"  AVISO: {len(unids)} unidade(s) com media < 2.5 (Inadequado) em periodos encerrados.")

    em_andamento = sum(1 for r in all_rows if r[4] == "em_andamento")
    if em_andamento:
        print(f"  NOTA: {em_andamento} linha(s) em periodo em_andamento — valores preliminares.")


if __name__ == "__main__":
    main()
