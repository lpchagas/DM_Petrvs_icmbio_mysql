"""IND_06.1_run.py — I06: Grau de Responsabilidade pelas Entregas.

Instrumento: Plano de Trabalho (PT).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ mensal (M01–M12). Base: 01/07/2025.

O I06 calcula quantos servidores estão vinculados a cada entrega do PE,
classificando-as por tamanho do grupo responsável, respondendo:
"As entregas têm cobertura distribuída ou há pontos únicos de falha?"

Nota metodológica: a unidade é derivada de pt.unidade_id (unidade do executor),
não de pe.unidade_id (planejador). Uma entrega da CGOV executada por servidor
da AUDIT aparece sob AUDIT no I06. Isso é intencional: mede responsabilidade
de quem executa, não de quem planejou. Consequência: total_entregas_unidade
no I06 pode diferir do total de PEs por unidade no I02.

Aviso metodológico: ciclos mistos (2025 trimestral vs 2026 quadrimestral)
afetam total_entregas_unidade — usar pct_categoria para comparações entre períodos.
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

SQL_I06 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
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
"""


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_06.2_grau_responsabilidade_entregas_{stamp}.csv"

    periods = build_periods_pt()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I06.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I06 {label} ({start} a {end})...")
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

    # Aviso de qualidade: proporcao de entregas com responsavel unico (ponto de falha)
    offset_grupo = len(meta_cols) + 2  # posicao de tamanho_grupo_responsavel
    total = len(all_rows)
    ponto_unico = sum(1 for r in all_rows if str(r[offset_grupo]) == "1 servidor")
    if total > 0:
        pct = round(ponto_unico * 100.0 / total, 1)
        if pct > 50:
            print(f"  AVISO: {pct}% das linhas sao '1 servidor' — alta concentracao de pontos unicos de falha.")
    print("  Nota: unidade = unidade do SERVIDOR (pt.unidade_id), nao do planejador (pe.unidade_id).")


if __name__ == "__main__":
    main()
