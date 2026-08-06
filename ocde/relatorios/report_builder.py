"""report_builder.py — Montagem do documento Markdown a partir de blocos de análise."""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from .metricas import MetricasPeriodo


def hdr(titulo: str, nivel: int = 2) -> str:
    return f"\n{'#' * nivel} {titulo}\n"


def divisor() -> str:
    return "\n---\n"


def cabecalho(mes_label: str, unidade: Optional[str], titulo: str) -> str:
    escopo = f"Unidade: {unidade}" if unidade else "Escopo: Nacional (todas as unidades)"
    return (
        f"# {titulo}\n\n"
        f"**Referência:** {mes_label}  \n"
        f"**{escopo}**  \n"
        f"**Gerado em:** {date.today().strftime('%d/%m/%Y')}\n"
        f"\n---\n"
    )


def tabela_metricas(serie: list[MetricasPeriodo], unidade_col: str = "%") -> str:
    if not serie:
        return "_Sem dados disponíveis._\n"
    rows = [
        f"| Período | N | Média ({unidade_col}) | Mediana | P25 | P75 | Mín | Máx | Δ% |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in serie:
        delta = f"{m.delta_pct:+.1f}%" if m.delta_pct is not None else "—"
        rows.append(
            f"| {m.periodo} | {m.n} | {m.media} | {m.mediana} "
            f"| {m.p25} | {m.p75} | {m.minimo} | {m.maximo} | {delta} |"
        )
    return "\n".join(rows) + "\n"


def tabela_ranking(
    df: Optional[pd.DataFrame],
    col: str,
    titulo: str = "",
    n: int = 10,
    fmt: str = ".2f",
) -> str:
    if df is None or df.empty:
        return "_Sem dados para ranking._\n"
    linhas: list[str] = []
    if titulo:
        linhas.append(f"**{titulo}**\n")
    linhas += ["| # | Unidade | Valor |", "|---|---|---|"]
    for i, (_, row) in enumerate(df.head(n).iterrows(), 1):
        sigla = row.get("unidade_sigla", "—")
        val = row.get(col)
        val_fmt = format(val, fmt) if isinstance(val, (int, float)) and pd.notna(val) else str(val or "—")
        linhas.append(f"| {i} | {sigla} | {val_fmt} |")
    return "\n".join(linhas) + "\n"


def bloco_insights(insights: list[str]) -> str:
    if not insights:
        return "_Sem insights disponíveis._\n"
    return "\n".join(f"- {i}" for i in insights) + "\n"


def bloco_recomendacoes(recs: list[str], titulo: str = "Recomendações aos Gestores") -> str:
    linhas = [f"\n## {titulo}\n"]
    if not recs:
        linhas.append("_Sem recomendações geradas._\n")
    else:
        for r in recs:
            linhas.append(f"- {r}")
        linhas.append("")
    return "\n".join(linhas)


def painel_semaforo(dados: dict[str, str]) -> str:
    """Tabela Markdown de semáforos. `dados`: {label: semaforo_str}."""
    rows = ["| Área / Indicador | Situação |", "|---|---|"]
    for label, sem in dados.items():
        rows.append(f"| {label} | {sem} |")
    return "\n".join(rows) + "\n"


def rodape(mes_label: str, unidade: Optional[str]) -> str:
    escopo = unidade or "Nacional"
    return (
        f"\n---\n\n"
        f"_Relatório gerado automaticamente a partir dos CSVs em "
        f"`artefatos_local/ocde/entregas/{mes_label}/`. "
        f"Escopo: {escopo}. "
        f"Para dúvidas sobre metodologia, consultar `docs/06-indicadores-ocde-mysql.md`._\n"
    )
