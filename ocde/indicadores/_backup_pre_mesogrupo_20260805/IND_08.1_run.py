"""IND_08.1_run.py — I08: Proporção de Horas por Entrega — Planejadas (%).

Instrumento: misto PT + PE — ciclo alinhado ao Plano de Entregas (PE).
Periodicidade: 2025 trimestral (T3–T4) | 2026+ quadrimestral (Q1–Q3). Base: 01/07/2025.

Calcula qual percentual da capacidade total planejada de cada unidade foi
alocado a cada entrega, normalizando o valor absoluto do I07 pelo total de
horas disponíveis na unidade. Responde: "Qual o peso relativo de cada entrega
no esforço total planejado da unidade?"

Fórmula:
  proporcao_horas_perc = horas_planejadas_entrega
                         / total_horas_disponiveis_unidade × 100

  onde total_horas_disponiveis_unidade = soma de horas proporcionais de todos
  os PTs ativos da unidade no período (denominador = capacidade total declarada).

Abordagem técnica Denodo/JDBC (compatível — sem WITH RECURSIVE):
  Mesma aritmética proporcional do I07 + bloco capacidade_unidade extra.
  Tabelas sem prefixo no DBeaver; com prefixo petrvs_icmbio_ via JDBC.

Correções aplicadas (alinhadas ao I07 — 14.06.2026):
  1. Unidade: COALESCE(pe.unidade_id, ph.unidade_id) atribui entrega à unidade
     do PE (planejador), com fallback para unidade do PT (executor).
  2. Filtro temporal do PE: adicionado em linhas para eliminar entregas de PEs
     fora do período consultado (elimina duplicatas entre períodos).
  3. Prefixos petrvs_icmbio_: adicionados a todas as tabelas físicas para
     compatibilidade JDBC (a doc original seção 2 usava formato DBeaver sem prefix).

Nota: proporcao_horas_perc pode superar 100% se forca_trabalho > 100% em algum
vínculo — indicador de dado inválido no PETRVS, detectado pelo aviso de qualidade.
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

SQL_I08 = """
WITH parametros AS (
    SELECT
        CAST('{ini}' AS DATE) AS data_inicio,
        CAST('{fim}' AS DATE) AS data_fim,
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
"""


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = out_dir / f"IND_08.2_proporcao_horas_entrega_{stamp}.csv"

    periods = build_periods_pe()
    meta_cols = period_metadata()
    all_cols: list[str] | None = None
    all_rows: list[list] = []

    try:
        for label, kind, start, end, status in periods:
            sql = SQL_I08.replace("{ini}", str(start)).replace("{fim}", str(end))
            print(f"Executando I08 {label} ({start} a {end})...")
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

    # Aviso de qualidade: proporcao > 100% indica forca_trabalho inconsistente
    offset_perc = len(meta_cols) + 6  # posicao de proporcao_horas_perc
    acima_100 = sum(1 for r in all_rows if _to_float(r[offset_perc]) > 100.0)
    if acima_100:
        print(f"  ALERTA: {acima_100} entrega(s) com proporcao_horas_perc > 100% — verificar forca_trabalho no PETRVS.")

    # Aviso de periodo em_andamento
    em_andamento = sum(1 for r in all_rows if str(r[4]) == "em_andamento")
    if em_andamento:
        print(f"  AVISO: {em_andamento} linha(s) de periodos em_andamento — resultados preliminares.")


def _to_float(value: object) -> float:
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return 0.0


if __name__ == "__main__":
    main()
