"""IND_01.1_run.py — I01: Proporcao de Servidores por Regime de Trabalho.

Instrumento: Plano de Trabalho (PT).
Periodicidade: 2025 trimestral (T3-T4) | 2026+ mensal (M01-M12). Base: 01/07/2025.

Estrategia de calculo: uma unica consulta ao Denodo carrega todos os planos
de trabalho com vigencia a partir de 2025. A segmentacao temporal e feita em
Python com verificacao de sobreposicao (plano_ini <= periodo_fim AND plano_fim
>= periodo_ini), permitindo cobrir multiplos periodos com um unico round-trip
ao banco (~14.000 registros em memoria).

Nota tecnica (23.05.2026): a view tipos_modalidades esta inacessivel no Denodo.
O regime de trabalho e obtido via integracao_servidores.modalidade_pgd (campo
SIAPE/PGD), consolidado por CPF com MIN() para servidores com multiplos
registros. UUIDs brutos indicam falha de mapeamento no cadastro SIAPE/PGD.

Alertas de qualidade:
  - UUIDs sem rotulo de modalidade: cadastro SIAPE/PGD sem mapeamento textual.
  - Planos com datas invalidas: descartados com aviso de contagem.
  - Periodo em andamento: dados do ultimo periodo sao preliminares.

Saidas (em artefatos_local/ocde/entregas/YYYY-MM/):
  IND_01.2_v1_proporcao_mensal_AAAAMMDD_HHMM.csv      -- visao institucional
  IND_01.2_v2_proporcao_unidade_mensal_AAAAMMDD_HHMM.csv -- visao por unidade

Colunas-meta padrao (6) presentes em ambos os CSVs:
  ciclo_tipo | periodo | periodo_inicio | periodo_fim | periodo_status | duracao_dias
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib" / "__init__.py").exists())
sys.path.insert(0, str(ROOT))

from lib.csv_utils import indicator_csv_dir, write_pipe_csv
from lib.denodo_config import connect, get_config
from lib.monthly_runner import query_rows
from lib.periodos import build_periods_pt, period_metadata

# ── Consulta principal (sem filtro de periodo — agregacao feita em Python) ──────
SQL_I01_PLANOS = """
SELECT
    pt.usuario_id,
    COALESCE(un.sigla, 'N.I.') AS unidade_sigla,
    COALESCE(un.nome,  'N.I.') AS unidade_nome,
    CASE
        WHEN NULLIF(TRIM(COALESCE(ins.modalidade_pgd, '')), '') IS NULL THEN 'N.I.'
        ELSE TRIM(ins.modalidade_pgd)
    END                          AS modalidade,
    CAST(pt.data_inicio AS DATE) AS plano_inicio,
    CAST(pt.data_fim    AS DATE) AS plano_fim
FROM petrvs_icmbio_planos_trabalhos pt
JOIN petrvs_icmbio_usuarios u
    ON  u.id = pt.usuario_id
LEFT JOIN (
    SELECT
        cpf,
        MIN(NULLIF(TRIM(COALESCE(modalidade_pgd, '')), '')) AS modalidade_pgd
    FROM petrvs_icmbio_integracao_servidores
    WHERE cpf IS NOT NULL
    GROUP BY cpf
) ins ON ins.cpf = u.cpf
LEFT JOIN petrvs_icmbio_unidades un
    ON  un.id = pt.unidade_id
WHERE pt.deleted_at  IS NULL
  AND pt.usuario_id  IS NOT NULL
  AND pt.data_inicio IS NOT NULL
  AND pt.data_fim    IS NOT NULL
  AND CAST(pt.data_fim AS DATE) >= CAST('2025-01-01' AS DATE)
