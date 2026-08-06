"""IND_05.1_run.py — I05: Distribuição das Entregas entre os Servidores.

Instrumento: Plano de Trabalho (PT).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ mensal (M01–M12). Base: 01/07/2025.

O I05 calcula quantas entregas do PE cada servidor carrega no PT e compara
com a média dos demais servidores da mesma unidade, respondendo:
"A carga está distribuída de forma equitativa ou concentrada em poucos?"

Nota metodológica: a unidade é derivada de pt.unidade_id (unidade do servidor),
pois o I05 mede distribuição de carga entre servidores, não entre planejadores.
O filtro temporal incide sobre a vigência do PT: servidores ativos no período,
não sobre datas de conclusão de cada entrega.

Correção (24.05.2026): adicionado filtro pte.deleted_at IS NULL, ausente na
versão original. Sem esse filtro, registros excluídos logicamente em
planos_trabalhos_entregas inflavam a quantidade de entregas por servidor.
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

SQL_I05 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
        0                     AS incluir_excluidos
),
vinculos_entregas AS (
    SELECT DISTINCT
        COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
        COALESCE(un.nome,  'N.I.') AS unidade_nome,
        pt.usuario_id              AS id_servidor,
        COALESCE(us.nome,  'N.I.') AS nome_servidor,
        pte.plano_entrega_entrega_id AS id_entrega
    FROM petrvs_icmbio_planos_trabalhos pt
    JOIN petrvs_icmbio_planos_trabalhos_entregas pte
        ON pte.plano_trabalho_id = pt.id
    LEFT JOIN petrvs_icmbio_unidades un
        ON un.id = pt.unidade_id
    LEFT JOIN petrvs_icmbio_usuarios us
        ON us.id = pt.usuario_id
    CROSS JOIN parametros p
    WHERE CAST(pt.data_inicio AS DATE) <= p.data_fim
      AND CAST(pt.data_fim   AS DATE) >= p.data_inicio
      AND (p.incluir_excluidos = 1 OR pt.deleted_at  IS NULL)
      AND (p.incluir_excluidos = 1 OR pte.deleted_at IS NULL)
      AND pt.usuario_id IS NOT NULL
      AND pte.plano_entrega_entrega_id IS NOT NULL
),
entregas_por_servidor AS (
    SELECT
        unidade_sigla,
        MIN(unidade_nome)              AS unidade_nome,
        id_servidor,
        MIN(nome_servidor)             AS nome_servidor,
        COUNT(DISTINCT id_entrega)     AS qtd_entregas_por_servidor
    FROM vinculos_entregas
    GROUP BY unidade_sigla, id_servidor
),
media_por_unidade AS (
    SELECT
        unidade_sigla,
        ROUND(AVG(qtd_entregas_por_servidor) * 1.0, 2)
            AS media_entregas_por_servidor_unidade
    FROM entregas_por_servidor
    GROUP BY unidade_sigla
)
SELECT
    e.unidade_sigla,
    e.unidade_nome,
    e.id_servidor,
    e.nome_servidor,
    e.qtd_entregas_por_servidor,
    m.media_entregas_por_servidor_unidade,
    CASE
        WHEN e.qtd_entregas_por_servidor > m.media_entregas_por_servidor_unidade THEN 'Acima da media'
        WHEN e.qtd_entregas_por_servidor < m.media_entregas_por_servidor_unidade THEN 'Abaixo da media'
        ELSE 'Na media'
    END AS posicao_relativa_media
FROM entregas_por_servidor e
JOIN media_por_unidade m ON m.unidade_sigla = e.unidade_sigla
ORDER BY e.unidade_sigla, e.qtd_entregas_por_servidor DESC, e.nome_servidor
"""


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_05.2_distribuicao_entregas_servidores_{stamp}.csv"

    periods = build_periods_pt()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I05.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I05 {label} ({start} a {end})...")
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

    # Aviso de qualidade: servidores com 0 entregas (PT ativo mas sem vinculos)
    offset_qtd = len(meta_cols) + 4  # posicao de qtd_entregas_por_servidor
    sem_entregas = sum(1 for r in all_rows if str(r[offset_qtd]) == "0")
    if sem_entregas:
        print(f"  AVISO: {sem_entregas} servidor(es) com 0 entregas vinculadas — verificar preenchimento do PT.")


if __name__ == "__main__":
    main()