"""

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(str(value).strip()))


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except (ValueError, AttributeError):
        return None


def main() -> None:
    config = get_config(require_credentials=True)
    conn = connect(config)
    out_dir = indicator_csv_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_v1 = out_dir / f"IND_01.2_v1_proporcao_mensal_{stamp}.csv"
    output_v2 = out_dir / f"IND_01.2_v2_proporcao_unidade_mensal_{stamp}.csv"

    print("Carregando planos de trabalho do Denodo...")
    try:
        columns, rows = query_rows(conn, SQL_I01_PLANOS)
    finally:
        conn.close()

    pos = {name: idx for idx, name in enumerate(columns)}
    plans: list[dict] = []
    uuid_count = 0
    skipped = 0

    for row in rows:
        start = _parse_date(row[pos["plano_inicio"]])
        end   = _parse_date(row[pos["plano_fim"]])
        if not start or not end or start > end:
            skipped += 1
            continue
        mod = row[pos["modalidade"]] or "N.I."
        if _is_uuid(mod):
            uuid_count += 1
        plans.append(
            {
                "usuario_id":    str(row[pos["usuario_id"]]) if row[pos["usuario_id"]] else "",
                "unidade_sigla": row[pos["unidade_sigla"]] or "N.I.",
                "unidade_nome":  row[pos["unidade_nome"]]  or "N.I.",
                "modalidade":    mod,
                "inicio":        start,
                "fim":           end,
            }
        )

    print(f"  {len(plans)} planos carregados | {skipped} descartados (data invalida).")
    if uuid_count:
        print(
            f"  AVISO: {uuid_count} plano(s) com UUID como modalidade "
            f"— cadastro SIAPE/PGD sem mapeamento textual."
        )

    # Descartar planos sem usuario_id valido (nao deve ocorrer apos filtro SQL)
    plans = [p for p in plans if p["usuario_id"]]

    periods = build_periods_pt()
    meta_cols = period_metadata()

    v1_cols = meta_cols + ["modalidade", "total_servidores", "proporcao_perc"]
    v2_cols = meta_cols + [
        "unidade_sigla", "unidade_nome",
        "modalidade", "total_servidores", "proporcao_na_unidade_perc",
    ]
    v1_rows: list[list] = []
    v2_rows: list[list] = []

    for label, kind, p_ini, p_fim, status in periods:
        dur    = (p_fim - p_ini).days + 1
        active = [p for p in plans if p["inicio"] <= p_fim and p["fim"] >= p_ini]
        if not active:
            print(f"  {label}: sem planos ativos no periodo.")
            continue

        by_mode: dict[str, set[str]]                   = defaultdict(set)
        by_unit: dict[tuple[str, str], set[str]]       = defaultdict(set)
        by_unit_mode: dict[tuple[str, str, str], set[str]] = defaultdict(set)

        for plan in active:
            uid = plan["usuario_id"]
            mod = plan["modalidade"]
            sig = plan["unidade_sigla"]
            nom = plan["unidade_nome"]
            by_mode[mod].add(uid)
            by_unit[(sig, nom)].add(uid)
            by_unit_mode[(sig, nom, mod)].add(uid)

        total = len(set().union(*by_mode.values())) if by_mode else 0
        print(f"  {label}: {total} servidores ativos | {len(active)} planos sobrepostos.")

        # V1 — visao institucional
        for mod in sorted(by_mode, key=lambda m: -len(by_mode[m])):
            n   = len(by_mode[mod])
            pct = round(n * 100.0 / total, 2) if total else 0.0
            v1_rows.append(
                [kind, label, str(p_ini), str(p_fim), status, dur, mod, n, pct]
            )

        # V2 — visao por unidade
        for (sig, nom) in sorted(by_unit):
            denom      = len(by_unit[(sig, nom)])
            unit_modes = {
                k[2]: v
                for k, v in by_unit_mode.items()
                if k[0] == sig and k[1] == nom
            }
            for mod in sorted(unit_modes, key=lambda m: -len(unit_modes[m])):
                n   = len(unit_modes[mod])
                pct = round(n * 100.0 / denom, 2) if denom else 0.0
                v2_rows.append(
                    [kind, label, str(p_ini), str(p_fim), status, dur,
                     sig, nom, mod, n, pct]
                )

    if not v1_rows:
        print("Nenhum dado retornado. CSVs nao gerados.")
        return

    write_pipe_csv(output_v1, v1_cols, v1_rows)
    write_pipe_csv(output_v2, v2_cols, v2_rows)

    print(f"\nV1 — {len(v1_rows)} linhas: {output_v1.name}")
    print(f"V2 — {len(v2_rows)} linhas: {output_v2.name}")
    print(f"Periodos cobertos: {len(periods)} | Arquivo destino: {out_dir}")

    last = periods[-1] if periods else None
    if last and last[4] == "em_andamento":
        print(
            f"  AVISO: Periodo {last[0]} em andamento — "
            f"dados de {last[2]} a {date.today()} sao preliminares."
        )
    print("Concluido.")


if __name__ == "__main__":
    main()
